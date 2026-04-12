import sys
import os
import traceback

# Ensure src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from core.openshot_bridge import openshot
    print(f"[TEST] openshot module type: {type(openshot)}")
    print(f"[TEST] openshot module name: {getattr(openshot, '__name__', 'N/A')}")
    try:
        ver = openshot.GetVersion().ToString()
        print(f"[TEST] OpenShot version: {ver}")
    except Exception as e:
        print(f"[TEST] GetVersion failed: {e}")
except Exception as e:
    print(f"[TEST] FAILED to import bridge: {e}")
    traceback.print_exc()
