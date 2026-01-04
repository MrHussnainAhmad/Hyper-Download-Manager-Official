import psutil
import time
from PySide6.QtCore import QObject, Signal, QThread

class SystemMonitorWorker(QThread):
    speed_updated = Signal(float) # bytes per second
    disk_usage_updated = Signal(float, float, float) # free_bytes, total_bytes, percent_used
    connection_status_changed = Signal(bool) # Connected/Disconnected

    def __init__(self):
        super().__init__()
        self.running = True
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()

    def run(self):
        while self.running:
            # Network Speed
            current_io = psutil.net_io_counters()
            current_time = time.time()
            
            bytes_recv = current_io.bytes_recv - self.last_io.bytes_recv
            # bytes_sent = current_io.bytes_sent - self.last_io.bytes_sent # Not monitoring upload
            
            elapsed = current_time - self.last_time
            if elapsed > 0:
                speed = bytes_recv / elapsed # Bytes/sec
                self.speed_updated.emit(speed)
            
            self.last_io = current_io
            self.last_time = current_time

            # Disk Usage (C:)
            try:
                usage = psutil.disk_usage('C:\\')
                self.disk_usage_updated.emit(usage.free, usage.total, usage.percent)
            except Exception:
                pass

            # Connection check
            is_connected = False
            try:
                # Check for active internet connection by trying to resolve/connect to a reliable host
                # We use socket connection for a lightweight check
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=1)
                is_connected = True
            except OSError:
                pass
                
            self.connection_status_changed.emit(is_connected)

            time.sleep(0.1) # 10Hz update rate as requested

    def stop(self):
        self.running = False
        self.wait()
