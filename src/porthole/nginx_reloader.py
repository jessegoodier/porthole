import os
import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ConfigHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.conf'):
            return
        
        print(f"Config change detected: {event.src_path}")
        # Test config first
        result = subprocess.run(['nginx', '-t'], capture_output=True)
        if result.returncode == 0:
            subprocess.run(['nginx', '-s', 'reload'])
            print("Configuration reloaded successfully")
        else:
            print("Configuration test failed, not reloading")

# Monitor /app/output directory
observer = Observer()
observer.schedule(ConfigHandler(), '/app/output', recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()