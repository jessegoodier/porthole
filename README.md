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

## Kubernetes Deployment

Deploy as a service in your Kubernetes cluster:

```bash
# Quick deployment
cd k8s/
./deploy.sh

# Or manually
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment.yaml

# Access the portal
kubectl -n k8s-service-proxy port-forward svc/k8s-service-proxy 6060:80
# Visit http://localhost:6060
```

The deployment includes:

- **RBAC**: Minimal permissions for service discovery
- **Deployment**: Single replica with health checks and resource limits
- **Service**: ClusterIP service for internal access
- **Ingress**: Optional external access (configure your domain)
- **Security**: Non-root user, read-only filesystem, dropped capabilities

For detailed deployment instructions, see [`k8s/README.md`](k8s/README.md).

## Configuration

Configure via environment variables:

```bash
# Kubernetes configuration
export KUBECONFIG=/path/to/kubeconfig  # Optional, auto-detects

# Output settings
export OUTPUT_DIR=./output             # Default: ./output
export SERVICE_JSON_FILE=services.json # Default: services.json
export PORTAL_HTML_FILE=portal.html   # Default: portal.html
export NGINX_CONFIG_FILE=services.conf # Default: services.conf

# Namespace filtering
export SKIP_NAMESPACES="kube-system,kube-public,cert-manager"

# Portal settings
export PORTAL_TITLE="My K8s Services"
export REFRESH_INTERVAL=300           # Auto-refresh interval (seconds)

# Debug mode
export DEBUG=true
```

## Output Files

The system generates several output files in the configured output directory:

- **`portal.html`** - Beautiful web interface with service dashboard
- **`services.json`** - Machine-readable service metadata
- **`services.conf`** - NGINX configuration with upstreams and locations
- **`docker-compose.override.yml`** - Docker Compose configuration (when generated)

## Portal Features

The generated web portal includes:

- **Service Grid**: Organized by namespace with service cards
- **Health Indicators**: ✅ healthy endpoints, ❌ unhealthy endpoints
- **Frontend Detection**: Additional ✅ for services containing "frontend"
- **Search & Filtering**: Filter by name, namespace, status, or frontend services
- **Statistics Dashboard**: Overview of total, healthy, unhealthy, and frontend services
- **Responsive Design**: Works on desktop and mobile devices
- **Auto-refresh**: Automatically updates when refresh interval is configured

## NGINX Integration

The system generates nginx configuration including:

- **Upstream blocks** for each healthy service
- **Location blocks** with proper path rewriting
- **Health-based routing** (only includes services with healthy endpoints)
- **Docker Compose integration** for containerized deployments

Example generated nginx config:

```nginx
upstream k8s-service-default-webapp-80 {
    server 10.244.1.5:80;
    server 10.244.2.3:80;
}

location /default_webapp_80 {
    rewrite ^/default_webapp_80/?(.*)$ /$1 break;
    proxy_pass http://k8s-service-default-webapp-80;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
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
├── config.py              # Configuration management
├── k8s_client.py          # Kubernetes client with auto-detection
├── models.py              # Pydantic models for type safety
├── service_discovery.py   # Core discovery logic
├── portal_generator.py    # HTML portal and JSON generation
├── nginx_generator.py     # NGINX config generation
└── porthole.py   # CLI interface

templates/
├── portal.html            # Jinja2 template for web portal
└── services_template.conf # NGINX location block template
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
