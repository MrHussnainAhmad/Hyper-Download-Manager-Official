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
            msg_type = msg.get('text')
            
            if msg_type == "download_url":
                url = msg.get('url')
                log(f"Processing URL: {url}")
                launch_downloader(url)
                send_message({"text": "download_started"})
                
            elif msg_type == "fetch_variants":
                url = msg.get('url')
                log(f"Fetching variants for: {url}")
                try:
                    # Import here to avoid startup overhead if not needed immediately, 
                    # but mostly to ensure we can log import errors safely
                    from core.youtube_extractor import fetch_youtube_data
                    data = fetch_youtube_data(url)
                    send_message({"success": True, "data": data['streams'], "info": data['info']})
                except Exception as e:
                    log(f"Error fetching variants: {e}")
                    send_message({"success": False, "error": str(e)})

            elif msg_type == "download_variant":
                url = msg.get('url')
                filename = msg.get('filename')
                filesize = msg.get('filesize')
                quality = msg.get('quality')  # e.g., "1080p"
                itag = msg.get('itag')        # Stream identifier
                
                log(f"Downloading variant: {url} (quality: {quality}, itag: {itag})")
                
                # Bundle arguments into a JSON string for the main app
                launch_data = {
                    "url": url,
                    "filename": filename,
                    "filesize": filesize,
                    "quality": quality,
                    "itag": itag
                }
                
                launch_downloader(launch_data)
                send_message({"success": True})

        except Exception as e:
            log(f"ERROR: {str(e)}")
            # send_message({"text": "error", "message": str(e)})
            sys.exit(1)

def launch_downloader(data):
    # Determine Executable Path
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        if sys.platform == "win32":
            exe_path = os.path.join(base_path, "HyperDownloadManager.exe")
        else:
            exe_path = os.path.join(base_path, "HyperDownloadManager")
    else:
        # Running from source (dev)
        base_path = os.path.dirname(os.path.abspath(__file__))
        exe_path = sys.executable
        # Assuming main.py is in the root or same dir as nm_host.py
        # Based on file list, nm_host.py is in root, main.py is in root.
        script_path = os.path.join(base_path, "main.py")
        
    log(f"Target Exe Path: {exe_path}")
    
    # Prepare argument: either raw URL or JSON string
    if isinstance(data, dict):
        arg = json.dumps(data)
    else:
        arg = data

    if getattr(sys, 'frozen', False):
        if os.path.exists(exe_path):
            subprocess.Popen([exe_path, arg])
            log("Launch command sent")
        else:
            log(f"ERROR: Executable not found at {exe_path}")
    else:
        # Pass script path if python
        subprocess.Popen([exe_path, script_path, arg])

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"CRITICAL: {str(e)}")
