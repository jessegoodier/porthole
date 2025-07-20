# Claude Context: k8s-service-proxy

## Project Overview

This is a comprehensive Kubernetes service discovery and proxy portal system that automatically discovers services in a cluster and generates:

1. A beautiful dark-mode web portal with service health indicators
2. NGINX proxy configuration for routing
3. JSON data files for service metadata

## Key Features Implemented

- **Service Discovery**: Auto-detects k8s environment (in-cluster vs kubeconfig)
- **Multi-API Support**: Works with both k8s 1.32 (Endpoints) and 1.33+ (EndpointSlices)
- **Health Monitoring**: Real-time endpoint health checking with visual indicators
- **Frontend Detection**: Automatically identifies frontend services
- **Portal UI**: Responsive dark-mode interface with filtering and search
- **NGINX Integration**: Generates upstream and location blocks for healthy services
- **CLI Tools**: Complete command-line interface for all operations

## Architecture

```
src/porthole/
├── __init__.py
├── config.py              # Configuration management with env var support
├── k8s_client.py          # Kubernetes client with auto-detection
├── models.py              # Pydantic models for type safety
├── service_discovery.py   # Core discovery logic with dual API support
├── portal_generator.py    # HTML portal and JSON generation
├── nginx_generator.py     # NGINX config generation
└── porthole.py   # CLI interface with multiple commands

templates/
├── portal.html            # Jinja2 template for web portal
└── services_template.conf # NGINX location block template
```

## CLI Commands

- `discover` - Find and display services (json/table/text formats)
- `generate` - Create portal HTML, JSON data, and nginx config
- `watch` - Continuous monitoring with auto-regeneration
- `serve` - Built-in HTTP server for the portal
- `info` - Display cluster and configuration information

## Configuration

Environment variables supported:

- `KUBECONFIG` - Path to kubeconfig file
- `OUTPUT_DIR` - Output directory (default: ./output)
- `SKIP_NAMESPACES` - Comma-separated list of namespaces to skip
- `REFRESH_INTERVAL` - Auto-refresh interval in seconds
- `DEBUG` - Enable debug logging

## Dependencies

Core: kubernetes, pydantic, jinja2, click, aiohttp, tabulate
Dev: mypy, pytest, ruff, coverage, taskipy

## Quality Standards

- Type checking with mypy --strict
- Code formatting with ruff
- Comprehensive error handling
- Production-ready logging
- Environment-based configuration

## Recent Changes

- Fixed all type annotations for strict mypy compliance
- Added comprehensive CLI interface
- Implemented dual k8s API support (1.32/1.33)
- Created responsive dark-mode portal UI
- Added nginx configuration generation
- Integrated auto-refresh and filtering capabilities
- **NEW**: Added Docker containerization with multi-stage builds
- **NEW**: Created Kubernetes deployment manifests with RBAC
- **NEW**: Added deployment automation scripts and Makefile
- **NEW**: Implemented security best practices (non-root, minimal permissions)

## Deployment Options

1. **Local Development**: `uv run task run serve` or `make dev`
2. **Docker**: `make build && make run-docker`
3. **Kubernetes**: `make deploy` or `cd k8s && ./deploy.sh`
4. **CI/CD**: `make full-deploy` for complete pipeline

## Kubernetes Features

- **RBAC**: Minimal cluster-wide permissions for service discovery
- **Security**: Non-root user, read-only filesystem, dropped capabilities
- **Health Checks**: Liveness and readiness probes
- **Resource Management**: CPU/memory limits and requests
- **Service Discovery**: Automatic in-cluster configuration
- **Ingress**: Optional external access with configurable domain

## Usage Patterns

1. **Development**: Use `discover` for exploration, `generate` for one-time outputs
2. **Production**: Deploy to Kubernetes with `make deploy` for continuous monitoring
3. **CI/CD**: Use `make full-deploy` for complete build-test-deploy pipeline
4. **Debugging**: Use `make logs` and `make debug` for troubleshooting

The system is production-ready with container deployment and follows modern Python and Kubernetes best practices.
