#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 k8s-service-proxy entrypoint${NC}"
echo "=============================="

# Get startup mode from environment variable (default to "generate")
STARTUP_MODE="${STARTUP_MODE:-generate}"

echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "  Startup Mode: ${STARTUP_MODE}"
echo -e "  Refresh Interval: ${REFRESH_INTERVAL:-300}s"
echo -e "  Debug: ${DEBUG:-false}"
echo -e "  Output Dir: ${OUTPUT_DIR:-/app/output}"
echo ""

case "$STARTUP_MODE" in
    "watch")
        echo -e "${BLUE}🔄 Starting in watch mode (continuous updates)${NC}"
        exec /app/scripts/startup-watch.sh
        ;;
    "generate")
        echo -e "${BLUE}⚡ Starting in generate mode (one-time config, nginx serves content)${NC}"
        exec /app/scripts/startup.sh
        ;;
    *)
        echo -e "${RED}❌ Unknown startup mode: ${STARTUP_MODE}${NC}"
        echo -e "${YELLOW}Valid modes: generate, watch${NC}"
        exit 1
        ;;
esac