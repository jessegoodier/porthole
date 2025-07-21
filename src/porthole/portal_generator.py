"""JSON data generation for Kubernetes services portal."""

import json
import logging
from pathlib import Path

from .config import Config
from .models import ServiceDiscoveryResult

logger = logging.getLogger(__name__)


class PortalGenerator:
    """Generates JSON data for Kubernetes services portal."""

    def __init__(self, config: Config) -> None:
        """Initialize portal generator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.output_dir = Path(self.config.output_dir)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_data(self, discovery_result: ServiceDiscoveryResult) -> str:
        """Generate JSON data file for services portal.

        Args:
            discovery_result: Service discovery result

        Returns:
            Path to generated JSON file
        """
        logger.info("Generating JSON data file")

        # Use centralized to_dict method with portal format and config for port-level frontend detection
        services_data = discovery_result.to_dict(format_type="portal", config=self.config)

        # Write JSON file
        json_file = self.output_dir / self.config.service_json_file
        json_content = json.dumps(services_data, indent=2)
        json_file.write_text(json_content, encoding="utf-8")

        logger.info("Generated JSON data file: %s", json_file)
        return str(json_file)
