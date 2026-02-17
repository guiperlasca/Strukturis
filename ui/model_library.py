"""
Strukturis Pro — Biblioteca Visual de Modelos de Documentos
Diálogo com tabs por categoria e cards visuais para navegação/seleção de modelos.
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QWidget, QFrame, QGridLayout,
                               QPushButton, QGraphicsDropShadowEffect, QTabWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import qtawesome as qta
from core.document_models import ALL_MODELS, CATEGORIES


class ModelCard(QFrame):
    """Card visual de um modelo de documento."""
    clicked = Signal(str)

    def __init__(self, model, is_detected=False, confidence=0.0, parent=None):
        super().__init__(parent)
        self.model = model
        self.model_name = model.NAME
        self.setFixedSize(210, 195)
        self.setCursor(Qt.PointingHandCursor)

        border_color = "#4ec9b0" if is_detected else "#3e3e42"
        self.setStyleSheet(f"""
            ModelCard {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #2d2d30, stop:1 #252528);
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 12px;
            }}
            ModelCard:hover {{
                border-color: #007acc;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #333337, stop:1 #2a2a2e);
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15 if is_detected else 8)
        shadow.setColor(QColor(78, 201, 176, 80) if is_detected else QColor(0, 0, 0, 60))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        # Icon
        icon_lbl = QLabel()
        color = "#4ec9b0" if is_detected else "#007acc"
        icon_lbl.setPixmap(qta.icon(model.ICON, color=color).pixmap(36, 36))
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        # Name
        name_lbl = QLabel(model.NAME)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(name_lbl)

        # Variant
        var_lbl = QLabel(f"Variante: {model.VARIANT}")
        var_lbl.setAlignment(Qt.AlignCenter)
        var_lbl.setStyleSheet("color: #007acc; font-size: 9px; border:none; background: transparent;")
        layout.addWidget(var_lbl)

        # Description
        desc_lbl = QLabel(model.DESCRIPTION)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #888; font-size: 9px; border: none; background: transparent;")
        layout.addWidget(desc_lbl)

        # Confidence badge
        if is_detected and confidence > 0:
            badge = QLabel(f"⚡ {confidence:.0%} match")
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet("""
                color: #1e1e1e; background: #4ec9b0;
                border-radius: 8px; padding: 2px 8px;
                font-size: 9px; font-weight: bold;
            """)
            layout.addWidget(badge)

    def mousePressEvent(self, event):
        self.clicked.emit(self.model_name)


class ModelLibraryDialog(QDialog):
    """Biblioteca visual de modelos com categorias em tabs."""
    model_selected = Signal(str)

    def __init__(self, detected_model=None, confidence=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Biblioteca de Modelos — Strukturis Pro")
        self.setMinimumSize(780, 560)
        self.selected_model = None
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: white; }
            QScrollArea { border: none; background: transparent; }
            QTabWidget::pane { border: 1px solid #3e3e42; border-radius: 6px; background: #1e1e1e; }
            QTabBar::tab {
                background: #2d2d30; color: #aaa; padding: 8px 18px;
                border: 1px solid #3e3e42; border-bottom: none; border-top-left-radius: 6px;
                border-top-right-radius: 6px; margin-right: 2px;
            }
            QTabBar::tab:selected { background: #1e1e1e; color: #4ec9b0; border-bottom: 2px solid #4ec9b0; }
            QTabBar::tab:hover { background: #333337; color: white; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # Header
        header = QLabel("📚 Biblioteca de Modelos")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff;")
        layout.addWidget(header)

        sub = QLabel("Navegue por categoria e selecione o modelo ideal para o seu documento.")
        sub.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(sub)

        # Detected banner
        if detected_model and confidence > 0.25:
            banner = QFrame()
            banner.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(78,201,176,0.15), stop:1 rgba(0,122,204,0.10));
                    border: 1px solid #4ec9b0; border-radius: 8px; padding: 10px;
                }
            """)
            bh = QHBoxLayout(banner)
            icon_l = QLabel()
            icon_l.setPixmap(qta.icon(detected_model.ICON, color='#4ec9b0').pixmap(28, 28))
            bh.addWidget(icon_l)
            txt = QLabel(f"  Modelo detectado: <b>{detected_model.NAME}</b> ({detected_model.VARIANT}) — confiança: {confidence:.0%}")
            txt.setStyleSheet("color: #4ec9b0; font-size: 12px; border: none; background: transparent;")
            bh.addWidget(txt)
            bh.addStretch()
            btn_use = QPushButton("Usar Este")
            btn_use.setStyleSheet("""
                QPushButton { background: #4ec9b0; color: #1e1e1e; border: none;
                    border-radius: 6px; padding: 8px 20px; font-weight: bold; }
                QPushButton:hover { background: #5fd9c0; }
            """)
            btn_use.clicked.connect(lambda: self._select(detected_model.NAME))
            bh.addWidget(btn_use)
            layout.addWidget(banner)

        # Tab widget for categories
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        # "Todos" tab
        self._add_category_tab(tabs, "Todos", ALL_MODELS, detected_model, confidence)

        # Category tabs
        for cat_name, models in CATEGORIES.items():
            self._add_category_tab(tabs, cat_name, models, detected_model, confidence)

        # Footer
        footer = QHBoxLayout()
        hint = QLabel("Clique em um card para selecionar o modelo")
        hint.setStyleSheet("color: #666; font-size: 10px;")
        footer.addWidget(hint)
        footer.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton { background: transparent; color: #aaa; border: 1px solid #555;
                border-radius: 6px; padding: 8px 24px; }
            QPushButton:hover { border-color: #888; color: white; }
        """)
        btn_cancel.clicked.connect(self.reject)
        footer.addWidget(btn_cancel)
        layout.addLayout(footer)

    def _add_category_tab(self, tabs, name, models, detected_model, confidence):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        grid = QGridLayout(container)
        grid.setSpacing(14)
        grid.setContentsMargins(12, 12, 12, 12)

        for i, model in enumerate(models):
            is_det = (detected_model == model) if detected_model else False
            conf = confidence if is_det else 0.0
            card = ModelCard(model, is_detected=is_det, confidence=conf)
            card.clicked.connect(self._select)
            grid.addWidget(card, i // 3, i % 3)

        scroll.setWidget(container)

        count = len(models)
        tab_label = f"{name} ({count})"
        tabs.addTab(scroll, tab_label)

    def _select(self, name):
        self.selected_model = name
        self.accept()
