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


def extrair_mes_ano_novo_formato(linhas):
    """Extrai o mês e ano do formato novo - procura por padrão MM/AAAA"""
    for linha in linhas:
        # Procura por padrão como "07/2024" no início da linha
        match = re.search(r'^(\d{2})/(\d{4})$', linha.strip())
        if match:
            mes = match.group(1)
            ano = match.group(2)
            return f"{mes}/{ano}"
        
        # Também pode estar em formato como "MÊS/ANO 07/2024"
        match2 = re.search(r'(\d{2})/(\d{4})', linha)
        if match2:
            mes = match2.group(1)
            ano = match2.group(2)
            return f"{mes}/{ano}"
    return None


def eh_desconto(descricao):
    """Determina se uma verba é desconto baseado na descrição"""
    descricoes_desconto = [
        'INSS', 'IRRF', 'IMPOSTO', 'DESCONTO', 'ADTO', 'ADIANTAMENTO',
        'VALE', 'CESTA', 'PLANO', 'CONTRIBUI', 'SINDICATO'
    ]
    
    descricao_upper = descricao.upper()
    return any(palavra in descricao_upper for palavra in descricoes_desconto)


def parse_linha_tabela_novo_formato(linha):
    """Parser para as linhas da tabela do novo formato"""
    linha = linha.strip()
    linha = re.sub(r'\s+', ' ', linha)
    
    # Divide a linha em partes
    partes = linha.split()
    
    if len(partes) < 3:
        return None
    
    # Primeira parte sempre é o código (3 dígitos)
    if not re.match(r'^\d{3}$', partes[0]):
        return None
    
    codigo = partes[0]
    
    # Identifica valores monetários na linha (formato brasileiro com vírgula)
    valores_monetarios = []
    indices_valores = []
    
    for i, parte in enumerate(partes):
        # Valores monetários têm formato: dígitos + vírgula + 2 dígitos
        if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', parte):
            valores_monetarios.append(parte)
            indices_valores.append(i)
    
    if not valores_monetarios:
        return None
    
    # Determina a descrição (tudo entre o código e o primeiro valor)
    if indices_valores:
        inicio_desc = 1
        fim_desc = indices_valores[0]
        descricao = ' '.join(partes[inicio_desc:fim_desc])
    else:
        return None
    
    # Analisa os valores baseado na quantidade encontrada
    if len(valores_monetarios) == 1:
        # Um valor apenas - determina se é vencimento ou desconto baseado na descrição
        valor = valores_monetarios[0]
        if eh_desconto(descricao):
            return {
                "codigo": codigo,
                "descricao": descricao,
                "referencia": None,
                "vencimento": None,
                "desconto": valor,
                "tipo": "desconto_simples"
            }
        else:
            return {
                "codigo": codigo,
                "descricao": descricao,
                "referencia": None,
                "vencimento": valor,
                "desconto": None,
                "tipo": "vencimento_simples"
            }
    
    elif len(valores_monetarios) == 2:
        # Dois valores - primeiro é referência, segundo é valor principal
        referencia = valores_monetarios[0]
        valor_principal = valores_monetarios[1]
        
        if eh_desconto(descricao):
            return {
                "codigo": codigo,
                "descricao": descricao,
                "referencia": referencia,
                "vencimento": None,
                "desconto": valor_principal,
                "tipo": "desconto_com_ref"
            }
        else:
            return {
                "codigo": codigo,
                "descricao": descricao,
                "referencia": referencia,
                "vencimento": valor_principal,
                "desconto": None,
                "tipo": "vencimento_com_ref"
            }
    
    return None


def agrupar_linhas_novo_formato(page, y_tolerance=3):
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
                linhas.append(" ".join([p['text'] for p in linha_atual]))
            linha_atual = [palavra]
            y_ref = palavra['top']
    
    if linha_atual:
        linhas.append(" ".join([p['text'] for p in linha_atual]))
    
    return linhas


