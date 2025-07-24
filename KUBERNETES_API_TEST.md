# Kubernetes API Connectivity Testing

Porthole now includes comprehensive Kubernetes API connectivity testing at startup to ensure proper authentication and authorization before attempting service discovery.

## What's New

### Automatic Startup Testing
All Porthole CLI commands now automatically test Kubernetes API connectivity at startup:
- `uv run python -m porthole.porthole discover`
- `uv run python -m porthole.porthole generate` 
- `uv run python -m porthole.porthole watch`
- `uv run python -m porthole.porthole info`

### Dedicated Test Command
A new CLI command specifically for testing API connectivity:
```bash
uv run python -m porthole.porthole test-api
```

## Tests Performed

### 1. Basic API Connectivity
- Connects to the Kubernetes API server
- Retrieves available API resources
- Verifies the connection is working

### 2. Authentication Verification
- Tests ability to authenticate with the cluster
- Attempts to list namespaces (basic read operation)
- **Exits with code 1** on 401 Unauthorized errors

### 3. Service Discovery Permissions
- Verifies permission to list services across all namespaces
- **Exits with code 1** on 403 Forbidden errors for services

### 4. Endpoint Discovery Permissions  
- Tests permission to list endpoints across all namespaces
- **Warns but continues** on 403 Forbidden errors for endpoints

## Error Handling

### 401 Unauthorized
```
✗ Authentication failed: 401 Unauthorized
  → Check your kubeconfig file or service account token
  → Verify your cluster connection settings
```
**Action**: Application exits with code 1

### 403 Forbidden (Critical Resources)
```
✗ Authorization failed: 403 Forbidden
  → Service account lacks permission to list namespaces
  → Required RBAC: 'get' and 'list' on 'namespaces' resource
```
**Action**: Application exits with code 1

### 403 Forbidden (Non-Critical Resources)
```
⚠ Missing endpoint permissions: 403 Forbidden
  → Endpoint status detection will be limited
  → Recommended RBAC: 'get' and 'list' on 'endpoints' resource
```
**Action**: Warning logged, application continues

## Required RBAC Permissions

For full functionality, your service account needs these permissions:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: porthole-reader
rules:
- apiGroups: [""]
  resources: ["namespaces", "services", "endpoints"]
  verbs: ["get", "list"]
```

### Minimum Required Permissions
- `namespaces`: get, list (required - app exits without this)
- `services`: get, list (required - app exits without this)
- `endpoints`: get, list (optional - warnings only)

## Benefits

1. **Fast Failure**: Detect authentication/authorization issues immediately instead of during service discovery
2. **Clear Error Messages**: Specific guidance on what permissions are missing
3. **Better Debugging**: Easy to identify whether issues are authentication, authorization, or connectivity related
4. **Graceful Degradation**: Non-critical permissions generate warnings but don't stop the application

## Usage Examples

### Test API connectivity only:
```bash
uv run python -m porthole.porthole test-api
```

### Normal operation (includes automatic API test):
```bash
uv run python -m porthole.porthole discover --format table
```

### Expected output on success:
```
INFO:porthole.k8s_client:Testing Kubernetes API connectivity and permissions...
INFO:porthole.k8s_client:✓ Kubernetes API connectivity test completed successfully
```

### Expected output on failure:
```
ERROR:porthole.k8s_client:✗ Authentication failed: 401 Unauthorized
ERROR:porthole.k8s_client:  → Check your kubeconfig file or service account token
ERROR:porthole.k8s_client:  → Verify your cluster connection settings
```

The application will exit with code 1, making it easy to detect failures in scripts and automation.