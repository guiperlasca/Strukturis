from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QListWidget, QPushButton, QLabel, QFrame, QSplitter,
                               QTabWidget, QToolBox, QScrollArea, QSlider, QSpinBox, QGroupBox, QLineEdit, QApplication, QMessageBox, QFileDialog, QInputDialog, QComboBox, QProgressBar, QDialog, QDialogButtonBox, QCheckBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction
import qtawesome as qta
import json
import pandas as pd
import os
from core.image_processing import ImageProcessing
from core.ocr_manager import OCRManager
from core.file_handler import FileHandler
from core.smart_parser import SmartParser
from core.data_parser import Exporter, DataParser
from core.document_models import ModelManager, ALL_MODELS
from core.pdf_tools import PDFTools
from ui.model_library import ModelLibraryDialog


# ═══════════════════════════════════════════════════════════════════════════
# Dialogs
# ═══════════════════════════════════════════════════════════════════════════

class PDFSplitDialog(QDialog):
    """Diálogo para dividir PDF."""
    def __init__(self, total_pages, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dividir PDF")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #2d2d30; color: white;")

        layout = QVBoxLayout(self)

        # Info
        lbl = QLabel(f"Documento com {total_pages} páginas")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #4ec9b0;")
        layout.addWidget(lbl)

        # Mode selection
        self.radio_range = QRadioButton("Dividir por intervalo de páginas")
        self.radio_range.setChecked(True)
        self.radio_each = QRadioButton("Dividir cada página individualmente")
        self.radio_extract = QRadioButton("Extrair páginas específicas")

        for r in [self.radio_range, self.radio_each, self.radio_extract]:
            r.setStyleSheet("color: white; padding: 4px;")
            layout.addWidget(r)

        # Range inputs
        self.range_widget = QWidget()
        hbox = QHBoxLayout(self.range_widget)
        hbox.addWidget(QLabel("De:"))
        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, total_pages)
        self.spin_start.setValue(1)
        self.spin_start.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; padding: 4px;")
        hbox.addWidget(self.spin_start)
        hbox.addWidget(QLabel("Até:"))
        self.spin_end = QSpinBox()
        self.spin_end.setRange(1, total_pages)
        self.spin_end.setValue(total_pages)
        self.spin_end.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; padding: 4px;")
        hbox.addWidget(self.spin_end)
        layout.addWidget(self.range_widget)

        # Extract pages input
        self.extract_widget = QWidget()
        ebox = QHBoxLayout(self.extract_widget)
        ebox.addWidget(QLabel("Páginas:"))
        self.txt_pages = QLineEdit()
        self.txt_pages.setPlaceholderText("Ex: 1, 3, 5-8, 12")
        self.txt_pages.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; padding: 4px;")
        ebox.addWidget(self.txt_pages)
        self.extract_widget.setVisible(False)
        layout.addWidget(self.extract_widget)

        # Toggle visibility
        self.radio_range.toggled.connect(lambda c: self.range_widget.setVisible(c))
        self.radio_each.toggled.connect(lambda c: (self.range_widget.setVisible(False), self.extract_widget.setVisible(False)) if c else None)
        self.radio_extract.toggled.connect(lambda c: (self.extract_widget.setVisible(c), self.range_widget.setVisible(False)) if c else None)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.setStyleSheet("QPushButton { background: #007acc; color: white; padding: 8px 20px; border: none; border-radius: 4px; } QPushButton:hover { background: #0098ff; }")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_mode(self):
        if self.radio_range.isChecked():
            return 'range'
        elif self.radio_each.isChecked():
            return 'each'
        else:
            return 'extract'