def processar_pagina_novo_formato(page):
    """Processa uma página do novo formato e extrai os dados"""
    linhas = agrupar_linhas_novo_formato(page)
    dados = {}
    
    # Extrai o mês/ano
    mes_ano = extrair_mes_ano_novo_formato(linhas)
    if mes_ano:
        dados["MES_ANO"] = mes_ano
        print(f"Mês/Ano encontrado: {mes_ano}")
    else:
        print("Mês/Ano não encontrado")
        return dados
    
    # Processa as linhas da tabela
    dentro_tabela = False
    
    for linha in linhas:
        # Identifica início da tabela
        if "CÓD." in linha and "DESCRIÇÃO" in linha:
            dentro_tabela = True
            print("Iniciando processamento da tabela")
            continue
        
        # Para de processar quando sai da tabela
        if any(palavra in linha for palavra in ["SALÁRIO BASE", "TOTAL DE VENCIMENTOS", "BASE CÁLC"]):
            print("Fim da tabela encontrado")
            dentro_tabela = False
            break
        
        if dentro_tabela:
            dados_linha = parse_linha_tabela_novo_formato(linha)
            if dados_linha:
                print(f"Processando: {dados_linha}")
                
                # Cria chaves para vencimento
                if dados_linha["vencimento"]:
                    chave_venc = f"{dados_linha['codigo']} - {dados_linha['descricao']} [VENCIMENTO]"
                    dados[chave_venc] = dados_linha["vencimento"]
                
                # Cria chaves para desconto
                if dados_linha["desconto"]:
                    chave_desc = f"{dados_linha['codigo']} - {dados_linha['descricao']} [DESCONTO]"
                    dados[chave_desc] = dados_linha["desconto"]
                
                # Salva referência se existir
                if dados_linha["referencia"]:
                    chave_ref = f"{dados_linha['codigo']} - {dados_linha['descricao']} [REFERENCIA]"
                    dados[chave_ref] = dados_linha["referencia"]
    
    print(f"DADOS EXTRAÍDOS DA PÁGINA: {dados}")
    return dados


def ler_pdf_novo_formato_e_gerar_planilha(caminho_pdf, caminho_excel, paginas_a_ler=None):
    """Lê o PDF do novo formato e gera a planilha Excel"""
    dados_consolidados = OrderedDict()
    
    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        paginas_a_ler = paginas_a_ler or range(total_paginas)
        
        for i in paginas_a_ler:
            if i >= total_paginas:
                print(f"Página {i+1} não existe (total: {total_paginas})")
                continue
                
            print(f"\nProcessando página {i+1}/{total_paginas}...")
            pagina = pdf.pages[i]
            dados_pagina = processar_pagina_novo_formato(pagina)
            
            if not dados_pagina.get("MES_ANO"):
                print(f"Página {i+1} não contém dados válidos")
                continue
            
            mes_ano = dados_pagina["MES_ANO"]
            
            if mes_ano not in dados_consolidados:
                dados_consolidados[mes_ano] = dados_pagina.copy()
                print(f"Adicionando dados para {mes_ano}")
            else:
                # Atualiza valores existentes
                for chave, valor in dados_pagina.items():
                    if chave == "MES_ANO":
                        continue
                    
                    if "[VENCIMENTO]" in chave or "[DESCONTO]" in chave:
                        valor_existente = converter_para_float(dados_consolidados[mes_ano].get(chave))
                        novo_valor = converter_para_float(valor)
                        
                        if novo_valor is not None:
                            if (valor_existente is None) or (novo_valor > valor_existente):
                                dados_consolidados[mes_ano][chave] = valor
                                print(f"Atualizando valor em {mes_ano}: {chave} = {valor}")
                    else:
                        dados_consolidados[mes_ano][chave] = valor
    
    # Gera a planilha
    if dados_consolidados:
        df = pd.DataFrame(dados_consolidados.values())
        df.to_excel(caminho_excel, index=False)
        print(f"\n✅ Planilha gerada em: {caminho_excel}")
        print(f"Dados consolidados para {len(df)} períodos:")
        for mes_ano in dados_consolidados.keys():
            print(f"  - {mes_ano}")
    else:
        print("\n⚠️ Nenhum dado válido encontrado.")


if __name__ == "__main__":
    CAMINHO_PDF = r"S:/work/eg-goncalves/pdfs/" + input("Digite o nome do arquivo PDF (ex.: contracheque_fulano.pdf): ")
    CAMINHO_EXCEL = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Digite o nome do arquivo Excel de saída (ex.: resultado.xlsx): ")
    
    pagina_inicial = int(input("Digite o número da página inicial: ")) - 1
    pagina_final = int(input("Digite o número da página final: "))
    
    ler_pdf_novo_formato_e_gerar_planilha(
        CAMINHO_PDF, 
        CAMINHO_EXCEL,
        paginas_a_ler=range(pagina_inicial, pagina_final)
    )