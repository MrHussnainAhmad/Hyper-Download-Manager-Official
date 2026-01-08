from PySide6.QtWidgets import (QTableWidget, QTableWidgetItem, QAbstractItemView, 
                               QHeaderView, QWidget, QHBoxLayout, QVBoxLayout,
                               QLabel, QProgressBar, QStyledItemDelegate, QStyle,
                               QFrame, QStackedWidget)
from PySide6.QtCore import Qt, Signal, QRect, QSize, QEvent
from PySide6.QtGui import QColor, QPainter, QFont, QBrush, QPen, QLinearGradient

from functools import partial
from ui.theme_manager import theme
from ui.icons import IconType, IconProvider, get_pixmap
from ui.components import StatusBadge, EmptyState
from utils.helpers import format_bytes, format_speed, format_time


class ProgressBarDelegate(QStyledItemDelegate):
    """Custom delegate for progress bar in table with gradient fill"""
    
    def paint(self, painter, option, index):
        progress = index.data(Qt.UserRole + 1)
        if progress is None:
            progress = 0
            
        t = theme.current
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Layout: [Bar ............] [xx%]
        
        rect = option.rect
        margin_h = 12
        margin_v = 18 # Increase margin for thinner bar
        
        # Text (Percentage)
        text = f"{int(progress)}%"
        text_font = QFont("Segoe UI", 10)
        text_font.setWeight(QFont.DemiBold)
        painter.setFont(text_font)
        
        text_width = painter.fontMetrics().horizontalAdvance("100%")
        text_rect = QRect(
            rect.right() - text_width - margin_h,
            rect.top(),
            text_width,
            rect.height()
        )
        
        # Draw Text
        painter.setPen(QColor(t['text_secondary']))
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignRight, text)
        
        # Bar Area
        bar_width = rect.width() - text_width - (margin_h * 3)
        bar_height = 8 # Thin sleek bar
        bar_y = rect.center().y() - (bar_height // 2)
        
        bar_rect = QRect(
            rect.left() + margin_h,
            bar_y,
            bar_width,
            bar_height
        )
        
        # Background Track
        painter.setBrush(QColor(t['progress_bg']))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_rect, 4, 4)
        
        # Fill
        if progress > 0:
            fill_w = int((bar_width * progress) / 100)
            if fill_w < 8: fill_w = 8 # Minimum width
            fill_rect = QRect(bar_rect.x(), bar_rect.y(), fill_w, bar_height)
            
            # Gradient
            gradient = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            gradient.setColorAt(0, QColor(t['accent_gradient_start']))
            gradient.setColorAt(1, QColor(t['accent_gradient_end']))
            
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(fill_rect, 4, 4)
            
        painter.restore()
        
    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 60)


class StatusDelegate(QStyledItemDelegate):
    """Custom delegate for status column with colored badges"""
    
    STATUS_COLORS = {
        "Downloading": ("status_downloading", IconType.DOWNLOAD),
        "Completed": ("status_completed", IconType.COMPLETE),
        "Finished": ("status_completed", IconType.COMPLETE),
        "Paused": ("status_paused", IconType.PAUSE),
        "Error": ("status_error", IconType.ERROR),
        "Queued": ("status_queued", IconType.QUEUE),
        "Idle": ("status_queued", IconType.CLOCK),
        "Stopped": ("status_paused", IconType.STOP),
    }
    
    def paint(self, painter, option, index):
        status = index.data(Qt.DisplayRole)
        if not status:
            return
            
        t = theme.current
        config = self.STATUS_COLORS.get(status, ("status_queued", IconType.QUEUE))
        color_key, icon_type = config
        color = QColor(t[color_key])
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate badge dimensions
        badge_width = 100
        badge_height = 24
        x = option.rect.center().x() - badge_width // 2
        y = option.rect.center().y() - badge_height // 2
        badge_rect = QRect(x, y, badge_width, badge_height)
        
        # Background
        bg_color = QColor(color)
        bg_color.setAlpha(25) # More transparent
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(badge_rect, 6, 6) # Softer radius
        
        # Text (Centered, No Icon)
        painter.setPen(color)
        font = QFont("Segoe UI", 7) # Reduced size as requested
        font.setWeight(QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        painter.setFont(font)
        
        painter.drawText(badge_rect, Qt.AlignCenter, status.upper())
        
        painter.restore()
        
    def sizeHint(self, option, index):
        return QSize(110, 60)


class FileNameDelegate(QStyledItemDelegate):
    """Custom delegate for file name with icon"""
    
    def paint(self, painter, option, index):
        text = index.data(Qt.DisplayRole)
        task = index.data(Qt.UserRole)
        
        t = theme.current
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Selection/hover background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor(t['bg_selected']))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor(t['bg_hover']))
        
        # Determine icon type based on status
        icon_type = IconType.FILE
        if task:
            status = task.status
            if status == "Downloading":
                icon_type = IconType.DOWNLOAD
            elif status in ["Completed", "Finished"]:
                icon_type = IconType.COMPLETE
            elif status == "Error":
                icon_type = IconType.ERROR
        
        # Draw icon
        icon_size = 22
        icon_x = option.rect.left() + 16
        icon_y = option.rect.center().y() - icon_size // 2
        
        icon_color = t['accent_primary'] if task and task.status == "Downloading" else t['text_secondary']
        icon_pixmap = get_pixmap(icon_type, icon_color, icon_size)
        painter.drawPixmap(icon_x, icon_y, icon_pixmap)
        
        # Draw text
        text_x = icon_x + icon_size + 14
        text_rect = QRect(text_x, option.rect.top(),
                          option.rect.width() - text_x - 10, option.rect.height())
        
        painter.setPen(QColor(t['text_primary']))
        font = QFont("Segoe UI", 11) # Slightly cleaner font size
        font.setWeight(QFont.DemiBold) # Clearer text
        painter.setFont(font)
        
        # Elide text if too long
        metrics = painter.fontMetrics()
        elided_text = metrics.elidedText(text or "", Qt.ElideMiddle, text_rect.width())
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, elided_text)
        
        painter.restore()
        
    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 52)


