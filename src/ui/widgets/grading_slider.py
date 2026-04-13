"""
Custom slider widget for color grading: 90px label | QSlider | value display.
Double-click value resets. Right-click context menu with "Reset to default".
50ms debounce for live preview.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSlider, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMouseEvent


from typing import Optional

class GradingSlider(QWidget):
    """A labeled slider with value display, reset, and debounced signal."""
    valueChanged = pyqtSignal(str, int)  # (param_name, value)

    def __init__(self, label: str, min_val: int = -100, max_val: int = 100,
                 default: int = 0, track_gradient: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.param_name = label
        self.default_val = default
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(50)
        self._debounce_timer.timeout.connect(self._emit_value)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        # Label (90px)
        self.label = QLabel(label)
        self.label.setFixedWidth(90)
        self.label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        layout.addWidget(self.label)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(default)
        self.slider.valueChanged.connect(self._on_slider_change)

        # Optional gradient on the track (e.g. Temperature blue→orange)
        if track_gradient:
            self.slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    height: 4px;
                    background: {track_gradient};
                    border-radius: 2px;
                }}
                QSlider::handle:horizontal {{
                    background: #7C3AED;
                    border: 1px solid #6D28D9;
                    width: 14px;
                    margin-top: -5px;
                    margin-bottom: -5px;
                    border-radius: 7px;
                }}
            """)
        layout.addWidget(self.slider, stretch=1)

        # Value label
        self.value_label = QLabel(str(default))
        self.value_label.setFixedWidth(32)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setStyleSheet("color: #E5E5E5; font-size: 11px;")
        layout.addWidget(self.value_label)

    def _on_slider_change(self, val: int):
        self.value_label.setText(str(val))
        self._debounce_timer.start()

    def _emit_value(self):
        self.valueChanged.emit(self.param_name, self.slider.value())

    def reset(self):
        self.slider.setValue(self.default_val)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # Double-click anywhere on value label area resets
        self.reset()
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #1A1A1A; color: #E5E5E5; }")
        reset_action = menu.addAction("Reset to default")
        action = menu.exec(event.globalPos())
        if action == reset_action:
            self.reset()
