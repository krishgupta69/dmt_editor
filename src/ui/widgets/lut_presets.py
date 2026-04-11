"""
LUT preset card grid + cube file import functionality.
2-column grid of 80x50px cards for the 6 bundled LUTs,
plus an [+Import .cube LUT] button.
Uses PyOpenColorIO when available, fallback to manual parsing.
"""
import os
import glob

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

try:
    import PyOpenColorIO as OCIO
    OCIO_AVAILABLE = True
except ImportError:
    OCIO_AVAILABLE = False

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "luts"))

# Bundled LUT metadata: display name -> filename (without .cube)
BUNDLED_LUTS = [
    {"name": "Orange+Teal", "file": "orange_teal", "color": "#E8863A"},
    {"name": "Film Noir",   "file": "film_noir",   "color": "#888888"},
    {"name": "Faded Film",  "file": "faded_film",  "color": "#8BAE82"},
    {"name": "Warm Vlog",   "file": "warm_vlog",   "color": "#D4A843"},
    {"name": "Cold Blue",   "file": "cold_blue",   "color": "#4488CC"},
    {"name": "Matte Black", "file": "matte_black", "color": "#555555"},
]


class LutCard(QFrame):
    """An 80x50px LUT preset card."""
    clicked = pyqtSignal(str, str)  # (lut_name, lut_path)

    def __init__(self, name: str, lut_path: str, accent_color: str, parent=None):
        super().__init__(parent)
        self.lut_name = name
        self.lut_path = lut_path
        self.setFixedSize(80, 50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {accent_color}, stop:1 #1A1A1A);
                border-radius: 6px;
                border: 2px solid transparent;
            }}
            QFrame:hover {{
                border: 2px solid #555555;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        label = QLabel(name)
        label.setStyleSheet("color: white; font-size: 9px; font-weight: bold; background: transparent;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.lut_name, self.lut_path)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        color = "#7C3AED" if selected else "transparent"
        curr = self.styleSheet()
        # Simple approach: just update border
        self.setProperty("selected", selected)
        if selected:
            self.setStyleSheet(self.styleSheet().replace("border: 2px solid transparent", f"border: 2px solid #7C3AED"))
        else:
            self.setStyleSheet(self.styleSheet().replace("border: 2px solid #7C3AED", "border: 2px solid transparent"))


class LutPresetsGrid(QWidget):
    """Grid of LUT preset cards with import button."""
    lutSelected = pyqtSignal(str, str)  # (name, path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: list[LutCard] = []
        self._selected_name: str | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(8)
        layout.addWidget(self.grid_widget)

        # Populate bundled LUTs
        row, col = 0, 0
        for lut_info in BUNDLED_LUTS:
            path = os.path.join(ASSETS_DIR, f"{lut_info['file']}.cube")
            card = LutCard(lut_info["name"], path, lut_info["color"])
            card.clicked.connect(self._on_card_clicked)
            self.grid_layout.addWidget(card, row, col)
            self._cards.append(card)
            col += 1
            if col > 1:
                col = 0
                row += 1

        # Import button
        import_btn = QPushButton("+ Import .cube LUT")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                color: #AAAAAA;
                border: 1px dashed #555555;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                border-color: #7C3AED;
                color: #E5E5E5;
            }
        """)
        import_btn.clicked.connect(self._import_lut)
        layout.addWidget(import_btn)

    def _on_card_clicked(self, name: str, path: str):
        self._selected_name = name
        for card in self._cards:
            card.set_selected(card.lut_name == name)
        self.lutSelected.emit(name, path)

    def _import_lut(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import .cube LUT", "", "LUT Files (*.cube *.3dl)"
        )
        if path:
            name = os.path.splitext(os.path.basename(path))[0]
            # Add a new card
            row = self.grid_layout.rowCount()
            col = self.grid_layout.count() % 2
            if col != 0:
                row -= 1
            card = LutCard(name, path, "#7C3AED")
            card.clicked.connect(self._on_card_clicked)
            self.grid_layout.addWidget(card, row, col)
            self._cards.append(card)
            # Auto-select imported
            self._on_card_clicked(name, path)


def load_lut_ocio(lut_path: str):
    """Load a .cube LUT file via PyOpenColorIO and return the transform config."""
    if not OCIO_AVAILABLE:
        print(f"PyOpenColorIO not available. LUT '{lut_path}' loaded as path reference only.")
        return lut_path

    config = OCIO.Config.CreateRaw()
    transform = OCIO.FileTransform()
    transform.setSrc(lut_path)
    transform.setInterpolation(OCIO.Interpolation.INTERP_LINEAR)
    processor = config.getProcessor(transform)
    return processor
