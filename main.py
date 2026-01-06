import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QFont, QFontDatabase
from PySide6.QtCore import Qt, QCoreApplication


def setup_environment():
    """Configure environment for optimal rendering"""
    # High DPI support
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
    
    # Consistent font rendering
    if sys.platform == "win32":
        os.environ["QT_FONT_DPI"] = "96"


def load_fonts(app: QApplication):
    """Load custom fonts if available"""
    font_paths = [
        "fonts/SegoeUI.ttf",
        "fonts/SegoeUI-Bold.ttf", 
        "fonts/SegoeUI-SemiBold.ttf",
    ]
    
    base_path = get_base_path()
    
    for font_path in font_paths:
        full_path = os.path.join(base_path, font_path)
        if os.path.exists(full_path):
            QFontDatabase.addApplicationFont(full_path)


def get_base_path() -> str:
    """Get base path for resources"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_app_icon() -> QIcon:
    """Load application icon"""
    # Prioritize ICO for Windows
    from utils.helpers import get_resource_path
    
    icon_candidates = ["icon.ico", "icon.png", "assets/icon.ico", "assets/icon.png"]
    
    for icon_name in icon_candidates:
        icon_path = get_resource_path(icon_name)
        if os.path.exists(icon_path):
            return QIcon(icon_path)
    
    return QIcon()


def setup_application() -> QApplication:
    """Initialize and configure the application"""
    from utils.helpers import get_app_version
    setup_environment()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Application metadata
    app.setApplicationName("Hyper Download Manager")
    app.setApplicationVersion(get_app_version())
    app.setOrganizationName("FDM")
    app.setOrganizationDomain("fdm.app")
    
    # Critical for Linux taskbar icon association
    # Must match the .desktop file name (without .desktop extension)
    app.setDesktopFileName("hyper-download-manager")
    
    # Use Fusion style for cross-platform consistency
    app.setStyle("Fusion")
    
    # Load fonts
    load_fonts(app)
    
    # Set global font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.SansSerif)
    font.setHintingPreference(QFont.PreferFullHinting)
    app.setFont(font)
    
    # Set application icon
    app_icon = get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    return app


def handle_command_line_url(window):
    """Handle URL passed via command line"""
    if len(sys.argv) > 1:
        potential_url = sys.argv[1]
        if potential_url.startswith(("http://", "https://", "ftp://")):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(300, lambda: window.handle_new_download(potential_url))


def main():
    """Main entry point"""
    # Create application first
    app = setup_application()
    
    # Import after app creation
    from ui.main_window import MainWindow
    from ui.theme_manager import theme
    from PySide6.QtNetwork import QLocalSocket, QLocalServer
    from PySide6.QtCore import QTextStream
    
    SERVER_NAME = "HyperDownloadManager_Instance"
    
    # Check for existing instance
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    
    if socket.waitForConnected(500):
        # App is already running
        # Send arguments (URL) to existing instance
        if len(sys.argv) > 1:
            stream = QTextStream(socket)
            stream << sys.argv[1]
            stream.flush()
            socket.waitForBytesWritten(1000)
        sys.exit(0)
    
    # Clean up any stale server
    QLocalServer.removeServer(SERVER_NAME)
    
    # Start Local Server
    server = QLocalServer()
    server.listen(SERVER_NAME)
    
    # Create main window
    window = MainWindow()
    
    # Handle incoming connections (URLs from new instances)
    def handle_new_connection():
        client_socket = server.nextPendingConnection()
        if client_socket.waitForReadyRead(1000):
            url_bytes = client_socket.readAll()
            url = str(url_bytes, 'utf-8')
            if url:
                window.handle_new_download(url)
    
    server.newConnection.connect(handle_new_connection)
    
    # Set window icon
    app_icon = get_app_icon()
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)
    
    # Show window
    window.show()
    
    # Handle command line URL (for the first instance)
    handle_command_line_url(window)
    
    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())