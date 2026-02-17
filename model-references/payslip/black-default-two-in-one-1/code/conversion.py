try:
    import pdfplumber
except ImportError:
    pdfplumber = None
import re
try:
    import pandas as pd
except ImportError:
    pd = None
from collections import OrderedDict
import sys
import os

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

def extrair_mes_ano_linha(linha):
    """Extrai mês e ano da linha de cabeçalho 'Demonstrativo de Pagamento Folha Mensal de MM/AAAA'"""
    match = re.search(r'Folha Mensal de (\d{2}/\d{4})', linha)
    if match:
        return match.group(1)
    return None

def eh_desconto(descricao):
    """Determina se uma verba é desconto baseado na descrição"""
    descricoes_desconto = [
        'INSS', 'IRRF', 'IMPOSTO', 'DESCONTO', 'ADTO', 'ADIANTAMENTO',
        'VALE', 'CESTA', 'PLANO', 'CONTRIBUI', 'SINDICATO', 'EMPRESTIMO', 'FALTAS'
    ]
    
    descricao_upper = descricao.upper()
    return any(palavra in descricao_upper for palavra in descricoes_desconto)

def parse_linha_tabela(linha):
    """Parser para as linhas da tabela"""
    linha = linha.strip()
    linha = re.sub(r'\s+', ' ', linha)
    
    parts = linha.split()
    
    if len(parts) < 3:
        return None
    
    # Verifica se começa com código (geralmente 5 dígitos neste modelo, ex: 00001, 00019)
    if not re.match(r'^\d+$', parts[0]):
        return None
        
    codigo = parts[0]
    
    # Identifica valores monetários/numéricos
    valores = []
    indices_valores = []
    
    for i, parte in enumerate(parts):
        # Formato numérico brasileiro: 1.234,56 ou 123,45
        if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', parte):
            valores.append(parte)
            indices_valores.append(i)
            
    if not valores:
        return None
        
    # Descrição está entre o código e o primeiro valor
    if indices_valores:
        inicio_desc = 1
        fim_desc = indices_valores[0]
        descricao = ' '.join(parts[inicio_desc:fim_desc])
    else:
        return None

    referencia = None
    valor_final = None
    
    # Lógica de distribuição dos valores
    if len(valores) == 2:
        referencia = valores[0]
        valor_final = valores[1]
            
    elif len(valores) == 1:
        valor_final = valores[0]
            
    return {
        "codigo": codigo,
        "descricao": descricao,
        "referencia": referencia,
        "valor": valor_final
    }

def processar_linhas_texto(linhas_texto):
    """
    Processa uma lista de strings (linhas do PDF ou do arquivo de texto)
    Retorna um dicionário consolidado por Mês/Ano
    """
    dados_consolidados = OrderedDict()
    
    dados_atual = {}
    mes_ano_atual = None
    dentro_tabela = False
    
    for linha in linhas_texto:
        linha = linha.strip()
        if not linha:
            continue
            
        # 1. Tenta detectar novo cabeçalho de contracheque
        novo_mes_ano = extrair_mes_ano_linha(linha)
        if novo_mes_ano:
            print(f"Novo contracheque detectado: {novo_mes_ano}")
            mes_ano_atual = novo_mes_ano
            if mes_ano_atual not in dados_consolidados:
                dados_consolidados[mes_ano_atual] = {"MES_ANO": mes_ano_atual}
            
            dados_atual = dados_consolidados[mes_ano_atual]
            dentro_tabela = False # Reinicia estado da tabela
            continue
            
        if not mes_ano_atual:
            continue
            
        # 2. Detecta início da tabela
        if "Cód" in linha and "Descrição" in linha:
            dentro_tabela = True
            continue
            
        # 3. Detecta fim da tabela / Rodapé
        if "Salário p/Mês" in linha or "Total Venctos" in linha or "L í q u i d o" in linha:
            dentro_tabela = False
            continue
            
        # 4. Processa linhas da tabela
        if dentro_tabela:
            dados_linha = parse_linha_tabela(linha)
            if dados_linha:
                print(f"Processando verba: {dados_linha}")
                
                # Monta as chaves
                if dados_linha["valor"]:
                    chave = f"{dados_linha['codigo']} - {dados_linha['descricao']} [VALOR]"
                    
                    # Verifica se deve atualizar o valor (pega o maior, similar ao reference)
                    valor_atual = converter_para_float(dados_atual.get(chave))
                    novo_valor = converter_para_float(dados_linha["valor"])
                    
                    if novo_valor is not None:
                        if (valor_atual is None) or (novo_valor > valor_atual):
                            dados_atual[chave] = dados_linha["valor"]
                            print(f"Atualizando {chave}: {dados_linha['valor']}")
                    
                if dados_linha["referencia"]:
                    chave = f"{dados_linha['codigo']} - {dados_linha['descricao']} [REFERENCIA]"
                    dados_atual[chave] = dados_linha["referencia"]

    return dados_consolidados

