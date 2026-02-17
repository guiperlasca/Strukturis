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


def extrair_data_periodo(linhas: List[str]) -> Optional[str]:
    """
    Extrai a data do período do contracheque (formato DD.MM.YYYY).
    
    Procura na linha que contém o CNPJ e extrai a data após "Período até".
    """
    for linha in linhas:
        # Procura padrão de data DD.MM.YYYY
        match = re.search(r'(\d{2}\.\d{2}\.\d{4})', linha)
        if match:
            data_raw = match.group(1)
            # Converte de DD.MM.YYYY para MM/YYYY
            partes = data_raw.split('.')
            if len(partes) == 3:
                return f"{partes[1]}/{partes[2]}"  # MM/YYYY
    return None


def parse_linha_rubrica(linha: str) -> Optional[Dict[str, str]]:
    """
    Extrai dados de uma linha de rubrica do contracheque.
    
    Formato esperado: CODIGO DESCRICAO [PROVENTO] [DESCONTO] [QTDE] [VALOR_UNIT]
    """
    linha = linha.strip()
    if not linha:
        return None
    
    # Padrão: código alfanumérico (ex: M389, /T20, 1010, MT50) seguido de descrição e valores
    # Códigos começam com letra, número ou /
    match_codigo = re.match(r'^([A-Z0-9/][A-Z0-9]*)\s+(.+)$', linha, re.IGNORECASE)
    
    if not match_codigo:
        return None
    
    codigo = match_codigo.group(1)
    resto = match_codigo.group(2)
    
    # Encontra todos os valores monetários no formato brasileiro (com vírgula)
    valores = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', resto)
    
    if not valores:
        return None
    
    # Remove os valores do resto para obter a descrição
    descricao = resto
    for valor in valores:
        descricao = descricao.replace(valor, '').strip()
    
    # Limpa espaços extras da descrição
    descricao = re.sub(r'\s+', ' ', descricao).strip()
    
    # Estrutura do contracheque STIHL blue-default-2:
    # Rubr | Descrição | $ Provent | $ Descto | Qtde | $ Unit
    # Pode ter 2, 3 ou 4 valores numéricos
    provento = None
    desconto = None
    quantidade = None
    valor_unitario = None
    
    if len(valores) >= 1:
        # Determina se é provento ou desconto baseado no código ou descrição
        primeiro_valor = valores[0]
        if len(valores) == 1:
            # Apenas um valor - verifica se é desconto ou provento
            if eh_desconto(codigo, descricao):
                desconto = primeiro_valor
            else:
                provento = primeiro_valor
        elif len(valores) == 2:
            # Pode ser: provento + qtde, desconto + qtde, ou provento + desconto
            if eh_desconto(codigo, descricao):
                desconto = valores[0]
                quantidade = valores[1]
            else:
                provento = valores[0]
                quantidade = valores[1]
        elif len(valores) == 3:
            # Provento ou Desconto + Qtde + Valor unitário
            if eh_desconto(codigo, descricao):
                desconto = valores[0]
            else:
                provento = valores[0]
            quantidade = valores[1]
            valor_unitario = valores[2]
        elif len(valores) >= 4:
            # Provento + Desconto + Qtde + Valor unitário
            provento = valores[0] if valores[0] != '0,00' else None
            desconto = valores[1] if valores[1] != '0,00' else None
            quantidade = valores[2]
            valor_unitario = valores[3]
    
    return {
        "codigo": codigo,
        "descricao": descricao,
        "provento": provento,
        "desconto": desconto,
        "quantidade": quantidade,
        "valor_unitario": valor_unitario
    }


def eh_desconto(codigo: str, descricao: str) -> bool:
    """Determina se uma verba é desconto baseado no código ou descrição."""
    # Códigos que indicam desconto começam com / ou são específicos
    codigos_desconto = ['/314', '/401', '/B02', '/T35', '/500', '/501', '/560']
    descricoes_desconto = [
        'INSS', 'IRRF', 'IMPOSTO', 'TRIBUTO', 'DESCONTO', 'ADTO', 'ADIANTAMENTO',
        'VALE', 'PLANO', 'EMPRESTIMO', 'EMPRÉSTIMO', 'SAÚDE', 'SAUDE', 
        'SINDICATO', 'SINDICAL', 'ONIBUS', 'ÔNIBUS', 'CO-PARTIC', 'COPARTIC',
        'FALTAS', 'FALTA', 'REFEIÇÃO', 'REFEICAO', 'MENSALIDADE'
    ]
    
    codigo_upper = codigo.upper()
    if codigo_upper in [c.upper() for c in codigos_desconto]:
        return True
    
    if codigo_upper.startswith('/'):
        return True
    
    descricao_upper = descricao.upper()
    return any(palavra in descricao_upper for palavra in descricoes_desconto)


