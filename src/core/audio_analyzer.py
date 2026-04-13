import librosa, numpy as np
from dataclasses import dataclass
from PyQt6.QtCore import QThread, pyqtSignal

@dataclass
class AudioAnalysis:
    file_path: str
    duration: float
    tempo: float
    beat_times: list
    onset_times: list
    waveform: list   # 1000 normalized floats 0.0-1.0

class AudioAnalyzeWorker(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            y, sr = librosa.load(self.file_path, sr=None, mono=True)
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()
            chunk = max(1, len(y) // 1000)
            raw = [float(np.max(np.abs(y[i:i+chunk])))
                   for i in range(0, len(y) - chunk, chunk)][:1000]
            peak = max(raw) if raw else 1.0
            waveform = [v / peak for v in raw]
            self.finished.emit(AudioAnalysis(
                file_path=self.file_path,
                duration=float(len(y) / sr),
                tempo=float(tempo),
                beat_times=beat_times,
                onset_times=onset_times,
                waveform=waveform
            ))
        except Exception as e:
            self.error.emit(str(e))
