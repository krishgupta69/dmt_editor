from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
    QAbstractItemView, QLabel, QPushButton, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

import os

class ThumbnailGenerator(QThread):
    finished = pyqtSignal(str, QPixmap)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        # Placeholder for actual thumbnail generation 
        # (e.g. using openshot or ffmpeg to extract a frame)
        pixmap = QPixmap(100, 60)
        pixmap.fill(Qt.GlobalColor.darkGray)
        self.finished.emit(self.file_path, pixmap)

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

        # Grid view using QListWidget in IconMode
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(100, 60))
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
        
        # Start thumbnail thread
        thread = ThumbnailGenerator(filepath)
        thread.finished.connect(lambda p, pix: self._on_thumbnail_ready(item, pix))
        # Keep reference to prevent GC
        if not hasattr(self, '_threads'):
            self._threads = []
        self._threads.append(thread)
        thread.start()

        self.list_widget.addItem(item)

    def _on_thumbnail_ready(self, item, pixmap):
        icon = QIcon(pixmap)
        item.setIcon(icon)
