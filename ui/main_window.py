import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QStatusBar, QLabel, QMessageBox, QMenu, QApplication,
                               QFrame)
from PySide6.QtCore import Qt, QSettings, QTimer, QSize
from PySide6.QtGui import QAction, QFont, QColor

from ui.theme_manager import theme
from ui.icons import IconType, IconProvider, get_icon, get_pixmap
from ui.sidebar import Sidebar
from ui.toolbar import MainToolbar
from ui.download_list import DownloadList
from ui.components import IconLabel
from core.download_manager import DownloadManager
from utils.system_monitor import SystemMonitorWorker
from core.updater import UpdateChecker
from core.ytdlp_updater import YtDlpUpdater
from ui.dialogs import UpdateDialog
from utils.helpers import get_app_version


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyper Download Manager")
        self.resize(1200, 800)
        self.setMinimumSize(950, 650)
        
        self._active_dialogs = []
        self._ytdlp_updater = None
        
        # Initialize components
        self.manager = DownloadManager()
        self.monitor =SystemMonitorWorker()
        
        # Setup UI
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._connect_signals()
        
        
        # Apply initial theme
        self.apply_theme()
        
        # Start monitoring
        self.monitor.start()
        
        # Start background yt-dlp updater (non-blocking)
        self._start_ytdlp_updater()
        
        # Check for updates
        UPDATE_API_URL = "https://hyper-download-manager-web.vercel.app" 
        current_version = get_app_version()
             
        self.updater = UpdateChecker(UPDATE_API_URL, current_version)
        self._setup_updater_signals()
        # Delay check by 5 seconds to not slow down startup
        QTimer.singleShot(5000, self.updater.start)
        
        # Restore downloads
        for task in self.manager.downloads:
            self.list_view.add_task(task)
            
        # First run check
        QTimer.singleShot(500, self.check_first_run)
        
    def _setup_menu_bar(self):
        self.menu_bar = self.menuBar()
        
        # File Menu
        file_menu = self.menu_bar.addMenu("File")
        
        self.action_add = file_menu.addAction("Add Download")
        self.action_add.setIcon(get_icon(IconType.ADD, theme.get('text_primary'), 16))
        self.action_add.setShortcut("Ctrl+N")
        self.action_add.triggered.connect(self.add_download_dialog)
        
        file_menu.addSeparator()
        
        self.action_exit = file_menu.addAction("Exit")
        self.action_exit.setIcon(get_icon(IconType.CLOSE, theme.get('text_primary'), 16))
        self.action_exit.triggered.connect(self.close)
        
        # View Menu
        view_menu = self.menu_bar.addMenu("View")
        
        self.action_toggle_theme = view_menu.addAction("Toggle Theme")
        self.action_toggle_theme.setIcon(get_icon(IconType.THEME_DARK, theme.get('text_primary'), 16))
        self.action_toggle_theme.setShortcut("Ctrl+T")
        self.action_toggle_theme.triggered.connect(self.toggle_theme)
        
        # Updates Menu
        updates_menu = self.menuBar().addMenu("Updates")
        self.action_check_updates = updates_menu.addAction("Check for Updates")
        self.action_check_updates.setIcon(get_icon(IconType.DOWNLOAD, theme.get('text_primary'), 16))
        self.action_check_updates.triggered.connect(self.check_for_updates_manual)
        
        # Help Menu
        help_menu = self.menu_bar.addMenu("Help")
        
        self.action_welcome = help_menu.addAction("Setup Guide")
        self.action_welcome.setIcon(get_icon(IconType.INFO, theme.get('text_primary'), 16))
        self.action_welcome.triggered.connect(self.show_welcome_dialog)
        
        help_menu.addSeparator()
        
        self.action_about = help_menu.addAction("About")
        self.action_about.setIcon(get_icon(IconType.INFO, theme.get('text_primary'), 16))
        self.action_about.triggered.connect(self.show_about_dialog)

        settings_menu = self.menu_bar.addMenu("Settings")
        self.action_settings = settings_menu.addAction("Preferences")
        self.action_settings.setIcon(get_icon(IconType.SETTINGS, theme.get('text_primary'), 16))
        self.action_settings.setShortcut("Ctrl+,")
        self.action_settings.triggered.connect(self.show_settings_dialog)
    
    def show_settings_dialog(self):
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        dlg.exec()

    def _setup_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(270)
        self.main_layout.addWidget(self.sidebar)
        
        # Content Area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.main_layout.addWidget(self.content_widget)
        
        # Toolbar
        self.toolbar = MainToolbar()
        self.content_layout.addWidget(self.toolbar)
        
        # Download List
        self.list_view = DownloadList()
        self.content_layout.addWidget(self.list_view)
        
        # Connect empty state action
        self.list_view.empty_state.action_clicked.connect(self.show_welcome_dialog)
        
    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(36)
        self.setStatusBar(self.status_bar)
        
        # Left section - Download count
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 0, 12, 0)
        left_layout.setSpacing(8)
        
        self.count_icon = IconLabel(IconType.DOWNLOAD, 14)
        left_layout.addWidget(self.count_icon)
        
        self.footer_count = QLabel("0 downloads")
        self.footer_count.setFont(QFont("Segoe UI", 11))
        left_layout.addWidget(self.footer_count)
        
        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(18)
        left_layout.addWidget(sep)
        
        self.active_icon = IconLabel(IconType.RESUME, 14)
        left_layout.addWidget(self.active_icon)
        
        self.active_count = QLabel("0 active")
        self.active_count.setFont(QFont("Segoe UI", 11))
        left_layout.addWidget(self.active_count)
        
        self.status_bar.addWidget(left_widget)
        
        # Right section - Connection status
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(12, 0, 12, 0)
        right_layout.setSpacing(8)
        
        self.connection_icon = IconLabel(IconType.SPEED, 14)
        right_layout.addWidget(self.connection_icon)
        
        self.footer_status = QLabel("Online")
        self.footer_status.setFont(QFont("Segoe UI", 11))
        right_layout.addWidget(self.footer_status)
        
        self.status_bar.addPermanentWidget(right_widget)
        
    def _connect_signals(self):
        # Monitor signals
        self.monitor.speed_updated.connect(self.toolbar.speed_monitor.update_speed)
        self.monitor.disk_usage_updated.connect(self.sidebar.storage.update_usage)
        self.monitor.connection_status_changed.connect(self.toolbar.speed_monitor.set_offline)
        self.monitor.connection_status_changed.connect(self.update_connection_status)
        
        # Toolbar signals
        self.toolbar.add_clicked.connect(self.add_download_dialog)
        self.toolbar.resume_clicked.connect(self.resume_selected)
        self.toolbar.pause_clicked.connect(self.pause_selected)
        self.toolbar.stop_clicked.connect(self.stop_selected)
        self.toolbar.remove_clicked.connect(self.remove_selected)
        self.toolbar.start_all_clicked.connect(self.manager.start_all_downloads)
        self.toolbar.pause_all_clicked.connect(self.manager.pause_all_downloads)
        self.toolbar.theme_toggle_clicked.connect(self.apply_theme)
        
        # Manager signals
        self.manager.download_added.connect(self.list_view.add_task)
        self.manager.download_removed.connect(self.list_view.remove_task)
        
        # List signals
        self.list_view.open_progress.connect(self.open_progress_dialog)
        self.list_view.context_menu_requested.connect(self.show_context_menu)
        self.list_view.delete_requested.connect(self.remove_selected)
        
        # Connect status updates
        self.manager.download_added.connect(self.update_status_counts)
        self.manager.download_removed.connect(self.update_status_counts)
        
        # Connect signals for new downloads
        self.manager.download_added.connect(self._setup_new_task_signals)
        
        # We need to connect to status changes of existing and new tasks
        for task in self.manager.downloads:
             self._setup_new_task_signals(task)
             
        # Initial update
        self.update_status_counts()

    def _setup_new_task_signals(self, task):
        """Connect signals for a single task"""
        # Simply connect - tasks should only be set up once
        task.status_changed.connect(self._on_task_status_changed)
        task.proxy_fallback_warning.connect(self.show_youtube_fallback_dialog)

    def _on_task_status_changed(self, status):
        """Handle status change from any task"""
        self.update_status_counts()

    def show_youtube_fallback_dialog(self):
        """Show warning when falling back to proxy for YouTube"""
        t = theme.current
        msg = QMessageBox(self)
        msg.setWindowTitle("YouTube Download Warning")
        msg.setIcon(QMessageBox.Warning)
        
        # Exact text requested by user
        text = (
            "YOUR ISP HAVE BANNED DOWNLOADING FROM YOUTUBE, WE ARE TRYING TO GET YOUR VIDEO "
            "THOURH OUR PROXIES, INCASE AFTER 30 SECONDS YOU DON'T FIND DONWLOAD RUNNING, "
            "PLEASE USE VPN OR CAN WAIT FEW UPDATES TILL WE ADD PURCHASE PROXY. "
            "FOR NOW YOU CAN ADD CUSTOM PROXY IN SETTINGS."
        )
        msg.setText(text)
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {t['bg_card']};
            }}
            QMessageBox QLabel {{
                color: {t['text_primary']};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {t['bg_tertiary']};
                color: {t['text_primary']};
                border: 1px solid {t['border_primary']};
                border-radius: 6px;
                padding: 6px 16px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {t['bg_hover']};
            }}
        """)
        
        # Show non-blocking so download can continue in background
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def update_status_counts(self):
        """Update the status bar counts for active and completed downloads"""
        total_active = 0
        total_completed = 0
        
        for task in self.manager.downloads:
            if task.status == "Downloading":
                total_active += 1
            elif task.status in ["Finished", "Completed"]:
                total_completed += 1
                
        # Update labels with plurals handling
        d_text = "download" if total_completed == 1 else "downloads"
        self.footer_count.setText(f"{total_completed} completed")
        
        a_text = "active" # simplifying text as per request active downloads -> active
        self.active_count.setText(f"{total_active} active")

        
    def apply_theme(self):
        """Apply current theme to all components"""
        t = theme.current
        
        # Clear icon cache
        IconProvider.clear_cache()
        
        # Main stylesheet
        self.setStyleSheet(theme.get_main_stylesheet())
        
        # Status bar
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: transparent;
                color: {t['text_muted']};
                border-top: 1px solid {t['border_primary']};
            }}
            QFrame#separator {{
                background-color: {t['border_primary']};
            }}
        """)
        
        # Update status bar icons
        self.count_icon.apply_theme()
        self.count_icon.set_color(t['text_muted'])
        self.active_icon.apply_theme()
        self.active_icon.set_color(t['accent_primary'])
        self.connection_icon.apply_theme()
        
        # Update labels
        self.footer_count.setStyleSheet(f"color: {t['text_muted']};")
        self.active_count.setStyleSheet(f"color: {t['text_secondary']};")
        
        # Update components
        self.sidebar.apply_theme()
        self.toolbar.apply_theme()
        self.list_view.apply_theme()
        
        # Update menu icons
        self._update_menu_icons()
        
    def _update_menu_icons(self):
        t = theme.current
        self.action_add.setIcon(get_icon(IconType.ADD, t['text_primary'], 16))
        self.action_exit.setIcon(get_icon(IconType.CLOSE, t['text_primary'], 16))
        self.action_toggle_theme.setIcon(
            get_icon(IconType.THEME_DARK if theme.is_dark else IconType.THEME_LIGHT, 
                    t['text_primary'], 16)
        )
        self.action_welcome.setIcon(get_icon(IconType.INFO, t['text_primary'], 16))
        self.action_about.setIcon(get_icon(IconType.INFO, t['text_primary'], 16))
        self.action_settings.setIcon(get_icon(IconType.SETTINGS, t['text_primary'], 16))  # Add this

        
    def toggle_theme(self):
        theme.toggle_theme()
        self.apply_theme()
        
    def update_connection_status(self, is_connected):
        t = theme.current
        if not is_connected:
            self.footer_status.setText("Offline")
            self.footer_status.setStyleSheet(f"color: {t['accent_error']};")
            self.connection_icon.set_color(t['accent_error'])
        else:
            self.footer_status.setText("Online")
            self.footer_status.setStyleSheet(f"color: {t['accent_success']};")
            self.connection_icon.set_color(t['accent_success'])
            
    def check_first_run(self):
        settings = QSettings("FastDownloadManager", "FDM")
        if not settings.value("welcome_shown", False, type=bool):
            self.show_welcome_dialog()
            settings.setValue("welcome_shown", True)
            
    def add_download_dialog(self):
        from ui.dialogs import NewDownloadDialog
        
        dialog = NewDownloadDialog(self)
        if dialog.exec():
            url = dialog.get_url()
            if url:
                self.handle_new_download(url)
                
    def handle_new_download(self, payload):
        import json
        
        url = payload
        filename = None
        filesize = 0
        quality = None
        itag = None
        
        # Try to parse as JSON metadata from extension
        if payload.strip().startswith('{'):
            try:
                data = json.loads(payload)
                url = data.get('url', payload)
                filename = data.get('filename')
                filesize = data.get('filesize', 0)
                quality = data.get('quality')
                itag = data.get('itag')
            except:
                pass

        try:
            with open("debug_urls.log", "a") as f:
                f.write(f"Received payload: {payload}\nParsed URL: {url}\nFile: {filename}\nQuality: {quality}\nItag: {itag}\n")
        except:
            pass

        from ui.dialogs import DownloadConfirmationDialog, ProgressDialog
        
        self.raise_()
        self.activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        
        try:
            # Pass metadata to dialog (including quality/itag from extension)
            confirm_dlg = DownloadConfirmationDialog(
                url, 
                self, 
                filename=filename, 
                filesize=filesize,
                quality=quality,  # Pass quality from extension
                itag=itag         # Pass itag from extension
            )
            if confirm_dlg.exec():
                # Unpack ALL 6 values from get_data() including quality/itag
                final_url, save_path, auto_start, file_size, returned_quality, returned_itag = confirm_dlg.get_data()
                
                # Use returned values (user might have changed them in dialog)
                task = self.manager.add_download(
                    final_url, 
                    save_path, 
                    auto_start, 
                    file_size=file_size, 
                    quality=returned_quality,  # Use value from dialog
                    itag=returned_itag         # Use value from dialog
                )
                
                # Connect status change for UI updates
                task.status_changed.connect(lambda s: self.update_status_counts())
                self.update_status_counts()
                
                if auto_start:
                    self.open_progress_dialog(task)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open dialog:\n{str(e)}")
                
    def open_progress_dialog(self, task):
        from ui.dialogs import ProgressDialog
        
        dlg = ProgressDialog(task, self)
        dlg.setAttribute(Qt.WA_DeleteOnClose)
        dlg.show()
        
        self._active_dialogs.append(dlg)
        dlg.destroyed.connect(
            lambda: self._active_dialogs.remove(dlg) if dlg in self._active_dialogs else None
        )
        
    def show_welcome_dialog(self):
        from ui.dialogs import WelcomeDialog
        
        dlg = WelcomeDialog(self)
        dlg.exec()
        
    def show_context_menu(self, task, global_pos):
        t = theme.current
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_primary']};
                border-radius: 10px;
                padding: 8px 0;
            }}
            QMenu::item {{
                padding: 12px 20px 12px 16px;
                color: {t['text_primary']};
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background-color: {t['bg_hover']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {t['border_primary']};
                margin: 8px 14px;
            }}
            QMenu::icon {{
                padding-left: 14px;
            }}
        """)
        
        if task.status == "Downloading":
            action_pause = menu.addAction("Pause")
            action_pause.setIcon(get_icon(IconType.PAUSE, t['text_primary'], 16))
            action_pause.triggered.connect(task.pause)
            
        if task.status in ["Paused", "Stopped", "Error", "Queued", "Idle"]:
            action_resume = menu.addAction("Resume")
            action_resume.setIcon(get_icon(IconType.RESUME, t['text_primary'], 16))
            action_resume.triggered.connect(task.resume)
            
        menu.addSeparator()
        
        action_delete = menu.addAction("Delete")
        action_delete.setIcon(get_icon(IconType.DELETE, t['accent_error'], 16))
        action_delete.triggered.connect(lambda: self.confirm_remove_download(task))
        
        if task.status in ["Finished", "Completed"]:
            menu.addSeparator()
            
            action_open = menu.addAction("Open File")
            action_open.setIcon(get_icon(IconType.FILE, t['text_primary'], 16))
            action_open.triggered.connect(lambda: self.open_file(task))
            
            action_open_loc = menu.addAction("Open Location")
            action_open_loc.setIcon(get_icon(IconType.FOLDER, t['text_primary'], 16))
            action_open_loc.triggered.connect(lambda: self.open_folder(task))
            
        menu.exec(global_pos)
        
    def confirm_remove_download(self, task):
        t = theme.current
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Delete")
        msg.setText("Are you sure you want to delete this download?")
        msg.setInformativeText("This will permanently delete the file from your disk.")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {t['bg_card']};
            }}
            QMessageBox QLabel {{
                color: {t['text_primary']};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {t['bg_tertiary']};
                color: {t['text_primary']};
                border: 1px solid {t['border_primary']};
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {t['bg_hover']};
            }}
            QPushButton:default {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent_gradient_start']},
                    stop:1 {t['accent_gradient_end']});
                color: white;
                border: none;
            }}
        """)
        
        if msg.exec() == QMessageBox.Yes:
            self.manager.remove_download(task)
            
    def open_file(self, task):
        try:
            os.startfile(task.save_path)
        except Exception as e:
            print(f"Error opening file: {e}")
            
    def open_folder(self, task):
        try:
            folder = os.path.dirname(task.save_path)
            os.startfile(folder)
        except Exception as e:
            print(f"Error opening folder: {e}")
            
    def get_selected_task(self):
        items = self.list_view.selectedItems()
        if not items:
            return None
        for item in items:
            if item.column() == 0:
                return item.data(Qt.UserRole)
        return None
        
    def stop_selected(self):
        task = self.get_selected_task()
        if task and task.status == "Downloading":
            task.stop()
            
    def pause_selected(self):
        task = self.get_selected_task()
        if task and task.status == "Downloading":
            task.pause()
            
    def resume_selected(self):
        task = self.get_selected_task()
        if task and task.status in ["Paused", "Stopped", "Idle", "Queued"]:
            task.resume()
            
    def remove_selected(self):
        task = self.get_selected_task()
        if task:
            self.confirm_remove_download(task)

    def show_welcome_dialog(self):
        from ui.dialogs import WelcomeDialog
        dlg = WelcomeDialog(self)
        dlg.exec()

    def show_about_dialog(self):
        from ui.dialogs import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    def show_update_dialog(self, new_version, download_url, note=""):
        dlg = UpdateDialog(self, new_version, download_url, note)
        if dlg.exec():
            # User clicked Update Now, open URL
            import webbrowser
            webbrowser.open(download_url)
            
    def check_for_updates_manual(self):
        self._is_manual_check = True
        self.updater.start()
        
    def _handle_up_to_date(self):
        if getattr(self, '_is_manual_check', False):
            QMessageBox.information(self, "Update Check", "You are using the latest version of Hyper Download Manager.")
            self._is_manual_check = False
            
    def _handle_update_error(self, error):
        if getattr(self, '_is_manual_check', False):
            QMessageBox.warning(self, "Update Check Failed", f"Could not check for updates:\n{error}")
            self._is_manual_check = False

    def _setup_updater_signals(self):
        # Called from init
        self.updater.update_available.connect(self.show_update_dialog)
        self.updater.up_to_date.connect(self._handle_up_to_date)
        self.updater.error_occurred.connect(self._handle_update_error)
    def _start_ytdlp_updater(self):
        try:
            self._ytdlp_updater = YtDlpUpdater(force_check=False)
            self._ytdlp_updater.status_signal.connect(self._on_ytdlp_status)
            self._ytdlp_updater.finished_signal.connect(self._on_ytdlp_finished)
            self._ytdlp_updater.start()
        except Exception as e:
            print(f'DEBUG: Failed to start yt-dlp updater: {e}')

    def _on_ytdlp_status(self, status):
        self.status_bar.showMessage(status, 3000)

    def _on_ytdlp_finished(self, success, message):
        if success and message == 'updated':
            self.status_bar.showMessage('yt-dlp updated successfully', 5000)
