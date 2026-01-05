import requests
from PySide6.QtCore import QThread, Signal, QObject
import os

class UpdateChecker(QThread):
    update_available = Signal(str, str) # version, download_url
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
            url = f"{self.api_url}/api/version?platform=windows&t={int(time.time())}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            remote_version = data.get("version")
            download_url = data.get("downloadUrl")
            
            if remote_version:
                if self._is_newer(remote_version):
                    self.update_available.emit(remote_version, download_url)
                else:
                    self.up_to_date.emit()
            else:
                self.error_occurred.emit("Invalid response from server")
                
        except Exception as e:
            self.error_occurred.emit(str(e))
            
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
