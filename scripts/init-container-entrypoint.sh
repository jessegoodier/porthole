#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting porthole init container${NC}"
echo "======================================"

# Debug environment
echo -e "${BLUE}📋 Environment Debug:${NC}"
echo "  Python executable: $(which python3 2>/dev/null || echo 'NOT FOUND')"
echo "  Python version: $(python3 --version 2>/dev/null || echo 'NOT AVAILABLE')"
echo "  Python path: ${PYTHONPATH:-NOT SET}"
echo "  PATH: $PATH"
echo ""

# Ensure output directories exist
echo -e "${YELLOW}📁 Creating output directories...${NC}"
mkdir -p /app/generated-output /app/web-root

# Set working directory to ensure imports work correctly
cd /app

# Test porthole import
echo -e "${YELLOW}🧪 Testing porthole import...${NC}"
python3 -c "import porthole; print('✅ porthole imported successfully')" || {
    echo -e "${RED}❌ Failed to import porthole${NC}"
    exit 1
}

# Service discovery and configuration generation
echo -e "${YELLOW}🔍 Performing service discovery...${NC}"
python3 -m porthole.porthole generate --output-dir /app/generated-output || {
    echo -e "${RED}❌ Service discovery failed${NC}"
    exit 1
}

# Copy the configmap to the output directory
cp -r /app/src/porthole/static/* /app/web-root/

echo -e "${GREEN}✅ Configuration init complete ${NC}"
