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
        """Test the Kubernetes connection and verify authentication."""
        try:
            # Try to get cluster version
            if self._core_v1 is None:
                msg = "Core v1 API client not initialized"
                raise RuntimeError(msg)
            
            # Test API connectivity and authentication
            version = self._core_v1.get_api_resources()
            logger.debug(
                "Connected to Kubernetes cluster with %d core resources",
                len(version.resources),
            )
            
            # Additional test to verify we can actually read cluster data
            # This will catch authorization issues more reliably
            try:
                namespaces = self._core_v1.list_namespace(limit=1)
                logger.debug("Authentication verified - can list namespaces")
            except ApiException as auth_e:
                if auth_e.status == 401:
                    logger.error("Kubernetes API authentication failed (401 Unauthorized)")
                    logger.error("Please check your kubeconfig or service account permissions")
                    raise SystemExit(1) from auth_e
                elif auth_e.status == 403:
                    logger.error("Kubernetes API authorization failed (403 Forbidden)")
                    logger.error("Service account lacks necessary permissions to list namespaces")
                    raise SystemExit(1) from auth_e
                else:
                    # Re-raise other API exceptions
                    raise
                    
        except ApiException as e:
            if e.status == 401:
                logger.error("Kubernetes API authentication failed (401 Unauthorized)")
                logger.error("Please check your kubeconfig or service account permissions")
                raise SystemExit(1) from e
            elif e.status == 403:
                logger.error("Kubernetes API authorization failed (403 Forbidden)")
                logger.error("Service account lacks necessary permissions")
                raise SystemExit(1) from e
            else:
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

    def test_api_connectivity(self) -> None:
        """Test Kubernetes API connectivity and permissions at startup.
        
        This function performs comprehensive tests to ensure the client can:
        1. Connect to the Kubernetes API server
        2. Authenticate with the cluster  
        3. Has minimum required permissions
        
        Exits with code 1 if any critical checks fail.
        """
        logger.info("Testing Kubernetes API connectivity and permissions...")
        
        try:
            if not self._is_initialized:
                self.initialize()
            
            # Test 1: Basic API connectivity
            logger.debug("Testing basic API connectivity...")
            version = self._core_v1.get_api_resources()
            logger.debug(f"✓ Connected to Kubernetes API with {len(version.resources)} core resources")
            
            # Test 2: Authentication and basic read permissions
            logger.debug("Testing authentication and namespace access...")
            try:
                namespaces = self._core_v1.list_namespace(limit=1)
                logger.debug(f"✓ Authentication successful - can read namespaces")
            except ApiException as auth_e:
                if auth_e.status == 401:
                    logger.error("✗ Authentication failed: 401 Unauthorized")
                    logger.error("  → Check your kubeconfig file or service account token")
                    logger.error("  → Verify your cluster connection settings")
                    raise SystemExit(1) from auth_e
                elif auth_e.status == 403:
                    logger.error("✗ Authorization failed: 403 Forbidden")
                    logger.error("  → Service account lacks permission to list namespaces")
                    logger.error("  → Required RBAC: 'get' and 'list' on 'namespaces' resource")
                    raise SystemExit(1) from auth_e
                else:
                    raise
            
            # Test 3: Service discovery permissions
            logger.debug("Testing service discovery permissions...")
            try:
                services = self._core_v1.list_service_for_all_namespaces(limit=1)
                logger.debug("✓ Can list services across namespaces")
            except ApiException as svc_e:
                if svc_e.status == 403:
                    logger.error("✗ Missing service permissions: 403 Forbidden")
                    logger.error("  → Service account lacks permission to list services")
                    logger.error("  → Required RBAC: 'get' and 'list' on 'services' resource")
                    raise SystemExit(1) from svc_e
                else:
                    raise
            
            # Test 4: Endpoint discovery permissions  
            logger.debug("Testing endpoint discovery permissions...")
            try:
                endpoints = self._core_v1.list_endpoints_for_all_namespaces(limit=1)
                logger.debug("✓ Can list endpoints across namespaces")
            except ApiException as ep_e:
                if ep_e.status == 403:
                    logger.warning("⚠ Missing endpoint permissions: 403 Forbidden")
                    logger.warning("  → Endpoint status detection will be limited")
                    logger.warning("  → Recommended RBAC: 'get' and 'list' on 'endpoints' resource")
                    # Don't exit for endpoints - it's not critical
                else:
                    raise
                    
            logger.info("✓ Kubernetes API connectivity test completed successfully")
            
        except SystemExit:
            # Re-raise SystemExit to preserve exit code
            raise
        except Exception as e:
            logger.error(f"✗ Kubernetes API connectivity test failed: {e}")
            logger.error("  → Check your cluster connection and authentication")
            raise SystemExit(1) from e

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
