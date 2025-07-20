"""Nginx configuration generation for Kubernetes services."""

import logging
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

from .config import Config
from .models import (
    KubernetesService,
    NginxConfig,
    NginxLocation,
    ServiceDiscoveryResult,
)

logger = logging.getLogger(__name__)


class NginxGenerator:
    """Generates nginx configuration for Kubernetes services."""

    def __init__(self, config: Config):
        """Initialize nginx generator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.template_dir = Path(__file__).parent.parent.parent / "templates"
        self.output_dir = Path(self.config.output_dir)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False,  # Nginx config doesn't need HTML escaping
        )


    def generate_nginx_config(self, discovery_result: ServiceDiscoveryResult) -> str:
        """Generate nginx configuration from service discovery result.

        Args:
            discovery_result: Service discovery result

        Returns:
            Path to generated nginx locations config file
        """
        logger.info("Generating nginx configuration")

        # Generate nginx config model
        nginx_config = self._build_nginx_config(discovery_result)

        # Generate location file
        locations_file = self._generate_locations_config(nginx_config)

        logger.info(f"Generated nginx locations: {locations_file}")
        return str(locations_file)

    def _generate_locations_config(self, nginx_config: NginxConfig) -> str:
        """Generate locations configuration file.

        Args:
            nginx_config: NginxConfig model

        Returns:
            Path to generated locations config file
        """
        # Load locations template
        template = self.jinja_env.get_template("locations.conf.j2")

        # Render locations configuration
        content = template.render(
            locations=nginx_config.locations,
            generated_at=nginx_config.generated_at,
        )

        # Write locations file
        locations_file = self.output_dir / self.config.locations_config_file
        locations_file.write_text(content, encoding="utf-8")

        return str(locations_file)

    def _build_nginx_config(
        self, discovery_result: ServiceDiscoveryResult
    ) -> NginxConfig:
        """Build nginx configuration model from services.

        Args:
            discovery_result: Service discovery result

        Returns:
            NginxConfig model
        """
        locations = []
        processed_services = set()

        for service in discovery_result.services:
            # Skip services without healthy endpoints
            if not service.has_valid_endpoints:
                logger.debug(
                    f"Skipping service without healthy endpoints: {service.display_name}"
                )
                continue

            for port in service.ports:
                # Generate location path and service DNS
                location_path = self._generate_location_path(service, port)
                service_dns = self._generate_service_dns(service, port)

                # Skip if already processed (avoid duplicates)
                service_key = f"{service.namespace}_{service.name}_{port.port}"
                if service_key in processed_services:
                    continue
                processed_services.add(service_key)

                # Create single location per service
                location = NginxLocation(
                    path=location_path,
                    service_dns=service_dns,
                )
                locations.append(location)

        return NginxConfig(locations=locations)

    def _generate_service_dns(self, service: KubernetesService, port: Any) -> str:
        """Generate service DNS name with port for direct proxy_pass.

        Args:
            service: Kubernetes service
            port: Service port

        Returns:
            Service DNS name with port (e.g., 'service-name.namespace.svc.cluster.local:port')
        """
        # Use Kubernetes DNS naming: service.namespace.svc.cluster.local:port
        return f"{service.name}.{service.namespace}.svc.cluster.local:{port.port}"

    def _generate_location_path(self, service: KubernetesService, port: Any) -> str:
        """Generate location path for a service.

        Args:
            service: Kubernetes service
            port: Service port

        Returns:
            Location path
        """
        # Format: /{namespace}_{service}_{port}
        path = f"/{service.namespace}_{service.name}_{port.port}"

        # Clean up the path
        clean_path = re.sub(r"[^a-zA-Z0-9\-_/]", "_", path)
        clean_path = re.sub(r"_+", "_", clean_path)  # Remove multiple underscores

        return clean_path




    def generate_docker_compose_override(
        self, discovery_result: ServiceDiscoveryResult
    ) -> str:
        """Generate docker-compose override for nginx proxy.

        Args:
            discovery_result: Service discovery result

        Returns:
            Path to generated docker-compose override file
        """
        logger.info("Generating docker-compose override for nginx proxy")

        # Generate port mappings for all services
        port_mappings = []
        base_port = 6060

        for i, service in enumerate(discovery_result.get_sorted_services()):
            if not service.has_valid_endpoints:
                continue

            for port in service.ports:
                external_port = base_port + i
                port_mappings.append(f'      - "{external_port}:80"')

        # Generate docker-compose override content
        override_content = f"""version: '3.8'
services:
  nginx-proxy:
    image: nginx:alpine
    ports:
{chr(10).join(port_mappings)}
    volumes:
      - ./output/{self.config.nginx_config_file}:/etc/nginx/conf.d/default.conf:ro
      - ./output/{self.config.portal_html_file}:/usr/share/nginx/html/index.html:ro
    restart: unless-stopped
    depends_on:
      - k8s-service-proxy
  
  k8s-service-proxy:
    build: .
    volumes:
      - ./output:/app/output
      - ~/.kube:/root/.kube:ro
    environment:
      - REFRESH_INTERVAL=300
    restart: unless-stopped
"""

        # Write override file
        override_file = self.output_dir / "docker-compose.override.yml"
        override_file.write_text(override_content, encoding="utf-8")

        logger.info(f"Generated docker-compose override: {override_file}")
        return str(override_file)

    def validate_nginx_config(self, config_file: str) -> bool:
        """Validate nginx configuration syntax.

        Args:
            config_file: Path to nginx config file

        Returns:
            True if config is valid
        """
        # This is a basic validation - in a real implementation,
        # you might want to use nginx -t or a more sophisticated parser
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                logger.error(f"Nginx config file not found: {config_file}")
                return False

            content = config_path.read_text(encoding="utf-8")

            # Basic syntax checks
            if content.count("{") != content.count("}"):
                logger.error("Mismatched braces in nginx config")
                return False

            # Check for required sections
            if "location" not in content:
                logger.warning("No location blocks found in nginx config")

            logger.info("Nginx configuration appears valid")
            return True

        except Exception as e:
            logger.error(f"Failed to validate nginx config: {e}")
            return False
