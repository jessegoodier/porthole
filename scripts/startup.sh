#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting k8s-service-proxy${NC}"
echo "=================================="

# Ensure output directory exists
mkdir -p /app/output

# Service discovery and configuration generation
echo -e "${YELLOW}🔍 Performing service discovery...${NC}"
python -m porthole.porthole generate || {
    echo -e "${RED}❌ Service discovery failed${NC}"
    exit 1
}

echo -e "${GREEN}✅ Configuration complete - files served by nginx${NC}"

# Keep container running (nginx handles web serving)
echo -e "${BLUE}💤 Keeping container alive - nginx serves content${NC}"
while true; do
    sleep 3600
done