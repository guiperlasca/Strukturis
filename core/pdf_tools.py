"""
Strukturis Pro — Ferramentas de manipulação de PDF
Dividir, mesclar, extrair páginas usando PyMuPDF (fitz).
"""

import fitz  # PyMuPDF
import os


class PDFTools:
    """Utilitários para manipulação de arquivos PDF."""

    @staticmethod
    def get_page_count(path: str) -> int:
        """Retorna o número de páginas de um PDF."""
        try:
            doc = fitz.open(path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0

    @staticmethod
    def split_by_range(input_path: str, output_path: str, start: int, end: int) -> bool:
        """
        Extrai páginas de start até end (1-based, inclusive) para um novo PDF.
        Retorna True se ok.
        """
        try:
            doc = fitz.open(input_path)
            total = len(doc)
            start_idx = max(0, start - 1)
            end_idx = min(total, end)

            out = fitz.open()
            out.insert_pdf(doc, from_page=start_idx, to_page=end_idx - 1)
            out.save(output_path)
            out.close()
            doc.close()
            return True
        except Exception as e:
            print(f"Erro ao dividir PDF: {e}")
            return False

    @staticmethod
    def split_each_page(input_path: str, output_dir: str) -> list:
        """
        Divide um PDF em arquivos individuais (1 página cada).
        Retorna lista de caminhos dos arquivos gerados.
        """
        results = []
        try:
            doc = fitz.open(input_path)
            base = os.path.splitext(os.path.basename(input_path))[0]

            os.makedirs(output_dir, exist_ok=True)

            for i in range(len(doc)):
                out = fitz.open()
                out.insert_pdf(doc, from_page=i, to_page=i)
                out_path = os.path.join(output_dir, f"{base}_pagina_{i + 1}.pdf")
                out.save(out_path)
                out.close()
                results.append(out_path)

            doc.close()
        except Exception as e:
            print(f"Erro ao dividir páginas: {e}")
        return results

    @staticmethod
    def extract_pages(input_path: str, output_path: str, pages: list) -> bool:
        """
        Extrai páginas específicas (lista 1-based) para um novo PDF.
        pages: lista de ints, ex: [1, 3, 5]
        """
        try:
            doc = fitz.open(input_path)
            out = fitz.open()

            for p in sorted(pages):
                idx = p - 1
                if 0 <= idx < len(doc):
                    out.insert_pdf(doc, from_page=idx, to_page=idx)

            out.save(output_path)
            out.close()
            doc.close()
            return True
        except Exception as e:
            print(f"Erro ao extrair páginas: {e}")
            return False

    @staticmethod
    def merge_pdfs(input_paths: list, output_path: str) -> bool:
        """
        Mescla múltiplos PDFs em um único arquivo.
        """
        try:
            out = fitz.open()
            for path in input_paths:
                if os.path.exists(path):
                    doc = fitz.open(path)
                    out.insert_pdf(doc)
                    doc.close()

            out.save(output_path)
            out.close()
            return True
        except Exception as e:
            print(f"Erro ao mesclar PDFs: {e}")
            return False

    @staticmethod
    def rotate_pages(input_path: str, output_path: str, angle: int, pages: list = None) -> bool:
        """
        Rotaciona páginas de um PDF.
        angle: 90, 180 ou 270
        pages: lista 1-based, None = todas
        """
        try:
            doc = fitz.open(input_path)
            target_pages = [p - 1 for p in pages] if pages else range(len(doc))

            for idx in target_pages:
                if 0 <= idx < len(doc):
                    page = doc.load_page(idx)
                    page.set_rotation(page.rotation + angle)

            doc.save(output_path)
            doc.close()
            return True
        except Exception as e:
            print(f"Erro ao rotacionar: {e}")
            return False
