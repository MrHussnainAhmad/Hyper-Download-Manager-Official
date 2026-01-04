from PySide6.QtCore import Qt, QRect, QRectF, QPointF, QSize
from PySide6.QtGui import (QIcon, QPixmap, QPainter, QPen, QColor, QBrush,
                            QPainterPath, QLinearGradient, QFont)
from PySide6.QtWidgets import QApplication
from enum import Enum, auto


class IconType(Enum):
    """Enumeration of all available icons"""
    ADD = auto()
    DOWNLOAD = auto()
    PAUSE = auto()
    RESUME = auto()
    STOP = auto()
    DELETE = auto()
    FOLDER = auto()
    FILE = auto()
    SETTINGS = auto()
    THEME_DARK = auto()
    THEME_LIGHT = auto()
    REFRESH = auto()
    LINK = auto()
    CHECK = auto()
    CLOSE = auto()
    CLOCK = auto()
    SPEED = auto()
    STORAGE = auto()
    QUEUE = auto()
    COMPLETE = auto()
    WARNING = auto()
    ERROR = auto()
    INFO = auto()
    SEARCH = auto()
    MENU = auto()
    ARROW_DOWN = auto()
    ARROW_RIGHT = auto()
    ARROW_UP = auto()
    CHROME = auto()
    FIREFOX = auto()
    EDGE = auto()
    GLOBE = auto()
    MINIMIZE = auto()
    MAXIMIZE = auto()
    COPY = auto()


