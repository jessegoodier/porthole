# Kubernetes Deployment

This directory contains the Kubernetes manifests to deploy the k8s-service-proxy as a service in your cluster.

## Quick Deployment

The static HTML files are deployed as ConfigMaps. Use these commands to create or update them:

```bash
kubectl create namespace k8s-service-proxy
# Create ConfigMap for static files
kubectl create configmap portal-static-files \
  --from-file=portal.html=./src/porthole/static/portal.html \
  --from-file=index.html=./src/porthole/static/index.html \
  --from-file=favicon.ico=./src/porthole/static/favicon.ico \
  --namespace=k8s-service-proxy \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/ -n k8s-service-proxy
```

## Configuration

### Environment Variables

The deployment can be customized using environment variables in `deployment.yaml`:

- `STARTUP_MODE`: Application startup mode (default: "watch")
  - `generate`: Generate initial config once, then serve
  - `watch`: Generate initial config + continuous updates + serve
  - `serve-only`: Just serve without config generation
- `REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 300)
- `PORTAL_TITLE`: Title for the web portal
- `DEBUG`: Enable debug logging (true/false)
- `SKIP_NAMESPACES`: Comma-separated list of namespaces to skip
- `OUTPUT_DIR`: Directory for generated files (default: /app/generated-output)

## Cleanup

```bash
# Remove everything
kubectl delete -f k8s/
kubectl delete namespace k8s-service-proxy
```
