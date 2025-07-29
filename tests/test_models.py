"""Tests for porthole models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from porthole.models import (EndpointStatus, KubernetesService, NginxConfig,
                             NginxLocation, ServiceDiscoveryResult,
                             ServiceEndpoint, ServicePort, ServiceType)


class TestServicePort:
    """Test ServicePort model."""

    def test_valid_port(self):
        """Test creating a valid service port."""
        port = ServicePort(port=7070, protocol="TCP")
        assert port.port == 7070
        assert port.protocol == "TCP"
        assert port.name is None

    def test_port_with_name(self):
        """Test creating a port with a name."""
        port = ServicePort(name="http", port=80)
        assert port.name == "http"
        assert port.port == 80

    def test_invalid_port_low(self):
        """Test port validation for values too low."""
        with pytest.raises(ValidationError) as exc_info:
            ServicePort(port=0)
        assert "Port must be between" in str(exc_info.value)

    def test_invalid_port_high(self):
        """Test port validation for values too high."""
        with pytest.raises(ValidationError) as exc_info:
            ServicePort(port=65536)
        assert "Port must be between" in str(exc_info.value)

    def test_node_port(self):
        """Test NodePort functionality."""
        port = ServicePort(port=80, node_port=30080)
        assert port.node_port == 30080


class TestServiceEndpoint:
    """Test ServiceEndpoint model."""

    def test_valid_endpoint(self):
        """Test creating a valid endpoint."""
        endpoint = ServiceEndpoint(ip="10.244.1.5", port=7070)
        assert endpoint.ip == "10.244.1.5"
        assert endpoint.port == 7070
        assert endpoint.ready is True

    def test_endpoint_not_ready(self):
        """Test endpoint that's not ready."""
        endpoint = ServiceEndpoint(ip="10.244.1.5", port=7070, ready=False)
        assert endpoint.ready is False

    def test_endpoint_with_hostname(self):
        """Test endpoint with hostname."""
        endpoint = ServiceEndpoint(
            ip="10.244.1.5",
            port=7070,
            hostname="pod-1.service.default.svc.cluster.local",
        )
        assert endpoint.hostname == "pod-1.service.default.svc.cluster.local"


class TestKubernetesService:
    """Test KubernetesService model."""

    def test_basic_service(self):
        """Test creating a basic service."""
        service = KubernetesService(
            name="webapp",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(port=80)],
            endpoints=[ServiceEndpoint(ip="10.244.1.5", port=80)],
        )
        assert service.name == "webapp"
        assert service.namespace == "default"
        assert service.service_type == ServiceType.CLUSTER_IP
        assert len(service.ports) == 1
        assert len(service.endpoints) == 1

    def test_frontend_detection_by_name(self):
        """Test frontend detection based on service name."""
        service = KubernetesService(
            name="frontend-webapp",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(port=80)],
            endpoints=[],
        )
        assert service.is_frontend is True

    def test_frontend_detection_by_labels(self):
        """Test frontend detection based on labels."""
        service = KubernetesService(
            name="webapp",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(port=80)],
            endpoints=[],
            labels={"tier": "frontend"},
        )
        assert service.is_frontend is True

    def test_display_name(self):
        """Test display name property."""
        service = KubernetesService(
            name="webapp",
            namespace="production",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(port=80)],
            endpoints=[],
        )
        assert service.display_name == "production/webapp"

    def test_no_valid_endpoints(self):
        """Test service with no endpoints."""
        service = KubernetesService(
            name="webapp",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(port=80)],
            endpoints=[],
        )
        assert service.has_valid_endpoints is False

    def test_get_port_display(self):
        """Test port display formatting."""
        service = KubernetesService(
            name="webapp",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(name="http", port=80)],
            endpoints=[],
        )
        port_display = service.get_port_display(service.ports[0])
        assert port_display == "http:80"

    def test_get_port_display_no_name(self):
        """Test port display without name."""
        service = KubernetesService(
            name="webapp",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(port=80)],
            endpoints=[],
        )
        port_display = service.get_port_display(service.ports[0])
        assert port_display == "80"

    def test_get_proxy_url(self):
        """Test proxy URL generation."""
        service = KubernetesService(
            name="webapp",
            namespace="default",
            service_type=ServiceType.CLUSTER_IP,
            ports=[ServicePort(port=80)],
            endpoints=[],
        )
        url = service.get_proxy_url(service.ports[0], "http://proxy.example.com")
        assert url == "http://proxy.example.com/default_webapp_80/"

    def test_empty_name_validation(self):
        """Test validation of empty service name."""
        with pytest.raises(ValidationError) as exc_info:
            KubernetesService(
                name="",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[],
            )
        assert "Service name cannot be empty" in str(exc_info.value)

    def test_empty_namespace_validation(self):
        """Test validation of empty namespace."""
        with pytest.raises(ValidationError) as exc_info:
            KubernetesService(
                name="webapp",
                namespace="",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[],
            )
        assert "Namespace cannot be empty" in str(exc_info.value)


