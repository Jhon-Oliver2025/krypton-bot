from app import app, start_monitoring, background_monitor, analyzer, db, notifier
import threading
import time
from app import app

server = app.server

if __name__ == "__main__":
    app.run()