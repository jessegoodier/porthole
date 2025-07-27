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
        if event.is_directory:
            return

        # Check if this is a config file or trigger file
        if src_path.endswith(".conf") or src_path.endswith("nginx-reload.trigger"):
            logger.info(f"Config change detected: {src_path}")
            self._reload_openresty()

    def _reload_openresty(self) -> None:
        """Reload openresty configuration after testing."""
        # Test config first
        result = subprocess.run(["openresty", "-t"], check=False, capture_output=True)
        if result.returncode == 0:
            subprocess.run(["openresty", "-s", "reload"], check=False)
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
