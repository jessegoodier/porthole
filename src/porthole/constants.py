"""Constants used throughout the porthole application."""

# HTTP Status Codes
HTTP_NOT_FOUND = 404

# Default Values
DEFAULT_REFRESH_INTERVAL = 60
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_HEALTH_CHECK_TIMEOUT = 5

# Port Limits
MIN_PORT = 1
MAX_PORT = 65535

# Service Types
SERVICE_TYPE_CLUSTERIP = "ClusterIP"
SERVICE_TYPE_NODEPORT = "NodePort"
SERVICE_TYPE_LOADBALANCER = "LoadBalancer"

# Endpoint Status
ENDPOINT_STATUS_HEALTHY = "healthy"
ENDPOINT_STATUS_UNHEALTHY = "unhealthy"
ENDPOINT_STATUS_UNKNOWN = "unknown"

# Frontend Detection Keywords
FRONTEND_KEYWORDS = ["frontend", "ui", "web", "portal", "dashboard"]

# Common Namespaces to Skip
DEFAULT_SKIP_NAMESPACES = [
    "kube-system",
    "kube-public",
    "kube-node-lease",
    "kubernetes-dashboard",
    "cert-manager",
    "istio-system",
    "linkerd",
    "linkerd-viz",
]
