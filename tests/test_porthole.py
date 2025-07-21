"""Tests for the main porthole CLI application."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from porthole.config import Config
from porthole.models import (
    EndpointStatus,
    KubernetesService,
    ServiceDiscoveryResult,
    ServiceEndpoint,
    ServicePort,
    ServiceType,
)
from porthole.porthole import _display_discovery_result, cli


class TestCLI:
    """Test the main CLI interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Kubernetes Service Proxy" in result.output
        assert "discover" in result.output
        assert "generate" in result.output
        assert "watch" in result.output
        assert "info" in result.output

    def test_cli_debug_flag(self):
        """Test debug flag functionality."""
        runner = CliRunner()
        with patch("porthole.porthole.setup_logging") as mock_setup:
            result = runner.invoke(cli, ["--debug", "info"])

            # Should call setup_logging with debug=True
            mock_setup.assert_called_with(True)

    @patch("porthole.porthole.get_kubernetes_client")
    @patch("porthole.porthole.ServiceDiscovery")
    def test_discover_command_json(self, mock_discovery_class, mock_get_client):
        """Test discover command with JSON output."""
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_discovery = Mock()
        mock_discovery_class.return_value = mock_discovery

        # Create test result
        services = [
            KubernetesService(
                name="webapp",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[ServiceEndpoint(ip="10.244.1.5", port=80)],
                endpoint_status=EndpointStatus.HEALTHY,
            ),
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default"],
            namespaces_skipped=["kube-system"],
        )

        mock_discovery.discover_services.return_value = result

        runner = CliRunner()
        cli_result = runner.invoke(cli, ["discover", "--format", "json"])

        assert cli_result.exit_code == 0
        assert "total_services" in cli_result.output
        assert "healthy_services" in cli_result.output
        assert "webapp" in cli_result.output

    @patch("porthole.porthole.get_kubernetes_client")
    @patch("porthole.porthole.ServiceDiscovery")
    def test_discover_command_table(self, mock_discovery_class, mock_get_client):
        """Test discover command with table output."""
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_discovery = Mock()
        mock_discovery_class.return_value = mock_discovery

        services = [
            KubernetesService(
                name="webapp",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[ServiceEndpoint(ip="10.244.1.5", port=80)],
                endpoint_status=EndpointStatus.HEALTHY,
            ),
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default"],
            namespaces_skipped=[],
        )

        mock_discovery.discover_services.return_value = result

        runner = CliRunner()
        cli_result = runner.invoke(cli, ["discover", "--format", "table"])

        assert cli_result.exit_code == 0
        assert "webapp" in cli_result.output
        assert "default" in cli_result.output

    @patch("porthole.porthole.get_kubernetes_client")
    @patch("porthole.porthole.ServiceDiscovery")
    @patch("porthole.porthole.PortalGenerator")
    @patch("porthole.porthole.NginxGenerator")
    def test_generate_command(self, mock_nginx_gen_class, mock_portal_gen_class,
                             mock_discovery_class, mock_get_client):
        """Test generate command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup mocks
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery

            mock_portal_gen = Mock()
            mock_portal_gen_class.return_value = mock_portal_gen
            mock_portal_gen.generate_json_data.return_value = f"{temp_dir}/services.json"
            mock_portal_gen.generate_portal.return_value = f"{temp_dir}/portal.html"
            mock_portal_gen.generate_table.return_value = f"{temp_dir}/table.html"

            mock_nginx_gen = Mock()
            mock_nginx_gen_class.return_value = mock_nginx_gen
            mock_nginx_gen.generate_nginx_config.return_value = f"{temp_dir}/nginx.conf"
            mock_nginx_gen.validate_nginx_config.return_value = True

            result = ServiceDiscoveryResult(
                services=[],
                namespaces_scanned=[],
                namespaces_skipped=[],
            )
            mock_discovery.discover_services.return_value = result

            runner = CliRunner()
            cli_result = runner.invoke(cli, ["generate", "--output-dir", temp_dir])

            assert cli_result.exit_code == 0
            assert "Generated 4 files:" in cli_result.output

            # Verify generators were called
            mock_portal_gen.generate_json_data.assert_called_once()
            mock_portal_gen.generate_portal.assert_called_once()
            mock_portal_gen.generate_table.assert_called_once()
            mock_nginx_gen.generate_nginx_config.assert_called_once()

    @patch("porthole.porthole.get_kubernetes_client")
    @patch("porthole.porthole.ServiceDiscovery")
    @patch("porthole.porthole.PortalGenerator")
    def test_generate_command_selective(self, mock_portal_gen_class,
                                       mock_discovery_class, mock_get_client):
        """Test generate command with selective output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup mocks
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_discovery = Mock()
            mock_discovery_class.return_value = mock_discovery

            mock_portal_gen = Mock()
            mock_portal_gen_class.return_value = mock_portal_gen
            mock_portal_gen.generate_json_data.return_value = f"{temp_dir}/services.json"

            result = ServiceDiscoveryResult(
                services=[],
                namespaces_scanned=[],
                namespaces_skipped=[],
            )
            mock_discovery.discover_services.return_value = result

            runner = CliRunner()
            cli_result = runner.invoke(cli, [
                "generate",
                "--output-dir", temp_dir,
                "--no-portal",
                "--no-nginx",
            ])

            assert cli_result.exit_code == 0
            assert "Generated 1 files:" in cli_result.output

            # Only JSON should be generated
            mock_portal_gen.generate_json_data.assert_called_once()

    @patch("porthole.porthole.get_kubernetes_client")
    def test_info_command(self, mock_get_client):
        """Test info command."""
        # Setup mock
        mock_client = Mock()
        mock_client.get_cluster_info.return_value = {
            "node_count": 3,
            "namespace_count": 5,
            "api_resources": 150,
            "cluster_ready": True,
        }
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        cli_result = runner.invoke(cli, ["info"])

        assert cli_result.exit_code == 0
        assert "Cluster Information:" in cli_result.output
        assert "Nodes: 3" in cli_result.output
        assert "Namespaces: 5" in cli_result.output
        assert "Configuration:" in cli_result.output

    @patch("porthole.porthole.get_kubernetes_client")
    def test_command_failure_handling(self, mock_get_client):
        """Test error handling in commands."""
        # Setup mock to raise exception
        mock_get_client.side_effect = Exception("Connection failed")

        runner = CliRunner()
        cli_result = runner.invoke(cli, ["info"])

        assert cli_result.exit_code == 1



