"""HTTP checking functionality for services."""

import logging
from typing import NamedTuple

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

logger = logging.getLogger(__name__)


class HttpCheckResult(NamedTuple):
    """Result of HTTP check operation."""

    response_code: int | None
    redirect_url: str


class HttpChecker:
    """Handles HTTP requests to check service accessibility."""

    def __init__(self, timeout: int = 10, user_agent: str = "porthole-http-checker/1.0") -> None:
        """Initialize HTTP checker.

        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
        """
        self.timeout = timeout
        self.user_agent = user_agent

    def check_service_http(
        self,
        service_name: str,
        namespace: str,
        port: int,
        protocol: str = "http",
    ) -> HttpCheckResult:
        """Check HTTP accessibility of a service.

        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            port: Port number to check
            protocol: Protocol to use (http or https)

        Returns:
            HttpCheckResult with response code and redirect information
        """
        # Construct the service URL using Kubernetes DNS
        url = f"{protocol}://{service_name}.{namespace}.svc.cluster.local:{port}/"

        logger.debug(f"Checking HTTP accessibility for {url}")

        try:
            # Make HTTP request with timeout
            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=False,  # Don't follow redirects automatically
                headers={"User-Agent": self.user_agent},
                verify=False,  # Skip SSL verification for internal services
            )

            # Handle different response scenarios
            if 200 <= response.status_code < 300:
                # Success response
                logger.debug(f"HTTP check successful: {url} -> {response.status_code}")
                return HttpCheckResult(response.status_code, "")

            if 300 <= response.status_code < 400:
                # Redirect response
                redirect_location = response.headers.get("Location", "")
                logger.debug(f"HTTP redirect: {url} -> {response.status_code} to {redirect_location}")
                return HttpCheckResult(
                    response.status_code,
                    redirect_location or f"Redirect ({response.status_code})",
                )

            # Error response (4xx, 5xx)
            logger.debug(f"HTTP error: {url} -> {response.status_code}")
            return HttpCheckResult(
                response.status_code,
                f"HTTP {response.status_code} Error",
            )

        except Timeout:
            logger.debug(f"HTTP request timeout for {url}")
            return HttpCheckResult(None, f"Timeout after {self.timeout}s")

        except ConnectionError:
            logger.debug(f"Connection error for {url}")
            return HttpCheckResult(None, "Connection refused")

        except RequestException as e:
            logger.debug(f"HTTP request failed for {url}: {e}")
            return HttpCheckResult(None, f"Request failed: {str(e)[:100]}")

        except Exception as e:
            logger.exception(f"Unexpected error checking {url}: {e}")
            return HttpCheckResult(None, f"Unexpected error: {str(e)[:100]}")

    def check_service_with_fallback(
        self,
        service_name: str,
        namespace: str,
        port: int,
    ) -> HttpCheckResult:
        """Check service with HTTP and HTTPS fallback.

        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            port: Port number to check

        Returns:
            HttpCheckResult from the first successful connection
        """
        # Try HTTP first for most services
        http_result = self.check_service_http(service_name, namespace, port, "http")

        # If HTTP fails with connection error, try HTTPS
        if http_result.response_code is None and "Connection refused" in http_result.redirect_url:
            logger.debug(f"HTTP failed for {service_name}:{port}, trying HTTPS")
            https_result = self.check_service_http(service_name, namespace, port, "https")

            # Return HTTPS result if it's better than HTTP result
            if https_result.response_code is not None:
                return https_result

        return http_result
