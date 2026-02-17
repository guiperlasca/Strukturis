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
        match = re.search(r'Competência\s+(\d{2}/\d{4})', linha)
        if match:
            return match.group(1)
    return None

def parse_verba_line(linha):
    """
    Extrai dados de uma linha que contém código, descrição, quantidade opcional e valor
    Padrão: CÓD DESCRIÇÃO [QUANTIDADE] [VALOR]
    """
    linha = re.sub(r'\s{2,}', ' ', linha.strip())
    # Padrão com horas/dias e valor
    padrao = r'^(\d{3})\s+(.+?)\s+([\d\.,]+)\s+([\d\.,]+)$'
    match = re.match(padrao, linha)
    if match:
        codigo = match.group(1)
        descricao = match.group(2).strip()
        quant = match.group(3)
        valor = match.group(4)
        return {"codigo": codigo, "descricao": descricao, "quantidade": quant, "valor": valor}
    # Padrão sem quantidade, só valor
    padrao2 = r'^(\d{3})\s+(.+?)\s+([\d\.,]+)$'
    match2 = re.match(padrao2, linha)
    if match2:
        codigo = match2.group(1)
        descricao = match2.group(2).strip()
        valor = match2.group(3)
        return {"codigo": codigo, "descricao": descricao, "quantidade": None, "valor": valor}
    return None

def agrupar_linhas(page, y_tolerance=3):
    """Agrupa palavras em linhas baseado na posição Y"""
    palavras = page.extract_words()
    if not palavras:
        return []
    palavras.sort(key=lambda w: (w['top'], w['x0']))
    linhas = []
    linha_atual = []
    y_ref = None
    for p in palavras:
        if y_ref is None or abs(p['top'] - y_ref) <= y_tolerance:
            linha_atual.append(p)
            y_ref = p['top']
        else:
            linhas.append(" ".join(w['text'] for w in linha_atual))
            linha_atual = [p]
            y_ref = p['top']
    if linha_atual:
        linhas.append(" ".join(w['text'] for w in linha_atual))
    return linhas

def processar_pagina(page):
    """Processa uma página e extrai os dados do contracheque"""
    linhas = agrupar_linhas(page)
    dados = {}
    mes_ano = extrair_mes_ano(linhas)
    if mes_ano:
        dados["MES_ANO"] = mes_ano
    else:
        return {}

    for linha in linhas:
        verba = parse_verba_line(linha)
        if verba:
            desc = verba["descricao"]
            cod = verba["codigo"]
            # chave valor
            chave_val = f"{cod} - {desc} [VALOR]"
            # valor
            dados[chave_val] = verba["valor"]
            # se houver quantidade
            if verba["quantidade"]:
                chave_qtd = f"{cod} - {desc} [QUANTIDADE]"
                dados[chave_qtd] = verba["quantidade"]
    return dados

def ler_pdf_e_gerar_planilha(caminho_pdf, caminho_excel, paginas_a_ler=None):
    dados_consolidados = OrderedDict()
    with pdfplumber.open(caminho_pdf) as pdf:
        total = len(pdf.pages)
        paginas = paginas_a_ler or range(total)
        for i in paginas:
            if i >= total:
                continue
            page = pdf.pages[i]
            dados_p = processar_pagina(page)
            if not dados_p.get("MES_ANO"):
                continue
            mes = dados_p.pop("MES_ANO")
            if mes not in dados_consolidados:
                dados_consolidados[mes] = dados_p.copy()
            else:
                for k,v in dados_p.items():
                    if "[VALOR]" in k:
                        atual = converter_para_float(dados_consolidados[mes].get(k))
                        novo = converter_para_float(v)
                        if novo is not None and (atual is None or novo>atual):
                            dados_consolidados[mes][k]=v
                    else:
                        dados_consolidados[mes][k]=v
    if dados_consolidados:
        df = pd.DataFrame(dados_consolidados.values())
        df.insert(0, "MES_ANO", list(dados_consolidados.keys()))
        df.to_excel(caminho_excel, index=False)
        print(f"Planilha gerada: {caminho_excel}")
    else:
        print("Nenhum dado válido encontrado.")

if __name__ == "__main__":
    pdf_file = input("Nome do arquivo PDF: ")
    xlsx_file = input("Nome do arquivo Excel de saída: ")
    ini = int(input("Página inicial: ")) - 1
    fim = int(input("Página final: "))
    ler_pdf_e_gerar_planilha(pdf_file, xlsx_file, paginas_a_ler=range(ini, fim))