class TestDisplayDiscoveryResult:
    """Test the _display_discovery_result function."""

    def test_display_json_format(self):
        """Test JSON format display."""
        services = [
            KubernetesService(
                name="webapp",
                namespace="default",
                service_type=ServiceType.CLUSTER_IP,
                ports=[ServicePort(port=80)],
                endpoints=[ServiceEndpoint(ip="10.244.1.5", port=80)],
                endpoint_status=EndpointStatus.HEALTHY,
            ),
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default"],
            namespaces_skipped=["kube-system"],
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Capture output
            import sys
            from io import StringIO

            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            try:
                _display_discovery_result(result, "json")
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout

            import json
            data = json.loads(output)

            assert data["total_services"] == 1
            assert data["healthy_services"] == 1
            assert len(data["services"]) == 1
            assert data["services"][0]["name"] == "webapp"

    def test_display_table_format(self):
        """Test table format display."""
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
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default"],
            namespaces_skipped=[],
        )

        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            _display_discovery_result(result, "table")
            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "webapp" in output
        assert "default" in output
        assert "ClusterIP" in output

    def test_display_text_format(self):
        """Test text format display."""
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
        ]

        result = ServiceDiscoveryResult(
            services=services,
            namespaces_scanned=["default"],
            namespaces_skipped=[],
        )

        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            _display_discovery_result(result, "text")
            output = captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "Total Services: 1" in output
        assert "Healthy: 1" in output
        assert "Frontend: 1" in output


if __name__ == "__main__":
    pytest.main([__file__])