class ExportDialog(QDialog):
    """Diálogo avançado de exportação."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Dados")
        self.setMinimumWidth(420)
        self.setStyleSheet("background-color: #2d2d30; color: white;")

        layout = QVBoxLayout(self)

        lbl = QLabel("Escolha o formato de exportação")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #4ec9b0; margin-bottom: 10px;")
        layout.addWidget(lbl)

        btn_style = """
            QPushButton {
                background-color: #3e3e42;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 14px 20px;
                text-align: left;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #505055; }
            QPushButton:pressed { background-color: #007acc; }
        """

        self.btn_excel = QPushButton("  Excel (.xlsx) — Planilha formatada com cores e filtros")
        self.btn_excel.setIcon(qta.icon('fa5s.file-excel', color='#55ff55'))
        self.btn_excel.setIconSize(QSize(24, 24))
        self.btn_excel.setStyleSheet(btn_style)
        self.btn_excel.clicked.connect(lambda: self.done(1))

        self.btn_csv = QPushButton("  CSV (.csv) — Texto separado por ponto-e-vírgula")
        self.btn_csv.setIcon(qta.icon('fa5s.file-csv', color='#ffaa55'))
        self.btn_csv.setIconSize(QSize(24, 24))
        self.btn_csv.setStyleSheet(btn_style)
        self.btn_csv.clicked.connect(lambda: self.done(2))

        self.btn_pdf = QPushButton("  PDF Relatório — Documento formatado profissional")
        self.btn_pdf.setIcon(qta.icon('fa5s.file-pdf', color='#ff5555'))
        self.btn_pdf.setIconSize(QSize(24, 24))
        self.btn_pdf.setStyleSheet(btn_style)
        self.btn_pdf.clicked.connect(lambda: self.done(3))

        self.btn_txt = QPushButton("  Texto (.txt) — Texto bruto extraído")
        self.btn_txt.setIcon(qta.icon('fa5s.file-alt', color='#aaaaaa'))
        self.btn_txt.setIconSize(QSize(24, 24))
        self.btn_txt.setStyleSheet(btn_style)
        self.btn_txt.clicked.connect(lambda: self.done(4))

        layout.addWidget(self.btn_excel)
        layout.addWidget(self.btn_csv)
        layout.addWidget(self.btn_pdf)
        layout.addWidget(self.btn_txt)

        # Cancel
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: transparent; color: #aaa; border: 1px solid #555; border-radius: 4px; padding: 8px;")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)


# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════

class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #252526; border-right: 1px solid #3e3e42;")

        layout = QVBoxLayout(self)

        # Header
        lbl = QLabel("EXPLORADOR")
        lbl.setStyleSheet("color: #ccc; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl)

        # File List
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("border: none; background-color: #252526; color: #fff;")
        layout.addWidget(self.file_list)

        # Import Button
        self.btn_import = QPushButton(" Importar Arquivos...")
        self.btn_import.setIcon(qta.icon('fa5s.file-import', color='white'))
        self.btn_import.setIconSize(QSize(20, 20))
        self.btn_import.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:pressed { background-color: #0b4a75; }
        """)
        layout.addWidget(self.btn_import)


# ═══════════════════════════════════════════════════════════════════════════
# Properties Panel
# ═══════════════════════════════════════════════════════════════════════════

class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(370)
        self.setStyleSheet("background-color: #252526; border-left: 1px solid #3e3e42;")

        layout = QVBoxLayout(self)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: #2d2d30; color: #ccc; padding: 8px 12px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; border-top: 2px solid #0e639c; }
        """)
        layout.addWidget(self.tabs)

        # Tab 1: Ajustes
        self.tools_widget = QWidget()
        self.setup_tools(self.tools_widget)
        self.tabs.addTab(self.tools_widget, "Ajustes")

        # Tab 2: Assistente IA
        self.chat_widget = QWidget()
        self.setup_chat(self.chat_widget)
        self.tabs.addTab(self.chat_widget, "Assistente IA")

        # Tab 3: Extração
        self.results_widget = QWidget()
        self.setup_results(self.results_widget)
        self.tabs.addTab(self.results_widget, "Extração")

    def setup_chat(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 10, 5, 5)

        from PySide6.QtWidgets import QTextEdit
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3e3e42; font-family: Segoe UI;")
        self.chat_history.setHtml("<div style='color: #6a9955'><i>Olá! Eu sou a IA do Strukturis.</i><br>Carregue um documento e me diga o que extrair.<br>Ex: 'Crie uma tabela com os produtos e preços'</div>")
        layout.addWidget(self.chat_history)

        hbox = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ex: Extraia o valor total...")
        self.chat_input.setStyleSheet("background-color: #252526; color: white; border: 1px solid #007acc; padding: 5px;")

        self.btn_send_chat = QPushButton("Enviar")
        self.btn_send_chat.setIcon(qta.icon('fa5s.paper-plane', color='white'))
        self.btn_send_chat.setStyleSheet("background-color: #007acc; color: white; padding: 5px; border: none;")

        hbox.addWidget(self.chat_input)
        hbox.addWidget(self.btn_send_chat)
        layout.addLayout(hbox)

    def setup_tools(self, widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignTop)

        btn_style = """
            QPushButton {
                background-color: #3e3e42;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #505055; }
            QPushButton:checked { background-color: #d83b01; }
        """
        grp_style = "QGroupBox { color: #ccc; font-weight: bold; margin-top: 10px; border: 1px solid #3e3e42; border-radius: 5px; padding-top: 20px; }"

        # ── Navigation (PDF) ──
        self.grp_nav = QGroupBox("Navegação de Páginas")
        self.grp_nav.setStyleSheet(grp_style)
        self.grp_nav.setVisible(False)

        nav_layout = QVBoxLayout()

        hbox_nav = QHBoxLayout()
        self.btn_prev_page = QPushButton()
        self.btn_prev_page.setIcon(qta.icon('fa5s.chevron-left', color='white'))
        self.btn_prev_page.setStyleSheet(btn_style)

        self.lbl_page_info = QLabel("Página 0 / 0")
        self.lbl_page_info.setAlignment(Qt.AlignCenter)
        self.lbl_page_info.setStyleSheet("color: white; font-weight: bold;")

        self.btn_next_page = QPushButton()
        self.btn_next_page.setIcon(qta.icon('fa5s.chevron-right', color='white'))
        self.btn_next_page.setStyleSheet(btn_style)

        hbox_nav.addWidget(self.btn_prev_page)
        hbox_nav.addWidget(self.lbl_page_info)
        hbox_nav.addWidget(self.btn_next_page)
        nav_layout.addLayout(hbox_nav)

        # Direct page jump
        hbox_jump = QHBoxLayout()
        lbl_goto = QLabel("Ir para:")
        lbl_goto.setStyleSheet("color: #aaa; font-size: 10px;")
        hbox_jump.addWidget(lbl_goto)
        self.spin_page = QSpinBox()
        self.spin_page.setMinimum(1)
        self.spin_page.setMaximum(1)
        self.spin_page.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; border-radius: 4px; padding: 4px; min-width: 50px;")
        hbox_jump.addWidget(self.spin_page)
        self.btn_goto_page = QPushButton("Ir")
        self.btn_goto_page.setStyleSheet("background: #007acc; color: white; border: none; border-radius: 4px; padding: 5px 14px; font-weight: bold;")
        hbox_jump.addWidget(self.btn_goto_page)
        hbox_jump.addStretch()
        nav_layout.addLayout(hbox_jump)

        self.grp_nav.setLayout(nav_layout)
        layout.addWidget(self.grp_nav)

        # ── Modelo de Documento ──
        grp_model = QGroupBox("Modelo de Documento")
        grp_model.setStyleSheet(grp_style)
        vbox_m = QVBoxLayout()

        self.combo_model = QComboBox()
        self.combo_model.addItem("Auto-Detectar")
        for m in ALL_MODELS:
            self.combo_model.addItem(m.NAME)
        self.combo_model.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; border-radius: 4px; padding: 6px;")
        vbox_m.addWidget(self.combo_model)

        self.lbl_model_info = QLabel("Selecione ou deixe auto-detectar")
        self.lbl_model_info.setStyleSheet("color: #6a9955; font-size: 10px; padding: 2px;")
        self.lbl_model_info.setWordWrap(True)
        vbox_m.addWidget(self.lbl_model_info)

        self.btn_model_library = QPushButton(" 📚 Biblioteca de Modelos")
        self.btn_model_library.setIcon(qta.icon('fa5s.th-large', color='#c586c0'))
        self.btn_model_library.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #3e3e42, stop:1 #4a3e55);
                color: #c586c0; border: 1px solid #6a4f7a;
                border-radius: 6px; padding: 8px; font-weight: bold;
            }
            QPushButton:hover { background: #5a4670; color: white; border-color: #c586c0; }
        """)
        vbox_m.addWidget(self.btn_model_library)

        # Auto-detect banner (hidden until file loaded)
        self.auto_detect_banner = QFrame()
        self.auto_detect_banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(78,201,176,0.12), stop:1 rgba(0,122,204,0.08));
                border: 1px solid #4ec9b0; border-radius: 6px; padding: 6px;
            }
        """)
        self.auto_detect_banner.setVisible(False)
        banner_layout = QVBoxLayout(self.auto_detect_banner)
        banner_layout.setContentsMargins(8, 4, 8, 4)
        self.lbl_detect_icon = QLabel()
        self.lbl_detect_icon.setStyleSheet("border: none; background: transparent;")
        self.lbl_detect_result = QLabel("")
        self.lbl_detect_result.setStyleSheet("color: #4ec9b0; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        self.lbl_detect_result.setWordWrap(True)
        bh = QHBoxLayout()
        bh.addWidget(self.lbl_detect_icon)
        bh.addWidget(self.lbl_detect_result, 1)
        banner_layout.addLayout(bh)
        self.btn_apply_detected = QPushButton("Aplicar")
        self.btn_apply_detected.setStyleSheet("background: #4ec9b0; color: #1e1e1e; border: none; border-radius: 4px; padding: 4px 12px; font-size: 10px; font-weight: bold;")
        self.btn_apply_detected.setVisible(False)
        banner_layout.addWidget(self.btn_apply_detected)
        vbox_m.addWidget(self.auto_detect_banner)

        grp_model.setLayout(vbox_m)
        layout.addWidget(grp_model)

        # ── Process Button ──
        self.btn_process = QPushButton(" EXTRAIR DADOS (Scan)")
        self.btn_process.setIcon(qta.icon('fa5s.microchip', color='white'))
        self.btn_process.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 13px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #0098ff; }
            QPushButton:pressed { background-color: #005a9e; }
        """)
        layout.addWidget(self.btn_process)

        # ── Seleção e Recorte ──
        grp_sel = QGroupBox("Seleção e Recorte")
        grp_sel.setStyleSheet(grp_style)
        vbox_sel = QVBoxLayout()

        self.btn_toggle_sel = QPushButton(" Ferramenta de Seleção")
        self.btn_toggle_sel.setIcon(qta.icon('fa5s.mouse-pointer', color='white'))
        self.btn_toggle_sel.setCheckable(True)
        self.btn_toggle_sel.setStyleSheet(btn_style)
        vbox_sel.addWidget(self.btn_toggle_sel)

        hbox_actions = QHBoxLayout()
        self.btn_crop_action = QPushButton(" Recortar")
        self.btn_crop_action.setIcon(qta.icon('fa5s.cut', color='white'))
        self.btn_crop_action.setToolTip("Corta a imagem para a área selecionada")
        self.btn_crop_action.setStyleSheet(btn_style)
        self.btn_crop_action.setEnabled(False)
        hbox_actions.addWidget(self.btn_crop_action)
        vbox_sel.addLayout(hbox_actions)

        grp_sel.setLayout(vbox_sel)
        layout.addWidget(grp_sel)

        # ── Rotação ──
        grp_rot = QGroupBox("Rotação")
        grp_rot.setStyleSheet(grp_style)
        vbox_r = QVBoxLayout()

        hbox_r = QHBoxLayout()
        self.btn_rot_left = QPushButton()
        self.btn_rot_left.setIcon(qta.icon('fa5s.undo', color='white'))
        self.btn_rot_left.setToolTip("Girar Esquerda 90°")
        self.btn_rot_left.setStyleSheet(btn_style)

        self.btn_rot_right = QPushButton()
        self.btn_rot_right.setIcon(qta.icon('fa5s.redo', color='white'))
        self.btn_rot_right.setToolTip("Girar Direita 90°")
        self.btn_rot_right.setStyleSheet(btn_style)

        hbox_r.addWidget(self.btn_rot_left)
        hbox_r.addWidget(self.btn_rot_right)
        vbox_r.addLayout(hbox_r)

        lbl_fine = QLabel("Ajuste Fino")
        lbl_fine.setStyleSheet("color: #aaa; margin-top: 5px;")
        vbox_r.addWidget(lbl_fine)
        self.slider_rot = QSlider(Qt.Horizontal)
        self.slider_rot.setRange(-45, 45)
        self.slider_rot.setValue(0)
        vbox_r.addWidget(self.slider_rot)

        grp_rot.setLayout(vbox_r)
        layout.addWidget(grp_rot)

        # ── Filtro de Páginas ──
        grp_pages = QGroupBox("Filtro de Páginas (Texto)")
        grp_pages.setStyleSheet(grp_style)
        vbox_p = QVBoxLayout()
        hbox_p = QHBoxLayout()
        lbl_icon_p = QLabel()
        lbl_icon_p.setPixmap(qta.icon('fa5s.copy', color='#aaa').pixmap(16, 16))
        hbox_p.addWidget(lbl_icon_p)
        self.txt_pages = QLineEdit()
        self.txt_pages.setPlaceholderText("Ex: 1-3, 5")
        self.txt_pages.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; border-radius: 4px; padding: 6px;")
        hbox_p.addWidget(self.txt_pages)
        vbox_p.addLayout(hbox_p)
        grp_pages.setLayout(vbox_p)
        layout.addWidget(grp_pages)

        # ── Melhoria de Imagem ──
        grp_filter = QGroupBox("Melhoria de Imagem")
        grp_filter.setStyleSheet(grp_style)
        vbox_f = QVBoxLayout()
        self.btn_bw = QPushButton(" Alto Contraste (P&B)")
        self.btn_bw.setIcon(qta.icon('fa5s.adjust', color='white'))
        self.btn_bw.setCheckable(True)
        self.btn_bw.setStyleSheet(btn_style)
        vbox_f.addWidget(self.btn_bw)
        grp_filter.setLayout(vbox_f)
        layout.addWidget(grp_filter)

        # ── Ferramentas PDF ──
        grp_pdf = QGroupBox("Ferramentas PDF")
        grp_pdf.setStyleSheet(grp_style)
        vbox_pdf = QVBoxLayout()

        self.btn_split_pdf = QPushButton(" Dividir PDF")
        self.btn_split_pdf.setIcon(qta.icon('fa5s.cut', color='#ffaa55'))
        self.btn_split_pdf.setStyleSheet(btn_style)

        self.btn_merge_pdf = QPushButton(" Mesclar PDFs")
        self.btn_merge_pdf.setIcon(qta.icon('fa5s.object-group', color='#55aaff'))
        self.btn_merge_pdf.setStyleSheet(btn_style)

        vbox_pdf.addWidget(self.btn_split_pdf)
        vbox_pdf.addWidget(self.btn_merge_pdf)
        grp_pdf.setLayout(vbox_pdf)
        layout.addWidget(grp_pdf)

        # ── Exportar ──
        grp_export = QGroupBox("Exportar")
        grp_export.setStyleSheet(grp_style)
        vbox_e = QVBoxLayout()

        self.btn_export = QPushButton(" EXPORTAR DADOS")
        self.btn_export.setIcon(qta.icon('fa5s.download', color='white'))
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #16825d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #1a9e70; }
            QPushButton:pressed { background-color: #126b4c; }
        """)
        vbox_e.addWidget(self.btn_export)

        grp_export.setLayout(vbox_e)
        layout.addWidget(grp_export)

        scroll.setWidget(inner)

        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def setup_results(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)

        sub_tabs = QTabWidget()
        layout.addWidget(sub_tabs)

        # 1. Text Output
        from PySide6.QtWidgets import QTextEdit
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setStyleSheet("border: none; font-family: Consolas;")
        sub_tabs.addTab(self.txt_output, "Texto")

        # 2. Smart Data (Tree)
        from PySide6.QtWidgets import QTreeWidget
        self.tree_smart = QTreeWidget()
        self.tree_smart.setHeaderLabel("Dados Identificados")
        self.tree_smart.setStyleSheet("border: none;")
        sub_tabs.addTab(self.tree_smart, "Smart Data")

        # 3. Table
        from PySide6.QtWidgets import QTableView
        self.table_view = QTableView()
        self.table_view.setStyleSheet("border: none;")
        sub_tabs.addTab(self.table_view, "Tabela")

        # 4. Modelo (Rich HTML)
        from PySide6.QtWidgets import QTextBrowser
        self.txt_model_output = QTextBrowser()
        self.txt_model_output.setReadOnly(True)
        self.txt_model_output.setOpenExternalLinks(False)
        self.txt_model_output.setStyleSheet("""
            QTextBrowser {
                border: none; background: #1e1e1e; color: #d4d4d4;
                font-family: 'Segoe UI', sans-serif; font-size: 12px;
            }
        """)
        sub_tabs.addTab(self.txt_model_output, "📊 Modelo")


# ═══════════════════════════════════════════════════════════════════════════
# Main Window
# ═══════════════════════════════════════════════════════════════════════════

class ModernMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strukturis Pro")
        self.resize(1400, 900)
        self.setStyleSheet("background-color: #1e1e1e; color: #cccccc;")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # 2. Center
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # AI Header
        self.ai_header = QFrame()
        self.ai_header.setStyleSheet("background-color: #2d2d30; border-bottom: 1px solid #3e3e42; padding: 5px;")
        self.ai_header.setFixedHeight(40)
        hbox_ai = QHBoxLayout(self.ai_header)
        hbox_ai.setContentsMargins(10, 0, 10, 0)

        self.lbl_ai_status = QLabel("⚡ IA Local (Offline)")
        self.lbl_ai_status.setStyleSheet("color: #aaa; font-weight: bold;")
        hbox_ai.addWidget(self.lbl_ai_status)
        hbox_ai.addStretch()

        self.btn_config_ai = QPushButton(" Configurar IA Nuvem")
        self.btn_config_ai.setIcon(qta.icon('fa5s.cloud', color='#007acc'))
        self.btn_config_ai.setStyleSheet("background: transparent; color: #007acc; border: 1px solid #007acc; border-radius: 4px; padding: 4px 8px;")
        hbox_ai.addWidget(self.btn_config_ai)

        center_layout.addWidget(self.ai_header)

        # Viewer
        from ui.image_viewer import ImageViewer
        self.viewer = ImageViewer()
        self.viewer.setStyleSheet("background-color: #1e1e1e; border: none;")
        center_layout.addWidget(self.viewer, 1)

        # Status Bar
        self.status_bar = QFrame()
        self.status_bar.setStyleSheet("background-color: #007acc; padding: 2px 10px;")
        self.status_bar.setFixedHeight(26)
        hbox_sb = QHBoxLayout(self.status_bar)
        hbox_sb.setContentsMargins(10, 0, 10, 0)

        self.lbl_status = QLabel("Pronto")
        self.lbl_status.setStyleSheet("color: white; font-size: 11px;")
        hbox_sb.addWidget(self.lbl_status)
        hbox_sb.addStretch()

        self.lbl_doc_info = QLabel("")
        self.lbl_doc_info.setStyleSheet("color: white; font-size: 11px;")
        hbox_sb.addWidget(self.lbl_doc_info)

        center_layout.addWidget(self.status_bar)

        # Progress Bar (hidden by default)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(3)
        self.progress.setStyleSheet("QProgressBar { border: none; background: #1e1e1e; } QProgressBar::chunk { background: #007acc; }")
        self.progress.setVisible(False)
        center_layout.addWidget(self.progress)

        main_layout.addWidget(center_widget, 1)

        # 3. Properties Panel
        self.props_panel = PropertiesPanel()
        main_layout.addWidget(self.props_panel)

        # ── Wire Connections ──
        self.btn_config_ai.clicked.connect(self.configure_cloud_ai)
        self.check_connectivity()

        # Import
        self.sidebar.btn_import.clicked.connect(self.import_files)
        self.sidebar.file_list.itemClicked.connect(self.on_file_selected)

        # Navigation
        self.props_panel.btn_prev_page.clicked.connect(lambda: self.navigate_page(-1))
        self.props_panel.btn_next_page.clicked.connect(lambda: self.navigate_page(1))
        self.props_panel.btn_goto_page.clicked.connect(self.jump_to_page)

        # Process
        self.props_panel.btn_process.clicked.connect(self.manual_process_trigger)

        # Selection/Crop
        self.props_panel.btn_toggle_sel.clicked.connect(self.toggle_selection_mode)
        self.props_panel.btn_crop_action.clicked.connect(self.perform_crop)

        # Chat
        self.props_panel.btn_send_chat.clicked.connect(self.send_chat_message)
        self.props_panel.chat_input.returnPressed.connect(self.send_chat_message)

        # Rotation
        self.props_panel.btn_rot_left.clicked.connect(lambda: self.rotate_image(-90))
        self.props_panel.btn_rot_right.clicked.connect(lambda: self.rotate_image(90))
        self.props_panel.slider_rot.valueChanged.connect(self.on_fine_rotate)
        self.props_panel.btn_bw.clicked.connect(self.toggle_bw)

        # Export
        self.props_panel.btn_export.clicked.connect(self.export_data)

        # PDF Tools
        self.props_panel.btn_split_pdf.clicked.connect(self.split_pdf)
        self.props_panel.btn_merge_pdf.clicked.connect(self.merge_pdfs)

        # Model change
        self.props_panel.combo_model.currentTextChanged.connect(self.on_model_changed)

        # Model Library
        self.props_panel.btn_model_library.clicked.connect(self.open_model_library)
        self.props_panel.btn_apply_detected.clicked.connect(self.apply_detected_model)

        # Drag & Drop
        self.setAcceptDrops(True)

        # State
        self.current_file_path = None
        self.current_page_idx = 0
        self.total_pages = 0
        self.current_img = None
        self.original_img = None
        self._detected_model = None
        self._detected_confidence = 0.0
        self.current_df = pd.DataFrame()
        self.current_text = ""
        self.current_model_data = {}

    # ── Status ──
    def set_status(self, msg, doc_info=""):
        self.lbl_status.setText(msg)
        if doc_info:
            self.lbl_doc_info.setText(doc_info)

    # ── Model Changed ──
    def on_model_changed(self, model_name):
        if model_name == "Auto-Detectar":
            self.props_panel.lbl_model_info.setText("O modelo será detectado automaticamente")
            self.props_panel.lbl_model_info.setStyleSheet("color: #6a9955; font-size: 10px; padding: 2px;")
        else:
            model = ModelManager.get_model_by_name(model_name)
            if model:
                self.props_panel.lbl_model_info.setText(model.DESCRIPTION)
                self.props_panel.lbl_model_info.setStyleSheet("color: #4ec9b0; font-size: 10px; padding: 2px;")

    # ── Process ──
    def manual_process_trigger(self):
        if self.viewer.drawing_crop or self.viewer.crop_rect_item:
            self.read_selection()
        else:
            self.run_ocr_and_update("Processando página completa...")

    def run_ocr_and_update(self, status_msg="Processando..."):
        self.props_panel.txt_output.setText(status_msg)
        self.set_status("Processando OCR...")
        self.progress.setVisible(True)
        QApplication.processEvents()

        text = OCRManager.extract_text(self.current_img, lang='por')
        self.current_text = text

        entities = SmartParser.extract_entities(text)
        df = SmartParser.preview_structure(text)
        self.current_df = df

        # Apply document model
        model_name = self.props_panel.combo_model.currentText()
        model, model_data, model_df = ModelManager.process(text, model_name)

        if model and model_data:
            self.current_model_data = model_data
            if not model_df.empty:
                self.current_df = model_df

            # Update model info
            self.props_panel.lbl_model_info.setText(f"✓ {model.NAME}")
            self.props_panel.lbl_model_info.setStyleSheet("color: #4ec9b0; font-size: 10px; font-weight: bold; padding: 2px;")

            # Rich HTML model output
            self.props_panel.txt_model_output.setHtml(self._render_model_html(model, model_data))

        self.display_results(text, entities, self.current_df)
        self.progress.setVisible(False)
        self.set_status("Extração completa", f"{len(text)} caracteres extraídos")

    # ── Navigation ──
    def navigate_page(self, delta):
        if not self.current_file_path or self.total_pages <= 1:
            return
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < self.total_pages:
            self.load_page(new_idx)

    def jump_to_page(self):
        """Jump directly to the page specified in the spinbox."""
        if not self.current_file_path or self.total_pages <= 1:
            return
        target = self.props_panel.spin_page.value() - 1  # 0-indexed
        if 0 <= target < self.total_pages:
            self.load_page(target)

    def load_page(self, page_idx):
        self.current_page_idx = page_idx
        self.props_panel.lbl_page_info.setText(f"Página {self.current_page_idx + 1} / {self.total_pages}")
        self.props_panel.btn_prev_page.setEnabled(self.current_page_idx > 0)
        self.props_panel.btn_next_page.setEnabled(self.current_page_idx < self.total_pages - 1)
        self.props_panel.spin_page.blockSignals(True)
        self.props_panel.spin_page.setMaximum(self.total_pages)
        self.props_panel.spin_page.setValue(self.current_page_idx + 1)
        self.props_panel.spin_page.blockSignals(False)

        if self.current_file_path.lower().endswith('.pdf'):
            img = ImageProcessing.load_pdf_as_image(self.current_file_path, self.current_page_idx)
        else:
            img = ImageProcessing.load_image(self.current_file_path)

        if img is not None:
            img, _ = ImageProcessing.deskew_image(img)
            self.original_img = img.copy()
            self.current_img = img
            self.viewer.set_image(self.current_img)
            self.props_panel.txt_output.setText(f"Página {page_idx + 1} carregada. Clique em 'EXTRAIR DADOS' para processar.")
            self.set_status(f"Página {page_idx + 1} de {self.total_pages}")

            self.props_panel.slider_rot.blockSignals(True)
            self.props_panel.slider_rot.setValue(0)
            self.props_panel.slider_rot.blockSignals(False)

    # ── Selection ──
    def toggle_selection_mode(self, checked):
        self.viewer.toggle_crop_mode(checked)
        self.props_panel.btn_crop_action.setEnabled(checked)

        if checked:
            self.props_panel.btn_toggle_sel.setText(" Cancelar Seleção")
            self.props_panel.btn_toggle_sel.setIcon(qta.icon('fa5s.times', color='white'))
        else:
            self.props_panel.btn_toggle_sel.setText(" Ferramenta de Seleção")
            self.props_panel.btn_toggle_sel.setIcon(qta.icon('fa5s.mouse-pointer', color='white'))

    def perform_crop(self):
        rect = self.viewer.get_crop_rect_coords()
        if rect:
            x, y, w, h = rect
            if self.current_img is not None:
                self.current_img = self.current_img[y:y + h, x:x + w]
                self.original_img = self.current_img.copy()
                self.props_panel.slider_rot.blockSignals(True)
                self.props_panel.slider_rot.setValue(0)
                self.props_panel.slider_rot.blockSignals(False)
                self.viewer.set_image(self.current_img)
                self.props_panel.btn_toggle_sel.setChecked(False)
                self.toggle_selection_mode(False)
                self.run_ocr_and_update("Recorte aplicado. Lendo novo texto...")

    def read_selection(self):
        rect = self.viewer.get_crop_rect_coords()
        if rect:
            x, y, w, h = rect
            if self.current_img is not None:
                roi_img = self.current_img[y:y + h, x:x + w]
                self.props_panel.txt_output.setText("Lendo área selecionada...")
                QApplication.processEvents()
                text = OCRManager.extract_text(roi_img, lang='por')
                entities = SmartParser.extract_entities(text)
                df = SmartParser.preview_structure(text)
                self.current_text = text
                self.current_df = df
                self.display_results(text, entities, df)
                self.props_panel.txt_output.append(f"\n--- Fim da Leitura de Área ({w}x{h}) ---")

    # ── Rotation ──
    def on_fine_rotate(self, value):
        if not hasattr(self, 'original_img') or self.original_img is None:
            return
        self.current_img = ImageProcessing.rotate_image(self.original_img, value)
        self.viewer.set_image(self.current_img)

    def rotate_image(self, angle):
        if self.current_img is None:
            return
        self.current_img = ImageProcessing.rotate_image(self.current_img, angle)
        self.original_img = self.current_img.copy()
        self.viewer.set_image(self.current_img)
        self.props_panel.slider_rot.blockSignals(True)
        self.props_panel.slider_rot.setValue(0)
        self.props_panel.slider_rot.blockSignals(False)

    def toggle_bw(self):
        if self.current_img is None:
            return
        if self.props_panel.btn_bw.isChecked():
            self.current_img = ImageProcessing.apply_bw_filter(self.current_img)
        else:
            if hasattr(self, 'original_img') and self.original_img is not None:
                self.current_img = self.original_img.copy()
        self.viewer.set_image(self.current_img)

    # ── Drag & Drop ──
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.sidebar.file_list.addItems(files)
            self.process_file(files[0])

    def on_file_selected(self, item):
        self.process_file(item.text())

    # ── Import ──
    def import_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Importar Arquivos", "", "Documentos (*.pdf *.png *.jpg *.jpeg *.tiff)"
        )
        if files:
            self.sidebar.file_list.addItems(files)
            self.process_file(files[0])

    # ── Process File ──
    def process_file(self, file_path):
        try:
            self.progress.setVisible(True)
            QApplication.processEvents()

            ftype = FileHandler.identify_file_type(file_path)
            self.current_file_path = file_path

            filename = os.path.basename(file_path)
            self.set_status(f"Carregando {filename}...", filename)

            if ftype == 'pdf':
                self.total_pages = ImageProcessing.get_pdf_page_count(file_path)
                self.props_panel.grp_nav.setVisible(True)
                self.load_page(0)
            elif ftype == 'image':
                self.total_pages = 1
                self.props_panel.grp_nav.setVisible(False)
                self.load_page(0)
            else:
                QMessageBox.warning(self, "Formato não suportado", f"O arquivo '{filename}' não é um formato suportado.")
                return

            # Auto-detect model on file load
            self._auto_detect_on_load()

        except Exception as e:
            print(f"Erro: {e}")
            QMessageBox.critical(self, "Erro no Processamento", str(e))
        finally:
            self.progress.setVisible(False)

    def _auto_detect_on_load(self):
        """Quick OCR on first page to auto-detect document model."""
        if self.current_img is None:
            return
        try:
            text = OCRManager.extract_text(self.current_img, lang='por')
            if not text or len(text.strip()) < 20:
                return
            model, score = ModelManager.auto_detect(text)
            self._detected_model = model
            self._detected_confidence = score
            if model and score > 0.25:
                self.props_panel.lbl_detect_icon.setPixmap(
                    qta.icon(model.ICON, color='#4ec9b0').pixmap(20, 20))
                self.props_panel.lbl_detect_result.setText(
                    f"Detectado: {model.NAME} ({score:.0%})")
                self.props_panel.btn_apply_detected.setVisible(True)
                self.props_panel.auto_detect_banner.setVisible(True)
                self.props_panel.combo_model.blockSignals(True)
                idx = self.props_panel.combo_model.findText(model.NAME)
                if idx >= 0:
                    self.props_panel.combo_model.setCurrentIndex(idx)
                self.props_panel.combo_model.blockSignals(False)
            else:
                self.props_panel.auto_detect_banner.setVisible(False)
        except Exception:
            pass

    def apply_detected_model(self):
        """Apply the auto-detected model and run full extraction."""
        if self._detected_model:
            self.props_panel.combo_model.blockSignals(True)
            idx = self.props_panel.combo_model.findText(self._detected_model.NAME)
            if idx >= 0:
                self.props_panel.combo_model.setCurrentIndex(idx)
            self.props_panel.combo_model.blockSignals(False)
            self.run_ocr_and_update("Aplicando modelo detectado...")

    def open_model_library(self):
        """Open the visual model library dialog."""
        dlg = ModelLibraryDialog(
            detected_model=self._detected_model,
            confidence=self._detected_confidence,
            parent=self
        )
        if dlg.exec() == QDialog.Accepted and dlg.selected_model:
            idx = self.props_panel.combo_model.findText(dlg.selected_model)
            if idx >= 0:
                self.props_panel.combo_model.setCurrentIndex(idx)
            if self.current_img is not None:
                self.run_ocr_and_update(f"Aplicando modelo: {dlg.selected_model}...")

    def _render_model_html(self, model, data):
        """Render model extraction results as rich HTML."""
        html = f"""
        <div style='font-family: Segoe UI, sans-serif; padding: 10px;'>
            <div style='background: linear-gradient(135deg, #2d4a3e, #1e3a2e);
                        border-radius: 10px; padding: 16px; margin-bottom: 12px;
                        border: 1px solid #4ec9b0;'>
                <span style='font-size: 20px; color: #4ec9b0; font-weight: bold;'>
                    {model.NAME}
                </span><br>
                <span style='color: #888; font-size: 11px;'>{model.DESCRIPTION}</span>
            </div>
        """
        list_keys = {'verbas', 'registros', 'lancamentos', 'itens', 'clausulas'}

        # Scalar fields as cards
        scalars = {k: v for k, v in data.items() if k not in list_keys and k != 'tipo_documento'}
        if scalars:
            html += "<div style='display: flex; flex-wrap: wrap;'>"
            for k, v in scalars.items():
                label = k.replace('_', ' ').title()
                val = v if not isinstance(v, list) else ', '.join(str(i) for i in v)
                html += f"""
                <div style='background: #2d2d30; border: 1px solid #3e3e42;
                            border-radius: 8px; padding: 10px; margin: 4px;
                            min-width: 140px;'>
                    <div style='color: #888; font-size: 9px; text-transform: uppercase;
                                letter-spacing: 1px;'>{label}</div>
                    <div style='color: #fff; font-size: 13px; font-weight: bold;
                                margin-top: 4px;'>{val}</div>
                </div>
                """
            html += "</div>"

        # List fields as tables
        for k in list_keys:
            items = data.get(k, [])
            if not items:
                continue
            label = k.replace('_', ' ').title()
            html += f"""
            <div style='margin-top: 14px;'>
                <div style='color: #4ec9b0; font-weight: bold; font-size: 13px;
                            border-bottom: 2px solid #4ec9b0; padding-bottom: 4px;
                            margin-bottom: 8px;'>
                    {label} ({len(items)} itens)
                </div>
            """
            if isinstance(items[0], dict):
                cols = list(items[0].keys())
                html += "<table style='width: 100%; border-collapse: collapse; font-size: 11px;'>"
                html += "<tr>"
                for c in cols:
                    html += f"<th style='background: #2d2d30; color: #ccc; padding: 6px 8px; border: 1px solid #3e3e42; text-align: left;'>{c}</th>"
                html += "</tr>"
                for i, item in enumerate(items[:30]):
                    bg = '#252528' if i % 2 == 0 else '#1e1e1e'
                    html += f"<tr style='background: {bg};'>"
                    for c in cols:
                        val = item.get(c, '')
                        color = '#4ec9b0' if c in ('vencimento',) and val else '#ff6b6b' if c in ('desconto',) and val else '#d4d4d4'
                        html += f"<td style='padding: 5px 8px; border: 1px solid #3e3e42; color: {color};'>{val or ''}</td>"
                    html += "</tr>"
                html += "</table>"
            html += "</div>"

        html += "</div>"
        return html

    # ── Display Results ──
    def display_results(self, text, entities, df):
        import pandas as pd
        self.props_panel.txt_output.setText(text)

        from PySide6.QtWidgets import QTreeWidgetItem
        self.props_panel.tree_smart.clear()

        if entities:
            for category, items in entities.items():
                parent = QTreeWidgetItem([category.upper()])
                self.props_panel.tree_smart.addTopLevelItem(parent)
                for item in items:
                    child = QTreeWidgetItem([item])
                    parent.addChild(child)
                parent.setExpanded(True)
        else:
            self.props_panel.tree_smart.addTopLevelItem(QTreeWidgetItem(["Nenhum dado estruturado identificado."]))

        # Table
        from PySide6.QtCore import QAbstractTableModel

        class PandasModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data

            def rowCount(self, parent=None):
                return self._data.shape[0]

            def columnCount(self, parent=None):
                return self._data.shape[1]

            def data(self, index, role=Qt.DisplayRole):
                if index.isValid() and role == Qt.DisplayRole:
                    return str(self._data.iloc[index.row(), index.column()])
                return None

            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if role == Qt.DisplayRole:
                    if orientation == Qt.Horizontal:
                        return str(self._data.columns[section])
                    if orientation == Qt.Vertical:
                        return str(self._data.index[section])
                return None

        if not df.empty:
            model = PandasModel(df)
            self.props_panel.table_view.setModel(model)

        self.props_panel.tabs.setCurrentIndex(2)

    def display_table_only(self, df):
        from PySide6.QtCore import QAbstractTableModel

        class PandasModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data

            def rowCount(self, parent=None):
                return self._data.shape[0]

            def columnCount(self, parent=None):
                return self._data.shape[1]

            def data(self, index, role=Qt.DisplayRole):
                if index.isValid() and role == Qt.DisplayRole:
                    return str(self._data.iloc[index.row(), index.column()])
                return None

            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if role == Qt.DisplayRole:
                    if orientation == Qt.Horizontal:
                        return str(self._data.columns[section])
                    if orientation == Qt.Vertical:
                        return str(self._data.index[section])
                return None

        if not df.empty:
            model = PandasModel(df)
            self.props_panel.table_view.setModel(model)

    # ── Export ──
    def export_data(self):
        text = self.props_panel.txt_output.toPlainText()
        if not text:
            QMessageBox.warning(self, "Aviso", "Nenhum texto extraído para exportar.")
            return

        dlg = ExportDialog(self)
        result = dlg.exec()

        if result == 0:
            return

        df = self.current_df if not self.current_df.empty else DataParser.parse_to_dataframe(text)
        doc_title = "Strukturis Pro"
        if self.current_file_path:
            doc_title = os.path.basename(self.current_file_path)

        metadata = None
        if self.current_model_data and 'tipo_documento' in self.current_model_data:
            metadata = f"Tipo: {self.current_model_data['tipo_documento']}"

        try:
            if result == 1:  # Excel
                path, _ = QFileDialog.getSaveFileName(self, "Salvar Excel", "", "Excel (*.xlsx)")
                if path:
                    Exporter.to_excel(df, path, doc_title=doc_title, metadata=metadata)
                    QMessageBox.information(self, "Sucesso", f"Planilha salva em:\n{path}")

            elif result == 2:  # CSV
                path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV (*.csv)")
                if path:
                    Exporter.to_csv(df, path, metadata=metadata)
                    QMessageBox.information(self, "Sucesso", f"CSV salvo em:\n{path}")

            elif result == 3:  # PDF Report
                path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Relatório", "", "PDF (*.pdf)")
                if path:
                    Exporter.to_pdf_report(df, path, title=doc_title, metadata=metadata)
                    QMessageBox.information(self, "Sucesso", f"PDF relatório salvo em:\n{path}")

            elif result == 4:  # TXT
                path, _ = QFileDialog.getSaveFileName(self, "Salvar Texto", "", "Texto (*.txt)")
                if path:
                    Exporter.to_txt(text, path)
                    QMessageBox.information(self, "Sucesso", f"Texto salvo em:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar: {e}")

    # ── PDF Tools ──
    def split_pdf(self):
        if not self.current_file_path or not self.current_file_path.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Aviso", "Carregue um arquivo PDF primeiro.")
            return

        total = PDFTools.get_page_count(self.current_file_path)
        if total == 0:
            QMessageBox.warning(self, "Aviso", "Não foi possível ler o PDF.")
            return

        dlg = PDFSplitDialog(total, self)
        if dlg.exec() != QDialog.Accepted:
            return

        mode = dlg.get_mode()

        try:
            if mode == 'range':
                start = dlg.spin_start.value()
                end = dlg.spin_end.value()
                path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Dividido", "", "PDF (*.pdf)")
                if path:
                    ok = PDFTools.split_by_range(self.current_file_path, path, start, end)
                    if ok:
                        QMessageBox.information(self, "Sucesso", f"PDF dividido salvo em:\n{path}\n(Páginas {start} a {end})")

            elif mode == 'each':
                folder = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino")
                if folder:
                    self.progress.setVisible(True)
                    QApplication.processEvents()
                    results = PDFTools.split_each_page(self.current_file_path, folder)
                    self.progress.setVisible(False)
                    QMessageBox.information(self, "Sucesso", f"{len(results)} arquivos gerados em:\n{folder}")

            elif mode == 'extract':
                pages_str = dlg.txt_pages.text()
                pages = self._parse_page_list(pages_str, total)
                if not pages:
                    QMessageBox.warning(self, "Aviso", "Nenhuma página válida especificada.")
                    return
                path, _ = QFileDialog.getSaveFileName(self, "Salvar Páginas Extraídas", "", "PDF (*.pdf)")
                if path:
                    ok = PDFTools.extract_pages(self.current_file_path, path, pages)
                    if ok:
                        QMessageBox.information(self, "Sucesso", f"Páginas extraídas para:\n{path}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao dividir PDF: {e}")
            self.progress.setVisible(False)

    def merge_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs para mesclar", "", "PDF (*.pdf)")
        if not files or len(files) < 2:
            if files:
                QMessageBox.warning(self, "Aviso", "Selecione pelo menos 2 arquivos PDF para mesclar.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Mesclado", "", "PDF (*.pdf)")
        if path:
            self.progress.setVisible(True)
            QApplication.processEvents()
            ok = PDFTools.merge_pdfs(files, path)
            self.progress.setVisible(False)
            if ok:
                QMessageBox.information(self, "Sucesso", f"PDFs mesclados em:\n{path}\n({len(files)} arquivos)")
            else:
                QMessageBox.critical(self, "Erro", "Erro ao mesclar PDFs.")

    def _parse_page_list(self, page_str, total_pages):
        """Parse '1, 3, 5-8, 12' into list of ints."""
        pages = set()
        if not page_str.strip():
            return []
        try:
            parts = page_str.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    s, e = map(int, part.split('-'))
                    pages.update(range(s, e + 1))
                else:
                    pages.add(int(part))
            return sorted([p for p in pages if 1 <= p <= total_pages])
        except Exception:
            return []

    def parse_page_range(self, page_str, total_pages):
        pages = set()
        if not page_str.strip():
            return list(range(total_pages))
        try:
            parts = page_str.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.update(range(start - 1, end))
                else:
                    pages.add(int(part) - 1)
            valid_pages = sorted([p for p in pages if 0 <= p < total_pages])
            return valid_pages if valid_pages else list(range(total_pages))
        except Exception:
            return list(range(total_pages))

    # ── Cloud AI ──
    def check_connectivity(self):
        from core.cloud_agent import CloudAgent
        if CloudAgent.is_connected():
            self.lbl_ai_status.setText("☁ IA Nuvem Disponível (Gemini)")
            self.lbl_ai_status.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        else:
            self.lbl_ai_status.setText("⚠ Sem Internet - Modo Local Ativo")
            self.lbl_ai_status.setStyleSheet("color: #ce9178; font-weight: bold;")

    def configure_cloud_ai(self):
        from core.cloud_agent import CloudAgent
        key, ok = QInputDialog.getText(self, "Configurar Gemini AI",
                                       "Insira sua API Key do Google Gemini (Gratuito):\n(Deixe vazio para usar apenas modo Local)",
                                       QLineEdit.Password)
        if ok:
            CloudAgent.configure(key)
            if key:
                QMessageBox.information(self, "IA Configurada", "Chave registrada! O modo Assistente Inteligente está ativo.")
                self.props_panel.tabs.setCurrentIndex(1)
            self.check_connectivity()

    # ── Chat ──
    def send_chat_message(self):
        msg = self.props_panel.chat_input.text().strip()
        if not msg:
            return

        self.props_panel.chat_history.append(f"<br><b>Você:</b> {msg}")
        self.props_panel.chat_input.clear()
        QApplication.processEvents()

        full_text = self.props_panel.txt_output.toPlainText()
        if not full_text:
            self.props_panel.chat_history.append("<div style='color: #ce9178'><i>Primeiro extraia dados de algum documento (Botão Extrair).</i></div>")
            return

        from core.cloud_agent import CloudAgent
        if not CloudAgent.is_connected() or not CloudAgent.API_KEY:
            self.props_panel.chat_history.append("<div style='color: #ce9178'><i>IA não configurada ou sem internet.</i></div>")
            return

        self.props_panel.chat_history.append("<i>Processando...</i>")
        QApplication.processEvents()

        ai_resp = CloudAgent.enhance_data(full_text, user_instruction=msg)

        if ai_resp:
            if "text_response" in ai_resp:
                self.props_panel.chat_history.append(f"<div style='color: #4ec9b0'><b>Strukturis AI:</b> {ai_resp['text_response']}</div>")
            elif isinstance(ai_resp, list) or "items" in ai_resp:
                self.props_panel.chat_history.append(f"<div style='color: #4ec9b0'><b>Strukturis AI:</b> Tabela gerada. Veja na aba 'Tabela'.</div>")
                import pandas as pd
                try:
                    df = pd.DataFrame(ai_resp if isinstance(ai_resp, list) else ai_resp['items'])
                    self.current_df = df
                    self.display_table_only(df)
                    self.props_panel.tabs.setCurrentIndex(2)
                except Exception:
                    pass
            else:
                self.props_panel.chat_history.append(f"<div style='color: #4ec9b0'><b>Strukturis AI:</b> Dados extraídos.</div>")
                self.props_panel.chat_history.append(f"<code>{json.dumps(ai_resp, indent=2)}</code>")
        else:
            self.props_panel.chat_history.append("<div style='color: red'>Erro na comunicação com a IA.</div>")
