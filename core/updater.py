import requests
from PySide6.QtCore import QThread, Signal, QObject
import os
import platform # Added at module level
import re

class UpdateChecker(QThread):
    update_available = Signal(str, str, str) # version, download_url, note
    up_to_date = Signal() # New signal
    error_occurred = Signal(str)
    
    def __init__(self, api_url, current_version):
        super().__init__()
        self.api_url = api_url
        self.current_version = current_version
        
    def run(self):
        try:
            # Add timestamp to prevent caching
            import time
            
            # Detect platform
            system = platform.system().lower()
            if system == "windows":
                plat_param = "windows"
            elif system == "linux":
                plat_param = "linux"
            else:
                plat_param = "windows" # Default to windows behavior if unknown
            
            url = f"{self.api_url}/api/version?platform={plat_param}&t={int(time.time())}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            remote_version = data.get("version")
            download_url = data.get("downloadUrl")
            note = data.get("note", "")
            
            if remote_version:
                # Validate URL extension against platform
                valid_update = False
                if plat_param == "windows":
                    if download_url and download_url.lower().endswith(".exe"):
                        valid_update = True
                elif plat_param == "linux":
                    if download_url and download_url.lower().endswith(".deb"):
                        valid_update = True
                
                if valid_update:
                    if self._is_newer(remote_version):
                        # Try to fetch note from GitHub if missing
                        if not note and download_url and "github.com" in download_url:
                            note = self._fetch_github_note(download_url)
                            
                        self.update_available.emit(remote_version, download_url, note)
                    else:
                        self.up_to_date.emit()
                else:
                     # If format doesn't match OS (e.g. linux user got .exe), treat as no update or error
                     # For now, we just don't emit update_available to avoid false positives
                     # We can emit up_to_date if we want to be silent, or error. 
                     # Given the requirements "do nothing", we might just emit up_to_date or nothing.
                     # Let's emit up_to_date so manual checks don't hang if they expect a signal.
                     self.up_to_date.emit()
            else:
                self.error_occurred.emit("Invalid response from server")
                
        except Exception as e:
            self.error_occurred.emit(str(e))
            
    def _fetch_github_note(self, download_url):
        try:
            # Extract owner, repo, tag from: https://github.com/OWNER/REPO/releases/download/TAG/filename
            match = re.search(r"github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/", download_url)
            if match:
                owner, repo, tag = match.groups()
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
                resp = requests.get(api_url, timeout=5)
                if resp.status_code == 200:
                    return resp.json().get("body", "")
        except:
            pass
        return ""

    def _is_newer(self, remote_ver):
        try:
            v1_parts = [int(x) for x in remote_ver.split('.')]
            v2_parts = [int(x) for x in self.current_version.split('.')]
            
            # Normalize length
            while len(v1_parts) < len(v2_parts): v1_parts.append(0)
            while len(v2_parts) < len(v1_parts): v2_parts.append(0)
            
            return v1_parts > v2_parts
        except:
            return False
