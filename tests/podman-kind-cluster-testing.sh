#!/bin/bash

# Path to kubeconfig
KUBECONFIG_PATH="$(echo $KUBECONFIG)"
TMP_KUBECONFIG_PATH="./tests/temp-kubeconfig"
CONTAINER_KUBECONFIG="/app/.kubeconfig"

# Image you want to use (change as needed – should have kubectl installed)
IMAGE_NAME="porthole-dev"

# Substitute 127.0.0.1 with host.containers.internal for Podman Mac networking
# Add insecure-skip-tls-verify to the kubeconfig
cp "$KUBECONFIG_PATH" $TMP_KUBECONFIG_PATH
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' '/- cluster:/a\
    insecure-skip-tls-verify: true
    ' $TMP_KUBECONFIG_PATH
    sed -i '' 's/127.0.0.1/host.containers.internal/g' $TMP_KUBECONFIG_PATH
else
    sed -i 's/127.0.0.1/host.containers.internal/g' $TMP_KUBECONFIG_PATH
    sed '/- cluster:/a\
    insecure-skip-tls-verify: true
    ' $TMP_KUBECONFIG_PATH
fi

# Start Podman container with kubeconfig mounted and env var set for KUBECONFIG
podman run -it --rm \
  -v $TMP_KUBECONFIG_PATH:$CONTAINER_KUBECONFIG:ro \
  --env KUBECONFIG=$CONTAINER_KUBECONFIG \
  $IMAGE_NAME \
  python -m porthole.porthole generate

# Cleanup
rm $TMP_KUBECONFIG_PATH
