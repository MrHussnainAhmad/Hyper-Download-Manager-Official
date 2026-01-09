import requests
import os
import time
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QProgressBar, QFileDialog, 
                               QGridLayout, QWidget, QSpacerItem, QSizePolicy,
                               QGraphicsDropShadowEffect, QFrame, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QStandardPaths, QSize, QPropertyAnimation, QUrl
from PySide6.QtGui import QColor, QFont, QPixmap, QDesktopServices

from ui.theme_manager import theme
from ui.icons import IconType, IconProvider, get_pixmap
from ui.components import (IconButton, IconLabel, Card, AnimatedProgressBar, 
                           StatusBadge, SectionHeader, Divider)
from utils.helpers import format_bytes, format_speed, format_time


# ═══════════════════════════════════════════════════════════════════════════════
#                           METADATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════════

class MetadataFetcher(QThread):
    """Fetches video/file metadata with automatic proxy support for YouTube"""
    finished = Signal(str, int)
    status = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def _get_working_proxy(self):
        """Get a working proxy URL from ProxyManager"""
        try:
            from core.proxy_manager import proxy_manager
            
            # Refresh proxies if needed
            if proxy_manager.needs_refresh() or proxy_manager.get_working_count() == 0:
                self.status.emit("Finding proxies...")
                
                import threading
                event = threading.Event()
                
                def on_done(success):
                    event.set()
                
                proxy_manager.refresh_proxies(callback=on_done)
                event.wait(timeout=60)
            
            return proxy_manager.get_proxy()
        except ImportError:
            print("DEBUG: proxy_manager not available")
            return None
        except Exception as e:
            print(f"DEBUG: Proxy manager error: {e}")
            return None

    def _try_ytdlp_metadata(self, proxy_url=None):
        """
        Try to get metadata using yt-dlp.
        Returns: (title, size) or raises exception
        """
        import subprocess
        
        cmd = [
            "yt-dlp",
            "--print", "%(title)s|||%(filesize,filesize_approx)s",
            "--no-playlist",
            "--no-warnings",
            "--socket-timeout", "20",
        ]
        
        if proxy_url:
            cmd.extend(["--proxy", proxy_url])
        
        cmd.append(self.url)
        
        proxy_display = "direct" if not proxy_url else proxy_url.split('@')[-1][:30]
        print(f"DEBUG: yt-dlp metadata ({proxy_display}): {' '.join(cmd[:5])}...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=35,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.lower() if result.stderr else ""
        
        # Check for blocking errors
        blocking_indicators = [
            "try refreshing",
            "sign in to confirm",
            "blocked",
            "http error 403",
            "403 forbidden",
            "connection refused",
            "connection reset",
            "timed out",
            "urlopen error",
            "proxy error",
            "unable to download webpage",
        ]
        
        for indicator in blocking_indicators:
            if indicator in stderr:
                print(f"DEBUG: Detected blocking: {indicator}")
                raise ConnectionError(f"YouTube blocked: {indicator}")
        
        if result.returncode == 0 and stdout:
            parts = stdout.split('|||')
            if len(parts) >= 1 and parts[0]:
                title = parts[0].strip()
                size = 0
                if len(parts) >= 2:
                    try:
                        size_str = parts[1].strip()
                        if size_str and size_str.lower() not in ['na', 'none', '']:
                            size = int(float(size_str))
                    except:
                        pass
                return title, size
        
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed with code {result.returncode}")
        
        return None, 0

    def run(self):
        try:
            print(f"DEBUG: MetadataFetcher started for: {self.url[:60]}...")
            
            def sanitize(n):
                """Clean filename of invalid characters"""
                if not n:
                    return ""
                keep = (" ", ".", "_", "-", "(", ")", "[", "]")
                result = "".join(c for c in n if c.isalnum() or c in keep).strip()
                # Remove multiple spaces
                while "  " in result:
                    result = result.replace("  ", " ")
                return result[:200]  # Limit length

            from urllib.parse import urlparse, unquote, parse_qs
            parsed = urlparse(self.url)
            
            name = "download.file"
            size = 0
            
            # ═══════════════════════════════════════════════════════════════════
            # YOUTUBE HANDLING
            # ═══════════════════════════════════════════════════════════════════
            if "youtube.com/watch" in self.url or "youtu.be/" in self.url:
                self.status.emit("Getting video info...")
                
                # Attempt 1: Direct connection (no proxy)
                try:
                    print("DEBUG: Attempt 1 - Direct yt-dlp...")
                    self.status.emit("Fetching video info...")
                    title, size = self._try_ytdlp_metadata(proxy_url=None)
                    
                    if title:
                        name = sanitize(title) + ".mp4"
                        print(f"DEBUG: Direct success: {name}, {size}")
                        self.finished.emit(name, size)
                        return
                        
                except ConnectionError as e:
                    print(f"DEBUG: Direct blocked: {e}")
                    self.status.emit("Direct connection blocked...")
                except subprocess.TimeoutExpired:
                    print("DEBUG: Direct connection timed out")
                    self.status.emit("Connection timed out...")
                except FileNotFoundError:
                    print("DEBUG: yt-dlp not installed!")
                    self.status.emit("yt-dlp not found")
                    self.finished.emit("youtube_video.mp4", 0)
                    return
                except Exception as e:
                    print(f"DEBUG: Direct attempt failed: {e}")
                
                # Attempt 2: First proxy
                self.status.emit("Finding proxy...")
                proxy_url = self._get_working_proxy()
                
                if proxy_url:
                    try:
                        print(f"DEBUG: Attempt 2 - Proxy: {proxy_url[:40]}...")
                        self.status.emit("Using proxy for info...")
                        title, size = self._try_ytdlp_metadata(proxy_url=proxy_url)
                        
                        if title:
                            name = sanitize(title) + ".mp4"
                            print(f"DEBUG: Proxy success: {name}, {size}")
                            
                            # Mark proxy as good
                            try:
                                from core.proxy_manager import proxy_manager
                                proxy_manager.mark_proxy_success(proxy_url)
                            except:
                                pass
                            
                            self.finished.emit(name, size)
                            return
                            
                    except Exception as e:
                        print(f"DEBUG: Proxy 1 failed: {e}")
                        try:
                            from core.proxy_manager import proxy_manager
                            proxy_manager.mark_proxy_failed(proxy_url)
                        except:
                            pass
                
                # Attempt 3: Second proxy
                self.status.emit("Trying another proxy...")
                proxy_url = self._get_working_proxy()
                
                if proxy_url:
                    try:
                        print(f"DEBUG: Attempt 3 - Proxy: {proxy_url[:40]}...")
                        title, size = self._try_ytdlp_metadata(proxy_url=proxy_url)
                        
                        if title:
                            name = sanitize(title) + ".mp4"
                            print(f"DEBUG: Proxy 2 success: {name}")
                            
                            try:
                                from core.proxy_manager import proxy_manager
                                proxy_manager.mark_proxy_success(proxy_url)
                            except:
                                pass
                            
                            self.finished.emit(name, size)
                            return
                            
                    except Exception as e:
                        print(f"DEBUG: Proxy 2 failed: {e}")
                        try:
                            from core.proxy_manager import proxy_manager
                            proxy_manager.mark_proxy_failed(proxy_url)
                        except:
                            pass
                
                # Attempt 4: Third proxy
                self.status.emit("Last proxy attempt...")
                proxy_url = self._get_working_proxy()
                
                if proxy_url:
                    try:
                        print(f"DEBUG: Attempt 4 - Proxy: {proxy_url[:40]}...")
                        title, size = self._try_ytdlp_metadata(proxy_url=proxy_url)
                        
                        if title:
                            name = sanitize(title) + ".mp4"
                            self.finished.emit(name, size)
                            return
                    except:
                        pass
                
                # All attempts failed - use fallback name
                print("DEBUG: All metadata attempts failed, using fallback name")
                self.status.emit("Using default name...")
                
                # Try to extract video ID for better naming
                video_id = ""
                try:
                    if "v=" in self.url:
                        video_id = self.url.split("v=")[1].split("&")[0][:11]
                    elif "youtu.be/" in self.url:
                        video_id = self.url.split("youtu.be/")[1].split("?")[0][:11]
                except:
                    pass
                
                if video_id:
                    name = f"youtube_{video_id}.mp4"
                else:
                    name = f"youtube_video_{int(time.time())}.mp4"
                
                self.finished.emit(name, 0)
                return
            
            # ═══════════════════════════════════════════════════════════════════
            # NON-YOUTUBE URLs
            # ═══════════════════════════════════════════════════════════════════
            
            self.status.emit("Getting file info...")
            
            # Check for 'clen' in URL (common in direct video streams)
            query = parse_qs(parsed.query)
            if 'clen' in query:
                try:
                    size = int(query['clen'][0])
                    print(f"DEBUG: Found size in URL (clen): {size}")
                except:
                    pass

            # Try to extract name from URL path
            path_name = parsed.path.split('/')[-1]
            if path_name:
                decoded_name = unquote(path_name)
                # Use if it looks like a real filename
                if "videoplayback" not in decoded_name.lower() and "." in decoded_name:
                    name = decoded_name
                    print(f"DEBUG: Name from URL path: {name}")

            # Network request for additional metadata
            if size == 0 or name == "download.file":
                try:
                    print("DEBUG: Fetching headers...")
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'identity',  # Don't use gzip for range requests
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    # GitHub releases don't support HEAD properly - use GET with Range
                    is_github = 'github.com' in self.url.lower() and '/releases/download/' in self.url.lower()
                    
                    if is_github:
                        print("DEBUG: GitHub release detected - using GET with Range header...")
                        print(f"DEBUG: Full requesting URL: {self.url}")  # FULL URL
                        headers['Range'] = 'bytes=0-1'
                        response = requests.get(self.url, headers=headers, stream=True, timeout=8, allow_redirects=True)
                        
                        print(f"DEBUG: Final URL: {response.url[:100]}")
                        print(f"DEBUG: Status code: {response.status_code}")
                        
                        if response.status_code in [200, 206]:  # 206 = Partial Content
                            # Get size from Content-Range or Content-Length
                            if 'Content-Range' in response.headers:
                                # Format: bytes 0-1/TOTAL_SIZE
                                size = int(response.headers['Content-Range'].split('/')[-1])
                                print(f"DEBUG: Size from Content-Range: {size}")
                            elif 'Content-Length' in response.headers:
                                size = int(response.headers['Content-Length'])
                                print(f"DEBUG: Size from Content-Length: {size}")
                            
                            # Get filename from Content-Disposition
                            if 'Content-Disposition' in response.headers:
                                import re
                                cd = response.headers['Content-Disposition']
                                fname_match = re.findall(r'filename[*]?=["\']?([^"\';]+)', cd)
                                if fname_match:
                                    name = unquote(fname_match[0].strip())
                                    print(f"DEBUG: Name from Content-Disposition: {name}")
                        else:
                            print(f"DEBUG: ⚠️ HTTP error {response.status_code}")
                        
                        response.close()
                    else:
                        # Standard HEAD request for non-GitHub URLs
                        head = requests.head(
                            self.url, 
                            headers=headers, 
                            allow_redirects=True, 
                            timeout=8
                        )
                        
                        print(f"DEBUG: Final URL after redirects: {head.url[:100]}")
                        print(f"DEBUG: Status code: {head.status_code}")
                        print(f"DEBUG: Content-Length header: {head.headers.get('content-length', 'NOT FOUND')}")
                        
                        # Check for errors
                        if head.status_code == 404:
                            print("DEBUG: ⚠️ File not found (404) - URL may be invalid or private")
                            size = 0
                        elif head.status_code >= 400:
                            print(f"DEBUG: ⚠️ HTTP error {head.status_code}")
                            size = 0
                        
                        # Try Content-Disposition header for filename
                        if head.status_code == 200 and "Content-Disposition" in head.headers:
                            import re
                            cd = head.headers["Content-Disposition"]
                            fname_match = re.findall(r'filename[*]?=["\']?([^"\';]+)', cd)
                            if fname_match:
                                clean_name = unquote(fname_match[0].strip())
                                if clean_name:
                                    name = clean_name
                                    print(f"DEBUG: Name from Content-Disposition: {name}")
                        
                        # Get size from Content-Length
                        if size == 0 and head.status_code == 200:
                            content_len = head.headers.get('content-length', '0')
                            try:
                                size = int(content_len)
                                if size > 0:
                                    print(f"DEBUG: Size from headers: {size}")
                            except (ValueError, TypeError):
                                print(f"DEBUG: Failed to parse content-length: '{content_len}'")
                        
                except requests.exceptions.Timeout:
                    print("DEBUG: HEAD request timed out")
                except Exception as e:
                    print(f"DEBUG: HEAD request failed: {e}")
                    
                    # Fallback: Try GET with Range header
                    if size == 0:
                        try:
                            headers = {
                                'User-Agent': 'Mozilla/5.0',
                                'Range': 'bytes=0-1'
                            }
                            with requests.get(self.url, headers=headers, stream=True, timeout=8) as r:
                                if "Content-Range" in r.headers:
                                    # Format: bytes 0-1/TOTAL
                                    size = int(r.headers["Content-Range"].split('/')[-1])
                                    print(f"DEBUG: Size from Content-Range: {size}")
                        except:
                            pass

            # Final cleanup
            if "videoplayback" in name.lower() or name == "download.file":
                if "googlevideo" in self.url.lower():
                    name = f"video_{int(time.time())}.mp4"
            
            name = sanitize(name)
            if not name:
                name = f"download_{int(time.time())}"
            
            # Ensure extension
            if '.' not in name:
                # Guess extension from Content-Type if we had it
                name += ".mp4" if "video" in self.url.lower() else ".file"
                
            print(f"DEBUG: MetadataFetcher complete: {name}, {size}")
            self.finished.emit(name, size)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"CRITICAL ERROR in MetadataFetcher: {e}")
            self.finished.emit(f"download_{int(time.time())}.mp4", 0)


