"""
Conversão de cartão ponto formato BLACK-SECRECY-1
Formato "Espelho do Ponto" com marcações O (Original), I (Incluída), P (Pré-assinalada)
- Primeiro limpa o PDF (remove textos de sigilo/visibilidade)
- Extrai apenas marcações de ponto (ignora horários padrão da seção "Horários")
- Gera CSV com Data, Entrada1, Saida1, Entrada2, Saida2
"""

import pdfplumber
import fitz  # PyMuPDF
import csv
import re
from collections import OrderedDict
import os
import sys

# Regex para identificar datas no formato DD/MM/YYYY seguido de dia da semana
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(Segunda|Terca|Terça|Quarta|Quinta|Sexta|Sabado|Sábado|Domingo)\b', flags=re.IGNORECASE)

# Regex para extrair horários com marcador (O, I, P)
HORARIO_COM_MARCADOR_PATTERN = re.compile(r'(\d{2}:\d{2})\s*([OIP])\b')

# Regex para extrair apenas horários HH:MM
HORARIO_SIMPLES_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')


def limpar_pdf_sigilo(pdf_path, output_path=None):
    """
    Remove os textos de sigilo e visibilidade do PDF.
    Retorna o caminho do PDF limpo.
    """
    if output_path is None:
        base, ext = os.path.splitext(pdf_path)
        output_path = f"{base}_limpo{ext}"
    
    # Se já existe, remove
    if os.path.exists(output_path):
        os.remove(output_path)
    
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


def converter_horario_para_minutos(horario):
    """Converte horário HH:MM para minutos totais"""
    partes = horario.split(':')
    return int(partes[0]) * 60 + int(partes[1])


def extrair_marcacoes_linha(linha):
    """
    Extrai as marcações de ponto de uma linha.
    
    Formato esperado: "HH:MM O" ou "HH:MM I" ou "HH:MM P"
    onde O=Original, I=Incluída, P=Pré-assinalada
    
    Ignora horários sem marcador (que são horários de jornada/extras)
    """
    # Encontra todos os horários com marcador
    marcacoes = HORARIO_COM_MARCADOR_PATTERN.findall(linha)
    
    # Retorna apenas os horários (sem o marcador)
    horarios = [h[0] for h in marcacoes]
    
    return horarios


def eh_linha_ausente(linha):
    """Verifica se a linha indica ausência ou folga"""
    return '** Ausente **' in linha or 'FOLGA' in linha.upper()


def eh_secao_marcacoes(linha):
    """Verifica se entramos na seção de marcações de ponto"""
    return 'Data Dia 1a E.' in linha


def eh_fim_marcacoes(linha):
    """Verifica se saímos da seção de marcações"""
    indicadores_fim = [
        'Marcações desconsideradas',
        'Banco de Horas',
        'Horários',
        '______________',
        'Assinatura do Funcionário',
        'Documento assinado'
    ]
    return any(ind in linha for ind in indicadores_fim)


def filtrar_marcacoes_crescentes(horarios):
    """
    Filtra marcações garantindo que cada horário seja maior que o anterior.
    Retorna no máximo 4 marcações válidas.
    """
    if not horarios:
        return []
    
    validas = [horarios[0]]
    ultimo_minutos = converter_horario_para_minutos(horarios[0])
    
    for horario in horarios[1:]:
        minutos = converter_horario_para_minutos(horario)
        if minutos > ultimo_minutos:
            validas.append(horario)
            ultimo_minutos = minutos
            if len(validas) >= 4:
                break
    
    return validas


