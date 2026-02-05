import pytesseract
import shutil
import os
import sys

class OCRManager:
    _configured = False

    @staticmethod
    def configure():
        """Attempts to find Tesseract executable on Windows."""
        if OCRManager._configured:
            return True

        # Common Windows paths
        paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.getenv('LOCALAPPDATA', ''), r"Tesseract-OCR\tesseract.exe")
        ]

        tess_path = shutil.which("tesseract")
        
        if not tess_path:
            for p in paths:
                if os.path.exists(p):
                    tess_path = p
                    break
        
        if tess_path:
            pytesseract.pytesseract.tesseract_cmd = tess_path
            OCRManager._configured = True
            return True
        return False

    @staticmethod
    def get_available_languages():
        if not OCRManager.configure():
            return []
        return pytesseract.get_languages()

    @staticmethod
    def check_language(lang='por'):
        """Checks if the specific language model is installed."""
        if not OCRManager.configure():
            return False
        langs = OCRManager.get_available_languages()
        return lang in langs

    @staticmethod
    def extract_text(image, lang='por'):
        if not OCRManager.configure():
            return "Erro: Tesseract não encontrado. Instale o Tesseract-OCR."
        
        # Fallback check
        if not OCRManager.check_language(lang):
             return f"Erro: Pacote de idioma '{lang}' não encontrado. Reinstale o Tesseract e selecione o idioma."

        try:
            return pytesseract.image_to_string(image, lang=lang)
        except Exception as e:
            return f"Erro no OCR: {str(e)}"
    
    @staticmethod
    def extract_data(image, lang='por'):
        """Returns detailed data (boxes, conf)."""
        if not OCRManager.configure():
            return None
        return pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
