import os
import requests
import time
from PySide6.QtCore import QObject, QThread, Signal, QMutex, QMutexLocker

class DownloadWorker(QThread):
    progress_signal = Signal(int, int) # chunk_id, bytes_downloaded
    finished_signal = Signal(int) # chunk_id
    error_signal = Signal(int, str) # chunk_id, error_message

    def __init__(self, url, start_byte, end_byte, chunk_id, file_path):
        super().__init__()
        self.url = url
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.chunk_id = chunk_id
        self.file_path = file_path
        self._is_paused = False
        self._is_stopped = False
        self.mutex = QMutex()

    def run(self):
        headers = {'Range': f'bytes={self.start_byte}-{self.end_byte}'}
        try:
            # Open file in 'ab' mode to append to part file
            
            with requests.get(self.url, headers=headers, stream=True, timeout=10) as response:
                response.raise_for_status()
                
                with open(self.file_path, "ab") as f:
                    # f.seek(self.start_byte) # Not needed for parts
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        with QMutexLocker(self.mutex):
                            if self._is_stopped:
                                return
                            if self._is_paused:
                                # Simple pause: break loop, saving is done by manager tracking progress
                                return 

                        if chunk:
                            f.write(chunk)
                            self.progress_signal.emit(self.chunk_id, len(chunk))
                            
            self.finished_signal.emit(self.chunk_id)

        except Exception as e:
            self.error_signal.emit(self.chunk_id, str(e))

    def pause(self):
        with QMutexLocker(self.mutex):
            self._is_paused = True

    def stop(self):
        with QMutexLocker(self.mutex):
            self._is_stopped = True

class DownloadTask(QObject):
    # Signals for the UI
    progress_updated = Signal(int, int, float) # progress_pct, download_speed, eta
    status_changed = Signal(str) # "Downloading", "Paused", "Finished", "Error", "Queued"
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, url, save_path, threads=8):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.num_threads = threads
        self.workers = []
        self.file_size = 0
        self.downloaded_bytes = 0
        self.status = "Idle"
        self.start_time = 0
        self.added_time = time.time()
        self.chunk_progress = {} # chunk_id: bytes_downloaded_in_chunk
        
        # Temp Management
        self.save_dir = os.path.dirname(save_path)
        self.file_name = os.path.basename(save_path)
        
        # Check for central Temp dir in App Directory (e.g. Program Files/FDM/Temp)
        import sys
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__)) # core dir
            base_path = os.path.dirname(base_path) # root dir
            
        central_temp = os.path.join(base_path, "Temp")
        if os.path.exists(central_temp) and os.access(central_temp, os.W_OK):
            self.temp_dir = os.path.join(central_temp, self.file_name)
        else:
            self.temp_dir = os.path.join(self.save_dir, ".fdm_temp", self.file_name)
        
    def _prepare_temp_dir(self):
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(os.path.dirname(self.temp_dir), FILE_ATTRIBUTE_HIDDEN)

    def start_download(self):
        if self.status in ["Downloading", "Finished"]:
            return

        self.status = "Downloading"
        self.status_changed.emit("Downloading")
        self.start_time = time.time()
        
        self._prepare_temp_dir()
        
        # 1. Get File Size
        try:
            head = requests.head(self.url, allow_redirects=True)
            self.file_size = int(head.headers.get('content-length', 0))
            if self.file_size == 0:
                 self.start_single_thread() # Fallback
                 return
        except Exception as e:
            self.error_occurred.emit(f"Failed to fetch metadata: {e}")
            self.status = "Error"
            return

        # 2. Calculate Chunks
        chunk_size = self.file_size // self.num_threads
        
        for i in range(self.num_threads):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < self.num_threads - 1 else self.file_size - 1
            
            part_path = os.path.join(self.temp_dir, f"part_{i}")
            
            # Check existing part size for resume logic (simplistic)
            current_size = 0
            if os.path.exists(part_path):
                current_size = os.path.getsize(part_path)
                
            self.chunk_progress[i] = current_size
            
            # If part is complete, skip? For now, we overwrite or append. 
            # Ideally we resume from start + current_size
            resume_start = start + current_size
            if resume_start > end:
                # Already done
                continue
                
            worker = DownloadWorker(self.url, resume_start, end, i, part_path)
            worker.progress_signal.connect(self._on_worker_progress)
            worker.finished_signal.connect(self._on_worker_finished)
            self.workers.append(worker)
            worker.start()

    def _on_worker_progress(self, chunk_id, bytes_count):
        self.chunk_progress[chunk_id] += bytes_count
        
        total_downloaded = sum(self.chunk_progress.values())
        self.downloaded_bytes = total_downloaded
        
        elapsed = time.time() - self.start_time
        speed = total_downloaded / elapsed if elapsed > 0 else 0
        
        pct = int((total_downloaded / self.file_size) * 100) if self.file_size > 0 else 0
        eta = (self.file_size - total_downloaded) / speed if speed > 0 else 0
        
        self.progress_updated.emit(pct, int(speed), eta)
        
        if total_downloaded >= self.file_size:
            self.merge_parts()

    def merge_parts(self):
        # Double-check if we are already merging or finished to prevent race conditions
        if self.status == "Merging" or self.status == "Finished":
            return
            
        # Verify all threads are done? 
        # Actually, _on_worker_progress triggers this when TOTAL matches file_size.
        # But workers might still be flushing?
        # Let's wait for workers to finish
        for worker in self.workers:
            worker.wait()

        self.status = "Merging"
        self.status_changed.emit("Merging")
        try:
            with open(self.save_path, "wb") as outfile:
                for i in range(self.num_threads):
                    part_path = os.path.join(self.temp_dir, f"part_{i}")
                    if not os.path.exists(part_path):
                         raise Exception(f"Missing part file: {part_path}")
                         
                    with open(part_path, "rb") as infile:
                        while True:
                            chunk = infile.read(1024 * 1024) # 1MB chunks
                            if not chunk:
                                break
                            outfile.write(chunk)
            
            # Cleanup
            self.delete_temp_files()
            
            self.status = "Finished"
            self.status_changed.emit("Finished")
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"Merge error: {e}")
            self.status = "Error"

    def _on_worker_finished(self, chunk_id):
        pass

    def pause(self):
        self.status = "Paused"
        self.status_changed.emit("Paused")
        for worker in self.workers:
            worker.pause()
            
    def resume(self):
        if self.status in ["Paused", "Stopped", "Queued"]:
            self.start_download() # It has resume logic built-in

    def stop(self):
        self.status = "Stopped"
        self.status_changed.emit("Stopped")
        for worker in self.workers:
            worker.stop()
            worker.wait()
            
    def delete_temp_files(self):
         import shutil
         if os.path.exists(self.temp_dir):
             shutil.rmtree(self.temp_dir)
             
    def delete_all_files(self):
        self.stop()
        try:
            self.delete_temp_files()
        except:
            pass
            
        try:
            if os.path.exists(self.save_path):
                os.remove(self.save_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
            # We don't re-raise, so manager can proceed to remove task from list
    
    def start_single_thread(self):
        # Fallback for unknown size
        pass
