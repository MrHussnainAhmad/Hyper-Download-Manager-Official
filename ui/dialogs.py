import requests
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QProgressBar, QFileDialog, 
                               QGridLayout, QWidget, QSpacerItem, QSizePolicy,
                               QGraphicsDropShadowEffect, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QStandardPaths, QSize, QPropertyAnimation, QUrl
from PySide6.QtGui import QColor, QFont, QPixmap, QDesktopServices

from ui.theme_manager import theme
from ui.icons import IconType, IconProvider, get_pixmap
from ui.components import (IconButton, IconLabel, Card, AnimatedProgressBar, 
                          StatusBadge, SectionHeader, Divider)
from utils.helpers import format_bytes, format_speed, format_time


class MetadataFetcher(QThread):
    finished = Signal(str, int)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            head = requests.head(self.url, allow_redirects=True, timeout=5)
            name = self.url.split('/')[-1] or "download.file"
            if "Content-Disposition" in head.headers:
                import re
                fname = re.findall("filename=(.+)", head.headers["Content-Disposition"])
                if fname:
                    name = fname[0].strip('\"')
            size = int(head.headers.get('content-length', 0))
            self.finished.emit(name, size)
        except:
            self.finished.emit("", 0)


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
        if hasattr(self, '_drag_pos') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)


# ═══════════════════════════════════════════════════════════════════════════════
#                         NEW DOWNLOAD DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class NewDownloadDialog(BaseDialog):
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
        self.url_icon.apply_theme()
        self.cancel_btn.apply_theme()
        self.ok_btn.apply_theme()


# ═══════════════════════════════════════════════════════════════════════════════
#                      DOWNLOAD CONFIRMATION DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class DownloadConfirmationDialog(BaseDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent, "Confirm Download", IconType.DOWNLOAD)
        self.resize(580, 380)
        
        self.url = url
        self.auto_start = True
        
        # File Info Section
        info_section = SectionHeader("FILE INFORMATION", IconType.FILE)
        self.main_layout.addWidget(info_section)
        
        # Info Grid
        info_grid = QGridLayout()
        info_grid.setSpacing(14)
        info_grid.setColumnMinimumWidth(0, 90)
        
        # URL Row
        url_label = QLabel("URL")
        url_label.setStyleSheet(f"color: {theme.get('text_muted')}; font-weight: 600;")
        info_grid.addWidget(url_label, 0, 0)
        
        self.url_edit = QLineEdit(url)
        self.url_edit.setReadOnly(True)
        info_grid.addWidget(self.url_edit, 0, 1)
        
        # Name Row
        name_label = QLabel("File Name")
        name_label.setStyleSheet(f"color: {theme.get('text_muted')}; font-weight: 600;")
        info_grid.addWidget(name_label, 1, 0)
        
        self.name_edit = QLineEdit("Fetching...")
        info_grid.addWidget(self.name_edit, 1, 1)
        
        # Size Row
        size_label = QLabel("Size")
        size_label.setStyleSheet(f"color: {theme.get('text_muted')}; font-weight: 600;")
        info_grid.addWidget(size_label, 2, 0)
        
        size_layout = QHBoxLayout()
        self.size_icon = IconLabel(IconType.STORAGE, 18)
        size_layout.addWidget(self.size_icon)
        
        self.size_value = QLabel("Calculating...")
        self.size_value.setStyleSheet(f"font-weight: 700; color: {theme.get('accent_primary')};")
        size_layout.addWidget(self.size_value)
        size_layout.addStretch()
        
        info_grid.addLayout(size_layout, 2, 1)
        
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
        
        # Start metadata fetch
        self.fetcher = MetadataFetcher(url)
        self.fetcher.finished.connect(self.on_metadata_ready)
        self.fetcher.start()
        
        self.apply_theme()

    def on_metadata_ready(self, name, size):
        if name:
            self.name_edit.setText(name)
        else:
            self.name_edit.setText(self.url.split('/')[-1] or "download.file")
            
        if size > 0:
            self.size_value.setText(format_bytes(size))
        else:
            self.size_value.setText("Unknown")

    def browse_folder(self):
        dir_ = QFileDialog.getExistingDirectory(self, "Select Directory", self.path_edit.text())
        if dir_:
            self.path_edit.setText(dir_)

    def on_download_now(self):
        self.auto_start = True
        self.accept()

    def on_download_later(self):
        self.auto_start = False
        self.accept()

    def get_data(self):
        save_path = os.path.join(self.path_edit.text(), self.name_edit.text())
        return self.url, save_path, self.auto_start
        
    def apply_theme(self):
        super().apply_theme()
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


