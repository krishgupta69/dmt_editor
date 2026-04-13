import os
import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QThread
from PyQt6.QtWebEngineWidgets import QWebEngineView

class MediaFinderWorker(QThread):
    finished = pyqtSignal(list)
    def __init__(self, manager, url):
        super().__init__()
        self.manager = manager
        self.url = url
    def run(self):
        try:
            urls = self.manager.find_media_urls(self.url)
            self.finished.emit(urls)
        except:
            self.finished.emit([])

class DownloadMediaWorker(QThread):
    finished = pyqtSignal(str)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "media"))
            os.makedirs(assets_dir, exist_ok=True)
            safe_name = self.url.split('/')[-1]
            if '?' in safe_name: safe_name = safe_name.split('?')[0]
            if not safe_name: safe_name = "downloaded_media.mp4"
            out_path = os.path.join(assets_dir, safe_name)
            
            with requests.get(self.url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(out_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            self.finished.emit(out_path)
        except Exception as e:
            self.finished.emit("")

class BrowserPanel(QWidget):
    mediaAdded = pyqtSignal(str) # Emits the filepath of the downloaded media

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = None
        self.media_urls = []
        self._init_ui()

    def _init_ui(self):
        self.stack = QStackedWidget(self)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)
        
        # Loading view
        self.loading_widget = QWidget()
        l_layout = QVBoxLayout(self.loading_widget)
        self.loading_lbl = QLabel("🌐 Starting Browser...\n(Downloading Lightpanda binary if missing)")
        self.loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_layout.addWidget(self.loading_lbl)
        
        # Browser view
        self.browser_widget = QWidget()
        b_layout = QVBoxLayout(self.browser_widget)
        b_layout.setContentsMargins(5, 5, 5, 5)
        b_layout.setSpacing(5)
        
        # Row 1
        r1 = QHBoxLayout()
        self.btn_back = QPushButton("◀")
        self.btn_fwd = QPushButton("▶")
        self.btn_ref = QPushButton("⟳")
        self.btn_back.setFixedWidth(30)
        self.btn_fwd.setFixedWidth(30)
        self.btn_ref.setFixedWidth(30)
        
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self._on_go)
        
        self.btn_go = QPushButton("GO")
        self.btn_go.clicked.connect(self._on_go)
        
        r1.addWidget(self.btn_back)
        r1.addWidget(self.btn_fwd)
        r1.addWidget(self.btn_ref)
        r1.addWidget(self.url_bar)
        r1.addWidget(self.btn_go)
        b_layout.addLayout(r1)
        
        # Row 2
        self.web_view = QWebEngineView()
        b_layout.addWidget(self.web_view, stretch=1)
        
        self.btn_back.clicked.connect(self.web_view.back)
        self.btn_fwd.clicked.connect(self.web_view.forward)
        self.btn_ref.clicked.connect(self.web_view.reload)
        self.web_view.urlChanged.connect(lambda u: self.url_bar.setText(u.toString()))
        
        # Row 3
        r3 = QHBoxLayout()
        quick_links = [
            ("🎵 Free Music", "https://freemusicarchive.org"),
            ("🎬 Stock Video", "https://www.pexels.com/videos"),
            ("📸 Photos", "https://www.pexels.com"),
            ("✨ Effects", "https://mixkit.co/free-video-effects")
        ]
        for name, link in quick_links:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, l=link: self._quick_link(l))
            r3.addWidget(btn)
        b_layout.addLayout(r3)
        
        # Row 4
        self.row4_widget = QWidget()
        r4 = QHBoxLayout(self.row4_widget)
        r4.setContentsMargins(0, 0, 0, 0)
        self.media_lbl = QLabel("")
        self.add_media_btn = QPushButton("+ Add to Project")
        self.add_media_btn.setObjectName("ExportButton")
        self.add_media_btn.clicked.connect(self._add_to_project)
        r4.addWidget(self.media_lbl)
        r4.addWidget(self.add_media_btn)
        self.row4_widget.hide()
        
        b_layout.addWidget(self.row4_widget)
        
        self.stack.addWidget(self.loading_widget)
        self.stack.addWidget(self.browser_widget)
        
    def _quick_link(self, url):
        self.url_bar.setText(url)
        self._on_go()
        
    def _on_go(self):
        url = self.url_bar.text().strip()
        if not url: return
        if not url.startswith("http"): url = "http://" + url
        
        self.row4_widget.hide()
        self.web_view.setUrl(QUrl(url))
        
        if self.manager and self.manager.is_running():
            self.finder = MediaFinderWorker(self.manager, url)
            self.finder.finished.connect(self._on_media_found)
            self.finder.start()
            
    def _on_media_found(self, urls):
        self.media_urls = urls
        if urls:
            first = urls[0]
            name = first.get("name", "Unknown Media")
            self.media_lbl.setText(f"Found: {name}")
            self.row4_widget.show()
            
    def _add_to_project(self):
        if not self.media_urls: return
        target_url = self.media_urls[0].get("url")
        if not target_url: return
        
        self.add_media_btn.setEnabled(False)
        self.add_media_btn.setText("Downloading...")
        
        self.downloader = DownloadMediaWorker(target_url)
        self.downloader.finished.connect(self._on_downloaded)
        self.downloader.start()
        
    def _on_downloaded(self, path):
        self.add_media_btn.setEnabled(True)
        self.add_media_btn.setText("+ Add to Project")
        if path:
            QMessageBox.information(self, "Success", "Added to Media Pool ✓")
            self.mediaAdded.emit(path)
        else:
            QMessageBox.critical(self, "Error", "Failed to download media")
