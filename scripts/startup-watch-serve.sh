#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting k8s-service-proxy in watch+serve mode${NC}"
echo "==============================================="

# Ensure output directory exists
mkdir -p /app/output

# Get refresh interval from environment variable (default 300 seconds)
REFRESH_INTERVAL="${REFRESH_INTERVAL:-300}"

echo -e "${BLUE}🌐 Starting HTTP server on 0.0.0.0:6060${NC}"
python -m porthole.porthole serve --host 0.0.0.0 --port 6060 &
SERVER_PID=$!

echo -e "${BLUE}👀 Starting watch mode with ${REFRESH_INTERVAL}s interval${NC}"
python -m porthole.porthole watch --interval "${REFRESH_INTERVAL}" &
WATCH_PID=$!

# Function to cleanup background processes
cleanup() {
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $SERVER_PID $WATCH_PID 2>/dev/null || true
    wait $SERVER_PID $WATCH_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Shutdown complete${NC}"
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for either process to exit
wait $SERVER_PID $WATCH_PID