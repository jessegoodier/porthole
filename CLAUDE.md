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
├── constants.py           # Application constants and magic numbers
├── k8s_client.py          # Kubernetes client with auto-detection
├── models.py              # Pydantic models for type safety
├── service_discovery.py   # Core discovery logic with dual API support
├── portal_generator.py    # HTML portal and JSON generation
├── nginx_generator.py     # NGINX config generation
├── nginx_reloader.py      # NGINX configuration reload monitoring
├── porthole.py           # CLI interface with multiple commands
└── static/               # Static files (favicon, index.html, images)

templates/
└── locations.conf.j2      # Jinja2 template for NGINX location blocks
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

Core: kubernetes, pydantic, jinja2, click, tabulate, requests, watchdog
Dev: mypy, pytest, ruff, coverage, taskipy, isort, pre-commit, types-tabulate

## Quality Standards

- Type checking with mypy --strict
- Code formatting with ruff
- Comprehensive error handling
- Production-ready logging
- Environment-based configuration

## Recent Changes

- **MAJOR REFACTOR**: Removed 7 unused/redundant files for cleaner codebase
- **CODE QUALITY**: Fixed 60+ ruff linting issues, applied consistent formatting
- **MAINTAINABILITY**: Added constants.py module to eliminate magic numbers
- **TYPE SAFETY**: Updated all type annotations, removed deprecated typing imports
- **LOGGING**: Improved logging practices with proper format strings
- Fixed all type annotations for strict mypy compliance
- Added comprehensive CLI interface
- Implemented dual k8s API support (1.32/1.33)
- Created responsive dark-mode portal UI
- Added nginx configuration generation
- Integrated auto-refresh and filtering capabilities
- Added Docker containerization with multi-stage builds
- Created Kubernetes deployment manifests with RBAC
- Added deployment automation scripts and Makefile
- Implemented security best practices (non-root, minimal permissions)

## Deployment Options

1. **Local Development**: `uv run task run serve` or `make dev`
2. **Docker**: `make build && make run-docker` 
3. **Kubernetes**: `make deploy` or `cd k8s && kubectl apply -f .`
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

## Testing

The project includes comprehensive test coverage for all core functionality:

- **Unit Tests**: All models, configuration, and utility functions
- **Integration Tests**: Service discovery, portal generation, and nginx config
- **CLI Tests**: Command-line interface functionality
- **Mock Tests**: Kubernetes API interactions with realistic fixtures

Run tests with:
```bash
uv run task tests       # Run all tests
uv run task coverage    # Generate coverage report
uv run task type        # Type checking
```

## Code Quality Metrics

- **Test Coverage**: 85%+ target with comprehensive edge case testing
- **Type Coverage**: 100% with strict mypy compliance
- **Linting**: Clean ruff checks with minimal exceptions
- **Documentation**: Comprehensive docstrings and README files

The system is production-ready with container deployment and follows modern Python and Kubernetes best practices.
