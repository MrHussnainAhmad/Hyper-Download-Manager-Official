from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


class ThemeManager(QObject):
    """
    Professional theme manager with comprehensive color palettes
    and stylesheet generators for consistent UI styling.
    """
    
    theme_changed = Signal(str)
    
    # ═══════════════════════════════════════════════════════════════
    #                         COLOR PALETTES
    # ═══════════════════════════════════════════════════════════════
    
    DARK_THEME = {
        "name": "dark",

        # Backgrounds – Light greys (NOT dark)
        "bg_primary": "#ECEFF1",
        "bg_secondary": "#E4E7EB",
        "bg_tertiary": "#DDE1E6",
        "bg_card": "#F2F4F6",
        "bg_hover": "#D6DADE",
        "bg_selected": "#CFE3F8",
        "bg_input": "#F2F4F6",
        # Specific component backgrounds
        "bg_sidebar": "#909090",  # Darker Grey
        "bg_toolbar": "#909090",  # Darker Grey
        "text_sidebar": "#FFFFFF", # White for sidebar
        "text_toolbar": "#FFFFFF", # White for toolbar
        "bg_overlay": "rgba(0, 0, 0, 0.25)",

        # Accents – Soft blue (not neon)
        "accent_primary": "#4A90E2",
        "accent_secondary": "#357ABD",
        "accent_tertiary": "#6BA4E7",
        "accent_gradient_start": "#6BA4E7",
        "accent_gradient_end": "#357ABD",
        "accent_success": "#4CAF50",
        "accent_warning": "#C9A227",
        "accent_error": "#E5533D",
        "accent_info": "#4A90E2",

        # Text – Dark grey (not pure black)
        "text_primary": "#2E3440",
        "text_secondary": "#4C566A",
        "text_muted": "#6B7280",
        "text_accent": "#357ABD",
        "text_inverse": "#FFFFFF",

        # Borders – Soft
        "border_primary": "#C5CBD3",
        "border_light": "#D8DDE3",
        "border_accent": "#4A90E2",
        "border_focus": "#4A90E2",

        # Progress
        "progress_bg": "#D1D5DB",
        "progress_fill": "#4A90E2",
        "progress_text": "#FFFFFF",

        # Scrollbar
        "scrollbar_bg": "#E4E7EB",
        "scrollbar_handle": "#C1C7CD",
        "scrollbar_hover": "#A8AFB7",

        # Status Colors
        "status_downloading": "#4A90E2",
        "status_completed": "#4CAF50",
        "status_paused": "#C9A227",
        "status_error": "#E5533D",
        "status_queued": "#6B7280",

        # Shadows – Very soft
        "shadow_color": "rgba(0, 0, 0, 0.12)",
        "shadow_color_strong": "rgba(0, 0, 0, 0.18)",
    }


    LIGHT_THEME = {
        "name": "light",

        # Backgrounds – Soft off-white (NOT pure white)
        "bg_primary": "#FAFAF8",
        "bg_secondary": "#F2F3F5",
        "bg_tertiary": "#E8EAED",
        "bg_card": "#FFFFFF",
        "bg_hover": "#E6E8EB",
        "bg_selected": "#E3F2FD",
        "bg_input": "#F2F3F5",
        # Specific component backgrounds
        "bg_sidebar": "#FFFFFF",  # Light White
        "bg_toolbar": "#FFFFFF",  # Light White
        "text_sidebar": "#000000", # Black for sidebar
        "text_toolbar": "#000000", # Black for toolbar
        "bg_overlay": "rgba(0, 0, 0, 0.3)",

        # Accents – Calm professional blue
        "accent_primary": "#3B82F6",
        "accent_secondary": "#2563EB",
        "accent_tertiary": "#60A5FA",
        "accent_gradient_start": "#60A5FA",
        "accent_gradient_end": "#2563EB",
        "accent_success": "#16A34A",
        "accent_warning": "#CA8A04",
        "accent_error": "#DC2626",
        "accent_info": "#3B82F6",

        # Text – Gentle contrast
        "text_primary": "#1F2933",
        "text_secondary": "#4B5563",
        "text_muted": "#6B7280",
        "text_accent": "#2563EB",
        "text_inverse": "#FFFFFF",

        # Borders
        "border_primary": "#D1D5DB",
        "border_light": "#E5E7EB",
        "border_accent": "#3B82F6",
        "border_focus": "#2563EB",

        # Progress
        "progress_bg": "#E5E7EB",
        "progress_fill": "#3B82F6",
        "progress_text": "#FFFFFF",

        # Scrollbar
        "scrollbar_bg": "#F2F3F5",
        "scrollbar_handle": "#C7CDD3",
        "scrollbar_hover": "#AEB5BC",

        # Status Colors
        "status_downloading": "#3B82F6",
        "status_completed": "#16A34A",
        "status_paused": "#CA8A04",
        "status_error": "#DC2626",
        "status_queued": "#6B7280",

        # Shadows
        "shadow_color": "rgba(0, 0, 0, 0.08)",
        "shadow_color_strong": "rgba(0, 0, 0, 0.15)",
    }

    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._current_theme = self.LIGHT_THEME
        
    @property
    def current(self) -> dict:
        """Get current theme dictionary"""
        return self._current_theme
    
    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark"""
        return self._current_theme["name"] == "dark"
    
    def set_theme(self, theme_name: str):
        """Set theme by name"""
        if theme_name == "dark":
            self._current_theme = self.DARK_THEME
        else:
            self._current_theme = self.LIGHT_THEME
        self.theme_changed.emit(theme_name)
        
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.is_dark:
            self.set_theme("light")
        else:
            self.set_theme("dark")
    
    def get(self, key: str, fallback: str = "#FF00FF") -> str:
        """Get a theme color by key with optional fallback"""
        return self._current_theme.get(key, fallback)
    
    # ═══════════════════════════════════════════════════════════════
    #                       STYLESHEET GENERATORS
    # ═══════════════════════════════════════════════════════════════
    
    def get_main_stylesheet(self) -> str:
        """Generate main application stylesheet"""
        t = self._current_theme
        return f"""
            * {{
                font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
                outline: none;
            }}
            
            QMainWindow {{
                background-color: {t['bg_primary']};
            }}
            
            QWidget {{
                background-color: transparent;
                color: {t['text_primary']};
            }}
            
            /* ══════════ SCROLLBARS ══════════ */
            QScrollBar:vertical {{
                background: {t['scrollbar_bg']};
                width: 12px;
                margin: 0;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {t['scrollbar_handle']};
                min-height: 40px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t['scrollbar_hover']};
            }}
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            
            QScrollBar:horizontal {{
                background: {t['scrollbar_bg']};
                height: 12px;
                margin: 0;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background: {t['scrollbar_handle']};
                min-width: 40px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {t['scrollbar_hover']};
            }}
            QScrollBar::add-line:horizontal, 
            QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            
            /* ══════════ TOOLTIPS ══════════ */
            QToolTip {{
                background-color: {t['bg_card']};
                color: {t['text_primary']};
                border: 1px solid {t['border_light']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 12px;
            }}
            
            /* ══════════ MENUS ══════════ */
            QMenu {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_primary']};
                border-radius: 12px;
                padding: 8px 0;
            }}
            QMenu::item {{
                padding: 12px 24px 12px 18px;
                color: {t['text_primary']};
                border-radius: 0;
                margin: 0 8px;
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: {t['bg_hover']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {t['border_primary']};
                margin: 8px 16px;
            }}
            QMenu::icon {{
                padding-left: 16px;
            }}
            
            QMenuBar {{
                background-color: {t['bg_secondary']};
                color: {t['text_primary']};
                border-bottom: 1px solid {t['border_primary']};
                padding: 6px 8px;
                spacing: 4px;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 10px 16px;
                border-radius: 6px;
            }}
            QMenuBar::item:selected {{
                background-color: {t['bg_hover']};
            }}
            QMenuBar::item:pressed {{
                background-color: {t['bg_selected']};
            }}
            
            /* ══════════ MESSAGE BOX ══════════ */
            QMessageBox {{
                background-color: {t['bg_card']};
            }}
            QMessageBox QLabel {{
                color: {t['text_primary']};
            }}
        """
    
    def get_dialog_stylesheet(self) -> str:
        """Generate dialog stylesheet"""
        t = self._current_theme
        return f"""
            QDialog {{
                background-color: {t['bg_primary']};
            }}
            
            QLabel {{
                color: {t['text_primary']};
                font-size: 13px;
                background: transparent;
            }}
            
            QLabel[class="title"] {{
                font-size: 20px;
                font-weight: 600;
                color: {t['text_primary']};
            }}
            
            QLabel[class="subtitle"] {{
                font-size: 13px;
                color: {t['text_secondary']};
            }}
            
            QLabel[class="section"] {{
                font-size: 11px;
                font-weight: 700;
                color: {t['text_muted']};
                text-transform: uppercase;
                letter-spacing: 1.5px;
            }}
            
            QLineEdit {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 2px solid {t['border_primary']};
                border-radius: 10px;
                padding: 14px 18px;
                font-size: 13px;
                selection-background-color: {t['accent_primary']};
                selection-color: {t['text_inverse']};
            }}
            QLineEdit:hover {{
                border-color: {t['border_light']};
            }}
            QLineEdit:focus {{
                border-color: {t['border_focus']};
                background-color: {t['bg_card']};
            }}
            QLineEdit:read-only {{
                background-color: {t['bg_tertiary']};
                color: {t['text_secondary']};
                border-color: {t['border_primary']};
            }}
            QLineEdit::placeholder {{
                color: {t['text_muted']};
            }}
            
            QProgressBar {{
                background-color: {t['progress_bg']};
                border: none;
                border-radius: 8px;
                height: 16px;
                text-align: center;
                font-size: 11px;
                font-weight: 700;
                color: {t['progress_text']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent_gradient_start']},
                    stop:1 {t['accent_gradient_end']});
                border-radius: 8px;
            }}
            
            QComboBox {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 2px solid {t['border_primary']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {t['border_light']};
            }}
            QComboBox:focus {{
                border-color: {t['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 16px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_primary']};
                border-radius: 10px;
                selection-background-color: {t['bg_hover']};
                selection-color: {t['text_primary']};
                padding: 8px;
            }}
            
            QSpinBox {{
                background-color: {t['bg_input']};
                color: {t['text_primary']};
                border: 2px solid {t['border_primary']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
            }}
            QSpinBox:hover {{
                border-color: {t['border_light']};
            }}
            QSpinBox:focus {{
                border-color: {t['border_focus']};
            }}
            
            QCheckBox {{
                color: {t['text_primary']};
                font-size: 13px;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 22px;
                height: 22px;
                border-radius: 6px;
                border: 2px solid {t['border_primary']};
                background-color: {t['bg_input']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {t['accent_primary']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {t['accent_primary']};
                border-color: {t['accent_primary']};
            }}
        """
    
    def get_button_stylesheet(self, variant: str = "primary") -> str:
        """Generate button stylesheet for specified variant"""
        t = self._current_theme
        
        if variant == "primary":
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {t['accent_gradient_start']},
                        stop:1 {t['accent_gradient_end']});
                    color: {t['text_inverse']};
                    border: none;
                    border-radius: 10px;
                    padding: 14px 28px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {t['accent_gradient_end']},
                        stop:1 {t['accent_gradient_start']});
                }}
                QPushButton:pressed {{
                    background-color: {t['accent_secondary']};
                }}
                QPushButton:disabled {{
                    background-color: {t['bg_tertiary']};
                    color: {t['text_muted']};
                }}
            """
        elif variant == "secondary":
            return f"""
                QPushButton {{
                    background-color: {t['bg_tertiary']};
                    color: {t['text_primary']};
                    border: 2px solid {t['border_primary']};
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {t['bg_hover']};
                    border-color: {t['accent_primary']};
                    color: {t['accent_primary']};
                }}
                QPushButton:pressed {{
                    background-color: {t['bg_selected']};
                }}
                QPushButton:disabled {{
                    background-color: {t['bg_tertiary']};
                    color: {t['text_muted']};
                    border-color: {t['border_primary']};
                }}
            """
        elif variant == "ghost":
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t['text_secondary']};
                    border: none;
                    border-radius: 10px;
                    padding: 12px 20px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {t['bg_hover']};
                    color: {t['text_primary']};
                }}
                QPushButton:pressed {{
                    background-color: {t['bg_selected']};
                }}
                QPushButton:disabled {{
                    color: {t['text_muted']};
                }}
            """
        elif variant == "danger":
            return f"""
                QPushButton {{
                    background-color: {t['accent_error']};
                    color: {t['text_inverse']};
                    border: none;
                    border-radius: 10px;
                    padding: 14px 28px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #FF6B6B;
                }}
                QPushButton:pressed {{
                    background-color: #E04545;
                }}
                QPushButton:disabled {{
                    background-color: {t['bg_tertiary']};
                    color: {t['text_muted']};
                }}
            """
        elif variant == "icon":
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t['text_secondary']};
                    border: none;
                    border-radius: 10px;
                    padding: 12px;
                }}
                QPushButton:hover {{
                    background-color: {t['bg_hover']};
                    color: {t['accent_primary']};
                }}
                QPushButton:pressed {{
                    background-color: {t['bg_selected']};
                }}
                QPushButton:disabled {{
                    color: {t['text_muted']};
                }}
            """
        elif variant == "success":
            return f"""
                QPushButton {{
                    background-color: {t['accent_success']};
                    color: {t['text_inverse']};
                    border: none;
                    border-radius: 10px;
                    padding: 14px 28px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #4AE066;
                }}
                QPushButton:pressed {{
                    background-color: #2EA043;
                }}
            """
        
        return ""
    
    def get_tab_stylesheet(self) -> str:
        """Generate tab widget stylesheet"""
        t = self._current_theme
        return f"""
            QTabWidget::pane {{
                border: 1px solid {t['border_primary']};
                border-radius: 12px;
                background-color: {t['bg_card']};
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background-color: {t['bg_secondary']};
                color: {t['text_secondary']};
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: 1px solid {t['border_primary']};
                border-bottom: none;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {t['bg_card']};
                color: {t['accent_primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {t['bg_hover']};
                color: {t['text_primary']};
            }}
        """


# Global instance
theme = ThemeManager()