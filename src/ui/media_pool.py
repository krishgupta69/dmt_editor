from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
    QAbstractItemView, QLabel, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QMimeData
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
import json

import os

class ThumbnailGenerator(QThread):
    finished = pyqtSignal(str, QPixmap)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        ext = os.path.splitext(self.file_path)[1].lower()
        pixmap = QPixmap(120, 68)

        try:
            if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                try:
                    from core.openshot_bridge import openshot
                    reader = openshot.FFmpegReader(self.file_path)
                    reader.Open()
                    frame = reader.GetFrame(1)
                    import tempfile
                    tmp = tempfile.mktemp(suffix=".png")
                    frame.Save(tmp, 1.0)
                    pixmap = QPixmap(tmp).scaled(
                        120, 68, 
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    if os.path.exists(tmp):
                        os.remove(tmp)
                    reader.Close()
                except Exception as e:
                    pixmap.fill(Qt.GlobalColor.darkGray)
                    painter = QPainter(pixmap)
                    painter.setPen(QColor("white"))
                    font = QFont()
                    font.setPixelSize(24)
                    painter.setFont(font)
                    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🎬")
                    painter.end()

            elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
                pixmap = QPixmap(self.file_path).scaled(
                    120, 68, 
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )

            elif ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg']:
                pixmap.fill(QColor("#15803D"))
                painter = QPainter(pixmap)
                painter.setPen(QColor("white"))
                font = QFont()
                font.setPixelSize(32)
                painter.setFont(font)
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "♪")
                painter.end()

            else:
                pixmap.fill(Qt.GlobalColor.darkGray)

        except Exception as e:
            pixmap.fill(Qt.GlobalColor.darkGray)
            print(f"Error generating thumbnail for {self.file_path}: {e}")

        self.finished.emit(self.file_path, pixmap)

class MediaListWidget(QListWidget):
    def mimeData(self, items):
        mime = QMimeData()
        if not items:
            return mime
        item = items[0]
        mime.setData("application/dmt-media", 
            json.dumps({"file_path": item.file_path, 
                        "duration": item.duration,
                        "type": item.media_type}).encode())
        mime.setText(item.file_path)
        return mime

class MediaPoolWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.supported_formats = ['.mp4', '.mov', '.avi', '.mkv', '.mp3', '.wav', '.png', '.jpg']

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Import Button
        self.import_btn = QPushButton("Import Media")
        self.import_btn.clicked.connect(self._import_media)
        layout.addWidget(self.import_btn)

        # Grid view using MediaListWidget in IconMode
        self.list_widget = MediaListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(120, 68))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.list_widget.setDefaultDropAction(Qt.DropAction.CopyAction)
        
        # Approximate 2-column layout width based on dock widget size
        self.list_widget.setMinimumWidth(220)

        layout.addWidget(self.list_widget)

    def _import_media(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Import Media", "", "Media Files (*.mp4 *.mov *.avi *.mkv *.mp3 *.wav *.png *.jpg)"
        )
        for filepath in file_paths:
            self._add_media_item(filepath)

    def _add_media_item(self, filepath):
        name = os.path.basename(filepath)
        item = QListWidgetItem(name)
        # Store filepath in user role for dragging
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        item.file_path = filepath
        
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            item.media_type = 'video'
        elif ext in ['.mp3', '.wav', '.aac', '.flac', '.ogg']:
            item.media_type = 'audio'
        else:
            item.media_type = 'text' if ext in ['.txt'] else 'image'
            
        item.duration = 5.0 # mock duration
        
        # Start thumbnail thread
        thread = ThumbnailGenerator(filepath)
        thread.finished.connect(lambda p, pix, t=thread: self._on_thumbnail_ready(item, pix, t))
        # Keep reference to prevent GC
        if not hasattr(self, '_workers'):
            self._workers = []
        self._workers.append(thread)
        thread.start()

        self.list_widget.addItem(item)

    def _on_thumbnail_ready(self, item, pixmap, thread):
        icon = QIcon(pixmap)
        item.setIcon(icon)
        if thread in self._workers:
            thread.wait()
            self._workers.remove(thread)
