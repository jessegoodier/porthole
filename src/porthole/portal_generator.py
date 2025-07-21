"""HTML portal generation for Kubernetes services."""

import json
import logging
from datetime import UTC, datetime, timezone
from pathlib import Path

from .config import Config
from .models import ServiceDiscoveryResult

logger = logging.getLogger(__name__)


class PortalGenerator:
    """Generates HTML portal for Kubernetes services."""

    def __init__(self, config: Config) -> None:
        """Initialize portal generator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.output_dir = Path(self.config.output_dir)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_portal(self, _discovery_result: ServiceDiscoveryResult) -> str:
        """Generate portal (static files now served via ConfigMap).

        Args:
            discovery_result: Service discovery result (not used for static files)

        Returns:
            Success message
        """
        logger.info("Portal HTML served via ConfigMap - no file generation needed")
        return "Portal served via ConfigMap"

    def generate_table(self, _discovery_result: ServiceDiscoveryResult) -> str:
        """Generate table (static files now served via ConfigMap).

        Args:
            discovery_result: Service discovery result (not used for static files)

        Returns:
            Success message
        """
        logger.info("Table HTML served via ConfigMap - no file generation needed")
        return "Table served via ConfigMap"

    def generate_json_data(self, discovery_result: ServiceDiscoveryResult) -> str:
        """Generate JSON data file for services.

        Args:
            discovery_result: Service discovery result

        Returns:
            Path to generated JSON file
        """
        logger.info("Generating JSON data file")

        # Convert services to JSON format matching template
        services_data = {
            "services": [],
            "meta": {
                "total_services": discovery_result.total_services,
                "healthy_services": discovery_result.healthy_services,
                "unhealthy_services": discovery_result.unhealthy_services,
                "frontend_services": discovery_result.frontend_services,
                "namespaces_scanned": discovery_result.namespaces_scanned,
                "namespaces_skipped": discovery_result.namespaces_skipped,
                "discovery_time": discovery_result.discovery_time.isoformat()
                if discovery_result.discovery_time
                else None,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        }

        # Convert each service to JSON format
        for service in discovery_result.get_sorted_services():
            for port in service.ports:
                service_entry = {
                    "namespace": service.namespace,
                    "service": service.name,
                    "port": port.port,
                    "port_name": port.name,
                    "protocol": port.protocol,
                    "service_type": service.service_type.value,
                    "cluster_ip": service.cluster_ip,
                    "endpoint_status": service.endpoint_status.value,
                    "is_frontend": service.is_frontend,
                    "has_endpoints": service.has_valid_endpoints,
                    "endpoint_count": len(service.endpoints),
                    "proxy_url": service.get_proxy_url(port),
                    "display_name": f"{service.display_name}:{port.port}",
                    "created_at": service.created_at.isoformat() if service.created_at else None,
                }
                services_data["services"].append(service_entry)  # type: ignore[attr-defined]

        # Write JSON file
        json_file = self.output_dir / self.config.service_json_file
        json_content = json.dumps(services_data, indent=2)
        json_file.write_text(json_content, encoding="utf-8")

        logger.info("Generated JSON data file: %s", json_file)
        return str(json_file)
