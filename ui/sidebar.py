from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                               QLabel, QProgressBar, QFrame, QHBoxLayout, QSpacerItem,
                               QSizePolicy, QGraphicsDropShadowEffect, QStyle)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QPixmap

from ui.theme_manager import theme
from ui.icons import IconType, IconProvider, get_pixmap, get_icon
from ui.components import IconLabel, Divider, IconButton
from utils.helpers import format_bytes


class CategoryItem(QTreeWidgetItem):
    """Custom category item with icon"""
    
    def __init__(self, icon_type: IconType, text: str, count: int = 0):
        super().__init__()
        self.icon_type = icon_type
        self.text = text
        self.count = count
        self.update_display()
        
    def update_display(self):
        display = self.text
        if self.count > 0:
            display += f"  ({self.count})"
        self.setText(0, display)
        
    def set_count(self, count: int):
        self.count = count
        self.update_display()


class CategoryDelegate(QWidget):
    """Custom widget for category items"""
    pass


class StorageWidget(QFrame):
    """Modern storage usage widget with gradient"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("storageWidget")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        
        self.icon_label = IconLabel(IconType.STORAGE, 22)
        header.addWidget(self.icon_label)
        
        title = QLabel("Storage")
        title.setFont(QFont("Segoe UI", 13, QFont.DemiBold))
        header.addWidget(title)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Progress bar with custom painting
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(10)
        layout.addWidget(self.bar)
        
        # Info row
        info_layout = QHBoxLayout()
        info_layout.setSpacing(4)
        
        self.label = QLabel("Loading...")
        self.label.setFont(QFont("Segoe UI", 11))
        info_layout.addWidget(self.label)
        
        info_layout.addStretch()
        
        self.percent_label = QLabel("0%")
        self.percent_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        info_layout.addWidget(self.percent_label)
        
        layout.addLayout(info_layout)
        
        self.apply_theme()

    def update_usage(self, free, total, percent):
        self.bar.setValue(int(percent))
        self.label.setText(f"{format_bytes(free)} free of {format_bytes(total)}")
        self.percent_label.setText(f"{int(percent)}%")
        
        t = theme.current
        if percent > 90:
            bar_color = t['accent_error']
            self.percent_label.setStyleSheet(f"color: {t['accent_error']};")
        elif percent > 70:
            bar_color = t['accent_warning']
            self.percent_label.setStyleSheet(f"color: {t['accent_warning']};")
        else:
            bar_color = t['accent_primary']
            self.percent_label.setStyleSheet(f"color: {t['accent_primary']};")
            
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {t['bg_tertiary']};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent_gradient_start']},
                    stop:1 {bar_color});
                border-radius: 5px;
            }}
        """)
        
    def apply_theme(self):
        t = theme.current
        self.setStyleSheet(f"""
            QFrame#storageWidget {{
                background-color: {t['bg_card']};
                border: 1px solid {t['border_primary']};
                border-radius: 14px;
            }}
            QLabel {{
                color: {t['text_primary']};
                background: transparent;
            }}
        """)
        self.label.setStyleSheet(f"color: {t['text_muted']};")
        self.icon_label.apply_theme()


