"""porthole."""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Optional

import click

from .config import Config
from .k8s_client import get_kubernetes_client
from .models import ServiceDiscoveryResult
from .nginx_generator import NginxGenerator
from .portal_generator import PortalGenerator
from .service_discovery import ServiceDiscovery


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration.

    Args:
        debug: Enable debug logging
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("k8s-service-proxy.log"),
        ],
    )


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.option("--config-file", type=click.Path(), help="Path to configuration file")
@click.pass_context
def cli(ctx: click.Context, debug: bool, config_file: str | None) -> None:
    """Kubernetes Service Proxy - Discover services and generate proxy configurations."""
    setup_logging(debug)

    # Load configuration
    if config_file:
        # TODO: Implement config file loading
        config = Config.from_env()
    else:
        config = Config.from_env()

    config.debug = debug

    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command()
@click.option(
    "--output-dir",
    type=click.Path(),
    help="Output directory for generated files",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml", "table"]),
    default="json",
    help="Output format",
)
@click.pass_context
def discover(ctx: click.Context, output_dir: str | None, output_format: str) -> None:
    """Discover services in the Kubernetes cluster."""
    config = ctx.obj["config"]

    if output_dir:
        config.output_dir = Path(output_dir)

    logger = logging.getLogger(__name__)
    logger.info("Starting service discovery")

    try:
        # Initialize Kubernetes client
        k8s_client = get_kubernetes_client(config)

        # Perform service discovery
        discovery = ServiceDiscovery(k8s_client, config)
        result = discovery.discover_services()

        # Display results
        _display_discovery_result(result, output_format)

        logger.info(
            f"Service discovery completed: {result.total_services} services found",
        )

    except Exception as e:
        logger.error(f"Service discovery failed: {e}")
        if config.debug:
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--output-dir",
    type=click.Path(),
    help="Output directory for generated files",
)
@click.option("--no-nginx", is_flag=True, help="Skip nginx configuration generation")
@click.option("--no-portal", is_flag=True, help="Skip portal generation")
@click.option("--no-json", is_flag=True, help="Skip JSON data generation")
@click.pass_context
def generate(
    ctx: click.Context,
    output_dir: str | None,
    no_nginx: bool,
    no_portal: bool,
    no_json: bool,
) -> None:
    """Generate portal and nginx configuration from discovered services."""
    config = ctx.obj["config"]

    if output_dir:
        config.output_dir = Path(output_dir)

    logger = logging.getLogger(__name__)
    logger.info("Starting service discovery and generation")

    try:
        # Initialize Kubernetes client
        k8s_client = get_kubernetes_client(config)

        # Perform service discovery
        discovery = ServiceDiscovery(k8s_client, config)
        result = discovery.discover_services()

        logger.info(f"Discovered {result.total_services} services")

        # Generate outputs
        generated_files = []

        if not no_json:
            portal_gen = PortalGenerator(config)
            json_file = portal_gen.generate_json_data(result)
            generated_files.append(json_file)
            logger.info(f"Generated JSON data: {json_file}")

        if not no_portal:
            portal_gen = PortalGenerator(config)
            portal_file = portal_gen.generate_portal(result)
            generated_files.append(portal_file)
            logger.info(f"Generated portal: {portal_file}")
            
            # Also generate table view
            table_file = portal_gen.generate_table(result)
            generated_files.append(table_file)
            logger.info(f"Generated table view: {table_file}")

        if not no_nginx:
            nginx_gen = NginxGenerator(config)
            nginx_file = nginx_gen.generate_nginx_config(result)
            generated_files.append(nginx_file)
            logger.info(f"Generated nginx config: {nginx_file}")

            # Validate nginx config
            if nginx_gen.validate_nginx_config(nginx_file):
                logger.info("Nginx configuration is valid")
            else:
                logger.warning("Nginx configuration validation failed")

        click.echo(f"Generated {len(generated_files)} files:")
        for file_path in generated_files:
            click.echo(f"  - {file_path}")

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        if config.debug:
            raise
        sys.exit(1)


