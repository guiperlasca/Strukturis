import re
import sys
import os
from collections import OrderedDict

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pandas as pd
except ImportError:
    pd = None

def converter_para_float(valor):
    """Converte valores no formato '1.234,56' ou '1.234,56-' para float 1234.56"""
    if not valor:
        return None
    try:
        valor = valor.strip()
        if valor.endswith('-'):
            valor = valor[:-1]
        return float(valor.replace('.', '').replace(',', '.'))
    except:
        return None

def extrair_mes_ano_linha(linha):
    """Extrai mês e ano da linha de cabeçalho 'Demonstrativo de Pagamento ... MM/AAAA'"""
    # Ex: Demonstrativo de Pagamento de Salário 0 M 8 Ê / S 2 /A 0 NO 24
    # O OCR do print.txt veio meio sujo: "0 M 8 Ê / S 2 /A 0 NO 24" -> tente limpar ou pegar padrao
    # Mas no pdfplumber geralmente vem melhor. Vamos tentar ser tolerantes.
    
    # Tentativa 1: Formato padrão MM/AAAA
    match = re.search(r'(\d{2}/\d{4})', linha)
    if match:
        return match.group(1)
        
    # Tentativa 2: OCR sujo do exemplo "0 M 8 Ê / S 2 /A 0 NO 24" -> 08/2024
    # 0 M (8) Ê / S (2) /A (0) NO (24) -> 08/2024
    numeros = re.findall(r'\d+', linha)
    if len(numeros) >= 3:
        # Tenta reconstruir se parecer data
        # Ex no print.txt linha 1: 0 M 8 Ê / S 2 /A 0 NO 24 -> 0, 8, 2, 0, 24
        # Pode ser complexo. Vamos focar no regex padrao e se falhar no print.txt a gente ajusta
        pass
        
    return None

def limpar_linha(linha):
    """Remove caracteres estranhos do inicio da linha que as vezes vem do OCR/Layout"""
    return linha.strip()

def eh_codigo(token):
    return re.match(r'^\d+$', token) and len(token) <= 5

def eh_valor(token):
    # Aceita 1.234,56 ou 123,45 ou 0,02
    return re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}-?$', token)

def parse_entries_in_line(linha):
    """
    Analisa uma linha e tenta extrair 1 ou 2 lançamentos financeiros.
    Formato esperado de um lançamento: [Codigo] [Descricao...] [Ref(opcional)] [Valor]
    """
    parts = linha.split()
    if not parts:
        return []

    # Estratégia: Encontrar índices de tokens que parecem Códigos
    # Um código geralmente é o início de um lançamento.
    indices_codigos = []
    for i, token in enumerate(parts):
        # Heuristica: Codigo é numerico, max 5 digitos.
        # Mas referencias e valores tambem podem parecer, entao cuidado.
        # Geralmente codigo vem antes de texto.
        if eh_codigo(token):
            # Verifica se nao eh uma referencia ou parte de data.
            # Se o proximo token for texto, é forte indicio de Codigo.
            if i + 1 < len(parts) and not eh_valor(parts[i+1]):
                indices_codigos.append(i)
    
    if not indices_codigos:
        return []

    entries = []
    
    # Processa cada bloco iniciado por um código
    for i in range(len(indices_codigos)):
        start_idx = indices_codigos[i]
        # O fim deste bloco é o inicio do proximo, ou o fim da linha
        end_idx = indices_codigos[i+1] if i + 1 < len(indices_codigos) else len(parts)
        
        segment = parts[start_idx:end_idx]
        
        # Agora dentro do segmento: [Codigo] [Desc...] [Ref?] [Valor] [Desc...] [Ref?] [Valor] ??
        # Nao, assumimos que indices_codigos pegou todos os inícios.
        # Entao segment deve ter 1 Codigo e 1 ou 2 Valores no final.
        
        if len(segment) < 2:
            continue
            
        codigo = segment[0]
        
        # Procura valores do fim para o começo do segmento
        valores_encontrados = []
        indices_valores_seg = []
        
        for j in range(len(segment)-1, 0, -1):
            token = segment[j]
            if eh_valor(token):
                valores_encontrados.insert(0, token)
                indices_valores_seg.insert(0, j)
            else:
                # Se achamos um token que nao é valor, e ja temos valores, paramos (os valores estao no fim)
                if valores_encontrados:
                    break
        
        if not valores_encontrados:
            continue
            
        valor_final = valores_encontrados[-1] # Ultimo numero é sempre o valor em R$
        referencia = valores_encontrados[0] if len(valores_encontrados) > 1 else None # Penultimo (se houver) é referencia
        
        # Descricao é tudo entre codigo e o primeiro valor encontrado
        idx_primeiro_valor = indices_valores_seg[0]
        descricao_tokens = segment[1:idx_primeiro_valor]
        descricao = " ".join(descricao_tokens)
        
        entries.append({
            "codigo": codigo,
            "descricao": descricao,
            "referencia": referencia,
            "valor": valor_final,
            "raw": " ".join(segment)
        })
        
    return entries

