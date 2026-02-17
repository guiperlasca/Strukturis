"""
Strukturis Pro — Motor de Modelos Inteligentes de Documentos
Suporta múltiplas variantes por tipo (ex: contracheque-default, contracheque-belshop).
Auto-detecção inteligente com sub-variante matching.
"""

import re
import pandas as pd


def _to_float_br(valor):
    if not valor:
        return None
    try:
        valor = valor.strip().rstrip('-')
        return float(valor.replace('.', '').replace(',', '.'))
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Base
# ═══════════════════════════════════════════════════════════════════════════

class BaseDocumentModel:
    NAME = "Genérico"
    ICON = "fa5s.file-alt"
    DESCRIPTION = "Modelo genérico"
    CATEGORY = "Outros"
    VARIANT = "Padrão"

    @staticmethod
    def detect(text: str) -> float:
        return 0.0

    @staticmethod
    def extract(text: str) -> dict:
        return {}

    @classmethod
    def to_dataframe(cls, data: dict) -> pd.DataFrame:
        if not data:
            return pd.DataFrame()
        flat = {}
        for k, v in data.items():
            if isinstance(v, list):
                flat[k] = '; '.join(str(i) for i in v)
            else:
                flat[k] = v
        return pd.DataFrame([flat])


# ═══════════════════════════════════════════════════════════════════════════
# Contracheque — Variante Padrão (espaço delimitado, MM/YYYY)
# ═══════════════════════════════════════════════════════════════════════════

DESCRICOES_DESCONTO = [
    'INSS', 'IRRF', 'IMPOSTO', 'DESCONTO', 'ADTO', 'ADIANTAMENTO',
    'VALE', 'CESTA', 'PLANO', 'CONTRIBUI', 'SINDICATO', 'TRANSPORTE',
    'ASSOCIA', 'REFEIÇÃO', 'ASEHUP', 'ARREDONDAMENTO'
]


def _eh_desconto(descricao):
    d = descricao.upper()
    return any(p in d for p in DESCRICOES_DESCONTO)


class ContrachequeDefaultModel(BaseDocumentModel):
    NAME = "Contracheque — Padrão"
    ICON = "fa5s.money-check-alt"
    DESCRIPTION = "Holerite com colunas separadas por espaço, data em MM/YYYY"
    CATEGORY = "Contracheque"
    VARIANT = "Padrão (espaço)"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('demonstrativo de pagamento', .35), ('contracheque', .35),
               ('holerite', .30), ('salário base', .15), ('total de vencimentos', .15),
               ('fgts', .08), ('inss', .08), ('vencimentos', .08), ('descontos', .08)]
        for kw, s in kws:
            if kw in t:
                score += s
        # Padrão de MM/YYYY
        if re.search(r'\b\d{2}/\d{4}\b', text):
            score += 0.05
        # Se tem pipe => provavelmente é formato Belshop, penaliza
        if '|' in text and text.count('|') > 5:
            score -= 0.20
        return min(max(score, 0), 1.0)

    @staticmethod
    def _parse_linha(linha):
        linha = re.sub(r'\s+', ' ', linha.strip())
        partes = linha.split()
        if len(partes) < 3:
            return None
        if not re.match(r'^\d{3,4}$', partes[0]):
            return None
        codigo = partes[0]
        valores, indices = [], []
        for i, p in enumerate(partes):
            if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', p):
                valores.append(p)
                indices.append(i)
        if not valores or not indices:
            return None
        descricao = ' '.join(partes[1:indices[0]])
        venc = desc = ref = None
        if len(valores) == 1:
            desc = valores[0] if _eh_desconto(descricao) else None
            venc = None if _eh_desconto(descricao) else valores[0]
        elif len(valores) >= 2:
            ref = valores[0]
            desc = valores[1] if _eh_desconto(descricao) else None
            venc = None if _eh_desconto(descricao) else valores[1]
        return {'codigo': codigo, 'descricao': descricao, 'referencia': ref,
                'vencimento': venc, 'desconto': desc}

    @staticmethod
    def extract(text: str) -> dict:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        data = {'tipo_documento': 'Contracheque'}
        for line in lines:
            m = re.search(r'(\d{2})/(\d{4})', line)
            if m:
                data['mes_ano'] = f"{m.group(1)}/{m.group(2)}"
                break
        verbas, in_table = [], False
        for line in lines:
            if 'CÓD' in line.upper() and 'DESCRIÇÃO' in line.upper():
                in_table = True
                continue
            if any(k in line for k in ['TOTAL DE VENCIMENTOS', 'TOTAIS', 'BASE CÁLC']):
                vals = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', line)
                if 'TOTAL DE VENCIMENTOS' in line and vals:
                    data['total_vencimentos'] = vals[0] if vals else None
                    data['total_descontos'] = vals[1] if len(vals) >= 2 else None
                in_table = False
                continue
            if in_table:
                parsed = ContrachequeDefaultModel._parse_linha(line)
                if parsed:
                    verbas.append(parsed)
        data['verbas'] = verbas
        cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text)
        if cnpj:
            data['cnpj'] = cnpj.group()
        return data

    @classmethod
    def to_dataframe(cls, data):
        v = data.get('verbas', [])
        return pd.DataFrame(v) if v else super().to_dataframe(data)


