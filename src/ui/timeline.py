from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QKeyEvent

class ClipItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height, color_hex, label, parent=None):
        super().__init__(x, y, width, height, parent)
        self.setBrush(QBrush(QColor(color_hex)))
        self.setPen(QPen(Qt.GlobalColor.transparent))
        self.setFlags(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        
        text = QGraphicsTextItem(label, self)
        text.setDefaultTextColor(QColor("white"))
        text.setPos(x + 5, y + ((height - 20) / 2))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(QPen(QColor("white"), 2))
                # Concept: floating toolbar would be emitted to show here
            else:
                self.setPen(QPen(Qt.GlobalColor.transparent))
        return super().itemChange(change, value)


class TimelineView(QGraphicsView):
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setStyleSheet("background-color: #0D0D0D; border: none;")
        self.setRenderHint(self.renderHints()) # Antialiasing etc if needed

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)


class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Headers
        headers = QFrame()
        headers.setFixedWidth(80)
        headers.setStyleSheet("background-color: #1A1A1A; border-right: 1px solid #333;")
        h_layout = QVBoxLayout(headers)
        h_layout.setContentsMargins(5, 5, 5, 5)
        h_layout.setSpacing(10)
        
        # We will assume each track is 40px high + spacing
        # For simplicity, just add some labels
        h_layout.addSpacing(20) # Time scale offset
        lbl_v = QLabel("V1")
        lbl_v.setFixedHeight(40)
        lbl_a = QLabel("A1")
        lbl_a.setFixedHeight(40)
        lbl_t = QLabel("T1")
        lbl_t.setFixedHeight(40)
        
        h_layout.addWidget(lbl_v)
        h_layout.addWidget(lbl_a)
        h_layout.addWidget(lbl_t)
        h_layout.addStretch(1)
        layout.addWidget(headers)

        # Scene and View
        self.scene = QGraphicsScene()
        # Scene coords
        self.scene.setSceneRect(0, 0, 2000, 220)
        
        self.view = TimelineView(self.scene)
        self.view.keyPressed.connect(self._handle_keypress)
        layout.addWidget(self.view, stretch=1)

        # Add dummy clips
        self._add_dummy_clips()

        # Playhead (Red line)
        self.playhead = QGraphicsRectItem(100, 0, 2, 220)
        self.playhead.setBrush(QBrush(QColor("red")))
        self.playhead.setPen(QPen(Qt.GlobalColor.transparent))
        self.playhead.setZValue(100) # Draw above clips
        self.scene.addItem(self.playhead)

    def _add_dummy_clips(self):
        # Video #1D4ED8
        # y positions for tracks: V1: 20-60, A1: 70-110, T1: 120-160
        v_clip = ClipItem(50, 20, 300, 40, "#1D4ED8", "Video_001.mp4")
        self.scene.addItem(v_clip)

        # Audio #15803D
        a_clip = ClipItem(50, 70, 300, 40, "#15803D", "Audio_001.wav")
        self.scene.addItem(a_clip)

        # Text #6D28D9
        t_clip = ClipItem(100, 120, 150, 40, "#6D28D9", "Title Text")
        self.scene.addItem(t_clip)

    def _handle_keypress(self, event):
        key = event.key()
        if key == Qt.Key.Key_S:
            print("Action: Split At Playhead")
        elif key == Qt.Key.Key_Delete or key == Qt.Key.Key_Backspace:
            print("Action: Delete Selected")
            for item in self.scene.selectedItems():
                self.scene.removeItem(item)
        elif key == Qt.Key.Key_Space:
            print("Action: Play/Pause")
        elif key == Qt.Key.Key_J:
            print("Action: Rewind")
        elif key == Qt.Key.Key_K:
            print("Action: Pause")
        elif key == Qt.Key.Key_L:
            print("Action: Fast Forward")
