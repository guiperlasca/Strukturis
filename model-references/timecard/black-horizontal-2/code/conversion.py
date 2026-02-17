import pdfplumber
import csv
import re
from collections import OrderedDict
from datetime import datetime


# Regex para identificar data no novo formato: DD/MM dia_semana
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2})\s+([a-zá]+)', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')

# Mapeamento de abreviações de dias da semana
DIAS_SEMANA = {'seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom'}


def converter_horario_para_minutos(horario):
    """
    Converte horário HH:MM para minutos totais para comparação
    """
    partes = horario.split(':')
    return int(partes[0]) * 60 + int(partes[1])


def extrair_periodo_ano(texto):
    """
    Extrai o período (datas inicial e final) e o ano do texto do cabeçalho
    Retorna: (periodo_inicial, periodo_final, ano)
    
    Ponto 1: Extrai o ano correto da linha exclusiva "DD/MM/YYYY à DD/MM/YYYY"
    """
    # Padrão: "01/03/2021 à 31/03/2021"
    padrao_periodo = re.compile(r'(\d{2}/\d{2})/(\d{4})\s+[àa]\s+(\d{2}/\d{2})/(\d{4})')
    match = padrao_periodo.search(texto)
    
    if match:
        dia_mes_inicial = match.group(1)
        ano_inicial = match.group(2)
        dia_mes_final = match.group(3)
        ano_final = match.group(4)
        
        periodo_inicial = f"{dia_mes_inicial}/{ano_inicial}"
        periodo_final = f"{dia_mes_final}/{ano_final}"
        # Usa o ano final como referência
        ano = ano_final
        
        return periodo_inicial, periodo_final, ano
    
    return None, None, None


def extrair_mes_ano_da_data(data_str, ano):
    """
    Converte DD/MM para DD/MM/YYYY usando o ano extraído
    """
    if ano and len(data_str) == 5:  # DD/MM
        return f"{data_str}/{ano}"
    return data_str


def extrair_informacoes_cabecalho(texto):
    """
    Extrai informações do cabeçalho do espelho de ponto
    """
    info = {}
    
    # Período e ano
    periodo_inicial, periodo_final, ano = extrair_periodo_ano(texto)
    if periodo_inicial:
        info['periodo_inicial'] = periodo_inicial
        info['periodo_final'] = periodo_final
        info['ano'] = ano
        # Extrai mês/ano da data final
        partes = periodo_final.split('/')
        info['mes_ano'] = f"{partes[1]}/{partes[2]}"
    
    # Nome da empresa
    padrao_empresa = re.compile(r'UBEA\s+(.+?)\s+CNPJ', re.MULTILINE)
    match_empresa = padrao_empresa.search(texto)
    if match_empresa:
        info['empresa'] = match_empresa.group(1).strip()
    
    # CNPJ
    padrao_cnpj = re.compile(r'CNPJ:\s*([\d./\-]+)')
    match_cnpj = padrao_cnpj.search(texto)
    if match_cnpj:
        info['cnpj'] = match_cnpj.group(1).strip()
    
    # Código e departamento
    padrao_depto = re.compile(r'(\d+)\s*-\s*(.+?)(?:\n|$)', re.MULTILINE)
    matches_depto = padrao_depto.findall(texto)
    if matches_depto:
        # Procura pelo primeiro que parece ser um departamento (não é ID de funcionário)
        for codigo, descricao in matches_depto:
            if len(codigo) == 4 and not descricao.startswith(('WALESKA', 'MARISA')):
                info['departamento_codigo'] = codigo
                info['departamento'] = descricao.strip()
                break
    
    # Nome do funcionário
    padrao_nome = re.compile(r'(\d+)\s*-\s*([A-Z][A-Z\s]+?)\s*-\s*(\d+)(?:\s|$)')
    match_nome = padrao_nome.search(texto)
    if match_nome:
        info['id_funcionario'] = match_nome.group(1).strip()
        info['nome_funcionario'] = match_nome.group(2).strip()
        info['horas_mensais'] = match_nome.group(3).strip()
    
    # Cargo/Função
    padrao_cargo = re.compile(r'(?:CENTRAL AGENDAMENTO|DEPARTAMENTO)\s+(.+?)(?:\n|$)', re.MULTILINE)
    match_cargo = padrao_cargo.search(texto)
    if match_cargo:
        info['cargo'] = match_cargo.group(1).strip()
    
    # Horário de trabalho (formato: 13:00-19:00 intervalo 16:00-16:15)
    padrao_horario = re.compile(r'HSL\s+[\d\w()]+\s+([\d:]+)-([\d:]+)\s+intervalo\s+([\d:]+)-([\d:]+)')
    match_horario = padrao_horario.search(texto)
    if match_horario:
        info['horario_entrada'] = match_horario.group(1)
        info['horario_saida'] = match_horario.group(2)
        info['intervalo_inicio'] = match_horario.group(3)
        info['intervalo_fim'] = match_horario.group(4)
    
    return info


