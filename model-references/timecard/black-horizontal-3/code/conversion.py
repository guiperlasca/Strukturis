import pdfplumber
import csv
import re
from collections import OrderedDict

# Regex para identificar datas no formato DD/MM
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2})\s+([A-Za-z]{3})', flags=re.IGNORECASE)

# Regex para extrair o ano do período
PERIODO_PATTERN = re.compile(r'Período\s*:\s*\d{2}/\d{2}/(\d{4})', re.IGNORECASE)

# Regex para extrair horários no formato HH:MM
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')

def converter_horario_para_minutos(horario):
    """
    Converte horário HH:MM para minutos totais para comparação
    """
    partes = horario.split(':')
    return int(partes[0]) * 60 + int(partes[1])

def extrair_horarios_marcacoes(linha):
    """
    Extrai os horários de marcações da linha.
    Para quando encontra texto (palavras não-numéricas).
    Garante número par de horários.
    """
    # Remove a data e dia da semana do início
    linha_limpa = DATA_PATTERN.sub('', linha).strip()
    
    # Remove código de horário (ex: 0072, 9998, etc) - são 4 dígitos no início
    linha_limpa = re.sub(r'^\d{4}\s+', '', linha_limpa).strip()
    
    # Extrai horários até encontrar uma palavra
    horarios = []
    partes = linha_limpa.split()
    
    for parte in partes:
        # Verifica se é um horário (formato HH:MM)
        if re.match(r'^\d{2}:\d{2}$', parte):
            horarios.append(parte)
        else:
            # Encontrou texto, para de extrair
            break
    
    # Garante número par de horários
    if len(horarios) % 2 != 0:
        horarios = horarios[:-1]  # Remove o último se for ímpar
    
    return horarios

def extrair_informacoes_cabecalho(texto):
    """
    Extrai informações do cabeçalho do cartão ponto
    """
    info = {}
    
    # Nome do funcionário - extrai o número e nome (ex: 24296 MARCOS ANTONIO DE SOUSA)
    padrao_nome = re.compile(r'Empregado:\s*(\d+)\s+(.+?)(?:\s+Sindicato|$)', re.MULTILINE)
    match_nome = padrao_nome.search(texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(2).strip()
        info['numero_funcionario'] = match_nome.group(1).strip()
    
    # Período (formato DD/MM/YYYY a DD/MM/YYYY)
    padrao_periodo = re.compile(r'Período\s*:\s*(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})', re.MULTILINE)
    match_periodo = padrao_periodo.search(texto)
    if match_periodo:
        info['periodo_inicial'] = match_periodo.group(1)
        info['periodo_final'] = match_periodo.group(2)
        
        # Extrai o ano do período
        partes = match_periodo.group(1).split('/')
        info['ano'] = partes[2]
        
        # Extrai mês/ano da data final
        partes = match_periodo.group(2).split('/')
        info['mes_ano'] = f"{partes[1]}/{partes[2]}"
    
    # Cargo
    padrao_cargo = re.compile(r'Cargo:\s*(.+?)(?:\s+CTPS|$)', re.MULTILINE)
    match_cargo = padrao_cargo.search(texto)
    if match_cargo:
        info['cargo'] = match_cargo.group(1).strip()
    
    # Empregador
    padrao_empregador = re.compile(r'Empregador:\d+\s+(.+?)(?:\s+CNPJ|$)', re.MULTILINE)
    match_empregador = padrao_empregador.search(texto)
    if match_empregador:
        info['empregador'] = match_empregador.group(1).strip()
    
    return info

def processar_pdf_cartao_ponto_novo_formato(arquivo_pdf, arquivo_csv, pagina_inicial=1, pagina_final=None):
    """
    Processa o PDF do cartão ponto (novo formato) e gera CSV com as marcações
    
    Formato esperado:
    DD/MM DIA HORARIO MARCACOES...
    
    Onde MARCACOES são horários (HH:MM) até encontrar texto
    """
    linhas_csv = []
    informacoes_cabecalho = None
    ano_atual = None
    
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
            
            # Extrai informações do cabeçalho de cada página (para pegar o ano certo)
            info_pagina = extrair_informacoes_cabecalho(texto)
            
            # Se é a primeira página, salva todas as informações
            if not informacoes_cabecalho:
                informacoes_cabecalho = info_pagina
                ano_atual = info_pagina.get('ano')
                print(f"Funcionário: {informacoes_cabecalho.get('nome_funcionario', 'NÃO IDENTIFICADO')}")
                print(f"Cargo: {informacoes_cabecalho.get('cargo', 'NÃO IDENTIFICADO')}")
                if 'periodo_inicial' in informacoes_cabecalho:
                    print(f"Período: {informacoes_cabecalho['periodo_inicial']} até {informacoes_cabecalho['periodo_final']}")
            else:
                # Atualiza o ano se houver mudança entre páginas
                if 'ano' in info_pagina:
                    ano_atual = info_pagina['ano']
            
            # Processa cada linha do texto
            for linha in texto.split('\n'):
                linha = linha.strip()
                
                if not linha:
                    continue
                
                # Verifica se é linha com data
                data_match = DATA_PATTERN.search(linha)
                
                if data_match:
                    data_ddmm = data_match.group(1)  # DD/MM
                    
                    # Combina com o ano
                    data_completa = f"{data_ddmm}/{ano_atual}"
                    
                    # Extrai horários de marcações
                    horarios = extrair_horarios_marcacoes(linha)
                    
                    # Converte para entrada1, saída1, entrada2, saída2
                    entrada1 = horarios[0] if len(horarios) > 0 else ''
                    saida1 = horarios[1] if len(horarios) > 1 else ''
                    entrada2 = horarios[2] if len(horarios) > 2 else ''
                    saida2 = horarios[3] if len(horarios) > 3 else ''
                    
                    linhas_csv.append([data_completa, entrada1, saida1, entrada2, saida2])
                    
                    horarios_str = ', '.join(horarios) if horarios else 'NENHUM'
                    print(f"{data_completa}: Horários: [{horarios_str}]")
    
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
            writer.writerow([f"# Cargo: {informacoes_cabecalho.get('cargo', 'NÃO IDENTIFICADO')}"])
            if 'empregador' in informacoes_cabecalho:
                writer.writerow([f"# Empregador: {informacoes_cabecalho.get('empregador', 'NÃO IDENTIFICADO')}"])
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
        processar_pdf_cartao_ponto_novo_formato(pdf_input, csv_output, pagina_inicial, pagina_final)
    except FileNotFoundError:
        print("❌ Erro: Arquivo não encontrado. Verifique o caminho e nome do arquivo.")
    except Exception as e:
        print(f"❌ Erro ao processar o arquivo: {e}")
        print("Verifique se o arquivo é um PDF válido e se tem permissões de leitura.")