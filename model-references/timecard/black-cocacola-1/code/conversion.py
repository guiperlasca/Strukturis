import pdfplumber
import csv
import re
from collections import OrderedDict

# Regex para identificar datas no formato DD/MM/YYYY seguido de dia da semana
DATA_PATTERN = re.compile(r'^(\d{2}/\d{2}/\d{4})\s+(Seg|Ter|Qua|Qui|Sex|Sáb|Dom)\b', flags=re.IGNORECASE)

# Regex para extrair horários no formato HH:MM
HORARIO_PATTERN = re.compile(r'\b(\d{2}:\d{2})\b')

def processar_pdf_para_csv(arquivo_pdf, arquivo_csv):
    linhas_csv = []
    data_anterior = None
    entrada_pendente = None

    with pdfplumber.open(arquivo_pdf) as pdf:
        for i, page in enumerate(pdf.pages):
            if i < initial_page -1 or i > final_page:
                continue
                
            texto = page.extract_text()
            if not texto:
                continue

            for linha in texto.split('\n'):
                linha = linha.strip()
                
                # Verifica se é linha de data
                data_match = DATA_PATTERN.search(linha)
                if data_match:
                    data = data_match.group(1)
                    horarios = HORARIO_PATTERN.findall(linha)
                    
                    # Filtra horários válidos (entre 00:00 e 23:59)
                    horarios = [h for h in horarios if 0 <= int(h.split(':')[0]) < 24]
                    
                    # Mesma data em múltiplas linhas
                    if data == data_anterior:
                        if horarios and entrada_pendente:
                            saida = horarios[0]
                            linhas_csv.append([data, entrada_pendente, saida])
                            entrada_pendente = None
                        continue
                    
                    # Nova data
                    data_anterior = data
                    
                    if len(horarios) >= 2:
                        entrada = horarios[0]
                        saida = horarios[1]
                        linhas_csv.append([data, entrada, saida])
                    elif len(horarios) == 1:
                        entrada_pendente = horarios[0]
                    else:
                        linhas_csv.append([data, '', ''])
                
                # Processa linhas subsequentes para mesma data
                elif entrada_pendente:
                    horarios = HORARIO_PATTERN.findall(linha)
                    if horarios:
                        saida = horarios[0]
                        linhas_csv.append([data_anterior, entrada_pendente, saida])
                        entrada_pendente = None

    # Remove datas duplicadas mantendo a ordem original
    registros_unicos = OrderedDict()
    for data, entrada, saida in linhas_csv:
        if data not in registros_unicos:
            registros_unicos[data] = (entrada, saida)
        else:
            # Mantém o maior horário de saída
            if saida and (saida > registros_unicos[data][1] or not registros_unicos[data][1]):
                registros_unicos[data] = (registros_unicos[data][0], saida)

    # Escreve o CSV mantendo a ordem original
    with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["Data", "Entrada1", "Saída1"])
        for data, (entrada, saida) in registros_unicos.items():
            writer.writerow([data, entrada, saida])
    
    print(f"Arquivo CSV gerado com sucesso: {arquivo_csv}")

if __name__ == "__main__":
    pdf_input = r"S:/work/eg-goncalves/pdfs/"
    csv_output = r"S:/work/eg-goncalves/resultados/tentativas/"
    
    pdf_input += input("Digite o nome do arquivo PDF (ex: cartao_ponto.pdf): ")
    csv_output += input("Digite o nome do arquivo CSV de saída (ex: resultado.csv): ")

    initial_page = int(input("Digite o número da página inicial (ex: 71): "))
    final_page = int(input("Digite o número da página final (ex: 89): "))

    processar_pdf_para_csv(pdf_input, csv_output)

# OBS.: AJUSTAR PARA ENTRADA2/SAIDA2 OU MAIS, SE NECESSÁRIO