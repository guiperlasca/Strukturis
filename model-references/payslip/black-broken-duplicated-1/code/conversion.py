import pdfplumber
import re
import pandas as pd
from collections import OrderedDict


def converter_para_float(valor):
    """Converte valores no formato '1.234,56' ou '1.234,56-' para float 1234.56"""
    if not valor:
        return None
    try:
        valor = valor.strip()
        if valor.endswith('-'):
            valor = valor[:-1]
        return float(valor.replace('.', '').replace(',', '.'))
    except:
        return None


def extrair_mes_ano(linhas):
    """Extrai o mês e ano do contracheque a partir das linhas de texto"""
    for linha in linhas:
        # Procura por padrões como "Mensalista Março de 2023"
        match = re.search(r'Mensalista\s+(\w+)\s+de\s+(\d{4})', linha)
        if match:
            mes = match.group(1)
            ano = match.group(2)
            return f"{mes}/{ano}"
    return None


def extrair_todos_valores(linha):
    """Extrai todos os valores monetários de uma linha (formato: 1.234,56)"""
    padrao_valor = r'\d{1,3}(?:\.\d{3})*,\d{2}'
    valores = re.findall(padrao_valor, linha)
    return valores


def is_texto_invertido(texto):
    """Detecta se o texto está invertido (escrito de trás para frente)"""
    # Lista de palavras conhecidas que aparecem invertidas
    palavras_invertidas = [
        'obicer',  # recibo
        'etsen',   # neste
        'adanimircsid',  # discriminada
        'adiuqíl',  # líquida
        'aicnâtropmi',  # importância
        'odibecer',  # recebido
        'ret',  # ter
        'oralceD',  # Declaro
        'oiránoicnuF',  # Funcionário
        'od',  # do
        'arutanissA',  # Assinatura
        'ataD'  # Data
    ]
    
    texto_lower = texto.lower()
    for palavra in palavras_invertidas:
        if palavra.lower() in texto_lower:
            return True
    return False


def limpar_texto_invertido(texto):
    """Remove palavras invertidas do texto"""
    palavras = texto.split()
    palavras_limpas = []
    
    for palavra in palavras:
        if not is_texto_invertido(palavra):
            palavras_limpas.append(palavra)
    
    return ' '.join(palavras_limpas)


def parse_verba_line_belshop(linha):
    """
    Extrai dados de uma linha do formato BELSHOP
    Formato esperado: [CODIGO] DESCRICAO VALOR1 VALOR2 [VALOR3]
    Sempre pega os últimos 2 valores como Vencimentos e Descontos
    """
    linha = linha.strip()
    
    # Remove texto invertido antes de processar
    linha = limpar_texto_invertido(linha)
    
    # Se a linha ficou vazia após limpeza, retorna None
    if not linha or len(linha.strip()) < 3:
        return None
    
    # Extrai todos os valores monetários da linha
    valores = extrair_todos_valores(linha)
    
    # Precisa ter pelo menos 2 valores (vencimentos e descontos)
    if len(valores) < 2:
        return None
    
    # Pega os últimos 2 valores
    descontos = valores[-1]
    vencimentos = valores[-2]
    referencia = valores[-3] if len(valores) >= 3 else ""
    
    # Remove os valores da linha para pegar código e descrição
    linha_sem_valores = linha
    for valor in valores:
        linha_sem_valores = linha_sem_valores.replace(valor, '', 1)
    
    linha_sem_valores = linha_sem_valores.strip()
    
    # Tenta extrair código (número no início)
    match_codigo = re.match(r'^(\d+)\s+(.+)$', linha_sem_valores)
    
    if match_codigo:
        codigo = match_codigo.group(1)
        descricao = match_codigo.group(2).strip()
    else:
        codigo = ""
        descricao = linha_sem_valores.strip()
    
    # Valida se a descrição não está vazia e tem conteúdo significativo
    if not descricao or len(descricao) < 3:
        return None
    
    # Verifica se a descrição ainda contém texto invertido
    if is_texto_invertido(descricao):
        return None
    
    return {
        "codigo": codigo,
        "descricao": descricao,
        "referencia": referencia,
        "vencimentos": vencimentos,
        "descontos": descontos
    }


def agrupar_linhas(page, y_tolerance=3):
    """Agrupa palavras em linhas baseado na posição Y"""
    palavras = page.extract_words()
    if not palavras:
        return []
    
    palavras.sort(key=lambda w: (w['top'], w['x0']))
    
    linhas = []
    linha_atual = []
    y_ref = None
    
    for palavra in palavras:
        if y_ref is None or abs(palavra['top'] - y_ref) <= y_tolerance:
            linha_atual.append(palavra)
            y_ref = palavra['top']
        else:
            if linha_atual:
                linha_texto = " ".join([p['text'] for p in linha_atual])
                # Limpa texto invertido antes de adicionar
                linha_texto = limpar_texto_invertido(linha_texto)
                if linha_texto.strip():  # Só adiciona se não ficou vazia
                    linhas.append(linha_texto)
            linha_atual = [palavra]
            y_ref = palavra['top']
    
    if linha_atual:
        linha_texto = " ".join([p['text'] for p in linha_atual])
        linha_texto = limpar_texto_invertido(linha_texto)
        if linha_texto.strip():
            linhas.append(linha_texto)
    
    return linhas


