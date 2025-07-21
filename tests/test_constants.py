"""Tests for porthole constants."""

import pytest

from porthole import constants


class TestConstants:
    """Test constants module."""

    def test_http_status_codes(self):
        """Test HTTP status code constants."""
        assert constants.HTTP_NOT_FOUND == 404

    def test_default_values(self):
        """Test default value constants."""
        assert constants.DEFAULT_REFRESH_INTERVAL == 300
        assert constants.DEFAULT_OUTPUT_DIR == "./output"
        assert constants.DEFAULT_HEALTH_CHECK_TIMEOUT == 5

    def test_port_limits(self):
        """Test port limit constants."""
        assert constants.MIN_PORT == 1
        assert constants.MAX_PORT == 65535
        assert constants.MIN_PORT < constants.MAX_PORT

    def test_service_types(self):
        """Test service type constants."""
        assert constants.SERVICE_TYPE_CLUSTERIP == "ClusterIP"
        assert constants.SERVICE_TYPE_NODEPORT == "NodePort"
        assert constants.SERVICE_TYPE_LOADBALANCER == "LoadBalancer"

    def test_endpoint_status(self):
        """Test endpoint status constants."""
        assert constants.ENDPOINT_STATUS_HEALTHY == "healthy"
        assert constants.ENDPOINT_STATUS_UNHEALTHY == "unhealthy"
        assert constants.ENDPOINT_STATUS_UNKNOWN == "unknown"

    def test_frontend_keywords(self):
        """Test frontend detection keywords."""
        assert "frontend" in constants.FRONTEND_KEYWORDS
        assert "ui" in constants.FRONTEND_KEYWORDS
        assert "web" in constants.FRONTEND_KEYWORDS
        assert "portal" in constants.FRONTEND_KEYWORDS
        assert "dashboard" in constants.FRONTEND_KEYWORDS

    def test_default_skip_namespaces(self):
        """Test default skip namespaces."""
        expected_namespaces = [
            "kube-system",
            "kube-public",
            "kube-node-lease",
            "kubernetes-dashboard",
            "cert-manager",
            "istio-system",
            "linkerd",
            "linkerd-viz",
        ]

        for namespace in expected_namespaces:
            assert namespace in constants.DEFAULT_SKIP_NAMESPACES

    def test_constants_have_expected_values(self):
        """Test that constants have expected values."""
        # Test that constants have the right types and values
        assert isinstance(constants.HTTP_NOT_FOUND, int)
        assert isinstance(constants.MIN_PORT, int)
        assert isinstance(constants.MAX_PORT, int)
        assert isinstance(constants.DEFAULT_REFRESH_INTERVAL, int)
        assert isinstance(constants.SERVICE_TYPE_CLUSTERIP, str)
        assert isinstance(constants.FRONTEND_KEYWORDS, list)
        assert isinstance(constants.DEFAULT_SKIP_NAMESPACES, list)

        # Test value ranges make sense
        assert constants.MIN_PORT > 0
        assert constants.MAX_PORT > constants.MIN_PORT
        assert constants.DEFAULT_REFRESH_INTERVAL > 0


if __name__ == "__main__":
    pytest.main([__file__])
