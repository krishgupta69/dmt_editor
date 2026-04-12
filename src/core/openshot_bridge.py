"""
OpenShot Bridge — single import point for all openshot bindings.
Searches known install locations for the real libopenshot Python module.
Falls back to core.openshot_mock if not found.

The bridge uses subprocess probing to test .pyd compatibility, preventing
hard Python crashes from ABI-incompatible binary modules.

Usage in all DMT editor files:
    from core.openshot_bridge import openshot
"""
import sys
import os
import subprocess

OPENSHOT_PATHS = [
    r"C:\Program Files\OpenShot Video Editor\lib",
    r"C:\Program Files\OpenShot Video Editor",
    r"/usr/lib/openshot",
    r"/usr/local/lib/openshot",
]

_loaded = False
openshot = None


def _probe_path(path):
    """Test if _openshot.pyd can load from 'path' in a subprocess.
    Returns version string on success, None on failure."""
    probe_code = f"""
import sys, os
sys.path.insert(0, r"{path}")
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    os.add_dll_directory(r"{path}")
    parent = os.path.dirname(r"{path}")
    if parent != r"{path}":
        os.add_dll_directory(parent)
try:
    import _openshot
    print("OK:" + _openshot.GetVersion().ToString())
except Exception as e:
    print("FAIL:" + str(e))
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", probe_code],
            capture_output=True, text=True, timeout=10
        )
        stdout = result.stdout.strip()
        if stdout.startswith("OK:"):
            return stdout[3:]
    except Exception:
        pass
    return None


for path in OPENSHOT_PATHS:
    if not os.path.exists(path):
        continue

    # First, probe in a subprocess to avoid crashing the main process
    ver = _probe_path(path)
    if ver is not None:
        # Safe to load in-process
        if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(path)
                parent = os.path.dirname(path)
                if parent != path:
                    os.add_dll_directory(parent)
            except OSError:
                pass

        sys.path.insert(0, path)
        try:
            import _openshot
            openshot = _openshot
            _loaded = True
            print(f"[DMT] OpenShot loaded from: {path}")
            print(f"[DMT] Version: {ver}")
            break
        except ImportError:
            sys.path.pop(0)
    else:
        print(f"[DMT] Skipping {path} (probe failed — likely Python version mismatch)")

if not _loaded:
    from core import openshot_mock as openshot  # type: ignore
    print("[DMT] WARNING: Using mock openshot -- install OpenShot Video Editor")
    print(f"[DMT] NOTE: Your Python is {sys.version.split()[0]}.")
    print(f"[DMT]       The _openshot.pyd in OpenShot v3.5.1 requires Python 3.8.")
    print(f"[DMT]       To use real bindings, install Python 3.8 and run this app with it,")
    print(f"[DMT]       or build libopenshot from source for your Python version.")
    print(f"[DMT] Searched paths: {OPENSHOT_PATHS}")
