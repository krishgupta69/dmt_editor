import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from ui.main_window import MainWindow

def load_stylesheet() -> str:
    # CapCut-style dark theme with violet accent
    # bg #0D0D0D, surface #1A1A1A, accent #7C3AED, text #E5E5E5
    return """
    QMainWindow {
        background-color: #0D0D0D;
        color: #E5E5E5;
    }
    QWidget {
        background-color: #0D0D0D;
        color: #E5E5E5;
        font-family: 'Inter', sans-serif;
    }
    /* Surface Elements */
    QDockWidget {
        background-color: #1A1A1A;
        color: #E5E5E5;
        border: none;
    }
    QDockWidget::title {
        background-color: #1A1A1A;
        padding: 5px;
        color: #E5E5E5;
    }
    /* Buttons */
    QPushButton {
        background-color: #1A1A1A;
        color: #E5E5E5;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 5px 10px;
    }
    QPushButton:hover {
        background-color: #333333;
    }
    /* Primary / Accent Button */
    QPushButton#ExportButton {
        background-color: #7C3AED;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
    }
    QPushButton#ExportButton:hover {
        background-color: #6D28D9;
    }
    /* Tabs */
    QTabWidget::pane {
        border: 1px solid #333333;
        background-color: #1A1A1A;
        border-radius: 8px;
    }
    QTabBar::tab {
        background-color: #0D0D0D;
        color: #888888;
        padding: 8px 16px;
        border: none;
    }
    QTabBar::tab:selected {
        color: #E5E5E5;
        border-bottom: 2px solid #7C3AED;
    }
    QTabBar::tab:hover {
        color: #E5E5E5;
    }
    /* Scrollbars */
    QScrollBar:vertical {
        border: none;
        background: #0D0D0D;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #333333;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #7C3AED;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
    }
    /* Sliders */
    QSlider::groove:horizontal {
        border: 1px solid #333333;
        height: 4px;
        background: #0D0D0D;
        border-radius: 2px;
    }
    QSlider::sub-page:horizontal {
        background: #7C3AED;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #7C3AED;
        border: 1px solid #6D28D9;
        width: 14px;
        margin-top: -5px;
        margin-bottom: -5px;
        border-radius: 7px;
    }
    /* Toolbars */
    QToolBar {
        background-color: #1A1A1A;
        border: none;
        border-bottom: 1px solid #333333;
    }
    /* Text Inputs */
    QLineEdit {
        background-color: #0D0D0D;
        border: 1px solid #333333;
        border-radius: 4px;
        padding: 4px;
        color: #E5E5E5;
    }
    QLineEdit:focus {
        border: 1px solid #7C3AED;
    }
    """

def main():
    app = QApplication(sys.argv)
    
    # Optional: Load Inter font from system or resources if available
    font_db = QFontDatabase()
    # Replace with path to actual Inter font if bundling
    # font_id = font_db.addApplicationFont("resources/Inter-Regular.ttf")
    app.setFont(QFont("Inter", 10))
    app.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
