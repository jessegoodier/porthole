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

# Initial service discovery and configuration generation
echo -e "${YELLOW}🔍 Performing initial service discovery...${NC}"
python -m porthole.porthole generate || {
    echo -e "${RED}❌ Initial service discovery failed, continuing with serve mode...${NC}"
}

echo -e "${GREEN}✅ Initial configuration complete${NC}"

# Start the HTTP server
echo -e "${BLUE}🌐 Starting HTTP server on 0.0.0.0:6060${NC}"
exec python -m porthole.porthole serve --host 0.0.0.0 --port 6060