# ═══════════════════════════════════════════════════════════════════════════════
#                            BASE DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class BaseDialog(QDialog):
    """Base dialog with theme support and custom title bar"""
    
    def __init__(self, parent=None, title: str = "Dialog", 
                 icon_type: IconType = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self._icon_type = icon_type
        self._drag_pos = None
        
        # Main container for shadow effect
        self.container = Card(self, shadow=True)
        
        # Container layout
        self.container_layout = QVBoxLayout(self)
        self.container_layout.setContentsMargins(24, 24, 24, 24)
        self.container_layout.addWidget(self.container)
        
        # Inner layout
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(28, 24, 28, 28)
        self.main_layout.setSpacing(16)
        
        # Title bar
        self._create_title_bar(title, icon_type)
        
        self.apply_theme()
        
    def _create_title_bar(self, title: str, icon_type: IconType = None):
        self.title_bar_layout = QHBoxLayout()
        self.title_bar_layout.setSpacing(12)
        
        # Optional icon
        if icon_type:
            self.title_icon = IconLabel(icon_type, 28)
            self.title_bar_layout.addWidget(self.title_icon)
        
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
        self.title_bar_layout.addWidget(self.title_label)
        
        self.title_bar_layout.addStretch()
        
        self.close_btn = IconButton(IconType.CLOSE, variant="icon", icon_size=16)
        self.close_btn.setFixedSize(36, 36)
        self.close_btn.clicked.connect(self.reject)
        self.title_bar_layout.addWidget(self.close_btn)
        
        self.main_layout.addLayout(self.title_bar_layout)
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(theme.get_dialog_stylesheet())
        self.container.apply_theme()
        self.title_label.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
        self.close_btn.apply_theme()
        if hasattr(self, 'title_icon'):
            self.title_icon.apply_theme()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
    
    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ═══════════════════════════════════════════════════════════════════════════════
#                         NEW DOWNLOAD DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class NewDownloadDialog(BaseDialog):
    """Dialog for entering a new download URL"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "Add New Download", IconType.ADD)
        self.resize(520, 200)
        
        # URL Section
        url_section = SectionHeader("DOWNLOAD URL", IconType.LINK)
        self.main_layout.addWidget(url_section)
        
        # URL Input with icon
        url_container = QHBoxLayout()
        url_container.setSpacing(14)
        
        self.url_icon = IconLabel(IconType.GLOBE, 24)
        url_container.addWidget(self.url_icon)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste download URL here...")
        self.url_input.setMinimumHeight(52)
        self.url_input.setFont(QFont("Segoe UI", 12))
        url_container.addWidget(self.url_input)
        
        self.main_layout.addLayout(url_container)
        
        self.main_layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)
        btn_layout.addStretch()
        
        self.cancel_btn = IconButton(IconType.CLOSE, "Cancel", variant="secondary")
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = IconButton(IconType.ARROW_RIGHT, "Continue", variant="primary")
        self.ok_btn.setMinimumWidth(140)
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        btn_layout.addWidget(self.ok_btn)
        
        self.main_layout.addLayout(btn_layout)
        
        self.apply_theme()

    def get_url(self):
        return self.url_input.text().strip()
        
    def apply_theme(self):
        super().apply_theme()
        t = theme.current
        
        # Guard against being called before widgets are created
        if hasattr(self, 'url_icon'):
            self.url_icon.apply_theme()
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.apply_theme()
        if hasattr(self, 'ok_btn'):
            self.ok_btn.apply_theme()
        
        # Style URL input
        if hasattr(self, 'url_input'):
            self.url_input.setStyleSheet(f"""
                QLineEdit {{
                    background: {t['bg_tertiary']};
                    border: 2px solid {t['border_primary']};
                    border-radius: 10px;
                    padding: 12px 16px;
                    color: {t['text_primary']};
                    font-size: 13px;
                }}
                QLineEdit:focus {{
                    border-color: {t['accent_primary']};
                }}
                QLineEdit::placeholder {{
                    color: {t['text_muted']};
                }}
            """)


# ═══════════════════════════════════════════════════════════════════════════════
#                      DOWNLOAD CONFIRMATION DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class DownloadConfirmationDialog(BaseDialog):
    """Dialog to confirm download details before starting"""
    
    def __init__(self, url, parent=None, filename=None, filesize=0, quality=None, itag=None):
        super().__init__(parent, "Confirm Download", IconType.DOWNLOAD)
        self.resize(580, 420)
        
        self.url = url
        self.auto_start = True
        self._detected_size = 0
        self._fetcher = None
        
        # Store quality/itag from extension
        self.quality = quality
        self.itag = itag
        
        print(f"DEBUG: DownloadConfirmationDialog for: {url[:50]}...")
        print(f"DEBUG: Quality={quality}, Itag={itag}")
        
        # Parse filesize safely
        try:
            filesize = int(filesize) if filesize else 0
        except:
            filesize = 0
        self._detected_size = filesize
        
        # URL display (truncated)
        display_url = url
        if len(url) > 50:
            display_url = url[:50] + "..."
        
        t = theme.current
        
        # File Info Section
        info_section = SectionHeader("FILE INFORMATION", IconType.FILE)
        self.main_layout.addWidget(info_section)
        
        # Info Grid
        info_grid = QGridLayout()
        info_grid.setSpacing(14)
        info_grid.setColumnMinimumWidth(0, 90)
        
        # URL Row
        url_label = QLabel("URL")
        url_label.setStyleSheet(f"color: {t['text_muted']}; font-weight: 600;")
        info_grid.addWidget(url_label, 0, 0)
        
        self.url_edit = QLineEdit(display_url)
        self.url_edit.setReadOnly(True)
        self.url_edit.setToolTip(url)
        info_grid.addWidget(self.url_edit, 0, 1)
        
        # Name Row
        name_label = QLabel("File Name")
        name_label.setStyleSheet(f"color: {t['text_muted']}; font-weight: 600;")
        info_grid.addWidget(name_label, 1, 0)
        
        initial_name = filename if filename else "Fetching..."
        self.name_edit = QLineEdit(initial_name)
        info_grid.addWidget(self.name_edit, 1, 1)
        
        # Quality Row (NEW - shows selected quality)
        quality_label = QLabel("Quality")
        quality_label.setStyleSheet(f"color: {t['text_muted']}; font-weight: 600;")
        info_grid.addWidget(quality_label, 2, 0)
        
        quality_display = quality if quality else "Best Available"
        if itag:
            quality_display += f" (itag: {itag})"
        self.quality_value = QLabel(quality_display)
        self.quality_value.setStyleSheet(f"color: {t['accent_primary']}; font-weight: 600;")
        info_grid.addWidget(self.quality_value, 2, 1)
        
        # Size Row
        size_label = QLabel("Size")
        size_label.setStyleSheet(f"color: {t['text_muted']}; font-weight: 600;")
        info_grid.addWidget(size_label, 3, 0)
        
        size_layout = QHBoxLayout()
        self.size_icon = IconLabel(IconType.STORAGE, 18)
        size_layout.addWidget(self.size_icon)
        
        size_text = format_bytes(filesize) if filesize > 0 else "Calculating..."
        self.size_value = QLabel(size_text)
        self.size_value.setStyleSheet(f"font-weight: 700; color: {t['accent_primary']};")
        size_layout.addWidget(self.size_value)
        size_layout.addStretch()
        
        info_grid.addLayout(size_layout, 3, 1)
        
        # Status Row
        status_label = QLabel("Status")
        status_label.setStyleSheet(f"color: {t['text_muted']}; font-weight: 600;")
        info_grid.addWidget(status_label, 4, 0)
        
        self.status_value = QLabel("Ready")
        self.status_value.setStyleSheet(f"color: {t['text_secondary']}; font-style: italic;")
        info_grid.addWidget(self.status_value, 4, 1)
        
        self.main_layout.addLayout(info_grid)
        
        # Save Location Section
        self.main_layout.addWidget(Divider())
        
        location_section = SectionHeader("SAVE LOCATION", IconType.FOLDER)
        self.main_layout.addWidget(location_section)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(14)
        
        dl_loc = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self.path_edit = QLineEdit(dl_loc)
        path_layout.addWidget(self.path_edit)
        
        self.browse_btn = IconButton(IconType.FOLDER, "Browse", variant="secondary")
        self.browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.browse_btn)
        
        self.main_layout.addLayout(path_layout)
        
        self.main_layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)
        
        self.cancel_btn = IconButton(IconType.CLOSE, "Cancel", variant="ghost")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        btn_layout.addStretch()
        
        self.later_btn = IconButton(IconType.CLOCK, "Download Later", variant="secondary")
        self.later_btn.setMinimumWidth(150)
        self.later_btn.clicked.connect(self.on_download_later)
        btn_layout.addWidget(self.later_btn)
        
        self.now_btn = IconButton(IconType.DOWNLOAD, "Start Download", variant="primary")
        self.now_btn.setMinimumWidth(160)
        self.now_btn.clicked.connect(self.on_download_now)
        btn_layout.addWidget(self.now_btn)
        
        self.main_layout.addLayout(btn_layout)
        
        self.apply_theme()
        
        # Start metadata fetcher
        self._start_metadata_fetch()

    def _start_metadata_fetch(self):
        """Start fetching metadata in background"""
        self._fetcher = MetadataFetcher(self.url)
        self._fetcher.finished.connect(self._on_metadata_ready)
        self._fetcher.status.connect(self._on_metadata_status)
        self._fetcher.start()
    
    def _on_metadata_status(self, status):
        """Update status label with fetcher progress"""
        self.status_value.setText(status)
    
    def _on_metadata_ready(self, name, size):
        """Handle metadata fetch completion"""
        print(f"DEBUG: Metadata ready: name={name}, size={size}")
        print(f"DEBUG: Current size in dialog: {self._detected_size}")
        
        t = theme.current
        current_name = self.name_edit.text()
        
        # Update name if we got a better one
        if current_name in ["Fetching...", "download.file", ""] or "download_" in current_name:
            if name and name != "download.file":
                self.name_edit.setText(name)
        
        # CRITICAL: Only update size if we DON'T already have a valid size from extension!
        # The extension provides the size for the SELECTED quality (e.g., 1080p = 200MB)
        # MetadataFetcher uses default quality (best/4K = 940MB) which would be WRONG!
        if self._detected_size <= 0 and size > 0:
            # We don't have a size yet, use the fetched one
            self._detected_size = size
            self.size_value.setText(format_bytes(size))
            self.size_value.setStyleSheet(f"font-weight: 700; color: {t['accent_primary']};")
            print(f"DEBUG: Updated size from metadata: {size}")
        elif self._detected_size > 0:
            # We already have size from extension - DON'T OVERWRITE IT!
            print(f"DEBUG: Keeping extension size: {self._detected_size} (ignoring metadata size: {size})")
        elif self.size_value.text() == "Calculating...":
            self.size_value.setText("Unknown")
            self.size_value.setStyleSheet(f"font-weight: 500; color: {t['text_muted']};")
        
        # Update status
        if name and name != "download.file":
            self.status_value.setText("Ready to download")
            self.status_value.setStyleSheet(f"color: {t['accent_success']};")
        else:
            self.status_value.setText("Ready (metadata limited)")
            self.status_value.setStyleSheet(f"color: {t['text_secondary']};")

    def browse_folder(self):
        dir_ = QFileDialog.getExistingDirectory(
            self, "Select Directory", self.path_edit.text()
        )
        if dir_:
            self.path_edit.setText(dir_)

    def on_download_now(self):
        self.auto_start = True
        self.accept()

    def on_download_later(self):
        self.auto_start = False
        self.accept()

    def get_data(self):
        """Return download data tuple including quality/itag"""
        filename = self.name_edit.text().strip()
        if not filename:
            filename = f"download_{int(time.time())}.file"
        
        save_path = os.path.join(self.path_edit.text(), filename)
        
        # Return quality and itag too!
        return (
            self.url, 
            save_path, 
            self.auto_start, 
            self._detected_size,
            self.quality,  # Add quality
            self.itag      # Add itag
        )
    
    def closeEvent(self, event):
        """Cleanup on close"""
        if self._fetcher and self._fetcher.isRunning():
            self._fetcher.quit()
            self._fetcher.wait(1000)
        super().closeEvent(event)
        
    def apply_theme(self):
        super().apply_theme()
        t = theme.current
        
        if hasattr(self, 'size_icon'):
            self.size_icon.apply_theme()
        if hasattr(self, 'browse_btn'):
            self.browse_btn.apply_theme()
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.apply_theme()
        if hasattr(self, 'later_btn'):
            self.later_btn.apply_theme()
        if hasattr(self, 'now_btn'):
            self.now_btn.apply_theme()
        
        # Style inputs
        input_style = f"""
            QLineEdit {{
                background: {t['bg_tertiary']};
                border: 1px solid {t['border_primary']};
                border-radius: 8px;
                padding: 10px 14px;
                color: {t['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {t['accent_primary']};
            }}
            QLineEdit:read-only {{
                background: {t['bg_secondary']};
                color: {t['text_secondary']};
            }}
        """
        
        if hasattr(self, 'url_edit'):
            self.url_edit.setStyleSheet(input_style)
        if hasattr(self, 'name_edit'):
            self.name_edit.setStyleSheet(input_style)
        if hasattr(self, 'path_edit'):
            self.path_edit.setStyleSheet(input_style)


# ═══════════════════════════════════════════════════════════════════════════════
#                         DOWNLOAD COMPLETE DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class DownloadedDialog(BaseDialog):
    """Dialog shown when a download completes"""
    
    def __init__(self, task, parent=None):
        super().__init__(parent, "Download Complete", IconType.COMPLETE)
        self.task = task
        self.resize(500, 320)
        
        t = theme.current
        
        # Centered Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        
        # Hero Icon (Large Checkmark)
        icon_container = QFrame()
        icon_container.setFixedSize(96, 96)
        bg_color = QColor(t['accent_success'])
        bg_color.setAlpha(30)
        icon_container.setStyleSheet(f"""
            background-color: {bg_color.name(QColor.HexArgb)}; 
            border-radius: 48px;
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        success_icon = IconLabel(IconType.COMPLETE, 48)
        success_icon.set_color(t['accent_success'])
        icon_layout.addWidget(success_icon)
        
        layout.addWidget(icon_container, 0, Qt.AlignCenter)
        
        # Text Info
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        title = QLabel("Download Complete")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {t['text_primary']};")
        text_layout.addWidget(title)
        
        # File Name
        name_label = QLabel(os.path.basename(task.save_path))
        name_label.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        name_label.setStyleSheet(f"color: {t['text_secondary']};")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        text_layout.addWidget(name_label)
        
        # Path
        path_label = QLabel(os.path.dirname(task.save_path))
        path_label.setFont(QFont("Segoe UI", 10))
        path_label.setStyleSheet(f"color: {t['text_muted']};")
        path_label.setAlignment(Qt.AlignCenter)
        path_label.setWordWrap(True)
        text_layout.addWidget(path_label)
        
        layout.addLayout(text_layout)
        
        self.main_layout.addLayout(layout)
        self.main_layout.addStretch()
        
        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.addStretch()
        
        self.folder_btn = IconButton(IconType.FOLDER, "Show in Folder", variant="secondary")
        self.folder_btn.setMinimumWidth(140)
        self.folder_btn.clicked.connect(self.open_folder)
        btn_layout.addWidget(self.folder_btn)
        
        self.open_btn = IconButton(IconType.FILE, "Open File", variant="primary")
        self.open_btn.setMinimumWidth(130)
        self.open_btn.clicked.connect(self.open_file)
        btn_layout.addWidget(self.open_btn)
        
        btn_layout.addStretch()
        
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addSpacing(16)
        
        self.apply_theme()

    def open_file(self):
        try:
            if os.path.exists(self.task.save_path):
                os.startfile(self.task.save_path)
            self.accept()
        except Exception as e:
            print(f"Error opening file: {e}")

    def open_folder(self):
        try:
            folder = os.path.dirname(self.task.save_path)
            if os.path.exists(folder):
                os.startfile(folder)
            self.accept()
        except Exception as e:
            print(f"Error opening folder: {e}")
    
    def apply_theme(self):
        super().apply_theme()
        if hasattr(self, 'folder_btn'):
            self.folder_btn.apply_theme()
        if hasattr(self, 'open_btn'):
            self.open_btn.apply_theme()


# ═══════════════════════════════════════════════════════════════════════════════
#                           PROGRESS DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressDialog(BaseDialog):
    """Dialog showing download progress"""
    
    def __init__(self, task, parent=None):
        super().__init__(parent, "Downloading...", IconType.DOWNLOAD)
        self.task = task
        self.resize(550, 500)
        
        t = theme.current
        
        # Main Layout
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # 1. File Name Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        # Icon container
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        bg_color = QColor(t['accent_primary'])
        bg_color.setAlpha(30)
        icon_container.setStyleSheet(f"""
            background-color: {bg_color.name(QColor.HexArgb)}; 
            border-radius: 24px;
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(IconLabel(IconType.FILE, 24), 0, Qt.AlignCenter)
        header_layout.addWidget(icon_container)
        
        # Title
        self.file_header = QLabel(os.path.basename(task.save_path))
        self.file_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.file_header.setWordWrap(True)
        self.file_header.setStyleSheet(f"color: {t['text_primary']};")
        header_layout.addWidget(self.file_header)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        layout.addSpacing(10)
        
        # 2. Details Grid
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)
        
        def add_row(row, label_text, value_widget):
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(f"color: {t['text_muted']}; font-weight: 500;")
            grid.addWidget(lbl, row, 0)
            grid.addWidget(value_widget, row, 1)

        # URL
        display_url = task.url[:50] + "..." if len(task.url) > 50 else task.url
        self.url_val = QLabel(display_url)
        self.url_val.setFont(QFont("Segoe UI", 10))
        self.url_val.setStyleSheet(f"color: {t['text_secondary']};")
        self.url_val.setWordWrap(True)
        self.url_val.setToolTip(task.url)
        add_row(0, "File URL:", self.url_val)
        
        # Size
        self.size_val = QLabel(format_bytes(task.file_size) if task.file_size > 0 else "Unknown")
        self.size_val.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.size_val.setStyleSheet(f"color: {t['text_primary']};")
        add_row(1, "File Size:", self.size_val)
        
        # Downloaded
        self.downloaded_val = QLabel("0 B")
        self.downloaded_val.setFont(QFont("Segoe UI", 10))
        self.downloaded_val.setStyleSheet(f"color: {t['accent_primary']};")
        add_row(2, "Downloaded:", self.downloaded_val)
        
        # Remaining
        self.remaining_val = QLabel("-")
        self.remaining_val.setFont(QFont("Segoe UI", 10))
        self.remaining_val.setStyleSheet(f"color: {t['text_secondary']};")
        add_row(3, "Remaining:", self.remaining_val)
        
        # ETA
        self.eta_val = QLabel("Calculating...")
        self.eta_val.setFont(QFont("Segoe UI", 10))
        self.eta_val.setStyleSheet(f"color: {t['text_secondary']};")
        add_row(4, "ETA:", self.eta_val)
        
        # Speed
        self.speed_val = QLabel("-")
        self.speed_val.setFont(QFont("Segoe UI", 10))
        self.speed_val.setStyleSheet(f"color: {t['accent_primary']};")
        add_row(5, "Transfer Rate:", self.speed_val)
        
        # Status (for proxy info)
        self.status_val = QLabel("Starting...")
        self.status_val.setFont(QFont("Segoe UI", 10))
        self.status_val.setStyleSheet(f"color: {t['text_muted']}; font-style: italic;")
        add_row(6, "Status:", self.status_val)

        layout.addLayout(grid)
        layout.addSpacing(16)
        
        # 3. Progress Bar
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        self.hide_btn = IconButton(IconType.MINIMIZE, "Hide", variant="ghost")
        self.hide_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.hide_btn)
        
        self.pause_btn = IconButton(IconType.PAUSE, "Pause", variant="secondary")
        self.pause_btn.setMinimumWidth(100)
        self.pause_btn.clicked.connect(self.toggle_pause)
        btn_layout.addWidget(self.pause_btn)

        self.cancel_btn = IconButton(IconType.CLOSE, "Cancel", variant="danger")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.cancel_download)
        btn_layout.addWidget(self.cancel_btn)
        
        self.main_layout.addLayout(layout)
        self.main_layout.addLayout(btn_layout)
        
        # Connect signals
        self.task.progress_updated.connect(self.update_stats)
        self.task.status_changed.connect(self.on_status_changed)
        self.task.finished.connect(self.on_finished)
        
        self.apply_theme()
    
    def on_status_changed(self, status):
        """Update status display"""
        self.status_val.setText(status)
        
    def update_stats(self, progress, speed, eta):
        t = theme.current
        
        # Update progress bar
        self.progress_bar.setValue(progress)
        
        # Update speed
        if speed > 0:
            self.speed_val.setText(format_speed(speed))
        
        # Update ETA
        if eta > 0:
            self.eta_val.setText(format_time(eta))
        elif progress >= 100:
            self.eta_val.setText("Complete")
        else:
            self.eta_val.setText("Calculating...")
        
        current_size = self.task.downloaded_bytes
        total_size = self.task.file_size
        
        # Update downloaded
        self.downloaded_val.setText(format_bytes(current_size))
        
        # Update total size if it changed
        if self.size_val.text() in ["Unknown", "0 B"] and total_size > 0:
            self.size_val.setText(format_bytes(total_size))
        
        # Update remaining
        if total_size > 0:
            remaining = max(0, total_size - current_size)
            self.remaining_val.setText(format_bytes(remaining))
        
        # Update status
        if progress > 0 and progress < 100:
            self.status_val.setText("Downloading...")
            self.status_val.setStyleSheet(f"color: {t['accent_primary']};")
        elif progress >= 100:
            self.status_val.setText("Finishing up...")
            self.status_val.setStyleSheet(f"color: {t['accent_success']};")

    def on_finished(self):
        self.accept()
        dlg = DownloadedDialog(self.task, self.parent())
        dlg.show()
        
        # Track dialog in parent if possible
        parent = self.parent()
        if parent and hasattr(parent, '_active_dialogs'):
            parent._active_dialogs.append(dlg)
            dlg.destroyed.connect(
                lambda: parent._active_dialogs.remove(dlg) 
                if dlg in parent._active_dialogs else None
            )

    def toggle_pause(self):
        if self.task.status == "Downloading":
            self.task.pause()
            self.pause_btn.set_icon_type(IconType.RESUME)
            self.pause_btn.setText("Resume")
            self.status_val.setText("Paused")
        elif self.task.status == "Paused":
            self.task.resume()
            self.pause_btn.set_icon_type(IconType.PAUSE)
            self.pause_btn.setText("Pause")
            self.status_val.setText("Resuming...")

    def cancel_download(self):
        # Pause instead of stopping completely
        if self.task.status == "Downloading":
            self.task.pause()
        self.reject()
    
    def apply_theme(self):
        super().apply_theme()
        if hasattr(self, 'hide_btn'):
            self.hide_btn.apply_theme()
        if hasattr(self, 'pause_btn'):
            self.pause_btn.apply_theme()
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.apply_theme()


# ═══════════════════════════════════════════════════════════════════════════════
#                           WELCOME DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class WelcomeDialog(BaseDialog):
    """Welcome dialog with browser extension setup instructions"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "Welcome to Hyper Download Manager", None)
        self.resize(660, 540)
        
        t = theme.current
        
        # Custom Title Icon (Logo)
        self.title_logo = QLabel()
        self.title_logo.setFixedSize(32, 32)
        self.title_logo.setScaledContents(True)
        try:
            from utils.helpers import get_resource_path
            self.title_logo.setPixmap(QPixmap(get_resource_path("icon.png")))
        except:
            pass
        self.title_bar_layout.insertWidget(0, self.title_logo)
        
        # Welcome Header
        welcome_layout = QVBoxLayout()
        welcome_layout.setAlignment(Qt.AlignCenter)
        welcome_layout.setSpacing(12)
        
        # App icon container
        icon_container = QFrame()
        icon_container.setFixedSize(80, 80)
        icon_container_layout = QVBoxLayout(icon_container)
        icon_container_layout.setContentsMargins(0, 0, 0, 0)
        icon_container_layout.setAlignment(Qt.AlignCenter)
        
        app_icon = QLabel()
        app_icon.setFixedSize(64, 64)
        app_icon.setScaledContents(True)
        try:
            from utils.helpers import get_resource_path
            app_icon.setPixmap(QPixmap(get_resource_path("icon.png")))
        except:
            pass
        icon_container_layout.addWidget(app_icon)
        icon_container.setStyleSheet("QFrame { background-color: transparent; }")
        
        welcome_layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        
        welcome_msg = QLabel("Setup Browser Extension")
        welcome_msg.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
        welcome_msg.setAlignment(Qt.AlignCenter)
        welcome_msg.setStyleSheet(f"color: {t['text_primary']};")
        welcome_layout.addWidget(welcome_msg)
        
        sub_msg = QLabel("Follow these steps to integrate with your browser")
        sub_msg.setStyleSheet(f"color: {t['text_muted']};")
        sub_msg.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(sub_msg)
        
        self.main_layout.addLayout(welcome_layout)
        
        self.main_layout.addWidget(Divider())
        self.main_layout.addSpacing(12)
        
        # Steps
        steps = [
            (IconType.SETTINGS, "Open your browser's Extension Management page"),
            (IconType.CHECK, "Enable 'Developer Mode' (toggle in top right corner)"),
            (IconType.FOLDER, "Click 'Load Unpacked' button"),
            (IconType.FILE, "Select the 'extension' folder from HDM directory"),
            (IconType.COMPLETE, "The HDM icon will appear in your toolbar"),
        ]
        
        for i, (icon_type, text) in enumerate(steps, 1):
            step_layout = QHBoxLayout()
            step_layout.setSpacing(16)
            
            # Step number badge
            num_label = QLabel(str(i))
            num_label.setFixedSize(30, 30)
            num_label.setAlignment(Qt.AlignCenter)
            num_label.setStyleSheet(f"""
                background: {t['accent_primary']};
                color: white;
                border-radius: 15px;
                font-weight: 700;
                font-size: 13px;
            """)
            step_layout.addWidget(num_label)
            
            # Step icon
            step_icon = IconLabel(icon_type, 20)
            step_icon.set_color(t['text_secondary'])
            step_layout.addWidget(step_icon)
            
            # Step text
            text_label = QLabel(text)
            text_label.setStyleSheet(f"color: {t['text_primary']}; font-size: 13px;")
            step_layout.addWidget(text_label)
            step_layout.addStretch()
            
            self.main_layout.addLayout(step_layout)
            self.main_layout.addSpacing(6)
            
        self.main_layout.addSpacing(16)
        
        # Extension Path Helper
        path_label = QLabel("Extension Folder Path:")
        path_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px; font-weight: 600;")
        self.main_layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        
        try:
            from utils.helpers import get_resource_path
            ext_path = get_resource_path("extension")
        except:
            ext_path = os.path.join(os.getcwd(), "extension")
            
        self.ext_path_input = QLineEdit(ext_path)
        self.ext_path_input.setReadOnly(True)
        self.ext_path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {t['bg_tertiary']};
                border: 1px solid {t['border_primary']};
                color: {t['text_secondary']};
                padding: 8px;
                border-radius: 6px;
            }}
        """)
        path_layout.addWidget(self.ext_path_input)
        
        copy_btn = IconButton(IconType.COPY, "Copy Path", variant="secondary")
        copy_btn.setMinimumWidth(100)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(ext_path))
        path_layout.addWidget(copy_btn)
        
        self.main_layout.addLayout(path_layout)
        
        self.main_layout.addSpacing(16)
        self.main_layout.addWidget(Divider())
        self.main_layout.addSpacing(12)
        
        # Browser Buttons
        browser_label = QLabel("Quick Links:")
        browser_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px; font-weight: 600;")
        self.main_layout.addWidget(browser_label)
        
        browser_layout = QHBoxLayout()
        browser_layout.setSpacing(14)
        
        self.chrome_btn = IconButton(IconType.CHROME, "Chrome", variant="secondary")
        self.chrome_btn.setMinimumWidth(110)
        self.chrome_btn.clicked.connect(lambda: self.show_browser_help("chrome://extensions"))
        browser_layout.addWidget(self.chrome_btn)
        
        self.firefox_btn = IconButton(IconType.FIREFOX, "Firefox", variant="secondary")
        self.firefox_btn.setMinimumWidth(110)
        self.firefox_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://addons.mozilla.org/en-US/firefox/addon/hyper-download-manager/")
            )
        )
        browser_layout.addWidget(self.firefox_btn)
        
        self.edge_btn = IconButton(IconType.EDGE, "Edge", variant="secondary")
        self.edge_btn.setMinimumWidth(110)
        self.edge_btn.clicked.connect(lambda: self.show_browser_help("edge://extensions"))
        browser_layout.addWidget(self.edge_btn)
        
        browser_layout.addStretch()
        
        self.main_layout.addLayout(browser_layout)
        
        self.main_layout.addStretch()
        
        # Done Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.done_btn = IconButton(IconType.CHECK, "Get Started", variant="primary")
        self.done_btn.setMinimumWidth(150)
        self.done_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.done_btn)
        
        self.main_layout.addLayout(btn_layout)

    def show_browser_help(self, url):
        from PySide6.QtWidgets import QMessageBox
        
        clipboard = QApplication.clipboard()
        clipboard.setText(url)
        
        t = theme.current
        msg = QMessageBox(self)
        msg.setWindowTitle("URL Copied")
        msg.setText(f"The URL has been copied to your clipboard:\n\n{url}\n\nPaste it in your browser's address bar.")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {t['bg_card']};
            }}
            QMessageBox QLabel {{
                color: {t['text_primary']};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {t['accent_primary']};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {t['accent_secondary']};
            }}
        """)
        msg.exec()


# ═══════════════════════════════════════════════════════════════════════════════
#                            ABOUT DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class AboutDialog(BaseDialog):
    """About dialog showing app information"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "About", None)
        self.resize(400, 320)
        
        t = theme.current
        
        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(64, 64)
        logo_label.setScaledContents(True)
        try:
            from utils.helpers import get_resource_path
            logo_label.setPixmap(QPixmap(get_resource_path("icon.png")))
        except:
            pass
        
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.addStretch()
        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()
        self.main_layout.addWidget(logo_container)
        self.main_layout.addSpacing(16)
        
        # App Name
        name_label = QLabel("Hyper Download Manager")
        name_label.setStyleSheet(f"color: {t['text_primary']}; font-size: 18px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(name_label)
        
        # Version
        version_label = QLabel("Version 2.0.0")
        version_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 13px;")
        version_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(version_label)
        
        self.main_layout.addSpacing(24)
        
        # Description
        desc_label = QLabel(
            "A high-performance file downloader built with Python and PySide6.\n"
            "Designed for speed, privacy, and simplicity."
        )
        desc_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 13px; line-height: 1.4;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        self.main_layout.addWidget(desc_label)
        
        self.main_layout.addStretch()
        
        # Copyright
        copy_label = QLabel("© 2025 Hyper Download Manager. All rights reserved.")
        copy_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px;")
        copy_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(copy_label)
        
        self.main_layout.addSpacing(16)


# ═══════════════════════════════════════════════════════════════════════════════
#                           UPDATE DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class UpdateDialog(BaseDialog):
    """Dialog shown when an update is available"""
    
    def __init__(self, parent, new_version, download_url, note=""):
        super().__init__(parent, "Update Available", IconType.DOWNLOAD)
        self.download_url = download_url
        self.resize(450, 280)
        
        t = theme.current
        
        # Content Layout
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 10, 24, 24)
        
        # Header Area
        header = QHBoxLayout()
        header.setSpacing(16)
        
        # Icon
        icon_label = QLabel()
        icon_pixmap = get_pixmap(IconType.DOWNLOAD, t['accent_primary'], 48)
        icon_label.setPixmap(icon_pixmap)
        header.addWidget(icon_label)
        
        # Text Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        title = QLabel("New Version Available")
        title.setStyleSheet(f"""
            font-family: 'Segoe UI'; 
            font-size: 18px; 
            font-weight: 700; 
            color: {t['text_primary']};
        """)
        
        subtitle = QLabel(f"Version {new_version} is ready to download.")
        subtitle.setStyleSheet(f"""
            font-family: 'Segoe UI'; 
            font-size: 14px; 
            color: {t['text_secondary']};
        """)
        
        info_layout.addWidget(title)
        info_layout.addWidget(subtitle)
        header.addLayout(info_layout)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Release Note
        if note:
            note_header = QLabel("What's New:")
            note_header.setStyleSheet(f"""
                font-family: 'Segoe UI'; 
                font-size: 13px; 
                font-weight: 700; 
                color: {t['text_primary']}; 
                margin-top: 10px;
            """)
            layout.addWidget(note_header)
            
        note_text = note if note else "Update to get the latest features and bug fixes."
        note_label = QLabel(note_text)
        note_label.setWordWrap(True)
        note_label.setStyleSheet(f"""
            font-family: 'Segoe UI'; 
            font-size: 13px; 
            color: {t['text_muted']}; 
            margin-top: {2 if note else 5}px;
        """)
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.later_btn = QPushButton("Not Now")
        self.later_btn.setCursor(Qt.PointingHandCursor)
        self.later_btn.setFixedHeight(36)
        self.later_btn.setFixedWidth(100)
        self.later_btn.clicked.connect(self.reject)
        
        self.update_btn = QPushButton("Update Now")
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.setFixedHeight(36)
        self.update_btn.setFixedWidth(130)
        self.update_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.later_btn)
        btn_layout.addWidget(self.update_btn)
        
        layout.addLayout(btn_layout)
        
        self.main_layout.addWidget(content)
        self.apply_theme()
        
    def apply_theme(self):
        super().apply_theme()
        t = theme.current
        
        if hasattr(self, 'later_btn'):
            self.later_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {t['border_primary']};
                    border-radius: 6px;
                    color: {t['text_primary']};
                    font-family: 'Segoe UI';
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {t['bg_hover']};
                }}
            """)
        
        if hasattr(self, 'update_btn'):
            bg_color = t.get('accent_primary', '#3B82F6')
            hover_color = t.get('accent_secondary', t.get('accent_primary', '#2563EB'))
            
            self.update_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: none;
                    border-radius: 6px;
                    color: white;
                    font-family: 'Segoe UI';
                    font-weight: 600;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)


