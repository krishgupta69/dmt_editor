from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QBrush, QPen, QColor, QKeyEvent, QPainterPath, QPainter
import math
import random
import json
import os

class ClipItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height, color_hex, label, parent=None):
        super().__init__(x, y, width, height, parent)
        self.color_hex = color_hex
        self.setBrush(QBrush(QColor(color_hex)))
        self.setPen(QPen(Qt.GlobalColor.transparent))
        self.setFlags(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        
        self.text = QGraphicsTextItem(label, self)
        self.text.setDefaultTextColor(QColor("white"))
        font = self.text.font()
        font.setPixelSize(10)
        self.text.setFont(font)
        self.text.setPos(x + 5, y + ((height - 20) / 2))
        
        self.waveform = None
        self.beats = None

    def set_audio_data(self, envelope, beats):
        self.waveform = envelope
        self.beats = beats
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        # Base rounded rectangle
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(rect, 4, 4)
        
        analysis = self.data(Qt.ItemDataRole.UserRole + 1)
        if analysis and getattr(self, 'media_type', '') == "audio":
            wf = analysis.waveform  # 1000 pts
            w, h = rect.width(), rect.height()
            cx = rect.x()
            cy = rect.y() + h / 2
            step = w / len(wf)
            path = QPainterPath()
            path.moveTo(cx, cy)
            for i, v in enumerate(wf):
                x = cx + i * step
                path.lineTo(x, cy - v * (h / 2 - 4))
            for i in range(len(wf)-1, -1, -1):
                x = cx + i * step
                v = wf[i]
                path.lineTo(x, cy + v * (h / 2 - 4))
            path.closeSubpath()
            painter.fillPath(path, QColor(255, 255, 255, 80))
            
            painter.setPen(QPen(QColor(255, 255, 0, 180), 1))
            total_duration = max(0.1, analysis.duration)
            for b_time in analysis.beat_times:
                bx = cx + (b_time / total_duration) * w
                if cx <= bx <= cx + w:
                    painter.drawLine(int(bx), int(rect.top()), int(bx), int(rect.bottom()))

        elif self.waveform:
            # Fallback dummy
            path = QPainterPath()
            path.moveTo(rect.left(), rect.center().y())
            num_points = len(self.waveform)
            if num_points > 1:
                step = rect.width() / (num_points - 1)
                for i, val in enumerate(self.waveform):
                    x = rect.left() + i * step
                    y = rect.center().y() - (val * rect.height() / 2.2)
                    path.lineTo(x, y)
                for i, val in reversed(list(enumerate(self.waveform))):
                    x = rect.left() + i * step
                    y = rect.center().y() + (val * rect.height() / 2.2)
                    path.lineTo(x, y)
                path.closeSubpath()
                painter.setBrush(QColor(255, 255, 255, 100))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(path)
                
        if self.beats and not analysis:
            painter.setPen(QPen(QColor(255, 255, 0, 180), 1))
            for b in self.beats:
                bx = rect.left() + b * rect.width()
                painter.drawLine(int(bx), int(rect.top()), int(bx), int(rect.bottom()))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(QPen(QColor("white"), 2))
            else:
                self.setPen(QPen(Qt.GlobalColor.transparent))
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        scene = self.scene()
        if scene and scene.views():
            view = scene.views()[0]
            tw = view.parentWidget()
            clip_id = self.data(Qt.ItemDataRole.UserRole)
            if hasattr(tw, 'clip_selected_signal'):
                tw.clip_selected_signal.emit(clip_id, self)


class TimelineView(QGraphicsView):
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setStyleSheet("background-color: #0D0D0D; border: none;")
        self.setRenderHint(self.renderHints()) 
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/dmt-media"):
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/dmt-media"):
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasFormat("application/dmt-media"):
            data = json.loads(mime.data("application/dmt-media").data().decode())
            file_path = data.get("file_path", "")
            duration = data.get("duration", 5.0)
            media_type = data.get("type", "video")

            pos = self.mapToScene(event.position().toPoint())
            drop_x = pos.x()
            drop_y = pos.y()

            # Track positioning (approx)
            if drop_y < 60:
                track_idx = 0
                y_pos = 20
            elif drop_y < 110:
                track_idx = 1
                y_pos = 70
            else:
                track_idx = 2
                y_pos = 120

            # X position
            track_header_width = 80 # though view x() starts after header natively
            position_seconds = (drop_x) / 10.0 # roughly 10px/s

            name = os.path.basename(file_path)

            if media_type == "video":
                color_hex = "#1D4ED8"
                label = name[:12] + "..." if len(name) > 12 else name
            elif media_type == "audio":
                color_hex = "#15803D"
                label = name
            else:
                color_hex = "#6D28D9"
                label = "Text"

            width = max(duration * 10, 50)
            clip = ClipItem(drop_x, y_pos, width, 40, color_hex, label)
            clip.file_path = file_path
            clip.duration = duration
            clip.media_type = media_type

            if media_type == "audio":
                from core.audio_analyzer import AudioAnalyzeWorker
                worker = AudioAnalyzeWorker(file_path)
                if not hasattr(self, '_workers'):
                    self._workers = []
                self._workers.append(worker)
                
                def on_analysis_finished(analysis, w=worker, c=clip):
                    c.setData(Qt.ItemDataRole.UserRole + 1, analysis)
                    c.update()
                    if w in self._workers:
                        w.wait()
                        self._workers.remove(w)
                        
                worker.finished.connect(on_analysis_finished)
                worker.start()

            main_win = self.window()
            if hasattr(main_win, "project") and main_win.project:
                from core.commands import AddClipCommand
                cmd = AddClipCommand(main_win.project, self.parentWidget(), file_path, track_idx, position_seconds, clip)
                if hasattr(main_win, 'undo_stack'):
                    main_win.undo_stack.push(cmd)
                else:
                    cmd.redo()
            else:
                self.scene().addItem(clip)
            
            event.accept()
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)


