"""HTML portal generation for Kubernetes services."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader, Template

from .config import Config
from .models import EndpointStatus, KubernetesService, PortalData, ServiceDiscoveryResult

logger = logging.getLogger(__name__)


class PortalGenerator:
    """Generates HTML portal for Kubernetes services."""

    def __init__(self, config: Config):
        """Initialize portal generator.

        Args:
            config: Configuration object
        """
        self.config = config
        self.template_dir = Path(__file__).parent.parent.parent / "templates"
        self.output_dir = Path(self.config.output_dir)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir), autoescape=True)

        # Add custom filters
        self.jinja_env.filters["datetime_format"] = self._datetime_format
        self.jinja_env.filters["status_icon"] = self._status_icon
        self.jinja_env.filters["frontend_icon"] = self._frontend_icon
        self.jinja_env.filters["service_url"] = self._service_url

    def generate_portal(self, discovery_result: ServiceDiscoveryResult) -> str:
        """Generate HTML portal from service discovery result.

        Args:
            discovery_result: Service discovery result

        Returns:
            Path to generated HTML file
        """
        logger.info("Generating HTML portal")

        # Create portal data
        portal_data = PortalData(
            discovery_result=discovery_result,
            portal_title=self.config.portal_title,
            refresh_interval=self.config.refresh_interval,
        )

        # Generate HTML
        try:
            template = self.jinja_env.get_template("portal.html")
            html_content = template.render(
                portal_data=portal_data,
                config=self.config,
                now=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to render portal template: {e}")
            # Fallback to inline template
            html_content = self._generate_inline_portal(portal_data)

        # Write HTML file
        html_file = self.output_dir / self.config.portal_html_file
        html_file.write_text(html_content, encoding="utf-8")

        logger.info(f"Generated HTML portal: {html_file}")
        return str(html_file)

    def generate_table(self, discovery_result: ServiceDiscoveryResult) -> str:
        """Generate HTML table view from service discovery result.

        Args:
            discovery_result: Service discovery result

        Returns:
            Path to generated HTML table file
        """
        logger.info("Generating HTML table view")

        # Create portal data
        portal_data = PortalData(
            discovery_result=discovery_result,
            portal_title=self.config.portal_title,
            refresh_interval=self.config.refresh_interval,
        )

        # Create services list for table template
        services_list = []
        for service in discovery_result.get_sorted_services():
            for port in service.ports:
                services_list.append({
                    "namespace": service.namespace,
                    "service": service.name,
                    "port": port.port,
                    "port_name": port.name if port.name else "N/A",
                    "protocol": port.protocol,
                    "service_type": service.service_type.value,
                    "cluster_ip": service.cluster_ip or "N/A",
                    "endpoint_status": service.endpoint_status.value,
                    "is_frontend": service.is_frontend,
                    "has_endpoints": service.has_valid_endpoints,
                    "endpoint_count": len(service.endpoints),
                    "proxy_url": service.get_proxy_url(port),
                    "display_name": service.display_name,
                    "created_at": service.created_at.strftime('%Y-%m-%d %H:%M:%S') if service.created_at else "N/A",
                })

        # Generate HTML
        try:
            template = self.jinja_env.get_template("table.html")
            html_content = template.render(
                portal_data=portal_data,
                services=services_list,
                config=self.config,
                now=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to render table template: {e}")
            raise

        # Write HTML file
        table_file = self.output_dir / "table.html"
        table_file.write_text(html_content, encoding="utf-8")

        logger.info(f"Generated HTML table: {table_file}")
        return str(table_file)

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
                "generated_at": datetime.now().isoformat(),
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
                services_data["services"].append(service_entry)  # type: ignore

        # Write JSON file
        json_file = self.output_dir / self.config.service_json_file
        json_file.write_text(json.dumps(services_data, indent=2), encoding="utf-8")

        logger.info(f"Generated JSON data file: {json_file}")
        return str(json_file)

    def _generate_inline_portal(self, portal_data: PortalData) -> str:
        """Generate inline HTML portal as fallback.

        Args:
            portal_data: Portal data

        Returns:
            Generated HTML content
        """
        logger.info("Generating inline HTML portal (fallback)")

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            f"    <title>{portal_data.portal_title}</title>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <style>",
            self._get_inline_css(),
            "    </style>",
            "</head>",
            "<body>",
            f"    <header><h1>{portal_data.portal_title}</h1></header>",
            "    <main>",
            self._generate_service_grid(portal_data),
            "    </main>",
            "    <footer>",
            f"        <p>Generated at {portal_data.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"        <p>Total: {portal_data.discovery_result.total_services} services, "
            f"Healthy: {portal_data.discovery_result.healthy_services}, "
            f"Unhealthy: {portal_data.discovery_result.unhealthy_services}</p>",
            "    </footer>",
            "</body>",
            "</html>",
        ]

        return "\n".join(html_parts)

    def _generate_service_grid(self, portal_data: PortalData) -> str:
        """Generate service grid HTML.

        Args:
            portal_data: Portal data

        Returns:
            Service grid HTML
        """
        grid_parts = ["<div class='service-grid'>"]

        # Group services by namespace
        by_namespace = portal_data.services_by_namespace

        for namespace in sorted(by_namespace.keys()):
            services = by_namespace[namespace]

            grid_parts.append("<div class='namespace-section'>")
            grid_parts.append(f"    <h2 class='namespace-title'>{namespace}</h2>")
            grid_parts.append("    <div class='services-list'>")

            # Sort services within namespace
            sorted_services = sorted(services, key=lambda s: s.name)

            for service in sorted_services:
                for port in service.ports:
                    service_html = self._generate_service_card(service, port)
                    grid_parts.append(f"        {service_html}")

            grid_parts.append("    </div>")
            grid_parts.append("</div>")

        grid_parts.append("</div>")
        return "\n".join(grid_parts)

    def _generate_service_card(self, service: KubernetesService, port: Any) -> str:
        """Generate HTML for a service card.

        Args:
            service: Kubernetes service
            port: Service port

        Returns:
            Service card HTML
        """
        status_icon = self._status_icon(service.endpoint_status)
        frontend_icon = self._frontend_icon(service.is_frontend)
        proxy_url = service.get_proxy_url(port)

        card_html = f"""
        <div class='service-card {service.endpoint_status.value}'>
            <div class='service-header'>
                <span class='status-icon'>{status_icon}</span>
                <span class='service-name'>{service.name}</span>
                <span class='frontend-icon'>{frontend_icon}</span>
            </div>
            <div class='service-details'>
                <div class='port-info'>Port: {port.port}</div>
                <div class='service-type'>{service.service_type.value}</div>
                <div class='endpoint-count'>{len(service.endpoints)} endpoints</div>
            </div>
            <div class='service-actions'>
                <a href='{proxy_url}' class='service-link' target='_blank'>
                    Open Service
                </a>
            </div>
        </div>
        """

        return card_html.strip()

    def _get_inline_css(self) -> str:
        """Get inline CSS for the portal.

        Returns:
            CSS styles
        """
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }
        
        header {
            background-color: #2d2d2d;
            padding: 1rem;
            border-bottom: 2px solid #4a4a4a;
        }
        
        h1 {
            color: #ffffff;
            text-align: center;
        }
        
        main {
            padding: 2rem;
        }
        
        .service-grid {
            display: grid;
            gap: 2rem;
        }
        
        .namespace-section {
            background-color: #2d2d2d;
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid #4a4a4a;
        }
        
        .namespace-title {
            color: #64b5f6;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }
        
        .services-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        
        .service-card {
            background-color: #3a3a3a;
            border-radius: 6px;
            padding: 1rem;
            border: 1px solid #4a4a4a;
            transition: transform 0.2s;
        }
        
        .service-card:hover {
            transform: translateY(-2px);
            border-color: #64b5f6;
        }
        
        .service-card.healthy {
            border-left: 4px solid #4caf50;
        }
        
        .service-card.unhealthy {
            border-left: 4px solid #f44336;
        }
        
        .service-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .service-name {
            font-weight: bold;
            color: #ffffff;
            margin-left: 0.5rem;
            flex-grow: 1;
        }
        
        .status-icon {
            font-size: 1.2rem;
        }
        
        .frontend-icon {
            font-size: 1.2rem;
            margin-left: 0.5rem;
        }
        
        .service-details {
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #b0b0b0;
        }
        
        .service-actions {
            text-align: center;
        }
        
        .service-link {
            display: inline-block;
            background-color: #64b5f6;
            color: #ffffff;
            padding: 0.5rem 1rem;
            text-decoration: none;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .service-link:hover {
            background-color: #42a5f5;
        }
        
        footer {
            background-color: #2d2d2d;
            padding: 1rem;
            text-align: center;
            border-top: 2px solid #4a4a4a;
            color: #b0b0b0;
        }
        """

    def _datetime_format(self, dt: datetime | None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime for display.

        Args:
            dt: Datetime object
            fmt: Format string

        Returns:
            Formatted datetime string
        """
        if dt is None:
            return "N/A"
        return dt.strftime(fmt)

    def _status_icon(self, status: EndpointStatus) -> str:
        """Get status icon for endpoint status.

        Args:
            status: Endpoint status

        Returns:
            Status icon character
        """
        if status == EndpointStatus.HEALTHY:
            return "✅"
        if status == EndpointStatus.UNHEALTHY:
            return "❌"
        return "❓"

    def _frontend_icon(self, is_frontend: bool) -> str:
        """Get frontend icon.

        Args:
            is_frontend: Whether service is frontend

        Returns:
            Frontend icon character
        """
        return "✅" if is_frontend else ""

    def _service_url(self, service: KubernetesService, port: Any, base_url: str = "") -> str:
        """Get service URL.

        Args:
            service: Kubernetes service
            port: Service port
            base_url: Base URL for services

        Returns:
            Service URL
        """
        return service.get_proxy_url(port, base_url)
