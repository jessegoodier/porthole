# Kubernetes Deployment

This directory contains the Kubernetes manifests to deploy the porthole as a service in your cluster.

## Quick Deployment

The static HTML files are deployed as ConfigMaps. Use these commands to create or update them:

```bash
kubectl create ns porthole
kubectl apply -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/rbac.yaml
kubectl apply -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/config.yaml
kubectl apply -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/deployment.yaml
kubectl apply -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/service.yaml
```

Check deployment status

```bash
kubectl get pods -n porthole
```

```bash
kubectl logs -n porthole -l app.kubernetes.io/name=porthole --all-containers 
```

Delete everything:

```bash
kubectl delete -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/rbac.yaml
kubectl delete -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/config.yaml
kubectl delete -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/deployment.yaml
kubectl delete -n porthole -f https://raw.githubusercontent.com/jessegoodier/porthole/main/k8s/service.yaml
kubectl delete ns porthole
```

## Configuration

### Environment Variables

The deployment can be customized using environment variables in `deployment.yaml`:

- `STARTUP_MODE`: Application startup mode (default: "watch")
  - `generate`: Generate initial config once, then serve
  - `watch`: Generate initial config + continuous updates + serve
  - `serve-only`: Just serve without config generation
- `REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 60)
- `PORTAL_TITLE`: Title for the web portal
- `DEBUG`: Enable debug logging (true/false)
- `SKIP_NAMESPACES`: Comma-separated list of namespaces to skip
- `OUTPUT_DIR`: Directory for generated files (default: /app/generated-output)

## Cleanup

```bash
# Remove everything
kubectl delete -f k8s/
kubectl delete namespace porthole
```
