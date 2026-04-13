import asyncio, json, subprocess, sys, time
import requests, websockets
from pathlib import Path

class LightpandaManager:
    BINARY = {
        "win32":  Path("browser/bin/lightpanda.exe"),
        "linux":  Path("browser/bin/lightpanda"),
        "darwin": Path("browser/bin/lightpanda"),
    }
    CDP = "ws://127.0.0.1:9222"
    
    def __init__(self): self.process = None
    
    def download_binary(self) -> bool:
        plat = {"win32":"windows","linux":"linux","darwin":"macos"}.get(sys.platform,"linux")
        resp = requests.get(
          "https://api.github.com/repos/lightpanda-io/browser/releases/latest",
          timeout=10).json()
        for asset in resp.get("assets", []):
            if plat in asset["name"].lower():
                binary = self.BINARY[sys.platform]
                binary.parent.mkdir(parents=True, exist_ok=True)
                binary.write_bytes(requests.get(asset["browser_download_url"]).content)
                if sys.platform != "win32": binary.chmod(0o755)
                return True
        return False
    
    def start(self) -> bool:
        binary = self.BINARY.get(sys.platform)
        if not binary or not binary.exists():
            if not self.download_binary(): return False
        self.process = subprocess.Popen(
            [str(binary), "--cdp-host", "127.0.0.1", "--cdp-port", "9222"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try: asyncio.run(self._ping()); return True
            except: time.sleep(0.1)
        return False
    
    async def _ping(self):
        async with websockets.connect(self.CDP, open_timeout=1): pass
    
    async def _cdp(self, method, params={}):
        async with websockets.connect(self.CDP) as ws:
            await ws.send(json.dumps({"id":1,"method":method,"params":params}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == 1: return msg.get("result", {})
    
    def navigate(self, url: str) -> str:
        asyncio.run(self._cdp("Page.navigate", {"url": url}))
        time.sleep(1.5)
        r = asyncio.run(self._cdp("Runtime.evaluate", {"expression": "document.title"}))
        return r.get("result", {}).get("value", url)
    
    def find_media_urls(self, url: str) -> list:
        self.navigate(url)
        r = asyncio.run(self._cdp("Runtime.evaluate", {"expression": """
            JSON.stringify([
              ...Array.from(document.querySelectorAll('audio[src],video[src]'))
                .map(e=>({url:e.src,type:e.tagName.toLowerCase(),name:e.src.split('/').pop()})),
              ...Array.from(document.querySelectorAll('a[href]'))
                .filter(a=>/\\.(mp3|wav|mp4|mov|ogg|flac|aac)$/i.test(a.href))
                .map(a=>({url:a.href,type:'link',name:a.textContent.trim()||a.href.split('/').pop()}))
            ])"""}))
        try: return json.loads(r.get("result",{}).get("value","[]"))
        except: return []
    
    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None
    
    def stop(self):
        if self.process: self.process.terminate(); self.process = None
