from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                               QPushButton, QFrame, QGraphicsDropShadowEffect,
                               QSizePolicy, QProgressBar)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPainter, QPainterPath, QLinearGradient, QFont, QIcon
from ui.theme_manager import theme
from ui.icons import IconProvider, IconType, get_icon, get_pixmap


# ═══════════════════════════════════════════════════════════════════════════════
#                              ICON BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

class IconButton(QPushButton):
    """Modern icon button with optional text - uses vector icons"""
    
    def __init__(self, icon_type: IconType = None, text: str = "", 
                 tooltip: str = "", variant: str = "ghost", 
                 icon_size: int = 18, parent=None):
        super().__init__(parent)
        
        self._icon_type = icon_type
        self._label_text = text
        self._variant = variant
        self._icon_size = icon_size
        
        if text:
            self.setText(text)
            
        if tooltip:
            self.setToolTip(tooltip)
            
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 11))
        self.apply_theme()
        
    def apply_theme(self):
        self.setStyleSheet(theme.get_button_stylesheet(self._variant))
        self._update_icon()
        
    def _update_icon(self):
        if self._icon_type is None:
            return
            
        t = theme.current
        
        # Choose icon color based on variant
        if self._variant == "primary":
            color = "#FFFFFF"
        elif self._variant == "danger":
            color = "#FFFFFF"
        else:
            color = t['text_secondary']
            
        icon = get_icon(self._icon_type, color, self._icon_size)
        self.setIcon(icon)
        self.setIconSize(QSize(self._icon_size, self._icon_size))
        
    def set_variant(self, variant: str):
        self._variant = variant
        self.apply_theme()
        
    def set_icon_type(self, icon_type: IconType):
        self._icon_type = icon_type
        self._update_icon()


class ToolbarButton(QPushButton):
    """Toolbar button with icon and label below - uses vector icons"""
    
    def __init__(self, icon_type: IconType, text: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(72, 64)
        self.setCursor(Qt.PointingHandCursor)
        
        if tooltip:
            self.setToolTip(tooltip)
        
        self._icon_type = icon_type
        self._text = text
        self._hovered = False
        
        self.apply_theme()
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
                color: {t['text_secondary']};
                font-size: 11px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {t['bg_hover']};
            }}
            QPushButton:pressed {{
                background-color: {t['bg_selected']};
            }}
            QPushButton:disabled {{
                color: {t['text_muted']};
            }}
        """)
        self.update()
        
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        t = theme.current
        color = t['accent_primary'] if self._hovered else t['text_secondary']
        
        # Draw icon
        icon_size = 24
        icon_pixmap = get_pixmap(self._icon_type, color, icon_size)
        icon_x = (self.width() - icon_size) // 2
        icon_y = 10
        painter.drawPixmap(icon_x, icon_y, icon_pixmap)
        
        # Draw text
        painter.setPen(QColor(color))
        text_font = QFont("Segoe UI", 10)
        text_font.setWeight(QFont.Medium)
        painter.setFont(text_font)
        text_rect = self.rect().adjusted(0, 40, 0, 0)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, self._text)


# ═══════════════════════════════════════════════════════════════════════════════
#                              ICON LABEL
# ═══════════════════════════════════════════════════════════════════════════════

class IconLabel(QLabel):
    """Label that displays a vector icon"""
    
    def __init__(self, icon_type: IconType, size: int = 24, 
                 color: str = None, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type
        self._size = size
        self._color = color
        self.setFixedSize(size, size)
        self.apply_theme()
        
    def apply_theme(self):
        t = theme.current
        color = self._color or t['accent_primary']
        pixmap = get_pixmap(self._icon_type, color, self._size)
        self.setPixmap(pixmap)
        
    def set_color(self, color: str):
        self._color = color
        self.apply_theme()


# ═══════════════════════════════════════════════════════════════════════════════
#                              CARD WIDGET
# ═══════════════════════════════════════════════════════════════════════════════

class Card(QFrame):
    """Modern card container with optional shadow"""
    
    def __init__(self, parent=None, shadow: bool = True):
        super().__init__(parent)
        self.setObjectName("card")
        
        if shadow and theme.is_dark:
            self._add_shadow()
            
        self.apply_theme()
        
    def _add_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_primary']};
                border-radius: 16px;
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
#                              STATUS BADGE
# ═══════════════════════════════════════════════════════════════════════════════

class StatusBadge(QLabel):
    """Colored status indicator badge with icon"""
    
    STATUS_CONFIG = {
        "Downloading": ("status_downloading", IconType.DOWNLOAD),
        "Completed": ("status_completed", IconType.COMPLETE),
        "Finished": ("status_completed", IconType.COMPLETE),
        "Paused": ("status_paused", IconType.PAUSE),
        "Error": ("status_error", IconType.ERROR),
        "Queued": ("status_queued", IconType.QUEUE),
        "Idle": ("status_queued", IconType.CLOCK),
        "Stopped": ("status_paused", IconType.STOP),
    }
    
    def __init__(self, status: str = "Queued", parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(28)
        self.setMinimumWidth(100)
        self.set_status(status)
        
    def set_status(self, status: str):
        config = self.STATUS_CONFIG.get(status, ("status_queued", IconType.QUEUE))
        color_key, icon_type = config
        
        t = theme.current
        color = t[color_key]
        
        # Create semi-transparent background
        bg_color = QColor(color)
        bg_color.setAlpha(30)
        
        self.setText(f"  {status}")
        
        # Set icon
        icon_pixmap = get_pixmap(icon_type, color, 14)
        # We'll use a compound widget approach for icon + text
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color.name(QColor.HexArgb)};
                color: {color};
                border-radius: 14px;
                padding: 4px 14px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
#                           ANIMATED PROGRESS BAR
# ═══════════════════════════════════════════════════════════════════════════════

class AnimatedProgressBar(QProgressBar):
    """Progress bar with gradient and smooth corners"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setFixedHeight(22)
        self.apply_theme()
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {t['progress_bg']};
                border: none;
                border-radius: 11px;
                text-align: center;
                font-size: 11px;
                font-weight: 600;
                color: {t['text_primary']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent_gradient_start']},
                    stop:1 {t['accent_gradient_end']});
                border-radius: 11px;
            }}
        """)


# ═══════════════════════════════════════════════════════════════════════════════
#                              SECTION HEADER
# ═══════════════════════════════════════════════════════════════════════════════

class SectionHeader(QWidget):
    """Section header with title and optional action button"""
    
    def __init__(self, title: str, icon_type: IconType = None, 
                 action_text: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 8)
        layout.setSpacing(8)
        
        # Optional icon
        if icon_type:
            self.icon_label = IconLabel(icon_type, 16)
            layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "section")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        if action_text:
            self.action_btn = IconButton(text=action_text, variant="ghost")
            layout.addWidget(self.action_btn)
            
        self.apply_theme()
        
    def apply_theme(self):
        t = theme.current
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 700;
                color: {t['text_muted']};
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }}
        """)
        if hasattr(self, 'icon_label'):
            self.icon_label.set_color(t['text_muted'])


