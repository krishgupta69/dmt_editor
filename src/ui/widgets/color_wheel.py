"""
3-way color wheel widget for Shadows / Midtones / Highlights.
70px diameter, full hue spectrum at edge, saturation from center,
draggable dot, luminance slider below.
"""
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QConicalGradient, QRadialGradient, QColor, QPen, QBrush, QMouseEvent
)


class ColorWheel(QWidget):
    """A single 70px color wheel with draggable control point and luminance slider."""
    colorChanged = pyqtSignal(str, float, float, float)  # (zone, hue, sat, lum)

    def __init__(self, zone: str = "Shadows", parent=None):
        super().__init__(parent)
        self.zone = zone
        self.wheel_radius = 35  # 70px diameter / 2
        self.setFixedSize(80, 120)

        # Current position of the dot in normalized coords (-1..1)
        self._dot_x = 0.0
        self._dot_y = 0.0
        self._dragging = False

        # Layout for luminance slider + label below the wheel
        self._lum_value = 0.0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = 40  # Center of the wheel area
        r = self.wheel_radius

        # Draw hue spectrum ring using conical gradient
        conical = QConicalGradient(cx, cy, 0)
        for i in range(361):
            conical.setColorAt(i / 360.0, QColor.fromHsv(i, 255, 220))
        painter.setBrush(QBrush(conical))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Inner circle: radial gradient from white center to transparent edge (saturation)
        radial = QRadialGradient(cx, cy, r)
        radial.setColorAt(0.0, QColor(200, 200, 200, 220))
        radial.setColorAt(0.7, QColor(128, 128, 128, 60))
        radial.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(radial))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Thin border
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Draw dot
        dot_px = cx + self._dot_x * r
        dot_py = cy + self._dot_y * r
        painter.setPen(QPen(QColor("white"), 2))
        painter.setBrush(QBrush(QColor("#7C3AED")))
        painter.drawEllipse(QPointF(dot_px, dot_py), 5, 5)

        # Center crosshair
        painter.setPen(QPen(QColor(100, 100, 100, 80), 1))
        painter.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        painter.drawLine(QPointF(cx, cy - r), QPointF(cx, cy + r))

        # Label below
        painter.setPen(QColor("#AAAAAA"))
        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)
        painter.drawText(0, 85, self.width(), 15, Qt.AlignmentFlag.AlignCenter, self.zone)

        # Luminance bar
        bar_y = 100
        bar_w = 60
        bar_x = (self.width() - bar_w) / 2
        bar_h = 6
        # Draw gradient bar (dark to light)
        for i in range(bar_w):
            t = i / bar_w
            c = int(t * 255)
            painter.setPen(QColor(c, c, c))
            painter.drawLine(int(bar_x + i), bar_y, int(bar_x + i), bar_y + bar_h)
        # Draw lum marker
        lum_pos = bar_x + (self._lum_value + 1.0) / 2.0 * bar_w
        painter.setPen(QPen(QColor("#7C3AED"), 2))
        painter.drawLine(int(lum_pos), bar_y - 2, int(lum_pos), bar_y + bar_h + 2)

        painter.end()

    def _pos_to_norm(self, pos: QPointF):
        cx = self.width() / 2
        cy = 40
        r = self.wheel_radius
        dx = (pos.x() - cx) / r
        dy = (pos.y() - cy) / r
        # Clamp to unit circle
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1.0:
            dx /= dist
            dy /= dist
        return dx, dy

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            cy = 40
            # Check if in luminance bar area
            if pos.y() > 95:
                self._update_luminance(pos)
            else:
                self._dot_x, self._dot_y = self._pos_to_norm(pos)
                self._dragging = True
                self._emit()
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self._dot_x, self._dot_y = self._pos_to_norm(event.position())
            self._emit()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._dot_x = 0.0
        self._dot_y = 0.0
        self._lum_value = 0.0
        self._emit()
        self.update()

    def _update_luminance(self, pos: QPointF):
        bar_w = 60
        bar_x = (self.width() - bar_w) / 2
        t = (pos.x() - bar_x) / bar_w
        t = max(0.0, min(1.0, t))
        self._lum_value = t * 2.0 - 1.0  # -1..1
        self._emit()
        self.update()

    def _emit(self):
        hue = math.degrees(math.atan2(-self._dot_y, self._dot_x)) % 360
        sat = math.sqrt(self._dot_x ** 2 + self._dot_y ** 2)
        self.colorChanged.emit(self.zone, hue, sat, self._lum_value)
