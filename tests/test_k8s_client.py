"""Tests for Kubernetes client functionality."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from kubernetes.client.rest import ApiException

from porthole.config import Config
from porthole.k8s_client import KubernetesClient, _raise_config_error, get_kubernetes_client


class TestKubernetesClient:
    """Test KubernetesClient class."""

    def test_init(self):
        """Test client initialization."""
        config = Config()
        client = KubernetesClient(config)

        assert client.config == config
        assert client._core_v1 is None
        assert client._apps_v1 is None
        assert client._discovery_v1 is None
        assert client._is_initialized is False

    @patch("porthole.k8s_client.KubernetesClient._try_in_cluster_config")
    @patch("porthole.k8s_client.KubernetesClient._try_kubeconfig")
    @patch("porthole.k8s_client.KubernetesClient._test_connection")
    @patch("porthole.k8s_client.client")
    def test_initialize_in_cluster(self, mock_client, mock_test, mock_kubeconfig, mock_in_cluster):
        """Test initialization with in-cluster config."""
        # Setup mocks
        mock_in_cluster.return_value = True
        mock_kubeconfig.return_value = False
        mock_client.CoreV1Api.return_value = Mock()
        mock_client.AppsV1Api.return_value = Mock()
        mock_client.DiscoveryV1Api.return_value = Mock()

        config = Config()
        client = KubernetesClient(config)
        client.initialize()

        assert client._is_initialized is True
        mock_in_cluster.assert_called_once()
        mock_kubeconfig.assert_not_called()
        mock_test.assert_called_once()

    @patch("porthole.k8s_client.KubernetesClient._try_in_cluster_config")
    @patch("porthole.k8s_client.KubernetesClient._try_kubeconfig")
    @patch("porthole.k8s_client.KubernetesClient._test_connection")
    @patch("porthole.k8s_client.client")
    def test_initialize_kubeconfig(self, mock_client, mock_test, mock_kubeconfig, mock_in_cluster):
        """Test initialization with kubeconfig."""
        # Setup mocks
        mock_in_cluster.return_value = False
        mock_kubeconfig.return_value = True
        mock_client.CoreV1Api.return_value = Mock()
        mock_client.AppsV1Api.return_value = Mock()
        mock_client.DiscoveryV1Api.return_value = Mock()

        config = Config()
        client = KubernetesClient(config)
        client.initialize()

        assert client._is_initialized is True
        mock_in_cluster.assert_called_once()
        mock_kubeconfig.assert_called_once()
        mock_test.assert_called_once()

    @patch("porthole.k8s_client.KubernetesClient._try_in_cluster_config")
    @patch("porthole.k8s_client.KubernetesClient._try_kubeconfig")
    def test_initialize_no_config(self, mock_kubeconfig, mock_in_cluster):
        """Test initialization failure when no config available."""
        # Setup mocks
        mock_in_cluster.return_value = False
        mock_kubeconfig.return_value = False

        config = Config()
        client = KubernetesClient(config)

        with pytest.raises(RuntimeError) as exc_info:
            client.initialize()

        assert "Unable to initialize Kubernetes client" in str(exc_info.value)

    @patch("porthole.k8s_client.config")
    def test_try_in_cluster_config_success(self, mock_config):
        """Test successful in-cluster config loading."""
        config = Config()
        client = KubernetesClient(config)

        result = client._try_in_cluster_config()

        assert result is True
        mock_config.load_incluster_config.assert_called_once()


    @patch("porthole.k8s_client.config")
    @patch("porthole.k8s_client.Path")
    def test_try_kubeconfig_explicit_path(self, mock_path, mock_config):
        """Test kubeconfig loading with explicit path."""
        # Setup mocks
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        config = Config(kubeconfig_path="/custom/kubeconfig")
        client = KubernetesClient(config)

        result = client._try_kubeconfig()

        assert result is True
        mock_config.load_kube_config.assert_called()

    @patch("porthole.k8s_client.config")
    @patch("porthole.k8s_client.Path")
    def test_try_kubeconfig_default_paths(self, mock_path, mock_config):
        """Test kubeconfig loading with default paths."""
        # Setup mocks - first path doesn't exist, second does
        path_instances = [Mock(), Mock()]
        path_instances[0].exists.return_value = False
        path_instances[1].exists.return_value = True
        mock_path.side_effect = path_instances

        config = Config()
        client = KubernetesClient(config)

        with patch("porthole.k8s_client.os.getenv", return_value="/env/kubeconfig"):
            result = client._try_kubeconfig()

        assert result is True


    def test_test_connection_success(self):
        """Test successful connection test."""
        config = Config()
        client = KubernetesClient(config)

        # Mock the core_v1 client
        mock_core_v1 = Mock()
        mock_resources = Mock()
        mock_resources.resources = ["services", "pods", "nodes"]
        mock_core_v1.get_api_resources.return_value = mock_resources
        client._core_v1 = mock_core_v1

        # Should not raise an exception
        client._test_connection()

    def test_test_connection_failure(self):
        """Test connection test failure."""
        config = Config()
        client = KubernetesClient(config)

        # Mock the core_v1 client to raise an exception
        mock_core_v1 = Mock()
        mock_core_v1.get_api_resources.side_effect = ApiException(status=401, reason="Unauthorized")
        client._core_v1 = mock_core_v1

        with pytest.raises(ApiException):
            client._test_connection()

    def test_test_connection_no_client(self):
        """Test connection test with no client initialized."""
        config = Config()
        client = KubernetesClient(config)
        # _core_v1 is None by default

        with pytest.raises(RuntimeError) as exc_info:
            client._test_connection()

        assert "Core v1 API client not initialized" in str(exc_info.value)


    def test_get_cluster_info_success(self):
        """Test successful cluster info retrieval."""
        config = Config()
        client = KubernetesClient(config)

        # Mock initialized client
        client._is_initialized = True
        mock_core_v1 = Mock()

        # Mock API responses
        mock_resources = Mock()
        mock_resources.resources = ["services", "pods"]
        mock_core_v1.get_api_resources.return_value = mock_resources

        mock_nodes = Mock()
        mock_nodes.items = [Mock(), Mock()]  # 2 nodes
        mock_core_v1.list_node.return_value = mock_nodes

        mock_namespaces = Mock()
        mock_namespaces.items = [Mock(), Mock(), Mock()]  # 3 namespaces
        mock_core_v1.list_namespace.return_value = mock_namespaces

        client._core_v1 = mock_core_v1

        info = client.get_cluster_info()

        assert info["api_resources"] == 2
        assert info["node_count"] == 2
        assert info["namespace_count"] == 3
        assert info["cluster_ready"] is True

    def test_get_cluster_info_failure(self):
        """Test cluster info retrieval failure."""
        config = Config()
        client = KubernetesClient(config)

        # Mock initialized client
        client._is_initialized = True
        mock_core_v1 = Mock()
        mock_core_v1.get_api_resources.side_effect = ApiException(status=403, reason="Forbidden")
        client._core_v1 = mock_core_v1

        info = client.get_cluster_info()

        assert "error" in info
        assert info["cluster_ready"] is False


class TestHelperFunctions:
    """Test helper functions."""

    def test_raise_config_error(self):
        """Test config error helper function."""
        with pytest.raises(RuntimeError) as exc_info:
            _raise_config_error()

        assert "Unable to initialize Kubernetes client" in str(exc_info.value)

    @patch("porthole.k8s_client.KubernetesClient")
    def test_get_kubernetes_client_with_config(self, mock_client_class):
        """Test getting kubernetes client with config."""
        config = Config()
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        result = get_kubernetes_client(config)

        mock_client_class.assert_called_once_with(config)
        mock_instance.initialize.assert_called_once()
        assert result == mock_instance

    @patch("porthole.k8s_client.KubernetesClient")
    @patch("porthole.k8s_client.default_config")
    def test_get_kubernetes_client_without_config(self, mock_default_config, mock_client_class):
        """Test getting kubernetes client without config."""
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        result = get_kubernetes_client()

        mock_client_class.assert_called_once_with(mock_default_config)
        mock_instance.initialize.assert_called_once()
        assert result == mock_instance


if __name__ == "__main__":
    pytest.main([__file__])