from PyQt6.QtWidgets import QPushButton, QMessageBox

class FloatingToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setStyleSheet("background: #2D2D2D; border: 1px solid #555; border-radius: 4px;")
        
        self.beat_sync_btn = QPushButton("🥁 Beat Sync")
        self.beat_sync_btn.setStyleSheet("color: white; border: none; padding: 4px;")
        self.layout.addWidget(self.beat_sync_btn)
        
        self.active_clip = None
        self.hide()

class TimelineWidget(QWidget):
    clip_selected_signal = pyqtSignal(str, object)

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

        self.floating_toolbar = FloatingToolbar(self)
        self.floating_toolbar.beat_sync_btn.clicked.connect(self._on_beat_sync)
        self.clip_selected_signal.connect(self.update_floating_toolbar)

        # Add dummy clips
        self._add_dummy_clips()

        # Playhead (Red line)
        self.playhead = QGraphicsRectItem(100, 0, 2, 220)
        self.playhead.setBrush(QBrush(QColor("red")))
        self.playhead.setPen(QPen(Qt.GlobalColor.transparent))
        self.playhead.setZValue(100) # Draw above clips
        self.scene.addItem(self.playhead)
        
    def update_floating_toolbar(self, clip_id, clip_item):
        if getattr(clip_item, 'media_type', '') == "audio":
            self.floating_toolbar.active_clip = clip_item
            scene_pos = clip_item.scenePos()
            view_pos = self.view.mapFromScene(scene_pos)
            self.floating_toolbar.move(self.view.x() + int(view_pos.x()), max(self.view.y(), self.view.y() + int(view_pos.y()) - 40))
            self.floating_toolbar.show()
        else:
            self.floating_toolbar.hide()

    def _on_beat_sync(self):
        clip_item = self.floating_toolbar.active_clip
        if not clip_item: return
        analysis = clip_item.data(Qt.ItemDataRole.UserRole + 1)
        if not analysis:
            QMessageBox.information(self, "Beat Sync", "Analyzing audio... please wait.")
            return
            
        reply = QMessageBox.question(self, "Beat Sync",
            f"Detected {analysis.tempo:.0f} BPM.\nSnap video cuts to beats?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
        if reply == QMessageBox.StandardButton.Yes:
            main_win = self.window()
            for item in self.scene.items():
                if getattr(item, 'media_type', '') == "video":
                    nearest = min(analysis.beat_times, key=lambda t: abs(t - item.x() / 10.0))
                    new_x = nearest * 10.0
                    item.setX(new_x)
                    if hasattr(main_win, "project") and main_win.project:
                        cid = item.data(Qt.ItemDataRole.UserRole)
                        # the project should handle track logic
                        main_win.project.move_clip(cid, nearest)

    def _add_dummy_clips(self):
        # Video #1D4ED8
        v_clip = ClipItem(50, 20, 300, 40, "#1D4ED8", "Video_001.mp4")
        self.scene.addItem(v_clip)

        # Audio #15803D
        a_clip = ClipItem(50, 70, 300, 40, "#15803D", "Audio_001.wav")
        # generate dummy waveform
        dummy_env = [math.sin(i * 0.2) * math.sin(i * 0.05) * 0.8 + 0.2 for i in range(100)]
        dummy_env = [abs(x) for x in dummy_env]
        dummy_beats = [0.1, 0.35, 0.6, 0.85]
        a_clip.set_audio_data(dummy_env, dummy_beats)
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
            main_win = self.window()
            for item in self.scene.selectedItems():
                clip_id = item.data(Qt.ItemDataRole.UserRole)
                if clip_id and hasattr(main_win, "project") and main_win.project:
                    from core.commands import RemoveClipCommand
                    cmd = RemoveClipCommand(main_win.project, self, clip_id, item)
                    if hasattr(main_win, 'undo_stack'):
                        main_win.undo_stack.push(cmd)
                    else:
                        cmd.redo()
                else:
                    self.scene.removeItem(item)
        elif key == Qt.Key.Key_Space:
            print("Action: Play/Pause")
        elif key == Qt.Key.Key_J:
            print("Action: Rewind")
        elif key == Qt.Key.Key_K:
            print("Action: Pause")
        elif key == Qt.Key.Key_L:
            print("Action: Fast Forward")
