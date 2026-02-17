
import pdfplumber
import re
import pandas as pd
from collections import OrderedDict
import sys

def converter_para_float(valor):
    """Converte "2.120,00" para 2120.00"""
    if not valor:
        return None
    try:
        valor = valor.strip().replace('.', '').replace(',', '.')
        return float(valor)
    except ValueError:
        return None

def parse_mes_ano(texto):
    """Converte JAN/2025 para 01/2025"""
    meses = {
        'JAN': '01', 'FEV': '02', 'MAR': '03', 'ABR': '04', 'MAI': '05', 'JUN': '06',
        'JUL': '07', 'AGO': '08', 'SET': '09', 'OUT': '10', 'NOV': '11', 'DEZ': '12'
    }
    match = re.search(r'([A-Z]{3})/(\d{4})', texto)
    if match:
        mes_nome, ano = match.groups()
        if mes_nome in meses:
            return f"{meses[mes_nome]}/{ano}"
    return None

def processar_pagina(page):
    text = page.extract_text()
    if not text:
        return {}
    
    linhas = text.split('\n')
    dados = {}
    mes_ano = None
    encontrou_base = False
    
    # Busca Mês/Ano (REFERÊNCIA)
    # Ex: ERC1151001 341 341 00000067201-2 2.120,00/MES JAN/2025
    
    for linha in linhas:
        # Tenta achar o Mês/Ano
        if not mes_ano:
            # Padrão JAN/2025 isolado ou no fim da linha
            match_data = re.search(r'\b(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(\d{4})\b', linha)
            if match_data:
                mes_ano = parse_mes_ano(match_data.group(0))

        # Verifica divisor de seção
        if "BASE/OUTROS" in linha:
            encontrou_base = True
            break
            
        # Processa linha de verba
        # Ex: 0010 Salário Base | 220,00 | 2.120,00 |
        if '|' in linha:
            parts = [p.strip() for p in linha.split('|')]
            # Esperamos pelo menos código+descrição
            if len(parts) < 2:
                continue
            
            # Parte 0 deve ter o código e descrição
            # Ex: "0010 Salário Base"
            # Regex para separar código numérico do resto
            match_cod = re.match(r'^(\d+)\s+(.+)$', parts[0])
            if match_cod:
                codigo = match_cod.group(1)
                descricao = match_cod.group(2).strip()
                
                # Mapeamento das colunas baseado na observação do print.txt:
                # 0: Cod Desc
                # 1: Ref (QTDE.v1)
                # 2: Vencimentos
                # 3: Descontos
                
                ref = parts[1] if len(parts) > 1 else ""
                venc = parts[2] if len(parts) > 2 else ""
                desc = parts[3] if len(parts) > 3 else ""
                
                valor_final = 0.0
                
                # Se tiver vencimento, usa (positivo)
                # Se tiver desconto, usa (negativo)
                
                val_venc = converter_para_float(venc)
                val_desc = converter_para_float(desc)
                
                if val_venc is not None:
                    valor_final = val_venc
                elif val_desc is not None:
                    valor_final = -val_desc
                else:
                    # Se não tem valor monetário, talvez seja só referência ou nada
                    valor_final = None

                # Salva [VALOR]
                if valor_final is not None:
                    chave_val = f"{codigo} - {descricao} [VALOR]"
                    # Se já existe, checa qual manter? Geralmente não duplica na mesma página desse jeito
                    dados[chave_val] = valor_final
                
                # Salva [REFERENCIA] se existir
                val_ref = converter_para_float(ref)
                if val_ref is not None:
                    chave_ref = f"{codigo} - {descricao} [REFERENCIA]"
                    dados[chave_ref] = val_ref

    if not encontrou_base:
        return {}

    if mes_ano:
        dados["MES_ANO"] = mes_ano
    
    return dados

def ler_pdf_e_gerar_planilha(caminho_pdf, caminho_excel, paginas_a_ler=None):
    dados_consolidados = OrderedDict()
    
    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        paginas_a_ler = paginas_a_ler or range(total_paginas)
        
        for i in paginas_a_ler:
            if i >= total_paginas:
                continue
            
            print(f"Processando página {i+1}...")
            pagina = pdf.pages[i]
            


            dados_pagina = processar_pagina(pagina)
            
            mes_ano = dados_pagina.get("MES_ANO")
            if not mes_ano:
                print(f"Página {i+1}: Data não encontrada.")
                continue
            
            # Consolidação
            if mes_ano not in dados_consolidados:
                dados_consolidados[mes_ano] = dados_pagina.copy()
            else:
                # Atualiza com valores novos (assumindo que se tiver duplicado pega o último ou funde?)
                # Normalmente, se é o mesmo mês, pode ser folha complementar ou só outra página.
                dados_consolidados[mes_ano].update(dados_pagina)
    
    # Gera Excel
    if dados_consolidados:
        df = pd.DataFrame(dados_consolidados.values())
        # Ordena colunas para ficar bonito
        cols = sorted(list(df.columns))
        # Move MES_ANO para frente
        if "MES_ANO" in cols:
            cols.insert(0, cols.pop(cols.index("MES_ANO")))
        
        df = df[cols]
        df.to_excel(caminho_excel, index=False)
        print(f"Gerado: {caminho_excel}")
    else:
        print("Nenhum dado extraído.")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        pdf_in = sys.argv[1]
        xlsx_out = sys.argv[2]
        
        # Paginas especificas se fornecidas
        if len(sys.argv) > 4:
            p_ini = int(sys.argv[3]) - 1
            p_fim = int(sys.argv[4])
            rng = range(p_ini, p_fim)
        else:
            rng = None
            
        ler_pdf_e_gerar_planilha(pdf_in, xlsx_out, rng)
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
