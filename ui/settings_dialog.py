from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QCheckBox, QComboBox,
                               QTabWidget, QWidget, QFormLayout, QSpinBox,
                               QMessageBox, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.dialogs import BaseDialog
from ui.theme_manager import theme
from ui.icons import IconType
from ui.components import IconButton, SectionHeader, Divider
from core.settings import settings


class SettingsDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Settings", IconType.SETTINGS)
        self.resize(550, 500)
        
        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.main_layout.addWidget(self.tabs)
        
        # Create tabs
        self._create_proxy_tab()
        self._create_download_tab()
        self._create_youtube_tab()
        
        self.main_layout.addSpacing(16)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.test_btn = IconButton(IconType.SPEED, "Test Proxy", variant="secondary")
        self.test_btn.setMinimumWidth(120)
        self.test_btn.clicked.connect(self.test_proxy)
        btn_layout.addWidget(self.test_btn)
        
        self.save_btn = IconButton(IconType.CHECK, "Save", variant="primary")
        self.save_btn.setMinimumWidth(100)
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)
        
        self.main_layout.addLayout(btn_layout)
        
        # Load current settings
        self._load_settings()
        self.apply_theme()
    
    def _create_proxy_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Info label
        info = QLabel(
            "Configure a proxy to bypass network restrictions.\n"
            "Required if YouTube videos fail to download on your network."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {theme.get('text_muted')}; font-size: 12px;")
        layout.addWidget(info)
        
        layout.addWidget(Divider())
        
        # Enable checkbox
        self.proxy_enabled = QCheckBox("Enable Proxy")
        self.proxy_enabled.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.proxy_enabled.stateChanged.connect(self._on_proxy_toggle)
        layout.addWidget(self.proxy_enabled)
        
        # Proxy settings group
        self.proxy_group = QGroupBox("Proxy Configuration")
        proxy_layout = QFormLayout(self.proxy_group)
        proxy_layout.setSpacing(12)
        
        # Type
        self.proxy_type = QComboBox()
        self.proxy_type.addItems(["http", "https", "socks5"])
        self.proxy_type.setMinimumWidth(150)
        proxy_layout.addRow("Type:", self.proxy_type)
        
        # Host
        self.proxy_host = QLineEdit()
        self.proxy_host.setPlaceholderText("e.g., proxy.example.com or 192.168.1.1")
        proxy_layout.addRow("Host:", self.proxy_host)
        
        # Port
        self.proxy_port = QLineEdit()
        self.proxy_port.setPlaceholderText("e.g., 8080")
        self.proxy_port.setMaximumWidth(100)
        proxy_layout.addRow("Port:", self.proxy_port)
        
        # Username (optional)
        self.proxy_user = QLineEdit()
        self.proxy_user.setPlaceholderText("Optional")
        proxy_layout.addRow("Username:", self.proxy_user)
        
        # Password (optional)
        self.proxy_pass = QLineEdit()
        self.proxy_pass.setPlaceholderText("Optional")
        self.proxy_pass.setEchoMode(QLineEdit.Password)
        proxy_layout.addRow("Password:", self.proxy_pass)
        
        layout.addWidget(self.proxy_group)
        
        # Free proxy info
        free_info = QLabel(
            "💡 Need a proxy? You can:\n"
            "• Use a VPN app that provides proxy settings\n"
            "• Get free proxies from sites like free-proxy-list.net\n"
            "• Use SOCKS5 proxies from services like ProtonVPN"
        )
        free_info.setWordWrap(True)
        free_info.setStyleSheet(f"color: {theme.get('text_muted')}; font-size: 11px; padding: 10px; background: {theme.get('bg_tertiary')}; border-radius: 8px;")
        layout.addWidget(free_info)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "Proxy")
    
    def _create_download_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        # Threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        self.threads_spin.setValue(4)
        self.threads_spin.setMaximumWidth(80)
        form.addRow("Download Threads:", self.threads_spin)
        
        # Auto start
        self.auto_start = QCheckBox("Start downloads automatically")
        form.addRow("", self.auto_start)
        
        layout.addLayout(form)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Downloads")
    
    def _create_youtube_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        # Preferred quality
        self.yt_quality = QComboBox()
        self.yt_quality.addItems(["Best Available", "4K (2160p)", "1080p", "720p", "480p", "360p"])
        self.yt_quality.setMinimumWidth(150)
        form.addRow("Preferred Quality:", self.yt_quality)
        
        # Prefer MP4
        self.yt_mp4 = QCheckBox("Prefer MP4 format")
        self.yt_mp4.setChecked(True)
        form.addRow("", self.yt_mp4)
        
        layout.addLayout(form)
        
        # Note about quality
        note = QLabel(
            "Note: High quality videos (1080p+) require:\n"
            "• ffmpeg installed (for merging video+audio)\n"
            "• Working proxy if your network blocks YouTube\n\n"
            "Without these, downloads will fall back to 720p or lower."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {theme.get('text_muted')}; font-size: 11px; padding: 10px; background: {theme.get('bg_tertiary')}; border-radius: 8px;")
        layout.addWidget(note)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "YouTube")
    
    def _on_proxy_toggle(self, state):
        enabled = (state == 2)  # Qt.CheckState.Checked.value == 2
        print(f"DEBUG: Proxy toggle - state={state}, enabled={enabled}")
        self.proxy_group.setEnabled(enabled)
    
    def _load_settings(self):
        # Proxy
        self.proxy_enabled.setChecked(settings.get('proxy.enabled', False))
        self.proxy_type.setCurrentText(settings.get('proxy.type', 'http'))
        self.proxy_host.setText(settings.get('proxy.host', ''))
        self.proxy_port.setText(settings.get('proxy.port', ''))
        self.proxy_user.setText(settings.get('proxy.username', ''))
        self.proxy_pass.setText(settings.get('proxy.password', ''))
        
        self.proxy_group.setEnabled(self.proxy_enabled.isChecked())
        
        # Download
        self.threads_spin.setValue(settings.get('download.threads', 4))
        self.auto_start.setChecked(settings.get('download.auto_start', True))
        
        # YouTube
        quality_map = {
            'best': 0, '2160p': 1, '1080p': 2, 
            '720p': 3, '480p': 4, '360p': 5
        }
        quality = settings.get('youtube.preferred_quality', 'best')
        self.yt_quality.setCurrentIndex(quality_map.get(quality, 0))
        self.yt_mp4.setChecked(settings.get('youtube.prefer_mp4', True))
    
    def save_settings(self):
        # Proxy
        settings.set('proxy.enabled', self.proxy_enabled.isChecked())
        settings.set('proxy.type', self.proxy_type.currentText())
        settings.set('proxy.host', self.proxy_host.text().strip())
        settings.set('proxy.port', self.proxy_port.text().strip())
        settings.set('proxy.username', self.proxy_user.text().strip())
        settings.set('proxy.password', self.proxy_pass.text())
        
        # Download
        settings.set('download.threads', self.threads_spin.value())
        settings.set('download.auto_start', self.auto_start.isChecked())
        
        # YouTube
        quality_map = ['best', '2160p', '1080p', '720p', '480p', '360p']
        settings.set('youtube.preferred_quality', quality_map[self.yt_quality.currentIndex()])
        settings.set('youtube.prefer_mp4', self.yt_mp4.isChecked())
        
        settings.save()
        
        QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        self.accept()
    
    def test_proxy(self):
        """Test if proxy connection works"""
        if not self.proxy_enabled.isChecked():
            QMessageBox.warning(self, "Proxy Disabled", "Enable proxy first to test it.")
            return
        
        host = self.proxy_host.text().strip()
        port = self.proxy_port.text().strip()
        
        if not host or not port:
            QMessageBox.warning(self, "Missing Info", "Please enter proxy host and port.")
            return
        
        # Build proxy URL
        proxy_type = self.proxy_type.currentText()
        username = self.proxy_user.text().strip()
        password = self.proxy_pass.text()
        
        if username and password:
            proxy_url = f"{proxy_type}://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"{proxy_type}://{host}:{port}"
        
        # Test connection
        self.test_btn.setText("Testing...")
        self.test_btn.setEnabled(False)
        
        from PySide6.QtCore import QThread, Signal
        
        class ProxyTester(QThread):
            result = Signal(bool, str)
            
            def __init__(self, proxy_url):
                super().__init__()
                self.proxy_url = proxy_url
            
            def run(self):
                import requests
                try:
                    proxies = {"http": self.proxy_url, "https": self.proxy_url}
                    
                    # Test with YouTube
                    response = requests.get(
                        "https://www.youtube.com",
                        proxies=proxies,
                        timeout=10,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    
                    if response.status_code == 200:
                        self.result.emit(True, "Proxy connection successful!")
                    else:
                        self.result.emit(False, f"Got status code: {response.status_code}")
                        
                except requests.exceptions.ProxyError as e:
                    self.result.emit(False, f"Proxy error: Could not connect to proxy")
                except requests.exceptions.Timeout:
                    self.result.emit(False, "Connection timed out")
                except Exception as e:
                    self.result.emit(False, f"Error: {str(e)}")
        
        def on_result(success, message):
            self.test_btn.setText("Test Proxy")
            self.test_btn.setEnabled(True)
            
            if success:
                QMessageBox.information(self, "Proxy Test", f"✓ {message}")
            else:
                QMessageBox.warning(self, "Proxy Test Failed", f"✗ {message}")
        
        self._tester = ProxyTester(proxy_url)
        self._tester.result.connect(on_result)
        self._tester.start()
    
    def apply_theme(self):
        super().apply_theme()
        t = theme.current
        
        if not hasattr(self, 'tabs'):
            return
        
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {t['border_primary']};
                border-radius: 8px;
                background: {t['bg_secondary']};
            }}
            QTabBar::tab {{
                background: {t['bg_tertiary']};
                color: {t['text_secondary']};
                padding: 10px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            QTabBar::tab:selected {{
                background: {t['bg_secondary']};
                color: {t['text_primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {t['bg_hover']};
            }}
        """)
        
        # Form elements
        form_style = f"""
            QLineEdit, QComboBox, QSpinBox {{
                background: {t['bg_tertiary']};
                border: 1px solid {t['border_primary']};
                border-radius: 6px;
                padding: 8px 12px;
                color: {t['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border-color: {t['accent_primary']};
            }}
            QCheckBox {{
                color: {t['text_primary']};
                font-size: 13px;
            }}
            QGroupBox {{
                font-weight: bold;
                color: {t['text_primary']};
                border: 1px solid {t['border_primary']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
            QLabel {{
                color: {t['text_secondary']};
            }}
        """
        
        for tab_idx in range(self.tabs.count()):
            self.tabs.widget(tab_idx).setStyleSheet(form_style)