def eh_folga_ou_ausencia(linha):
    """
    Verifica se a linha indica folga, feriado, não admitido, etc.
    """
    linha_lower = linha.lower()
    
    if 'n.admitido' in linha_lower or 'não admitido' in linha_lower:
        return 'NAO_ADMITIDO'
    elif 'feriado' in linha_lower:
        return 'FERIADO'
    elif '(f)' in linha_lower or 'folga' in linha_lower:
        return 'FOLGA'
    elif '(n)' in linha_lower:
        return 'NORMAL'
    
    return None


def extrair_horarios_da_linha(linha):
    """
    Extrai horários válidos da linha, respeitando:
    - Ponto 2: Para em traço (-)
    - Ponto 3: Apenas horários maiores que o anterior
    - Ponto 4: Ignora os 4 primeiros horários (previstos)
    
    Retorna: lista com apenas os horários realizados válidos
    """
    # Ponto 2: Se houver traço, pega apenas até ele
    if '-' in linha:
        linha = linha.split('-')[0].strip()
    
    # Extrai todos os horários
    horarios = HORARIO_PATTERN.findall(linha)
    
    # Filtra horários válidos (entre 00:00 e 23:59)
    horarios_validos = []
    for h in horarios:
        horas, minutos = map(int, h.split(':'))
        if 0 <= horas < 24 and 0 <= minutos < 60:
            horarios_validos.append(h)
    
    # Ponto 4: Se tem mais de 4 horários, os primeiros 4 são previstos (ignorar)
    if len(horarios_validos) > 4:
        horarios_realizados = horarios_validos[4:]
    else:
        horarios_realizados = horarios_validos
    
    # Ponto 3: Filtra apenas horários maiores que o anterior (crescente)
    horarios_filtrados = []
    ultimo_minutos = -1
    
    for horario in horarios_realizados:
        horario_minutos = converter_horario_para_minutos(horario)
        
        # Se o horário é maior que o anterior, adiciona
        if horario_minutos > ultimo_minutos:
            horarios_filtrados.append(horario)
            ultimo_minutos = horario_minutos
    
    return horarios_filtrados


