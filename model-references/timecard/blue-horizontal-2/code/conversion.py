import pdfplumber
import csv
import re
from collections import OrderedDict
from typing import Optional, List, Dict, Tuple


# Dias da semana para validar linhas de marcação
DIAS_SEMANA = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

# Regex para identificar linhas de marcação: DD DIA [F] HH:MM HH:MM
# Formato: "16 Qui 05:47 14:22" ou "25 Sáb F 05:50 14:22" ou "02 Dom" (sem horários)
LINHA_MARCACAO_PATTERN = re.compile(
    r'^(\d{1,2})\s+(Seg|Ter|Qua|Qui|Sex|Sáb|Dom)(?:\s+F)?(?:\s+(.*))?$',
    flags=re.IGNORECASE
)

# Regex para extrair horários no formato HH:MM (com possível 'x' no final)
HORARIO_PATTERN = re.compile(r'(\d{2}:\d{2})x?')

# Regex para extrair período do cabeçalho
PERIODO_PATTERN = re.compile(r'Período:\s*(\d{2}\.\d{2}\.\d{4})\s*até\s*(\d{2}\.\d{2}\.\d{4})')

# Regex para extrair nome do funcionário
FUNCIONARIO_PATTERN = re.compile(r'Funcionário:\s*(\d+)\s+(.+?)\s+Regime')


def converter_data_format(data_dot: str) -> str:
    """Converte data de DD.MM.YYYY para DD/MM/YYYY"""
    return data_dot.replace('.', '/')


def extrair_informacoes_cabecalho(texto: str) -> Dict[str, str]:
    """
    Extrai informações do cabeçalho do cartão ponto STIHL.
    """
    info = {}
    
    # Nome do funcionário
    match_func = FUNCIONARIO_PATTERN.search(texto)
    if match_func:
        info['codigo_funcionario'] = match_func.group(1)
        info['nome_funcionario'] = match_func.group(2).strip()
    
    # Período
    match_periodo = PERIODO_PATTERN.search(texto)
    if match_periodo:
        info['periodo_inicial'] = converter_data_format(match_periodo.group(1))
        info['periodo_final'] = converter_data_format(match_periodo.group(2))
        
        # Extrai mês/ano da data final
        partes = match_periodo.group(2).split('.')
        info['mes_ano'] = f"{partes[1]}/{partes[2]}"
    
    return info


