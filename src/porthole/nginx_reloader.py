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
            self._reload_nginx()

    def _reload_nginx(self) -> None:
        """Reload nginx configuration."""
        try:
            # Check if nginx is running by looking for the PID file
            pid_file = "/tmp/nginx.pid"
            if not os.path.exists(pid_file):
                logger.warning(f"Nginx PID file not found at {pid_file}, checking for running processes...")
                
                # Check if nginx process is actually running
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", "nginx"],
                        check=False, capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        logger.info(f"Found nginx process(es): {result.stdout.strip()}")
                        # Process is running but no PID file, try reload anyway
                    else:
                        logger.warning("No nginx processes found")
                        return
                except Exception as e:
                    logger.error(f"Failed to check for nginx processes: {e}")
                    return
                
            # Test configuration first
            result = subprocess.run(
                ["nginx", "-t"],
                check=False, capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Configuration is valid, reload
                reload_result = subprocess.run(
                    ["nginx", "-s", "reload"],
                    check=False, capture_output=True,
                    text=True,
                    timeout=10,
                )
                if reload_result.returncode == 0:
                    logger.info("Nginx configuration reloaded successfully")
                else:
                    logger.error(f"Nginx reload failed: {reload_result.stderr}")
            else:
                logger.error(f"Nginx configuration test failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Nginx reload command timed out")
        except Exception as e:
            logger.error(f"Failed to reload nginx: {e}")


def start_config_watcher(watch_dir: str) -> None:
    """Start watching for configuration changes."""
    logger.info(f"Starting nginx configuration watcher on directory: {watch_dir}")

    event_handler = ConfigHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Nginx configuration watcher stopped")

    observer.join()


if __name__ == "__main__":
    import os
    watch_dir = os.environ.get("WATCH_DIR", "/app/generated-output")
    start_config_watcher(watch_dir)
