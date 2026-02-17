import pdfplumber
import csv
import re
import sys
import os

# Regex para identificar datas no formato DD/MM - Dia
# Ex: 16/05 - Qui
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2})\s+-\s+(Dom|Seg|Ter|Qua|Qui|Sex|Sáb|Sab)\b', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM
HORARIO_PATTERN = re.compile(r'\b(\d{1,2}:\d{2})\b')

def extrair_informacoes_cabecalho(texto):
    """Extrai informações do cabeçalho do cartão ponto"""
    info = {}
    
    # Nome do funcionário e Matrícula
    # Funcionário: Lucio Nei Ancelmo Antuarte Matrícula: 3783999
    padrao_nome = re.compile(r'Funcionário:\s*(.+?)(?:\s+Matrícula:|\s*$)', re.MULTILINE)
    match_nome = padrao_nome.search(texto)
    if match_nome:
        info['nome_funcionario'] = match_nome.group(1).strip()
    
    # Período
    # Período: 16/05/2024 a 15/06/2024
    padrao_periodo = re.compile(r'Período:\s*(\d{2}/\d{2}/\d{4})\s*a\s*(\d{2}/\d{2}/\d{4})', re.IGNORECASE)
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
        # Se não tem info de período, retorna DD/MM/AAAA placeholder
        # mas como o padrão exige DD/MM/AAAA, melhor tentar algo ou deixar fixo?
        # Vamos deixar com ano atual ou placeholder
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
            # Se mês é 12 e estamos no início do ano seguinte (se baseando no FIM), ano anterior
            if mes == 12 and fim_mes == 1:
                return f"{data_ddmm}/{ini_ano}"
            # Se mês é 1 e estamos no final do ano anterior (se baseando no INICIO), ano seguinte
            if mes == 1 and ini_mes == 12:
                return f"{data_ddmm}/{fim_ano}"
            
            # Fallback: usa ano final
            return f"{data_ddmm}/{fim_ano}"
            
    except:
        return f"{data_ddmm}/{periodo_info.get('ano', 'AAAA')}"

def converter_horario_normalizado(h):
    """Garante formato HH:MM (07:00 ao invés de 7:00)"""
    partes = h.split(':')
    if len(partes) == 2:
        return f"{int(partes[0]):02d}:{int(partes[1]):02d}"
    return h

def processar_texto(texto):
    """Processa o texto completo extraído"""
    linhas_csv = []
    info_cabecalho = extrair_informacoes_cabecalho(texto)
    
    print(f"Info Cabeçalho: {info_cabecalho}")
    
    linhas_texto = texto.split('\n')
    i = 0
    total_linhas = len(linhas_texto)
    
    while i < total_linhas:
        linha = linhas_texto[i].strip()
        
        # Procura por linha de data
        match_data = DATA_PATTERN.search(linha)
        if match_data:
            data_ddmm = match_data.group(1)
            data_completa = extrair_ano_da_data(data_ddmm, info_cabecalho)
            
            # Verifica texto na própria linha da data (pode ter 'Folga', 'Feriado', etc)
            # Remove a parte da data para verificar o resto
            resto_linha_data = linha[match_data.end():].lower()
            
            entrada1 = ""
            saida1 = ""
            
            if "folga" in resto_linha_data or "feriado" in resto_linha_data or "compensar" in resto_linha_data:
                pass
            
            # Procura nas próximas linhas por marcações (até encontrar outra data ou fim)
            j = i + 1
            encontrou_marcacao = False
            pode_ser_ponto = True

            while j < total_linhas:
                prox_linha = linhas_texto[j].strip()
                
                # Se encontrar outra data, para
                if DATA_PATTERN.search(prox_linha):
                    break
                
                # Verifica se é linha de marcação REAL
                tem_horario = HORARIO_PATTERN.search(prox_linha)
                
                # Regex para identificar horários planejados (ex: 13:00 - 18:00)
                # O usuário reclamou de "conjunto inicial separados entre traços"
                # Garante que detectamos padrões como HH:MM-HH:MM ou HH:MM - HH:MM
                eh_planejado = re.search(r'\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}', prox_linha)
                
                # Palavras-chave que indicam que a linha deve ser ignorada (mas pode haver ponto depois, ex: quebra de pág)
                palavras_ignorar_linha = [
                    "documento assinado", "fls.:", 
                    "calamidade", "crédito", "dsr", "feriado", "férias", "irregulares"
                ]
                
                # Palavras-chave que indicam FIM da leitura de ponto para aquele dia/período (rodapés de totais)
                palavras_encerrar_dia = [
                    "banco de horas", "saldo", "eventos gerados", "horas contratuais"
                ]
                
                eh_ignorar = any(p in prox_linha.lower() for p in palavras_ignorar_linha)
                eh_encerrar = any(p in prox_linha.lower() for p in palavras_encerrar_dia)
                eh_ocorrencia = eh_ignorar or eh_encerrar
                
                if eh_encerrar:
                    pode_ser_ponto = False
                
                if tem_horario and not eh_planejado and not eh_ocorrencia and pode_ser_ponto:
                    # É linha de marcação!
                    # Extrai todos horários
                    todos_horarios = HORARIO_PATTERN.findall(prox_linha)
                    validos = []
                    for h in todos_horarios:
                        # Filtra valores válidos
                        validos.append(converter_horario_normalizado(h))
                    
                    if len(validos) >= 1:
                        entrada1 = validos[0]
                    if len(validos) >= 2:
                        saida1 = validos[1]
                        
                    encontrou_marcacao = True
                    # Assume apenas 1 linha de marcação válida por dia, ou a primeira é a que conta
                    pode_ser_ponto = False 
                
                # Se não é marcação mas tem texto relevante (Ocorrência)
                # if prox_linha and not eh_planejado:
                #    if eh_ocorrencia or "folga" in prox_linha.lower():
                #        # Concatena obs se já existir
                #        if obs:
                #            obs += " | " + prox_linha
                #        else:
                #            obs = prox_linha
                
                j += 1
            
            # Registra no CSV
            linhas_csv.append([
                data_completa,
                entrada1,
                saida1,
                "", # Entrada2
                "", # Saida2
            ])
            
            # Avança o índice principal
            # Não avançamos j inteiramente pois o loop externo vai continuar linha por linha
            # Mas podemos pular para j-1 para otimizar? 
            # Não, melhor deixar o loop externo continuar, ele vai ignorar linhas que não são data
            # até achar a próxima data.
            
        i += 1
            
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
        print("--- Conversor Black Coca-Cola 2 ---")
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