# ═══════════════════════════════════════════════════════════════════════════════
#                              DIVIDER
# ═══════════════════════════════════════════════════════════════════════════════

class Divider(QFrame):
    """Horizontal divider line"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.apply_theme()
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(f"background-color: {t['border_primary']};")


# ═══════════════════════════════════════════════════════════════════════════════
#                              STAT CARD
# ═══════════════════════════════════════════════════════════════════════════════

class StatCard(QFrame):
    """Mini card for displaying statistics with icon"""
    
    def __init__(self, icon_type: IconType, title: str, 
                 value: str = "-", parent=None):
        super().__init__(parent)
        self.setFixedHeight(76)
        self._icon_type = icon_type
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        
        # Icon container with background
        self.icon_container = QFrame()
        self.icon_container.setFixedSize(44, 44)
        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_label = IconLabel(icon_type, 22)
        icon_layout.addWidget(self.icon_label)
        layout.addWidget(self.icon_container)
        
        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self.title_label = QLabel(title)
        self.value_label = QLabel(value)
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        self.apply_theme()
        
    def set_value(self, value: str):
        self.value_label.setText(value)
        
    def apply_theme(self):
        t = theme.current
        
        # Main card styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_primary']};
                border-radius: 12px;
            }}
        """)
        
        # Icon container with subtle accent background
        accent_bg = QColor(t['accent_primary'])
        accent_bg.setAlpha(20)
        self.icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {accent_bg.name(QColor.HexArgb)};
                border-radius: 10px;
                border: none;
            }}
        """)
        
        self.title_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {t['text_muted']};
            background: transparent;
            border: none;
        """)
        self.value_label.setStyleSheet(f"""
            font-size: 17px;
            font-weight: 700;
            color: {t['text_primary']};
            background: transparent;
            border: none;
        """)
        self.icon_label.apply_theme()


# ═══════════════════════════════════════════════════════════════════════════════
#                           EMPTY STATE
# ═══════════════════════════════════════════════════════════════════════════════

class EmptyState(QWidget):
    """Empty state placeholder with icon and message"""
    
    action_clicked = Signal()
    
    def __init__(self, icon_type: IconType, title: str, 
                 message: str = "", action_text: str = "", parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        
        # Large icon
        self.icon_label = IconLabel(icon_type, 64)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.DemiBold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Message
        if message:
            self.message_label = QLabel(message)
            self.message_label.setFont(QFont("Segoe UI", 12))
            self.message_label.setAlignment(Qt.AlignCenter)
            self.message_label.setWordWrap(True)
            layout.addWidget(self.message_label)
        
        # Action button
        if action_text:
            layout.addSpacing(8)
            self.action_btn = IconButton(
                icon_type=IconType.ADD,
                text=action_text,
                variant="primary"
            )
            self.action_btn.clicked.connect(self.action_clicked.emit)
            layout.addWidget(self.action_btn, alignment=Qt.AlignCenter)
        
        self.apply_theme()
        
    def apply_theme(self):
        t = theme.current
        self.title_label.setStyleSheet(f"color: {t['text_primary']};")
        if hasattr(self, 'message_label'):
            self.message_label.setStyleSheet(f"color: {t['text_muted']};")
        self.icon_label.set_color(t['text_muted'])
        if hasattr(self, 'action_btn'):
            self.action_btn.apply_theme()