# ═══════════════════════════════════════════════════════════════════════════════
#                         DOWNLOAD COMPLETE DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class DownloadedDialog(BaseDialog):
    def __init__(self, task, parent=None):
        super().__init__(parent, "Download Complete", IconType.COMPLETE)
        self.task = task
        self.resize(500, 320)
        
        # Success Message with large icon
        success_layout = QVBoxLayout()
        success_layout.setAlignment(Qt.AlignCenter)
        success_layout.setSpacing(16)
        
        # Large success icon with glow effect
        success_container = QFrame()
        success_container.setFixedSize(80, 80)
        success_container_layout = QVBoxLayout(success_container)
        success_container_layout.setContentsMargins(0, 0, 0, 0)
        success_container_layout.setAlignment(Qt.AlignCenter)
        
        success_icon = IconLabel(IconType.COMPLETE, 48)
        success_icon.set_color(theme.get('accent_success'))
        success_container_layout.addWidget(success_icon)
        
        t = theme.current
        success_bg = QColor(t['accent_success'])
        success_bg.setAlpha(25)
        success_container.setStyleSheet(f"""
            QFrame {{
                background-color: {success_bg.name(QColor.HexArgb)};
                border-radius: 40px;
            }}
        """)
        
        success_layout.addWidget(success_container, alignment=Qt.AlignCenter)
        
        success_msg = QLabel("Download Completed Successfully!")
        success_msg.setFont(QFont("Segoe UI", 15, QFont.DemiBold))
        success_msg.setAlignment(Qt.AlignCenter)
        success_msg.setStyleSheet(f"color: {t['text_primary']};")
        success_layout.addWidget(success_msg)
        
        self.main_layout.addLayout(success_layout)
        
        self.main_layout.addWidget(Divider())
        
        # File Info
        info_layout = QGridLayout()
        info_layout.setSpacing(10)
        info_layout.setColumnMinimumWidth(0, 80)
        
        file_icon = IconLabel(IconType.FILE, 16)
        info_layout.addWidget(file_icon, 0, 0, Qt.AlignRight)
        name_label = QLabel(os.path.basename(task.save_path))
        name_label.setStyleSheet(f"font-weight: 600; color: {t['text_primary']};")
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label, 0, 1)
        
        size_icon = IconLabel(IconType.STORAGE, 16)
        info_layout.addWidget(size_icon, 1, 0, Qt.AlignRight)
        size_label = QLabel(format_bytes(task.file_size))
        size_label.setStyleSheet(f"color: {t['accent_primary']}; font-weight: 600;")
        info_layout.addWidget(size_label, 1, 1)
        
        folder_icon = IconLabel(IconType.FOLDER, 16)
        info_layout.addWidget(folder_icon, 2, 0, Qt.AlignRight)
        loc_label = QLabel(os.path.dirname(task.save_path))
        loc_label.setWordWrap(True)
        loc_label.setStyleSheet(f"color: {t['text_muted']};")
        info_layout.addWidget(loc_label, 2, 1)
        
        self.main_layout.addLayout(info_layout)
        
        self.main_layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)
        
        self.close_btn = IconButton(IconType.CLOSE, "Close", variant="ghost")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        btn_layout.addStretch()
        
        self.folder_btn = IconButton(IconType.FOLDER, "Open Folder", variant="secondary")
        self.folder_btn.setMinimumWidth(140)
        self.folder_btn.clicked.connect(self.open_folder)
        btn_layout.addWidget(self.folder_btn)
        
        self.open_btn = IconButton(IconType.FILE, "Open File", variant="primary")
        self.open_btn.setMinimumWidth(130)
        self.open_btn.clicked.connect(self.open_file)
        btn_layout.addWidget(self.open_btn)
        
        self.main_layout.addLayout(btn_layout)

    def open_file(self):
        try:
            os.startfile(self.task.save_path)
            self.accept()
        except Exception as e:
            print(f"Error opening file: {e}")

    def open_folder(self):
        try:
            folder = os.path.dirname(self.task.save_path)
            os.startfile(folder)
            self.accept()
        except Exception as e:
            print(f"Error opening folder: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#                           PROGRESS DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressDialog(BaseDialog):
    def __init__(self, task, parent=None):
        super().__init__(parent, "Downloading...", IconType.DOWNLOAD)
        self.task = task
        self.resize(560, 420)
        
        t = theme.current
        
        # File Name Header
        file_layout = QHBoxLayout()
        file_layout.setSpacing(12)
        
        file_icon = IconLabel(IconType.FILE, 28)
        file_layout.addWidget(file_icon)
        
        self.file_header = QLabel(task.save_path.split(os.sep)[-1])
        self.file_header.setFont(QFont("Segoe UI", 14, QFont.DemiBold))
        self.file_header.setWordWrap(True)
        self.file_header.setStyleSheet(f"color: {t['text_primary']};")
        file_layout.addWidget(self.file_header)
        file_layout.addStretch()
        
        self.main_layout.addLayout(file_layout)
        
        # URL (truncated)
        url_display = task.url if len(task.url) < 60 else task.url[:57] + "..."
        self.url_label = QLabel(url_display)
        self.url_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px;")
        self.main_layout.addWidget(self.url_label)
        
        self.main_layout.addSpacing(20)
        
        # Progress Bar
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setFixedHeight(26)
        self.main_layout.addWidget(self.progress_bar)
        
        self.main_layout.addSpacing(12)
        
        # Speed Display - Prominent
        speed_card = QFrame()
        speed_card.setFixedHeight(70)
        speed_layout = QHBoxLayout(speed_card)
        speed_layout.setContentsMargins(20, 0, 20, 0)
        
        speed_icon = IconLabel(IconType.SPEED, 32)
        speed_layout.addWidget(speed_icon)
        
        speed_text_layout = QVBoxLayout()
        speed_text_layout.setSpacing(2)
        
        self.speed_label = QLabel("0 B/s")
        self.speed_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.speed_label.setStyleSheet(f"color: {t['accent_primary']};")
        speed_text_layout.addWidget(self.speed_label)
        
        speed_subtitle = QLabel("Download Speed")
        speed_subtitle.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px;")
        speed_text_layout.addWidget(speed_subtitle)
        
        speed_layout.addLayout(speed_text_layout)
        speed_layout.addStretch()
        
        speed_bg = QColor(t['accent_primary'])
        speed_bg.setAlpha(15)
        speed_card.setStyleSheet(f"""
            QFrame {{
                background-color: {speed_bg.name(QColor.HexArgb)};
                border-radius: 12px;
            }}
        """)
        
        self.main_layout.addWidget(speed_card)
        
        self.main_layout.addSpacing(8)
        self.main_layout.addWidget(Divider())
        self.main_layout.addSpacing(8)
        
        # Stats Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        stats_grid.setColumnStretch(1, 1)
        stats_grid.setColumnStretch(3, 1)
        
        # Row 0
        stats_grid.addWidget(self._create_stat_label(IconType.STORAGE, "File Size"), 0, 0)
        self.size_value = self._create_stat_value("-")
        stats_grid.addWidget(self.size_value, 0, 1)
        
        stats_grid.addWidget(self._create_stat_label(IconType.DOWNLOAD, "Downloaded"), 0, 2)
        self.downloaded_value = self._create_stat_value("-")
        stats_grid.addWidget(self.downloaded_value, 0, 3)
        
        # Row 1
        stats_grid.addWidget(self._create_stat_label(IconType.ARROW_UP, "Remaining"), 1, 0)
        self.remaining_value = self._create_stat_value("-")
        stats_grid.addWidget(self.remaining_value, 1, 1)
        
        stats_grid.addWidget(self._create_stat_label(IconType.CLOCK, "Time Left"), 1, 2)
        self.eta_value = self._create_stat_value("-")
        stats_grid.addWidget(self.eta_value, 1, 3)
        
        self.main_layout.addLayout(stats_grid)
        
        self.main_layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(14)
        
        self.hide_btn = IconButton(IconType.MINIMIZE, "Hide", variant="ghost")
        self.hide_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.hide_btn)
        
        btn_layout.addStretch()
        
        self.cancel_btn = IconButton(IconType.CLOSE, "Cancel", variant="danger")
        self.cancel_btn.setMinimumWidth(110)
        self.cancel_btn.clicked.connect(self.cancel_download)
        btn_layout.addWidget(self.cancel_btn)
        
        self.pause_btn = IconButton(IconType.PAUSE, "Pause", variant="secondary")
        self.pause_btn.setMinimumWidth(110)
        self.pause_btn.clicked.connect(self.toggle_pause)
        btn_layout.addWidget(self.pause_btn)
        
        self.main_layout.addLayout(btn_layout)
        
        # Connect signals
        self.task.progress_updated.connect(self.update_stats)
        self.task.finished.connect(self.on_finished)
        
        self.update_stats(0, 0, 0)
        
    def _create_stat_label(self, icon_type: IconType, text: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        icon = IconLabel(icon_type, 14)
        icon.set_color(theme.get('text_muted'))
        layout.addWidget(icon)
        
        label = QLabel(text)
        label.setStyleSheet(f"color: {theme.get('text_muted')}; font-size: 11px;")
        layout.addWidget(label)
        layout.addStretch()
        
        return widget
        
    def _create_stat_value(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {theme.get('text_primary')}; font-weight: 600; font-size: 13px;")
        return label

    def update_stats(self, progress, speed, eta):
        self.progress_bar.setValue(progress)
        self.speed_label.setText(format_speed(speed))
        self.eta_value.setText(format_time(eta) if eta > 0 else "-")
        
        size = self.task.file_size
        self.size_value.setText(format_bytes(size) if size > 0 else "-")
        
        downloaded = self.task.downloaded_bytes
        self.downloaded_value.setText(format_bytes(downloaded))
        
        remaining = max(0, size - downloaded)
        self.remaining_value.setText(format_bytes(remaining))

    def on_finished(self):
        self.accept()
        dlg = DownloadedDialog(self.task, self.parent())
        dlg.show()
        parent = self.parent()
        if parent and hasattr(parent, '_active_dialogs'):
            parent._active_dialogs.append(dlg)
            dlg.destroyed.connect(lambda: parent._active_dialogs.remove(dlg) if dlg in parent._active_dialogs else None)

    def toggle_pause(self):
        if self.task.status == "Downloading":
            self.task.pause()
            self.pause_btn.set_icon_type(IconType.RESUME)
            self.pause_btn.setText("Resume")
        elif self.task.status == "Paused":
            self.task.resume()
            self.pause_btn.set_icon_type(IconType.PAUSE)
            self.pause_btn.setText("Pause")

    def cancel_download(self):
        parent = self.parent()
        if parent and hasattr(parent, 'manager'):
            parent.manager.remove_download(self.task)
        else:
            self.task.delete_all_files()
        self.reject()


# ═══════════════════════════════════════════════════════════════════════════════
#                           WELCOME DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class WelcomeDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Welcome to Hyper Download Manager", None)
        self.resize(660, 520)
        
        # Custom Title Icon (Logo)
        self.title_logo = QLabel()
        self.title_logo.setFixedSize(32, 32)
        self.title_logo.setScaledContents(True)
        from utils.helpers import get_resource_path
        self.title_logo.setPixmap(QPixmap(get_resource_path("icon.png")))
        self.title_bar_layout.insertWidget(0, self.title_logo)
        
        t = theme.current
        
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
        from utils.helpers import get_resource_path
        app_icon.setPixmap(QPixmap(get_resource_path("icon.png")))
        icon_container_layout.addWidget(app_icon)
        
        icon_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        
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
        
        from utils.helpers import get_resource_path
        ext_path = get_resource_path("extension")
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
        self.firefox_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://addons.mozilla.org/en-US/firefox/addon/hyper-download-manager/")))
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
        from PySide6.QtWidgets import QMessageBox, QApplication
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


class AboutDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "About", None)
        self.resize(400, 320)
        
        t = theme.current
        
        # Logo
        logo_label = QLabel()
        logo_label.setFixedSize(64, 64)
        logo_label.setScaledContents(True)
        from utils.helpers import get_resource_path
        logo_label.setPixmap(QPixmap(get_resource_path("icon.png")))
        
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
        desc_label = QLabel("A high-performance file downloader built with Python and PySide6.\nDesigned for speed, privacy, and simplicity.")
        desc_label.setStyleSheet(f"color: {t['text_secondary']}; font-size: 13px; line-height: 1.4;")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        self.main_layout.addWidget(desc_label)
        
        self.main_layout.addStretch()
        
        # Copyright
        copy_label = QLabel(" 2026 Hyper Download Manager. All rights reserved.")
        copy_label.setStyleSheet(f"color: {t['text_muted']}; font-size: 11px;")
        copy_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(copy_label)
        
        self.main_layout.addSpacing(16)