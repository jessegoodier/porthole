# Kubernetes Service Proxy Portal

A comprehensive Kubernetes service discovery and proxy portal system that automatically discovers services in your cluster and generates a beautiful web interface with nginx proxy configuration.

## Features

- 🔍 **Service Discovery**: Automatically discovers all services across namespaces
- 🌐 **Web Portal**: Beautiful dark-mode responsive interface with filtering and search
- ✅ **Health Monitoring**: Real-time endpoint health checking with visual indicators
- 🎯 **Frontend Detection**: Automatically identifies and highlights frontend services
- 🔧 **NGINX Integration**: Generates proxy configuration for healthy services
- 🛠️ **CLI Tools**: Complete command-line interface for all operations
- 🔄 **Auto-refresh**: Continuous monitoring with configurable intervals
- 🏗️ **Multi-API Support**: Works with both k8s 1.32 (Endpoints) and 1.33+ (EndpointSlices)

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd k8s-service-proxy

# Install dependencies
uv sync
```

### Basic Usage

```bash
# Discover services in your cluster
uv run python -m porthole.porthole discover --format table

# Generate portal and nginx configuration
uv run python -m porthole.porthole generate

# Start continuous monitoring
uv run python -m porthole.porthole watch --interval 300

# Serve portal via HTTP
uv run python -m porthole.porthole serve --port 6060
```

### Using Task Commands

```bash
# Format and lint code
uv run task format
uv run task lint

# Run type checking
uv run task type

# Run the application
uv run task run discover --format table
```

## CLI Commands

### `discover`

Find and display services in various formats:

```bash
# Table format (human-readable)
uv run task run discover --format table

# JSON format (machine-readable)
uv run task run discover --format json

# Simple text format
uv run task run discover --format text
```

### `generate`

Create portal HTML, JSON data, and nginx configuration:

```bash
# Generate all outputs
uv run task run generate

# Generate only specific outputs
uv run task run generate --no-nginx --no-portal  # JSON only
uv run task run generate --no-json --no-nginx    # Portal only
```

### `watch`

Continuous monitoring with auto-regeneration:

```bash
# Watch with default 5-minute interval
uv run task run watch

# Custom interval and max iterations
uv run task run watch --interval 60 --max-iterations 10
```

### `serve`

Built-in HTTP server for the portal:

```bash
# Start server on default port 6060
uv run task run serve

# Custom host and port
uv run task run serve --host 0.0.0.0 --port 3000
```

### `info`

Display cluster and configuration information:

```bash
uv run task run info
```

## Development

### Code Quality

```bash
# Format code
uv run task format

# Lint code
uv run task lint

# Type checking
uv run task type

# Run tests
uv run task tests
```

### Project Structure

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
└── static/               # Static files (favicon, index.html)
    ├── favicon.ico
    ├── index.html
    └── porthole.png

templates/
└── locations.conf.j2      # Jinja2 template for NGINX location blocks
```

## Requirements Met

✅ JSON file generation with service metadata  
✅ Web portal template with dark mode theme  
✅ Alphabetical listing by namespace/service:port  
✅ Health indicators using both k8s 1.32 and 1.33 APIs  
✅ NGINX proxy configuration generation  
✅ Frontend service detection and highlighting  
✅ Modern Kubernetes library (kubernetes>=29.0.0)  
✅ Auto-detection of in-cluster vs kubeconfig  
✅ System namespace filtering  
✅ Best practices project structure  
✅ Quality tooling (ruff, mypy, pytest)  
✅ Type checking and linting compliance