def agrupar_linhas(page, y_tolerance: int = 3) -> List[str]:
    """
    Agrupa palavras em linhas baseado na proximidade vertical.
    """
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
            linhas.append(" ".join([p['text'] for p in linha_atual]))
            linha_atual = [palavra]
            y_ref = palavra['top']

    if linha_atual:
        linhas.append(" ".join([p['text'] for p in linha_atual]))

    return linhas


def processar_pagina(page) -> Dict[str, Any]:
    """
    Processa uma página do PDF extraindo dados de verbas.
    """
    linhas = agrupar_linhas(page)
    dados = {}
    
    # Extrai data da página
    data = extrair_data_periodo(linhas)
    if data:
        dados["MES_ANO"] = data
        print(f"Data encontrada: {data}")
    else:
        print("Data não encontrada")
        return dados

    # Processa linhas de rubricas
    dentro_tabela = False
    
    for linha in linhas:
        linha_limpa = linha.strip()
        
        # Identifica início da tabela de rubricas
        if "Rubr" in linha and "Descri" in linha and "Provent" in linha:
            dentro_tabela = True
            print("Iniciando processamento da tabela de rubricas")
            continue
        
        # Para de processar em marcadores específicos
        if "Vencimentos" in linha_limpa and "Descontos" in linha_limpa and "Líquido" in linha_limpa:
            print("Fim da tabela encontrado")
            dentro_tabela = False
            break
        
        if "Mensagens Adicionais" in linha_limpa:
            dentro_tabela = False
            break
            
        if dentro_tabela:
            dados_linha = parse_linha_rubrica(linha)
            if dados_linha:
                chave_base = f"{dados_linha['codigo']} - {dados_linha['descricao']}"
                
                # Adiciona provento
                if dados_linha['provento']:
                    chave_provento = f"{chave_base} [PROVENTO]"
                    valor_existente = converter_para_float(dados.get(chave_provento))
                    novo_valor = converter_para_float(dados_linha['provento'])
                    
                    if novo_valor is not None:
                        if (valor_existente is None) or (abs(novo_valor) > abs(valor_existente)):
                            dados[chave_provento] = dados_linha['provento']
                
                # Adiciona desconto
                if dados_linha['desconto']:
                    chave_desconto = f"{chave_base} [DESCONTO]"
                    valor_existente = converter_para_float(dados.get(chave_desconto))
                    novo_valor = converter_para_float(dados_linha['desconto'])
                    
                    if novo_valor is not None:
                        if (valor_existente is None) or (abs(novo_valor) > abs(valor_existente)):
                            dados[chave_desconto] = dados_linha['desconto']
                
                # Adiciona quantidade
                if dados_linha['quantidade']:
                    chave_qtde = f"{chave_base} [QUANTIDADE]"
                    valor_existente = converter_para_float(dados.get(chave_qtde))
                    novo_valor = converter_para_float(dados_linha['quantidade'])
                    
                    if novo_valor is not None:
                        if (valor_existente is None) or (abs(novo_valor) > abs(valor_existente)):
                            dados[chave_qtde] = dados_linha['quantidade']
                
                # Adiciona valor unitário
                if dados_linha['valor_unitario']:
                    chave_unit = f"{chave_base} [VALOR_UNITARIO]"
                    dados[chave_unit] = dados_linha['valor_unitario']
    
    print(f"DADOS EXTRAÍDOS DA PÁGINA: {len(dados)} campos")
    return dados


def ler_pdf_e_gerar_planilha(caminho_pdf: str, caminho_excel: str, paginas_a_ler: Optional[range] = None) -> None:
    """
    Lê PDF de contracheques STIHL (blue-default-2) e gera planilha Excel consolidada.
    """
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
                # Consolida com valores de maior magnitude
                for chave, valor in dados_pagina.items():
                    if chave == "MES_ANO":
                        continue
                        
                    valor_existente = converter_para_float(dados_consolidados[mes_ano].get(chave))
                    novo_valor = converter_para_float(valor)
                    
                    if novo_valor is not None:
                        if (valor_existente is None) or (abs(novo_valor) > abs(valor_existente)):
                            dados_consolidados[mes_ano][chave] = valor
                            print(f"Atualizando valor em {mes_ano}: {chave} = {valor}")

    # Gera planilha final
    if dados_consolidados:
        df = pd.DataFrame(dados_consolidados.values())
        df.to_excel(caminho_excel, index=False)
        print(f"\n✅ Planilha gerada em: {caminho_excel}")
        print(f"Valores consolidados para {len(df)} registros:")
        for mes_ano in dados_consolidados.keys():
            print(f"  - {mes_ano}")
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
