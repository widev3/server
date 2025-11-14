import os
import threading
from datetime import datetime

class Logging:
    _folder = "logs"
    _lock = threading.Lock()

    @staticmethod
    def log(message: str):
        os.makedirs(Logging._folder, exist_ok=True)                 # ensure folder exists

        filename = datetime.now().strftime("%Y%m%d") + ".txt"       # daily file name
        path = os.path.join(Logging._folder, filename)

        now = datetime.now()
        ts = now.strftime("%Y-%m-%d %H:%M:%S") + f".{now.microsecond // 1000:03d}"

        with Logging._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
