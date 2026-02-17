"""
Conversão de contracheques formato BLACK-SECRECY-1
Formato com 3 colunas: REMUNERAÇÕES, DESCONTOS, BASES
- Primeiro limpa o PDF (remove textos de sigilo/visibilidade)
- Depois extrai apenas REMUNERAÇÕES e DESCONTOS (ignora BASES)
"""

import pdfplumber
import fitz  # PyMuPDF
import re
import pandas as pd
from collections import OrderedDict
import os
import sys
import tempfile

# Adiciona o caminho para importar o módulo de limpeza
sys.path.insert(0, r"S:\work\eg-goncalves\programas\scanned_pdfs_conversion")


def limpar_pdf_sigilo(pdf_path, output_path=None):
    """
    Remove os textos de sigilo e visibilidade do PDF.
    Retorna o caminho do PDF limpo.
    """
    if output_path is None:
        # Cria arquivo temporário
        base, ext = os.path.splitext(pdf_path)
        output_path = f"{base}_limpo{ext}"
    
    print(f"🧹 Limpando PDF: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    total_removed = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page.clean_contents()
        
        for xref in page.get_contents():
            stream = doc.xref_stream(xref)
            if stream:
                decoded = stream.decode('latin-1')
                original_len = len(decoded)
                
                # Padrão 1: "Documento em sigilo" (fonte 40pt)
                pattern_sigilo = r'BT/F1\s+40\s+Tf\s+[^<]+<446f63756d656e746f20656d20736967696c6f[^>]*>Tj\s+ET'
                
                # Padrão 2: "Usuário em visibilidade: ..." (fonte 24pt)
                pattern_usuario = r'BT/F1\s+24\s+Tf\s+[^<]+<557375[^>]*>Tj\s+ET'
                
                modified = re.sub(pattern_sigilo, '', decoded)
                modified = re.sub(pattern_usuario, '', modified)
                
                if len(modified) != original_len:
                    total_removed += 1
                    doc.update_stream(xref, modified.encode('latin-1'))
    
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    
    print(f"✅ PDF limpo ({total_removed} páginas processadas): {output_path}")
    return output_path


def converter_para_float(valor):
    """Converte valores no formato '1.234,56' para float"""
    if not valor:
        return None
    try:
        valor = valor.strip()
        if valor.endswith('-'):
            valor = '-' + valor[:-1]
        return float(valor.replace('.', '').replace(',', '.'))
    except:
        return None


def extrair_mes_ano(linhas):
    """Extrai o mês e ano do cabeçalho - formato 'Mês/Ano' ou 'MM/AAAA'"""
    meses = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'marco': '03',
        'abril': '04', 'maio': '05', 'junho': '06',
        'julho': '07', 'agosto': '08', 'setembro': '09',
        'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }
    
    for linha in linhas:
        # Procura por "Mês/Ano" (ex: "Maio/2021")
        for mes_nome, mes_num in meses.items():
            pattern = rf'{mes_nome}/(\d{{4}})'
            match = re.search(pattern, linha, re.IGNORECASE)
            if match:
                ano = match.group(1)
                return f"{mes_num}/{ano}"
        
        # Procura por MM/AAAA
        match = re.search(r'(\d{2})/(\d{4})', linha)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    
    return None


def separar_entradas_linha(linha):
    """
    Separa as entradas concatenadas de uma linha.
    
    Exemplo de entrada:
    "001 ADTO VALE TRANSPORTE 0.00 391,30401 INSS 0.00 267,13706 BASE I.R. SALARIO 0.00 2.647,37"
    
    Deve separar em:
    - "001 ADTO VALE TRANSPORTE 0.00 391,30"
    - "401 INSS 0.00 267,13"
    - "706 BASE I.R. SALARIO 0.00 2.647,37"
    
    O padrão é: após um valor monetário (dígitos,dois_dígitos), vem um código de 3 dígitos
    """
    
    # Regex para encontrar pontos de separação:
    # valor monetário seguido imediatamente de código de 3 dígitos
    # Exemplo: "391,30401" -> separar entre "391,30" e "401"
    
    # Padrão: dígitos + vírgula + 2 dígitos + 3 dígitos (código)
    # Substitui por: valor + separador + código
    pattern = r'(\d{1,3}(?:\.\d{3})*,\d{2})(\d{3}\s)'
    
    # Adiciona um separador único entre valor e código
    separador = '|||'
    linha_separada = re.sub(pattern, rf'\1{separador}\2', linha)
    
    # Divide pelas separações
    entradas = linha_separada.split(separador)
    
    return [e.strip() for e in entradas if e.strip()]


def parse_entrada(entrada):
    """
    Parseia uma entrada individual no formato:
    "CODE DESCRIÇÃO QTD VALOR"
    
    Exemplo: "001 ADTO VALE TRANSPORTE 0.00 391,30"
    Retorna: {"codigo": "001", "descricao": "ADTO VALE TRANSPORTE", "qtd": "0.00", "valor": "391,30"}
    """
    entrada = entrada.strip()
    partes = entrada.split()
    
    if len(partes) < 3:
        return None
    
    # Primeira parte deve ser código de 3 dígitos
    if not re.match(r'^\d{3}$', partes[0]):
        return None
    
    codigo = partes[0]
    
    # Encontra valores monetários (formato brasileiro)
    valores = []
    indices_valores = []
    
    for i, parte in enumerate(partes):
        if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', parte):
            valores.append(parte)
            indices_valores.append(i)
    
    if not valores:
        return None
    
    # Encontra quantidade (número com ponto como decimal, ex: 0.00, 29.00)
    qtd = None
    idx_qtd = None
    for i, parte in enumerate(partes[1:], 1):
        if re.match(r'^\d+\.\d{2}$', parte):
            qtd = parte
            idx_qtd = i
            break
    
    # Descrição é tudo entre código e quantidade (ou primeiro valor)
    if idx_qtd:
        descricao = ' '.join(partes[1:idx_qtd])
    elif indices_valores:
        descricao = ' '.join(partes[1:indices_valores[0]])
    else:
        descricao = ' '.join(partes[1:])
    
    # Último valor é o valor principal
    valor = valores[-1] if valores else None
    
    return {
        "codigo": codigo,
        "descricao": descricao,
        "qtd": qtd,
        "valor": valor
    }


def eh_linha_dados(linha):
    """Verifica se a linha contém dados de verba (começa com código de 3 dígitos)"""
    linha = linha.strip()
    return bool(re.match(r'^\d{3}\s', linha))


def classificar_verba(codigo, descricao):
    """
    Classifica se a verba é REMUNERAÇÃO ou DESCONTO baseado no código e descrição.
    
    Códigos típicos:
    - 0xx, 1xx, 2xx, 3xx: geralmente REMUNERAÇÕES
    - 4xx, 5xx: geralmente DESCONTOS
    - 7xx, 8xx: geralmente BASES (mas não queremos essas)
    """
    codigo_int = int(codigo)
    descricao_upper = descricao.upper()
    
    # Palavras-chave de desconto
    palavras_desconto = [
        'INSS', 'I.R.', 'IR ', 'IRRF', 'IMPOSTO', 'DESCONTO', 'DESC ',
        'VALE-REFEICAO', 'VALE REFEICAO', 'VALE-TRANSPORTE', 'VALE TRANSPORTE',
        'ADIANTAMENTO', 'ADTO', 'SINDICATO', 'CONTRIBUI', 'PLANO', 'CESTA',
        'ARRED.ANTERIOR', 'DESC ADI'
    ]
    
    # Palavras-chave de base (para ignorar)
    palavras_base = [
        'BASE ', 'LIMITE', 'F.G.T.S', 'FGTS', '% INSS', 'DED INSS',
        'LIQUIDO A RECEBER', 'BASE SALARIO', 'LIQ VALORES',
        'PTE EMPRESA', 'PTE.EMPRESA', 'RECOLHER'
    ]
    
    # Se tem palavra de base, ignorar
    if any(p in descricao_upper for p in palavras_base):
        return "BASE"
    
    # Se código >= 700, provavelmente é BASE
    if codigo_int >= 700:
        return "BASE"
    
    # Se tem palavra de desconto, é DESCONTO
    if any(p in descricao_upper for p in palavras_desconto):
        return "DESCONTO"
    
    # Códigos 4xx e 5xx são tipicamente descontos
    if 400 <= codigo_int < 600:
        return "DESCONTO"
    
    # O resto é remuneração
    return "REMUNERAÇÃO"


def processar_pagina(page):
    """Processa uma página e extrai os dados de remuneração e desconto"""
    
    # Extrai texto da página
    texto = page.extract_text()
    if not texto:
        return {}
    
    linhas = texto.split('\n')
    dados = {}
    
    # Extrai mês/ano
    mes_ano = extrair_mes_ano(linhas)
    if mes_ano:
        dados["MES_ANO"] = mes_ano
        print(f"  📅 Mês/Ano: {mes_ano}")
    else:
        print("  ⚠️ Mês/Ano não encontrado")
        return {}
    
    # Processa linhas de dados
    dentro_tabela = False
    
    for linha in linhas:
        # Detecta início da tabela
        if 'R E M U N E R A' in linha or 'REMUNERAÇ' in linha.upper():
            dentro_tabela = True
            continue
        
        # Detecta fim da tabela
        if 'TOTAL BRUTO' in linha.upper():
            dentro_tabela = False
            # Extrai totais
            match_bruto = re.search(r'TOTAL BRUTO[:\s]+([0-9.,]+)', linha, re.IGNORECASE)
            match_desc = re.search(r'TOTAL DE DESCONTOS[:\s]+([0-9.,]+)', linha, re.IGNORECASE)
            if match_bruto:
                dados["TOTAL_BRUTO"] = match_bruto.group(1)
            if match_desc:
                dados["TOTAL_DESCONTOS"] = match_desc.group(1)
            continue
        
        # Processa linhas de dados
        if dentro_tabela and eh_linha_dados(linha):
            # Separa as entradas da linha
            entradas = separar_entradas_linha(linha)
            
            # Remove o último item (sempre é BASE quando há mais de 1)
            if len(entradas) > 1:
                entradas = entradas[:-1]
            elif len(entradas) == 1:
                # Se só tem um item, verifica se é BASE (código >= 700 ou descrição de base)
                entrada = parse_entrada(entradas[0])
                if entrada:
                    tipo = classificar_verba(entrada["codigo"], entrada["descricao"])
                    if tipo == "BASE":
                        continue  # Pula bases
                    # Se não é base e está sozinho na linha, é DESCONTO
                    # (os descontos extras aparecem sozinhos nas linhas finais)
            
            # Processa cada entrada pela POSIÇÃO na linha
            for idx, entrada_str in enumerate(entradas):
                entrada = parse_entrada(entrada_str)
                if not entrada:
                    continue
                
                # Verifica se é BASE mesmo após remoção do último
                tipo_verba = classificar_verba(entrada["codigo"], entrada["descricao"])
                if tipo_verba == "BASE":
                    continue  # Ignora bases que escaparam
                
                # Determina tipo pela POSIÇÃO:
                # - 1ª entrada (idx=0) = REMUNERAÇÃO (quando há 2+ entradas)
                # - 2ª entrada (idx=1) = DESCONTO
                # - Entrada única = DESCONTO (geralmente são descontos extras)
                if len(entradas) >= 2:
                    if idx == 0:
                        tipo = "REMUNERAÇÃO"
                    else:
                        tipo = "DESCONTO"
                else:
                    # Entrada única - provavelmente desconto
                    tipo = "DESCONTO"
                
                # Cria chave para o dado - usa apenas [VALOR]
                chave = f"{entrada['codigo']} - {entrada['descricao']} [VALOR]"
                dados[chave] = entrada["valor"]
                
                # Salva referência/quantidade se existir
                if entrada.get("qtd") and entrada["qtd"] != "0.00":
                    chave_ref = f"{entrada['codigo']} - {entrada['descricao']} [REFERÊNCIA]"
                    dados[chave_ref] = entrada["qtd"]
    
    return dados


def processar_pdf(caminho_pdf, caminho_excel, paginas_a_ler=None, limpar=True):
    """
    Processa o PDF e gera a planilha Excel.
    
    Args:
        caminho_pdf: Caminho do PDF original
        caminho_excel: Caminho do Excel de saída
        paginas_a_ler: Range de páginas (0-indexed) ou None para todas
        limpar: Se True, limpa o PDF antes de processar
    """
    
    # Primeiro limpa o PDF se necessário
    if limpar:
        pdf_limpo = limpar_pdf_sigilo(caminho_pdf)
    else:
        pdf_limpo = caminho_pdf
    
    print(f"\n📖 Extraindo dados de: {pdf_limpo}")
    print("-" * 50)
    
    dados_consolidados = OrderedDict()
    
    with pdfplumber.open(pdf_limpo) as pdf:
        total_paginas = len(pdf.pages)
        paginas_a_ler = paginas_a_ler or range(total_paginas)
        
        for i in paginas_a_ler:
            if i >= total_paginas:
                print(f"⚠️ Página {i+1} não existe (total: {total_paginas})")
                continue
            
            print(f"\n📄 Página {i+1}/{total_paginas}")
            pagina = pdf.pages[i]
            dados_pagina = processar_pagina(pagina)
            
            if not dados_pagina.get("MES_ANO"):
                print(f"  ⚠️ Página sem dados válidos")
                continue
            
            mes_ano = dados_pagina["MES_ANO"]
            
            if mes_ano not in dados_consolidados:
                dados_consolidados[mes_ano] = dados_pagina.copy()
                print(f"  ✅ Novo período: {mes_ano}")
            else:
                # Atualiza valores existentes
                for chave, valor in dados_pagina.items():
                    if chave == "MES_ANO":
                        continue
                    
                    if "[VALOR]" in chave or "[REFERÊNCIA]" in chave:
                        valor_existente = converter_para_float(dados_consolidados[mes_ano].get(chave))
                        novo_valor = converter_para_float(valor)
                        
                        if novo_valor is not None:
                            if valor_existente is None or novo_valor > valor_existente:
                                dados_consolidados[mes_ano][chave] = valor
                    else:
                        dados_consolidados[mes_ano][chave] = valor
    
    # Gera a planilha
    if dados_consolidados:
        df = pd.DataFrame(dados_consolidados.values())
        
        # Reordena colunas: MES_ANO primeiro, depois TOTAIS no final
        colunas = list(df.columns)
        ordem = ['MES_ANO']
        ordem += [c for c in colunas if c not in ['MES_ANO', 'TOTAL_BRUTO', 'TOTAL_DESCONTOS']]
        if 'TOTAL_BRUTO' in colunas:
            ordem.append('TOTAL_BRUTO')
        if 'TOTAL_DESCONTOS' in colunas:
            ordem.append('TOTAL_DESCONTOS')
        
        df = df[[c for c in ordem if c in df.columns]]
        
        df.to_excel(caminho_excel, index=False)
        print(f"\n✅ Planilha gerada: {caminho_excel}")
        print(f"📊 Períodos encontrados: {len(df)}")
        for mes_ano in dados_consolidados.keys():
            print(f"   - {mes_ano}")
    else:
        print("\n⚠️ Nenhum dado válido encontrado.")


if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSOR DE CONTRACHEQUES - FORMATO BLACK-SECRECY-1")
    print("=" * 60)
    
    CAMINHO_PDF = r"S:/work/eg-goncalves/pdfs/" + input("Nome do arquivo PDF: ")
    CAMINHO_EXCEL = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Nome do arquivo Excel de saída: ")
    
    pagina_inicial = int(input("Página inicial: ")) - 1
    pagina_final = int(input("Página final: "))
    
    processar_pdf(
        CAMINHO_PDF,
        CAMINHO_EXCEL,
        paginas_a_ler=range(pagina_inicial, pagina_final),
        limpar=True
    )
