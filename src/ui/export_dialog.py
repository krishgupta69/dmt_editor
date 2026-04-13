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
        self.open_folder_btn.clicked.connect(self._open_folder)
        layout.addWidget(self.open_folder_btn)

    def _open_folder(self):
        import subprocess, os, sys
        folder = self.loc_input.text()
        filename = self.filename_input.text()
        if not filename.endswith(".mp4"):
            filename += ".mp4"
        path = os.path.join(folder, filename)
        
        if sys.platform == 'win32':
            subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if folder:
            self.loc_input.setText(folder)

    def _start_export(self):
        from core.export_worker import ExportWorker
        from PyQt6.QtWidgets import QMessageBox
        import os
        
        self.export_btn.setEnabled(False)
        self.progress_label.setText("Exporting...")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        preset_map = {
            "YouTube 1080p (1920x1080 H.264 8Mbps AAC 320k)": "YouTube 1080p",
            "YouTube 4K (3840x2160)": "YouTube 4K",
            "TikTok 9:16 (1080x1920 H.264 6Mbps)": "TikTok / Reels",
            "Twitter 720p": "Twitter / X",
            "Discord (Under 8MB/25MB)": "Discord",
            "Custom": "Custom"
        }
        
        preset = preset_map.get(self.preset_combo.currentText(), "YouTube 1080p")
        
        folder = self.loc_input.text()
        filename = self.filename_input.text()
        if not filename.endswith(".mp4"):
            filename += ".mp4"
        path = os.path.join(folder, filename)
        
        main_win = self.window()
        if not hasattr(main_win, "project") or not main_win.project:
            QMessageBox.critical(self, "Error", "Project not initialized")
            self.export_btn.setEnabled(True)
            return
            
        self.worker = ExportWorker(main_win.project.timeline, path, preset)
        self.worker.progress.connect(self.progress_bar.setValue)
        
        def on_finished(p):
            self.progress_bar.setValue(100)
            self.progress_label.setText("✅ Export complete!")
            self.open_folder_btn.setVisible(True)
            self.export_btn.setEnabled(True)
            
        def on_error(msg):
            QMessageBox.critical(self, "Export Failed", msg)
            self.progress_bar.setValue(0)
            self.export_btn.setEnabled(True)
            
        self.worker.finished.connect(on_finished)
        self.worker.error.connect(on_error)
        
        # Override cancel button to actually stop FFmpeg generator
        self.cancel_btn.clicked.disconnect()
        def cancel_export():
            if hasattr(self, 'worker'):
                self.worker.cancel()
                self.progress_label.setText("Export Cancelled.")
                self.export_btn.setEnabled(True)
                self.cancel_btn.clicked.disconnect(cancel_export)
                self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.clicked.connect(cancel_export)
        
        self.worker.start()
