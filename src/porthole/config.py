"""Configuration management for k8s service proxy."""

import json
import logging
import os
import re
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Config(BaseModel):
    """Configuration for k8s service proxy."""

    # Kubernetes configuration
    kubeconfig_path: str | None = Field(
        default=None,
        description="Path to kubeconfig file. If None, will try in-cluster config first",
    )

    # Output configuration
    output_dir: Path = Field(
        default=Path("./generated-output"),
        description="Directory to write output files",
    )

    service_json_file: str = Field(
        default="services.json",
        description="Filename for service JSON data",
    )

    portal_html_file: str = Field(
        default="portal.html",
        description="Filename for portal HTML file",
    )

    nginx_config_file: str = Field(
        default="services.conf",
        description=(
            "Filename for nginx configuration "
            "(legacy, use upstreams_config_file and locations_config_file)"
        ),
    )
    locations_config_file: str = Field(
        default="locations.conf",
        description="Filename for nginx locations configuration",
    )

    # Namespace filtering
    skip_namespaces: list[str] = Field(
        default_factory=lambda: [
            "kube-system",
            "kube-public",
            "kube-node-lease",
            "local-path-storage",
            "kubernetes-dashboard",
            "metallb-system",
            "cert-manager",
            "ingress-nginx",
            "monitoring",
            "logging",
            "istio-system",
            "linkerd",
            "calico-system",
            "tigera-operator",
            "rook-ceph",
            "velero",
            "argocd",
            "flux-system",
        ],
        description="List of namespaces to skip during service discovery",
    )

    # Service filtering
    include_headless_services: bool = Field(
        default=False,
        description="Include services without cluster IP (headless services)",
    )

    # Portal configuration
    portal_title: str = Field(
        default="Kubernetes Services Portal",
        description="Title for the portal HTML page",
    )

    # Refresh configuration
    refresh_interval: int = Field(
        default=60,
        description="Refresh interval in seconds (0 to disable)",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)",
    )

    # Frontend pattern matching
    frontend_patterns: list[str] = Field(
        default_factory=list,
        description="Regex patterns to match frontend services",
    )

    # HTTP checking configuration
    enable_http_checking: bool = Field(
        default=True,
        description="Enable HTTP checking of service endpoints",
    )
    http_timeout: int = Field(
        default=10,
        description="Timeout in seconds for HTTP requests",
    )
    http_user_agent: str = Field(
        default="porthole-http-checker/1.0",
        description="User agent string for HTTP requests",
    )

    def is_frontend_service(self, service_name: str) -> bool:
        """Check if a service matches any frontend pattern in name."""
        if not self.frontend_patterns:
            return False

        # Check service name against patterns
        for pattern in self.frontend_patterns:
            if re.search(pattern, service_name, re.IGNORECASE):
                logger.debug(f"Service {service_name} matches pattern {pattern}")
                return True

        return False

    def is_frontend_port(self, port_name: str) -> bool:
        """Check if a specific port matches any frontend pattern."""
        if not self.frontend_patterns or not port_name:
            return False

        for pattern in self.frontend_patterns:
            if re.search(pattern, port_name, re.IGNORECASE):
                logger.debug(f"Port {port_name} matches pattern {pattern}")
                return True

        return False

    @classmethod
    def _load_json_config(cls) -> dict:
        """Load configuration from porthole-config.json if it exists."""
        config_path = Path(__file__).parent / "config" / "porthole-config.json"

        if not config_path.exists():
            logger.warning(f"Config file {config_path} does not exist")
            return {}
        logger.info(f"Loading config from {config_path}")
        try:
            with open(config_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Error loading config from {config_path}")
            logger.error(f"Error: {e}")
            exit(1)
            return {}

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables and JSON config file."""
        return cls.parse_config(debug_logging=False)

    @classmethod
    def parse_config(cls, debug_logging: bool = False) -> "Config":
        """Create configuration from environment variables and JSON config file."""
        # Load JSON config first
        json_config = cls._load_json_config()

        # Get skip_namespaces - prioritize env var, then JSON, then default
        skip_namespaces = None
        # if os.getenv("SKIP_NAMESPACES"):
        #     skip_namespaces = os.getenv("SKIP_NAMESPACES", "").split(",")
        if "namespaces-to-skip" in json_config:
            skip_namespaces = json_config["namespaces-to-skip"]
        else:
            skip_namespaces = []

        if debug_logging:
            logger.debug(f"Skip namespaces: {skip_namespaces}")

        # Get frontend patterns from JSON config
        frontend_patterns = json_config.get("frontend-pattern-matching", [])
        if debug_logging:
            logger.debug(f"Frontend patterns: {frontend_patterns}")

        # Get portal title from JSON config with fallback to default
        portal_title = json_config.get("portal-title", "Kubernetes Services Portal")
        if debug_logging:
            logger.debug(f"Portal title: {portal_title}")

        # Get refresh interval from JSON config with fallback to default
        refresh_interval = json_config.get("refresh-interval", 60)
        if debug_logging:
            logger.debug(f"Refresh interval: {refresh_interval}")

        # Get log level from JSON config with fallback to default
        log_level = json_config.get("log-level", "INFO")
        if debug_logging:
            logger.debug(f"Log level from JSON: {log_level}")

        # Get HTTP checking settings from JSON config
        enable_http_checking = json_config.get("enable-http-checking", True)
        http_timeout = json_config.get("http-timeout", 10)
        http_user_agent = json_config.get("http-user-agent", "porthole-http-checker/1.0")
        if debug_logging:
            logger.debug(f"HTTP checking enabled: {enable_http_checking}")
            logger.debug(f"HTTP timeout: {http_timeout}")

        return cls(
            kubeconfig_path=os.getenv("KUBECONFIG"),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./generated-output")),
            service_json_file=os.getenv("SERVICE_JSON_FILE", "services.json"),
            portal_html_file=os.getenv("PORTAL_HTML_FILE", "portal.html"),
            nginx_config_file=os.getenv("NGINX_CONFIG_FILE", "services.conf"),
            locations_config_file=os.getenv("LOCATIONS_CONFIG_FILE", "locations.conf"),
            skip_namespaces=skip_namespaces,
            include_headless_services=os.getenv(
                "INCLUDE_HEADLESS_SERVICES", "false",
            ).lower()
            == "true",
            portal_title=portal_title,
            refresh_interval=refresh_interval,
            log_level=os.getenv("LOG_LEVEL", log_level).upper(),
            frontend_patterns=frontend_patterns,
            enable_http_checking=os.getenv("ENABLE_HTTP_CHECKING", str(enable_http_checking)).lower() == "true",
            http_timeout=int(os.getenv("HTTP_TIMEOUT", str(http_timeout))),
            http_user_agent=os.getenv("HTTP_USER_AGENT", http_user_agent),
        )


# Global configuration instance (fallback)
config = Config.from_env()
