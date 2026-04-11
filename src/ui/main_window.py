from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QDockWidget, 
    QTabWidget, QFrame, QScrollArea, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from ui.media_pool import MediaPoolWidget
from ui.timeline import TimelineWidget
from ui.export_dialog import ExportDialog
from ui.templates_panel import TemplatesPanel
from ui.color_grading_panel import ColorGradingPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DMT Video Editor")
        self.resize(1440, 900)

        # Allow docks to be nested and animated
        self.setDockOptions(QMainWindow.DockOption.AnimatedDocks | QMainWindow.DockOption.AllowNestedDocks)

        self._init_ui()

    def _init_ui(self):
        # 1. Top Toolbar (using MenuWidget space for full horizontal span)
        toolbar = self._create_top_toolbar()
        self.setMenuWidget(toolbar)

        # 2. Constraints for Dock Widgets
        self.setCorner(Qt.Corner.TopLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.BottomLeftCorner, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setCorner(Qt.Corner.TopRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)
        self.setCorner(Qt.Corner.BottomRightCorner, Qt.DockWidgetArea.RightDockWidgetArea)

        # 3. Create Left Panel (240px)
        self._init_left_panel()

        # 4. Create Center Preview
        self._init_center_preview()

        # 5. Create Right Panel (280px)
        self._init_right_panel()

        # 6. Create Timeline (220px tall)
        self._init_timeline()

    def _create_top_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setObjectName("TopToolbar")
        toolbar.setFixedHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 0, 20, 0)

        logo_label = QLabel("DMT")
        logo_label.setStyleSheet("color: #7C3AED; font-size: 24px; font-weight: bold; border: none;")
        layout.addWidget(logo_label)

        layout.addStretch(1)

        project_name = QLineEdit("Untitled Project")
        project_name.setFixedWidth(200)
        project_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(project_name)

        layout.addStretch(1)

        # Shortcuts: Ctrl+Z
        undo_btn = QPushButton("Undo")
        redo_btn = QPushButton("Redo")
        export_btn = QPushButton("Export")
        export_btn.setObjectName("ExportButton")
        export_btn.clicked.connect(self._show_export_dialog)
        
        layout.addWidget(undo_btn)
        layout.addWidget(redo_btn)
        layout.addWidget(export_btn)
        
        return toolbar

    def _init_left_panel(self):
        left_dock = QDockWidget("Media Pool", self)
        left_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # Force 240px roughly
        left_dock.setMinimumWidth(240)
        left_dock.setMaximumWidth(300)

        # Tabs
        tabs = QTabWidget()
        for tab_name in ["Media", "Templates", "Text", "Audio", "Browser"]:
            tab_content = QWidget()
            tab_layout = QVBoxLayout(tab_content)
            if tab_name == "Media":
                layout_for_media = QVBoxLayout(tab_content)
                layout_for_media.setContentsMargins(0,0,0,0)
                media_pool = MediaPoolWidget()
                layout_for_media.addWidget(media_pool)
            elif tab_name == "Templates":
                layout_for_templates = QVBoxLayout(tab_content)
                layout_for_templates.setContentsMargins(0,0,0,0)
                templates_pool = TemplatesPanel()
                layout_for_templates.addWidget(templates_pool)
            else:
                layout_for_tab = QVBoxLayout(tab_content)
                lbl = QLabel(f"{tab_name} Panel")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout_for_tab.addWidget(lbl)
            tabs.addTab(tab_content, tab_name)

        left_dock.setWidget(tabs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)

    def _init_center_preview(self):
        center_widget = QWidget()
        layout = QVBoxLayout(center_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Preview Area
        preview_label = QLabel("Video Preview")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("background-color: #000000; border-radius: 8px;")
        layout.addWidget(preview_label, stretch=1)
        
        # Controls
        controls_layout = QHBoxLayout()
        quality_cb = QComboBox()
        quality_cb.addItems(["Full", "Half", "Quarter"])
        controls_layout.addWidget(quality_cb)
        
        controls_layout.addStretch(1)
        play_btn = QPushButton("Play / Pause")
        controls_layout.addWidget(play_btn)
        
        controls_layout.addStretch(1)
        timecode = QLabel("00:00:00:00")
        controls_layout.addWidget(timecode)
        
        layout.addLayout(controls_layout)
        self.setCentralWidget(center_widget)

    def _init_right_panel(self):
        right_dock = QDockWidget("Inspector", self)
        right_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        right_dock.setMinimumWidth(280)
        right_dock.setMaximumWidth(350)

        right_widget = QWidget()
        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tabs = QTabWidget()
        for tab_name in ["Properties", "Color Grade", "Effects", "Audio"]:
            if tab_name == "Color Grade":
                color_panel = ColorGradingPanel()
                tabs.addTab(color_panel, tab_name)
            else:
                tab_content = QWidget()
                tab_layout = QVBoxLayout(tab_content)
                lbl = QLabel(f"{tab_name} Settings")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                tab_layout.addWidget(lbl)
                tabs.addTab(tab_content, tab_name)
        
        layout.addWidget(tabs, stretch=1)
        
        # Download button pinned at very bottom
        download_btn = QPushButton("Download")
        download_btn.setFixedHeight(40)
        download_btn.setObjectName("ExportButton") # Reuse purple style
        layout.addWidget(download_btn)
        
        right_dock.setWidget(right_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, right_dock)

    def _init_timeline(self):
        timeline_dock = QDockWidget("Timeline", self)
        timeline_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        
        timeline_widget = TimelineWidget()
        timeline_dock.setWidget(timeline_widget)
        
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, timeline_dock)

    def _show_export_dialog(self):
        dialog = ExportDialog(self)
        dialog.exec()
