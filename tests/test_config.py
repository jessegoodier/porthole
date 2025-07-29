"""Tests for porthole configuration."""

import os
import tempfile
from pathlib import Path

import pytest

from porthole.config import Config


class TestConfig:
    """Test Config model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.kubeconfig_path is None
        assert config.output_dir == Path("./generated-output")
        assert config.service_json_file == "services.json"
        assert config.portal_html_file == "portal.html"
        assert config.nginx_config_file == "services.conf"
        assert config.locations_config_file == "locations.conf"
        assert config.include_headless_services is False
        assert config.portal_title == "Kubernetes Services Portal"
        assert config.refresh_interval == 300
        assert config.debug is False

    def test_custom_config(self):
        """Test custom configuration values."""
        config = Config(
            kubeconfig_path="/custom/kubeconfig",
            output_dir=Path("/custom/output"),
            service_json_file="custom.json",
            portal_html_file="custom.html",
            nginx_config_file="custom.conf",
            locations_config_file="custom-locations.conf",
            skip_namespaces=["custom-system"],
            include_headless_services=True,
            portal_title="Custom Portal",
            refresh_interval=600,
            debug=True,
        )

        assert config.kubeconfig_path == "/custom/kubeconfig"
        assert config.output_dir == Path("/custom/output")
        assert config.service_json_file == "custom.json"
        assert config.portal_html_file == "custom.html"
        assert config.nginx_config_file == "custom.conf"
        assert config.locations_config_file == "custom-locations.conf"
        assert config.skip_namespaces == ["custom-system"]
        assert config.include_headless_services is True
        assert config.portal_title == "Custom Portal"
        assert config.refresh_interval == 600
        assert config.debug is True

    def test_skip_namespaces_default(self):
        """Test default skip namespaces list."""
        config = Config()

        # Check that common system namespaces are included
        assert "kube-system" in config.skip_namespaces
        assert "kube-public" in config.skip_namespaces
        assert "kube-node-lease" in config.skip_namespaces
        assert "cert-manager" in config.skip_namespaces
        assert "istio-system" in config.skip_namespaces

    def test_from_env_defaults(self, monkeypatch):
        """Test creating config from environment with defaults."""
        # Clear any existing environment variables
        env_vars = [
            "KUBECONFIG",
            "OUTPUT_DIR",
            "SERVICE_JSON_FILE",
            "PORTAL_HTML_FILE",
            "NGINX_CONFIG_FILE",
            "LOCATIONS_CONFIG_FILE",
            "SKIP_NAMESPACES",
            "INCLUDE_HEADLESS_SERVICES",
            "PORTAL_TITLE",
            "REFRESH_INTERVAL",
            "DEBUG",
        ]
        for var in env_vars:
            monkeypatch.delenv(var, raising=False)

        config = Config.from_env()

        assert config.kubeconfig_path is None
        assert config.output_dir == Path("./generated-output")
        assert config.debug is False

    def test_from_env_custom(self, monkeypatch):
        """Test creating config from custom environment variables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monkeypatch.setenv("KUBECONFIG", "/custom/kubeconfig")
            monkeypatch.setenv("OUTPUT_DIR", temp_dir)
            monkeypatch.setenv("SERVICE_JSON_FILE", "custom-services.json")
            monkeypatch.setenv("PORTAL_HTML_FILE", "custom-portal.html")
            monkeypatch.setenv("NGINX_CONFIG_FILE", "custom-nginx.conf")
            monkeypatch.setenv("LOCATIONS_CONFIG_FILE", "custom-locations.conf")
            monkeypatch.setenv("SKIP_NAMESPACES", "ns1,ns2,ns3")
            monkeypatch.setenv("INCLUDE_HEADLESS_SERVICES", "true")
            monkeypatch.setenv("PORTAL_TITLE", "Custom K8s Portal")
            monkeypatch.setenv("REFRESH_INTERVAL", "180")
            monkeypatch.setenv("DEBUG", "true")

            config = Config.from_env()

            assert config.kubeconfig_path == "/custom/kubeconfig"
            assert config.output_dir == Path(temp_dir)
            assert config.service_json_file == "custom-services.json"
            assert config.portal_html_file == "custom-portal.html"
            assert config.nginx_config_file == "custom-nginx.conf"
            assert config.locations_config_file == "custom-locations.conf"
            assert config.skip_namespaces == ["ns1", "ns2", "ns3"]
            assert config.include_headless_services is True
            assert config.portal_title == "Custom K8s Portal"
            assert config.refresh_interval == 180
            assert config.debug is True

    def test_from_env_empty_skip_namespaces(self, monkeypatch):
        """Test handling empty SKIP_NAMESPACES environment variable."""
        monkeypatch.setenv("SKIP_NAMESPACES", "")

        config = Config.from_env()

        # Should use default list when empty
        assert "kube-system" in config.skip_namespaces
        assert "kube-public" in config.skip_namespaces

    def test_from_env_boolean_parsing(self, monkeypatch):
        """Test boolean environment variable parsing."""
        # Test various boolean representations
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("1", False),  # Only "true" (case-insensitive) should be True
            ("0", False),
            ("yes", False),
            ("no", False),
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("DEBUG", env_value)
            monkeypatch.setenv("INCLUDE_HEADLESS_SERVICES", env_value)

            config = Config.from_env()

            assert config.debug is expected, f"DEBUG={env_value} should be {expected}"
            assert config.include_headless_services is expected, (
                f"INCLUDE_HEADLESS_SERVICES={env_value} should be {expected}"
            )

    def test_from_env_integer_parsing(self, monkeypatch):
        """Test integer environment variable parsing."""
        monkeypatch.setenv("REFRESH_INTERVAL", "450")

        config = Config.from_env()

        assert config.refresh_interval == 450

    def test_from_env_invalid_integer(self, monkeypatch):
        """Test handling invalid integer values."""
        monkeypatch.setenv("REFRESH_INTERVAL", "invalid")

        with pytest.raises(ValueError):
            Config.from_env()

    def test_path_handling(self):
        """Test Path object handling."""
        config = Config(output_dir=Path("/tmp/test"))

        assert isinstance(config.output_dir, Path)
        assert str(config.output_dir) == "/tmp/test"

    def test_skip_namespaces_immutable(self):
        """Test that skip_namespaces list is properly handled."""
        config = Config(skip_namespaces=["test1", "test2"])

        # Should be able to access the list
        assert "test1" in config.skip_namespaces
        assert "test2" in config.skip_namespaces
        assert len(config.skip_namespaces) == 2


if __name__ == "__main__":
    pytest.main([__file__])