def processar_pagina_belshop(page):
    """Processa uma página do formato BELSHOP e extrai os dados do contracheque"""
    linhas = agrupar_linhas(page)
    dados = {}
    
    # Extrai o mês/ano
    mes_ano = extrair_mes_ano(linhas)
    if mes_ano:
        dados["MES_ANO"] = mes_ano
        print(f"Mês/Ano encontrado: {mes_ano}")
    else:
        print("Mês/Ano não encontrado")
        return dados
    
    # Flags de controle
    dentro_tabela = False
    primeira_tabela = True
    linhas_processadas_descricoes = set()
    
    for i, linha in enumerate(linhas):
        # Detecta o início da tabela de dados
        if "Código Descrição Referência Vencimentos Descontos" in linha:
            if primeira_tabela:
                dentro_tabela = True
                primeira_tabela = False
                print(f"Início da tabela detectado na linha {i}")
                continue
            else:
                # Segunda tabela (duplicata) - para de processar
                print(f"Segunda tabela detectada na linha {i} - parando processamento")
                break
        
        # Para de processar quando encontrar "Total de Vencimentos"
        if "Total de Vencimentos" in linha:
            print(f"Total de Vencimentos encontrado - encerrando tabela")
            dentro_tabela = False
            break
        
        # Processa apenas se estiver dentro da tabela
        if dentro_tabela:
            # Tenta fazer parse da linha
            verba_data = parse_verba_line_belshop(linha)
            
            if verba_data and verba_data["descricao"]:
                descricao = verba_data["descricao"]
                # Verifica se não é uma descrição duplicada
                if descricao in linhas_processadas_descricoes:
                    print(f"Descrição duplicada ignorada: {descricao}")
                    continue
                
                linhas_processadas_descricoes.add(descricao)
                print(f"Processando: {verba_data}")
                
                chave_ref = f"{descricao} [REFERENCIA]"
                chave_venc = f"{descricao} [VENCIMENTOS]"
                chave_desc = f"{descricao} [DESCONTOS]"
                
                if verba_data["referencia"]:
                    dados[chave_ref] = verba_data["referencia"]
                
                dados[chave_venc] = verba_data["vencimentos"]
                dados[chave_desc] = verba_data["descontos"]
    
    print(f"Total de descrições processadas: {len(linhas_processadas_descricoes)}")
    print(f"DADOS EXTRAÍDOS: {dados}")
    return dados


def ler_pdf_e_gerar_planilha(caminho_pdf, caminho_excel, paginas_a_ler=None):
    """Lê o PDF e gera a planilha Excel com os dados consolidados"""
    dados_consolidados = OrderedDict()
    
    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        paginas_a_ler = paginas_a_ler or range(total_paginas)
        
        for i in paginas_a_ler:
            if i >= total_paginas:
                print(f"Página {i+1} não existe (total: {total_paginas})")
                continue
                
            print(f"\n{'='*70}")
            print(f"Processando página {i+1}/{total_paginas}...")
            print(f"{'='*70}")
            pagina = pdf.pages[i]
            dados_pagina = processar_pagina_belshop(pagina)
            
            if not dados_pagina.get("MES_ANO"):
                print(f"Página {i+1} não contém dados válidos")
                continue
            
            mes_ano = dados_pagina["MES_ANO"]
            
            if mes_ano not in dados_consolidados:
                dados_consolidados[mes_ano] = dados_pagina.copy()
                print(f"✓ Dados adicionados para {mes_ano}")
            else:
                # Atualiza valores existentes
                print(f"⚠ Dados já existem para {mes_ano} - atualizando...")
                for chave, valor in dados_pagina.items():
                    if chave == "MES_ANO":
                        continue
                    
                    if "[VENCIMENTOS]" in chave or "[DESCONTOS]" in chave:
                        valor_existente = converter_para_float(dados_consolidados[mes_ano].get(chave))
                        novo_valor = converter_para_float(valor)
                        
                        if novo_valor is not None:
                            if (valor_existente is None) or (novo_valor > valor_existente):
                                dados_consolidados[mes_ano][chave] = valor
                                print(f"  Atualizado: {chave} = {valor}")
                    else:
                        dados_consolidados[mes_ano][chave] = valor
    
    # Gera a planilha (colunas baseadas apenas nas descrições, ignorando código)
    if dados_consolidados:
        df = pd.DataFrame(dados_consolidados.values())
        df.to_excel(caminho_excel, index=False)
        print(f"\n{'='*70}")
        print(f"✅ PLANILHA GERADA COM SUCESSO!")
        print(f"{'='*70}")
        print(f"Arquivo: {caminho_excel}")
        print(f"Períodos consolidados: {len(df)}")
        print("\nResumo dos períodos:")
        for mes_ano in dados_consolidados.keys():
            num_colunas = len([k for k in dados_consolidados[mes_ano].keys() if k != "MES_ANO"])
            print(f"  • {mes_ano}: {num_colunas} colunas de dados")
    else:
        print("\n⚠️ NENHUM DADO VÁLIDO ENCONTRADO.")


if __name__ == "__main__":
    CAMINHO_PDF = r"S:/work/eg-goncalves/pdfs/" + input("Digite o nome do arquivo PDF (ex.: contracheque_fulano.pdf): ")
    CAMINHO_EXCEL = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Digite o nome do arquivo Excel de saída (ex.: resultado.xlsx): ")
    
    pagina_inicial = int(input("Digite o número da página inicial: ")) - 1
    pagina_final = int(input("Digite o número da página final: "))
    
    ler_pdf_e_gerar_planilha(
        CAMINHO_PDF, 
        CAMINHO_EXCEL,
        paginas_a_ler=range(pagina_inicial, pagina_final)
    )
