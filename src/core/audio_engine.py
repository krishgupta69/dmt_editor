import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import librosa
except ImportError:
    librosa = None


class AudioAnalyzerThread(QThread):
    """
    Background worker to compute waveform envelope and beat times.
    """
    finished = pyqtSignal(str, dict)  # filepath, {"duration": float, "envelope": np.ndarray, "beats": list}
    error = pyqtSignal(str, str)      # filepath, error_message

    def __init__(self, filepath, num_points=1000):
        super().__init__()
        self.filepath = filepath
        self.num_points = num_points

    def run(self):
        if librosa is None:
            self.error.emit(self.filepath, "Librosa is not installed.")
            return

        try:
            # Load audio (downsampled to 22.05kHz for faster processing)
            y, sr = librosa.load(self.filepath, sr=22050)
            duration = librosa.get_duration(y=y, sr=sr)

            # 1. Waveform Envelope (Decimation for UI rendering)
            # We want roughly self.num_points in our envelope
            samples_per_pixel = max(1, len(y) // self.num_points)
            
            # Truncate array to make it divisible
            truncated_len = (len(y) // samples_per_pixel) * samples_per_pixel
            y_truncated = y[:truncated_len]
            
            if len(y_truncated) > 0:
                y_reshaped = y_truncated.reshape(-1, samples_per_pixel)
                # Calculate the max absolute value in each window chunk
                envelope = np.max(np.abs(y_reshaped), axis=1)
                
                # Normalize envelope to 0.0 - 1.0 for UI drawing
                if np.max(envelope) > 0:
                    envelope = envelope / np.max(envelope)
            else:
                envelope = np.zeros(self.num_points)

            # 2. Beat Detection (Onset detection)
            # onset_detect returns frame indices
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr, wait=1, pre_avg=1, post_avg=1, pre_max=1, post_max=1)
            # convert frames to time in seconds
            onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()

            data = {
                "duration": float(duration),
                "envelope": envelope.tolist(),  # Ensure JSON/pyqtsignal safe
                "beats": onset_times
            }
            self.finished.emit(self.filepath, data)

        except Exception as e:
            self.error.emit(self.filepath, str(e))
