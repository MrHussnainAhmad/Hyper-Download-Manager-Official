import os
import json
from PySide6.QtCore import QStandardPaths

class Settings:
    """Application settings manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Settings file path
        self.config_dir = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.AppDataLocation),
            "HyperDownloadManager"
        )
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
        # Default settings
        self._defaults = {
            "proxy": {
                "enabled": False,
                "type": "http",  # http, https, socks5
                "host": "",
                "port": "",
                "username": "",
                "password": "",
            },
            "download": {
                "threads": 4,
                "auto_start": True,
                "default_path": QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),
                "socket_timeout": 60,  # Socket timeout in seconds
                "max_retries": 10,     # Maximum retry attempts
            }
            # Removed youtube.preferred_quality - quality is selected via extension only
        }
        
        self._settings = {}
        self._ensure_config_dir()
        self.load()
    
    def _ensure_config_dir(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
    
    def load(self):
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self._settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                self._settings = {}
        else:
            self._settings = {}
    
    def save(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self._settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key, default=None):
        """Get a setting value using dot notation (e.g., 'proxy.enabled')"""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Try defaults
                value = self._defaults
                for k2 in keys:
                    if isinstance(value, dict) and k2 in value:
                        value = value[k2]
                    else:
                        return default
                return value
        
        return value
    
    def set(self, key, value):
        """Set a setting value using dot notation"""
        keys = key.split('.')
        d = self._settings
        
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        
        d[keys[-1]] = value
        self.save()
    
    def get_proxy_url(self):
        """Get formatted proxy URL for use with requests/yt-dlp"""
        if not self.get('proxy.enabled'):
            return None
        
        host = self.get('proxy.host', '').strip()
        port = self.get('proxy.port', '').strip()
        
        if not host or not port:
            return None
        
        proxy_type = self.get('proxy.type', 'http')
        username = self.get('proxy.username', '').strip()
        password = self.get('proxy.password', '').strip()
        
        if username and password:
            return f"{proxy_type}://{username}:{password}@{host}:{port}"
        else:
            return f"{proxy_type}://{host}:{port}"
    
    def get_proxy_dict(self):
        """Get proxy dict for requests library"""
        url = self.get_proxy_url()
        if url:
            return {"http": url, "https": url}
        return None


# Global settings instance
settings = Settings()