# Porthole - Kubernetes Service Proxy Portal

## ALLOWED COMMANDS

```bash
# Clone the repository
git clone https://github.com/jessegoodier/porthole.git
cd porthole
```

[Kubernetes Deployment](k8s/README.md)

## Using UV for development

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
uv sync

# Run the application
```

### Basic Usage

```bash
# Discover services in your cluster
uv run python -m porthole.porthole discover --format table

# Generate portal and nginx configuration
uv run python -m porthole.porthole generate

# Start continuous monitoring
uv run python -m porthole.porthole watch --interval 300
```

### Using Task Commands

```bash
# Format and lint code
uv run task format
uv run task lint

# Run type checking
uv run task type
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

## Development

### Code Quality

Tests should pass:

```bash
uv run task test
```

Below are WIP, needs some cleanup.

```bash
# Format code
uv run task format

# Lint code
uv run task lint

# Type checking
uv run task type
```

### Project Structure

```
. (project root)
├── .bumpversion.toml                # bump-my-version config
├── .dockerignore                    # ignore files for docker build
├── Dockerfile                       # Dockerfile for the container
├── Makefile                         # Makefile for the project
├── k8s/                             # Kubernetes manifests
│   ├── config.yaml
│   ├── deployment.yaml
│   ├── rbac.yaml
│   └── README.md
├── pyproject.toml
├── scripts/                         # Scripts for the container
│   ├── entrypoint.sh
│   ├── startup-watch.sh
│   └── startup.sh
├── src/                             # Source code
│   └── porthole/
│       ├── __init__.py
│       ├── config.py
│       ├── constants.py
│       ├── k8s_client.py
│       ├── models.py
│       ├── nginx_generator.py
│       ├── nginx_reloader.py
│       ├── portal_generator.py
│       ├── porthole.py
│       ├── service_discovery.py
│       ├── py.typed
│       ├── static/                    # Static files for the portal
│       │   ├── favicon.ico
│       │   ├── index.html
│       │   └── porthole.png
│       └── templates/                 # Templates for the nginx configuration
│           └── locations.conf.j2
├── tests/                             # Tests
│   ├── conftest.py
│   ├── podman-kind-cluster-testing.sh
│   ├── test_config.py
│   ├── test_constants.py
│   ├── test_k8s_client.py
│   ├── test_models.py
│   ├── test_porthole.py
│   └── trivy.sh                        # Trivy scan for vulnerabilities
```

## Special Thanks

- [Claude AI](https://www.anthropic.com/)
- [Cursor AI](https://www.cursor.com/)
