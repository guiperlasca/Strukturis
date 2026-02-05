from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QListWidget, QPushButton, QLabel, QFrame, QSplitter,
                               QTabWidget, QToolBox, QScrollArea, QSlider, QSpinBox, QGroupBox, QLineEdit, QApplication, QMessageBox, QFileDialog, QInputDialog)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QAction
import qtawesome as qta
import json
from core.image_processing import ImageProcessing
from core.ocr_manager import OCRManager
from core.file_handler import FileHandler
from core.smart_parser import SmartParser
from core.data_parser import Exporter, DataParser

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

class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(350) # Widen slightly
        self.setStyleSheet("background-color: #252526; border-left: 1px solid #3e3e42;")
        
        layout = QVBoxLayout(self)
        
        # Tabs for Tools vs Results
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: #2d2d30; color: #ccc; padding: 8px 15px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; border-top: 2px solid #0e639c; }
        """)
        layout.addWidget(self.tabs)
        
        # Tab 1: Ajustes (Tools)
        self.tools_widget = QWidget()
        self.setup_tools(self.tools_widget)
        self.tabs.addTab(self.tools_widget, "Ajustes")
        
        # Tab 2: Assistente IA (Chat)
        self.chat_widget = QWidget()
        self.setup_chat(self.chat_widget)
        self.tabs.addTab(self.chat_widget, "Assistente IA")

        # Tab 3: Extração (Results)
        self.results_widget = QWidget()
        self.setup_results(self.results_widget)
        self.tabs.addTab(self.results_widget, "Extração")

    def setup_chat(self, widget):
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 10, 5, 5)
        
        # History
        from PySide6.QtWidgets import QTextEdit
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3e3e42; font-family: Segoe UI;")
        self.chat_history.setHtml("<div style='color: #6a9955'><i>Olá! Eu sou a IA do Strukturis.</i><br>Carregue um documento e me diga o que extrair.<br>Ex: 'Crie uma tabela com os produtos e preços'</div>")
        layout.addWidget(self.chat_history)
        
        # Input Area
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
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)
        
        # --- STYLES ---
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
        
        # Navigation Group (PDF)
        self.grp_nav = QGroupBox("Navegação")
        self.grp_nav.setStyleSheet("QGroupBox { color: #ccc; font-weight: bold; margin-top: 10px; border: 1px solid #3e3e42; border-radius: 5px; padding-top: 20px; }")
        self.grp_nav.setVisible(False) # Hidden by default, shown for PDFs
        
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
        
        self.grp_nav.setLayout(hbox_nav)
        layout.addWidget(self.grp_nav)

        # Main Process Button
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

        # Selection / Crop Group
        grp_sel = QGroupBox("Seleção e Recorte")
        grp_sel.setStyleSheet("QGroupBox { color: #ccc; font-weight: bold; margin-top: 10px; border: 1px solid #3e3e42; border-radius: 5px; padding-top: 20px; }")
        vbox_sel = QVBoxLayout()

        # Toggle Selection Mode
        self.btn_toggle_sel = QPushButton(" Ferramenta de Seleção")
        self.btn_toggle_sel.setIcon(qta.icon('fa5s.mouse-pointer', color='white'))
        self.btn_toggle_sel.setCheckable(True)
        self.btn_toggle_sel.setStyleSheet(btn_style)
        vbox_sel.addWidget(self.btn_toggle_sel)
        
        # Action Buttons (Hidden until selection active)
        hbox_actions = QHBoxLayout()
        self.btn_crop_action = QPushButton(" Recortar")
        self.btn_crop_action.setIcon(qta.icon('fa5s.cut', color='white'))
        self.btn_crop_action.setToolTip("Corta a imagem para a área selecionada")
        self.btn_crop_action.setStyleSheet(btn_style)
        self.btn_crop_action.setEnabled(False)
        
        # self.btn_read_action removed from here as per user request to have a general button
        # Functionality will be merged into "Extrair Dados" if selection is active
        
        hbox_actions.addWidget(self.btn_crop_action)
        vbox_sel.addLayout(hbox_actions)
        
        grp_sel.setLayout(vbox_sel)
        layout.addWidget(grp_sel)

        # Rotation Group
        grp_rot = QGroupBox("Rotação")
        grp_rot.setStyleSheet("QGroupBox { color: #ccc; font-weight: bold; margin-top: 10px; border: 1px solid #3e3e42; border-radius: 5px; padding-top: 20px; }")
        vbox = QVBoxLayout()

        # Quick Rotate
        hbox = QHBoxLayout()
        self.btn_rot_left = QPushButton()
        self.btn_rot_left.setIcon(qta.icon('fa5s.undo', color='white'))
        self.btn_rot_left.setToolTip("Girar Esquerda 90°")
        self.btn_rot_left.setStyleSheet(btn_style)
        
        self.btn_rot_right = QPushButton()
        self.btn_rot_right.setIcon(qta.icon('fa5s.redo', color='white'))
        self.btn_rot_right.setToolTip("Girar Direita 90°")
        self.btn_rot_right.setStyleSheet(btn_style)
        
        hbox.addWidget(self.btn_rot_left)
        hbox.addWidget(self.btn_rot_right)
        vbox.addLayout(hbox)
        
        # Fine Tune
        lbl_fine = QLabel("Ajuste Fino")
        lbl_fine.setStyleSheet("color: #aaa; margin-top: 5px;")
        vbox.addWidget(lbl_fine)
        self.slider_rot = QSlider(Qt.Horizontal)
        self.slider_rot.setRange(-45, 45)
        self.slider_rot.setValue(0)
        vbox.addWidget(self.slider_rot)
        
        grp_rot.setLayout(vbox)
        layout.addWidget(grp_rot)
        
        # Page Selection Group (Hidden now that we have nav? No, kept for batch export range if needed)
        # Maybe keep it but deprioritize
        grp_pages = QGroupBox("Filtro de Páginas (Texto)")
        grp_pages.setStyleSheet("QGroupBox { color: #ccc; font-weight: bold; margin-top: 10px; border: 1px solid #3e3e42; border-radius: 5px; padding-top: 20px;}")
        vbox_p = QVBoxLayout()
        
        hbox_p = QHBoxLayout()
        lbl_icon_p = QLabel()
        lbl_icon_p.setPixmap(qta.icon('fa5s.copy', color='#aaa').pixmap(16,16))
        hbox_p.addWidget(lbl_icon_p)
        
        self.txt_pages = QLineEdit()
        self.txt_pages.setPlaceholderText("Ex: 1-3, 5")
        self.txt_pages.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; border-radius: 4px; padding: 6px;")
        hbox_p.addWidget(self.txt_pages)
        vbox_p.addLayout(hbox_p)
        
        grp_pages.setLayout(vbox_p)
        layout.addWidget(grp_pages)
        
        # Image Filters Group
        grp_filter = QGroupBox("Melhoria de Imagem")
        grp_filter.setStyleSheet("QGroupBox { color: #ccc; font-weight: bold; margin-top: 10px; border: 1px solid #3e3e42; border-radius: 5px; padding-top: 20px;}")
        vbox_f = QVBoxLayout()
        
        self.btn_bw = QPushButton(" Alto Contraste (P&B)")
        self.btn_bw.setIcon(qta.icon('fa5s.adjust', color='white'))
        self.btn_bw.setCheckable(True)
        self.btn_bw.setStyleSheet(btn_style)
        vbox_f.addWidget(self.btn_bw)
        
        grp_filter.setLayout(vbox_f)
        layout.addWidget(grp_filter)
        
        # Export Actions
        grp_export = QGroupBox("Exportar")
        grp_export.setStyleSheet("QGroupBox { color: #ccc; font-weight: bold; margin-top: 10px; border: 1px solid #3e3e42; border-radius: 5px; padding-top: 20px;}")
        vbox_e = QVBoxLayout()
        
        self.btn_exp_pdf = QPushButton(" PDF Pesquisável")
        self.btn_exp_pdf.setIcon(qta.icon('fa5s.file-pdf', color='#ff5555'))
        self.btn_exp_pdf.setStyleSheet(btn_style)
        
        self.btn_exp_excel = QPushButton(" Excel / CSV")
        self.btn_exp_excel.setIcon(qta.icon('fa5s.file-excel', color='#55ff55'))
        self.btn_exp_excel.setStyleSheet(btn_style)
        
        vbox_e.addWidget(self.btn_exp_pdf)
        vbox_e.addWidget(self.btn_exp_excel)
        
        grp_export.setLayout(vbox_e)
        layout.addWidget(grp_export)

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
        from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
        self.tree_smart = QTreeWidget()
        self.tree_smart.setHeaderLabel("Dados Identificados")
        self.tree_smart.setStyleSheet("border: none;")
        sub_tabs.addTab(self.tree_smart, "Smart Data")
        
        # 3. Table
        from PySide6.QtWidgets import QTableView
        self.table_view = QTableView()
        self.table_view.setStyleSheet("border: none;")
        sub_tabs.addTab(self.table_view, "Tabela")

class ModernMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Strukturis Pro")
        self.resize(1400, 900)
        
        # Styling
        self.setStyleSheet("background-color: #1e1e1e; color: #cccccc;")
        
        # Main Layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 1.5 Center Layout (Header + Viewer)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        # --- AI STATUS HEADER ---
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
        
        # 2. Center Preview Area (Placeholder for QGraphicsView)
        from ui.image_viewer import ImageViewer
        self.viewer = ImageViewer()
        self.viewer.setStyleSheet("background-color: #1e1e1e; border: none;")
        center_layout.addWidget(self.viewer, 1) # Expand
        
        main_layout.addWidget(center_widget, 1) # Add center container
        
        # 3. Properties Panel
        self.props_panel = PropertiesPanel()
        main_layout.addWidget(self.props_panel)
        
        # Wire up AI Config
        self.btn_config_ai.clicked.connect(self.configure_cloud_ai)
        
        # Check connectivity on start (async logic simulation)
        self.check_connectivity()

        # Wire up Import
        self.sidebar.btn_import.clicked.connect(self.import_files)
        self.sidebar.file_list.itemClicked.connect(self.on_file_selected)
        
        # Wire up Tools
        self.props_panel.btn_prev_page.clicked.connect(lambda: self.navigate_page(-1))
        self.props_panel.btn_next_page.clicked.connect(lambda: self.navigate_page(1))
        self.props_panel.btn_process.clicked.connect(self.manual_process_trigger)
        # Wire up Tools
        self.props_panel.btn_toggle_sel.clicked.connect(self.toggle_selection_mode)
        self.props_panel.btn_crop_action.clicked.connect(self.perform_crop)
        
        # Wire up Chat
        self.props_panel.btn_send_chat.clicked.connect(self.send_chat_message)
        self.props_panel.chat_input.returnPressed.connect(self.send_chat_message)
        
        self.props_panel.btn_rot_left.clicked.connect(lambda: self.rotate_image(-90))
        self.props_panel.btn_rot_right.clicked.connect(lambda: self.rotate_image(90))
        self.props_panel.slider_rot.valueChanged.connect(self.on_fine_rotate)
        self.props_panel.btn_bw.clicked.connect(self.toggle_bw)
        
        # Wire up Exports
        self.props_panel.btn_exp_pdf.clicked.connect(self.export_searchable_pdf)
        self.props_panel.btn_exp_excel.clicked.connect(self.export_excel)
        
        # Enable Drag & Drop
        self.setAcceptDrops(True)
        
        # State
        self.current_file_path = None
        self.current_page_idx = 0
        self.total_pages = 0

    def manual_process_trigger(self):
        """Called by the big 'EXTRAIR DADOS' button."""
        # Check if we have a selection active
        if self.viewer.drawing_crop or self.viewer.crop_rect_item: # If selection exists
            self.read_selection()
        else:
            # Full Page / Multi Page Process
            self.run_ocr_and_update("Processando página completa...")

    def navigate_page(self, delta):
        if not self.current_file_path or self.total_pages <= 1: return
        
        new_idx = self.current_page_idx + delta
        if 0 <= new_idx < self.total_pages:
            self.load_page(new_idx)

    def load_page(self, page_idx):
        from core.image_processing import ImageProcessing
        self.current_page_idx = page_idx
        
        # Update UI Labels
        self.props_panel.lbl_page_info.setText(f"Página {self.current_page_idx + 1} / {self.total_pages}")
        self.props_panel.btn_prev_page.setEnabled(self.current_page_idx > 0)
        self.props_panel.btn_next_page.setEnabled(self.current_page_idx < self.total_pages - 1)
        
        # Load Image
        if self.current_file_path.lower().endswith('.pdf'):
            img = ImageProcessing.load_pdf_as_image(self.current_file_path, self.current_page_idx)
        else:
            # Re-load image (shouldn't happen for nav, but valid for generic)
            img = ImageProcessing.load_image(self.current_file_path)
            
        if img is not None:
             # Auto Deskew on load? Yes
             img, _ = ImageProcessing.deskew_image(img)
             self.original_img = img.copy()
             self.current_img = img
             self.viewer.set_image(self.current_img)
             self.props_panel.txt_output.setText(f"Página {page_idx+1} carregada. Clique em 'EXTRAIR DADOS' para processar.")
             
             # Reset modifications state
             self.props_panel.slider_rot.blockSignals(True)
             self.props_panel.slider_rot.setValue(0)
             self.props_panel.slider_rot.blockSignals(False)

    def toggle_selection_mode(self, checked):
        self.viewer.toggle_crop_mode(checked)
        self.props_panel.btn_crop_action.setEnabled(checked)
        # self.props_panel.btn_read_action.setEnabled(checked) # Removed btn_read_action
        
        if checked:
            self.props_panel.btn_toggle_sel.setText(" Cancelar Seleção")
            self.props_panel.btn_toggle_sel.setIcon(qta.icon('fa5s.times', color='white'))
            self.props_panel.btn_toggle_sel.setStyleSheet("""
                QPushButton { background-color: #555; color: white; border: none; border-radius: 4px; padding: 8px; }
                QPushButton:hover { background-color: #666; }
            """)
        else:
            self.props_panel.btn_toggle_sel.setText(" Ferramenta de Seleção")
            self.props_panel.btn_toggle_sel.setIcon(qta.icon('fa5s.mouse-pointer', color='white'))
            self.props_panel.btn_toggle_sel.setStyleSheet("""
                QPushButton { background-color: #3e3e42; color: white; border: none; border-radius: 4px; padding: 8px; }
                QPushButton:hover { background-color: #505055; }
                QPushButton:checked { background-color: #d83b01; }
            """)

    def perform_crop(self):
        """Destructive: Updates current_img to selected area."""
        rect = self.viewer.get_crop_rect_coords()
        if rect:
            x, y, w, h = rect
            if self.current_img is not None:
                self.current_img = self.current_img[y:y+h, x:x+w]
                # Update original to allow further rotations on cropped content
                self.original_img = self.current_img.copy() 
                self.slider_rot_base = 0 
                self.props_panel.slider_rot.blockSignals(True)
                self.props_panel.slider_rot.setValue(0)
                self.props_panel.slider_rot.blockSignals(False)
                
                self.viewer.set_image(self.current_img)
                
                # Exit selection mode
                self.props_panel.btn_toggle_sel.setChecked(False)
                self.toggle_selection_mode(False)
                
                # Re-run OCR
                self.run_ocr_and_update("Recorte aplicado. Lendo novo texto...")

    def read_selection(self):
        """Non-destructive: Reads text from area but keeps full image."""
        rect = self.viewer.get_crop_rect_coords()
        if rect:
            x, y, w, h = rect
            if self.current_img is not None:
                # Crop a copy
                roi_img = self.current_img[y:y+h, x:x+w]
                
                # Run OCR on ROI
                self.props_panel.txt_output.setText("Lendo área selecionada...")
                QApplication.processEvents()
                
                text = OCRManager.extract_text(roi_img, lang='por')
                entities = SmartParser.extract_entities(text)
                df = SmartParser.preview_structure(text)
                
                self.display_results(text, entities, df)
                self.props_panel.txt_output.append(f"\n--- Fim da Leitura de Área ({w}x{h}) ---")

    def run_ocr_and_update(self, status_msg="Processando..."):
        self.props_panel.txt_output.setText(status_msg)
        QApplication.processEvents()
        
        text = OCRManager.extract_text(self.current_img, lang='por')
        entities = SmartParser.extract_entities(text)
        df = SmartParser.preview_structure(text)
        self.display_results(text, entities, df)

    def on_fine_rotate(self, value):
        if not hasattr(self, 'original_img') or self.original_img is None: return
        
        # We rotate from the ORIGINAL (or last saved state) to avoid degradation
        from core.image_processing import ImageProcessing
        self.current_img = ImageProcessing.rotate_image(self.original_img, value)
        self.viewer.set_image(self.current_img)
        # Note: We do NOT re-run OCR on every slide step to avoid lag.
        # User implies "done" when stopping. We could add a timer or "Apply" button?
        # For this version: Visual only until they hit "Export" or another action?
        # BETTER: Use sliderReleased signal if possible, but for now live preview is key.

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.sidebar.file_list.addItems(files)
            self.process_file(files[0]) # Auto-process first dropped

    def on_file_selected(self, item):
        self.process_file(item.text())

    def rotate_image(self, angle):
        if not hasattr(self, 'current_img') or self.current_img is None: return
        from core.image_processing import ImageProcessing
        # For 90 degree clicks, we update the CURRENT image indefinitely
        self.current_img = ImageProcessing.rotate_image(self.current_img, angle)
        self.original_img = self.current_img.copy() # Update base
        self.viewer.set_image(self.current_img)
        # Reset slider
        self.props_panel.slider_rot.blockSignals(True)
        self.props_panel.slider_rot.setValue(0) 
        self.props_panel.slider_rot.blockSignals(False)

    def toggle_bw(self):
        if not hasattr(self, 'current_img'): return
        # Logic to toggle B&W - Requires keeping original state
        pass
        # Simple toggle for demo
        from core.image_processing import ImageProcessing
        if self.props_panel.btn_bw.isChecked():
            self.current_img = ImageProcessing.apply_bw_filter(self.current_img)
        else:
            # Revert to original? We need to keep a clean 'color' copy.
            if hasattr(self, 'original_img'):
                 self.current_img = self.original_img.copy()
        self.viewer.set_image(self.current_img)

    def export_searchable_pdf(self):
        # Implementation of PDF Export
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        if not hasattr(self, 'current_img') or self.current_img is None:
             QMessageBox.warning(self, "Aviso", "Nenhum documento carregado.")
             return

        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Pesquisável", "", "PDF (*.pdf)")
        if path:
            import pytesseract
            pdf = pytesseract.image_to_pdf_or_hocr(self.current_img, extension='pdf', lang='por')
            with open(path, 'wb') as f:
                f.write(pdf)
            QMessageBox.information(self, "Sucesso", f"PDF salvo em:\n{path}")

    def import_files(self):
        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Importar Arquivos", "", "Documentos (*.pdf *.png *.jpg *.jpeg *.tiff)"
        )
        if files:
            self.sidebar.file_list.addItems(files)
            # Process first file immediately
            self.process_file(files[0])

    def export_excel(self):
        # Implementation of Excel Export
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from core.data_parser import Exporter, DataParser
        
        # We need the dataframe. It's not stored in self, but we can re-parse or store it.
        # Ideally store self.current_df in process_file
        
        text = self.props_panel.txt_output.toPlainText()
        if not text:
             QMessageBox.warning(self, "Aviso", "Nenhum texto extraído para exportar.")
             return

        # Re-parse for safety ensure latest text edit is used
        df = DataParser.parse_to_dataframe(text)

        path, _ = QFileDialog.getSaveFileName(self, "Salvar Excel", "", "Excel Files (*.xlsx)")
        if path:
            try:
                Exporter.to_excel(df, path)
                QMessageBox.information(self, "Sucesso", f"Planilha salva em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

    def parse_page_range(self, page_str, total_pages):
        """Parses string like '1-3, 5' into a list of 0-based indices."""
        pages = set()
        if not page_str.strip():
            return list(range(total_pages))
        
        try:
            parts = page_str.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.update(range(start-1, end)) # 1-based to 0-based
                else:
                    pages.add(int(part) - 1)
            
            valid_pages = sorted([p for p in pages if 0 <= p < total_pages])
            return valid_pages if valid_pages else list(range(total_pages))
        except:
            print("Invalid page range, defaulting to all.")
            return list(range(total_pages))

    def check_connectivity(self):
        from core.cloud_agent import CloudAgent
        if CloudAgent.is_connected():
             self.lbl_ai_status.setText("☁ IA Nuvem Disponível (Gemini)")
             self.lbl_ai_status.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        else:
             self.lbl_ai_status.setText("⚠ Sem Internet - Modo Local Ativo")
             self.lbl_ai_status.setStyleSheet("color: #ce9178; font-weight: bold;")

    def configure_cloud_ai(self):
        from PySide6.QtWidgets import QInputDialog
        from core.cloud_agent import CloudAgent
        
        key, ok = QInputDialog.getText(self, "Configurar Gemini AI", 
            "Insira sua API Key do Google Gemini (Gratuito):\n(Deixe vazio para usar apenas modo Local)", 
            QLineEdit.Password)
            
        if ok:
            CloudAgent.configure(key)
            if key:
                QMessageBox.information(self, "IA Configurada", "Chave registrada! O modo Assistente Inteligente está ativo.")
                self.props_panel.tabs.setCurrentIndex(1) # Switch to Chat Tab
            self.check_connectivity()

    def process_file(self, file_path):
        from core.image_processing import ImageProcessing
        from core.file_handler import FileHandler
        from core.cloud_agent import CloudAgent

        try:
            self.progress.setVisible(True)
            self.progress.setRange(0, 0) # Indeterminate
            QApplication.processEvents()

            ftype = FileHandler.identify_file_type(file_path)
            self.current_file_path = file_path
            
            if ftype == 'pdf':
                self.total_pages = ImageProcessing.get_pdf_page_count(file_path)
                self.props_panel.grp_nav.setVisible(True)
                self.load_page(0) # Load first page
                
            elif ftype == 'image':
                self.total_pages = 1
                self.props_panel.grp_nav.setVisible(False)
                self.load_page(0) 

        except Exception as e:
            print(f"Erro: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Erro no Processamento", str(e))
        
        finally:
            self.progress.setVisible(False)


    def display_results(self, text, entities, df):
        # Update Text
        self.props_panel.txt_output.setText(text)
        
        # Update Smart Data (Tree)
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

        # Update Table
        from PySide6.QtCore import QAbstractTableModel
        class PandasModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data
            def rowCount(self, parent=None): return self._data.shape[0]
            def columnCount(self, parent=None): return self._data.shape[1]
            def data(self, index, role=Qt.DisplayRole):
                if index.isValid() and role == Qt.DisplayRole: return str(self._data.iloc[index.row(), index.column()])
                return None
            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if role == Qt.DisplayRole:
                    if orientation == Qt.Horizontal: return str(self._data.columns[section])
                    if orientation == Qt.Vertical: return str(self._data.index[section])
                return None

        if not df.empty:
            model = PandasModel(df)
            self.props_panel.table_view.setModel(model)
        
        # Force switch to Results tab to show user success
        self.props_panel.tabs.setCurrentIndex(1)

    def send_chat_message(self):
        msg = self.props_panel.chat_input.text().strip()
        if not msg: return
        
        # User UI
        self.props_panel.chat_history.append(f"<br><b>Você:</b> {msg}")
        self.props_panel.chat_input.clear()
        QApplication.processEvents()
        
        # Check context
        full_text = self.props_panel.txt_output.toPlainText()
        if not full_text:
            self.props_panel.chat_history.append("<div style='color: #ce9178'><i>Primeiro extraia dados de algum documento (Botão Extrair).</i></div>")
            return
            
        from core.cloud_agent import CloudAgent
        if not CloudAgent.is_connected() or not CloudAgent.API_KEY:
             self.props_panel.chat_history.append("<div style='color: #ce9178'><i>IA não configurada ou sem internet.</i></div>")
             return

        # Send to AI
        self.props_panel.chat_history.append("<i>Processando...</i>")
        QApplication.processEvents()
        
        ai_resp = CloudAgent.enhance_data(full_text, user_instruction=msg)
        
        # Handle Response
        if ai_resp:
            if "text_response" in ai_resp:
                # Text answer
                self.props_panel.chat_history.append(f"<div style='color: #4ec9b0'><b>Strukturis AI:</b> {ai_resp['text_response']}</div>")
            elif isinstance(ai_resp, list) or "items" in ai_resp:
                 # It's a list/table!
                 self.props_panel.chat_history.append(f"<div style='color: #4ec9b0'><b>Strukturis AI:</b> Gere uma tabela com os dados solicitados. Veja na aba 'Tabela'.</div>")
                 # Force update table
                 import pandas as pd
                 try:
                     df = pd.DataFrame(ai_resp if isinstance(ai_resp, list) else ai_resp['items'])
                     self.display_table_only(df)
                     self.props_panel.tabs.setCurrentIndex(2) # Switch to Table (now tab 2 or 3? Check index)
                 except:
                     pass
            else:
                 # Dictionary
                 self.props_panel.chat_history.append(f"<div style='color: #4ec9b0'><b>Strukturis AI:</b> Dados extraídos.</div>")
                 self.props_panel.chat_history.append(f"<code>{json.dumps(ai_resp, indent=2)}</code>")
        else:
            self.props_panel.chat_history.append("<div style='color: red'>Erro na comunicação com a IA.</div>")

    def display_table_only(self, df):
        # Helper to update just table
        from PySide6.QtCore import QAbstractTableModel
        class PandasModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self._data = data
            def rowCount(self, parent=None): return self._data.shape[0]
            def columnCount(self, parent=None): return self._data.shape[1]
            def data(self, index, role=Qt.DisplayRole):
                if index.isValid() and role == Qt.DisplayRole: return str(self._data.iloc[index.row(), index.column()])
                return None
            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if role == Qt.DisplayRole:
                    if orientation == Qt.Horizontal: return str(self._data.columns[section])
                    if orientation == Qt.Vertical: return str(self._data.index[section])
                return None
        
        if not df.empty:
            model = PandasModel(df)
            self.props_panel.table_view.setModel(model)

