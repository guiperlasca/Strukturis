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
    """
    Extrai o mês e ano do novo formato
    Procura por padrão "DEMONSTRATIVO DE MM/AAAA"
    """
    for linha in linhas:
        # Procura por "DEMONSTRATIVO DE 03/2021"
        match = re.search(r'DEMONSTRATIVO\s+DE\s+(\d{2})/(\d{4})', linha, re.IGNORECASE)
        if match:
            mes = match.group(1)
            ano = match.group(2)
            return f"{mes}/{ano}"

        # Também procura por padrão direto MM/AAAA após palavras-chave
        if "Mês / Ano" in linha or "DEMONSTRATIVO" in linha:
            match2 = re.search(r'(\d{2})/(\d{4})', linha)
            if match2:
                mes = match2.group(1)
                ano = match2.group(2)
                return f"{mes}/{ano}"

    return None


def eh_desconto(descricao):
    """
    Determina se uma verba é desconto baseado na descrição
    """
    descricoes_desconto = [
        'INSS', 'IRRF', 'IMPOSTO', 'DESCONTO', 'VALE', 'TRANSPORTE',
        'PLANO', 'CONTRIBUI', 'SINDICATO', 'ASSOCIA', 'REFEIÇÃO',
        'ASEHUP', 'ARREDONDAMENTO'
    ]

    descricao_upper = descricao.upper()
    return any(palavra in descricao_upper for palavra in descricoes_desconto)


def parse_linha_tabela_novo_formato(linha):
    """
    Parser para as linhas da tabela do novo formato
    Formato esperado: código (4 dígitos) + descrição + quantidade + valores
    """
    linha = linha.strip()
    linha = re.sub(r'\s+', ' ', linha)

    partes = linha.split()

    if len(partes) < 3:
        return None

    # Primeira parte é o código (4 dígitos)
    if not re.match(r'^\d{4}$', partes[0]):
        return None

    codigo = partes[0]

    # Identifica valores monetários na linha (formato brasileiro)
    valores_monetarios = []
    indices_valores = []

    for i, parte in enumerate(partes):
        # Valores monetários: dígitos + vírgula + 2 dígitos
        if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', parte):
            valores_monetarios.append(parte)
            indices_valores.append(i)

    if not valores_monetarios:
        return None

    # A descrição fica entre o código e o primeiro valor
    if indices_valores:
        inicio_desc = 1
        fim_desc = indices_valores[0]
        descricao = ' '.join(partes[inicio_desc:fim_desc])
    else:
        return None

    # Analisa os valores
    # No novo formato, temos: QTDE + VENCIMENTOS ou DESCONTOS

    if len(valores_monetarios) == 1:
        # Um valor apenas - pode ser quantidade+vencimento ou quantidade+desconto
        valor = valores_monetarios[0]

        # O primeiro valor pode ser a quantidade (não monetário no sentido de centavos)
        # Mas aqui tratamos valores com vírgula, então é um valor monetário

        if eh_desconto(descricao):
            return {
                "codigo": codigo,
                "descricao": descricao,
                "quantidade": None,
                "vencimento": None,
                "desconto": valor,
                "tipo": "desconto_simples"
            }
        else:
            return {
                "codigo": codigo,
                "descricao": descricao,
                "quantidade": None,
                "vencimento": valor,
                "desconto": None,
                "tipo": "vencimento_simples"
            }

    elif len(valores_monetarios) == 2:
        # Dois valores - primeiro é quantidade, segundo é vencimento ou desconto
        quantidade = valores_monetarios[0]
        valor_principal = valores_monetarios[1]

        if eh_desconto(descricao):
            return {
                "codigo": codigo,
                "descricao": descricao,
                "quantidade": quantidade,
                "vencimento": None,
                "desconto": valor_principal,
                "tipo": "desconto_com_qtde"
            }
        else:
            return {
                "codigo": codigo,
                "descricao": descricao,
                "quantidade": quantidade,
                "vencimento": valor_principal,
                "desconto": None,
                "tipo": "vencimento_com_qtde"
            }

    elif len(valores_monetarios) == 3:
        # Três valores - quantidade + vencimento + desconto (linha completa)
        quantidade = valores_monetarios[0]
        vencimento = valores_monetarios[1]
        desconto = valores_monetarios[2]

        return {
            "codigo": codigo,
            "descricao": descricao,
            "quantidade": quantidade,
            "vencimento": vencimento,
            "desconto": desconto,
            "tipo": "completo"
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
        # Identifica início da tabela (novo formato usa "COD. Descrição QTDE.")
        if ("COD." in linha or "Descrição" in linha) and ("VENCIMENTOS" in linha or "DESCONTOS" in linha):
            dentro_tabela = True
            print("Iniciando processamento da tabela")
            continue

        # Para de processar quando encontra "TOTAIS"
        if "TOTAIS" in linha:
            print("Fim da tabela encontrado (TOTAIS)")
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

                # Salva quantidade se existir
                if dados_linha["quantidade"]:
                    chave_qtde = f"{dados_linha['codigo']} - {dados_linha['descricao']} [QUANTIDADE]"
                    dados[chave_qtde] = dados_linha["quantidade"]

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