def processar_linhas_texto(linhas_texto):
    dados_consolidados = OrderedDict()
    
    dados_atual = {}
    mes_ano_atual = None
    dentro_tabela = False
    
    # Buffer para capturar cabeçalhos (Data Adm, Nome) se necessario
    
    for linha in linhas_texto:
        linha = limpar_linha(linha)
        if not linha:
            continue

        # --- 1. Detectar Cabeçalho (Mês/Ano) ---
        # Ex: "Demonstrativo ... 08/2024"
        # No print.txt a linha do mes/ano é bem suja, mas vamos tentar pegar padroes
        if "Demonstrativo de Pagamento" in linha:
            # Tenta extrair data da linha ou linhas proximas na versao final
            # No print.txt, linha 1: "0 M 8 Ê ... NO 24"
            # Vamos usar uma heuristica de contagem: se achamos "Demonstrativo", incrementamos um contador ou algo assim?
            # Melhor: Tentar limpar a string para achar MM/AAAA
            
            # Limpeza especifica para o padrao sujo visto no print.txt
            linha_limpa = linha.replace(" ", "").replace("M", "").replace("Ê", "").replace("/S", "").replace("/A", "").replace("NO", "")
            # "082024" ?
            match_data = re.search(r'(\d{1,2})(\d{4})', linha_limpa)
            
            novo_mes_ano = None
            if match_data:
                mes = match_data.group(1).zfill(2)
                ano = match_data.group(2)
                novo_mes_ano = f"{mes}/{ano}"
            else:
                # Tenta padrao normal MM/AAAA
                m = re.search(r'(\d{2}/\d{4})', linha)
                if m: novo_mes_ano = m.group(1)

            if novo_mes_ano:
                print(f"Novo contracheque detectado: {novo_mes_ano}")
                mes_ano_atual = novo_mes_ano
                
                # Se ja existe, pode ser a segunda pagina do mesmo mes? Ou outro funcionario?
                # Assumindo 1 funcionario por arquivo, se repetir mes, é continuação ou duplicata.
                # Mas nossa estrutura é por MES_ANO. 
                
                if mes_ano_atual not in dados_consolidados:
                    dados_consolidados[mes_ano_atual] = {"MES_ANO": mes_ano_atual}
                
                dados_atual = dados_consolidados[mes_ano_atual]
                dentro_tabela = False
                continue

        if not mes_ano_atual:
            continue

        # --- 2. Detectar Inicio/Fim Tabela ---
        if "CÓD." in linha and "DESCRIÇÃO" in linha:
            dentro_tabela = True
            continue
            
        if "SALÁRIO BASE" in linha or "Total Venctos" in linha or "L í q u i d o" in linha:
            dentro_tabela = False
            continue
            
        # --- 3. Processar Linhas de Dados ---
        if dentro_tabela:
            entries = parse_entries_in_line(linha)
            if not entries:
                continue
            
            # Analise de Duplicidade vs Continuação
            # Cenário A: 1 Entry -> É uma linha normal (que pode estar na esquerda ou direita, mas so tem 1)
            # Cenário B: 2 Entries -> Pode ser Duplicada (Esq == Dir) ou Contincacao (Esq != Dir)
            
            to_add = []
            
            if len(entries) == 1:
                to_add.append(entries[0])
            elif len(entries) >= 2:
                e1 = entries[0]
                e2 = entries[1]
                
                # Verifica se sao iguais (Codigo e Valor iguais)
                # Descricao as vezes varia um caractere no OCR, entao confiamos em Codigo e Valor
                if e1['codigo'] == e2['codigo'] and e1['valor'] == e2['valor']:
                    # É duplicata, pega só o primeiro
                    to_add.append(e1)
                    # print(f"  Duplicata ignorada: {e2['codigo']}")
                else:
                    # Diferentes, então é continuação (folha lado a lado com itens diferentes)
                    to_add.append(e1)
                    to_add.append(e2)
                    # print(f"  Continuação detectada: {e1['codigo']} e {e2['codigo']}")
            
            for entry in to_add:
                chave_val = f"{entry['codigo']} - {entry['descricao']} [VALOR]"
                chave_ref = f"{entry['codigo']} - {entry['descricao']} [REFERENCIA]"
                
                # Adiciona Valor
                # Se já existe, mantemos o maior (comum em pre-processamento onde cabeçalhos repetem)
                # Mas aqui estamos dentro da tabela. Se repetir codigo, pode ser erro?
                # No caso de rescisão, codigos nao repetem.
                # Vamos apenas sobrescrever ou manter se for maior? 
                # Melhor: Sobrescrever (ou somar? nao, contracheque nao soma linhas de mesmo codigo usualmente)
                
                dados_atual[chave_val] = entry['valor']
                if entry['referencia']:
                    dados_atual[chave_ref] = entry['referencia']
                
                print(f"  Processado: {entry['codigo']} - {entry['descricao']} = {entry['valor']}")

    return dados_consolidados

