"""
Color Grading Panel — the full contents of the "Color Grade" tab in the right panel.

Layout (top to bottom):
  [Auto Color] full-width button
  [Before/After] toggle
  ─── Basic Sliders (collapsible) ───
  ─── Color Wheels (collapsible) ───
  ─── Curves Editor (collapsible) ───
  ─── LUT Presets (collapsible) ───
  [Apply to Selected] [Apply to All] [Copy Grade]
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.widgets.grading_slider import GradingSlider
from ui.widgets.color_wheel import ColorWheel
from ui.widgets.curves_editor import CurvesEditor
from ui.widgets.lut_presets import LutPresetsGrid


class CollapsibleSection(QWidget):
    """A section with a clickable header that expands/collapses its content."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        self._header = QPushButton(f"  \u25BC  {title}")
        self._header.setStyleSheet("""
            QPushButton {
                background-color: #141414;
                color: #AAAAAA;
                border: none;
                text-align: left;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E1E1E;
                color: #E5E5E5;
            }
        """)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 4, 8, 8)
        self._content_layout.setSpacing(2)
        layout.addWidget(self._content)

        self._collapsed = False
        self._title = title

    def add_widget(self, widget: QWidget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        arrow = "\u25B6" if self._collapsed else "\u25BC"
        self._header.setText(f"  {arrow}  {self._title}")


class ColorGradingPanel(QWidget):
    """Full color grading panel for the right dock's Color Grade tab."""

    # Signals for downstream application
    gradeChanged = pyqtSignal(dict)   # emits the full grading state
    applyToSelected = pyqtSignal()
    applyToAll = pyqtSignal()
    copyGrade = pyqtSignal()
    beforeAfterToggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._grade_state = {}
        self._init_ui()

    def _init_ui(self):
        # Wrap everything in a scroll area for the narrow right panel
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # ── TOP ACTIONS ──
        auto_btn = QPushButton("\u2728 Auto Color")
        auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                color: #E5E5E5;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #7C3AED;
                background-color: #222222;
            }
        """)
        auto_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(auto_btn)

        ba_btn = QPushButton("\U0001F441 Before / After")
        ba_btn.setCheckable(True)
        ba_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                color: #AAAAAA;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:checked {
                background-color: #7C3AED;
                color: white;
                border-color: #7C3AED;
            }
        """)
        ba_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ba_btn.toggled.connect(self.beforeAfterToggled.emit)
        layout.addWidget(ba_btn)

        # ── BASIC SLIDERS ──
        sliders_section = CollapsibleSection("Basic Adjustments")

        temp_gradient = ("qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                         "stop:0 #3B82F6, stop:0.5 #AAAAAA, stop:1 #F97316)")
        tint_gradient = ("qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                         "stop:0 #22C55E, stop:0.5 #AAAAAA, stop:1 #EC4899)")

        slider_defs = [
            ("Exposure",    -100, 100,  0, None),
            ("Contrast",    -100, 100,  0, None),
            ("Saturation",     0, 200, 100, None),
            ("Highlights",  -100, 100,  0, None),
            ("Shadows",     -100, 100,  0, None),
            ("Whites",      -100, 100,  0, None),
            ("Blacks",      -100, 100,  0, None),
            ("Temperature", -100, 100,  0, temp_gradient),
            ("Tint",        -100, 100,  0, tint_gradient),
            ("Sharpness",      0, 100,  0, None),
            ("Vignette",       0, 100,  0, None),
        ]
        self._sliders: dict[str, GradingSlider] = {}
        for name, lo, hi, default, grad in slider_defs:
            s = GradingSlider(name, lo, hi, default, track_gradient=grad)
            s.valueChanged.connect(self._on_slider_change)
            sliders_section.add_widget(s)
            self._sliders[name] = s

        layout.addWidget(sliders_section)

        # ── COLOR WHEELS ──
        wheels_section = CollapsibleSection("Color Wheels")
        wheels_row = QHBoxLayout()
        wheels_row.setSpacing(4)
        self._wheels: dict[str, ColorWheel] = {}
        for zone in ["Shadows", "Midtones", "Highlights"]:
            w = ColorWheel(zone)
            w.colorChanged.connect(self._on_wheel_change)
            wheels_row.addWidget(w)
            self._wheels[zone] = w
        wheels_section.add_layout(wheels_row)
        layout.addWidget(wheels_section)

        # ── CURVES EDITOR ──
        curves_section = CollapsibleSection("Curves")
        self.curves = CurvesEditor()
        self.curves.curveChanged.connect(self._on_curve_change)
        curves_section.add_widget(self.curves)
        layout.addWidget(curves_section)

        # ── LUT PRESETS ──
        luts_section = CollapsibleSection("LUT Presets")
        self.lut_grid = LutPresetsGrid()
        self.lut_grid.lutSelected.connect(self._on_lut_selected)
        luts_section.add_widget(self.lut_grid)
        layout.addWidget(luts_section)

        layout.addStretch(1)

        scroll.setWidget(container)
        outer.addWidget(scroll, stretch=1)

        # ── BOTTOM ACTIONS ──
        bottom = QHBoxLayout()
        bottom.setContentsMargins(6, 4, 6, 6)

        apply_sel_btn = QPushButton("Apply to Selected")
        apply_sel_btn.setStyleSheet(self._action_btn_style())
        apply_sel_btn.clicked.connect(self.applyToSelected.emit)

        apply_all_btn = QPushButton("Apply to All")
        apply_all_btn.setStyleSheet(self._action_btn_style())
        apply_all_btn.clicked.connect(self.applyToAll.emit)

        copy_btn = QPushButton("Copy Grade")
        copy_btn.setStyleSheet(self._action_btn_style())
        copy_btn.clicked.connect(self.copyGrade.emit)

        bottom.addWidget(apply_sel_btn)
        bottom.addWidget(apply_all_btn)
        bottom.addWidget(copy_btn)

        outer.addLayout(bottom)

    def _action_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #1E1E1E;
                color: #E5E5E5;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                border-color: #7C3AED;
                background-color: #222222;
            }
        """

    def _on_slider_change(self, name: str, value: int):
        self._grade_state[name] = value
        self.gradeChanged.emit(self._grade_state)

    def _on_wheel_change(self, zone: str, hue: float, sat: float, lum: float):
        self._grade_state[f"wheel_{zone}"] = {"hue": hue, "sat": sat, "lum": lum}
        self.gradeChanged.emit(self._grade_state)

    def _on_curve_change(self, channel: str, points: list):
        self._grade_state[f"curve_{channel}"] = points
        self.gradeChanged.emit(self._grade_state)

    def _on_lut_selected(self, name: str, path: str):
        self._grade_state["lut"] = {"name": name, "path": path}
        self.gradeChanged.emit(self._grade_state)

    def get_grade_state(self) -> dict:
        return dict(self._grade_state)

    def reset_all(self):
        for slider in self._sliders.values():
            slider.reset()
        for wheel in self._wheels.values():
            wheel.mouseDoubleClickEvent(None)
        self.curves.canvas.reset()
        self._grade_state.clear()
        self.gradeChanged.emit(self._grade_state)
