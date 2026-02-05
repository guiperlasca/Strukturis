import pandas as pd
import re
from io import StringIO

class DataParser:
    @staticmethod
    def parse_to_dataframe(text):
        """
        Attempts to convert unstructured text into a DataFrame.
        Strategy: Look for lines with similar structure/delimiters.
        """
        lines = text.split('\n')
        data = []
        
        # Simple heuristic: Lines with multiple spaces or tabs might be columns
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Split by 2+ spaces or tabs
            parts = re.split(r'\s{2,}|\t', line)
            if len(parts) > 1:
                data.append(parts)
            else:
                # Fallback: maybe CSV-like lines?
                pass
        
        if not data:
            return pd.DataFrame([text], columns=["Conteúdo"])

        # Create Header
        df = pd.DataFrame(data)
        
        # Promote first row to header if it looks like one (all strings, non-numeric)
        # For now, just generic headers
        df.columns = [f"Coluna {i+1}" for i in range(df.shape[1])]
        
        return df

class Exporter:
    @staticmethod
    def to_excel(df, path):
        df.to_excel(path, index=False)

    @staticmethod
    def to_csv(df, path):
        df.to_csv(path, index=False, sep=';', encoding='utf-8-sig')

    @staticmethod
    def to_txt(text, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
