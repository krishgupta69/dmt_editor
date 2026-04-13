import json
import base64
import urllib.request
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import websockets
except ImportError:
    websockets = None

class LightpandaClientThread(QThread):
    """
    Background worker that connects to a local CDP interface (Lightpanda/Chrome),
    navigates to a URL, and captures a PNG screenshot.
    """
    finished = pyqtSignal(str, str) # url, output_png_path
    error = pyqtSignal(str, str)    # url, error_message

    def __init__(self, url, width, height, output_path):
        super().__init__()
        self.url = url
        self.width = width
        self.height = height
        self.output_path = output_path

    def run(self):
        if websockets is None:
            self.error.emit(self.url, "websockets library not installed.")
            return

        try:
            # 1. Fetch debugger URL from 127.0.0.1:9222/json
            resp = urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=5)
            targets = json.loads(resp.read().decode('utf-8'))
            if not targets:
                self.error.emit(self.url, "No CDP targets available. Is Lightpanda running?")
                return
            
            # Find a valid page target
            ws_url = None
            for t in targets:
                if t.get('type') == 'page' and 'webSocketDebuggerUrl' in t:
                    ws_url = t['webSocketDebuggerUrl']
                    break
            
            if not ws_url:
                self.error.emit(self.url, "No suitable WebSocket Debugger URL found from Lightpanda.")
                return

            # Run async event loop for websockets operations
            # Since PyQt threads and asyncio can sometimes clash if reusing event loops,
            # we create a fresh one for this thread explicitly if needed.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._capture(ws_url))
            finally:
                loop.close()

        except Exception as e:
            self.error.emit(self.url, f"Lightpanda Connection Error: {e}")

    async def _capture(self, ws_url):
        import websockets
        async with websockets.connect(ws_url) as ws:
            # Helper to send and recv
            msg_id = [0]
            async def send_cmd(method, params=None):
                msg_id[0] += 1
                cmd = {"id": msg_id[0], "method": method}
                if params: cmd["params"] = params
                await ws.send(json.dumps(cmd))
                # Wait for response matching this ID
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get("id") == msg_id[0]:
                        if "error" in resp:
                            raise Exception(resp["error"].get("message", "Unknown CDP Error"))
                        return resp.get("result", {})

            # 2. Set viewport size
            await send_cmd("Emulation.setDeviceMetricsOverride", {
                "width": self.width,
                "height": self.height,
                "deviceScaleFactor": 1,
                "mobile": False,
            })

            # 3. Navigate
            await send_cmd("Page.enable")
            await send_cmd("Page.navigate", {"url": self.url})

            # Wait for load event (simple polling/wait for now)
            # In a full robust client, we listen to Page.loadEventFired
            await asyncio.sleep(2.0) 

            # 4. Capture screenshot
            res = await send_cmd("Page.captureScreenshot", {"format": "png"})
            data = res.get("data")
            
            if data:
                img_bytes = base64.b64decode(data)
                with open(self.output_path, "wb") as f:
                    f.write(img_bytes)
                self.finished.emit(self.url, self.output_path)
            else:
                raise Exception("Screenshot data empty")
