import sys
import json
import struct
import subprocess
import os

# Windows-specific: ensure we run with pythonw to avoid console window if needed, 
# but for the host itself, it's run by chrome. 
# We need to launch the main app.

# Logging setup
def log(msg):
    try:
        log_path = os.path.join(os.path.expanduser("~"), "hdm_debug.log")
        with open(log_path, "a") as f:
            f.write(str(msg) + "\n")
    except:
        pass

def get_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        log("Read 0 bytes, exiting")
        sys.exit(0)
    message_length = struct.unpack('@I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    log(f"Received message: {message}")
    return json.loads(message)

def send_message(message):
    encoded_content = json.dumps(message).encode('utf-8')
    encoded_length = struct.pack('@I', len(encoded_content))
    sys.stdout.buffer.write(encoded_length)
    sys.stdout.buffer.write(encoded_content)
    sys.stdout.buffer.flush()

def main():
    log("Native Host monitoring started")
    while True:
        try:
            msg = get_message()
            if msg.get('text') == "download_url":
                url = msg.get('url')
                log(f"Processing URL: {url}")
                
                # Determine Executable Path
                if getattr(sys, 'frozen', False):
                    # Running as compiled exe
                    base_path = os.path.dirname(sys.executable)
                    # Aassuming we compile nm_host.exe and put it in same folder as HyperDownloadManager.exe
                    exe_path = os.path.join(base_path, "HyperDownloadManager.exe")
                else:
                    # Running from source (dev)
                    base_path = os.path.dirname(os.path.abspath(__file__))
                    # We can't really test this easily without python, but dev flow is usually manual
                    # Point to python and main.py
                    exe_path = "python"
                    args = [exe_path, os.path.join(base_path, "main.py"), url]
                
                log(f"Target Exe Path: {exe_path}")
                
                if getattr(sys, 'frozen', False):
                    if os.path.exists(exe_path):
                        log("Executable found, launching...")
                        subprocess.Popen([exe_path, url], shell=False)
                        log("Launch command sent")
                    else:
                        log(f"ERROR: Executable not found at {exe_path}")
                else:
                    subprocess.Popen(args, shell=True)
                    
                send_message({"text": "download_started"})
        except Exception as e:
            log(f"ERROR: {str(e)}")
            # send_message({"text": "error", "message": str(e)})
            sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"CRITICAL: {str(e)}")
