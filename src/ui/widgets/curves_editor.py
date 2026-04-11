"""
Bezier curves editor for color grading.
200x200px canvas, 4x4 grid, diagonal default line, click-to-add control points,
drag to reshape, smooth bezier interpolation.
Tabs: Master / R / G / B.
"""
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor, QBrush, QMouseEvent


class CurvesCanvas(QWidget):
    """200x200 canvas with grid, bezier curve, and draggable control points."""
    curveChanged = pyqtSignal(str, list)  # (channel, points_list)

    CANVAS_SIZE = 200
    POINT_RADIUS = 5
    GRAB_RADIUS = 10

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.CANVAS_SIZE, self.CANVAS_SIZE)
        self.channel = "Master"  # Master / R / G / B

        # Points stored as normalized (0..1, 0..1), y=0 is bottom
        # Default: bottom-left to top-right diagonal
        self._points: dict[str, list[list[float]]] = {
            "Master": [[0.0, 0.0], [1.0, 1.0]],
            "R": [[0.0, 0.0], [1.0, 1.0]],
            "G": [[0.0, 0.0], [1.0, 1.0]],
            "B": [[0.0, 0.0], [1.0, 1.0]],
        }
        self._dragging_idx: int | None = None

    @property
    def points(self):
        return self._points[self.channel]

    @points.setter
    def points(self, pts):
        self._points[self.channel] = pts

    def _to_screen(self, p: list[float]) -> QPointF:
        return QPointF(p[0] * self.CANVAS_SIZE, (1.0 - p[1]) * self.CANVAS_SIZE)

    def _to_norm(self, sp: QPointF) -> list[float]:
        x = max(0.0, min(1.0, sp.x() / self.CANVAS_SIZE))
        y = max(0.0, min(1.0, 1.0 - sp.y() / self.CANVAS_SIZE))
        return [x, y]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.CANVAS_SIZE

        # Background
        painter.fillRect(0, 0, s, s, QColor("#111111"))

        # 4x4 grid
        painter.setPen(QPen(QColor("#2A2A2A"), 1))
        for i in range(1, 4):
            t = i * s / 4
            painter.drawLine(QPointF(t, 0), QPointF(t, s))
            painter.drawLine(QPointF(0, t), QPointF(s, t))

        # Diagonal reference
        painter.setPen(QPen(QColor("#333333"), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(0, s), QPointF(s, 0))

        # Build bezier path through control points
        pts = self.points
        if len(pts) >= 2:
            color_map = {
                "Master": QColor("#FFFFFF"),
                "R": QColor("#FF4444"),
                "G": QColor("#44FF44"),
                "B": QColor("#4488FF"),
            }
            pen_color = color_map.get(self.channel, QColor("#FFFFFF"))
            painter.setPen(QPen(pen_color, 2))

            path = QPainterPath()
            screen_pts = [self._to_screen(p) for p in pts]
            path.moveTo(screen_pts[0])

            if len(screen_pts) == 2:
                path.lineTo(screen_pts[1])
            else:
                # Catmull-Rom to Bezier conversion for smooth curve
                for i in range(len(screen_pts) - 1):
                    p0 = screen_pts[max(0, i - 1)]
                    p1 = screen_pts[i]
                    p2 = screen_pts[min(len(screen_pts) - 1, i + 1)]
                    p3 = screen_pts[min(len(screen_pts) - 1, i + 2)]

                    # Control points
                    cp1 = QPointF(
                        p1.x() + (p2.x() - p0.x()) / 6.0,
                        p1.y() + (p2.y() - p0.y()) / 6.0
                    )
                    cp2 = QPointF(
                        p2.x() - (p3.x() - p1.x()) / 6.0,
                        p2.y() - (p3.y() - p1.y()) / 6.0
                    )
                    path.cubicTo(cp1, cp2, p2)

            painter.drawPath(path)

            # Draw control points (white filled squares)
            painter.setPen(QPen(QColor("white"), 1))
            painter.setBrush(QBrush(QColor("white")))
            for sp in screen_pts:
                r = self.POINT_RADIUS
                painter.drawRect(QRectF(sp.x() - r, sp.y() - r, r * 2, r * 2))

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()

        # Check if clicking near an existing point
        for i, p in enumerate(self.points):
            sp = self._to_screen(p)
            dx = pos.x() - sp.x()
            dy = pos.y() - sp.y()
            if math.sqrt(dx * dx + dy * dy) < self.GRAB_RADIUS:
                self._dragging_idx = i
                return

        # Otherwise, add a new point and sort by x
        new_p = self._to_norm(pos)
        self.points.append(new_p)
        self.points.sort(key=lambda p: p[0])
        self._dragging_idx = self.points.index(new_p)
        self._emit()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging_idx is not None:
            new_p = self._to_norm(event.position())
            pts = self.points
            # Lock endpoints' x but allow y changes
            if self._dragging_idx == 0:
                new_p[0] = 0.0
            elif self._dragging_idx == len(pts) - 1:
                new_p[0] = 1.0
            pts[self._dragging_idx] = new_p
            pts.sort(key=lambda p: p[0])
            # Re-find the index after sort
            try:
                self._dragging_idx = pts.index(new_p)
            except ValueError:
                self._dragging_idx = None
            self._emit()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging_idx = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Double-click to remove a control point (not endpoints)."""
        pos = event.position()
        for i, p in enumerate(self.points):
            if i == 0 or i == len(self.points) - 1:
                continue
            sp = self._to_screen(p)
            dx = pos.x() - sp.x()
            dy = pos.y() - sp.y()
            if math.sqrt(dx * dx + dy * dy) < self.GRAB_RADIUS:
                self.points.pop(i)
                self._emit()
                self.update()
                return

    def _emit(self):
        self.curveChanged.emit(self.channel, [list(p) for p in self.points])

    def set_channel(self, ch: str):
        self.channel = ch
        self.update()

    def reset(self):
        self._points[self.channel] = [[0.0, 0.0], [1.0, 1.0]]
        self._emit()
        self.update()


class CurvesEditor(QWidget):
    """Full curves editor with Master / R / G / B tab switcher."""
    curveChanged = pyqtSignal(str, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Channel tabs
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(2)
        self._tab_btns: list[QPushButton] = []
        for ch in ["Master", "R", "G", "B"]:
            btn = QPushButton(ch)
            btn.setCheckable(True)
            btn.setFixedHeight(22)
            color_map = {
                "Master": "#FFFFFF", "R": "#FF4444",
                "G": "#44FF44", "B": "#4488FF"
            }
            c = color_map[ch]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1E1E1E; color: {c};
                    border: none; border-radius: 4px; font-size: 10px; font-weight: bold;
                }}
                QPushButton:checked {{
                    background-color: #333333; border-bottom: 2px solid {c};
                }}
            """)
            btn.clicked.connect(lambda _, c=ch: self._switch_channel(c))
            tabs_layout.addWidget(btn)
            self._tab_btns.append(btn)
        self._tab_btns[0].setChecked(True)
        layout.addLayout(tabs_layout)

        # Canvas
        self.canvas = CurvesCanvas()
        self.canvas.curveChanged.connect(self.curveChanged.emit)
        layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)

    def _switch_channel(self, ch: str):
        for btn in self._tab_btns:
            btn.setChecked(btn.text() == ch)
        self.canvas.set_channel(ch)
