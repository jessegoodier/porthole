"""Pydantic models for service data structures."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .constants import MAX_PORT, MIN_PORT


class ServiceType(str, Enum):
    """Kubernetes service types."""

    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"
    EXTERNAL_NAME = "ExternalName"


class EndpointStatus(str, Enum):
    """Endpoint status for services."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServicePort(BaseModel):
    """Represents a service port."""

    name: str | None = Field(None, description="Port name")
    port: int = Field(..., description="Service port number")
    target_port: str | None = Field(None, description="Target port on the pod")
    protocol: str = Field(default="TCP", description="Protocol (TCP/UDP)")
    node_port: int | None = Field(None, description="Node port for NodePort services")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not MIN_PORT <= v <= MAX_PORT:
            msg = f"Port must be between {MIN_PORT} and {MAX_PORT}"
            raise ValueError(msg)
        return v


class ServiceEndpoint(BaseModel):
    """Represents a service endpoint."""

    ip: str = Field(..., description="Endpoint IP address")
    port: int = Field(..., description="Endpoint port")
    ready: bool = Field(default=True, description="Whether endpoint is ready")
    hostname: str | None = Field(None, description="Endpoint hostname")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not MIN_PORT <= v <= MAX_PORT:
            msg = f"Port must be between {MIN_PORT} and {MAX_PORT}"
            raise ValueError(msg)
        return v


class KubernetesService(BaseModel):
    """Represents a Kubernetes service."""

    name: str = Field(..., description="Service name")
    namespace: str = Field(..., description="Service namespace")
    service_type: ServiceType = Field(..., description="Service type")
    cluster_ip: str | None = Field(None, description="Service cluster IP")
    external_ips: list[str] = Field(default_factory=list, description="External IPs")
    ports: list[ServicePort] = Field(default_factory=list, description="Service ports")
    endpoints: list[ServiceEndpoint] = Field(
        default_factory=list,
        description="Service endpoints",
    )
    labels: dict[str, str] = Field(default_factory=dict, description="Service labels")
    annotations: dict[str, str] = Field(
        default_factory=dict,
        description="Service annotations",
    )
    selector: dict[str, str] = Field(
        default_factory=dict,
        description="Service selector",
    )
    created_at: datetime | None = Field(None, description="Service creation timestamp")
    endpoint_status: EndpointStatus = Field(
        default=EndpointStatus.UNKNOWN,
        description="Endpoint health status",
    )
    is_frontend: bool = Field(
        default=False,
        description="Whether service is identified as frontend",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate service name."""
        if not v:
            msg = "Service name cannot be empty"
            raise ValueError(msg)
        return v

    @field_validator("namespace")
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Validate namespace."""
        if not v:
            msg = "Namespace cannot be empty"
            raise ValueError(msg)
        return v

    @model_validator(mode="before")
    @classmethod
    def detect_frontend(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Detect if service is a frontend service."""
        if isinstance(values, dict):
            v = values.get("is_frontend")
            if v is not None:
                values["is_frontend"] = bool(v)
                return values

            # Default to False - frontend detection will be handled in service discovery
            values["is_frontend"] = False
        return values

    @property
    def display_name(self) -> str:
        """Get display name for the service."""
        return f"{self.namespace}/{self.name}"

    @property
    def has_valid_endpoints(self) -> bool:
        """Check if service has valid endpoints."""
        return self.endpoint_status == EndpointStatus.HEALTHY

    @property
    def is_headless(self) -> bool:
        """Check if service is headless (no cluster IP)."""
        return self.cluster_ip is None or self.cluster_ip == "None"

    def get_port_display(self, port: ServicePort) -> str:
        """Get display string for a port."""
        if port.name:
            return f"{port.name}:{port.port}"
        return str(port.port)

    def get_proxy_url(self, port: ServicePort, base_url: str = "") -> str:
        """Get proxy URL for a service port."""
        port_suffix = f"_{port.port}"
        service_path = f"{self.namespace}_{self.name}{port_suffix}"
        return f"{base_url}/{service_path}/"


class ServiceDiscoveryResult(BaseModel):
    """Result of service discovery operation."""

    services: list[KubernetesService] = Field(
        default_factory=list,
        description="Discovered services",
    )
    namespaces_scanned: list[str] = Field(
        default_factory=list,
        description="Namespaces that were scanned",
    )
    namespaces_skipped: list[str] = Field(
        default_factory=list,
        description="Namespaces that were skipped",
    )
    total_services: int = Field(default=0, description="Total number of services found")
    healthy_services: int = Field(
        default=0,
        description="Number of services with healthy endpoints",
    )
    unhealthy_services: int = Field(
        default=0,
        description="Number of services with unhealthy endpoints",
    )
    frontend_services: int = Field(default=0, description="Number of frontend services")
    discovery_time: datetime | None = Field(
        None,
        description="When discovery was performed",
    )

    @model_validator(mode="before")
    @classmethod
    def calculate_services(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Calculate service counts from services list."""
        if isinstance(values, dict):
            services = values.get("services", [])
            values["total_services"] = len(services)
            values["healthy_services"] = sum(
                1 for s in services if s.endpoint_status == EndpointStatus.HEALTHY
            )
            values["unhealthy_services"] = sum(
                1 for s in services if s.endpoint_status == EndpointStatus.UNHEALTHY
            )
            values["frontend_services"] = sum(
                1 for s in services if s.is_frontend
            )
        return values

    def get_services_by_namespace(self) -> dict[str, list[KubernetesService]]:
        """Group services by namespace."""
        by_namespace: dict[str, list[KubernetesService]] = {}
        for service in self.services:
            if service.namespace not in by_namespace:
                by_namespace[service.namespace] = []
            by_namespace[service.namespace].append(service)
        return by_namespace

    def get_sorted_services(self) -> list[KubernetesService]:
        """Get services sorted alphabetically by namespace/service:port."""
        return sorted(self.services, key=lambda s: (s.namespace, s.name))


class PortalData(BaseModel):
    """Data structure for portal generation."""

    discovery_result: ServiceDiscoveryResult = Field(
        ...,
        description="Service discovery result",
    )
    portal_title: str = Field(
        default="Kubernetes Services Portal",
        description="Portal title",
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Generation timestamp",
    )
    refresh_interval: int = Field(
        default=300,
        description="Refresh interval in seconds",
    )

    @property
    def services_by_namespace(self) -> dict[str, list[KubernetesService]]:
        """Get services grouped by namespace."""
        return self.discovery_result.get_services_by_namespace()

    @property
    def sorted_services(self) -> list[KubernetesService]:
        """Get sorted services."""
        return self.discovery_result.get_sorted_services()


class NginxLocation(BaseModel):
    """Represents an nginx location configuration."""

    path: str = Field(..., description="Location path")
    service_dns: str = Field(..., description="Service DNS name with port")
    rewrite_rule: str | None = Field(None, description="Rewrite rule")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate location path."""
        if not v.startswith("/"):
            msg = "Location path must start with /"
            raise ValueError(msg)
        return v


class NginxConfig(BaseModel):
    """Represents nginx configuration."""

    locations: list[NginxLocation] = Field(
        default_factory=list,
        description="Location configurations",
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Generation timestamp",
    )
