from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                               QPushButton, QFrame, QSizePolicy, QSpacerItem,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient

from ui.theme_manager import theme
from ui.icons import IconType, IconProvider, get_pixmap, get_icon
from ui.components import IconButton, IconLabel, Divider
from utils.helpers import format_speed


class SpeedGraph(QFrame):
    """Mini speed graph visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._values = [0] * 20
        self._max_value = 1
        
    def add_value(self, value):
        self._values.pop(0)
        self._values.append(value)
        if value > 0:
            self._max_value = max(self._max_value, value * 1.2)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        t = theme.current
        
        # Background
        painter.fillRect(self.rect(), QColor(t['bg_tertiary']))
        
        if self._max_value <= 0:
            return
            
        # Draw graph
        points = []
        width = self.width()
        height = self.height()
        step = width / (len(self._values) - 1)
        
        for i, val in enumerate(self._values):
            x = i * step
            y = height - (val / self._max_value) * (height - 4) - 2
            points.append((x, y))
        
        # Gradient fill
        if len(points) > 1:
            gradient = QLinearGradient(0, 0, 0, height)
            accent = QColor(t['accent_primary'])
            accent.setAlpha(100)
            gradient.setColorAt(0, accent)
            accent.setAlpha(20)
            gradient.setColorAt(1, accent)
            
            from PySide6.QtGui import QPainterPath, QPolygonF
            from PySide6.QtCore import QPointF
            
            path = QPainterPath()
            path.moveTo(0, height)
            for x, y in points:
                path.lineTo(x, y)
            path.lineTo(width, height)
            path.closeSubpath()
            
            painter.fillPath(path, gradient)
            
            # Line
            pen = QPen(QColor(t['accent_primary']))
            pen.setWidth(2)
            painter.setPen(pen)
            
            for i in range(len(points) - 1):
                painter.drawLine(QPointF(*points[i]), QPointF(*points[i + 1]))


class SpeedMonitor(QFrame):
    """Modern speed monitor widget with graph"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("speedMonitor")
        self.setFixedSize(120, 48)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)
        
        # Speed value
        self.speed_label = QLabel("0 B/s")
        self.speed_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.speed_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.speed_label)
        
        # Subtitle
        subtitle = QLabel("Speed")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet(f"color: {theme.current['text_muted']};")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        self._speed_history = []
        self.apply_theme()
        
    def update_speed(self, speed):
        self.speed_label.setText(format_speed(speed))
        self._speed_history.append(speed)
        if len(self._speed_history) > 20:
            self._speed_history.pop(0)
        
    def set_offline(self, is_offline):
        # Removed visual indicator as requested
        pass
            
    def apply_theme(self):
        t = theme.current
        
        # Card background with subtle border
        self.setStyleSheet(f"""
            QFrame#speedMonitor {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_primary']};
                border-radius: 12px;
            }}
        """)
        
        self.speed_label.setStyleSheet(f"color: {t['accent_primary']}; background: transparent;")



class ToolbarSeparator(QFrame):
    """Vertical separator for toolbar"""
    
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFixedSize(1, 44)
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(f"background-color: {t['border_primary']};")


