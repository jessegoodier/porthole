#!/bin/bash

KIND_CLUSTER_NAME="kind2"
KIND_CONFIG_FILE="kind-config.yaml"

# Create the cluster if it doesn't exist
if ! kind get clusters | grep -q "$KIND_CLUSTER_NAME"; then
    # prompt for confirmation
    read -p "Create cluster $KIND_CLUSTER_NAME? (y/n): " confirm
    if [ "$confirm" == "y" ]; then
        kind create cluster --name "$KIND_CLUSTER_NAME" --config "$KIND_CONFIG_FILE"
    fi
fi
echo "Cluster $KIND_CLUSTER_NAME ready, building image..."

# Build the image
UNIQUE_TAG=$(date +%Y%m%d%H%M%S)
podman build -t porthole-dev:$UNIQUE_TAG -f docker/Dockerfile.app-changes-only .
podman save porthole-dev:$UNIQUE_TAG -o porthole-dev-${UNIQUE_TAG}.tar
echo "Saved image to porthole-dev-${UNIQUE_TAG}.tar"
kind load image-archive porthole-dev-${UNIQUE_TAG}.tar --name "$KIND_CLUSTER_NAME"

# check if current context is the kind cluster
if ! kubectl config current-context | grep -q "$KIND_CLUSTER_NAME"; then
    kind export kubeconfig --name "$KIND_CLUSTER_NAME"
fi

echo "Deploying pod..."
kubectl create namespace porthole-dev
kubectl create configmap porthole-config --from-file=./src/porthole/config
kubectl run -n porthole-dev porthole-dev --image=porthole-dev:$UNIQUE_TAG --restart=Never
