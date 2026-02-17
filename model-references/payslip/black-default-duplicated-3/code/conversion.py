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
        # Procura por "Período da Folha: 06/2024"
        match = re.search(r'Período da Folha:\s+(\d{2}/\d{4})', linha)
        if match:
            return match.group(1)
    return None


def parse_verba_line(linha):
    """
    Extrai dados de uma linha que contém código, descrição, referência e valores
    Padrão esperado: CODIGO DESCRICAO REF VALOR1 VALOR2 (sendo o último sempre o valor principal)
    """
    # Remove espaços extras
    linha = re.sub(r'\s+', ' ', linha.strip())
    
    # Padrão para capturar: código, descrição, referência, e valores monetários
    # Os valores monetários podem ter formato: 123,45 ou 1.234,56
    padrao = r'^(\d+)\s+(.+?)\s+(\d+[,\.]\d+)\s+([\d\.,]+)(?:\s+([\d\.,]+))?$'
    match = re.match(padrao, linha)
    
    if not match:
        # Tenta um padrão mais flexível para casos como "DESC VALE ALIMENTACAO 52,80 52,80"
        padrao_alt = r'^(\d+)?\s*([A-Z\s]+?)\s+([\d\.,]+)\s+([\d\.,]+)$'
        match_alt = re.match(padrao_alt, linha)
        if match_alt:
            codigo = match_alt.group(1) or ""
            descricao = match_alt.group(2).strip()
            referencia = match_alt.group(3)
            valor = match_alt.group(4)
            return {
                "codigo": codigo,
                "descricao": descricao,
                "referencia": referencia,
                "valor": valor
            }
        return None
    
    codigo = match.group(1)
    descricao = match.group(2).strip()
    referencia = match.group(3)
    valor1 = match.group(4)
    valor2 = match.group(5) if match.group(5) else valor1
    
    return {
        "codigo": codigo,
        "descricao": descricao,
        "referencia": referencia,
        "valor": valor2  # Sempre pega o último valor
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
                linhas.append(" ".join([p['text'] for p in linha_atual]))
            linha_atual = [palavra]
            y_ref = palavra['top']
    
    if linha_atual:
        linhas.append(" ".join([p['text'] for p in linha_atual]))
    
    return linhas


def processar_pagina(page):
    """Processa uma página e extrai os dados do contracheque"""
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
    
    # Processa apenas até encontrar "Total Vencimentos" (para evitar duplicatas na mesma página)
    processando = True
    linha_processada = False
    
    for i, linha in enumerate(linhas):
        if not processando:
            break
            
        # Para de processar quando encontrar "Total Vencimentos" (primeira aparição)
        # Ajustado para "Total Vencimentos" conforme exemplo print.txt
        if "Total Vencimentos" in linha and linha_processada:
            print("Parando processamento após primeira aparição de 'Total Vencimentos'")
            processando = False
            break
        
        # Marca que já processou pelo menos uma linha relevante (evita parar antes de começar)
        if "Horas" in linha or "INSS" in linha or any(palavra in linha for palavra in ["Ad.", "Vale", "Salário"]):
            linha_processada = True
        
        # Tenta fazer parse da linha como uma verba
        verba_data = parse_verba_line(linha)
        if verba_data and verba_data["descricao"]:
            print(f"Processando verba: {verba_data}")
            
            # Cria a chave da coluna
            if verba_data["codigo"]:
                chave_coluna = f"{verba_data['codigo']} - {verba_data['descricao']} [VALOR]"
            else:
                chave_coluna = f"{verba_data['descricao']} [VALOR]"
            
            # Verifica se deve atualizar o valor (pega o maior)
            valor_atual = converter_para_float(dados.get(chave_coluna))
            novo_valor = converter_para_float(verba_data["valor"])
            
            if novo_valor is not None:
                if (valor_atual is None) or (novo_valor > valor_atual):
                    dados[chave_coluna] = verba_data["valor"]
                    print(f"Atualizando {chave_coluna}: {verba_data['valor']}")
            
            # Também salva a referência se existir
            if verba_data["referencia"]:
                chave_ref = f"{verba_data['codigo']} - {verba_data['descricao']} [REFERENCIA]" if verba_data["codigo"] else f"{verba_data['descricao']} [REFERENCIA]"
                dados[chave_ref] = verba_data["referencia"]
    
    print(f"DADOS EXTRAÍDOS DA PÁGINA: {dados}")
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
                
            print(f"\nProcessando página {i+1}/{total_paginas}...")
            pagina = pdf.pages[i]
            dados_pagina = processar_pagina(pagina)
            
            if not dados_pagina.get("MES_ANO"):
                print(f"Página {i+1} não contém dados válidos")
                continue
            
            mes_ano = dados_pagina["MES_ANO"]
            
            if mes_ano not in dados_consolidados:
                dados_consolidados[mes_ano] = dados_pagina.copy()
                print(f"Adicionando dados para {mes_ano}")
            else:
                # Atualiza valores existentes com os maiores encontrados
                for chave, valor in dados_pagina.items():
                    if chave == "MES_ANO":
                        continue
                    
                    if "[VALOR]" in chave:
                        valor_existente = converter_para_float(dados_consolidados[mes_ano].get(chave))
                        novo_valor = converter_para_float(valor)
                        
                        if novo_valor is not None:
                            if (valor_existente is None) or (novo_valor > valor_existente):
                                dados_consolidados[mes_ano][chave] = valor
                                print(f"Atualizando valor em {mes_ano}: {chave} = {valor}")
                    else:
                        # Para referências e outros dados, apenas atualiza
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
    import sys
    # Se passar argumentos via linha de comando, usa eles.
    # Caso contrário, solicita input (comportamento original mantido para compatibilidade)
    if len(sys.argv) > 1:
        CAMINHO_PDF = sys.argv[1]
        CAMINHO_EXCEL = sys.argv[2]
        pagina_inicial = 0
        pagina_final = 1000 # Um número grande qualquer
        
        ler_pdf_e_gerar_planilha(CAMINHO_PDF, CAMINHO_EXCEL)
    else:
        CAMINHO_PDF = r"S:/work/eg-goncalves/pdfs/" + input("Digite o nome do arquivo PDF (ex.: contracheque_fulano.pdf): ")
        CAMINHO_EXCEL = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Digite o nome do arquivo Excel de saída (ex.: resultado.xlsx): ")
        
        pagina_inicial = int(input("Digite o número da página inicial: ")) - 1
        pagina_final = int(input("Digite o número da página final: "))
        
        ler_pdf_e_gerar_planilha(
            CAMINHO_PDF, 
            CAMINHO_EXCEL,
            paginas_a_ler=range(pagina_inicial, pagina_final)
        )