class DownloadList(QWidget):
    """Download list with table and empty state"""
    
    open_progress = Signal(object)
    context_menu_requested = Signal(object, object)
    delete_requested = Signal()

    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget for table/empty state
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Table widget
        self.table = QTableWidget()
        self._setup_table()
        self.stack.addWidget(self.table)
        
        # Empty state
        self.empty_state = EmptyState(
            IconType.DOWNLOAD,
            "No Downloads Yet.",
            "Start Downloading, Can't fetch File? Are you sure you have added extension?",
            "Let's add"
        )
        self.stack.addWidget(self.empty_state)
        
        # Show empty state initially
        self._update_empty_state()
        
        self.apply_theme()
        
    def _setup_table(self):
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "  File Name", "Size", "Progress", "Status", "Speed", "ETA", "Added"
        ])
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setFocusPolicy(Qt.StrongFocus)
        
        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 115)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 90)
        
        # Custom delegates
        self.table.setItemDelegateForColumn(0, FileNameDelegate(self.table))
        self.table.setItemDelegateForColumn(2, ProgressBarDelegate(self.table))
        self.table.setItemDelegateForColumn(3, StatusDelegate(self.table))
        
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self.table.itemDoubleClicked.connect(self._on_double_click)
        
        # Install event filter to catch Delete key
        self.table.installEventFilter(self)

    def eventFilter(self, source, event):
        if source == self.table and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Delete:
                self.delete_requested.emit()
                return True
        return super().eventFilter(source, event)

        
    def _update_empty_state(self):
        """Show empty state if no downloads"""
        if self.table.rowCount() == 0:
            self.stack.setCurrentWidget(self.empty_state)
        else:
            self.stack.setCurrentWidget(self.table)
        
    def apply_theme(self):
        t = theme.current
        
        self.setStyleSheet(f"background-color: {t['bg_primary']};")
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {t['bg_primary']};
                alternate-background-color: {t['bg_secondary']};
                border: none;
                font-family: 'Segoe UI';
                font-size: 13px;
                color: {t['text_primary']};
                gridline-color: transparent;
                outline: none;
            }}
            
            QTableWidget::item {{
                padding: 0px 8px;
                border: none;
                border-bottom: 1px solid {t['border_light']};
            }}
            
            QTableWidget::item:selected {{
                background-color: {t['bg_selected']};
                color: {t['text_primary']};
            }}
            
            QTableWidget::item:hover {{
                background-color: {t['bg_hover']};
            }}
            
            QHeaderView::section {{
                background-color: {t['bg_primary']};
                color: {t['text_secondary']};
                padding: 14px 12px;
                border: none;
                border-bottom: 1px solid {t['border_primary']};
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            QHeaderView::section:hover {{
                background-color: {t['bg_hover']};
                color: {t['text_secondary']};
            }}
            
            QHeaderView::section:first {{
                padding-left: 20px;
            }}
        """)
        
        self.empty_state.apply_theme()

    def add_task(self, task):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 64)
        
        t = theme.current
        
        # 0: Name (get from save_path, not URL)
        import os
        name = os.path.basename(task.save_path) if task.save_path else "Unknown"
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, task)
        self.table.setItem(row, 0, name_item)
        
        # 1: Size
        size_text = format_bytes(task.file_size) if task.file_size > 0 else "-"
        size_item = QTableWidgetItem(size_text)
        size_item.setTextAlignment(Qt.AlignCenter)
        size_item.setFont(QFont("Segoe UI", 11))
        self.table.setItem(row, 1, size_item)
        
        # 2: Progress
        initial_progress = 0
        if task.file_size > 0:
             initial_progress = int((task.downloaded_bytes / task.file_size) * 100)
        
        progress_item = QTableWidgetItem()
        progress_item.setData(Qt.UserRole + 1, initial_progress)
        self.table.setItem(row, 2, progress_item)
        
        # 3: Status
        status_item = QTableWidgetItem(task.status)
        status_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, status_item)
        
        # 4: Speed
        speed_item = QTableWidgetItem("-")
        speed_item.setTextAlignment(Qt.AlignCenter)
        speed_item.setFont(QFont("Segoe UI", 11))
        self.table.setItem(row, 4, speed_item)
        
        # 5: ETA
        eta_item = QTableWidgetItem("-")
        eta_item.setTextAlignment(Qt.AlignCenter)
        eta_item.setFont(QFont("Segoe UI", 11))
        eta_item.setForeground(QColor(t['text_muted']))
        self.table.setItem(row, 5, eta_item)
        
        # 6: Date
        from datetime import datetime
        added_dt = datetime.fromtimestamp(task.added_time)
        date_item = QTableWidgetItem(added_dt.strftime("%H:%M"))
        date_item.setTextAlignment(Qt.AlignCenter)
        date_item.setFont(QFont("Segoe UI", 11))
        date_item.setForeground(QColor(t['text_muted']))
        self.table.setItem(row, 6, date_item)
        
        # Connect signals
        task.progress_updated.connect(partial(self.update_task_row, task))
        task.status_changed.connect(partial(self.update_task_status, task))
        
        self._update_empty_state()

    def find_row_for_task(self, task):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == task:
                return row
        return -1

    def update_task_row(self, task, progress, speed, eta):
        row = self.find_row_for_task(task)
        if row == -1:
            return
        
        # Size
        size_text = format_bytes(task.file_size) if task.file_size > 0 else "-"
        self.table.item(row, 1).setText(size_text)
        
        # Progress
        self.table.item(row, 2).setData(Qt.UserRole + 1, progress)
        
        # Speed
        speed_text = format_speed(speed) if speed > 0 else "-"
        speed_item = self.table.item(row, 4)
        speed_item.setText(speed_text)
        if speed > 0:
            speed_item.setForeground(QColor(theme.get('accent_primary')))
        else:
            speed_item.setForeground(QColor(theme.get('text_muted')))
        
        # ETA
        self.table.item(row, 5).setText(format_time(eta) if eta > 0 else "-")
        
        # Refresh view
        self.table.viewport().update()

    def update_task_status(self, task, status):
        row = self.find_row_for_task(task)
        if row == -1:
            return
        
        display_status = "Completed" if status == "Finished" else status
        self.table.item(row, 3).setText(display_status)
        
        # Refresh file name column to update icon
        self.table.viewport().update()

    def _on_double_click(self, item):
        row = item.row()
        task_item = self.table.item(row, 0)
        task = task_item.data(Qt.UserRole)
        if task and task.status == "Downloading":
            self.open_progress.emit(task)

    def remove_task(self, task):
        row = self.find_row_for_task(task)
        if row != -1:
            self.table.removeRow(row)
        self._update_empty_state()

    def _on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item:
            row = item.row()
            task_item = self.table.item(row, 0)
            task = task_item.data(Qt.UserRole)
            if task:
                global_pos = self.table.viewport().mapToGlobal(pos)
                self.context_menu_requested.emit(task, global_pos)
    
    # Delegate methods to table
    def rowCount(self):
        return self.table.rowCount()
    
    def selectedItems(self):
        return self.table.selectedItems()
    
    def item(self, row, col):
        return self.table.item(row, col)