def extrair_informacoes_cabecalho(texto):
    """Extrai informações do cabeçalho do cartão ponto"""
    info = {}
    
    # Nome do funcionário
    match_nome = re.search(r'Nome:\s*([A-Z\s]+?)(?:\s+Chapa|\s+CPF|\s*$)', texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(1).strip()
    
    # Período
    match_periodo = re.search(r'Espelho do Ponto\s+(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', texto)
    if match_periodo:
        info['periodo_inicial'] = match_periodo.group(1)
        info['periodo_final'] = match_periodo.group(2)
        
        # Extrai mês/ano da data final
        partes = match_periodo.group(2).split('/')
        info['mes_ano'] = f"{partes[1]}/{partes[2]}"
    
    # Função
    match_funcao = re.search(r'Função:\s*\d+\s*-\s*([A-Z]+)', texto)
    if match_funcao:
        info['funcao'] = match_funcao.group(1).strip()
    
    # Matrícula
    match_matricula = re.search(r'Matrícula:\s*([\d\s-]+)', texto)
    if match_matricula:
        info['matricula'] = match_matricula.group(1).strip()
    
    return info


def processar_pdf_cartao_ponto(arquivo_pdf, arquivo_csv, pagina_inicial=1, pagina_final=None, limpar=True):
    """
    Processa o PDF do cartão ponto e gera CSV com as marcações.
    """
    
    # Limpa o PDF primeiro se necessário
    if limpar:
        pdf_limpo = limpar_pdf_sigilo(arquivo_pdf)
    else:
        pdf_limpo = arquivo_pdf
    
    print(f"\n📖 Extraindo marcações de: {pdf_limpo}")
    print("-" * 50)
    
    linhas_csv = []
    informacoes_cabecalho = None
    
    with pdfplumber.open(pdf_limpo) as pdf:
        total_paginas = len(pdf.pages)
        pagina_final = pagina_final or total_paginas
        
        print(f"Processando páginas {pagina_inicial} a {pagina_final} de {total_paginas}...")
        
        for i, page in enumerate(pdf.pages):
            # Ajusta índices (usuário digita 1-based)
            if i < pagina_inicial - 1 or i >= pagina_final:
                continue
            
            texto = page.extract_text()
            if not texto:
                continue
            
            print(f"\n📄 Página {i + 1}")
            
            # Extrai informações do cabeçalho
            if not informacoes_cabecalho:
                informacoes_cabecalho = extrair_informacoes_cabecalho(texto)
                if informacoes_cabecalho.get('nome_funcionario'):
                    print(f"  👤 Funcionário: {informacoes_cabecalho['nome_funcionario']}")
                if informacoes_cabecalho.get('periodo_inicial'):
                    print(f"  📅 Período: {informacoes_cabecalho['periodo_inicial']} a {informacoes_cabecalho['periodo_final']}")
            
            # Processa linhas
            dentro_marcacoes = False
            
            for linha in texto.split('\n'):
                linha = linha.strip()
                if not linha:
                    continue
                
                # Detecta início da seção de marcações
                if eh_secao_marcacoes(linha):
                    dentro_marcacoes = True
                    continue
                
                # Detecta fim da seção
                if eh_fim_marcacoes(linha):
                    dentro_marcacoes = False
                    continue
                
                # Processa apenas linhas dentro da seção de marcações
                if dentro_marcacoes:
                    # Verifica se a linha começa com data
                    data_match = DATA_PATTERN.match(linha)
                    if data_match:
                        data = data_match.group(1)
                        
                        # Verifica se é ausência/folga
                        if eh_linha_ausente(linha):
                            linhas_csv.append([data, '', '', '', ''])
                            print(f"  {data}: FOLGA/AUSENTE")
                            continue
                        
                        # Extrai marcações com indicador O/I/P
                        marcacoes = extrair_marcacoes_linha(linha)
                        
                        # Filtra marcações garantindo ordem crescente
                        marcacoes_validas = filtrar_marcacoes_crescentes(marcacoes)
                        
                        # Preenche entrada1, saida1, entrada2, saida2
                        entrada1 = marcacoes_validas[0] if len(marcacoes_validas) > 0 else ''
                        saida1 = marcacoes_validas[1] if len(marcacoes_validas) > 1 else ''
                        entrada2 = marcacoes_validas[2] if len(marcacoes_validas) > 2 else ''
                        saida2 = marcacoes_validas[3] if len(marcacoes_validas) > 3 else ''
                        
                        linhas_csv.append([data, entrada1, saida1, entrada2, saida2])
                        
                        if marcacoes_validas:
                            print(f"  {data}: {' | '.join(marcacoes_validas)}")
                        else:
                            print(f"  {data}: SEM MARCAÇÕES")
    
    # Remove duplicatas mantendo a última ocorrência
    registros_unicos = OrderedDict()
    for data, entrada1, saida1, entrada2, saida2 in linhas_csv:
        registros_unicos[data] = (entrada1, saida1, entrada2, saida2)
    
    # Escreve o CSV
    with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Cabeçalho com info do funcionário
        if informacoes_cabecalho:
            if informacoes_cabecalho.get('nome_funcionario'):
                writer.writerow([f"# Funcionário: {informacoes_cabecalho['nome_funcionario']}"])
            if informacoes_cabecalho.get('funcao'):
                writer.writerow([f"# Função: {informacoes_cabecalho['funcao']}"])
            if informacoes_cabecalho.get('periodo_inicial'):
                writer.writerow([f"# Período: {informacoes_cabecalho['periodo_inicial']} até {informacoes_cabecalho['periodo_final']}"])
            writer.writerow([])
        
        # Cabeçalho das colunas
        writer.writerow(["Data", "Entrada1", "Saida1", "Entrada2", "Saida2"])
        
        # Dados
        for data, (entrada1, saida1, entrada2, saida2) in registros_unicos.items():
            writer.writerow([data, entrada1, saida1, entrada2, saida2])
    
    print(f"\n✅ CSV gerado: {arquivo_csv}")
    print(f"📊 Total de registros: {len(registros_unicos)}")
    
    return len(registros_unicos)


if __name__ == "__main__":
    print("=" * 60)
    print("CONVERSOR DE CARTÃO PONTO - FORMATO BLACK-SECRECY-1")
    print("=" * 60)
    
    pdf_input = r"S:/work/eg-goncalves/pdfs/"
    csv_output = r"S:/work/eg-goncalves/resultados/tentativas/"
    
    nome_pdf = input("Nome do arquivo PDF: ")
    nome_csv = input("Nome do arquivo CSV de saída: ")
    
    pdf_input += nome_pdf
    csv_output += nome_csv
    
    pagina_inicial = int(input("Página inicial: "))
    pagina_final_input = input("Página final (deixe em branco para todas): ")
    pagina_final = int(pagina_final_input) if pagina_final_input.strip() else None
    
    try:
        processar_pdf_cartao_ponto(pdf_input, csv_output, pagina_inicial, pagina_final)
    except FileNotFoundError:
        print("❌ Arquivo não encontrado.")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
