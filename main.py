import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
# from ui.main_window import MainWindow # Legacy
from ui.modern_main_window import ModernMainWindow
import qtawesome as qta 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Modern Dark Theme Setup
    app.setStyle("Fusion")
    
    # Simple Dark Palette (Expanded)
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(45, 45, 45)) 
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(0, 122, 204))
    palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)
    
    # window = MainWindow()
    window = ModernMainWindow()
    window.show()
    sys.exit(app.exec())
