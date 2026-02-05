import re
import pandas as pd

class SmartParser:
    """
    Local 'AI' using regex patterns and heuristics to structure data.
    """
    
    PATTERNS = {
        'cpf': r'\d{3}\.\d{3}\.\d{3}-\d{2}',
        'cnpj': r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}',
        'data': r'\d{1,2}/\d{1,2}/\d{2,4}',
        'valor_monetario': r'R\$\s?[\d\.,]+',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'telefone': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}'
    }

    @staticmethod
    def extract_entities(text):
        """Returns a dictionary of detected entities."""
        results = {}
        for key, pattern in SmartParser.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                results[key] = list(set(matches)) # Unique values
        
        # Heuristic Classification
        lower_text = text.lower()
        if 'nota fiscal' in lower_text or 'danfe' in lower_text:
            results['TIPO_DOC'] = ['Nota Fiscal / DANFE']
        elif 'recibo' in lower_text:
            results['TIPO_DOC'] = ['Recibo de Pagamento']
        elif 'contrato' in lower_text:
            results['TIPO_DOC'] = ['Contrato / Acordo']
        elif 'boleto' in lower_text or 'banco' in lower_text:
            results['TIPO_DOC'] = ['Boleto Bancário']
        else:
            results['TIPO_DOC'] = ['Documento Genérico']
            
        return results

    @staticmethod
    def preview_structure(text):
        """
        Analyzes line structure to guess if it's a table/list.
        Returns a suggested DataFrame.
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return pd.DataFrame()

        # Heuristic: Check if lines have similar token counts (potential table)
        token_counts = [len(re.split(r'\s{2,}|\t', l)) for l in lines]
        if not token_counts: return pd.DataFrame() # Safety
        
        most_common_count = max(set(token_counts), key=token_counts.count)
        
        if most_common_count > 1:
            # Likely a table
            data = []
            for line in lines:
                parts = re.split(r'\s{2,}|\t', line)
                # Pad if missing columns
                if len(parts) < most_common_count:
                    parts += [''] * (most_common_count - len(parts))
                data.append(parts[:most_common_count])
            
            df = pd.DataFrame(data)
            # Try to promote header
            return df
        else:
            # Just Key-Value pairs?
            # Look for "Label: Value"
            kv_data = {}
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 1)
                    kv_data[parts[0].strip()] = parts[1].strip()
            
            if kv_data:
                return pd.DataFrame([kv_data]) # Single row DF
            
            # Implementation Fallback: List
            return pd.DataFrame(lines, columns=["Linhas do Texto"])
