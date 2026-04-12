# DMT Video Editor — Project Spec
Company: Don't Miss Tomorrow | Team: Krish & Tanmay

## What Is Built (Frontend — COMPLETE)
- PyQt6 QMainWindow CapCut-style layout, dark theme #0D0D0D, violet #7C3AED
- QGraphicsScene timeline with video/audio/text tracks
- 8 JSON templates + TemplateEngine parser + Gallery UI
- Color grading: debounced sliders, 3-way color wheels (QPainter),
  Catmull-Rom Bezier curves, LUT preset grid, 6 procedural .cube files
- All openshot references are currently MOCKED

## What Remains (Backend — TODO)
1. OpenShot Python bindings — replace mocks with real engine
2. Lightpanda CDP client — WebSocket connection ws://127.0.0.1:9222
3. Librosa audio engine — waveform parsing + beat detection

## Key Repos (do NOT clone these into the project)
- OpenShot bindings: ships with installer, path:
  C:\Program Files\OpenShot Video Editor\lib\_openshot.pyd
  NOTE: v3.5.1 .pyd is compiled for Python 3.8.
  System Python is 3.13 — ABI mismatch prevents loading.
  Bridge module (core/openshot_bridge.py) safely probes via
  subprocess and falls back to core/openshot_mock.py.
  To use real bindings: install Python 3.8 or build libopenshot
  from source for your Python version.
- Lightpanda: runs as separate service, 
  binary from https://github.com/lightpanda-io/browser/releases/latest
  CDP at ws://127.0.0.1:9222

## Stack
Python 3.11, PyQt6, openshot bindings, OpenColorIO,
librosa, websockets, PyInstaller
