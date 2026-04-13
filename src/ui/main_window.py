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
from ui.browser_panel import BrowserPanel

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from browser.lightpanda_manager import LightpandaManager

class LightpandaBootWorker(QThread):
    finished = pyqtSignal()
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    def run(self):
        self.manager.start()
        self.finished.emit()

class FramePlayer(QThread):
    frame_ready = pyqtSignal(QImage)
    timecode_update = pyqtSignal(str)
    playback_ended = pyqtSignal()
    
    def __init__(self, timeline, fps: int = 30):
        super().__init__()
        self.timeline = timeline
        self.fps = fps
        self.current_frame = 1
        self._playing = False
        self._stop_flag = False
    
    def play(self):  self._playing = True
    def pause(self): self._playing = False
    def stop(self):  self._stop_flag = True
    def seek(self, frame_num: int):
        self.current_frame = max(1, frame_num)
        self._emit_current_frame()
    
    def _emit_current_frame(self):
        try:
            frame = self.timeline.GetFrame(self.current_frame)
            img_data = bytes(frame.GetImage().data)
            w, h = frame.GetWidth(), frame.GetHeight()
            qimg = QImage(img_data, w, h, w * 3, QImage.Format.Format_RGB888)
            self.frame_ready.emit(qimg.copy())
            self.timecode_update.emit(self._format_tc(self.current_frame))
        except Exception as e:
            print(f"[Preview] Frame error: {e}")
    
    def _format_tc(self, frame: int) -> str:
        total_s = frame / self.fps
        h = int(total_s // 3600)
        m = int((total_s % 3600) // 60)
        s = int(total_s % 60)
        f = frame % self.fps
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"
    
    def run(self):
        import time
        interval = 1.0 / self.fps
        while not self._stop_flag:
            if self._playing:
                self._emit_current_frame()
                self.current_frame += 1
                total = int(self.timeline.Duration() * self.fps) if hasattr(self.timeline, 'Duration') else 300
                if self.current_frame > total:
                    self._playing = False
                    self.current_frame = 1
                    self.playback_ended.emit()
                time.sleep(interval)
            else:
                time.sleep(0.033)


class DummyProject:
    def __init__(self):
        from core.openshot_bridge import openshot
        self.timeline = openshot.Timeline(1920, 1080, openshot.Fraction(30, 1), 30, 44100, 2)
        
    def get_duration(self):
        return 10.0

    def initialize(self):
        self.timeline.Open()
        
    def add_clip(self, path, track, pos):
        return "mock_clip_id_1"

    def move_clip(self, cid, pos): pass
    def trim_clip(self, cid, start, end): pass
    def remove_clip(self, cid): pass


class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10)
        
        # Title
        title_lbl = QLabel("CLIP PROPERTIES")
        title_lbl.setStyleSheet("color: #7C3AED; font-weight: bold; font-size: 14px;")
        self.layout.addWidget(title_lbl)
        
        # Info Box
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        self.file_lbl = QLabel("File: --")
        self.file_lbl.setStyleSheet("color: #888888;")
        self.dur_lbl = QLabel("Duration: 0.0s")
        self.pos_lbl = QLabel("Position: 0.0s")
        self.track_lbl = QLabel("Track: Auto")
        info_layout.addWidget(self.file_lbl)
        info_layout.addWidget(self.dur_lbl)
        info_layout.addWidget(self.pos_lbl)
        info_layout.addWidget(self.track_lbl)
        self.layout.addWidget(info_frame)
        
        from PyQt6.QtWidgets import QSlider
        # Transform
        self.layout.addWidget(QLabel("Scale:"))
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(10, 200)
        self.scale_slider.setValue(100)
        self.layout.addWidget(self.scale_slider)
        
        self.layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.layout.addWidget(self.opacity_slider)
        
        # Trim
        self.layout.addWidget(QLabel("Trim:"))
        trim_lay = QHBoxLayout()
        self.start_input = QLineEdit("0.0s")
        self.end_input = QLineEdit("0.0s")
        trim_lay.addWidget(QLabel("Start:"))
        trim_lay.addWidget(self.start_input)
        trim_lay.addWidget(QLabel("End:"))
        trim_lay.addWidget(self.end_input)
        self.layout.addLayout(trim_lay)
        
        # Speed
        self.layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 400) # 0.25x to 4.0x
        self.speed_slider.setValue(100)
        self.layout.addWidget(self.speed_slider)

        self.layout.addStretch(1)

    def set_data(self, clip_item):
        path = getattr(clip_item, 'file_path', '')
        name = path.split('/')[-1].split('\\')[-1]
        if len(name) > 25: name = name[:22] + "..."
        self.file_lbl.setText(f"File: {name}")
        
        dur = getattr(clip_item, 'duration', 0.0)
        self.dur_lbl.setText(f"Duration: {dur:.1f}s")
        
        pos = clip_item.x() / 10.0
        self.pos_lbl.setText(f"Position: {pos:.1f}s")
        
        self.start_input.setText("0.0s")
        self.end_input.setText(f"{dur:.1f}s")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DMT Video Editor")
        self.resize(1440, 900)

        # Allow docks to be nested and animated
        self.setDockOptions(QMainWindow.DockOption.AnimatedDocks | QMainWindow.DockOption.AllowNestedDocks)

        self.project = DummyProject()
        self.project.initialize()

        from PyQt6.QtGui import QUndoStack
        self.undo_stack = QUndoStack(self)

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
        browser_btn = QPushButton("🌐 Browser")
        browser_btn.clicked.connect(self._show_browser)
        undo_btn = QPushButton("Undo")
        redo_btn = QPushButton("Redo")
        export_btn = QPushButton("Export")
        export_btn.setObjectName("ExportButton")
        export_btn.clicked.connect(self._show_export_dialog)
        
        undo_btn.clicked.connect(self.undo_stack.undo)
        redo_btn.clicked.connect(self.undo_stack.redo)
        undo_btn.setEnabled(False)
        redo_btn.setEnabled(False)
        self.undo_stack.canUndoChanged.connect(undo_btn.setEnabled)
        self.undo_stack.canRedoChanged.connect(redo_btn.setEnabled)
        
        layout.addWidget(browser_btn)
        layout.addWidget(undo_btn)
        layout.addWidget(redo_btn)
        layout.addWidget(export_btn)
        
        return toolbar

    def _show_browser(self):
        # Switch tabs to browser
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Browser":
                self.tabs.setCurrentIndex(i)
                if hasattr(self, 'browser_panel'):
                    self.browser_panel.url_bar.setFocus()
                break

    def _init_left_panel(self):
        left_dock = QDockWidget("Media Pool", self)
        left_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        # Force 240px roughly
        left_dock.setMinimumWidth(240)
        left_dock.setMaximumWidth(300)

        # Tabs
        self.tabs = QTabWidget()
        for tab_name in ["Media", "Templates", "Text", "Audio", "Browser"]:
            tab_content = QWidget()
            tab_layout = QVBoxLayout(tab_content)
            if tab_name == "Media":
                tab_layout.setContentsMargins(0,0,0,0)
                self.media_pool = MediaPoolWidget()
                tab_layout.addWidget(self.media_pool)
            elif tab_name == "Templates":
                tab_layout.setContentsMargins(0,0,0,0)
                templates_pool = TemplatesPanel()
                tab_layout.addWidget(templates_pool)
            elif tab_name == "Browser":
                tab_layout.setContentsMargins(0,0,0,0)
                self.browser_panel = BrowserPanel()
                self.browser_panel.mediaAdded.connect(self.media_pool._add_media_item)
                tab_layout.addWidget(self.browser_panel)
            else:
                lbl = QLabel(f"{tab_name} Panel")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                tab_layout.addWidget(lbl)
            self.tabs.addTab(tab_content, tab_name)

        left_dock.setWidget(self.tabs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
        
        # Start Lightpanda background connection
        self.lightpanda = LightpandaManager()
        self.browser_panel.manager = self.lightpanda
        self.browser_panel.stack.setCurrentWidget(self.browser_panel.loading_widget)
        
        self.lp_worker = LightpandaBootWorker(self.lightpanda)
        self.lp_worker.finished.connect(lambda: self.browser_panel.stack.setCurrentWidget(self.browser_panel.browser_widget))
        self.lp_worker.start()

    def _init_center_preview(self):
        center_widget = QWidget()
        layout = QVBoxLayout(center_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Preview Area
        self.preview_label = QLabel("Video Preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #000000; border-radius: 8px;")
        layout.addWidget(self.preview_label, stretch=1)
        
        # Controls
        controls_layout = QHBoxLayout()
        quality_cb = QComboBox()
        quality_cb.addItems(["Full", "Half", "Quarter"])
        controls_layout.addWidget(quality_cb)
        
        controls_layout.addStretch(1)
        
        from PyQt6.QtWidgets import QSlider
        self.scrubber = QSlider(Qt.Orientation.Horizontal)
        self.scrubber.setMinimumWidth(150)
        self.scrubber.setRange(1, int(self.project.get_duration() * 30))
        controls_layout.addWidget(self.scrubber)
        
        controls_layout.addSpacing(10)
        
        self.play_btn = QPushButton("▶ Play")
        controls_layout.addWidget(self.play_btn)
        
        controls_layout.addStretch(1)
        self.timecode_label = QLabel("00:00:00:00")
        controls_layout.addWidget(self.timecode_label)
        
        layout.addLayout(controls_layout)
        self.setCentralWidget(center_widget)

        self.player = FramePlayer(self.project.timeline, fps=30)
        self.player.frame_ready.connect(
            lambda img: self.preview_label.setPixmap(
                QPixmap.fromImage(img).scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        )
        self.player.timecode_update.connect(self.timecode_label.setText)
        
        def toggle_play():
            if self.player._playing:
                self.player.pause()
                self.play_btn.setText("▶ Play")
            else:
                self.player.play()
                self.play_btn.setText("⏸ Pause")
                
        self.play_btn.clicked.connect(toggle_play)
        self.scrubber.valueChanged.connect(self.player.seek)
        
        self.player.start()

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
                self.color_grading_panel = ColorGradingPanel()
                self.color_grading_panel.gradeChanged.connect(self._apply_grade_to_clip)
                tabs.addTab(self.color_grading_panel, tab_name)
            elif tab_name == "Properties":
                self.properties_panel = PropertiesPanel()
                tabs.addTab(self.properties_panel, tab_name)
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
        
        self.timeline_widget = TimelineWidget()
        self.timeline_widget.clip_selected_signal.connect(self._on_clip_selected)
        timeline_dock.setWidget(self.timeline_widget)
        
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, timeline_dock)

    def _show_export_dialog(self):
        dialog = ExportDialog(self)
        dialog.exec()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.play_btn.click()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if hasattr(self, 'player'):
            self.player.stop()
            self.player.wait()
        if hasattr(self, 'lightpanda'):
            self.lightpanda.stop()
        super().closeEvent(event)

    def _on_clip_selected(self, clip_id, clip_item):
        self.selected_clip_id = clip_id
        self.selected_clip_item = clip_item
        if hasattr(self, 'properties_panel'):
            self.properties_panel.set_data(clip_item)

    def _apply_grade_to_clip(self, grade: dict):
        if not hasattr(self, "selected_clip_id") or not self.selected_clip_id:
            return
            
        clip_id = self.selected_clip_id
        if not hasattr(self, "project") or not hasattr(self.project, "clips"):
            return
            
        clip_data = self.project.clips.get(clip_id)
        if not clip_data: return
        
        clip = clip_data[0]
        from core.openshot_bridge import openshot
        
        # Brightness (-100/100 -> 0.0/2.0)
        brightness_val = 1.0 + (grade.get("exposure", 0) / 100.0)
        clip.brightness = openshot.Keyframe(brightness_val)
        
        # Contrast (-100/100 -> 0.0/2.0)
        contrast_val = 1.0 + (grade.get("contrast", 0) / 100.0)
        clip.contrast = openshot.Keyframe(contrast_val)
        
        # Saturation (0/200 -> 0.0/2.0)
        sat_val = grade.get("saturation", 100) / 100.0
        clip.saturation = openshot.Keyframe(sat_val)
        
        # Hue (-100/100 -> -0.5/0.5)
        hue_val = grade.get("temperature", 0) / 200.0
        clip.hue = openshot.Keyframe(hue_val)
        
        if "lut_path" in grade:
            self.selected_clip_item.setData(Qt.ItemDataRole.UserRole + 2, grade)
            
        # Re-render step
        if hasattr(self, "player") and hasattr(self.player, "current_frame"):
            self.player.seek(self.player.current_frame)