@cli.command()
@click.option(
    "--output-dir",
    type=click.Path(),
    help="Output directory for generated files",
)
@click.option("--interval", type=int, default=300, help="Refresh interval in seconds")
@click.option(
    "--max-iterations",
    type=int,
    help="Maximum number of iterations (0 for unlimited)",
)
@click.pass_context
def watch(
    ctx: click.Context,
    output_dir: str | None,
    interval: int,
    max_iterations: int | None,
) -> None:
    """Watch for service changes and regenerate configurations."""
    config = ctx.obj["config"]

    if output_dir:
        config.output_dir = Path(output_dir)

    config.refresh_interval = interval

    logger = logging.getLogger(__name__)
    logger.info(f"Starting watch mode with {interval}s interval")

    try:
        # Initialize clients
        k8s_client = get_kubernetes_client(config)
        discovery = ServiceDiscovery(k8s_client, config)
        portal_gen = PortalGenerator(config)
        nginx_gen = NginxGenerator(config)

        iteration = 0

        while True:
            iteration += 1
            logger.info(f"Watch iteration {iteration}")

            try:
                # Discover services
                result = discovery.discover_services()

                # Generate all outputs
                portal_gen.generate_json_data(result)
                portal_gen.generate_portal(result)
                nginx_gen.generate_nginx_config(result)

                logger.info(
                    f"Generated configurations for {result.total_services} services",
                )

                # Check if we've reached max iterations
                if max_iterations and iteration >= max_iterations:
                    logger.info(f"Reached maximum iterations ({max_iterations})")
                    break

                # Wait for next iteration
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping watch")
                break
            except Exception as e:
                logger.error(f"Watch iteration {iteration} failed: {e}")
                if config.debug:
                    raise
                # Continue watching despite errors
                time.sleep(interval)

    except Exception as e:
        logger.error(f"Watch mode failed: {e}")
        if config.debug:
            raise
        sys.exit(1)



@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Display cluster and configuration information."""
    config = ctx.obj["config"]

    logger = logging.getLogger(__name__)

    try:
        # Initialize Kubernetes client
        k8s_client = get_kubernetes_client(config)

        # Get cluster info
        cluster_info = k8s_client.get_cluster_info()

        click.echo("Cluster Information:")
        click.echo(f"  - Nodes: {cluster_info.get('node_count', 'N/A')}")
        click.echo(f"  - Namespaces: {cluster_info.get('namespace_count', 'N/A')}")
        click.echo(f"  - API Resources: {cluster_info.get('api_resources', 'N/A')}")
        click.echo(f"  - Cluster Ready: {cluster_info.get('cluster_ready', 'N/A')}")

        click.echo("\nConfiguration:")
        click.echo(f"  - Output Directory: {config.output_dir}")
        click.echo(f"  - Skip Namespaces: {len(config.skip_namespaces)} namespaces")
        click.echo(f"  - Include Headless: {config.include_headless_services}")
        click.echo(f"  - Refresh Interval: {config.refresh_interval}s")
        click.echo(f"  - Debug Mode: {config.debug}")

    except Exception as e:
        logger.error(f"Failed to get cluster info: {e}")
        if config.debug:
            raise
        sys.exit(1)


def _display_discovery_result(
    result: ServiceDiscoveryResult,
    output_format: str,
) -> None:
    """Display service discovery result.

    Args:
        result: Service discovery result
        output_format: Output format (json, yaml, table)
    """
    if output_format == "json":
        import json

        data = {
            "total_services": result.total_services,
            "healthy_services": result.healthy_services,
            "unhealthy_services": result.unhealthy_services,
            "frontend_services": result.frontend_services,
            "namespaces_scanned": result.namespaces_scanned,
            "namespaces_skipped": result.namespaces_skipped,
            "services": [
                {
                    "namespace": service.namespace,
                    "name": service.name,
                    "type": service.service_type.value,
                    "ports": [port.port for port in service.ports],
                    "endpoint_status": service.endpoint_status.value,
                    "is_frontend": service.is_frontend,
                    "endpoint_count": len(service.endpoints),
                }
                for service in result.get_sorted_services()
            ],
        }
        click.echo(json.dumps(data, indent=2))

    elif output_format == "table":
        from tabulate import tabulate

        headers = [
            "Namespace",
            "Service",
            "Type",
            "Ports",
            "Status",
            "Frontend",
            "Endpoints",
        ]
        rows = []

        for service in result.get_sorted_services():
            ports_str = ",".join(str(port.port) for port in service.ports)
            status_icon = "" if service.endpoint_status.value == "healthy" else "L"
            frontend_icon = "" if service.is_frontend else ""

            rows.append(
                [
                    service.namespace,
                    service.name,
                    service.service_type.value,
                    ports_str,
                    status_icon,
                    frontend_icon,
                    len(service.endpoints),
                ],
            )

        click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    else:
        # Simple text format
        click.echo(f"Total Services: {result.total_services}")
        click.echo(f"Healthy: {result.healthy_services}")
        click.echo(f"Unhealthy: {result.unhealthy_services}")
        click.echo(f"Frontend: {result.frontend_services}")
        click.echo(f"Namespaces: {len(result.namespaces_scanned)}")


if __name__ == "__main__":
    cli()