class ToolbarButton(QPushButton):
    """Toolbar button with icon and label - uses vector icons"""
    
    def __init__(self, icon_type: IconType, text: str, tooltip: str = "", 
                 accent: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(76, 68)
        self.setCursor(Qt.PointingHandCursor)
        
        if tooltip:
            self.setToolTip(tooltip)
        
        self._icon_type = icon_type
        self._text = text
        self._hovered = False
        self._pressed = False
        self._accent = accent
        
        self.apply_theme()
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 12px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {t['bg_hover']};
            }}
            QPushButton:pressed {{
                background-color: {t['bg_selected']};
            }}
            QPushButton:disabled {{
                opacity: 0.5;
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
        
    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        t = theme.current
        
        # Determine colors based on state
        if self._accent:
            if theme.is_dark and self._text == "Add URL":
                icon_color = "#FFFFFF"
                text_color = "#FFFFFF"
            else:
                icon_color = t['accent_primary']
                text_color = t['accent_primary'] if self._hovered else t['text_secondary']
        else:
            icon_color = t['accent_primary'] if self._hovered else t['text_toolbar']
            text_color = t['text_primary'] if self._hovered else t['text_toolbar']
        
        if not self.isEnabled():
            icon_color = t['text_muted']
            text_color = t['text_muted']
        
        # Draw icon
        icon_size = 26
        icon_pixmap = get_pixmap(self._icon_type, icon_color, icon_size)
        icon_x = (self.width() - icon_size) // 2
        icon_y = 12
        painter.drawPixmap(icon_x, icon_y, icon_pixmap)
        
        # Draw text
        painter.setPen(QColor(text_color))
        text_font = QFont("Segoe UI", 10)
        text_font.setWeight(QFont.Medium)
        painter.setFont(text_font)
        text_rect = self.rect().adjusted(0, 44, 0, 0)
        painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, self._text)


class MainToolbar(QWidget):
    """Modern toolbar with icon buttons"""
    
    # Signals for actions
    add_clicked = Signal()
    resume_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    remove_clicked = Signal()
    start_all_clicked = Signal()
    pause_all_clicked = Signal()
    settings_clicked = Signal()
    theme_toggle_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("toolbar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(88)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(6)
        
        # Primary Action - Add (highlighted)
        self.add_btn = ToolbarButton(IconType.ADD, "Add URL", "Add new download (Ctrl+N)", accent=True)
        self.add_btn.clicked.connect(self.add_clicked.emit)
        layout.addWidget(self.add_btn)
        
        layout.addSpacing(8)
        
        # Separator
        self.sep1 = ToolbarSeparator()
        layout.addWidget(self.sep1)
        
        layout.addSpacing(8)
        
        # Download Control Buttons
        self.resume_btn = ToolbarButton(IconType.RESUME, "Resume", "Resume selected download")
        self.resume_btn.clicked.connect(self.resume_clicked.emit)
        layout.addWidget(self.resume_btn)
        
        self.pause_btn = ToolbarButton(IconType.PAUSE, "Pause", "Pause selected download")
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        layout.addWidget(self.pause_btn)
        
        self.stop_btn = ToolbarButton(IconType.STOP, "Stop", "Stop selected download")
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self.stop_btn)
        
        self.remove_btn = ToolbarButton(IconType.DELETE, "Remove", "Remove selected download")
        self.remove_btn.clicked.connect(self.remove_clicked.emit)
        layout.addWidget(self.remove_btn)
        
        layout.addSpacing(8)
        
        # Separator
        self.sep2 = ToolbarSeparator()
        layout.addWidget(self.sep2)
        
        layout.addSpacing(8)
        
        # Batch Actions
        self.start_all_btn = ToolbarButton(IconType.DOWNLOAD, "Start All", "Start all queued downloads")
        self.start_all_btn.clicked.connect(self.start_all_clicked.emit)
        layout.addWidget(self.start_all_btn)
        
        self.pause_all_btn = ToolbarButton(IconType.PAUSE, "Pause All", "Pause all active downloads")
        self.pause_all_btn.clicked.connect(self.pause_all_clicked.emit)
        layout.addWidget(self.pause_all_btn)
        
        # Spacer
        layout.addStretch()
        
        # Speed Monitor
        self.speed_monitor = SpeedMonitor()
        layout.addWidget(self.speed_monitor)
        
        layout.addSpacing(20)
        
        # Separator
        self.sep3 = ToolbarSeparator()
        layout.addWidget(self.sep3)
        
        layout.addSpacing(12)
        
        # Theme Toggle
        self.theme_btn = IconButton(
            icon_type=IconType.THEME_DARK if theme.is_dark else IconType.THEME_LIGHT,
            variant="icon",
            tooltip="Toggle Theme (Ctrl+T)",
            icon_size=22
        )
        self.theme_btn.setFixedSize(48, 48)
        self.theme_btn.clicked.connect(self._on_theme_toggle)
        layout.addWidget(self.theme_btn)
        
        # Settings button removed as per user request
        
        self.apply_theme()
        
    def _on_theme_toggle(self):
        theme.toggle_theme()
        self.theme_toggle_clicked.emit()
        
    def update_theme_icon(self):
        icon_type = IconType.THEME_DARK if theme.is_dark else IconType.THEME_LIGHT
        self.theme_btn.set_icon_type(icon_type)
        
    def apply_theme(self):
        t = theme.current
        
        # Main toolbar background
        self.setStyleSheet(f"""
            QWidget#toolbar {{
                background-color: {t['bg_toolbar']};
                border-bottom: 1px solid {t['border_primary']};
            }}
        """)
        
        # Update all toolbar buttons
        for btn in [self.add_btn, self.resume_btn, self.pause_btn, 
                    self.stop_btn, self.remove_btn, self.start_all_btn, 
                    self.pause_all_btn]:
            btn.apply_theme()
        
        # Update separators
        for sep in [self.sep1, self.sep2, self.sep3]:
            sep.apply_theme()
            
        # Update other components
        self.speed_monitor.apply_theme()
        self.theme_btn.apply_theme()
        self.update_theme_icon()