class IconProvider:
    """
    Professional vector icon provider using QPainter.
    Creates crisp, scalable icons at any size.
    """
    
    _cache = {}
    
    @classmethod
    def get_icon(cls, icon_type: IconType, color: str = "#FFFFFF", 
                 size: int = 24) -> QIcon:
        """Get a QIcon for the specified icon type"""
        cache_key = (icon_type, color, size)
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        pixmap = cls._create_pixmap(icon_type, color, size)
        icon = QIcon(pixmap)
        cls._cache[cache_key] = icon
        return icon
    
    @classmethod
    def get_pixmap(cls, icon_type: IconType, color: str = "#FFFFFF", 
                   size: int = 24) -> QPixmap:
        """Get a QPixmap for the specified icon type"""
        return cls._create_pixmap(icon_type, color, size)
    
    @classmethod
    def clear_cache(cls):
        """Clear the icon cache (call when theme changes)"""
        cls._cache.clear()
    
    @classmethod
    def _create_pixmap(cls, icon_type: IconType, color: str, size: int) -> QPixmap:
        """Create a pixmap with the drawn icon"""
        # High DPI support
        device_pixel_ratio = 2.0
        if QApplication.instance():
            screen = QApplication.primaryScreen()
            if screen:
                device_pixel_ratio = screen.devicePixelRatio()
        
        actual_size = int(size * device_pixel_ratio)
        pixmap = QPixmap(actual_size, actual_size)
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Setup pen
        pen_width = max(1.5, size / 12)
        pen = QPen(QColor(color))
        pen.setWidthF(pen_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw the icon
        rect = QRectF(pen_width, pen_width, 
                      size - 2 * pen_width, size - 2 * pen_width)
        cls._draw_icon(painter, icon_type, rect, color, pen_width)
        
        painter.end()
        return pixmap
    
    @classmethod
    def _draw_icon(cls, painter: QPainter, icon_type: IconType, 
                   rect: QRectF, color: str, stroke: float):
        """Draw the specific icon type"""
        
        method_map = {
            IconType.ADD: cls._draw_add,
            IconType.DOWNLOAD: cls._draw_download,
            IconType.PAUSE: cls._draw_pause,
            IconType.RESUME: cls._draw_resume,
            IconType.STOP: cls._draw_stop,
            IconType.DELETE: cls._draw_delete,
            IconType.FOLDER: cls._draw_folder,
            IconType.FILE: cls._draw_file,
            IconType.SETTINGS: cls._draw_settings,
            IconType.THEME_DARK: cls._draw_moon,
            IconType.THEME_LIGHT: cls._draw_sun,
            IconType.REFRESH: cls._draw_refresh,
            IconType.LINK: cls._draw_link,
            IconType.CHECK: cls._draw_check,
            IconType.CLOSE: cls._draw_close,
            IconType.CLOCK: cls._draw_clock,
            IconType.SPEED: cls._draw_speed,
            IconType.STORAGE: cls._draw_storage,
            IconType.QUEUE: cls._draw_queue,
            IconType.COMPLETE: cls._draw_complete,
            IconType.WARNING: cls._draw_warning,
            IconType.ERROR: cls._draw_error,
            IconType.INFO: cls._draw_info,
            IconType.SEARCH: cls._draw_search,
            IconType.MENU: cls._draw_menu,
            IconType.ARROW_DOWN: cls._draw_arrow_down,
            IconType.ARROW_RIGHT: cls._draw_arrow_right,
            IconType.ARROW_UP: cls._draw_arrow_up,
            IconType.GLOBE: cls._draw_globe,
            IconType.MINIMIZE: cls._draw_minimize,
            IconType.MAXIMIZE: cls._draw_maximize,
            IconType.CHROME: cls._draw_chrome,
            IconType.FIREFOX: cls._draw_firefox,
            IconType.EDGE: cls._draw_edge,
            IconType.COPY: cls._draw_copy,
        }
        
        draw_method = method_map.get(icon_type, cls._draw_placeholder)
        draw_method(painter, rect, color, stroke)
        
    @staticmethod
    def _draw_copy(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Copy icon - two overlapping rectangles"""
        w = rect.width() * 0.6
        h = rect.height() * 0.7
        offset = rect.width() * 0.2
        
        # Back rectangle
        back = QRectF(rect.left() + offset, rect.top(), w, h)
        painter.drawRoundedRect(back, 2, 2)
        
        # Front rectangle
        # Fill it with transparent background to hide backend line? No, wireframe style
        # Actually standard copy icon is solid or outline. We do outline.
        # But we need to clip or draw opaque. We are using QPen.
        
        front = QRectF(rect.left(), rect.top() + offset, w, h)
        
        # We need to ensure the front one obscures the back one where they overlap if we want a solid feel
        # But for wireframe, just drawing both is fine, maybe slightly offset.
        
        painter.drawRoundedRect(front, 2, 2)
    
    # ═══════════════════════════════════════════════════════════════
    #                        ICON DRAWING METHODS
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def _draw_add(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Plus icon"""
        cx, cy = rect.center().x(), rect.center().y()
        half = rect.width() * 0.35
        
        painter.drawLine(QPointF(cx - half, cy), QPointF(cx + half, cy))
        painter.drawLine(QPointF(cx, cy - half), QPointF(cx, cy + half))
    
    @staticmethod
    def _draw_download(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Download arrow icon"""
        cx = rect.center().x()
        top = rect.top() + rect.height() * 0.15
        bottom = rect.bottom() - rect.height() * 0.25
        arrow_width = rect.width() * 0.3
        
        # Vertical line
        painter.drawLine(QPointF(cx, top), QPointF(cx, bottom))
        
        # Arrow head
        painter.drawLine(QPointF(cx, bottom), 
                        QPointF(cx - arrow_width, bottom - arrow_width))
        painter.drawLine(QPointF(cx, bottom), 
                        QPointF(cx + arrow_width, bottom - arrow_width))
        
        # Bottom line
        base_y = rect.bottom() - rect.height() * 0.1
        painter.drawLine(QPointF(rect.left() + rect.width() * 0.2, base_y),
                        QPointF(rect.right() - rect.width() * 0.2, base_y))
    
    @staticmethod
    def _draw_pause(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Pause icon - two vertical bars"""
        gap = rect.width() * 0.15
        bar_width = rect.width() * 0.2
        top = rect.top() + rect.height() * 0.2
        bottom = rect.bottom() - rect.height() * 0.2
        
        cx = rect.center().x()
        
        # Left bar
        painter.drawLine(QPointF(cx - gap, top), QPointF(cx - gap, bottom))
        # Right bar  
        painter.drawLine(QPointF(cx + gap, top), QPointF(cx + gap, bottom))
    
    @staticmethod
    def _draw_resume(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Play/Resume triangle icon"""
        path = QPainterPath()
        
        left = rect.left() + rect.width() * 0.25
        right = rect.right() - rect.width() * 0.2
        top = rect.top() + rect.height() * 0.2
        bottom = rect.bottom() - rect.height() * 0.2
        cy = rect.center().y()
        
        path.moveTo(left, top)
        path.lineTo(right, cy)
        path.lineTo(left, bottom)
        path.closeSubpath()
        
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPath(path)
        painter.setBrush(Qt.NoBrush)
    
    @staticmethod
    def _draw_stop(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Stop icon - square"""
        margin = rect.width() * 0.25
        stop_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        painter.setBrush(QBrush(QColor(color)))
        painter.drawRoundedRect(stop_rect, 2, 2)
        painter.setBrush(Qt.NoBrush)
    
    @staticmethod
    def _draw_delete(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Trash can icon"""
        # Lid
        lid_y = rect.top() + rect.height() * 0.2
        lid_left = rect.left() + rect.width() * 0.15
        lid_right = rect.right() - rect.width() * 0.15
        painter.drawLine(QPointF(lid_left, lid_y), QPointF(lid_right, lid_y))
        
        # Handle
        handle_width = rect.width() * 0.2
        cx = rect.center().x()
        handle_top = rect.top() + rect.height() * 0.08
        painter.drawLine(QPointF(cx - handle_width, lid_y),
                        QPointF(cx - handle_width, handle_top))
        painter.drawLine(QPointF(cx - handle_width, handle_top),
                        QPointF(cx + handle_width, handle_top))
        painter.drawLine(QPointF(cx + handle_width, handle_top),
                        QPointF(cx + handle_width, lid_y))
        
        # Body
        body_top = lid_y + rect.height() * 0.05
        body_bottom = rect.bottom() - rect.height() * 0.1
        body_left = rect.left() + rect.width() * 0.22
        body_right = rect.right() - rect.width() * 0.22
        
        path = QPainterPath()
        path.moveTo(body_left, body_top)
        path.lineTo(body_left + rect.width() * 0.05, body_bottom)
        path.lineTo(body_right - rect.width() * 0.05, body_bottom)
        path.lineTo(body_right, body_top)
        painter.drawPath(path)
        
        # Lines inside
        line_y1 = body_top + rect.height() * 0.1
        line_y2 = body_bottom - rect.height() * 0.1
        for i in range(3):
            x = body_left + (body_right - body_left) * (i + 1) / 4
            painter.drawLine(QPointF(x, line_y1), QPointF(x, line_y2))
    
    @staticmethod
    def _draw_folder(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Folder icon"""
        path = QPainterPath()
        
        left = rect.left() + rect.width() * 0.1
        right = rect.right() - rect.width() * 0.1
        top = rect.top() + rect.height() * 0.2
        bottom = rect.bottom() - rect.height() * 0.15
        tab_width = rect.width() * 0.3
        tab_height = rect.height() * 0.12
        
        path.moveTo(left, top + tab_height)
        path.lineTo(left, bottom)
        path.lineTo(right, bottom)
        path.lineTo(right, top + tab_height)
        path.lineTo(left + tab_width + rect.width() * 0.05, top + tab_height)
        path.lineTo(left + tab_width, top)
        path.lineTo(left, top)
        path.lineTo(left, top + tab_height)
        
        painter.drawPath(path)
    
    @staticmethod
    def _draw_file(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """File/document icon"""
        left = rect.left() + rect.width() * 0.2
        right = rect.right() - rect.width() * 0.2
        top = rect.top() + rect.height() * 0.1
        bottom = rect.bottom() - rect.height() * 0.1
        fold = rect.width() * 0.25
        
        path = QPainterPath()
        path.moveTo(left, top)
        path.lineTo(right - fold, top)
        path.lineTo(right, top + fold)
        path.lineTo(right, bottom)
        path.lineTo(left, bottom)
        path.closeSubpath()
        
        painter.drawPath(path)
        
        # Fold line
        painter.drawLine(QPointF(right - fold, top), 
                        QPointF(right - fold, top + fold))
        painter.drawLine(QPointF(right - fold, top + fold), 
                        QPointF(right, top + fold))
    
    @staticmethod
    def _draw_settings(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Gear/settings icon"""
        cx, cy = rect.center().x(), rect.center().y()
        outer_r = rect.width() * 0.4
        inner_r = rect.width() * 0.25
        teeth = 8
        
        path = QPainterPath()
        import math
        
        for i in range(teeth):
            angle1 = (i * 2 * math.pi / teeth) - math.pi / 2
            angle2 = ((i + 0.4) * 2 * math.pi / teeth) - math.pi / 2
            angle3 = ((i + 0.6) * 2 * math.pi / teeth) - math.pi / 2
            angle4 = ((i + 1) * 2 * math.pi / teeth) - math.pi / 2
            
            if i == 0:
                path.moveTo(cx + outer_r * math.cos(angle1),
                           cy + outer_r * math.sin(angle1))
            
            path.lineTo(cx + outer_r * math.cos(angle2),
                       cy + outer_r * math.sin(angle2))
            path.lineTo(cx + inner_r * math.cos(angle3),
                       cy + inner_r * math.sin(angle3))
            path.lineTo(cx + inner_r * math.cos(angle4),
                       cy + inner_r * math.sin(angle4))
        
        path.closeSubpath()
        painter.drawPath(path)
        
        # Center circle
        center_r = rect.width() * 0.12
        painter.drawEllipse(QPointF(cx, cy), center_r, center_r)
    
    @staticmethod
    def _draw_moon(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Moon/dark theme icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.35
        
        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), r, r)
        
        # Subtract circle for crescent
        cut_path = QPainterPath()
        cut_path.addEllipse(QPointF(cx + r * 0.6, cy - r * 0.3), r * 0.8, r * 0.8)
        
        result = path.subtracted(cut_path)
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPath(result)
        painter.setBrush(Qt.NoBrush)
    
    @staticmethod
    def _draw_sun(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Sun/light theme icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.18
        ray_inner = rect.width() * 0.25
        ray_outer = rect.width() * 0.38
        
        # Center circle
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.setBrush(Qt.NoBrush)
        
        # Rays
        import math
        for i in range(8):
            angle = i * math.pi / 4
            x1 = cx + ray_inner * math.cos(angle)
            y1 = cy + ray_inner * math.sin(angle)
            x2 = cx + ray_outer * math.cos(angle)
            y2 = cy + ray_outer * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    
    @staticmethod
    def _draw_refresh(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Refresh/sync icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.32
        arrow_size = rect.width() * 0.12
        
        import math
        
        # Draw arc
        arc_rect = QRectF(cx - r, cy - r, r * 2, r * 2)
        painter.drawArc(arc_rect, 45 * 16, 270 * 16)
        
        # Arrow at end
        end_angle = math.radians(45)
        end_x = cx + r * math.cos(end_angle)
        end_y = cy - r * math.sin(end_angle)
        
        painter.drawLine(QPointF(end_x, end_y),
                        QPointF(end_x + arrow_size, end_y))
        painter.drawLine(QPointF(end_x, end_y),
                        QPointF(end_x, end_y + arrow_size))
    
    @staticmethod
    def _draw_link(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Link/chain icon"""
        # Two connected ovals
        w = rect.width() * 0.25
        h = rect.height() * 0.15
        cx, cy = rect.center().x(), rect.center().y()
        offset = rect.width() * 0.12
        
        # First link (top-left)
        rect1 = QRectF(cx - offset - w, cy - h, w * 2, h * 2)
        painter.drawRoundedRect(rect1, h, h)
        
        # Second link (bottom-right)
        rect2 = QRectF(cx + offset - w, cy - h, w * 2, h * 2)
        painter.drawRoundedRect(rect2, h, h)
    
    @staticmethod
    def _draw_check(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Checkmark icon"""
        path = QPainterPath()
        
        left = rect.left() + rect.width() * 0.2
        right = rect.right() - rect.width() * 0.2
        top = rect.top() + rect.height() * 0.3
        bottom = rect.bottom() - rect.height() * 0.25
        mid_x = rect.left() + rect.width() * 0.4
        
        path.moveTo(left, rect.center().y())
        path.lineTo(mid_x, bottom)
        path.lineTo(right, top)
        
        painter.drawPath(path)
    
    @staticmethod
    def _draw_close(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """X/close icon"""
        margin = rect.width() * 0.25
        
        painter.drawLine(QPointF(rect.left() + margin, rect.top() + margin),
                        QPointF(rect.right() - margin, rect.bottom() - margin))
        painter.drawLine(QPointF(rect.right() - margin, rect.top() + margin),
                        QPointF(rect.left() + margin, rect.bottom() - margin))
    
    @staticmethod
    def _draw_clock(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Clock icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        # Circle
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # Hour hand
        painter.drawLine(QPointF(cx, cy), 
                        QPointF(cx, cy - r * 0.5))
        # Minute hand
        painter.drawLine(QPointF(cx, cy),
                        QPointF(cx + r * 0.45, cy))
    
    @staticmethod
    def _draw_speed(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Lightning bolt/speed icon"""
        path = QPainterPath()
        
        cx = rect.center().x()
        top = rect.top() + rect.height() * 0.1
        bottom = rect.bottom() - rect.height() * 0.1
        
        path.moveTo(cx + rect.width() * 0.1, top)
        path.lineTo(cx - rect.width() * 0.15, rect.center().y())
        path.lineTo(cx + rect.width() * 0.05, rect.center().y())
        path.lineTo(cx - rect.width() * 0.1, bottom)
        path.lineTo(cx + rect.width() * 0.15, rect.center().y())
        path.lineTo(cx - rect.width() * 0.05, rect.center().y())
        path.closeSubpath()
        
        painter.setBrush(QBrush(QColor(color)))
        painter.drawPath(path)
        painter.setBrush(Qt.NoBrush)
    
    @staticmethod
    def _draw_storage(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Hard drive/storage icon"""
        margin_x = rect.width() * 0.12
        margin_y = rect.height() * 0.25
        r = rect.width() * 0.08
        
        storage_rect = rect.adjusted(margin_x, margin_y, -margin_x, -margin_y)
        painter.drawRoundedRect(storage_rect, r, r)
        
        # Middle line
        painter.drawLine(QPointF(storage_rect.left(), storage_rect.center().y()),
                        QPointF(storage_rect.right(), storage_rect.center().y()))
        
        # LED dots
        dot_r = rect.width() * 0.04
        dot_y = storage_rect.bottom() - (storage_rect.height() / 4)
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QPointF(storage_rect.right() - rect.width() * 0.15, dot_y),
                           dot_r, dot_r)
        painter.setBrush(Qt.NoBrush)
    
    @staticmethod
    def _draw_queue(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """List/queue icon"""
        left = rect.left() + rect.width() * 0.15
        right = rect.right() - rect.width() * 0.15
        
        for i in range(3):
            y = rect.top() + rect.height() * (0.3 + i * 0.2)
            painter.drawLine(QPointF(left, y), QPointF(right, y))
    
    @staticmethod
    def _draw_complete(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Checkmark in circle icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        # Circle
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # Checkmark
        check_rect = rect.adjusted(rect.width() * 0.25, rect.height() * 0.25,
                                   -rect.width() * 0.25, -rect.height() * 0.25)
        IconProvider._draw_check(painter, check_rect, color, stroke)
    
    @staticmethod
    def _draw_warning(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Warning triangle icon"""
        cx = rect.center().x()
        top = rect.top() + rect.height() * 0.15
        bottom = rect.bottom() - rect.height() * 0.15
        half_w = rect.width() * 0.4
        
        path = QPainterPath()
        path.moveTo(cx, top)
        path.lineTo(cx + half_w, bottom)
        path.lineTo(cx - half_w, bottom)
        path.closeSubpath()
        
        painter.drawPath(path)
        
        # Exclamation
        cy = rect.center().y()
        painter.drawLine(QPointF(cx, cy - rect.height() * 0.1),
                        QPointF(cx, cy + rect.height() * 0.08))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QPointF(cx, bottom - rect.height() * 0.12),
                           rect.width() * 0.03, rect.width() * 0.03)
        painter.setBrush(Qt.NoBrush)
    
    @staticmethod
    def _draw_error(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """X in circle icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        # Circle
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # X
        cross = r * 0.5
        painter.drawLine(QPointF(cx - cross, cy - cross),
                        QPointF(cx + cross, cy + cross))
        painter.drawLine(QPointF(cx + cross, cy - cross),
                        QPointF(cx - cross, cy + cross))
    
    @staticmethod
    def _draw_info(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Info icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        # Circle
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # i dot
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QPointF(cx, cy - r * 0.45), 
                           rect.width() * 0.05, rect.width() * 0.05)
        painter.setBrush(Qt.NoBrush)
        
        # i stem
        painter.drawLine(QPointF(cx, cy - r * 0.15),
                        QPointF(cx, cy + r * 0.5))
    
    @staticmethod
    def _draw_search(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Magnifying glass icon"""
        cx = rect.center().x() - rect.width() * 0.08
        cy = rect.center().y() - rect.height() * 0.08
        r = rect.width() * 0.28
        
        # Circle
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # Handle
        import math
        handle_start_x = cx + r * math.cos(math.pi / 4)
        handle_start_y = cy + r * math.sin(math.pi / 4)
        handle_end_x = rect.right() - rect.width() * 0.18
        handle_end_y = rect.bottom() - rect.height() * 0.18
        
        painter.drawLine(QPointF(handle_start_x, handle_start_y),
                        QPointF(handle_end_x, handle_end_y))
    
    @staticmethod
    def _draw_menu(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Hamburger menu icon"""
        left = rect.left() + rect.width() * 0.2
        right = rect.right() - rect.width() * 0.2
        
        for i in range(3):
            y = rect.top() + rect.height() * (0.3 + i * 0.2)
            painter.drawLine(QPointF(left, y), QPointF(right, y))
    
    @staticmethod
    def _draw_arrow_down(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Chevron down icon"""
        cx = rect.center().x()
        cy = rect.center().y()
        half_w = rect.width() * 0.25
        half_h = rect.height() * 0.15
        
        painter.drawLine(QPointF(cx - half_w, cy - half_h),
                        QPointF(cx, cy + half_h))
        painter.drawLine(QPointF(cx, cy + half_h),
                        QPointF(cx + half_w, cy - half_h))
    
    @staticmethod
    def _draw_arrow_right(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Chevron right icon"""
        cx = rect.center().x()
        cy = rect.center().y()
        half_w = rect.width() * 0.15
        half_h = rect.height() * 0.25
        
        painter.drawLine(QPointF(cx - half_w, cy - half_h),
                        QPointF(cx + half_w, cy))
        painter.drawLine(QPointF(cx + half_w, cy),
                        QPointF(cx - half_w, cy + half_h))
    
    @staticmethod
    def _draw_arrow_up(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Chevron up icon"""
        cx = rect.center().x()
        cy = rect.center().y()
        half_w = rect.width() * 0.25
        half_h = rect.height() * 0.15
        
        painter.drawLine(QPointF(cx - half_w, cy + half_h),
                        QPointF(cx, cy - half_h))
        painter.drawLine(QPointF(cx, cy - half_h),
                        QPointF(cx + half_w, cy + half_h))
    
    @staticmethod
    def _draw_globe(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Globe/web icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        # Main circle
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # Horizontal line
        painter.drawLine(QPointF(cx - r, cy), QPointF(cx + r, cy))
        
        # Vertical ellipse
        painter.drawEllipse(QPointF(cx, cy), r * 0.4, r)
    
    @staticmethod
    def _draw_minimize(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Minimize icon"""
        y = rect.center().y() + rect.height() * 0.15
        painter.drawLine(QPointF(rect.left() + rect.width() * 0.25, y),
                        QPointF(rect.right() - rect.width() * 0.25, y))
    
    @staticmethod
    def _draw_maximize(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Maximize/square icon"""
        margin = rect.width() * 0.25
        painter.drawRect(rect.adjusted(margin, margin, -margin, -margin))
    
    @staticmethod
    def _draw_chrome(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Chrome-like browser icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawEllipse(QPointF(cx, cy), r * 0.4, r * 0.4)
    
    @staticmethod
    def _draw_firefox(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Firefox-like browser icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        painter.drawEllipse(QPointF(cx, cy), r, r)
        # Simplified fox tail
        import math
        path = QPainterPath()
        path.moveTo(cx + r * 0.5, cy - r * 0.5)
        path.quadTo(cx + r, cy - r * 0.8, cx + r * 0.3, cy - r)
        painter.drawPath(path)
    
    @staticmethod
    def _draw_edge(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Edge-like browser icon"""
        cx, cy = rect.center().x(), rect.center().y()
        r = rect.width() * 0.38
        
        # Wave shape
        import math
        path = QPainterPath()
        path.moveTo(cx - r, cy)
        path.quadTo(cx - r, cy - r, cx, cy - r)
        path.quadTo(cx + r, cy - r, cx + r, cy)
        path.quadTo(cx + r, cy + r * 0.5, cx, cy + r * 0.5)
        painter.drawPath(path)
    
    @staticmethod
    def _draw_placeholder(painter: QPainter, rect: QRectF, color: str, stroke: float):
        """Placeholder for missing icons"""
        painter.drawRect(rect)
        painter.drawLine(rect.topLeft(), rect.bottomRight())
        painter.drawLine(rect.topRight(), rect.bottomLeft())


# Convenience functions
def get_icon(icon_type: IconType, color: str = "#FFFFFF", size: int = 24) -> QIcon:
    """Convenience function to get an icon"""
    return IconProvider.get_icon(icon_type, color, size)


def get_pixmap(icon_type: IconType, color: str = "#FFFFFF", size: int = 24) -> QPixmap:
    """Convenience function to get a pixmap"""
    return IconProvider.get_pixmap(icon_type, color, size)