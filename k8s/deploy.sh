#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="k8s-service-proxy"
IMAGE="jgoodier/k8s-service-proxy:0.2.9"

echo -e "${BLUE}🚀 Deploying k8s-service-proxy to Kubernetes${NC}"
echo "========================================"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

# Check cluster connectivity
echo -e "${YELLOW}🔍 Checking cluster connectivity...${NC}"
ls -la
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster. Check your kubeconfig.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Connected to cluster${NC}"

# Deploy RBAC
echo -e "${YELLOW}🔐 Creating RBAC resources...${NC}"
kubectl apply -f rbac.yaml

# Deploy application
echo -e "${YELLOW}🚀 Deploying application...${NC}"
kubectl apply -f deployment.yaml

# Wait for deployment to be ready
echo -e "${YELLOW}⏳ Waiting for deployment to be ready...${NC}"
kubectl -n ${NAMESPACE} rollout status deployment/k8s-service-proxy --timeout=300s

# Show status
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${BLUE}📊 Status:${NC}"
kubectl -n ${NAMESPACE} get pods,svc,ingress

echo ""
echo -e "${BLUE}🌐 Access the portal:${NC}"
echo -e "${GREEN}Port Forward:${NC} kubectl -n ${NAMESPACE} port-forward svc/k8s-service-proxy 6060:80"
echo -e "${GREEN}Then visit:${NC} http://localhost:6060"
echo ""
echo -e "${GREEN}Ingress:${NC} http://k8s-services.local (add to /etc/hosts if needed)"

echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo "View logs: kubectl -n ${NAMESPACE} logs deployment/k8s-service-proxy"
echo "Debug mode: kubectl -n ${NAMESPACE} set env deployment/k8s-service-proxy DEBUG=true"
echo "Scale up: kubectl -n ${NAMESPACE} scale deployment/k8s-service-proxy --replicas=2"
echo "Delete: kubectl delete -f deployment.yaml && kubectl delete -f rbac.yaml"