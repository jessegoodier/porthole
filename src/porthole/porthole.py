"""porthole."""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Optional

import click

# Add TRACE log level (below DEBUG)
TRACE_LEVEL_NUM = 5
if not hasattr(logging, "TRACE"):
    logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

    def trace(self, message, *args, **kws):
        if self.isEnabledFor(TRACE_LEVEL_NUM):
            self._log(TRACE_LEVEL_NUM, message, args, **kws)

    logging.Logger.trace = trace
    logging.TRACE = TRACE_LEVEL_NUM

from .config import Config
from .k8s_client import get_kubernetes_client
from .models import ServiceDiscoveryResult
from .nginx_generator import NginxGenerator
from .portal_generator import PortalGenerator
from .service_discovery import ServiceDiscovery


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration.

    Args:
        log_level: Log level (TRACE,DEBUG, INFO, WARNING, ERROR)
    """
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    if numeric_level is None:
        if log_level.upper() == "TRACE":
            numeric_level = TRACE_LEVEL_NUM
        else:
            numeric_level = logging.INFO

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("porthole.log"),
        ],
    )


@click.group()
@click.option(
    "--log-level",
    type=click.Choice(
        ["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False
    ),
    help="Set logging level",
)
@click.option("--config-file", type=click.Path(), help="Path to configuration file")
@click.pass_context
def cli(ctx: click.Context, log_level: str | None, config_file: str | None) -> None:
    """Kubernetes Service Proxy - Discover services and generate proxy configurations."""
    # First, do a quick config parse to get the base log level
    if config_file:
        # TODO: Implement config file loading
        config = Config.parse_config()
    else:
        config = Config.parse_config()

    # Override log level if provided via CLI
    if log_level:
        config.log_level = log_level.upper()
    
    # Setup logging with the resolved log level
    setup_logging(config.log_level)
    
    # Now re-parse config with debug logging enabled (if debug level)
    debug_logging = config.log_level in ["DEBUG", "TRACE"]
    if debug_logging:
        logger = logging.getLogger(__name__)
        logger.debug("Re-parsing configuration with debug logging enabled")
        if config_file:
            # TODO: Implement config file loading
            config = Config.parse_config(debug_logging=True)
        else:
            config = Config.parse_config(debug_logging=True)
        
        # Override log level again if provided via CLI
        if log_level:
            config.log_level = log_level.upper()

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
        logger.exception(f"Service discovery failed: {e}")
        if config.log_level == "DEBUG":
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

        logger.debug(f"Discovered {result.total_services} services")

        # Generate outputs
        generated_files = []

        if not no_json:
            portal_gen = PortalGenerator(config)
            json_file = portal_gen.generate_json_data(result)
            generated_files.append(json_file)
            logger.debug(f"Generated JSON data: {json_file}")

        if not no_nginx:
            nginx_gen = NginxGenerator(config)
            nginx_file = nginx_gen.generate_nginx_config(result)
            generated_files.append(nginx_file)
            logger.debug(f"Generated nginx config: {nginx_file}")

            # Validate nginx config
            if nginx_gen.validate_nginx_config(nginx_file):
                logger.debug("NGINX configiguration is valid")
            else:
                logger.warning("NGINX configiguration validation failed")

        click.echo(f"Generated {len(generated_files)} files:")
        for file_path in generated_files:
            click.echo(f"  - {file_path}")

    except Exception as e:
        logger.exception(f"Generation failed: {e}")
        if config.log_level == "DEBUG":
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
                nginx_gen.generate_nginx_config(result)

                logger.debug(
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
                logger.exception(f"Watch iteration {iteration} failed: {e}")
                if config.debug:
                    raise
                # Continue watching despite errors
                time.sleep(interval)

    except Exception as e:
        logger.exception(f"Watch mode failed: {e}")
        if config.log_level == "DEBUG":
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
        click.echo(f"  - Log Level: {config.log_level}")

    except Exception as e:
        logger.exception(f"Failed to get cluster info: {e}")
        if config.log_level == "DEBUG":
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

        # Use centralized to_dict method with CLI format
        data = result.to_dict(format_type="cli")
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
            status_icon = "  " if service.endpoint_status.value == "healthy" else "L"
            frontend_icon = "  " if service.is_frontend else ""

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
