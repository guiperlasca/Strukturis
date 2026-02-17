import pdfplumber
import csv
import re
from collections import OrderedDict


# Regex para identificar datas no formato DD/MM/YYYY seguido de dia da semana
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(Seg|Ter|Qua|Qui|Sex|Sáb|Dom)\b', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')

# Horário padrão de trabalho (usado como referência)
HORARIO_PADRAO = ['08:00', '12:00', '13:00', '17:00']


def converter_horario_para_minutos(horario):
    """
    Converte horário HH:MM para minutos totais para comparação
    """
    partes = horario.split(':')
    return int(partes[0]) * 60 + int(partes[1])


def extrair_marcacoes_validas(horarios):
    """
    Extrai as marcações válidas seguindo a regra específica:
    - Ignora os primeiros 4 horários fixos (08:00 12:00 13:00 17:00)
    - Pega exatamente 2 ou 4 horários seguintes
    - Para de contar quando aparecer um horário menor que o último válido
    """
    if len(horarios) <= 4:
        return []
    
    # Pega apenas os horários após os 4 primeiros fixos
    horarios_candidatos = horarios[4:]
    
    marcacoes_validas = []
    ultimo_horario_minutos = -1
    
    for horario in horarios_candidatos:
        # Ignora horários negativos (como "-07:54")
        if horario.startswith('-'):
            continue
            
        # Converte para minutos para comparação
        horario_minutos = converter_horario_para_minutos(horario)
        
        # Se o horário atual é menor que o último válido, para de processar
        if ultimo_horario_minutos != -1 and horario_minutos < ultimo_horario_minutos:
            break
        
        # Adiciona à lista de válidas
        marcacoes_validas.append(horario)
        ultimo_horario_minutos = horario_minutos
        
        # Limita a 4 marcações no máximo
        if len(marcacoes_validas) >= 4:
            break
    
    return marcacoes_validas


def determinar_entradas_saidas(marcacoes):
    """
    Determina entrada1, saída1, entrada2, saída2 baseado nas marcações válidas
    """
    entrada1, saida1, entrada2, saida2 = '', '', '', ''
    
    if len(marcacoes) >= 1:
        entrada1 = marcacoes[0]
    
    if len(marcacoes) >= 2:
        saida1 = marcacoes[1]
    
    if len(marcacoes) >= 3:
        entrada2 = marcacoes[2]
    
    if len(marcacoes) >= 4:
        saida2 = marcacoes[3]
    
    return entrada1, saida1, entrada2, saida2


def eh_linha_folga(linha):
    """
    Verifica se a linha indica folga ou ausência
    """
    palavras_folga = ['folga', 'casa', 'ausente', 'falta', '(-)']
    linha_lower = linha.lower()
    return any(palavra in linha_lower for palavra in palavras_folga)


