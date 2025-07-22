"""Kubernetes client management with auto-detection of environment."""

import logging
import os
from pathlib import Path
from typing import Any, Optional

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .config import Config
from .config import config as default_config
from .constants import HTTP_NOT_FOUND

logger = logging.getLogger(__name__)
if logger.level == logging.TRACE:
    logging.getLogger("kubernetes.client.rest").setLevel(logging.DEBUG)
else:
    logging.getLogger("kubernetes.client.rest").setLevel(logging.ERROR)


def _raise_config_error() -> None:
    """Raise a configuration error for Kubernetes client initialization."""
    msg = "Unable to initialize Kubernetes client: no valid configuration found"
    raise RuntimeError(msg)


class KubernetesClient:
    """Manages Kubernetes client with auto-detection of environment."""

    def __init__(self, config_obj: Config) -> None:
        """Initialize Kubernetes client.

        Args:
            config_obj: Configuration object
        """
        self.config = config_obj
        self._core_v1: client.CoreV1Api | None = None
        self._apps_v1: client.AppsV1Api | None = None
        self._discovery_v1: client.DiscoveryV1Api | None = None
        self._is_initialized = False

    def initialize(self) -> None:
        """Initialize the Kubernetes client with appropriate configuration."""
        if self._is_initialized:
            return

        try:
            # First try to load in-cluster configuration
            if self._try_in_cluster_config():
                logger.info("Using in-cluster Kubernetes configuration")
            elif self._try_kubeconfig():
                logger.info("Using kubeconfig file for Kubernetes configuration")
            else:
                _raise_config_error()

            # Initialize API clients
            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._discovery_v1 = client.DiscoveryV1Api()

            # Test the connection
            self._test_connection()

            self._is_initialized = True
            logger.info("Kubernetes client initialized successfully")

        except Exception:
            logger.exception("Failed to initialize Kubernetes client")
            raise

    def _try_in_cluster_config(self) -> bool:
        """Try to load in-cluster configuration.

        Returns:
            True if in-cluster config was loaded successfully
        """
        try:
            config.load_incluster_config()
        except config.ConfigException:
            logger.debug("In-cluster configuration not available")
            return False
        else:
            return True

    def _try_kubeconfig(self) -> bool:
        """Try to load kubeconfig file.

        Returns:
            True if kubeconfig was loaded successfully
        """
        try:
            # Try explicit kubeconfig path from config
            if self.config.kubeconfig_path:
                kubeconfig_path = Path(self.config.kubeconfig_path)
                if kubeconfig_path.exists():
                    config.load_kube_config(config_file=str(kubeconfig_path))
                    logger.info("Loaded kubeconfig from %s", kubeconfig_path)
                    return True
                logger.warning("Kubeconfig file not found: %s", kubeconfig_path)

            # Try default kubeconfig locations
            default_paths = [
                Path.home() / ".kube" / "config",
                Path(os.getenv("KUBECONFIG", "")),
            ]

            for path in default_paths:
                if path and path.exists():
                    config.load_kube_config(config_file=str(path))
                    logger.info("Loaded kubeconfig from %s", path)
                    return True

            # Try loading default kubeconfig without explicit path
            config.load_kube_config()
            logger.info("Loaded kubeconfig from default location")

        except (config.ConfigException, FileNotFoundError):
            logger.debug("Failed to load kubeconfig")
            return False
        else:
            return True

    def _test_connection(self) -> None:
        """Test the Kubernetes connection."""
        try:
            # Try to get cluster version
            if self._core_v1 is None:
                msg = "Core v1 API client not initialized"
                raise RuntimeError(msg)
            version = self._core_v1.get_api_resources()
            logger.debug(
                "Connected to Kubernetes cluster with %d core resources",
                len(version.resources),
            )
        except ApiException:
            logger.exception("Failed to connect to Kubernetes cluster")
            raise

    @property
    def core_v1(self) -> client.CoreV1Api:
        """Get CoreV1Api client."""
        if not self._is_initialized:
            self.initialize()
        return self._core_v1

    @property
    def apps_v1(self) -> client.AppsV1Api:
        """Get AppsV1Api client."""
        if not self._is_initialized:
            self.initialize()
        return self._apps_v1

    @property
    def discovery_v1(self) -> client.DiscoveryV1Api:
        """Get DiscoveryV1Api client."""
        if not self._is_initialized:
            self.initialize()
        return self._discovery_v1

    def get_cluster_info(self) -> dict[str, Any]:
        """Get basic cluster information.

        Returns:
            Dictionary with cluster information
        """
        if not self._is_initialized:
            self.initialize()

        try:
            # Get cluster version
            version_info = self.core_v1.get_api_resources()

            # Get node count
            nodes = self.core_v1.list_node()
            node_count = len(nodes.items)

            # Get namespace count
            namespaces = self.core_v1.list_namespace()
            namespace_count = len(namespaces.items)

            return {
                "api_resources": len(version_info.resources),
                "node_count": node_count,
                "namespace_count": namespace_count,
                "cluster_ready": True,
            }

        except ApiException as e:
            logger.exception("Failed to get cluster info")
            return {
                "error": str(e),
                "cluster_ready": False,
            }


def get_kubernetes_client(config_obj: Config | None = None) -> KubernetesClient:
    """Get a configured Kubernetes client.

    Args:
        config_obj: Optional configuration object

    Returns:
        Configured KubernetesClient instance
    """
    if config_obj is None:
        config_obj = default_config

    client_instance = KubernetesClient(config_obj)
    client_instance.initialize()
    return client_instance
