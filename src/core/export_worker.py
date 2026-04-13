from PyQt6.QtCore import QThread, pyqtSignal
from core.openshot_bridge import openshot

PRESETS = {
    "YouTube 1080p":  dict(w=1920,h=1080,fps=30,vc="libx264",vb=8000000, ac="aac",ab=320000),
    "YouTube 4K":     dict(w=3840,h=2160,fps=30,vc="libx265",vb=35000000,ac="aac",ab=320000),
    "TikTok / Reels": dict(w=1080,h=1920,fps=30,vc="libx264",vb=6000000, ac="aac",ab=192000),
    "Twitter / X":    dict(w=1280,h=720, fps=30,vc="libx264",vb=4000000, ac="aac",ab=192000),
    "Discord":        dict(w=1280,h=720, fps=30,vc="libx264",vb=3000000, ac="aac",ab=128000),
    "Custom":         dict(w=1920,h=1080,fps=30,vc="libx264",vb=8000000, ac="aac",ab=320000),
}

class ExportWorker(QThread):
    progress  = pyqtSignal(int)   # 0-100
    finished  = pyqtSignal(str)   # output path
    error     = pyqtSignal(str)
    
    def __init__(self, timeline, output_path: str, preset: str, custom: dict = None):
        super().__init__()
        self.timeline = timeline
        self.output_path = output_path
        self.s = custom if custom else PRESETS[preset]
        self._cancel = False
    
    def cancel(self): self._cancel = True
    
    def run(self):
        try:
            s = self.s
            total = int(self.timeline.Duration() * s["fps"])
            if total <= 0:
                self.error.emit("Timeline is empty. Add clips before exporting.")
                return
            
            w = openshot.FFmpegWriter(self.output_path)
            w.SetVideoOptions(True, s["vc"],
                openshot.Fraction(s["fps"], 1),
                s["w"], s["h"], openshot.Fraction(1,1),
                False, False, s["vb"])
            w.SetAudioOptions(True, s["ac"], 44100, 2,
                openshot.LAYOUT_STEREO, s["ab"])
            w.Open()
            
            for n in range(1, total + 1):
                if self._cancel: break
                w.WriteFrame(self.timeline.GetFrame(n))
                self.progress.emit(int(n / total * 100))
            
            w.Close()
            if not self._cancel:
                self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))