# ═══════════════════════════════════════════════════════════════════════════
# Contracheque — Variante Belshop (pipe '|' delimitado)
# ═══════════════════════════════════════════════════════════════════════════

class ContrachequeBelshopModel(BaseDocumentModel):
    NAME = "Contracheque — Belshop"
    ICON = "fa5s.money-check-alt"
    DESCRIPTION = "Holerite com colunas separadas por '|', possível texto invertido"
    CATEGORY = "Contracheque"
    VARIANT = "Belshop (pipe)"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        if '|' in text and text.count('|') > 5:
            score += 0.30
        kws = [('contracheque', .20), ('holerite', .20), ('total de vencimentos', .15),
               ('base/outros', .20), ('mensalista', .15)]
        for kw, s in kws:
            if kw in t:
                score += s
        # Se NÃO tem pipe, penaliza muito
        if text.count('|') < 3:
            score -= 0.40
        return min(max(score, 0), 1.0)

    @staticmethod
    def _limpar_invertido(texto):
        inv = ['obicer', 'etsen', 'adanimircsid', 'adiuqíl',
               'aicnâtropmi', 'odibecer', 'oralceD', 'oiránoicnuF', 'arutanissA']
        palavras = texto.split()
        return ' '.join(p for p in palavras if not any(i in p.lower() for i in inv))

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Contracheque (Belshop)'}
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        # Mês/Ano — "Mensalista Março de 2023" ou "JAN/2025"
        for line in lines:
            m = re.search(r'Mensalista\s+(\w+)\s+de\s+(\d{4})', line)
            if m:
                data['mes_ano'] = f"{m.group(1)}/{m.group(2)}"
                break
            m2 = re.search(r'(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(\d{4})', line)
            if m2:
                meses = {'JAN':'01','FEV':'02','MAR':'03','ABR':'04','MAI':'05','JUN':'06',
                         'JUL':'07','AGO':'08','SET':'09','OUT':'10','NOV':'11','DEZ':'12'}
                data['mes_ano'] = f"{meses.get(m2.group(1), m2.group(1))}/{m2.group(2)}"
                break

        verbas, in_table = [], False
        for line in lines:
            if 'Código' in line and 'Descrição' in line and 'Vencimentos' in line:
                in_table = True
                continue
            if 'Total de Vencimentos' in line or 'BASE/OUTROS' in line:
                in_table = False
                continue
            if in_table and '|' in line:
                line = ContrachequeBelshopModel._limpar_invertido(line)
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 2:
                    continue
                m = re.match(r'^(\d+)\s+(.+)$', parts[0])
                if m:
                    codigo, desc = m.group(1), m.group(2).strip()
                    ref = parts[1] if len(parts) > 1 else ''
                    venc = parts[2] if len(parts) > 2 else ''
                    dsc = parts[3] if len(parts) > 3 else ''
                    verbas.append({'codigo': codigo, 'descricao': desc,
                                   'referencia': ref, 'vencimento': venc, 'desconto': dsc})
        data['verbas'] = verbas
        return data

    @classmethod
    def to_dataframe(cls, data):
        v = data.get('verbas', [])
        return pd.DataFrame(v) if v else super().to_dataframe(data)


# ═══════════════════════════════════════════════════════════════════════════
# Contracheque — Variante JAN/YYYY (mês textual)
# ═══════════════════════════════════════════════════════════════════════════

