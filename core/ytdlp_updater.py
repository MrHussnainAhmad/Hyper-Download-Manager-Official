"""
Background yt-dlp Auto-Updater

Automatically checks for and updates yt-dlp in the background without blocking UI.
Runs on app startup (cached to run once per 24h).
"""

import os
import subprocess
import time
import json
from PySide6.QtCore import QThread, Signal, QStandardPaths


class YtDlpUpdater(QThread):
    """Background thread to check and update yt-dlp"""
    
    # Signals
    status_signal = Signal(str)  # Status messages
    finished_signal = Signal(bool, str)  # (success, message)
    
    def __init__(self, force_check=False):
        super().__init__()
        self.force_check = force_check
        self._cache_file = self._get_cache_file()
    
    def _get_cache_file(self):
        """Get path to cache file"""
        try:
            config_dir = os.path.join(
                QStandardPaths.writableLocation(QStandardPaths.AppDataLocation),
                "HyperDownloadManager"
            )
            os.makedirs(config_dir, exist_ok=True)
            return os.path.join(config_dir, "ytdlp_last_check.json")
        except:
            return None
    
    def _should_check_update(self):
        """Check if we should check for updates (24h cache)"""
        if self.force_check:
            return True
        
        if not self._cache_file or not os.path.exists(self._cache_file):
            return True
        
        try:
            with open(self._cache_file, 'r') as f:
                data = json.load(f)
                last_check = data.get('last_check', 0)
                
                # Check if more than 24 hours have passed
                if time.time() - last_check > 86400:  # 24 hours
                    return True
                
                print(f"DEBUG: yt-dlp check skipped (last check {(time.time() - last_check) / 3600:.1f}h ago)")
                return False
        except:
            return True
    
    def _save_check_time(self):
        """Save last check time to cache"""
        if not self._cache_file:
            return
        
        try:
            with open(self._cache_file, 'w') as f:
                json.dump({'last_check': time.time()}, f)
        except:
            pass
    
    def _check_ytdlp_installed(self):
        """Check if yt-dlp is installed"""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except:
            return False
    
    def _get_current_version(self):
        """Get current yt-dlp version"""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None
    
    def _update_ytdlp(self):
        """Update yt-dlp using pip or self-update"""
        try:
            # Try yt-dlp self-update first (faster)
            print("DEBUG: Attempting yt-dlp self-update...")
            result = subprocess.run(
                ['yt-dlp', '-U'],
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                # Check if actually updated
                if "already up to date" in result.stdout.lower() or "up-to-date" in result.stdout.lower():
                    return True, "already_updated"
                else:
                    return True, "updated"
            
            # If self-update failed, try pip
            print("DEBUG: Self-update failed, trying pip...")
            result = subprocess.run(
                ['pip', 'install', '--upgrade', 'yt-dlp'],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                if "already satisfied" in result.stdout.lower():
                    return True, "already_updated"
                else:
                    return True, "updated"
            
            return False, "update_failed"
            
        except subprocess.TimeoutExpired:
            return False, "timeout"
        except Exception as e:
            print(f"DEBUG: Update error: {e}")
            return False, str(e)
    
    def run(self):
        """Main thread execution"""
        try:
            # Check if we should run (24h cache)
            if not self._should_check_update():
                self.finished_signal.emit(True, "skipped")
                return
            
            # Check if yt-dlp is installed
            self.status_signal.emit("Checking yt-dlp...")
            
            if not self._check_ytdlp_installed():
                print("DEBUG: yt-dlp not found")
                self.finished_signal.emit(False, "not_installed")
                return
            
            # Get current version
            current_version = self._get_current_version()
            if current_version:
                print(f"DEBUG: Current yt-dlp version: {current_version}")
            
            # Attempt update
            self.status_signal.emit("Updating yt-dlp...")
            success, result = self._update_ytdlp()
            
            # Save check time
            self._save_check_time()
            
            # Emit result
            if success:
                if result == "already_updated":
                    print("DEBUG: yt-dlp already up to date")
                    self.status_signal.emit("yt-dlp up to date")
                    self.finished_signal.emit(True, "already_updated")
                else:
                    new_version = self._get_current_version()
                    print(f"DEBUG: yt-dlp updated to {new_version}")
                    self.status_signal.emit(f"yt-dlp updated to {new_version}")
                    self.finished_signal.emit(True, "updated")
            else:
                print(f"DEBUG: yt-dlp update failed: {result}")
                self.status_signal.emit("Update check complete")
                self.finished_signal.emit(False, result)
                
        except Exception as e:
            print(f"DEBUG: YtDlpUpdater error: {e}")
            import traceback
            traceback.print_exc()
            self.finished_signal.emit(False, str(e))
