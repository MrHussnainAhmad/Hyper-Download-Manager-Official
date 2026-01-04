import json
import os
from PySide6.QtCore import QObject, Signal, QStandardPaths, QTimer
from core.downloader import DownloadTask

class DownloadManager(QObject):
    # Signals
    download_added = Signal(object) # DownloadTask object
    download_removed = Signal(object) # DownloadTask object
    
    def __init__(self):
        super().__init__()
        self.downloads = [] # List of DownloadTask objects
        self.config_dir = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.AppDataLocation), 
            "HyperDownloadManager"
        )
        self.downloads_file = os.path.join(self.config_dir, "downloads.json")
        self.ensure_config_dir()
        
        # Autosave timer
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_state)
        self.autosave_timer.start(30000) # Save every 30 seconds
        
        self.load_state()
        
    def ensure_config_dir(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def _connect_task_signals(self, task):
        # Save on important state changes
        task.status_changed.connect(lambda s: self.save_state())
        task.finished.connect(self.save_state)
        task.error_occurred.connect(lambda e: self.save_state())

    def add_download(self, url, save_path, auto_start=True):
        # Check if already exists?
        task = DownloadTask(url, save_path)
        self.downloads.append(task)
        self._connect_task_signals(task)
        self.download_added.emit(task)
        
        if auto_start:
            task.start_download()
        else:
            task.status = "Queued" # Or Idle
            task.status_changed.emit("Queued")
            
        self.save_state()
        return task
        
    def is_duplicate(self, url):
        return any(t.url == url for t in self.downloads)

    def remove_download(self, task):
        if task in self.downloads:
            task.delete_all_files() # Delete from disk
            if task in self.downloads: # Check again if deletion modified list?
                self.downloads.remove(task)
            self.download_removed.emit(task)
            self.save_state()

    def start_all_downloads(self):
        for task in self.downloads:
            if task.status in ["Paused", "Stopped", "Idle", "Queued"]:
                task.resume() # Needs resume impl in DownloadTask, or start_download

    def pause_all_downloads(self):
        for task in self.downloads:
            if task.status == "Downloading":
                task.pause()

    def load_state(self):
        if not os.path.exists(self.downloads_file):
            return

        try:
            with open(self.downloads_file, 'r') as f:
                data = json.load(f)
                # Reconstruct tasks from data
                for item in data:
                    try:
                        task = DownloadTask(item.get("url"), item.get("save_path"))
                        task.status = item.get("status", "Stopped")
                        task.file_size = item.get("file_size", 0)
                        task.downloaded_bytes = item.get("downloaded_bytes", 0)
                        
                        # Reset transient states
                        if task.status == "Downloading":
                            task.status = "Stopped"
                            
                        self.downloads.append(task)
                        self._connect_task_signals(task)
                        self.download_added.emit(task)
                    except Exception as e:
                        print(f"Error restoring task: {e}")
                        continue
        except Exception as e:
            print(f"Error loading state: {e}")

    def save_state(self):
        data = []
        for task in self.downloads:
            data.append({
                "url": task.url,
                "save_path": task.save_path,
                "status": task.status,
                "file_size": task.file_size,
                "downloaded_bytes": task.downloaded_bytes
            })
        
        try:
            with open(self.downloads_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving state: {e}")