# ═══════════════════════════════════════════════════════════════════════════════
#                         PROXY STATUS DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class ProxyStatusDialog(BaseDialog):
    """Dialog showing proxy status and allowing refresh"""
    
    def __init__(self, parent=None):
        super().__init__(parent, "Proxy Status", IconType.GLOBE)
        self.resize(450, 350)
        
        t = theme.current
        
        # Status section
        status_section = SectionHeader("BUILT-IN PROXIES", IconType.SETTINGS)
        self.main_layout.addWidget(status_section)
        
        # Info grid
        grid = QGridLayout()
        grid.setSpacing(12)
        
        # Total proxies
        grid.addWidget(QLabel("Available Proxies:"), 0, 0)
        self.total_label = QLabel("Loading...")
        self.total_label.setStyleSheet(f"color: {t['accent_primary']}; font-weight: bold;")
        grid.addWidget(self.total_label, 0, 1)
        
        # Working proxies
        grid.addWidget(QLabel("Working:"), 1, 0)
        self.working_label = QLabel("-")
        self.working_label.setStyleSheet(f"color: {t['accent_success']}; font-weight: bold;")
        grid.addWidget(self.working_label, 1, 1)
        
        # Last refresh
        grid.addWidget(QLabel("Last Updated:"), 2, 0)
        self.last_refresh_label = QLabel("-")
        self.last_refresh_label.setStyleSheet(f"color: {t['text_secondary']};")
        grid.addWidget(self.last_refresh_label, 2, 1)
        
        # Status
        grid.addWidget(QLabel("Status:"), 3, 0)
        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet(f"color: {t['text_secondary']};")
        grid.addWidget(self.status_label, 3, 1)
        
        self.main_layout.addLayout(grid)
        
        # Info text
        info_text = QLabel(
            "The built-in proxy system automatically finds and uses free proxies\n"
            "when YouTube downloads are blocked on your network.\n\n"
            "Proxies are refreshed automatically every 30 minutes."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"""
            color: {t['text_muted']}; 
            font-size: 12px; 
            padding: 16px;
            background: {t['bg_tertiary']};
            border-radius: 8px;
        """)
        self.main_layout.addWidget(info_text)
        
        self.main_layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.refresh_btn = IconButton(IconType.REFRESH, "Refresh Proxies", variant="primary")
        self.refresh_btn.setMinimumWidth(150)
        self.refresh_btn.clicked.connect(self.refresh_proxies)
        btn_layout.addWidget(self.refresh_btn)
        
        self.close_btn = IconButton(IconType.CHECK, "Close", variant="secondary")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        self.main_layout.addLayout(btn_layout)
        
        self.apply_theme()
        self._update_status()
    
    def _update_status(self):
        """Update status display"""
        try:
            from core.proxy_manager import proxy_manager
            
            total = proxy_manager.get_proxy_count()
            working = proxy_manager.get_working_count()
            
            self.total_label.setText(str(total))
            self.working_label.setText(str(working))
            
            if proxy_manager._last_refresh > 0:
                elapsed = int(time.time() - proxy_manager._last_refresh)
                if elapsed < 60:
                    self.last_refresh_label.setText(f"{elapsed} seconds ago")
                elif elapsed < 3600:
                    self.last_refresh_label.setText(f"{elapsed // 60} minutes ago")
                else:
                    self.last_refresh_label.setText(f"{elapsed // 3600} hours ago")
            else:
                self.last_refresh_label.setText("Never")
            
            if proxy_manager.is_fetching():
                self.status_label.setText("Fetching proxies...")
            elif total > 0:
                self.status_label.setText("Ready")
            else:
                self.status_label.setText("No proxies loaded")
                
        except ImportError:
            self.total_label.setText("N/A")
            self.status_label.setText("Proxy manager not available")
    
    def refresh_proxies(self):
        """Start proxy refresh"""
        try:
            from core.proxy_manager import proxy_manager
            
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("Refreshing...")
            self.status_label.setText("Fetching fresh proxies...")
            
            def on_done(success):
                self.refresh_btn.setEnabled(True)
                self.refresh_btn.setText("Refresh Proxies")
                self._update_status()
                
                if success:
                    self.status_label.setText("Refresh complete!")
                else:
                    self.status_label.setText("Refresh failed")
            
            proxy_manager.refresh_proxies(callback=on_done)
            
        except ImportError:
            self.status_label.setText("Proxy manager not available")
    
    def apply_theme(self):
        super().apply_theme()
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.apply_theme()
        if hasattr(self, 'close_btn'):
            self.close_btn.apply_theme()