"""Service discovery logic for Kubernetes services."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from kubernetes.client.rest import ApiException

from .config import Config
from .k8s_client import KubernetesClient
from .models import (
    EndpointStatus,
    KubernetesService,
    ServiceDiscoveryResult,
    ServiceEndpoint,
    ServicePort,
    ServiceType,
)

logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """Handles discovery of Kubernetes services."""

    def __init__(self, k8s_client: KubernetesClient, config: Config):
        """Initialize service discovery.

        Args:
            k8s_client: Kubernetes client instance
            config: Configuration object
        """
        self.k8s_client = k8s_client
        self.config = config

    def discover_services(self) -> ServiceDiscoveryResult:
        """Discover all services in the cluster.

        Returns:
            ServiceDiscoveryResult with discovered services
        """
        logger.info("Starting service discovery")

        # Get all namespaces
        namespaces = self._get_namespaces()
        namespaces_to_scan = self._filter_namespaces(namespaces)

        # Discover services in each namespace
        all_services = []
        scanned_namespaces = []

        for namespace in namespaces_to_scan:
            try:
                logger.debug(f"Discovering services in namespace: {namespace}")
                services = self._discover_services_in_namespace(namespace)
                all_services.extend(services)
                scanned_namespaces.append(namespace)
            except Exception as e:
                logger.error(f"Failed to discover services in namespace {namespace}: {e}")
                continue

        # Calculate statistics
        skipped_namespaces = [ns for ns in namespaces if ns not in scanned_namespaces]

        result = ServiceDiscoveryResult(
            services=all_services,
            namespaces_scanned=scanned_namespaces,
            namespaces_skipped=skipped_namespaces,
            discovery_time=datetime.now(),
        )

        logger.info(
            f"Service discovery completed: {result.total_services} services found "
            f"in {len(scanned_namespaces)} namespaces",
        )

        return result

    def _get_namespaces(self) -> list[str]:
        """Get all namespaces in the cluster.

        Returns:
            List of namespace names
        """
        try:
            namespaces = self.k8s_client.core_v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as e:
            logger.error(f"Failed to get namespaces: {e}")
            return []

    def _filter_namespaces(self, namespaces: list[str]) -> list[str]:
        """Filter namespaces based on skip list.

        Args:
            namespaces: List of all namespaces

        Returns:
            List of namespaces to scan
        """
        skip_set = set(self.config.skip_namespaces)
        filtered = [ns for ns in namespaces if ns not in skip_set]

        logger.debug(
            f"Filtered {len(namespaces)} namespaces to {len(filtered)} (skipped: {len(skip_set)})",
        )

        return filtered

    def _discover_services_in_namespace(self, namespace: str) -> list[KubernetesService]:
        """Discover services in a specific namespace.

        Args:
            namespace: Namespace name

        Returns:
            List of discovered services
        """
        try:
            services = self.k8s_client.core_v1.list_namespaced_service(namespace)
            discovered_services = []

            for service in services.items:
                try:
                    k8s_service = self._convert_service(service)

                    # Skip headless services if not configured to include them
                    if k8s_service.is_headless and not self.config.include_headless_services:
                        logger.debug(f"Skipping headless service: {k8s_service.display_name}")
                        continue

                    # Get endpoints for the service
                    endpoints = self._get_service_endpoints(service)
                    k8s_service.endpoints = endpoints
                    k8s_service.endpoint_status = self._determine_endpoint_status(endpoints)

                    discovered_services.append(k8s_service)

                except Exception as e:
                    logger.error(f"Failed to process service {service.metadata.name}: {e}")
                    continue

            return discovered_services

        except ApiException as e:
            logger.error(f"Failed to list services in namespace {namespace}: {e}")
            return []

    def _convert_service(self, service: Any) -> KubernetesService:
        """Convert Kubernetes service object to our model.

        Args:
            service: Kubernetes service object

        Returns:
            KubernetesService instance
        """
        # Extract service ports
        ports = []
        if service.spec.ports:
            for port in service.spec.ports:
                service_port = ServicePort(
                    name=port.name,
                    port=port.port,
                    target_port=str(port.target_port) if port.target_port else None,
                    protocol=port.protocol or "TCP",
                    node_port=port.node_port,
                )
                ports.append(service_port)

        # Extract service type
        service_type = ServiceType(service.spec.type or "ClusterIP")

        # Extract external IPs
        external_ips = service.spec.external_i_ps or []

        # Extract labels and annotations
        labels = service.metadata.labels or {}
        annotations = service.metadata.annotations or {}

        # Extract selector
        selector = service.spec.selector or {}

        return KubernetesService(
            name=service.metadata.name,
            namespace=service.metadata.namespace,
            service_type=service_type,
            cluster_ip=service.spec.cluster_ip,
            external_ips=external_ips,
            ports=ports,
            labels=labels,
            annotations=annotations,
            selector=selector,
            created_at=service.metadata.creation_timestamp,
            is_frontend=None,  # Let validator determine based on name/labels
        )

    def _get_service_endpoints(self, service: Any) -> list[ServiceEndpoint]:
        """Get endpoints for a service supporting both k8s 1.32 and 1.33.

        Args:
            service: Kubernetes service object

        Returns:
            List of service endpoints
        """
        endpoints = []

        # Try EndpointSlice API first (k8s 1.33+)
        try:
            endpoints.extend(self._get_endpoint_slices(service))
        except Exception as e:
            logger.debug(f"Failed to get endpoint slices for {service.metadata.name}: {e}")

        # Fallback to Endpoints API (k8s 1.32 and earlier)
        if not endpoints:
            try:
                endpoints.extend(self._get_endpoints_legacy(service))
            except Exception as e:
                logger.debug(f"Failed to get endpoints for {service.metadata.name}: {e}")

        return endpoints

    def _get_endpoint_slices(self, service: Any) -> list[ServiceEndpoint]:
        """Get endpoints using EndpointSlice API (k8s 1.33+).

        Args:
            service: Kubernetes service object

        Returns:
            List of service endpoints
        """
        endpoints = []

        try:
            # Get endpoint slices for the service
            label_selector = f"kubernetes.io/service-name={service.metadata.name}"
            endpoint_slices = self.k8s_client.discovery_v1.list_namespaced_endpoint_slice(
                namespace=service.metadata.namespace,
                label_selector=label_selector,
            )

            for slice_obj in endpoint_slices.items:
                if not slice_obj.endpoints:
                    continue

                for endpoint in slice_obj.endpoints:
                    if not endpoint.addresses:
                        continue

                    # Get endpoint readiness
                    ready = endpoint.conditions.ready if endpoint.conditions else True

                    # Get hostname
                    hostname = endpoint.hostname

                    # Add endpoint for each address and port
                    for address in endpoint.addresses:
                        if slice_obj.ports:
                            for port in slice_obj.ports:
                                endpoints.append(
                                    ServiceEndpoint(
                                        ip=address,
                                        port=port.port,
                                        ready=ready,
                                        hostname=hostname,
                                    ),
                                )
                        else:
                            # If no ports defined, use service ports
                            for service_port in service.spec.ports or []:
                                endpoints.append(
                                    ServiceEndpoint(
                                        ip=address,
                                        port=service_port.port,
                                        ready=ready,
                                        hostname=hostname,
                                    ),
                                )

        except ApiException as e:
            if e.status == 404:
                logger.debug("EndpointSlice API not available, falling back to Endpoints API")
            else:
                logger.error(f"Failed to get endpoint slices: {e}")
            raise

        return endpoints

    def _get_endpoints_legacy(self, service: Any) -> list[ServiceEndpoint]:
        """Get endpoints using legacy Endpoints API (k8s 1.32 and earlier).

        Args:
            service: Kubernetes service object

        Returns:
            List of service endpoints
        """
        endpoints: list[ServiceEndpoint] = []

        try:
            # Get endpoints for the service
            endpoint_obj = self.k8s_client.core_v1.read_namespaced_endpoints(
                name=service.metadata.name,
                namespace=service.metadata.namespace,
            )

            if not endpoint_obj.subsets:
                return endpoints

            for subset in endpoint_obj.subsets:
                # Get ready addresses
                ready_addresses = subset.addresses or []
                not_ready_addresses = subset.not_ready_addresses or []

                # Process ready addresses
                for address in ready_addresses:
                    if subset.ports:
                        for port in subset.ports:
                            endpoints.append(
                                ServiceEndpoint(
                                    ip=address.ip,
                                    port=port.port,
                                    ready=True,
                                    hostname=address.hostname,
                                ),
                            )
                    else:
                        # If no ports defined, use service ports
                        for service_port in service.spec.ports or []:
                            endpoints.append(
                                ServiceEndpoint(
                                    ip=address.ip,
                                    port=service_port.port,
                                    ready=True,
                                    hostname=address.hostname,
                                ),
                            )

                # Process not ready addresses
                for address in not_ready_addresses:
                    if subset.ports:
                        for port in subset.ports:
                            endpoints.append(
                                ServiceEndpoint(
                                    ip=address.ip,
                                    port=port.port,
                                    ready=False,
                                    hostname=address.hostname,
                                ),
                            )
                    else:
                        # If no ports defined, use service ports
                        for service_port in service.spec.ports or []:
                            endpoints.append(
                                ServiceEndpoint(
                                    ip=address.ip,
                                    port=service_port.port,
                                    ready=False,
                                    hostname=address.hostname,
                                ),
                            )

        except ApiException as e:
            if e.status == 404:
                logger.debug(f"No endpoints found for service {service.metadata.name}")
            else:
                logger.error(f"Failed to get endpoints: {e}")
            raise

        return endpoints

    def _determine_endpoint_status(self, endpoints: list[ServiceEndpoint]) -> EndpointStatus:
        """Determine the overall endpoint status for a service.

        Args:
            endpoints: List of service endpoints

        Returns:
            Overall endpoint status
        """
        if not endpoints:
            return EndpointStatus.UNHEALTHY

        ready_count = sum(1 for ep in endpoints if ep.ready)

        if ready_count == 0:
            return EndpointStatus.UNHEALTHY
        if ready_count == len(endpoints):
            return EndpointStatus.HEALTHY
        # Some endpoints are ready, some are not
        return EndpointStatus.HEALTHY  # Consider it healthy if at least one is ready

    def get_service_by_name(self, namespace: str, name: str) -> KubernetesService | None:
        """Get a specific service by name.

        Args:
            namespace: Service namespace
            name: Service name

        Returns:
            KubernetesService if found, None otherwise
        """
        try:
            service = self.k8s_client.core_v1.read_namespaced_service(
                name=name,
                namespace=namespace,
            )

            k8s_service = self._convert_service(service)
            endpoints = self._get_service_endpoints(service)
            k8s_service.endpoints = endpoints
            k8s_service.endpoint_status = self._determine_endpoint_status(endpoints)

            return k8s_service

        except ApiException as e:
            if e.status == 404:
                logger.debug(f"Service {namespace}/{name} not found")
            else:
                logger.error(f"Failed to get service {namespace}/{name}: {e}")
            return None

    def refresh_service_status(self, services: list[KubernetesService]) -> list[KubernetesService]:
        """Refresh the status of existing services.

        Args:
            services: List of services to refresh

        Returns:
            List of refreshed services
        """
        refreshed_services = []

        for service in services:
            try:
                # Get fresh service data
                fresh_service = self.get_service_by_name(service.namespace, service.name)
                if fresh_service:
                    refreshed_services.append(fresh_service)
                else:
                    logger.warning(f"Service {service.display_name} no longer exists")

            except Exception as e:
                logger.error(f"Failed to refresh service {service.display_name}: {e}")
                # Keep the original service if refresh fails
                refreshed_services.append(service)

        return refreshed_services
