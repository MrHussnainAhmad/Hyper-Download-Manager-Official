"""
Utility helper functions for formatting and calculations
"""
import os

def format_bytes(bytes_value: int, precision: int = 1) -> str:
    """
    Format bytes into human-readable string.
    
    Args:
        bytes_value: Number of bytes
        precision: Decimal places to show
        
    Returns:
        Formatted string like "1.5 GB"
    """
    if bytes_value < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    
    return f"{size:.{precision}f} {units[unit_index]}"


def format_speed(bytes_per_second: float, precision: int = 1) -> str:
    """
    Format speed into human-readable string.
    
    Args:
        bytes_per_second: Download speed in bytes/second
        precision: Decimal places to show
        
    Returns:
        Formatted string like "5.2 MB/s"
    """
    if bytes_per_second <= 0:
        return "0 B/s"
    
    units = ['B/s', 'KB/s', 'MB/s', 'GB/s']
    unit_index = 0
    speed = float(bytes_per_second)
    
    while speed >= 1024 and unit_index < len(units) - 1:
        speed /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(speed)} {units[unit_index]}"
    
    return f"{speed:.{precision}f} {units[unit_index]}"


def format_time(seconds: int) -> str:
    """
    Format seconds into human-readable time string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string like "2h 15m" or "45s"
    """
    if seconds <= 0:
        return "-"
    
    if seconds < 60:
        return f"{int(seconds)}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        if remaining_seconds > 0:
            return f"{int(minutes)}m {int(remaining_seconds)}s"
        return f"{int(minutes)}m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours < 24:
        if remaining_minutes > 0:
            return f"{int(hours)}h {int(remaining_minutes)}m"
        return f"{int(hours)}h"
    
    days = hours // 24
    remaining_hours = hours % 24
    
    if remaining_hours > 0:
        return f"{int(days)}d {int(remaining_hours)}h"
    return f"{int(days)}d"


def format_time_detailed(seconds: int) -> str:
    """
    Format seconds into detailed time string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string like "02:15:30"
    """
    if seconds <= 0:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def truncate_filename(filename: str, max_length: int = 40) -> str:
    """
    Truncate filename while preserving extension.
    
    Args:
        filename: Filename to truncate
        max_length: Maximum length
        
    Returns:
        Truncated filename with extension preserved
    """
    if len(filename) <= max_length:
        return filename
    
    # Split name and extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = '.' + ext
    else:
        name = filename
        ext = ''
    
    # Calculate available space for name
    available = max_length - len(ext) - 3  # 3 for "..."
    
    if available <= 0:
        return filename[:max_length]
    
    return name[:available] + "..." + ext


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Filename to extract extension from
        
    Returns:
        Extension without dot, or empty string
    """
    if '.' in filename:
        return filename.rsplit('.', 1)[-1].lower()
    return ""


def get_file_type(filename: str) -> str:
    """
    Get file type category from filename.
    
    Args:
        filename: Filename to check
        
    Returns:
        File type category string
    """
    ext = get_file_extension(filename)
    
    categories = {
        'video': ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v'],
        'audio': ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma'],
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'],
        'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf'],
        'archive': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
        'executable': ['exe', 'msi', 'dmg', 'app', 'deb', 'rpm'],
        'code': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'json', 'xml'],
    }
    
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    
    return 'other'


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL
    """
    if not url:
        return False
    
    valid_schemes = ('http://', 'https://', 'ftp://', 'ftps://')
    return url.lower().startswith(valid_schemes)


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, working for dev and PyInstaller.
    
    Args:
        relative_path: Relative path from app root
        
    Returns:
        Absolute path to resource
    """
    import sys
    import os
    
    # 1. PyInstaller
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        path = os.path.join(base_path, relative_path)
        if os.path.exists(path):
            return path
            
    # 2. Development (relative to this file)
    # utils/helpers.py -> utils -> root
    root_from_file = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root_from_file, relative_path)
    if os.path.exists(path):
        return path
        
    # 3. Development (CWD - often root when running main.py)
    cwd = os.getcwd()
    path = os.path.join(cwd, relative_path)
    if os.path.exists(path):
        return path
        
    # 4. Try assets/ folder?
    if not relative_path.startswith("assets/"):
        asset_path = os.path.join(root_from_file, "assets", relative_path)
        if os.path.exists(asset_path):
            return asset_path
            
    # Default return (even if not exists, return best guess)
    return os.path.join(root_from_file, relative_path)


def get_app_version() -> str:
    """
    Get application version from version.txt using robust path finding.
    
    Returns:
        Version string (e.g. "1.0.0")
    """
    try:
        version_path = get_resource_path("version.txt")
        if os.path.exists(version_path):
            with open(version_path, "r") as f:
                return f.read().strip()
    except Exception as e:
        print(f"Error reading version: {e}")
    return "1.0.0"
