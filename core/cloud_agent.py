import google.generativeai as genai
import socket
import json
import os

class CloudAgent:
    """
    Handles connection to Google Gemini API (Free Tier).
    Acts as an enhancement layer over the local OCR.
    """
    
    API_KEY = None # User must provide this
    
    @staticmethod
    def is_connected():
        """Checks for active internet connection."""
        try:
            # Simple DNS check to Google
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    @staticmethod
    def configure(api_key):
        """Sets the API Key for the session."""
        CloudAgent.API_KEY = api_key
        if api_key:
            genai.configure(api_key=api_key)

    @staticmethod
    def enhance_data(text, user_instruction=None):
        """
        Sends OCR text to Gemini Flash.
        If user_instruction is provided, follows it.
        Otherwise, defaults to struct extraction.
        """
        if not CloudAgent.is_connected():
            return None
            
        if not CloudAgent.API_KEY:
            return {"error": "API Key não configurada"}

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            base_instruction = """
            Extraia as informações mais relevantes em formato JSON puro.
            Tente identificar: tipo_documento, data, valor_total, pessoas/empresas envolvidas.
            Retorne APENAS o JSON.
            """
            
            if user_instruction:
                # Chat Mode / Custom Instruction
                prompt = f"""
                Analise o texto abaixo extraído de um documento:
                
                --- INÍCIO TEXTO ---
                {text[:8000]}
                --- FIM TEXTO ---
                
                SEU OBJETIVO: {user_instruction}
                
                IMPORTANTE:
                - Se o usuário pediu tabela, retorne um ARRAY de objetos JSON.
                - Se pediu resumo, retorne texto.
                - Priorize o formato JSON se for estrutura de dados.
                """
            else:
                # Default Extraction Mode
                prompt = f"""
                Analise o seguinte texto OCR:
                {text[:4000]}
                
                INSTRUÇÃO:
                {base_instruction}
                """
            
            response = model.generate_content(prompt)
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            
            # Try to parse JSON, if fails, return text (for chat answers)
            try:
                data = json.loads(clean_text)
                return data
            except:
                return {"text_response": response.text} # Fallback for conversational answers
            
        except Exception as e:
            print(f"Cloud AI Error: {e}")
            return {"error": str(e)}
