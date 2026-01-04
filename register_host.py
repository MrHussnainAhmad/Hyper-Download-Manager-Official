import sys
import os
import winreg

def register_host():
    # 1. Define Host Name
    HOST_NAME = "com.hussnain.fdm"
    
    # 2. Get Path to Manifest
    # Needs to be absolute.
    # We created nm_manifest.json in d:/FDM/
    manifest_path = os.path.abspath("nm_manifest.json")
    
    # 3. Registry Key
    # HKCU\Software\Google\Chrome\NativeMessagingHosts\com.hussnain.fdm
    key_path = f"Software\\Google\\Chrome\\NativeMessagingHosts\\{HOST_NAME}"
    
    try:
        # Create Key
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        
        # Set default value to manifest path
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, manifest_path)
        winreg.CloseKey(key)
        
        print(f"Successfully registered '{HOST_NAME}'")
        print(f"Manifest: {manifest_path}")
        print("\nNOTE: You must verify the allowed_origins in nm_manifest.json matches your installed Extension ID.")
        
    except Exception as e:
        print(f"Failed to register host: {e}")

if __name__ == "__main__":
    register_host()