class SidebarCategoryTree(QTreeWidget):
    """Custom tree widget for sidebar categories"""
    
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setIndentation(0)
        self.setAnimated(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setIconSize(QSize(20, 20))
        
    def drawRow(self, painter, option, index):
        """Custom row drawing with icon"""
        item = self.itemFromIndex(index)
        if not isinstance(item, CategoryItem):
            super().drawRow(painter, option, index)
            return
            
        t = theme.current
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.visualRect(index)
        is_selected = item.isSelected()
        is_hovered = bool(option.state & QStyle.State_MouseOver)
        
        # Background
        if is_selected:
            bg_color = QColor(t['bg_selected'])
            painter.setBrush(bg_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect.adjusted(8, 2, -8, -2), 10, 10)
        
        # Icon
        icon_size = 20
        icon_x = rect.left() + 20
        icon_y = rect.center().y() - icon_size // 2
        
        icon_color = t['accent_primary'] if is_selected else t['text_secondary']
        pixmap = get_pixmap(item.icon_type, icon_color, icon_size)
        painter.drawPixmap(icon_x, icon_y, pixmap)
        
        # Text
        text_x = icon_x + icon_size + 14
        text_color = t['accent_primary'] if is_selected else t['text_sidebar']
        painter.setPen(QColor(text_color))
        
        font = QFont("Segoe UI", 13)
        font.setWeight(QFont.Medium if is_selected else QFont.Normal)
        painter.setFont(font)
        
        text_rect = rect.adjusted(text_x, 0, -50, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, item.text)
        
        # Count badge
        if item.count > 0:
            badge_text = str(item.count)
            badge_font = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(badge_font)
            
            badge_width = max(24, len(badge_text) * 10 + 12)
            badge_height = 22
            badge_x = rect.right() - badge_width - 16
            badge_y = rect.center().y() - badge_height // 2
            badge_rect = rect.adjusted(badge_x - rect.left(), badge_y - rect.top(), 
                                        -16, -(rect.height() - badge_height) // 2)
            badge_rect.setWidth(badge_width)
            badge_rect.setHeight(badge_height)
            badge_rect.moveCenter(rect.center())
            badge_rect.moveRight(rect.right() - 16)
            
            # Badge background
            badge_bg = QColor(t['accent_primary'] if is_selected else t['bg_tertiary'])
            if not is_selected:
                badge_bg.setAlpha(180)
            painter.setBrush(badge_bg)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge_x, badge_y, badge_width, badge_height, 11, 11)
            
            # Badge text
            painter.setPen(QColor("#FFFFFF" if is_selected else t['text_secondary']))
            painter.drawText(badge_x, badge_y, badge_width, badge_height,
                           Qt.AlignCenter, badge_text)
        
        painter.restore()


class Sidebar(QWidget):
    """Modern sidebar navigation"""
    
    category_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(8)
        
        # App Title/Logo
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(12)
        logo_layout.setContentsMargins(8, 0, 8, 0)
        
        # Logo icon container
        logo_container = QFrame()
        logo_container.setFixedSize(48, 48)
        logo_container_layout = QVBoxLayout(logo_container)
        logo_container_layout.setContentsMargins(0, 0, 0, 0)
        logo_container_layout.setAlignment(Qt.AlignCenter)
        
        self.logo_icon = QLabel()
        self.logo_icon.setFixedSize(40, 40)
        self.logo_icon.setScaledContents(True)
        from utils.helpers import get_resource_path
        self.logo_icon.setPixmap(QPixmap(get_resource_path("icon.png")))
        logo_container_layout.addWidget(self.logo_icon)
        
        logo_layout.addWidget(logo_container)
        
        # App name
        name_layout = QVBoxLayout()
        name_layout.setSpacing(0)
        
        logo_text = QLabel("Hyper Download")
        logo_text.setFont(QFont("Segoe UI", 15, QFont.Bold))
        name_layout.addWidget(logo_text)
        
        logo_subtitle = QLabel("Manager")
        logo_subtitle.setFont(QFont("Segoe UI", 11))
        name_layout.addWidget(logo_subtitle)
        
        logo_layout.addLayout(name_layout)
        logo_layout.addStretch()
        
        layout.addLayout(logo_layout)
        layout.addSpacing(24)
        
        # Section label
        section_label = QLabel("DOWNLOADS")
        section_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        section_label.setContentsMargins(12, 0, 0, 8)
        layout.addWidget(section_label)
        
        # Category Tree
        self.tree = SidebarCategoryTree()
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Add categories
        self.categories = {}
        category_data = [
            (IconType.DOWNLOAD, "All Downloads"),
            (IconType.CLOCK, "Unfinished"),
            (IconType.COMPLETE, "Finished"),
            (IconType.QUEUE, "Queued"),
        ]
        
        for icon_type, name in category_data:
            item = CategoryItem(icon_type, name)
            self.tree.addTopLevelItem(item)
            self.categories[name] = item
            
        self.tree.setCurrentItem(self.tree.topLevelItem(0))
        self.tree.itemClicked.connect(self._on_item_clicked)
        
        layout.addWidget(self.tree)
        
        layout.addStretch()
        
        # Divider
        layout.addWidget(Divider())
        layout.addSpacing(12)
        
        # Storage Widget
        self.storage = StorageWidget()
        layout.addWidget(self.storage)
        
        # Version info
        try:
            with open("version.txt", "r") as f:
                version_text = f"v{f.read().strip()}"
        except:
            version_text = "v1.0.0"
            
        self.version_label = QLabel(version_text)
        self.version_label.setFont(QFont("Segoe UI", 10))
        self.version_label.setAlignment(Qt.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(self.version_label)
        
        self.apply_theme()
        
    def _on_item_clicked(self, item, column):
        if isinstance(item, CategoryItem):
            self.category_changed.emit(item.text)
            
    def update_counts(self, all_count: int, unfinished: int, finished: int, queued: int):
        self.categories["All Downloads"].set_count(all_count)
        self.categories["Unfinished"].set_count(unfinished)
        self.categories["Finished"].set_count(finished)
        self.categories["Queued"].set_count(queued)
        
    def apply_theme(self):
        t = theme.current
        
        # Main sidebar styling
        self.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {t['bg_sidebar']};
                border-right: 1px solid {t['border_primary']};
            }}
            QLabel {{
                color: {t['text_sidebar']};
                background: transparent;
            }}
        """)
        
        # Logo container styling
        # Logo container styling
        self.findChild(QFrame).setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 12px;
            }
        """)
        
        # Find and style specific labels
        # Find and style specific labels
        for label in self.findChildren(QLabel):
            if label.text() == "DOWNLOADS":
                label.setStyleSheet(f"""
                    color: {t['text_muted']};
                    letter-spacing: 1.5px;
                """)
            elif label == self.version_label:
                label.setStyleSheet(f"color: {t['text_muted']};")
            elif label.text() == "Manager":
                label.setStyleSheet(f"color: {t['text_muted']};")
        
        # Tree styling
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                color: {t['text_sidebar']};
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 14px 8px;
                border-radius: 10px;
                margin: 3px 8px;
            }}
            QTreeWidget::item:selected {{
                background-color: {t['bg_selected']};
                color: {t['accent_primary']};
            }}
            QTreeWidget::item:hover:!selected {{
                background-color: {t['bg_hover']};
            }}
        """)
        
        self.storage.apply_theme()
