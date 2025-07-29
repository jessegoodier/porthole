"""Shared test fixtures for porthole tests."""

import tempfile
from pathlib import Path

import pytest

from porthole.config import Config
from porthole.models import (EndpointStatus, KubernetesService,
                             ServiceDiscoveryResult, ServiceEndpoint,
                             ServicePort, ServiceType)


@pytest.fixture
def temp_config():
    """Create a temporary configuration with temp directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Config(output_dir=Path(temp_dir))


@pytest.fixture
def sample_service():
    """Create a sample Kubernetes service for testing."""
    return KubernetesService(
        name="webapp",
        namespace="default",
        service_type=ServiceType.CLUSTER_IP,
        ports=[
            ServicePort(name="http", port=80),
            ServicePort(name="https", port=443),
        ],
        endpoints=[
            ServiceEndpoint(ip="10.244.1.5", port=80),
            ServiceEndpoint(ip="10.244.1.6", port=80),
        ],
        endpoint_status=EndpointStatus.HEALTHY,
        is_frontend=True,
        cluster_ip="10.96.100.1",
        labels={"app": "webapp", "tier": "frontend"},
    )


@pytest.fixture
def unhealthy_service():
    """Create an unhealthy Kubernetes service for testing."""
    return KubernetesService(
        name="broken-api",
        namespace="default",
        service_type=ServiceType.CLUSTER_IP,
        ports=[ServicePort(port=7070)],
        endpoints=[],
        endpoint_status=EndpointStatus.UNHEALTHY,
        cluster_ip="10.96.100.2",
    )


@pytest.fixture
def sample_services(sample_service, unhealthy_service):
    """Create a list of sample services."""
    backend_service = KubernetesService(
        name="api",
        namespace="production",
        service_type=ServiceType.NODE_PORT,
        ports=[ServicePort(port=7070, node_port=30080)],
        endpoints=[ServiceEndpoint(ip="10.244.2.5", port=7070)],
        endpoint_status=EndpointStatus.HEALTHY,
        cluster_ip="10.96.100.3",
    )

    return [sample_service, unhealthy_service, backend_service]


@pytest.fixture
def sample_discovery_result(sample_services):
    """Create a sample service discovery result."""
    return ServiceDiscoveryResult(
        services=sample_services,
        namespaces_scanned=["default", "production"],
        namespaces_skipped=["kube-system", "kube-public"],
    )


@pytest.fixture
def empty_discovery_result():
    """Create an empty service discovery result."""
    return ServiceDiscoveryResult(
        services=[],
        namespaces_scanned=["default"],
        namespaces_skipped=["kube-system"],
    )


@pytest.fixture
def mock_k8s_client():
    """Create a mock Kubernetes client."""
    from unittest.mock import Mock

    mock_client = Mock()
    mock_client.get_cluster_info.return_value = {
        "node_count": 3,
        "namespace_count": 5,
        "api_resources": 150,
        "cluster_ready": True,
    }

    return mock_client


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return Config(
        kubeconfig_path="/test/kubeconfig",
        service_json_file="test-services.json",
        portal_html_file="test-portal.html",
        nginx_config_file="test-nginx.conf",
        skip_namespaces=["test-system"],
        include_headless_services=True,
        portal_title="Test Portal",
        refresh_interval=120,
        debug=True,
    )


@pytest.fixture
def frontend_service():
    """Create a frontend service for testing."""
    return KubernetesService(
        name="frontend-dashboard",
        namespace="default",
        service_type=ServiceType.LOAD_BALANCER,
        ports=[ServicePort(name="web", port=3000)],
        endpoints=[ServiceEndpoint(ip="10.244.1.10", port=3000)],
        endpoint_status=EndpointStatus.HEALTHY,
        is_frontend=True,
        cluster_ip="10.96.100.10",
        labels={"component": "frontend", "app": "dashboard"},
    )


@pytest.fixture
def headless_service():
    """Create a headless service for testing."""
    return KubernetesService(
        name="database-headless",
        namespace="data",
        service_type=ServiceType.CLUSTER_IP,
        ports=[ServicePort(name="mysql", port=3306)],
        endpoints=[
            ServiceEndpoint(ip="10.244.3.1", port=3306),
            ServiceEndpoint(ip="10.244.3.2", port=3306),
            ServiceEndpoint(ip="10.244.3.3", port=3306),
        ],
        endpoint_status=EndpointStatus.HEALTHY,
        cluster_ip=None,  # Headless service
        labels={"app": "mysql", "tier": "database"},
    )


@pytest.fixture
def nodeport_service():
    """Create a NodePort service for testing."""
    return KubernetesService(
        name="external-api",
        namespace="public",
        service_type=ServiceType.NODE_PORT,
        ports=[
            ServicePort(name="api", port=7070, node_port=30080),
            ServicePort(name="metrics", port=9090, node_port=30090),
        ],
        endpoints=[ServiceEndpoint(ip="10.244.4.1", port=7070)],
        endpoint_status=EndpointStatus.HEALTHY,
        cluster_ip="10.96.100.20",
        labels={"exposure": "external", "app": "api"},
    )
