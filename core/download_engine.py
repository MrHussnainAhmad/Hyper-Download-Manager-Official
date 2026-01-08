import os
import requests
import time
from PySide6.QtCore import QObject, QThread, Signal, QMutex, QMutexLocker

# Import settings and proxy manager
try:
    from core.settings import settings
except ImportError:
    settings = None

try:
    from core.proxy_manager import proxy_manager
except ImportError:
    proxy_manager = None


# REMOVED get_proxy_url() and get_proxy_dict()
# Proxies are now ONLY used for YouTube downloads via yt-dlp
# Regular downloads use direct connection for better performance and reliability


class YtDlpWorker(QThread):
    """Downloads using yt-dlp with automatic proxy rotation"""
    progress_signal = Signal(int)
    finished_signal = Signal()
    error_signal = Signal(str)
    status_signal = Signal(str)

    def __init__(self, url, save_path, itag=None, quality=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.itag = itag
        self.quality = quality
        self._stop_flag = False
        self.actual_file_path = None
        self._max_proxy_retries = 8  # Try up to 8 different proxies

    def stop(self):
        self._stop_flag = True

    def run(self):
        # First try without proxy (direct connection)
        self.status_signal.emit("Trying direct connection...")
        result = self._attempt_download(proxy_url=None)
        
        if result == "success":
            return
        elif result == "stopped":
            return
        elif result == "ytdlp_missing":
            self.error_signal.emit("YT_DLP_NOT_INSTALLED")
            return
        
        # Direct connection failed - try DEFAULT proxy immediately (no validation!)
        print("DEBUG: Direct connection failed, trying DEFAULT proxy...")
        self.status_signal.emit("Trying built-in proxy...")
        
        if proxy_manager:
            default_proxy = proxy_manager.get_default_proxy()
            if default_proxy:
                proxy_display = default_proxy.split("://")[-1][:25]
                print(f"DEBUG: Trying default proxy: {default_proxy}")
                result = self._attempt_download(proxy_url=default_proxy)
                
                if result == "success":
                    print("DEBUG: ✅ Default proxy worked!")
                    return
                elif result == "stopped":
                    return
                else:
                    print("DEBUG: ❌ Default proxy failed, will fetch more...")
        
        # Default proxy failed - now fetch and validate more proxies
        print("DEBUG: Default proxy failed, trying with validated proxies...")
        self.status_signal.emit("Direct blocked, finding proxies...")
        
        # Ensure we have proxies
        if proxy_manager:
            if proxy_manager.needs_refresh() or proxy_manager.get_working_count() < 3:
                self.status_signal.emit("Fetching fresh proxies...")
                self._refresh_proxies_sync()
        
        # Try with different proxies
        for attempt in range(self._max_proxy_retries):
            if self._stop_flag:
                return
            
            proxy_url = None
            if proxy_manager:
                proxy_url = proxy_manager.get_proxy()
            
            if not proxy_url:
                self.status_signal.emit("No proxies available")
                self.error_signal.emit("PROXY_UNAVAILABLE")
                return
            
            # Display short proxy info
            proxy_display = proxy_url.split("://")[-1][:25]
            self.status_signal.emit(f"Proxy {attempt + 1}/{self._max_proxy_retries}: {proxy_display}...")
            print(f"DEBUG: Attempt {attempt + 1} with proxy: {proxy_url[:50]}...")
            
            result = self._attempt_download(proxy_url=proxy_url)
            
            if result == "success":
                # Mark this proxy as good
                if proxy_manager:
                    proxy_manager.mark_proxy_success(proxy_url)
                return
            elif result == "stopped":
                return
            else:
                # Mark proxy as failed and try next
                if proxy_manager:
                    proxy_manager.mark_proxy_failed(proxy_url)
        
        # All attempts failed
        self.error_signal.emit("DOWNLOAD_FAILED_ALL_PROXIES")
    
    def _refresh_proxies_sync(self):
        """Synchronously refresh proxies (blocking)"""
        if not proxy_manager:
            return
        
        import threading
        event = threading.Event()
        
        def on_done(success):
            event.set()
        
        proxy_manager.refresh_proxies(callback=on_done)
        
        # Wait up to 90 seconds for proxies
        event.wait(timeout=90)
    
    def _attempt_download(self, proxy_url=None):
        """
        Attempt download with optional proxy.
        Returns: "success", "failed", "stopped", or "ytdlp_missing"
        """
        try:
            import subprocess
            
            format_selector = self._build_format_selector()
            
            save_dir = os.path.dirname(self.save_path)
            save_name = os.path.basename(self.save_path)
            
            if save_name.endswith('.mp4'):
                save_name = save_name[:-4]
            
            output_template = os.path.join(save_dir, save_name + ".%(ext)s")
            
            cmd = [
                "yt-dlp",
                "--no-playlist",
                "--newline",
                "--progress",
                "--force-overwrites",
                "--no-continue",
                "--socket-timeout", "30",
                "--retries", "3",
                "--fragment-retries", "3",
                "--retry-sleep", "2",
                "-f", format_selector,
                "--merge-output-format", "mp4",
                "-o", output_template,
            ]
            
            # Add proxy if provided
            if proxy_url:
                cmd.extend(["--proxy", proxy_url])
            
            cmd.append(self.url)
            
            print(f"DEBUG: yt-dlp command: {' '.join(cmd[:12])}...")
            
            # Delete existing file
            expected_file = os.path.join(save_dir, save_name + ".mp4")
            if os.path.exists(expected_file):
                try:
                    os.remove(expected_file)
                except:
                    pass
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            download_started = False
            last_progress = 0
            network_error = False
            gave_up = False
            
            for line in process.stdout:
                if self._stop_flag:
                    process.terminate()
                    process.wait()
                    return "stopped"
                
                line = line.strip()
                if line:
                    print(f"yt-dlp: {line}")
                
                line_lower = line.lower()
                
                # Detect network/proxy errors - IMPROVED DETECTION
                error_indicators = [
                    "timed out",
                    "timeout",
                    "connection refused",
                    "connection reset",
                    "unable to download webpage",
                    "proxy error",
                    "httpconnectionpool",
                    "httpsconnectionpool",
                    "max retries exceeded",
                    "network is unreachable",
                    "no route to host",
                    "http error 403",
                    "http error 429",
                    "got error: 403",
                    "got error",  # Generic yt-dlp error during download
                    "urlopen error",
                    "errno 10060",
                    "errno 10061",
                    "errno 111",
                    "failed to resolve",
                    "name resolution",
                    "connect timeout",
                    "read timeout",
                    "giving up after",
                ]
                
                for indicator in error_indicators:
                    if indicator in line_lower:
                        network_error = True
                        print(f"DEBUG: Network error detected: {indicator}")
                        break
                
                # Detect "giving up"
                if "giving up" in line_lower:
                    gave_up = True
                
                if "[download]" in line:
                    if "Destination:" in line:
                        download_started = True
                        try:
                            self.actual_file_path = line.split("Destination:")[-1].strip()
                        except:
                            pass
                    
                    # Progress parsing
                    if "%" in line and any(x in line for x in ["ETA", "MiB", "KiB", "GiB", "B/s"]):
                        download_started = True
                        try:
                            for part in line.split():
                                if '%' in part:
                                    pct_str = part.replace('%', '').strip()
                                    pct = float(pct_str)
                                    if pct > last_progress:
                                        last_progress = pct
                                        self.progress_signal.emit(int(pct))
                                    break
                        except:
                            pass
                
                if "[Merger]" in line or "Merging" in line:
                    self.progress_signal.emit(99)
            
            process.wait()
            
            print(f"DEBUG: yt-dlp exit code: {process.returncode}, network_error: {network_error}, gave_up: {gave_up}, started: {download_started}, progress: {last_progress}%")
            
            # Check if it failed due to network
            if process.returncode != 0:
                # If we detected network errors OR download never properly started, retry with proxy
                if network_error or gave_up or not download_started:
                    return "failed"  # Will retry with different proxy
                # Even if download started, if we got very little progress it's likely a network issue
                elif download_started and last_progress < 5:
                    print("DEBUG: Download started but made no progress - treating as network error")
                    return "failed"
                else:
                    # Some other error (format not available, etc)
                    self.error_signal.emit(f"yt-dlp failed (exit {process.returncode})")
                    return "failed"
            
            # Verify file exists
            for ext in ['.mp4', '.mkv', '.webm', '.mp4.part']:
                check_path = os.path.join(save_dir, save_name + ext)
                if os.path.exists(check_path):
                    size = os.path.getsize(check_path)
                    if size > 10000:  # At least 10KB
                        self.progress_signal.emit(100)
                        self.finished_signal.emit()
                        return "success"
            
            # Check actual path from yt-dlp output
            if self.actual_file_path and os.path.exists(self.actual_file_path):
                if os.path.getsize(self.actual_file_path) > 10000:
                    self.progress_signal.emit(100)
                    self.finished_signal.emit()
                    return "success"
            
            # File not found or too small
            return "failed"
                
        except FileNotFoundError:
            return "ytdlp_missing"
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"DEBUG: Download attempt exception: {e}")
            return "failed"
    
    def _build_format_selector(self):
        """Build yt-dlp format selector string"""
        
        # If specific itag is provided, use it directly
        if self.itag:
            print(f"DEBUG: Using specific itag: {self.itag}")
            # Try the exact itag with best audio, fallback to itag alone, then best
            return f"{self.itag}+bestaudio[ext=m4a]/{self.itag}+bestaudio/{self.itag}/best"
        
        # If quality string is provided
        if self.quality:
            q = self.quality.lower().strip()
            print(f"DEBUG: Using quality string: {q}")
            
            height_map = {
                "4k": 2160, "2160p": 2160, "2160": 2160,
                "1440p": 1440, "1440": 1440,
                "1080p": 1080, "1080": 1080,
                "720p": 720, "720": 720,
                "480p": 480, "480": 480,
                "360p": 360, "360": 360,
                "240p": 240, "240": 240,
                "144p": 144, "144": 144,
            }
            
            # Find matching height
            target_height = None
            for key, height in height_map.items():
                if key in q:
                    target_height = height
                    break
            
            if target_height:
                # Exact height match preferred
                return (
                    f"bestvideo[height={target_height}][ext=mp4]+bestaudio[ext=m4a]/"
                    f"bestvideo[height={target_height}]+bestaudio/"
                    f"bestvideo[height<={target_height}][ext=mp4]+bestaudio[ext=m4a]/"
                    f"bestvideo[height<={target_height}]+bestaudio/"
                    f"best[height<={target_height}]/best"
                )
        
        # Default: best quality available
        print("DEBUG: Using default format selector (best)")
        return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best"


