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

# Verify checksum (Alpine Linux compatible)
echo "Verifying checksum..."
if [ -f kubectl.sha256 ]; then
    # Read the expected checksum from the file
    expected_checksum=$(cat kubectl.sha256)
    # Calculate the actual checksum
    actual_checksum=$(sha256sum kubectl | cut -d' ' -f1)
    
    if [ "$expected_checksum" = "$actual_checksum" ]; then
        echo "Checksum verification successful"
    else
        echo "Checksum verification failed"
        echo "Expected: $expected_checksum"
        echo "Actual:   $actual_checksum"
        exit 1
    fi
else
    echo "Warning: checksum file not found, skipping verification"
fi

# Make kubectl executable
chmod +x kubectl

# Move to system path
echo "Installing kubectl to /usr/local/bin/..."
mv kubectl /usr/local/bin/
