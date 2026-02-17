import pdfplumber
import csv
import re
import sys
import os
from collections import OrderedDict

# Regex para identificar datas no formato DD/MM seguido de dia da semana
# Ex: 15/07 SEG
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2})\s+(SEG|TER|QUA|QUI|SEX|SAB|DOM)\b', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')

def extrair_informacoes_cabecalho(texto):
    """Extrai informações do cabeçalho do cartão ponto (black-horizontal-5)"""
    info = {}
    
    # Empregado: 101320 Leticia Mello de Oliveira Data Admissão:15/07/2024
    padrao_nome = re.compile(r'Empregado:\s*\d+\s+(.+?)(?:\s+Data|\s*$)', re.MULTILINE)
    match_nome = padrao_nome.search(texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(1).strip()
    
    # Período : 15/07/2024 a 31/07/2024
    padrao_periodo = re.compile(r'Período\s*:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})', re.IGNORECASE)
    match_periodo = padrao_periodo.search(texto)
    if match_periodo:
        info['periodo_inicial'] = match_periodo.group(1)
        info['periodo_final'] = match_periodo.group(2)
        
        # Extrai mês/ano da data final para referência
        partes = match_periodo.group(2).split('/')
        info['ano'] = partes[2]
        
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
    
    # Verifica se é folga/repouso/feriado e define obs inicial
    linha_lower = linha.lower()
    obs = ""
    if 'repouso' in linha_lower:
        obs = "FOLGA_DSR"
    elif 'feriado' in linha_lower:
        obs = "FOLGA_FERIADO"
    elif 'ausência' in linha_lower or 'ausencia' in linha_lower:
         obs = "FALTA" # Ou apenas deixar vazio e deixar as colunas vazias falarem por si
         # No exemplo temos: "Ausência p/Comp Feriado 07:20", "Ausência p/ Compens. N: 00:55"
         # Vamos capturar os horários de qualquer forma.

    # Extrai horários
    # Ex: 15/07 SEG 0041 11:05 13:52 15:12 20:22 07:20 00:37
    # Regex pega todas HH:MM
    horarios = HORARIO_PATTERN.findall(linha)
    
    entrada1, saida1, entrada2, saida2 = "", "", "", ""
    
    # Ignora horários que pareçam "totais" se tivermos muitos.
    # A estratégia será pegar os primeiros 4.
    # Mas no exemplo temos: 11:05 13:52 15:12 20:22 07:20 00:37
    # As 4 primeiras são as batidas. 07:20 e 00:37 são totais.
    
    batidas = []
    
    # Filtragem básica de horários inválidos visualmente não é necessária pois o regex já é restritivo
    # Mas podemos validar ranges se precisar.
    
    for h in horarios:
         batidas.append(h)

    # Se for Repouso/Feriado explicito na linha, as vezes não tem batidas, ou tem total 07:20.
    # Ex: 21/07 DOM 9999 Repouso (Domingo) -> 0 batidas
    # Ex: 27/09 SEX 0203 Ausência p/Comp Feriado 07:20 -> 1 horário (07:20) que é total
    
    if obs in ["FOLGA_DSR", "FOLGA_FERIADO"] and len(batidas) < 2:
        # Se for folga e tiver poucas "batidas" (provavelmente totais), ignoramos batidas
        pass 
    else:
        # Tenta preencher as 4 batidas
        if len(batidas) >= 1: entrada1 = batidas[0]
        if len(batidas) >= 2: saida1 = batidas[1]
        if len(batidas) >= 3: entrada2 = batidas[2]
        if len(batidas) >= 4: saida2 = batidas[3]
        
    return {
        "data": data_completa,
        "entrada1": entrada1,
        "saida1": saida1,
        "entrada2": entrada2,
        "saida2": saida2,
        "obs": obs if obs else ""
    }

def processar_texto(texto):
    """Processa o texto completo extraído"""
    linhas_csv = []
    info_cabecalho = extrair_informacoes_cabecalho(texto)
    
    print(f"Info Cabeçalho: {info_cabecalho}")
    
    # Divide em linhas e processa
    for linha in texto.split('\n'):
        linha = linha.strip()
        if not linha:
            continue
            
        dados_linha = processar_linha_data(linha, info_cabecalho)
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
            texto_completo += page.extract_text() + "\n"
            
    return processar_texto(texto_completo)

def gerar_csv(linhas, info_cabecalho, caminho_csv):
    """Gera o arquivo CSV"""
    with open(caminho_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Cabeçalho metadata
        if info_cabecalho:
            writer.writerow([f"# Funcionário: {info_cabecalho.get('nome_funcionario', '')}"])
            # writer.writerow([f"# Cargo: {info_cabecalho.get('cargo', '')}"]) # Cargo não extraído robustamente no novo regex, opcional
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
            
            # Print preview for validation
            print("\nPreview das primeiras linhas:")
            for l in linhas[:5]:
                print(l)
        else:
            print(f"Arquivo de exemplo não encontrado: {txt_path}")
        
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
