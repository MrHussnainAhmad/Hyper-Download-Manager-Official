import sys
import os
import json
import platform

def install_host():
    HOST_NAME = "com.hussnain.fdm"
    ALLOWED_ORIGINS = [
        "chrome-extension://gjcibhkanadbielaoejhgjpggbehnblp/"
    ]
    
    # Check OS
    system = platform.system()
    
    if system == "Windows":
        import winreg
        print("Detected Windows system.")
        
        manifest_path = os.path.abspath("nm_manifest.json")
        key_path = f"Software\\Google\\Chrome\\NativeMessagingHosts\\{HOST_NAME}"
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, manifest_path)
            winreg.CloseKey(key)
            print(f"Successfully registered '{HOST_NAME}' in Registry.")
            print(f"Manifest: {manifest_path}")
        except Exception as e:
            print(f"Failed to register host: {e}")
            
    elif system == "Linux" or system == "Darwin":
        print(f"Detected {system} system.")
        
        # 1. Determine Native Host Path
        # In a dev environment, we point to the python script
        # In a production environment (installed via deb), this script might not be used directly
        # But for manual install, we'll setup a wrapper script
        
        # Get absolute path to nm_host.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        host_script = os.path.join(current_dir, "nm_host.py")
        wrapper_path = os.path.join(current_dir, "nm_host_wrapper.sh")
        
        # 2. Create Wrapper Script
        # Native hosts on Linux must be an executable file, can't be just a .py file usually without a shebang+permissions
        # Safer to use a shell wrapper that calls the right python
        python_exe = sys.executable
        
        print(f"Creating wrapper script at: {wrapper_path}")
        with open(wrapper_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f'"{python_exe}" "{host_script}" "$@"\n')
            
        os.chmod(wrapper_path, 0o755)
        
        # 3. Create Manifest
        manifest_path = os.path.join(current_dir, "nm_manifest.json")
        print(f"Creating manifest at: {manifest_path}")
        
        manifest = {
            "name": HOST_NAME,
            "description": "Hyper Download Manager Native Host",
            "path": wrapper_path,
            "type": "stdio",
            "allowed_origins": ALLOWED_ORIGINS
        }
        
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=4)
            
        # 4. Install Manifest
        # User-level installation path
        home = os.path.expanduser("~")
        if system == "Linux":
            # Chrome/Chromium
            config_dirs = [
                os.path.join(home, ".config/google-chrome/NativeMessagingHosts"),
                os.path.join(home, ".config/chromium/NativeMessagingHosts")
            ]
            # Firefox
            config_dirs.append(os.path.join(home, ".mozilla/native-messaging-hosts"))
            
        elif system == "Darwin":
            config_dirs = [
                os.path.join(home, "Library/Application Support/Google/Chrome/NativeMessagingHosts"),
                os.path.join(home, "Library/Application Support/Chromium/NativeMessagingHosts"),
                os.path.join(home, "Library/Application Support/Mozilla/NativeMessagingHosts")
            ]
            
        for config_dir in config_dirs:
            if not os.path.exists(config_dir):
                try:
                    os.makedirs(config_dir)
                except OSError:
                    continue
            
            target_path = os.path.join(config_dir, f"{HOST_NAME}.json")
            try:
                # We can symlink or copy. Valid manifest "path" must be absolute.
                # Since we generated absolute path in manifest, we can just copy the manifest file.
                with open(target_path, "w") as f:
                    json.dump(manifest, f, indent=4)
                print(f"Installed manifest to: {target_path}")
            except Exception as e:
                print(f"Failed to install to {target_path}: {e}")
                
        print("\nInstallation complete. Restart your browser.")
        
    else:
        print(f"Unsupported OS: {system}")

if __name__ == "__main__":
    install_host()