class ContrachequeJanModel(BaseDocumentModel):
    NAME = "Contracheque — JAN/YYYY"
    ICON = "fa5s.money-check-alt"
    DESCRIPTION = "Holerite com data em formato JAN/2025, colunas por espaço"
    CATEGORY = "Contracheque"
    VARIANT = "JAN/YYYY (textual)"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('contracheque', .20), ('holerite', .20), ('salário base', .10),
               ('total de vencimentos', .10)]
        for kw, s in kws:
            if kw in t:
                score += s
        # Esse modelo usa JAN/2025
        if re.search(r'\b(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/\d{4}\b', text):
            score += 0.35
        if text.count('|') > 5:
            score -= 0.20
        return min(max(score, 0), 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Contracheque (JAN/YYYY)'}
        meses = {'JAN':'01','FEV':'02','MAR':'03','ABR':'04','MAI':'05','JUN':'06',
                 'JUL':'07','AGO':'08','SET':'09','OUT':'10','NOV':'11','DEZ':'12'}
        m = re.search(r'(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)/(\d{4})', text)
        if m:
            data['mes_ano'] = f"{meses.get(m.group(1), '??')}/{m.group(2)}"

        verbas = []
        for line in text.split('\n'):
            line = line.strip()
            if not line or not re.match(r'^\d{3,4}\s', line):
                continue
            vals = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', line)
            if not vals:
                continue
            parts = line.split()
            codigo = parts[0]
            first_val_idx = next((i for i, p in enumerate(parts) if re.match(r'\d{1,3}(?:\.\d{3})*,\d{2}$', p)), len(parts))
            descricao = ' '.join(parts[1:first_val_idx])
            venc = desc = ref = None
            if len(vals) >= 2:
                ref, venc = vals[0], vals[1]
                if _eh_desconto(descricao):
                    venc, desc = None, vals[1]
            elif len(vals) == 1:
                if _eh_desconto(descricao):
                    desc = vals[0]
                else:
                    venc = vals[0]
            verbas.append({'codigo': codigo, 'descricao': descricao,
                           'referencia': ref, 'vencimento': venc, 'desconto': desc})
        data['verbas'] = verbas
        return data

    @classmethod
    def to_dataframe(cls, data):
        v = data.get('verbas', [])
        return pd.DataFrame(v) if v else super().to_dataframe(data)


# ═══════════════════════════════════════════════════════════════════════════
# Cartão Ponto — Variante Horizontal (DD/MM/YYYY + dia semana completo)
# ═══════════════════════════════════════════════════════════════════════════

class CartaoPontoHorizontalModel(BaseDocumentModel):
    NAME = "Cartão Ponto — Horizontal"
    ICON = "fa5s.clock"
    DESCRIPTION = "Espelho de ponto com DD/MM/YYYY + dia da semana, 4+ marcações"
    CATEGORY = "Cartão Ponto"
    VARIANT = "Horizontal (completo)"

    DATA_RE = re.compile(r'(\d{2}/\d{2}/\d{4})\s+(Seg|Ter|Qua|Qui|Sex|Sáb|Dom)', re.IGNORECASE)
    HORA_RE = re.compile(r'\b(\d{2}:\d{2})\b')
    FOLGAS = ['folga', 'casa', 'ausente', 'falta', '(-)', 'feriado', 'n.admitido']

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('cartão ponto', .30), ('cartao ponto', .30), ('espelho de ponto', .30),
               ('horário de trabalho', .15), ('banco de horas', .10), ('empregado:', .08),
               ('período:', .08), ('função:', .08)]
        for kw, s in kws:
            if kw in t:
                score += s
        dates = re.findall(r'\d{2}/\d{2}/\d{4}\s+(?:Seg|Ter|Qua|Qui|Sex|Sáb|Dom)', text, re.IGNORECASE)
        if len(dates) > 5:
            score += 0.30
        # Check for DD/MM without year (CurtaModel territory)
        short_dates = re.findall(r'^\d{2}/\d{2}\s+(?:seg|ter|qua|qui|sex|sáb|dom)', text, re.IGNORECASE | re.MULTILINE)
        if len(short_dates) > len(dates):
            score -= 0.15
        return min(max(score, 0), 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Cartão Ponto (Horizontal)', 'registros': []}
        lines = text.split('\n')
        for line in lines:
            m = re.search(r'Empregado:\s*\d+-(.+?)(?:\s+Carteira|\s+Admissão|\s*$)', line)
            if m:
                data['funcionario'] = m.group(1).strip()
            m2 = re.search(r'Período:\s*(\d{2}/\d{2}/\d{4})\s*até\s*(\d{2}/\d{2}/\d{4})', line)
            if m2:
                data['periodo_inicio'], data['periodo_fim'] = m2.group(1), m2.group(2)

        for line in lines:
            dm = CartaoPontoHorizontalModel.DATA_RE.search(line)
            if not dm:
                continue
            reg = {'data': dm.group(1), 'dia_semana': dm.group(2)}
            if any(w in line.lower() for w in CartaoPontoHorizontalModel.FOLGAS):
                reg.update({'status': 'Folga', 'entrada1': '', 'saida1': '', 'entrada2': '', 'saida2': ''})
            else:
                horas = CartaoPontoHorizontalModel.HORA_RE.findall(line)
                marcacoes = horas[4:8] if len(horas) > 4 else horas[:4]
                reg['status'] = 'Normal'
                reg['entrada1'] = marcacoes[0] if len(marcacoes) >= 1 else ''
                reg['saida1'] = marcacoes[1] if len(marcacoes) >= 2 else ''
                reg['entrada2'] = marcacoes[2] if len(marcacoes) >= 3 else ''
                reg['saida2'] = marcacoes[3] if len(marcacoes) >= 4 else ''
            data['registros'].append(reg)
        return data

    @classmethod
    def to_dataframe(cls, data):
        r = data.get('registros', [])
        return pd.DataFrame(r) if r else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════
# Cartão Ponto — Variante Curta (DD/MM sem ano, período no cabeçalho)
# ═══════════════════════════════════════════════════════════════════════════

class CartaoPontoCurtaModel(BaseDocumentModel):
    NAME = "Cartão Ponto — Curta"
    ICON = "fa5s.clock"
    DESCRIPTION = "Espelho de ponto com DD/MM (ano no cabeçalho), período à"
    CATEGORY = "Cartão Ponto"
    VARIANT = "Curta (DD/MM)"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('cartão ponto', .25), ('cartao ponto', .25), ('espelho de ponto', .25)]
        for kw, s in kws:
            if kw in t:
                score += s
        short = re.findall(r'^\d{2}/\d{2}\s+(?:seg|ter|qua|qui|sex|sáb|dom)', text, re.IGNORECASE | re.MULTILINE)
        if len(short) > 5:
            score += 0.35
        if re.search(r'\d{2}/\d{2}/\d{4}\s+[àa]\s+\d{2}/\d{2}/\d{4}', text):
            score += 0.15
        full = re.findall(r'\d{2}/\d{2}/\d{4}\s+(?:Seg|Ter|Qua|Qui|Sex|Sáb|Dom)', text, re.IGNORECASE)
        if len(full) > len(short):
            score -= 0.20
        return min(max(score, 0), 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Cartão Ponto (Curta)', 'registros': []}
        # Extract year from period
        m_per = re.search(r'(\d{2}/\d{2})/(\d{4})\s+[àa]\s+(\d{2}/\d{2})/(\d{4})', text)
        ano = m_per.group(4) if m_per else ''
        if m_per:
            data['periodo_inicio'] = f"{m_per.group(1)}/{m_per.group(2)}"
            data['periodo_fim'] = f"{m_per.group(3)}/{m_per.group(4)}"

        for line in text.split('\n'):
            line = line.strip()
            m = re.match(r'^(\d{2}/\d{2})\s+([a-záéíóúâê]+)', line, re.IGNORECASE)
            if not m:
                continue
            dt = f"{m.group(1)}/{ano}" if ano else m.group(1)
            dia = m.group(2)
            reg = {'data': dt, 'dia_semana': dia}
            if any(w in line.lower() for w in ['folga', 'feriado', '(f)', 'n.admitido']):
                reg.update({'status': 'Folga', 'entrada1': '', 'saida1': '', 'entrada2': '', 'saida2': ''})
            else:
                horas = re.findall(r'\b(\d{2}:\d{2})\b', line)
                # Skip first 4 scheduled hours
                marc = horas[4:8] if len(horas) > 4 else horas[:4]
                # Filter increasing only
                filtered = []
                last = -1
                for h in marc:
                    mins = int(h[:2]) * 60 + int(h[3:])
                    if mins > last:
                        filtered.append(h)
                        last = mins
                reg['status'] = 'Normal'
                reg['entrada1'] = filtered[0] if len(filtered) >= 1 else ''
                reg['saida1'] = filtered[1] if len(filtered) >= 2 else ''
                reg['entrada2'] = filtered[2] if len(filtered) >= 3 else ''
                reg['saida2'] = filtered[3] if len(filtered) >= 4 else ''
            data['registros'].append(reg)
        return data

    @classmethod
    def to_dataframe(cls, data):
        r = data.get('registros', [])
        return pd.DataFrame(r) if r else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════
# Cartão Ponto — PontoMais (Dia,DD/MM/YYYY sequencial)
# ═══════════════════════════════════════════════════════════════════════════

class CartaoPontoPontoMaisModel(BaseDocumentModel):
    NAME = "Cartão Ponto — PontoMais"
    ICON = "fa5s.clock"
    DESCRIPTION = "PontoMais: Dia,DD/MM/YYYY com horários sequenciais"
    CATEGORY = "Cartão Ponto"
    VARIANT = "PontoMais"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        if 'pontomais' in t or 'ponto mais' in t:
            score += 0.40
        matches = re.findall(r'(?:Seg|Ter|Qua|Qui|Sex|Sáb|Dom),?\s*\d{2}/\d{2}/\d{4}', text, re.IGNORECASE)
        if len(matches) > 5:
            score += 0.35
        if 'cartão' in t or 'ponto' in t:
            score += 0.10
        return min(max(score, 0), 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Cartão Ponto (PontoMais)', 'registros': []}
        for line in text.split('\n'):
            m = re.search(r'(?:Seg|Ter|Qua|Qui|Sex|Sáb|Dom),?\s*(\d{2}/\d{2}/\d{4})', line, re.IGNORECASE)
            if not m:
                continue
            dt = m.group(1)
            tokens = line.split()
            horarios = []
            last = -1
            for tok in tokens:
                if re.match(r'^\d{2}:\d{2}$', tok):
                    mins = int(tok[:2]) * 60 + int(tok[3:])
                    if mins > last:
                        horarios.append(tok)
                        last = mins
                    if len(horarios) == 4:
                        break
            data['registros'].append({
                'data': dt,
                'entrada1': horarios[0] if len(horarios) >= 1 else '',
                'saida1': horarios[1] if len(horarios) >= 2 else '',
                'entrada2': horarios[2] if len(horarios) >= 3 else '',
                'saida2': horarios[3] if len(horarios) >= 4 else '',
            })
        return data

    @classmethod
    def to_dataframe(cls, data):
        r = data.get('registros', [])
        return pd.DataFrame(r) if r else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════
# Nota Fiscal (NF-e / DANFE)
# ═══════════════════════════════════════════════════════════════════════════

class NotaFiscalModel(BaseDocumentModel):
    NAME = "Nota Fiscal (NF-e)"
    ICON = "fa5s.file-invoice-dollar"
    DESCRIPTION = "Nota Fiscal Eletrônica / DANFE"
    CATEGORY = "Nota Fiscal"
    VARIANT = "NF-e / DANFE"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('nota fiscal', .30), ('danfe', .35), ('nf-e', .30), ('chave de acesso', .20),
               ('icms', .10), ('destinatário', .10), ('emitente', .10), ('cfop', .10),
               ('natureza da operação', .10)]
        for kw, s in kws:
            if kw in t:
                score += s
        return min(score, 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Nota Fiscal'}
        m = re.search(r'(?:N[°ºo.]?\s*|Número[:\s]*)(\d{3,9})', text, re.IGNORECASE)
        if m:
            data['numero_nf'] = m.group(1)
        chave = re.search(r'(\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4})', text)
        if chave:
            data['chave_acesso'] = chave.group(1).replace(' ', '')
        cnpjs = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text)
        if cnpjs:
            data['cnpj_emitente'] = cnpjs[0]
            if len(cnpjs) > 1:
                data['cnpj_destinatario'] = cnpjs[1]
        vals = re.findall(r'(?:valor\s+total|total\s+da\s+nota)[:\s]*R?\$?\s*([\d.,]+)', text, re.IGNORECASE)
        if vals:
            data['valor_total'] = vals[0]
        datas = re.findall(r'(?:emissão|emissao)[:\s]*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if datas:
            data['data_emissao'] = datas[0]
        return data


# ═══════════════════════════════════════════════════════════════════════════
# NFS-e (Nota Fiscal de Serviço)
# ═══════════════════════════════════════════════════════════════════════════

class NFSeModel(BaseDocumentModel):
    NAME = "Nota de Serviço (NFS-e)"
    ICON = "fa5s.file-invoice"
    DESCRIPTION = "Nota Fiscal de Serviço Eletrônica"
    CATEGORY = "Nota Fiscal"
    VARIANT = "NFS-e"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('nfs-e', .35), ('nota fiscal de serviço', .35), ('prestador', .15),
               ('tomador', .15), ('iss', .10), ('issqn', .15)]
        for kw, s in kws:
            if kw in t:
                score += s
        return min(score, 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'NFS-e'}
        m = re.search(r'(?:N[°ºo.]?\s*|NFS-e\s*N[°ºo.]?\s*)(\d+)', text, re.IGNORECASE)
        if m:
            data['numero'] = m.group(1)
        m = re.search(r'[Pp]restador[:\s]*(.+?)(?:\n|CNPJ)', text)
        if m:
            data['prestador'] = m.group(1).strip()
        m = re.search(r'[Tt]omador[:\s]*(.+?)(?:\n|CNPJ|CPF)', text)
        if m:
            data['tomador'] = m.group(1).strip()
        vals = re.findall(r'R\$\s*([\d.,]+)', text)
        if vals:
            data['valor_servico'] = vals[0]
        cnpjs = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text)
        if cnpjs:
            data['cnpj_prestador'] = cnpjs[0]
        return data


