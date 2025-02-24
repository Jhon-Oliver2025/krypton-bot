from app import background_monitor
import threading

def start_monitoring():
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()

if __name__ == "__main__":
    start_monitoring()