def agrupar_linhas_pdf(page, y_tolerance=3):
    """Agrupa palavras do PDF em linhas (mesma lógica do original)"""
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
                linhas.append(" ".join([p['text'] for p in linha_atual]))
            linha_atual = [palavra]
            y_ref = palavra['top']
    
    if linha_atual:
        linhas.append(" ".join([p['text'] for p in linha_atual]))
    
    return linhas

def ler_pdf_e_gerar_planilha(caminho_pdf, caminho_excel, paginas_a_ler=None):
    """Fluxo principal para ler PDF"""
    todas_linhas = []
    
    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        paginas_a_ler = paginas_a_ler or range(total_paginas)
        
        for i in paginas_a_ler:
            if i >= total_paginas:
                print(f"Página {i+1} não existe (total: {total_paginas})")
                continue
                
            print(f"\nProcessando página {i+1}/{total_paginas}...")
            page = pdf.pages[i]
            linhas_pagina = agrupar_linhas_pdf(page)
            todas_linhas.extend(linhas_pagina)
            
    dados = processar_linhas_texto(todas_linhas)
    gerar_excel(dados, caminho_excel)

def ler_texto_exemplo_e_gerar_planilha(caminho_txt, caminho_excel):
    """Fluxo alternativo para ler do arquivo de texto (debug/dev)"""
    with open(caminho_txt, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
        
    dados = processar_linhas_texto(linhas)
    gerar_excel(dados, caminho_excel)

def gerar_excel(dados_consolidados, caminho_excel):
    if not dados_consolidados:
        print("Nenhum dado encontrado.")
        return

    # Transforma o dicionário de dicionários em uma lista de dicionários
    lista_dados = list(dados_consolidados.values())
    
    if pd:
        df = pd.DataFrame(lista_dados)
        
        # Ordena colunas para ficar bonitinho (MES_ANO primeiro)
        cols = ['MES_ANO'] + [c for c in df.columns if c != 'MES_ANO']
        df = df[cols]
        
        df.to_excel(caminho_excel, index=False)
        print(f"Planilha gerada com sucesso: {caminho_excel}")
        
        print(f"Dados consolidados para {len(df)} períodos:")
        for mes_ano in dados_consolidados.keys():
            print(f"  - {mes_ano}")
    else:
        print("Pandas não está instalado. Exibindo dados extraídos:")
        import json
        print(json.dumps(lista_dados, indent=2, ensure_ascii=False))
        print(f"AVISO: Planilha não foi gerada em {caminho_excel} pois o pandas não está disponível.")

if __name__ == "__main__":
    # Modo de teste rápido se passar argumento 'test'
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        txt_path = os.path.join(base_dir, "examples", "print.txt") # Atualizado para usar print.txt
        excel_path = os.path.join(base_dir, "examples", "resultado_teste.xlsx")
        print(f"Modo de teste: Lendo {txt_path}")
        ler_texto_exemplo_e_gerar_planilha(txt_path, excel_path)
    else:
        # Modo interativo com seleção de páginas
        CAMINHO_PDF = r"S:/work/eg-goncalves/pdfs/" + input("Digite o nome do arquivo PDF: ")
        CAMINHO_EXCEL = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Digite o nome do arquivo Excel de saída: ")
        
        try:
            pagina_inicial = int(input("Digite o número da página inicial: ")) - 1
            pagina_final = int(input("Digite o número da página final: "))
            
            ler_pdf_e_gerar_planilha(
                CAMINHO_PDF, 
                CAMINHO_EXCEL,
                paginas_a_ler=range(pagina_inicial, pagina_final)
            )
        except ValueError:
            print("Entrada inválida para número de páginas. Processando tudo.")
            ler_pdf_e_gerar_planilha(CAMINHO_PDF, CAMINHO_EXCEL)
