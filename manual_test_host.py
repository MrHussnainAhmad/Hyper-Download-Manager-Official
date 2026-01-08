import sys
import struct
import json
import subprocess
import os
import time

def check_host():
    msg = {"text": "fetch_variants", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    encoded = json.dumps(msg).encode('utf-8')
    length = struct.pack('@I', len(encoded))
    
    # Run host
    host_path = os.path.join(os.getcwd(), 'nm_host.py')
    cmd = [sys.executable, host_path]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print(f"Sending message: {msg}")
    try:
        proc.stdin.write(length)
        proc.stdin.write(encoded)
        proc.stdin.flush()
        
        # Read response
        len_bytes = proc.stdout.read(4)
        if not len_bytes:
            print("No response length")
            print("Stderr:", proc.stderr.read().decode())
            return

        res_len = struct.unpack('@I', len_bytes)[0]
        res_bytes = proc.stdout.read(res_len)
        response = json.loads(res_bytes.decode('utf-8'))
        
        print("Response received!")
        print(json.dumps(response, indent=2)[:500] + "...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()

if __name__ == "__main__":
    check_host()
