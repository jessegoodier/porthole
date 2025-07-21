"""Configuration management for k8s service proxy."""

import json
import os
import re
from pathlib import Path

from pydantic import BaseModel, Field


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
        default=300,
        description="Refresh interval in seconds (0 to disable)",
    )

    # Debug configuration
    debug: bool = Field(default=False, description="Enable debug logging")

    # Frontend pattern matching
    frontend_patterns: list[str] = Field(
        default_factory=list,
        description="Regex patterns to match frontend services",
    )

    def is_frontend_service(self, service_name: str) -> bool:
        """Check if a service matches any frontend pattern in name."""
        if not self.frontend_patterns:
            return False

        # Check service name against patterns
        for pattern in self.frontend_patterns:
            if re.search(pattern, service_name, re.IGNORECASE):
                print(f"--------------Service {service_name} matches pattern {pattern}")
                return True

        return False

    def is_frontend_port(self, port_name: str) -> bool:
        """Check if a specific port matches any frontend pattern."""
        if not self.frontend_patterns or not port_name:
            return False

        for pattern in self.frontend_patterns:
            if re.search(pattern, port_name, re.IGNORECASE):
                print(f"--------------Port {port_name} matches pattern {pattern}")
                return True
        
        return False

    @classmethod
    def _load_json_config(cls) -> dict:
        """Load configuration from porthole-config.json if it exists."""
        config_path = Path(__file__).parent / "config" / "porthole-config.json"

        if not config_path.exists():
            print(f"Warning: {config_path} does not exist")
            return {}

        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables and JSON config file."""
        # Load JSON config first
        json_config = cls._load_json_config()

        # Get skip_namespaces - prioritize env var, then JSON, then default
        skip_namespaces = None
        if os.getenv("SKIP_NAMESPACES"):
            skip_namespaces = os.getenv("SKIP_NAMESPACES", "").split(",")
        elif "namespaces-to-skip" in json_config:
            skip_namespaces = json_config["namespaces-to-skip"]
        else:
            skip_namespaces = []

        # Get frontend patterns from JSON config
        frontend_patterns = json_config.get("frontend-pattern-matching", [])

        return cls(
            kubeconfig_path=os.getenv("KUBECONFIG"),
            output_dir=Path(os.getenv("OUTPUT_DIR", "./generated-output")),
            service_json_file=os.getenv("SERVICE_JSON_FILE", "services.json"),
            portal_html_file=os.getenv("PORTAL_HTML_FILE", "portal.html"),
            nginx_config_file=os.getenv("NGINX_CONFIG_FILE", "services.conf"),
            locations_config_file=os.getenv("LOCATIONS_CONFIG_FILE", "locations.conf"),
            skip_namespaces=skip_namespaces,
            include_headless_services=os.getenv(
                "INCLUDE_HEADLESS_SERVICES", "false"
            ).lower()
            == "true",
            portal_title=os.getenv("PORTAL_TITLE", "Kubernetes Services Portal"),
            refresh_interval=int(os.getenv("REFRESH_INTERVAL", "300")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            frontend_patterns=frontend_patterns,
        )


# Global configuration instance
config = Config.from_env()
