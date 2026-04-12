"""
OpenShot Mock — fallback when real bindings aren't available.
Provides stub classes matching the openshot C++ SWIG API so the
DMT editor UI can run without the real engine installed.
"""

class Fraction:
    def __init__(self, num=30, den=1):
        self.num = num
        self.den = den


class _Version:
    def ToString(self):
        return "MOCK-0.0.0"


def GetVersion():
    return _Version()


class Timeline:
    def __init__(self, width=1920, height=1080, fps=None, *args, **kwargs):
        self.width = width
        self.height = height
        self._clips = []
        self._is_open = False

    def Open(self):
        self._is_open = True

    def Close(self):
        self._is_open = False

    def AddClip(self, clip):
        self._clips.append(clip)

    def RemoveClip(self, clip):
        self._clips.remove(clip)

    def ClearAllCache(self):
        pass

    def GetFrame(self, frame_number):
        return Frame()

    def SetMaxSize(self, w, h):
        pass


class Clip:
    def __init__(self, path=""):
        self.path = path
        self._position = 0.0
        self._layer = 0
        self._start = 0.0
        self._end = 0.0

    def Position(self, pos=None):
        if pos is not None:
            self._position = pos
        return self._position

    def Layer(self, layer=None):
        if layer is not None:
            self._layer = layer
        return self._layer

    def Start(self, start=None):
        if start is not None:
            self._start = start
        return self._start

    def End(self, end=None):
        if end is not None:
            self._end = end
        return self._end

    def Reader(self):
        return FFmpegReader(self.path)


class FFmpegReader:
    def __init__(self, path=""):
        self.path = path

    def Open(self):
        pass

    def Close(self):
        pass

    def GetFrame(self, frame_number):
        return Frame()


class FFmpegWriter:
    def __init__(self, path=""):
        self.path = path

    def Open(self):
        pass

    def Close(self):
        pass

    def WriteFrame(self, frame):
        pass

    def SetAudioOptions(self, *args, **kwargs):
        pass

    def SetVideoOptions(self, *args, **kwargs):
        pass


class Frame:
    def __init__(self):
        self.number = 0

    def Save(self, path, scale=1.0):
        pass

    def GetWidth(self):
        return 1920

    def GetHeight(self):
        return 1080


class Keyframe:
    def __init__(self, value=0.0):
        self.value = value

    def AddPoint(self, *args):
        pass

    def GetValue(self, frame):
        return self.value


class Color:
    def __init__(self, r=0, g=0, b=0, a=255):
        self.red = Keyframe(r)
        self.green = Keyframe(g)
        self.blue = Keyframe(b)
        self.alpha = Keyframe(a)
