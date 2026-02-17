import pdfplumber
import re
import pandas as pd
from collections import OrderedDict
from typing import Optional, List, Dict, Any


def converter_para_float(valor: str) -> Optional[float]:
    """
    Converte valores monetários no formato brasileiro para float.
    
    Suporta formatos: '1.234,56', '1.234,56-', '-1.234,56', '-1.234,56-'
    """
    if not valor:
        return None
    
    try:
        valor = valor.strip()
        negativo = False
        
        # Verifica se é negativo (início ou fim)
        if valor.startswith('-') or valor.endswith('-'):
            negativo = True
            valor = valor.strip('-')
        
        # Converte para formato float
        resultado = float(valor.replace('.', '').replace(',', '.'))
        return -resultado if negativo else resultado
    except:
        return None


def parse_line_segments(linha: str) -> List[Dict[str, str]]:
    """
    Extrai segmentos de verba de uma linha do contracheque.
    
    Formato esperado: CODIGO DESCRICAO QUANTIDADE VALOR
    """
    padrao_verba = r"^(\S+)\s+(.*?)\s+((?:-?\d{1,3}(?:\.\d{3})*,\d{2}-?\s*)+)$"
    verba_match = re.match(padrao_verba, linha)
    
    if not verba_match:
        return []

    verba = verba_match.group(1)
    descricao = verba_match.group(2).strip()
    numeros = re.findall(r"(-?\d{1,3}(?:\.\d{3})*,\d{2}-?)", verba_match.group(3))

    return [{
        "verba": verba,
        "descricao": descricao,
        "quantidade": numeros[0] if len(numeros) >= 2 else None,
        "valor": numeros[-1]
    }]


def agrupar_linhas(page, y_tolerance: int = 3) -> List[str]:
    """
    Agrupa palavras em linhas baseado na proximidade vertical.
    """
    palavras = page.extract_words()
    palavras.sort(key=lambda w: (w['top'], w['x0']))
    
    linhas = []
    linha_atual = []
    y_ref = None

    for palavra in palavras:
        if y_ref is None or abs(palavra['top'] - y_ref) <= y_tolerance:
            linha_atual.append(palavra)
            y_ref = palavra['top']
        else:
            linhas.append(" ".join([p['text'] for p in linha_atual]))
            linha_atual = [palavra]
            y_ref = palavra['top']

    if linha_atual:
        linhas.append(" ".join([p['text'] for p in linha_atual]))

    return linhas


def encontrar_data_por_linha_abaixo_unidade_organizacional(linhas: List[str]) -> Optional[str]:
    """
    Localiza a data na linha subsequente à "Unidade Organizacional".
    """
    for i, linha in enumerate(linhas):
        if linha.strip().startswith("Unidade Organizacional"):
            if i + 1 < len(linhas):
                linha_abaixo = linhas[i + 1].strip()
                palavras = linha_abaixo.split()
                if palavras:
                    return palavras[-1]
    return None


def processar_pagina(page) -> Dict[str, Any]:
    """
    Processa uma página do PDF extraindo dados de verbas.
    """
    linhas = agrupar_linhas(page)
    dados = {}
    
    # Extrai data da página
    data = encontrar_data_por_linha_abaixo_unidade_organizacional(linhas)
    if data:
        dados["DATA"] = data

    # Processa linhas até encontrar marcadores de parada
    for linha in linhas:
        linha_limpa = linha.strip()
        
        # Para de processar em marcadores específicos
        if linha_limpa == "BASES" or linha_limpa.startswith("TOTAIS"):
            break
            
        segmentos = parse_line_segments(linha)
        for segmento in segmentos:
            chave_base = f"{segmento['verba']} - {segmento['descricao']}"
            
            # Processa quantidade
            if segmento["quantidade"]:
                coluna_quantidade = f"{chave_base} [QUANTIDADE]"
                valor_atual = converter_para_float(dados.get(coluna_quantidade))
                novo_valor = converter_para_float(segmento["quantidade"])
                
                if novo_valor is not None:
                    if (valor_atual is None) or (abs(novo_valor) > abs(valor_atual)):
                        dados[coluna_quantidade] = segmento["quantidade"]
            
            # Processa valor
            coluna_valor = f"{chave_base} [VALOR]"
            valor_atual = converter_para_float(dados.get(coluna_valor))
            novo_valor = converter_para_float(segmento["valor"])
            
            if novo_valor is not None:
                if (valor_atual is None) or (abs(novo_valor) > abs(valor_atual)):
                    dados[coluna_valor] = segmento["valor"]

    return dados


def ler_pdf_e_gerar_planilha(caminho_pdf: str, caminho_excel: str, paginas_a_ler: Optional[range] = None) -> None:
    """
    Lê PDF de contracheques e gera planilha Excel consolidada.
    """
    dados_consolidados = OrderedDict()
    
    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        paginas_a_ler = paginas_a_ler or range(total_paginas)
        
        for i in paginas_a_ler:
            print(f"Processando página {i+1}/{total_paginas}...")
            pagina = pdf.pages[i]
            dados_pagina = processar_pagina(pagina)
            
            if not dados_pagina.get("DATA"):
                continue
                
            data = dados_pagina["DATA"]
            
            if data not in dados_consolidados:
                dados_consolidados[data] = dados_pagina.copy()
            else:
                # Consolida com valores de maior magnitude
                for chave, valor in dados_pagina.items():
                    if chave == "DATA":
                        continue
                        
                    valor_existente = converter_para_float(dados_consolidados[data].get(chave))
                    novo_valor = converter_para_float(valor)
                    
                    if novo_valor is not None:
                        if (valor_existente is None) or (abs(novo_valor) > abs(valor_existente)):
                            dados_consolidados[data][chave] = valor

    # Gera planilha final
    if dados_consolidados:
        df = pd.DataFrame(dados_consolidados.values())
        df.to_excel(caminho_excel, index=False)
        print(f"\n✅ Planilha gerada em: {caminho_excel}")
        print(f"Valores consolidados para {len(df)} registros")
    else:
        print("\n⚠️ Nenhum dado válido encontrado.")


if __name__ == "__main__":
    caminho_pdf = r"S:/work/eg-goncalves/pdfs/" + input("Digite o nome do arquivo PDF (ex.: contracheque_fulano.pdf): ")
    caminho_excel = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Digite o nome do arquivo Excel de saída (ex.: resultado.xlsx): ")
    
    pagina_inicial = int(input("Digite o número da página inicial: ")) - 1
    pagina_final = int(input("Digite o número da página final: "))
    
    ler_pdf_e_gerar_planilha(
        caminho_pdf, 
        caminho_excel,
        paginas_a_ler=range(pagina_inicial, pagina_final)
    )