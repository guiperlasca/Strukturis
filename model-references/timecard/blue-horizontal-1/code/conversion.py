import pdfplumber
import csv
import re
import sys
import os

# Regex para identificar datas no formato DD.MM.YYYY seguido de dia da semana
# Ex: 16.04.2020 Qui
DATA_PATTERN = re.compile(r'^(\d{2}\.\d{2}\.\d{4})\s+(Dom|Seg|Ter|Qua|Qui|Sex|Sáb|Sab)\b', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM:SS
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2}:\d{2})\b')

def extrair_informacoes_cabecalho(texto):
    """Extrai informações do cabeçalho do cartão ponto"""
    info = {}
    
    # Nome do funcionário e Centro de Custo
    # Funcionário: 03783999 Lucio Nei Ancelmo Antuarte Centro de custo: 0421POAD02 Manutenção e Serviços de Linha
    padrao_nome = re.compile(r'Funcionário:\s*\d+\s+(.+?)(?:\s+Centro de custo|\s*$)', re.MULTILINE)
    match_nome = padrao_nome.search(texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(1).strip()
    
    # Período
    # Período: 16.04.2020 a 15.05.2020
    padrao_periodo = re.compile(r'Período:\s*(\d{2}\.\d{2}\.\d{4})\s*a\s*(\d{2}\.\d{2}\.\d{4})', re.IGNORECASE)
    match_periodo = padrao_periodo.search(texto)
    if match_periodo:
        info['periodo_inicial'] = match_periodo.group(1)
        info['periodo_final'] = match_periodo.group(2)
    
    # Cargo
    # Cargo: TECNICO MANUTENCAO MECANI
    padrao_cargo = re.compile(r'Cargo:(.+?)(?:\n|$)', re.MULTILINE)
    match_cargo = padrao_cargo.search(texto)
    if match_cargo:
        info['cargo'] = match_cargo.group(1).strip()
        
    return info

def processar_linha_data(linha):
    """Processa uma linha de data e retorna os dados extraídos"""
    data_match = DATA_PATTERN.search(linha)
    if not data_match:
        return None
        
    data_completa = data_match.group(1)
    # Convertendo pontos em barras para manter padrão CSV se desejado, 
    # ou mantendo original. O padrão black-* usa barras. Vamos converter para barras.
    data_formatada = data_completa.replace('.', '/')
    
    # Verifica se é folga/repouso/feriado na descrição textual da linha
    # O texto restante após o dia da semana
    resto_linha = linha[data_match.end():].strip()
    
    # Extrai horários
    horarios = HORARIO_PATTERN.findall(resto_linha)
    
    # Se não tiver horários, assume que o texto é observação (Feriado, Falta, etc)
    if not horarios:
        return {
            "data": data_formatada,
            "entrada1": "", "saida1": "",
            "entrada2": "", "saida2": "",
            "obs": resto_linha  # Ex: "3ª-FEIRA FERIADO" ou "Compens. Banco de Horas ..." (se não pegou horário)
        }

    # Se tiver horários, precisamos pegar Entrada e Saída
    # Neste layout blue-horizontal-1, os primeiros 2 horários costumam ser as marcações efetivas.
    # Os horários subsequentes (como 12:00:00 e 13:00:00) são horários padrão de refeição.
    
    entrada1 = ""
    saida1 = ""
    entrada2 = ""
    saida2 = ""
    obs = ""
    
    # Pega os 2 primeiros como Ent/Sai
    if len(horarios) >= 1:
        entrada1 = horarios[0]
    if len(horarios) >= 2:
        saida1 = horarios[1]
        
    # Verifica se há texto relevante entre a data e os horários ou depois
    # Mas simples: se tem horários, é dia trabalhado normal, a menos que seja banco de horas
    if "Banco de Horas" in resto_linha or "Compens." in resto_linha:
        obs = resto_linha # Pode ser útil manter o texto original no OBS se for um caso misto
        
    # Converter HH:MM:SS para HH:MM para manter consistência com black-* (opcional, mas recomendado)
    entrada1 = entrada1[:5] if entrada1 else ""
    saida1 = saida1[:5] if saida1 else ""
    
    return {
        "data": data_formatada,
        "entrada1": entrada1,
        "saida1": saida1,
        "entrada2": entrada2,
        "saida2": saida2,
        "obs": obs
    }

def processar_texto(texto):
    """Processa o texto completo extraído"""
    linhas_csv = []
    info_cabecalho = extrair_informacoes_cabecalho(texto)
    
    print(f"Info Cabeçalho: {info_cabecalho}")
    
    for linha in texto.split('\n'):
        linha = linha.strip()
        if not linha:
            continue
            
        dados_linha = processar_linha_data(linha)
        if dados_linha:
            # print(f"Processado: {dados_linha['data']} -> {dados_linha['entrada1']} - {dados_linha['saida1']}")
            linhas_csv.append([
                dados_linha['data'],
                dados_linha['entrada1'],
                dados_linha['saida1'],
                dados_linha['entrada2'],
                dados_linha['saida2']
            ])
            
    return linhas_csv, info_cabecalho

def processar_pdf(caminho_pdf, pagina_inicial=1, pagina_final=None):
    """Lê PDF e extrai dados"""
    texto_completo = ""
    
    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        pagina_final = pagina_final or total_paginas
        
        for i in range(pagina_inicial - 1, pagina_final):
            if i >= total_paginas:
                break
            print(f"Lendo página {i+1}...")
            page = pdf.pages[i]
            if page:
                texto_completo += (page.extract_text() or "") + "\n"
            
    return processar_texto(texto_completo)

def gerar_csv(linhas, info_cabecalho, caminho_csv):
    """Gera o arquivo CSV"""
    with open(caminho_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Cabeçalho metadata
        if info_cabecalho:
            writer.writerow([f"# Funcionário: {info_cabecalho.get('nome_funcionario', '')}"])
            writer.writerow([f"# Cargo: {info_cabecalho.get('cargo', '')}"])
            writer.writerow([f"# Período: {info_cabecalho.get('periodo_inicial', '')} a {info_cabecalho.get('periodo_final', '')}"])
            writer.writerow([])
        
        # Cabeçalho colunas
        writer.writerow(["Data", "Entrada1", "Saida1", "Entrada2", "Saida2"])
        
        for linha in linhas:
            writer.writerow(linha)
            
    print(f"CSV gerado em: {caminho_csv}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Modo teste com arquivo local
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        txt_path = os.path.join(base_dir, "examples", "print.txt")
        csv_path = os.path.join(base_dir, "examples", "resultado_teste.csv")
        
        print(f"Modo teste: lendo {txt_path}")
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                texto = f.read()
                
            linhas, info = processar_texto(texto)
            gerar_csv(linhas, info, csv_path)
        else:
            print(f"Arquivo de teste não encontrado: {txt_path}")
        
    else:
        # Modo interativo
        print("--- Conversor Blue Horizontal 1 ---")
        nome_pdf = input("Digite o nome do arquivo PDF (na pasta S:/work/eg-goncalves/pdfs/): ")
        if not nome_pdf.lower().endswith('.pdf'):
            nome_pdf += ".pdf"
            
        CAMINHO_PDF = os.path.join(r"S:\work\eg-goncalves\pdfs", nome_pdf)
        
        nome_csv = input("Digite o nome do arquivo CSV de saída (na pasta S:/work/eg-goncalves/resultados/tentativas/): ")
        if not nome_csv.lower().endswith('.csv'):
            nome_csv += ".csv"
            
        CAMINHO_CSV = os.path.join(r"S:\work\eg-goncalves\resultados\tentativas", nome_csv)
        
        try:
            pag_ini_str = input("Página inicial (padrão 1): ")
            pag_ini = int(pag_ini_str) if pag_ini_str.strip() else 1
            
            pag_fim_str = input("Página final (enter para todas): ")
            pag_fim = int(pag_fim_str) if pag_fim_str.strip() else None
            
            if os.path.exists(CAMINHO_PDF):
                linhas, info = processar_pdf(CAMINHO_PDF, pag_ini, pag_fim)
                
                # Garante que o diretório de saída existe
                os.makedirs(os.path.dirname(CAMINHO_CSV), exist_ok=True)
                
                gerar_csv(linhas, info, CAMINHO_CSV)
            else:
                print(f"Arquivo PDF não encontrado: {CAMINHO_PDF}")
            
        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()
