#!/bin/bash

# Script to create a ConfigMap from all files in a folder
# Usage: ./create-configmap.sh <folder_path> <configmap_name> [namespace]

set -e

# Check if required arguments are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <folder_path> <configmap_name> [namespace]"
    echo "Example: $0 ./config my-configmap"
    echo "Example: $0 ./config my-configmap my-namespace"
    exit 1
fi

FOLDER_PATH="$1"
CONFIGMAP_NAME="$2"
NAMESPACE="${3:-default}"

# Check if folder exists
if [ ! -d "$FOLDER_PATH" ]; then
    echo "Error: Folder '$FOLDER_PATH' does not exist"
    exit 1
fi

# Check if folder is empty
if [ -z "$(ls -A "$FOLDER_PATH")" ]; then
    echo "Error: Folder '$FOLDER_PATH' is empty"
    exit 1
fi

echo "Creating ConfigMap '$CONFIGMAP_NAME' from files in '$FOLDER_PATH' in namespace '$NAMESPACE'"

# Create ConfigMap from folder
kubectl create configmap "$CONFIGMAP_NAME" \
    --from-file="$FOLDER_PATH" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml

echo ""
echo "To apply this ConfigMap, run:"
echo "kubectl create configmap $CONFIGMAP_NAME --from-file=$FOLDER_PATH --namespace=$NAMESPACE"
echo ""
echo "Or to save to a file first:"
echo "kubectl create configmap $CONFIGMAP_NAME --from-file=$FOLDER_PATH --namespace=$NAMESPACE --dry-run=client -o yaml > ${CONFIGMAP_NAME}-configmap.yaml" 