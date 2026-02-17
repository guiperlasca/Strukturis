
import pdfplumber
import csv
import re
import sys
import os

# Regex para identificar datas no formato DD/MM followed by year
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(SEG|TER|QUA|QUI|SEX|SAB|DOM)\b', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM (apenas 2 dígitos na hora para diferenciar de totais H:MM)
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')

def extrair_informacoes_cabecalho(texto):
    """Extrai informações do cabeçalho e definições de horários"""
    info = {}
    map_horarios = {}
    
    # Empregado
    match_nome = re.search(r'Empregado\.\.:\s*\d+\s*-\s*(.+)', texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(1).strip()
    
    # Período
    match_periodo = re.search(r'PERÍODO\s*\.:\s*(\d{2}/\d{2}/\d{4})\s*A\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    if match_periodo:
        info['periodo_inicial'] = match_periodo.group(1)
        info['periodo_final'] = match_periodo.group(2)
        
    # Mapeamento de Horários
    # Procura linhas começando com "Horários ..:" ou contendo "|" com padrões de horário
    # Ex: 15 06:30 11:00 12:00 14:50 | 188 06:30 11:30 12:30 16:18
    
    lines = texto.split('\n')
    capturing_schedules = False
    
    for line in lines:
        if 'Horários ..:' in line:
            capturing_schedules = True
            content = line.split('Horários ..:')[1]
        elif capturing_schedules and ('|' in line or re.search(r'\d+\s+\d{2}:\d{2}', line)):
            content = line
        elif capturing_schedules and not re.search(r'\d+\s+\d{2}:\d{2}', line):
            capturing_schedules = False
            continue
        else:
            continue
            
        if capturing_schedules:
            # Separa por pipe
            parts = content.split('|')
            for part in parts:
                part = part.strip()
                # Tenta capturar "COD HH:MM HH:MM HH:MM HH:MM"
                # Às vezes tem 2, 4 ou mais horários
                match_sched = re.match(r'(\d+)\s+((?:\d{2}:\d{2}\s*)+)', part)
                if match_sched:
                    cod = match_sched.group(1)
                    times_str = match_sched.group(2).strip()
                    # Store exact string to replace later
                    map_horarios[cod] = times_str
                    
    info['map_horarios'] = map_horarios
    return info

def processar_linha_data(linha, map_horarios):
    """Processa uma linha de registro diário"""
    
    data_match = DATA_PATTERN.search(linha)
    if not data_match:
        return None
        
    data_completa = data_match.group(1)
    
    # Identifica Código do horário para remover a string de escala
    # Geralmente após o dia da semana: 09/12/2020 QUA 208 ...
    # Pega palavra após o dia da semana
    parts = linha.split()
    # parts[0] = date, parts[1] = dia sem
    # parts[2] = potential code
    
    linha_limpa = linha
    
    if len(parts) > 2:
        possivel_cod = parts[2]
        if possivel_cod in map_horarios:
            schedule_str = map_horarios[possivel_cod]
            # Remove a primeira ocorrência do schedule string DA DIREITA para esquerda ou apenas replace?
            # A schedule printada aparece APÓS os registros.
            # Se o registro for igual ao início do schedule, replace simples pode remover errado.
            # Mas o schedule completo ("07:10 11:00 12:00 16:58") é longo e específico.
            # É seguro fazer replace se a string inteira bater.
            if schedule_str in linha_limpa:
                linha_limpa = linha_limpa.replace(schedule_str, ' ', 1)
    
    # Remove palavras chave que não são horários de batida
    palavras_ignorar = ["FOLGA", "DSR", "FERIADO", "Falta", "Abonada", "Atraso", "Abonado", "Compensado"]
    for p in palavras_ignorar:
        linha_limpa = re.sub(p, ' ', linha_limpa, flags=re.IGNORECASE)
        
    # Extrai horários restantes (batidas)
    horarios = HORARIO_PATTERN.findall(linha_limpa)
    
    entrada1, saida1, entrada2, saida2 = "", "", "", ""
    
    if len(horarios) >= 1: entrada1 = horarios[0]
    if len(horarios) >= 2: saida1 = horarios[1]
    if len(horarios) >= 3: entrada2 = horarios[2]
    if len(horarios) >= 4: saida2 = horarios[3]
    
    # Se só tiver 2 batidas, assume Jornada Direta ou Turno Único (Entrada 1 e Saída 1). 
    # Às vezes pode sem Entrada 1 e Saída 2? Não, assumimos sequencial.
    
    return {
        "Data": data_completa,
        "Entrada1": entrada1,
        "Saida1": saida1,
        "Entrada2": entrada2,
        "Saida2": saida2
    }

def processar_texto(texto):
    """Processa o texto completo do PDF"""
    linhas_csv = []
    info = extrair_informacoes_cabecalho(texto)
    map_horarios = info.get('map_horarios', {})
    
    print(f"Informações extraídas: {info.get('nome_funcionario')}")
    print(f"Map Horários: {map_horarios}")
    
    for linha in texto.split('\n'):
        linha = linha.strip()
        if not linha:
            continue
            
        dados = processar_linha_data(linha, map_horarios)
        if dados:
            linhas_csv.append([
                dados['Data'],
                dados['Entrada1'],
                dados['Saida1'],
                dados['Entrada2'],
                dados['Saida2']
            ])
            
    return linhas_csv, info

def processar_pdf(caminho_pdf, pagina_inicial=1, pagina_final=None):
    texto_completo = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        total = len(pdf.pages)
        pagina_final = pagina_final or total
        for i in range(pagina_inicial-1, min(pagina_final, total)):
            print(f"Lendo página {i+1}...")
            texto_completo += pdf.pages[i].extract_text() + "\n"
            
    return processar_texto(texto_completo)

def gerar_csv(linhas, info, caminho_csv):
    with open(caminho_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([f"# Funcionário: {info.get('nome_funcionario', '')}"])
        writer.writerow([f"# Período: {info.get('periodo_inicial', '')} a {info.get('periodo_final', '')}"])
        writer.writerow([])
        writer.writerow(["Data", "Entrada1", "Saida1", "Entrada2", "Saida2"])
        writer.writerows(linhas)
    print(f"CSV gerado: {caminho_csv}")

if __name__ == "__main__":
    # Modo interativo padrão
    try:
        # Verifica se há argumentos (modo batch/teste)
        if len(sys.argv) > 1 and sys.argv[1] == "dev":
             # Hardcoded paths for dev/test
             f_pdf = r"S:/work/eg-goncalves/programas/tipos/cartao_ponto/black-horizontal-6/examples/document.pdf"
             f_csv = r"S:/work/eg-goncalves/programas/tipos/cartao_ponto/black-horizontal-6/examples/output.csv"
             result, nfo = processar_pdf(f_pdf)
             gerar_csv(result, nfo, f_csv)
        else:
            filename = input("Digite o nome do arquivo PDF: ")
            caminho_pdf = r"S:/work/eg-goncalves/pdfs/" + filename
            csv_name = input("Digite o nome do arquivo CSV de saída: ")
            caminho_csv = r"S:/work/eg-goncalves/resultados/tentativas/" + csv_name
            
            p_ini = input("Página inicial (1): ")
            p_ini = int(p_ini) if p_ini else 1
            p_fim = input("Página final (todas): ")
            p_fim = int(p_fim) if p_fim else None
            
            result, nfo = processar_pdf(caminho_pdf, p_ini, p_fim)
            gerar_csv(result, nfo, caminho_csv)
            
    except Exception as e:
        print(f"Erro: {e}")