class TestServiceDiscoveryResult:
    """Test ServiceDiscoveryResult model."""

    def test_empty_result(self):
        """Test empty discovery result."""
        result = ServiceDiscoveryResult(
            services=[],
            namespaces_scanned=["default"],
            namespaces_skipped=["kube-system"],
        )
        assert result.total_services == 0
        assert result.healthy_services == 0
        assert result.unhealthy_services == 0
        assert result.frontend_services == 0

    def test_result_with_services(self):
        """Test result with multiple services."""
        services = [
            KubernetesService(
                name="webapp",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[ServiceEndpoint(ip="10.244.1.5", port=80)],
                endpoint_status=EndpointStatus.HEALTHY,
                is_frontend=True,
            ),
            KubernetesService(
                name="api",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=7070)],
                endpoints=[],
                endpoint_status=EndpointStatus.UNHEALTHY,
            ),
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default"],
            namespaces_skipped=[],
        )

        assert result.total_services == 2
        assert result.healthy_services == 1
        assert result.unhealthy_services == 1
        assert result.frontend_services == 1

    def test_get_services_by_namespace(self):
        """Test grouping services by namespace."""
        services = [
            KubernetesService(
                name="webapp",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[],
            ),
            KubernetesService(
                name="api",
                namespace="production",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=7070)],
                endpoints=[],
            ),
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default", "production"],
            namespaces_skipped=[],
        )

        by_namespace = result.get_services_by_namespace()
        assert "default" in by_namespace
        assert "production" in by_namespace
        assert len(by_namespace["default"]) == 1
        assert len(by_namespace["production"]) == 1

    def test_get_sorted_services(self):
        """Test sorting services."""
        services = [
            KubernetesService(
                name="zebra",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[],
            ),
            KubernetesService(
                name="alpha",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=7070)],
                endpoints=[],
            ),
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default"],
            namespaces_skipped=[],
        )

        sorted_services = result.get_sorted_services()
        assert sorted_services[0].name == "alpha"
        assert sorted_services[1].name == "zebra"


class TestNginxLocation:
    """Test NginxLocation model."""

    def test_valid_location(self):
        """Test creating a valid nginx location."""
        location = NginxLocation(
            path="/api",
            service_dns="api.default.svc.cluster.local:7070",
        )
        assert location.path == "/api"
        assert location.service_dns == "api.default.svc.cluster.local:7070"

    def test_location_with_rewrite(self):
        """Test location with rewrite rule."""
        location = NginxLocation(
            path="/app",
            service_dns="webapp.default.svc.cluster.local:80",
            rewrite_rule="^/app/?(.*)$ /$1 break",
        )
        assert location.rewrite_rule == "^/app/?(.*)$ /$1 break"

    def test_invalid_path(self):
        """Test path validation."""
        with pytest.raises(ValidationError) as exc_info:
            NginxLocation(
                path="api",  # Missing leading slash
                service_dns="api.default.svc.cluster.local:7070",
            )
        assert "Location path must start with /" in str(exc_info.value)


class TestNginxConfig:
    """Test NginxConfig model."""

    def test_empty_config(self):
        """Test empty nginx config."""
        config = NginxConfig(locations=[])
        assert len(config.locations) == 0

    def test_config_with_locations(self):
        """Test config with locations."""
        locations = [
            NginxLocation(
                path="/api",
                service_dns="api.default.svc.cluster.local:7070",
            ),
            NginxLocation(
                path="/web",
                service_dns="webapp.default.svc.cluster.local:80",
            ),
        ]
        config = NginxConfig(locations=locations)
        assert len(config.locations) == 2


if __name__ == "__main__":
    pytest.main([__file__])