# ═══════════════════════════════════════════════════════════════════════════
# Boleto Bancário
# ═══════════════════════════════════════════════════════════════════════════

class BoletoModel(BaseDocumentModel):
    NAME = "Boleto Bancário"
    ICON = "fa5s.barcode"
    DESCRIPTION = "Boleto de cobrança bancário"
    CATEGORY = "Boleto"
    VARIANT = "Padrão"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('boleto', .30), ('linha digitável', .25), ('beneficiário', .15),
               ('sacado', .15), ('nosso número', .15), ('cedente', .15)]
        for kw, s in kws:
            if kw in t:
                score += s
        if re.search(r'\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+\d{14}', text):
            score += 0.30
        return min(score, 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Boleto Bancário'}
        m = re.search(r'(\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+\d{14})', text)
        if m:
            data['linha_digitavel'] = m.group(1)
        m = re.search(r'[Vv]encimento[:\s]*(\d{2}/\d{2}/\d{4})', text)
        if m:
            data['vencimento'] = m.group(1)
        m = re.search(r'[Vv]alor\s*(?:do\s+)?(?:documento|boleto)?[:\s]*R?\$?\s*([\d.,]+)', text, re.IGNORECASE)
        if m:
            data['valor'] = m.group(1)
        return data


# ═══════════════════════════════════════════════════════════════════════════
# Recibo de Pagamento
# ═══════════════════════════════════════════════════════════════════════════

class ReciboModel(BaseDocumentModel):
    NAME = "Recibo de Pagamento"
    ICON = "fa5s.receipt"
    DESCRIPTION = "Recibo de Pagamento / Confirmação"
    CATEGORY = "Recibo"
    VARIANT = "Padrão"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('recibo', .35), ('recebi de', .25), ('importância de', .20),
               ('quitação', .15), ('para devida comprovação', .20)]
        for kw, s in kws:
            if kw in t:
                score += s
        return min(score, 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Recibo de Pagamento'}
        vals = re.findall(r'R\$\s*([\d.,]+)', text)
        if vals:
            data['valor'] = vals[0]
        datas = re.findall(r'(\d{2}/\d{2}/\d{4})', text)
        if datas:
            data['data'] = datas[0]
        cpfs = re.findall(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text)
        if cpfs:
            data['cpf'] = cpfs[0]
        return data


# ═══════════════════════════════════════════════════════════════════════════
# Extrato Bancário
# ═══════════════════════════════════════════════════════════════════════════

class ExtratoBancarioModel(BaseDocumentModel):
    NAME = "Extrato Bancário"
    ICON = "fa5s.university"
    DESCRIPTION = "Extrato de conta bancária"
    CATEGORY = "Extrato"
    VARIANT = "Padrão"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('extrato', .25), ('saldo anterior', .25), ('saldo final', .20),
               ('conta corrente', .15), ('lançamentos', .10), ('movimentação', .10)]
        for kw, s in kws:
            if kw in t:
                score += s
        return min(score, 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Extrato Bancário', 'lancamentos': []}
        for line in text.split('\n'):
            m = re.match(r'(\d{2}/\d{2}(?:/\d{2,4})?)\s+(.+?)\s+([\d.,]+[DC]?)\s*$', line.strip())
            if m:
                data['lancamentos'].append({'data': m.group(1), 'descricao': m.group(2).strip(), 'valor': m.group(3)})
        return data

    @classmethod
    def to_dataframe(cls, data):
        l = data.get('lancamentos', [])
        return pd.DataFrame(l) if l else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════════════════
# Contrato
# ═══════════════════════════════════════════════════════════════════════════

class ContratoModel(BaseDocumentModel):
    NAME = "Contrato"
    ICON = "fa5s.file-signature"
    DESCRIPTION = "Contrato / Acordo / Termo"
    CATEGORY = "Contrato"
    VARIANT = "Padrão"

    @staticmethod
    def detect(text: str) -> float:
        t = text.lower()
        score = 0.0
        kws = [('contrato', .25), ('contratante', .20), ('contratado', .20),
               ('cláusula', .20), ('vigência', .10), ('testemunhas', .10)]
        for kw, s in kws:
            if kw in t:
                score += s
        return min(score, 1.0)

    @staticmethod
    def extract(text: str) -> dict:
        data = {'tipo_documento': 'Contrato'}
        m = re.search(r'[Cc]ontratante[:\s]*(.+?)(?:\n|,\s*(?:inscrit|CNPJ|CPF))', text)
        if m:
            data['contratante'] = m.group(1).strip()
        m = re.search(r'[Cc]ontratad[oa][:\s]*(.+?)(?:\n|,\s*(?:inscrit|CNPJ|CPF))', text)
        if m:
            data['contratado'] = m.group(1).strip()
        vals = re.findall(r'R\$\s*([\d.,]+)', text)
        if vals:
            data['valor'] = vals[0]
        return data


# ═══════════════════════════════════════════════════════════════════════════
# Model Manager
# ═══════════════════════════════════════════════════════════════════════════

ALL_MODELS = [
    ContrachequeDefaultModel,
    ContrachequeBelshopModel,
    ContrachequeJanModel,
    CartaoPontoHorizontalModel,
    CartaoPontoCurtaModel,
    CartaoPontoPontoMaisModel,
    NotaFiscalModel,
    NFSeModel,
    BoletoModel,
    ReciboModel,
    ExtratoBancarioModel,
    ContratoModel,
]

# Organize by category for library UI
CATEGORIES = {}
for _m in ALL_MODELS:
    cat = _m.CATEGORY
    if cat not in CATEGORIES:
        CATEGORIES[cat] = []
    CATEGORIES[cat].append(_m)


class ModelManager:
    @staticmethod
    def get_all_models():
        return ALL_MODELS

    @staticmethod
    def get_model_names():
        return [m.NAME for m in ALL_MODELS]

    @staticmethod
    def get_categories():
        return CATEGORIES

    @staticmethod
    def auto_detect(text: str):
        best_model, best_score = None, 0.0
        for model in ALL_MODELS:
            score = model.detect(text)
            if score > best_score:
                best_score = score
                best_model = model
        return best_model, best_score

    @staticmethod
    def get_model_by_name(name: str):
        for m in ALL_MODELS:
            if m.NAME == name:
                return m
        return None

    @staticmethod
    def process(text: str, model_name: str = None):
        if model_name and model_name != "Auto-Detectar":
            model = ModelManager.get_model_by_name(model_name)
        else:
            model, _ = ModelManager.auto_detect(text)
        if model is None:
            return None, {}, pd.DataFrame()
        data = model.extract(text)
        df = model.to_dataframe(data)
        return model, data, df