def extrair_informacoes_cabecalho(texto):
    """
    Extrai informações do cabeçalho do cartão ponto
    """
    info = {}
    
    # Nome do funcionário
    padrao_nome = re.compile(r'Empregado:\s*\d+-(.+?)(?:\s+Carteira|\s*Admissão)', re.MULTILINE)
    match_nome = padrao_nome.search(texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(1).strip()
    
    # Período
    padrao_periodo = re.compile(r'Período:\s*(\d{2}/\d{2}/\d{4})\s*até\s*(\d{2}/\d{2}/\d{4})')
    match_periodo = padrao_periodo.search(texto)
    if match_periodo:
        info['periodo_inicial'] = match_periodo.group(1)
        info['periodo_final'] = match_periodo.group(2)
        
        # Extrai mês/ano da data final
        partes = match_periodo.group(2).split('/')
        info['mes_ano'] = f"{partes[1]}/{partes[2]}"
    
    # Função
    padrao_funcao = re.compile(r'Função:\s*(.+?)(?:\s+Estrutura|\s*$)', re.MULTILINE)
    match_funcao = padrao_funcao.search(texto)
    if match_funcao:
        info['funcao'] = match_funcao.group(1).strip()
    
    return info


def processar_pdf_cartao_ponto_para_csv(arquivo_pdf, arquivo_csv, pagina_inicial=1, pagina_final=None):
    """
    Processa o PDF do cartão ponto e gera CSV com as marcações
    """
    linhas_csv = []
    informacoes_cabecalho = None
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        total_paginas = len(pdf.pages)
        pagina_final = pagina_final or total_paginas
        
        print(f"Processando páginas {pagina_inicial} a {pagina_final} de {total_paginas} páginas...")
        
        for i, page in enumerate(pdf.pages):
            # Ajusta índices (usuário digita 1-based, código usa 0-based)
            if i < pagina_inicial - 1 or i >= pagina_final:
                continue
                
            print(f"Processando página {i + 1}...")
            
            texto = page.extract_text()
            if not texto:
                continue
            
            # Extrai informações do cabeçalho da primeira página processada
            if not informacoes_cabecalho:
                informacoes_cabecalho = extrair_informacoes_cabecalho(texto)
                print(f"Funcionário: {informacoes_cabecalho.get('nome_funcionario', 'NÃO IDENTIFICADO')}")
                print(f"Função: {informacoes_cabecalho.get('funcao', 'NÃO IDENTIFICADA')}")
                if 'periodo_inicial' in informacoes_cabecalho:
                    print(f"Período: {informacoes_cabecalho['periodo_inicial']} até {informacoes_cabecalho['periodo_final']}")
            
            # Processa cada linha do texto
            for linha in texto.split('\n'):
                linha = linha.strip()
                if not linha:
                    continue
                
                # Verifica se é linha com data
                data_match = DATA_PATTERN.search(linha)
                if data_match:
                    data = data_match.group(1)
                    
                    # Verifica se é folga
                    if eh_linha_folga(linha):
                        linhas_csv.append([data, '', '', '', ''])
                        print(f"{data}: FOLGA")
                        continue
                    
                    # Extrai todos os horários da linha
                    horarios = HORARIO_PATTERN.findall(linha)
                    
                    # Filtra horários válidos (entre 00:00 e 23:59)
                    horarios_validos = [h for h in horarios if 0 <= int(h.split(':')[0]) < 24 and 0 <= int(h.split(':')[1]) < 60]
                    
                    if not horarios_validos:
                        linhas_csv.append([data, '', '', '', ''])
                        print(f"{data}: SEM HORÁRIOS")
                        continue
                    
                    # Extrai marcações válidas seguindo a regra específica
                    marcacoes_validas = extrair_marcacoes_validas(horarios_validos)
                    
                    print(f"{data}: Horários encontrados: {horarios_validos}")
                    print(f"{data}: Marcações válidas: {marcacoes_validas}")
                    
                    # Determina entrada1, saída1, entrada2, saída2
                    entrada1, saida1, entrada2, saida2 = determinar_entradas_saidas(marcacoes_validas)
                    
                    # Adiciona ao CSV
                    linhas_csv.append([data, entrada1, saida1, entrada2, saida2])
                    
                    print(f"{data}: Entrada1: {entrada1}, Saída1: {saida1}, Entrada2: {entrada2}, Saída2: {saida2}")
    
    # Remove datas duplicadas mantendo a última ocorrência
    registros_unicos = OrderedDict()
    for data, entrada1, saida1, entrada2, saida2 in linhas_csv:
        registros_unicos[data] = (entrada1, saida1, entrada2, saida2)
    
    # Escreve o CSV
    with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Cabeçalho do CSV com informações do funcionário
        if informacoes_cabecalho:
            writer.writerow([f"# Funcionário: {informacoes_cabecalho.get('nome_funcionario', 'NÃO IDENTIFICADO')}"])
            writer.writerow([f"# Função: {informacoes_cabecalho.get('funcao', 'NÃO IDENTIFICADA')}"])
            if 'periodo_inicial' in informacoes_cabecalho:
                writer.writerow([f"# Período: {informacoes_cabecalho['periodo_inicial']} até {informacoes_cabecalho['periodo_final']}"])
            writer.writerow([])
        
        # Cabeçalho das colunas
        writer.writerow(["Data", "Entrada1", "Saida1", "Entrada2", "Saida2"])
        
        # Dados
        for data, (entrada1, saida1, entrada2, saida2) in registros_unicos.items():
            writer.writerow([data, entrada1, saida1, entrada2, saida2])
    
    print(f"\n✅ Arquivo CSV gerado com sucesso: {arquivo_csv}")
    print(f"📊 Total de registros processados: {len(registros_unicos)}")
    
    return len(registros_unicos)


if __name__ == "__main__":
    # Configuração dos caminhos
    pdf_input = r"S:/work/eg-goncalves/pdfs/"
    csv_output = r"S:/work/eg-goncalves/resultados/tentativas/"
    
    # Input do usuário
    nome_pdf = input("Digite o nome do arquivo PDF (ex: cartao_ponto.pdf): ")
    nome_csv = input("Digite o nome do arquivo CSV de saída (ex: resultado.csv): ")
    
    pdf_input += nome_pdf
    csv_output += nome_csv
    
    pagina_inicial = int(input("Digite o número da página inicial (ex: 1): "))
    pagina_final_input = input("Digite o número da página final (deixe em branco para processar até o final): ")
    pagina_final = int(pagina_final_input) if pagina_final_input.strip() else None
    
    # Processa o arquivo
    try:
        processar_pdf_cartao_ponto_para_csv(pdf_input, csv_output, pagina_inicial, pagina_final)
    except FileNotFoundError:
        print("❌ Erro: Arquivo não encontrado. Verifique o caminho e nome do arquivo.")
    except Exception as e:
        print(f"❌ Erro ao processar o arquivo: {e}")
        print("Verifique se o arquivo é um PDF válido e se tem permissões de leitura.")