class DownloadWorker(QThread):
    """Multi-threaded chunk downloader"""
    progress_signal = Signal(int, int)
    finished_signal = Signal(int)
    error_signal = Signal(int, str)

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
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        
        retries = Retry(
            total=10,
            backoff_factor=1,
            status_forcelist=[403, 429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        headers = {
            'Range': f'bytes={self.start_byte}-{self.end_byte}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
        }
        
        try:
            # Proxy NOT used for regular downloads - YouTube only!
            with session.get(self.url, headers=headers, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                
                with open(self.file_path, "ab") as f:
                    for chunk in response.iter_content(chunk_size=32768):
                        with QMutexLocker(self.mutex):
                            if self._is_stopped or self._is_paused:
                                return

                        if chunk:
                            f.write(chunk)
                            self.progress_signal.emit(self.chunk_id, len(chunk))
                            
            self.finished_signal.emit(self.chunk_id)
            
        except Exception as e:
            self.error_signal.emit(self.chunk_id, str(e))
        finally:
            session.close()

    def pause(self):
        with QMutexLocker(self.mutex):
            self._is_paused = True

    def stop(self):
        with QMutexLocker(self.mutex):
            self._is_stopped = True


class SingleThreadWorker(QThread):
    """Single-threaded downloader for simple files"""
    progress = Signal(int, int)
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, url, save_path, file_size):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.file_size = file_size
        self._stop_flag = False
        self.mutex = QMutex()
    
    def stop(self):
        with QMutexLocker(self.mutex):
            self._stop_flag = True
    
    def run(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            # Proxy NOT used for regular downloads - YouTube only!
            with requests.get(self.url, headers=headers, stream=True, timeout=(15, 120)) as r:
                r.raise_for_status()
                
                if self.file_size == 0:
                    self.file_size = int(r.headers.get('content-length', 0))
                
                downloaded = 0
                
                with open(self.save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        with QMutexLocker(self.mutex):
                            if self._stop_flag:
                                return
                        
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pct = int((downloaded / self.file_size) * 100) if self.file_size > 0 else 0
                            self.progress.emit(pct, downloaded)
                
                if os.path.exists(self.save_path) and os.path.getsize(self.save_path) > 0:
                    self.finished.emit()
                else:
                    self.error.emit("File empty")
                
        except Exception as e:
            self.error.emit(str(e))


class DownloadTask(QObject):
    """Main download task controller"""
    progress_updated = Signal(int, int, float)
    status_changed = Signal(str)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, url, save_path, file_size=0, threads=4, quality=None, itag=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.num_threads = threads
        self.workers = []
        self.file_size = file_size
        self.quality = quality
        self.itag = itag
        self.downloaded_bytes = 0
        self.status = "Idle"
        self.start_time = 0
        self.added_time = time.time()
        self.chunk_progress = {}
        
        self._active_worker = None
        
        self.save_dir = os.path.dirname(save_path)
        self.file_name = os.path.basename(save_path)
        
        import sys
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(base_path)
            
        central_temp = os.path.join(base_path, "Temp")
        if os.path.exists(central_temp) and os.access(central_temp, os.W_OK):
            self.temp_dir = os.path.join(central_temp, self.file_name)
        else:
            self.temp_dir = os.path.join(self.save_dir, ".fdm_temp", self.file_name)
        
    def _prepare_temp_dir(self):
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            if os.name == 'nt':
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(os.path.dirname(self.temp_dir), 0x02)
                except:
                    pass

    def start_download(self):
        if self.status in ["Downloading", "Finished"]:
            return

        self.status = "Downloading"
        self.status_changed.emit("Downloading")
        self.start_time = time.time()
        self.downloaded_bytes = 0
        
        self._prepare_temp_dir()
        
        # YouTube - use yt-dlp with auto proxy
        if "youtube.com/watch" in self.url or "youtu.be/" in self.url:
            print(f"DEBUG: YouTube download. Quality={self.quality}, Itag={self.itag}")
            self._download_youtube()
            return
        
        # Direct stream (already extracted URL)
        if "googlevideo.com" in self.url:
            # This shouldn't happen normally, but handle it
            self._download_youtube()
            return
        
        # Standard download
        if self.file_size <= 0:
            try:
                # Proxy NOT used for regular downloads - YouTube only!
                head = requests.head(self.url, allow_redirects=True, timeout=10)
                self.file_size = int(head.headers.get('content-length', 0))
                if self.file_size == 0:
                    self.start_single_thread()
                    return
            except Exception as e:
                self.error_occurred.emit(f"Failed: {e}")
                self.status = "Error"
                self.status_changed.emit("Error")
                return
        
        self._start_multi_thread_download()

    def _start_multi_thread_download(self):
        chunk_size = self.file_size // self.num_threads
        
        for i in range(self.num_threads):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < self.num_threads - 1 else self.file_size - 1
            
            part_path = os.path.join(self.temp_dir, f"part_{i}")
            
            current_size = os.path.getsize(part_path) if os.path.exists(part_path) else 0
            self.chunk_progress[i] = current_size
            
            resume_start = start + current_size
            if resume_start > end:
                continue
                
            worker = DownloadWorker(self.url, resume_start, end, i, part_path)
            worker.progress_signal.connect(self._on_worker_progress)
            worker.finished_signal.connect(self._on_worker_finished)
            worker.error_signal.connect(self._on_worker_error)
            self.workers.append(worker)
            worker.start()

    # ═══════════════════════════════════════════════════════════════════════════
    #                         YOUTUBE
    # ═══════════════════════════════════════════════════════════════════════════

    def _download_youtube(self):
        print("DEBUG: Starting YouTube download with auto-proxy...")
        self._try_ytdlp()

    def _try_ytdlp(self):
        self.ytdlp_worker = YtDlpWorker(self.url, self.save_path, self.itag, self.quality)
        self.ytdlp_worker.progress_signal.connect(self._on_ytdlp_progress)
        self.ytdlp_worker.finished_signal.connect(self._on_ytdlp_finished)
        self.ytdlp_worker.error_signal.connect(self._on_ytdlp_error)
        self.ytdlp_worker.status_signal.connect(self._on_ytdlp_status)
        self._active_worker = self.ytdlp_worker
        self.ytdlp_worker.start()
    
    def _on_ytdlp_status(self, status):
        """Handle status updates from yt-dlp worker"""
        print(f"DEBUG: yt-dlp status: {status}")
        self.status_changed.emit(status)
    
    def _on_ytdlp_progress(self, progress):
        elapsed = time.time() - self.start_time if self.start_time > 0 else 1
        if self.file_size > 0:
            self.downloaded_bytes = int((progress / 100) * self.file_size)
        speed = self.downloaded_bytes / elapsed if elapsed > 0 else 0
        eta = (self.file_size - self.downloaded_bytes) / speed if speed > 0 else 0
        self.progress_updated.emit(progress, int(speed), eta)
    
    def _on_ytdlp_finished(self):
        self._active_worker = None
        
        save_dir = os.path.dirname(self.save_path)
        base_name = os.path.splitext(os.path.basename(self.save_path))[0]
        
        for ext in ['.mp4', '.mkv', '.webm', '']:
            check = self.save_path if ext == '' else os.path.join(save_dir, base_name + ext)
            if os.path.exists(check) and os.path.getsize(check) > 0:
                self.save_path = check
                self.file_size = os.path.getsize(check)
                self.downloaded_bytes = self.file_size
                self.progress_updated.emit(100, 0, 0)
                self.status = "Finished"
                self.status_changed.emit("Finished")
                self.finished.emit()
                return
        
        self.status = "Error"
        self.status_changed.emit("Error")
        self.error_occurred.emit("File not found after download")
    
    def _on_ytdlp_error(self, error):
        self._active_worker = None
        print(f"DEBUG: yt-dlp error: {error}")
        
        error_messages = {
            "YT_DLP_NOT_INSTALLED": (
                "yt-dlp is not installed\n\n"
                "Install yt-dlp to download YouTube videos:\n\n"
                "pip install yt-dlp\n\n"
                "Or download from: https://github.com/yt-dlp/yt-dlp"
            ),
            "PROXY_UNAVAILABLE": (
                "No working proxies available\n\n"
                "Your network blocks YouTube and proxy sources.\n\n"
                "Try:\n"
                "• Use a VPN application\n"
                "• Configure a manual proxy in Settings\n"
                "• Try again later"
            ),
            "DOWNLOAD_FAILED_ALL_PROXIES": (
                "YouTube download failed\n\n"
                "Tried multiple proxies but none worked.\n\n"
                "Your network has strong restrictions.\n\n"
                "Try:\n"
                "• Use a VPN application\n"
                "• Configure a reliable proxy in Settings\n"
                "• Download on a different network"
            ),
        }
        
        msg = error_messages.get(error, f"Download failed: {error}")
        
        self.status = "Error"
        self.status_changed.emit("Error")
        self.error_occurred.emit(msg)

    # ═══════════════════════════════════════════════════════════════════════════
    #                         STANDARD
    # ═══════════════════════════════════════════════════════════════════════════

    def start_download_standard(self):
        if self.file_size <= 0:
            try:
                # Proxy NOT used for regular downloads - YouTube only!
                head = requests.head(self.url, allow_redirects=True, timeout=10)
                self.file_size = int(head.headers.get('content-length', 0))
                if self.file_size == 0:
                    self.start_single_thread()
                    return
            except Exception as e:
                self.error_occurred.emit(f"Failed: {e}")
                self.status = "Error"
                self.status_changed.emit("Error")
                return

        self._start_multi_thread_download()

    def _on_worker_progress(self, chunk_id, bytes_count):
        self.chunk_progress[chunk_id] = self.chunk_progress.get(chunk_id, 0) + bytes_count
        total = sum(self.chunk_progress.values())
        self.downloaded_bytes = total
        
        elapsed = time.time() - self.start_time
        speed = total / elapsed if elapsed > 0 else 0
        pct = int((total / self.file_size) * 100) if self.file_size > 0 else 0
        eta = (self.file_size - total) / speed if speed > 0 else 0
        
        self.progress_updated.emit(pct, int(speed), eta)
        
        if total >= self.file_size:
            self.merge_parts()

    def _on_worker_finished(self, chunk_id):
        pass

    def _on_worker_error(self, chunk_id, error):
        print(f"DEBUG: Worker {chunk_id} error: {error}")

    def merge_parts(self):
        if self.status in ["Merging", "Finished"]:
            return
            
        for w in self.workers:
            w.wait()

        self.status = "Merging"
        self.status_changed.emit("Merging")
        
        try:
            with open(self.save_path, "wb") as out:
                for i in range(self.num_threads):
                    part = os.path.join(self.temp_dir, f"part_{i}")
                    if os.path.exists(part):
                        with open(part, "rb") as inp:
                            while chunk := inp.read(1024 * 1024):
                                out.write(chunk)
            
            self.delete_temp_files()
            self.status = "Finished"
            self.status_changed.emit("Finished")
            self.finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(f"Merge error: {e}")
            self.status = "Error"
            self.status_changed.emit("Error")

    def start_single_thread(self):
        self.single_worker = SingleThreadWorker(self.url, self.save_path, self.file_size)
        self.single_worker.progress.connect(lambda pct, dl: self.progress_updated.emit(pct, 0, 0))
        self.single_worker.finished.connect(self._on_single_finished)
        self.single_worker.error.connect(self._on_single_error)
        self._active_worker = self.single_worker
        self.single_worker.start()
    
    def _on_single_finished(self):
        self._active_worker = None
        self.status = "Finished"
        self.status_changed.emit("Finished")
        self.finished.emit()
    
    def _on_single_error(self, error):
        self._active_worker = None
        self.status = "Error"
        self.status_changed.emit("Error")
        self.error_occurred.emit(error)

    # ═══════════════════════════════════════════════════════════════════════════
    #                         CONTROL
    # ═══════════════════════════════════════════════════════════════════════════

    def pause(self):
        self.status = "Paused"
        self.status_changed.emit("Paused")
        if self._active_worker and hasattr(self._active_worker, 'pause'):
            self._active_worker.pause()
        elif self._active_worker and hasattr(self._active_worker, 'stop'):
            self._active_worker.stop()
        for w in self.workers:
            w.pause()
            
    def resume(self):
        if self.status in ["Paused", "Stopped", "Queued", "Idle", "Error"]:
            self.start_download()

    def stop(self):
        self.status = "Stopped"
        self.status_changed.emit("Stopped")
        if self._active_worker and hasattr(self._active_worker, 'stop'):
            self._active_worker.stop()
        for w in self.workers:
            w.stop()
            w.wait()
            
    def delete_temp_files(self):
        import shutil
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
             
    def delete_all_files(self):
        self.stop()
        try:
            self.delete_temp_files()
        except:
            pass
        try:
            if os.path.exists(self.save_path):
                os.remove(self.save_path)
        except:
            pass