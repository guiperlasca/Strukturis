# Strukturis Pro 🚀
**Inteligência Híbrida para Extração e Gestão de Documentos**

> *Desenvolvido por [Guilherme Perlasca]*

[![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge&logo=qt)](https://doc.qt.io/qtforpython/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-8E75B2?style=for-the-badge&logo=google)](https://deepmind.google/technologies/gemini/)

## 📄 Sobre o Projeto

**Strukturis Pro** é uma solução desktop moderna e robusta para digitação, OCR e extração inteligente de dados. Projetado para otimizar fluxos de trabalho administrativos, ele combina a velocidade do processamento local com a inteligência da nuvem.

O sistema permite transformar PDFs e imagens (Notas Fiscais, Boletos, Contratos) em dados estruturados (Excel, JSON) e arquivos pesquisáveis, com uma interface "Workbench" profissional.

---

## ✨ Funcionalidades Principais

### 🧠 Inteligência Híbrida (Hybrid AI)
O Strukturis opera com dois motores de inteligência que trabalham em conjunto:
1.  **⚡ IA Local (Offline)**:
    - Utiliza **Tesseract OCR (LSTM)** e algoritmos heurísticos (`SmartParser`).
    - Funciona 100% sem internet.
    - Identifica CPFs, CNPJs, Datas e Tabelas automaticamente.
2.  **☁ IA Nuvem (Gemini Integration)**:
    - Conecta-se à API do **Google Gemini** para análises profundas.
    - **Chat com Documento**: Converse com seus arquivos ("Resuma este contrato", "Qual o valor total?").
    - Estruturação semântica de dados complexos.
    - *Fallback Automático*: Sem internet? O sistema volta instantaneamente para o modo local.

### 🖥️ Interface Moderna (Workbench)
- **Dark Mode Profissional**: Design ergonômico com ícones vetoriais (`qtawesome`).
- **Navegação PDF**: Visualize e navegue por documentos de múltiplas páginas sem travamentos.
- **Ferramentas de Imagem**:
    - **Recorte Inteligente (Smart Crop)**: Foque apenas no que importa.
    - **Rotação Fina**: Ajuste documentos digitalizados tortos com precisão de graus.
    - **Filtros**: Melhore a legibilidade com alto contraste.

### 🛠️ Produtividade
- **Seleção de ROI (Region of Interest)**: Extraia dados de apenas uma parte da página sem perder o documento original.
- **Exportação Universal**:
    - Excel (`.xlsx`) com tabelas formatadas.
    - PDF Pesquisável (Camada de texto sobre imagem).
- **Processamento em Lote**: Arraste múltiplos arquivos para a fila.

---

## 🚀 Instalação e Uso

### Pré-requisitos
- Python 3.10 ou superior.
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado no sistema.

### Instalação
```bash
# Clone o repositório
git clone https://github.com/guiperlasca/Strukturis.git
cd Strukturis


# Crie um ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

### Executando
```bash
python main.py
```

## 📦 Download / Executável (.exe)
Para quem prefere não instalar Python, o projeto conta com um script de build.
1.  O executável gerado (`StrukturisPro.exe`) fica na pasta `dist/`.
2.  **Download Direto**: [Acesse a aba Releases](https://github.com/guiperlasca/Strukturis/releases).

**Para gerar você mesmo:**
```bash
pip install pyinstaller
python -m PyInstaller --name "StrukturisPro" --windowed --onefile main.py
```

---

## 🤖 Como Configurar a IA (Opcional)
Para ativar os recursos de Chat de Nuvem:
1.  Abra o Strukturis Pro.
2.  Clique no botão **"Configurar IA Nuvem"** no topo da tela.
3.  Insira sua API Key gratuita do [Google AI Studio](https://aistudio.google.com/).
4.  Pronto! O ícone mudará para "☁ Nuvem Disponível".

---

## 🛠️ Tecnologias Utilizadas
- **Core**: Python 3.12
- **GUI**: PySide6 (Qt for Python)
- **Computer Vision**: OpenCV, PyMuPDF
- **OCR Engine**: Tesseract 5
- **Data Science**: Pandas
- **Generative AI**: Google Generative AI SDK

---

## 👤 Autor

**Guilherme Perlasca**  

---

*© 2026 Strukturis Pro. Todos os direitos reservados.*