def agrupar_linhas_pdf(page, y_tolerance=3):
    palavras = page.extract_words()
    if not palavras:
        return []
    
    palavras.sort(key=lambda w: (w['top'], w['x0']))
    
    linhas = []
    linha_atual = []
    y_ref = None
    
    for palavra in palavras:
        if y_ref is None or abs(palavra['top'] - y_ref) <= y_tolerance:
            linha_atual.append(palavra)
            y_ref = palavra['top']
        else:
            if linha_atual:
                linhas.append(" ".join([p['text'] for p in linha_atual]))
            linha_atual = [palavra]
            y_ref = palavra['top']
    
    if linha_atual:
        linhas.append(" ".join([p['text'] for p in linha_atual]))
    
    return linhas

def ler_pdf_e_gerar_planilha(caminho_pdf, caminho_excel, paginas_a_ler=None):
    todas_linhas = []
    with pdfplumber.open(caminho_pdf) as pdf:
        total_paginas = len(pdf.pages)
        paginas_a_ler = paginas_a_ler or range(total_paginas)
        
        for i in paginas_a_ler:
            if i >= total_paginas: continue
            print(f"\nProcessando página {i+1}/{total_paginas}...")
            page = pdf.pages[i]
            linhas_pagina = agrupar_linhas_pdf(page)
            todas_linhas.extend(linhas_pagina)
            
    dados = processar_linhas_texto(todas_linhas)
    gerar_excel(dados, caminho_excel)

def ler_texto_exemplo_e_gerar_planilha(caminho_txt, caminho_excel):
    with open(caminho_txt, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
        
    # Remove numeração de linha se houver (formato "1: ...") do view_file
    linhas_limpas = []
    for l in linhas:
        # Remove "1: " no inicio se existir (copia do chat)
        l = re.sub(r'^\d+:\s', '', l)
        linhas_limpas.append(l)

    dados = processar_linhas_texto(linhas_limpas)
    gerar_excel(dados, caminho_excel)

def gerar_excel(dados_consolidados, caminho_excel):
    if not dados_consolidados:
        print("Nenhum dado encontrado.")
        return

    lista_dados = list(dados_consolidados.values())
    
    if pd:
        df = pd.DataFrame(lista_dados)
        cols = ['MES_ANO'] + [c for c in df.columns if c != 'MES_ANO']
        df = df[cols]
        df.to_excel(caminho_excel, index=False)
        print(f"Planilha gerada: {caminho_excel}")
    else:
        print("Pandas ausente. Output JSON:")
        import json
        print(json.dumps(lista_dados, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # Modo de teste rápido se passar argumento 'test'
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        txt_path = os.path.join(base_dir, "examples", "print.txt") # Atualizado para usar print.txt
        excel_path = os.path.join(base_dir, "examples", "resultado_teste.xlsx")
        print(f"Modo de teste: Lendo {txt_path}")
        ler_texto_exemplo_e_gerar_planilha(txt_path, excel_path)
    else:
        # Modo interativo com seleção de páginas
        CAMINHO_PDF = r"S:/work/eg-goncalves/pdfs/" + input("Digite o nome do arquivo PDF: ")
        CAMINHO_EXCEL = r"S:/work/eg-goncalves/resultados/tentativas/" + input("Digite o nome do arquivo Excel de saída: ")
        
        try:
            pagina_inicial = int(input("Digite o número da página inicial: ")) - 1
            pagina_final = int(input("Digite o número da página final: "))
            
            ler_pdf_e_gerar_planilha(
                CAMINHO_PDF, 
                CAMINHO_EXCEL,
                paginas_a_ler=range(pagina_inicial, pagina_final)
            )
        except ValueError:
            print("Entrada inválida para número de páginas. Processando tudo.")
            ler_pdf_e_gerar_planilha(CAMINHO_PDF, CAMINHO_EXCEL)
