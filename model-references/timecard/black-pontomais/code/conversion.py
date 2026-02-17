import pdfplumber
import csv
import re
import tkinter as tk
from tkinter import filedialog
from pathlib import Path


def extrair_horarios_sequenciais(tokens):
    """
    Extrai horários no formato HH:MM de uma lista de tokens.
    Para quando encontrar um horário menor que o anterior.
    """
    horarios = []
    ultimo_horario = None
    
    for token in tokens:
        # Verifica se o token é um horário no formato HH:MM
        if re.match(r'^\d{2}:\d{2}$', token):
            # Converte para minutos para comparação
            horas, minutos = map(int, token.split(':'))
            horario_em_minutos = horas * 60 + minutos
            
            # Se já temos um horário anterior, verifica se o atual é menor
            if ultimo_horario is not None and horario_em_minutos < ultimo_horario:
                break  # Para de ler horários
            
            horarios.append(token)
            ultimo_horario = horario_em_minutos
            
            # Limita a 4 horários (Entrada1, Saída1, Entrada2, Saída2)
            if len(horarios) == 4:
                break
    
    return horarios


def extrair_data(linha):
    """
    Extrai a data no formato DD/MM/YYYY de uma linha.
    """
    # Procura por padrões de data com dia da semana
    match = re.search(r'(Seg|Ter|Qua|Qui|Sex|Sáb|Sab|Dom),?\s*(\d{2}/\d{2}/\d{4})', linha, re.IGNORECASE)
    if match:
        return match.group(2)
    
    # Procura apenas pela data
    match = re.search(r'\d{2}/\d{2}/\d{4}', linha)
    if match:
        return match.group(0)
    
    return None


def processar_pdf_para_csv(arquivo_pdf, arquivo_csv):
    """
    Processa o PDF e gera um arquivo CSV com as colunas Data, Entrada1, Saída1, Entrada2, Saída2.
    """
    linhas_csv = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for page in pdf.pages:
            texto_pagina = page.extract_text()
            if not texto_pagina:
                continue
            
            linhas = texto_pagina.split('\n')
            for linha in linhas:
                linha = linha.strip()
                
                # Extrai a data da linha
                data = extrair_data(linha)
                if not data:
                    continue
                
                # Divide a linha em tokens
                tokens = linha.split()
                
                # Extrai os horários sequenciais
                horarios = extrair_horarios_sequenciais(tokens)
                
                # Se encontrou pelo menos um horário, adiciona ao CSV
                if horarios:
                    entrada1 = horarios[0] if len(horarios) > 0 else ""
                    saida1 = horarios[1] if len(horarios) > 1 else ""
                    entrada2 = horarios[2] if len(horarios) > 2 else ""
                    saida2 = horarios[3] if len(horarios) > 3 else ""
                    
                    linhas_csv.append([data, entrada1, saida1, entrada2, saida2])
    
    # Escreve o CSV usando ponto-e-vírgula como delimitador
    with open(arquivo_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["Data", "Entrada1", "Saída1", "Entrada2", "Saída2"])
        for linha in linhas_csv:
            writer.writerow(linha)
    
    print(f"CSV gerado com sucesso em: {arquivo_csv}")
    return True


def selecionar_arquivos():
    """
    Abre interface gráfica para seleção do arquivo PDF e local de saída.
    """
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal
    
    # Diretório padrão de entrada
    dir_entrada_padrao = "S:/work/eg-goncalves/pdfs/"
    # Verifica se o diretório existe, senão usa o diretório atual
    if not Path(dir_entrada_padrao).exists():
        dir_entrada_padrao = "."
    
    # Seleciona o arquivo PDF
    arquivo_pdf = filedialog.askopenfilename(
        title="Selecione o arquivo PDF",
        initialdir=dir_entrada_padrao,
        filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
    )
    
    if not arquivo_pdf:
        print("Nenhum arquivo PDF selecionado.")
        return
    
    # Diretório padrão de saída
    dir_saida_padrao = "S:/work/eg-goncalves/resultados/tentativas/"
    # Verifica se o diretório existe, senão usa o diretório atual
    if not Path(dir_saida_padrao).exists():
        dir_saida_padrao = "."
    
    # Define nome padrão do arquivo de saída
    nome_arquivo = Path(arquivo_pdf).stem
    arquivo_csv_padrao = f"{nome_arquivo}_convertido.csv"
    
    # Seleciona o local de saída
    arquivo_csv = filedialog.asksaveasfilename(
        title="Salvar arquivo CSV como",
        initialdir=dir_saida_padrao,
        initialfile=arquivo_csv_padrao,
        defaultextension=".csv",
        filetypes=[("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
    )
    
    if not arquivo_csv:
        print("Nenhum local de saída selecionado.")
        return
    
    # Processa o PDF
    try:
        processar_pdf_para_csv(arquivo_pdf, arquivo_csv)
        print("\nProcessamento concluído!")
    except Exception as e:
        print(f"\nErro ao processar o arquivo: {e}")


if __name__ == "__main__":
    selecionar_arquivos()
