# Kubernetes Deployment

This directory contains the Kubernetes manifests to deploy the k8s-service-proxy as a service in your cluster.

## Quick Deployment

### Using kubectl directly

```bash
# Deploy everything
kubectl apply -f rbac.yaml
kubectl apply -f deployment.yaml

# Check deployment status
kubectl -n k8s-service-proxy get pods
kubectl -n k8s-service-proxy get svc
```

### Using Kustomize

```bash
# Deploy with kustomize
kubectl apply -k .

# Check deployment status
kubectl -n k8s-service-proxy get pods
```

## Access the Portal

### Port Forward (Development)

```bash
kubectl -n k8s-service-proxy port-forward svc/k8s-service-proxy 6060:80
# Access at http://localhost:6060
```

### Ingress (Production)

The deployment includes an Ingress resource configured for `k8s-services.local`.

For local development, add to your `/etc/hosts`:

```
127.0.0.1 k8s-services.local
```

For production, update the `host` field in the Ingress to your actual domain.

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

### Resource Limits

Default resource limits:

- **Requests**: 256Mi memory, 100m CPU
- **Limits**: 512Mi memory, 500m CPU

Adjust these in `deployment.yaml` based on your cluster size and needs.

## RBAC Permissions

The service requires the following cluster-wide permissions:

- `services`: get, list, watch
- `endpoints`: get, list, watch (for k8s 1.32 compatibility)
- `endpointslices`: get, list, watch (for k8s 1.33+)
- `namespaces`: get, list, watch
- `nodes`: get, list (for cluster info)

## Security

The deployment follows security best practices:

- Runs as non-root user (UID 1000)
- Uses read-only root filesystem where possible
- Drops all capabilities
- Uses dedicated ServiceAccount with minimal permissions
- Network policies can be added for additional isolation

## Monitoring

The deployment includes:

- **Liveness Probe**: HTTP GET to `/` every 30 seconds
- **Readiness Probe**: HTTP GET to `/` every 10 seconds
- **Health Check**: Built-in Docker health check

## Troubleshooting

### Check pod logs

```bash
kubectl -n k8s-service-proxy logs deployment/k8s-service-proxy
```

### Debug mode

```bash
# Enable debug logging
kubectl -n k8s-service-proxy patch deployment k8s-service-proxy -p '{"spec":{"template":{"spec":{"containers":[{"name":"k8s-service-proxy","env":[{"name":"DEBUG","value":"true"}]}]}}}}'
```

### Check RBAC

```bash
# Verify ServiceAccount
kubectl -n k8s-service-proxy get sa k8s-service-proxy

# Check ClusterRoleBinding
kubectl get clusterrolebinding k8s-service-proxy -o yaml
```

### Common Issues

1. **403 Forbidden**: Check RBAC permissions
2. **Pod CrashLoopBackOff**: Check logs for Python/dependency issues
3. **Service not accessible**: Verify Service and Ingress configuration
4. **Empty service list**: Check namespace filtering and cluster connectivity

## Customization

### Custom Image

```bash
# Build and push custom image
docker build -t your-registry/k8s-service-proxy:v1.0.0 .
docker push your-registry/k8s-service-proxy:v1.0.0

# Update deployment
kubectl -n k8s-service-proxy set image deployment/k8s-service-proxy k8s-service-proxy=your-registry/k8s-service-proxy:v1.0.0
```

### Custom Configuration

Use Kustomize overlays or Helm charts for environment-specific configurations.

## ConfigMap Generation

The static HTML files are deployed as ConfigMaps. Use these commands to create or update them:

```bash
# Create ConfigMap for static files
kubectl create configmap portal-static-files \
  --from-file=portal.html=./src/porthole/static/portal.html \
  --from-file=index.html=./src/porthole/static/index.html \
  --from-file=favicon.ico=./src/porthole/static/favicon.ico \
  --namespace=k8s-service-proxy \
  --dry-run=client -o yaml | kubectl apply -f -


# Restart deployment to pick up ConfigMap changes
kubectl -n k8s-service-proxy rollout restart deployment/k8s-service-proxy
```

## Cleanup

```bash
# Remove everything
kubectl delete -f deployment.yaml
kubectl delete -f rbac.yaml

# Remove ConfigMaps
kubectl delete configmap portal-static-files -n k8s-service-proxy

# Or with kustomize
kubectl delete -k .
```
