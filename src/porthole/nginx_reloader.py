import logging
import os
import subprocess
import time

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ConfigHandler(FileSystemEventHandler):
    def on_modified(self, event: FileSystemEvent) -> None:
        src_path = str(event.src_path)
        if event.is_directory or not src_path.endswith(".conf"):
            return

        logger.info(f"Config change detected: {src_path}")
        # Test config first
        result = subprocess.run(["nginx", "-t"], check=False, capture_output=True)
        if result.returncode == 0:
            subprocess.run(["nginx", "-s", "reload"], check=False)
            logger.info("Configuration reloaded successfully")
        else:
            logger.error("Configuration test failed, not reloading")


# Monitor /app/output directory
observer = Observer()
observer.schedule(ConfigHandler(), "/app/output", recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
