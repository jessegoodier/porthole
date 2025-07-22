#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting porthole${NC}"
echo "=================================="

# Ensure output directory exists
mkdir -p /app/output

# Service discovery and configuration generation
echo -e "${YELLOW}🔍 Performing service discovery...${NC}"
python -m porthole.porthole generate || {
    echo -e "${RED}❌ Service discovery failed${NC}"
    exit 1
}

# Copy the configmap to the output directory
cp -r /app/src/porthole/static/* /app/shared-configs/

echo -e "${GREEN}✅ Configuration init complete ${NC}"
