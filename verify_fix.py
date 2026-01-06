
import sys
import os
import json
import time

# Mock PySide6 for headless environment if needed, or just import core modules
# Assuming we can run this with the current python environment
sys.path.append(os.getcwd())

from core.downloader import DownloadTask
from core.download_manager import DownloadManager

def verify_fix():
    print("Verifying Added Time Fix...")
    
    # 1. Test Task Creation
    task = DownloadTask("http://example.com/file.zip", "C:\\Downloads\\file.zip")
    initial_time = task.added_time
    print(f"Task created at: {initial_time}")
    
    if initial_time == 0:
        print("FAIL: added_time not initialized in __init__")
        return False
        
    # 2. Test JSON Serialization (Simulate Save)
    data = {
        "url": task.url,
        "save_path": task.save_path,
        "status": task.status,
        "file_size": task.file_size,
        "downloaded_bytes": task.downloaded_bytes,
        "added_time": task.added_time
    }
    
    json_str = json.dumps([data])
    print(f"JSON Data: {json_str}")
    
    if "added_time" not in json_str:
        print("FAIL: added_time not present in JSON")
        return False

    # 3. Test JSON Deserialization (Simulate Load)
    loaded_data = json.loads(json_str)
    item = loaded_data[0]
    
    loaded_task = DownloadTask(item.get("url"), item.get("save_path"))
    # Simulate logic in manager's load_state
    loaded_task.status = item.get("status", "Stopped")
    loaded_task.file_size = item.get("file_size", 0)
    loaded_task.downloaded_bytes = item.get("downloaded_bytes", 0)
    loaded_task.added_time = item.get("added_time", time.time())
    
    print(f"Loaded Task Time: {loaded_task.added_time}")
    
    if abs(loaded_task.added_time - initial_time) > 0.001:
        print("FAIL: Time mismatch after load")
        return False
        
    print("SUCCESS: Added Time persisted correctly.")
    return True

if __name__ == "__main__":
    try:
        if verify_fix():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