def processar_pdf_espelho_ponto_para_csv(arquivo_pdf, arquivo_csv, pagina_inicial=1, pagina_final=None):
    """
    Processa o PDF do espelho de ponto e gera CSV com as marcações
    """
    linhas_csv = []
    informacoes_cabecalho = None
    ano_processamento = None
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        total_paginas = len(pdf.pages)
        pagina_final = pagina_final or total_paginas
        
        print(f"Processando páginas {pagina_inicial} a {pagina_final} de {total_paginas} páginas...")
        
        for i, page in enumerate(pdf.pages):
            # Ajusta índices (usuário digita 1-based, código usa 0-based)
            if i < pagina_inicial - 1 or i >= pagina_final:
                continue
                
            print(f"\nProcessando página {i + 1}...")
            
            texto = page.extract_text()
            if not texto:
                continue
            
            # Extrai informações do cabeçalho de cada página
            # Ponto 1: Extrai o ano correto de cada página
            informacoes_pagina = extrair_informacoes_cabecalho(texto)
            
            if informacoes_pagina.get('ano'):
                ano_processamento = informacoes_pagina['ano']
            
            # Usa informações da primeira página para cabeçalho do CSV
            if not informacoes_cabecalho:
                informacoes_cabecalho = informacoes_pagina
                
                print(f"Funcionário: {informacoes_cabecalho.get('nome_funcionario', 'NÃO IDENTIFICADO')}")
                print(f"Cargo: {informacoes_cabecalho.get('cargo', 'NÃO IDENTIFICADO')}")
                print(f"Departamento: {informacoes_cabecalho.get('departamento', 'NÃO IDENTIFICADO')}")
                if 'periodo_inicial' in informacoes_cabecalho:
                    print(f"Período: {informacoes_cabecalho['periodo_inicial']} até {informacoes_cabecalho['periodo_final']}")
            
            # Processa cada linha do texto
            for linha in texto.split('\n'):
                linha = linha.strip()
                if not linha:
                    continue
                
                # Verifica se é linha com data (DD/MM + dia semana)
                data_match = DATA_PATTERN.search(linha)
                if data_match:
                    data_ddmm = data_match.group(1)
                    dia_semana = data_match.group(2).lower()
                    
                    # Valida se é realmente um dia da semana
                    if dia_semana not in DIAS_SEMANA:
                        continue
                    
                    # Converte para formato completo DD/MM/YYYY
                    data_completa = extrair_mes_ano_da_data(data_ddmm, ano_processamento)
                    
                    # Verifica tipo de ocorrência
                    tipo_ocorrencia = eh_folga_ou_ausencia(linha)
                    
                    if tipo_ocorrencia in ['NAO_ADMITIDO', 'FERIADO']:
                        # Não registra marcações para esses casos
                        linhas_csv.append([data_completa, '', '', '', ''])
                        print(f"{data_completa}: {tipo_ocorrencia}")
                        continue
                    elif tipo_ocorrencia == 'FOLGA':
                        linhas_csv.append([data_completa, '', '', '', ''])
                        print(f"{data_completa}: FOLGA")
                        continue
                    
                    # Extrai horários da linha (com todas as correções)
                    horarios = extrair_horarios_da_linha(linha)
                    
                    if not horarios:
                        linhas_csv.append([data_completa, '', '', '', ''])
                        print(f"{data_completa}: SEM HORÁRIOS")
                        continue
                    
                    # Mapeia os horários para entrada1, saída1, entrada2, saída2
                    entrada1 = horarios[0] if len(horarios) > 0 else ''
                    saida1 = horarios[1] if len(horarios) > 1 else ''
                    entrada2 = horarios[2] if len(horarios) > 2 else ''
                    saida2 = horarios[3] if len(horarios) > 3 else ''
                    
                    linhas_csv.append([data_completa, entrada1, saida1, entrada2, saida2])
                    
                    print(f"{data_completa}: Horários: {horarios} → E1: {entrada1}, S1: {saida1}, E2: {entrada2}, S2: {saida2}")
    
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
            writer.writerow([f"# Departamento: {informacoes_cabecalho.get('departamento', 'NÃO IDENTIFICADO')}"])
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
    nome_pdf = input("Digite o nome do arquivo PDF (ex: espelho_ponto.pdf): ")
    nome_csv = input("Digite o nome do arquivo CSV de saída (ex: resultado.csv): ")
    
    pdf_input += nome_pdf
    csv_output += nome_csv
    
    pagina_inicial = int(input("Digite o número da página inicial (ex: 1): "))
    pagina_final_input = input("Digite o número da página final (deixe em branco para processar até o final): ")
    pagina_final = int(pagina_final_input) if pagina_final_input.strip() else None
    
    # Processa o arquivo
    try:
        processar_pdf_espelho_ponto_para_csv(pdf_input, csv_output, pagina_inicial, pagina_final)
    except FileNotFoundError:
        print("❌ Erro: Arquivo não encontrado. Verifique o caminho e nome do arquivo.")
    except Exception as e:
        print(f"❌ Erro ao processar o arquivo: {e}")
        print("Verifique se o arquivo é um PDF válido e se tem permissões de leitura.")