from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QProgressBar, QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Video")
        self.setFixedSize(400, 300)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # File Name
        fname_layout = QHBoxLayout()
        fname_layout.addWidget(QLabel("File Name:"))
        self.filename_input = QLineEdit("My_Video")
        fname_layout.addWidget(self.filename_input)
        layout.addLayout(fname_layout)

        # Preset Selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "YouTube 1080p (1920x1080 H.264 8Mbps AAC 320k)",
            "YouTube 4K (3840x2160)",
            "TikTok 9:16 (1080x1920 H.264 6Mbps)",
            "Twitter 720p",
            "Discord (Under 8MB/25MB)",
            "Custom"
        ])
        preset_layout.addWidget(self.preset_combo)
        layout.addLayout(preset_layout)

        # Save Location
        loc_layout = QHBoxLayout()
        self.loc_input = QLineEdit("C:/Videos/Exports")
        self.loc_input.setReadOnly(True)
        loc_btn = QPushButton("...")
        loc_btn.setFixedWidth(40)
        loc_btn.clicked.connect(self._select_folder)
        loc_layout.addWidget(QLabel("Save To:"))
        loc_layout.addWidget(self.loc_input)
        loc_layout.addWidget(loc_btn)
        layout.addLayout(loc_layout)

        layout.addStretch(1)

        # Progress
        self.progress_label = QLabel("Ready to export")
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Actions
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("ExportButton")  # Use the violet style
        self.export_btn.clicked.connect(self._start_export)
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.setVisible(False)
        self.open_folder_btn.clicked.connect(lambda: print("Opening folder..."))
        layout.addWidget(self.open_folder_btn)

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if folder:
            self.loc_input.setText(folder)

    def _start_export(self):
        self.export_btn.setEnabled(False)
        self.progress_label.setText("Exporting... ETA: calculating")
        self.progress_bar.setRange(0, 0) # Indeterminate state block
        # Actual export logic should connect to openshot FFmpegWriter here
        # E.g. trigger an external QThread
