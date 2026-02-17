"""
Strukturis Pro — Smart Parser com padrões expandidos
Extração local de entidades via regex e heurísticas.
"""

import re
import pandas as pd
from core.document_models import ModelManager


class SmartParser:
    """
    'IA' local usando regex e heurísticas para estruturar dados.
    """

    PATTERNS = {
        'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
        'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
        'data': r'\d{1,2}/\d{1,2}/\d{2,4}',
        'valor_monetario': r'R\$\s?[\d\.,]+',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'telefone': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
        # Novos padrões
        'cep': r'\d{5}-\d{3}',
        'rg': r'\d{1,2}\.\d{3}\.\d{3}-[\dXx]',
        'pis_pasep': r'\d{3}\.\d{5}\.\d{2}-\d',
        'linha_digitavel': r'\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+\d{14}',
        'chave_nfe': r'\d{44}',
        'horario': r'\b\d{2}:\d{2}\b',
        'percentual': r'\d+[,.]?\d*\s?%',
        'placa_veiculo': r'[A-Z]{3}-?\d[A-Z0-9]\d{2}',
        'inscricao_estadual': r'(?:IE|Insc\.?\s*Est\.?)[:\s]*[\d./\-]+',
    }

    @staticmethod
    def extract_entities(text):
        """Retorna dicionário de entidades detectadas."""
        results = {}
        for key, pattern in SmartParser.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                results[key] = list(set(matches))

        # Classificação heurística de tipo de documento via ModelManager
        model, score = ModelManager.auto_detect(text)
        if model and score > 0.3:
            results['TIPO_DOC'] = [f"{model.NAME} (confiança: {score:.0%})"]
        else:
            # Fallback com heurísticas simples
            lower_text = text.lower()
            if 'nota fiscal' in lower_text or 'danfe' in lower_text:
                results['TIPO_DOC'] = ['Nota Fiscal / DANFE']
            elif 'recibo' in lower_text:
                results['TIPO_DOC'] = ['Recibo de Pagamento']
            elif 'contrato' in lower_text:
                results['TIPO_DOC'] = ['Contrato / Acordo']
            elif 'boleto' in lower_text or 'banco' in lower_text:
                results['TIPO_DOC'] = ['Boleto Bancário']
            elif 'contracheque' in lower_text or 'holerite' in lower_text:
                results['TIPO_DOC'] = ['Contracheque / Holerite']
            elif 'extrato' in lower_text:
                results['TIPO_DOC'] = ['Extrato Bancário']
            else:
                results['TIPO_DOC'] = ['Documento Genérico']

        return results

    @staticmethod
    def preview_structure(text):
        """
        Analisa estrutura de linhas para sugerir DataFrame.
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return pd.DataFrame()

        # Heurística: Linhas com contagem de tokens similar (potencial tabela)
        token_counts = [len(re.split(r'\s{2,}|\t', l)) for l in lines]
        if not token_counts:
            return pd.DataFrame()

        most_common_count = max(set(token_counts), key=token_counts.count)

        if most_common_count > 1:
            data = []
            for line in lines:
                parts = re.split(r'\s{2,}|\t', line)
                if len(parts) < most_common_count:
                    parts += [''] * (most_common_count - len(parts))
                data.append(parts[:most_common_count])

            df = pd.DataFrame(data)

            # Tenta promover cabeçalho
            first_row = df.iloc[0]
            is_header = all(
                not re.match(r'^[\d.,]+$', str(v).strip())
                for v in first_row if str(v).strip()
            )
            if is_header and len(df) > 1:
                df.columns = [str(v).strip() for v in first_row]
                df = df.iloc[1:].reset_index(drop=True)

            return df
        else:
            # Key-Value
            kv_data = {}
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 1)
                    kv_data[parts[0].strip()] = parts[1].strip()

            if kv_data:
                return pd.DataFrame([kv_data])

            return pd.DataFrame(lines, columns=["Linhas do Texto"])