def extrair_ano_mes_periodo(texto: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extrai o ano e mês do período do cabeçalho.
    Retorna (ano_inicio, mes_inicio, ano_fim, mes_fim) baseado no período.
    """
    match_periodo = PERIODO_PATTERN.search(texto)
    if match_periodo:
        # Data final do período
        data_final = match_periodo.group(2)  # DD.MM.YYYY
        partes = data_final.split('.')
        dia_final = int(partes[0])
        mes_final = int(partes[1])
        ano_final = int(partes[2])
        
        # Data inicial do período
        data_inicial = match_periodo.group(1)  # DD.MM.YYYY
        partes_ini = data_inicial.split('.')
        dia_inicial = int(partes_ini[0])
        mes_inicial = int(partes_ini[1])
        ano_inicial = int(partes_ini[2])
        
        return (ano_inicial, mes_inicial, dia_inicial, ano_final, mes_final, dia_final)
    return None


def determinar_mes_ano_para_dia(dia: int, periodo_info: Tuple) -> Tuple[int, int]:
    """
    Determina o mês e ano correto para um dia baseado no período.
    O período vai de dia X de um mês até dia Y do próximo mês (geralmente 16 até 15).
    """
    if periodo_info is None:
        return (1, 2020)  # Fallback
    
    ano_ini, mes_ini, dia_ini, ano_fim, mes_fim, dia_fim = periodo_info
    
    # Se o dia é maior ou igual ao dia inicial, pertence ao mês inicial
    if dia >= dia_ini:
        return (mes_ini, ano_ini)
    else:
        # Senão pertence ao mês final
        return (mes_fim, ano_fim)


def processar_linha_marcacao(linha: str) -> Optional[Dict[str, str]]:
    """
    Processa uma linha de marcação de ponto.
    Retorna dict com dia, entrada1, saida1, entrada2, saida2.
    """
    linha = linha.strip()
    
    match = LINHA_MARCACAO_PATTERN.match(linha)
    if not match:
        return None
    
    dia = match.group(1).zfill(2)  # Garante 2 dígitos
    dia_semana = match.group(2)
    resto = match.group(3) or ''
    
    # Extrai horários da linha
    horarios = HORARIO_PATTERN.findall(resto)
    
    entrada1 = ''
    saida1 = ''
    entrada2 = ''
    saida2 = ''
    
    if len(horarios) >= 1:
        entrada1 = horarios[0]
    if len(horarios) >= 2:
        saida1 = horarios[1]
    if len(horarios) >= 3:
        entrada2 = horarios[2]
    if len(horarios) >= 4:
        saida2 = horarios[3]
    
    return {
        'dia': dia,
        'dia_semana': dia_semana,
        'entrada1': entrada1,
        'saida1': saida1,
        'entrada2': entrada2,
        'saida2': saida2
    }


def processar_pdf_cartao_ponto_para_csv(arquivo_pdf: str, arquivo_csv: str, 
                                         pagina_inicial: int = 1, 
                                         pagina_final: Optional[int] = None) -> int:
    """
    Processa o PDF do cartão ponto STIHL (blue-horizontal-2) e gera CSV.
    """
    registros = OrderedDict()
    informacoes_cabecalho = None
    periodo_atual = None
    
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
            
            # Extrai informações do cabeçalho
            info_pagina = extrair_informacoes_cabecalho(texto)
            if not informacoes_cabecalho and info_pagina:
                informacoes_cabecalho = info_pagina
                print(f"Funcionário: {informacoes_cabecalho.get('nome_funcionario', 'NÃO IDENTIFICADO')}")
                if 'periodo_inicial' in informacoes_cabecalho:
                    print(f"Período: {informacoes_cabecalho['periodo_inicial']} até {informacoes_cabecalho['periodo_final']}")
            
            # Extrai período desta página para calcular datas corretas
            periodo_atual = extrair_ano_mes_periodo(texto)
            
            # Processa cada linha do texto
            dentro_tabela = False
            for linha in texto.split('\n'):
                linha = linha.strip()
                if not linha:
                    continue
                
                # Detecta início da tabela de marcações
                if 'Dia' in linha and 'Entr.' in linha and 'Saída' in linha:
                    dentro_tabela = True
                    continue
                
                # Detecta fim da tabela
                if 'Documento assinado' in linha or 'STIHL Relatório' in linha:
                    dentro_tabela = False
                    continue
                
                if dentro_tabela:
                    marcacao = processar_linha_marcacao(linha)
                    if marcacao:
                        # Determina mês/ano correto para este dia
                        mes, ano = determinar_mes_ano_para_dia(int(marcacao['dia']), periodo_atual)
                        
                        # Formata data completa
                        data_completa = f"{marcacao['dia']}/{mes:02d}/{ano}"
                        
                        # Armazena registro (sobrescreve se duplicado)
                        registros[data_completa] = (
                            marcacao['entrada1'],
                            marcacao['saida1'],
                            marcacao['entrada2'],
                            marcacao['saida2']
                        )
                        
                        if marcacao['entrada1'] or marcacao['saida1']:
                            print(f"{data_completa}: E1={marcacao['entrada1']} S1={marcacao['saida1']} E2={marcacao['entrada2']} S2={marcacao['saida2']}")
                        else:
                            print(f"{data_completa}: SEM MARCAÇÕES")
    
    # Escreve o CSV
    with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Cabeçalho do CSV com informações do funcionário
        if informacoes_cabecalho:
            writer.writerow([f"# Funcionário: {informacoes_cabecalho.get('nome_funcionario', 'NÃO IDENTIFICADO')}"])
            if 'periodo_inicial' in informacoes_cabecalho:
                writer.writerow([f"# Período: {informacoes_cabecalho['periodo_inicial']} até {informacoes_cabecalho['periodo_final']}"])
            writer.writerow([])
        
        # Cabeçalho das colunas
        writer.writerow(["Data", "Entrada1", "Saida1", "Entrada2", "Saida2"])
        
        # Dados
        for data, (entrada1, saida1, entrada2, saida2) in registros.items():
            writer.writerow([data, entrada1, saida1, entrada2, saida2])
    
    print(f"\n✅ Arquivo CSV gerado com sucesso: {arquivo_csv}")
    print(f"📊 Total de registros processados: {len(registros)}")
    
    return len(registros)


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
