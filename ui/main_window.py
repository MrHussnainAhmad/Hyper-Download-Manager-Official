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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyper Download Manager")
        self.resize(1200, 800)
        self.setMinimumSize(950, 650)
        
        self._active_dialogs = []
        
        # Initialize components
        self.manager = DownloadManager()
        self.monitor = SystemMonitorWorker()
        
        # Setup UI
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._connect_signals()
        
        # Apply initial theme
        self.apply_theme()
        
        # Start monitoring
        self.monitor.start()
        
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
        
        # Help Menu
        help_menu = self.menu_bar.addMenu("Help")
        
        self.action_welcome = help_menu.addAction("Setup Guide")
        self.action_welcome.setIcon(get_icon(IconType.INFO, theme.get('text_primary'), 16))
        self.action_welcome.triggered.connect(self.show_welcome_dialog)
        
        help_menu.addSeparator()
        
        self.action_about = help_menu.addAction("About")
        self.action_about.setIcon(get_icon(IconType.INFO, theme.get('text_primary'), 16))
        self.action_about.triggered.connect(self.show_about_dialog)
        
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
                
    def handle_new_download(self, url):
        from ui.dialogs import DownloadConfirmationDialog, ProgressDialog
        
        self.raise_()
        self.activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        
        try:
            confirm_dlg = DownloadConfirmationDialog(url, self)
            if confirm_dlg.exec():
                final_url, save_path, auto_start = confirm_dlg.get_data()
                task = self.manager.add_download(final_url, save_path, auto_start)
                
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