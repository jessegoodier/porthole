#!/bin/bash

set -e

KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)
echo "Latest version: $KUBECTL_VERSION"

# Download kubectl binary
echo "Downloading kubectl binary..."
curl -LO "https://dl.k8s.io/release/$KUBECTL_VERSION/bin/linux/amd64/kubectl"

# Download checksum file
echo "Downloading checksum..."
curl -LO "https://dl.k8s.io/$KUBECTL_VERSION/bin/linux/amd64/kubectl.sha256"

# Verify checksum
echo "Verifying checksum..."
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

# Make kubectl executable
chmod +x kubectl

# Move to system path
echo "Installing kubectl to /usr/local/bin/..."
mv kubectl /usr/local/bin/
