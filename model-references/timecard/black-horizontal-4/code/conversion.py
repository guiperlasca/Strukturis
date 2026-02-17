import pdfplumber
import csv
import re
import sys
import os
from collections import OrderedDict

# Regex para identificar datas no formato DD/MM seguido de dia da semana
# Ex: 15/12 Dom
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2})\s+(Dom|Seg|Ter|Qua|Qui|Sex|Sáb|Sab)\b', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')

def converter_horario_para_minutos(horario):
    """Converte horário HH:MM para minutos totais"""
    try:
        partes = horario.split(':')
        return int(partes[0]) * 60 + int(partes[1])
    except:
        return 0

def extrair_informacoes_cabecalho(texto):
    """Extrai informações do cabeçalho do cartão ponto"""
    info = {}
    
    # Nome do funcionário
    # Empregado:601412-Nasser Ibrahim Muhd Ahmad Eid Data Admissão: 01/06/2010
    padrao_nome = re.compile(r'Empregado:\d+-(.+?)(?:\s+Data|\s*$)', re.MULTILINE)
    match_nome = padrao_nome.search(texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(1).strip()
    
    # Período
    # Cartão Ponto Período De 15/12/2019 Até 14/01/2020
    padrao_periodo = re.compile(r'Período De\s*(\d{2}/\d{2}/\d{4})\s*Até\s*(\d{2}/\d{2}/\d{4})', re.IGNORECASE)
    match_periodo = padrao_periodo.search(texto)
    if match_periodo:
        info['periodo_inicial'] = match_periodo.group(1)
        info['periodo_final'] = match_periodo.group(2)
        
        # Extrai mês/ano da data final para referência
        partes = match_periodo.group(2).split('/')
        info['ano'] = partes[2]
    
    # Cargo
    padrao_cargo = re.compile(r'Cargo:(.+?)(?:\n|$)', re.MULTILINE)
    match_cargo = padrao_cargo.search(texto)
    if match_cargo:
        info['cargo'] = match_cargo.group(1).strip()
        
    return info

def extrair_ano_da_data(data_ddmm, periodo_info):
    """Tenta inferir o ano da data baseado no período do cartão"""
    if not periodo_info or 'periodo_inicial' not in periodo_info:
        return f"{data_ddmm}/AAAA"
        
    try:
        dia, mes = map(int, data_ddmm.split('/'))
        
        ini_dia, ini_mes, ini_ano = map(int, periodo_info['periodo_inicial'].split('/'))
        fim_dia, fim_mes, fim_ano = map(int, periodo_info['periodo_final'].split('/'))
        
        # Se o mês da data for igual ao mês inicial, usa o ano inicial
        if mes == ini_mes:
            return f"{data_ddmm}/{ini_ano}"
        # Se o mês da data for igual ao mês final, usa o ano final
        elif mes == fim_mes:
            return f"{data_ddmm}/{fim_ano}"
        # Caso genérico (ex: período cruzando ano novo)
        else:
            # Se mês é 12 e estamos no início do ano seguinte, provavelmente é ano anterior
            if mes == 12 and fim_mes == 1:
                return f"{data_ddmm}/{ini_ano}"
            return f"{data_ddmm}/{fim_ano}"
            
    except:
        return f"{data_ddmm}/{periodo_info.get('ano', 'AAAA')}"

def processar_linha_data(linha, periodo_info):
    """Processa uma linha de data e retorna os dados extraídos"""
    data_match = DATA_PATTERN.search(linha)
    if not data_match:
        return None
        
    data_ddmm = data_match.group(1)
    data_completa = extrair_ano_da_data(data_ddmm, periodo_info)
    
    # Verifica se é folga/repouso/feriado
    linha_lower = linha.lower()
    if 'repouso' in linha_lower or 'feriado' in linha_lower:
        return {
            "data": data_completa,
            "entrada1": "", "saida1": "",
            "entrada2": "", "saida2": "",
            "obs": "FOLGA/FERIADO"
        }
        
    # Extrai horários
    horarios = HORARIO_PATTERN.findall(linha)
    
    # Lógica específica para este layout:
    # Ex: 19/12 Qui Compensado - 19:57 07:05 08:00 11:08
    # Ex: 09/01 Qui Compensado - 07:29 19:18 11:49
    # Geralmente os primeiros 2 horários são Entrada/Saída.
    # Se tiver mais, podem ser totais.
    # Mas cuidado com intervalos.
    
    entrada1, saida1, entrada2, saida2 = "", "", "", ""
    
    # Filtra horários válidos (00:00 a 23:59)
    horarios_validos = []
    for h in horarios:
        try:
            hh, mm = map(int, h.split(':'))
            if 0 <= hh < 24 and 0 <= mm < 60:
                horarios_validos.append(h)
        except:
            pass
            
    if not horarios_validos:
        return {
            "data": data_completa,
            "entrada1": "", "saida1": "",
            "entrada2": "", "saida2": "",
            "obs": "SEM MARCACAO"
        }

    # Assumindo que os primeiros horários são as marcações
    # Se tiver 2: Ent1, Sai1
    # Se tiver 3: Ent1, Sai1, (Total?) -> Ignora o 3º
    # Se tiver 4: Ent1, Sai1, (Total1?), (Total2?) -> Ignora 3º e 4º?
    # OU Ent1, Sai1, Ent2, Sai2?
    # No exemplo 19/12: 19:57 (Ent), 07:05 (Sai), 08:00 (Total?), 11:08 (Total?)
    # No exemplo 09/01: 07:29 (Ent), 19:18 (Sai), 11:49 (Total?)
    
    # Parece que neste modelo, as marcações vêm primeiro.
    # Vamos pegar até 4 horários, mas precisamos ser espertos.
    # Se tiver "Compensado -", pode indicar algo.
    
    # Vamos pegar os 2 primeiros como Ent1/Sai1
    if len(horarios_validos) >= 1:
        entrada1 = horarios_validos[0]
    if len(horarios_validos) >= 2:
        saida1 = horarios_validos[1]
    
    # Se tiver mais horários, vamos ver se fazem sentido como Ent2/Sai2 ou se são totais.
    # Totais geralmente são horas redondas ou somas.
    # No exemplo 19/12, 08:00 e 11:08 parecem totais (8h trab + extras?).
    # No exemplo 09/01, 11:49 parece total.
    
    # Por enquanto, vamos assumir apenas 1 par de entrada/saída, pois o cabeçalho "Horários: 103 - 07:00 19:00" sugere turno único.
    # Se o usuário reclamar, ajustamos.
    
    return {
        "data": data_completa,
        "entrada1": entrada1,
        "saida1": saida1,
        "entrada2": entrada2,
        "saida2": saida2,
        "obs": ""
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
            
        dados_linha = processar_linha_data(linha, info_cabecalho)
        if dados_linha:
            print(f"Processado: {dados_linha['data']} -> {dados_linha['entrada1']} - {dados_linha['saida1']}")
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
            texto_completo += page.extract_text() + "\n"
            
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
        
        # Dados
        # Remove duplicatas de datas (mantendo a última?) ou mantém tudo?
        # Cartão ponto geralmente é sequencial.
        # Vamos usar OrderedDict para garantir unicidade por data se necessário, mas aqui vamos escrever direto.
        
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
        with open(txt_path, 'r', encoding='utf-8') as f:
            texto = f.read()
            
        linhas, info = processar_texto(texto)
        gerar_csv(linhas, info, csv_path)
        
    else:
        # Modo interativo
        CAMINHO_PDF = r"S:/work/eg-goncalves/pdfs/" + input("Digite o nome do arquivo PDF: ")
        CAMINHO_CSV = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Digite o nome do arquivo CSV de saída: ")
        
        try:
            pag_ini = int(input("Página inicial: "))
            pag_fim_str = input("Página final (enter para todas): ")
            pag_fim = int(pag_fim_str) if pag_fim_str.strip() else None
            
            linhas, info = processar_pdf(CAMINHO_PDF, pag_ini, pag_fim)
            gerar_csv(linhas, info, CAMINHO_CSV)
            
        except Exception as e:
            print(f"Erro: {e}")
