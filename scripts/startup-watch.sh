#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting porthole in watch mode${NC}"
echo "=============================================="

# Ensure output directory exists
mkdir -p /app/output

# Get refresh interval from environment variable (default 300 seconds)
REFRESH_INTERVAL="${REFRESH_INTERVAL:-300}"

# Initial service discovery and configuration generation
echo -e "${YELLOW}🔍 Performing initial service discovery...${NC}"
python -m porthole.porthole generate || {
    echo -e "${RED}❌ Initial service discovery failed, continuing anyway...${NC}"
}

echo -e "${GREEN}✅ Initial configuration complete${NC}"

# Start the watch mode for continuous updates
echo -e "${BLUE}👀 Starting watch mode with ${REFRESH_INTERVAL}s interval${NC}"
python -m porthole.porthole watch --interval "${REFRESH_INTERVAL}" &
WATCH_PID=$!

# Function to cleanup background processes
cleanup() {
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $WATCH_PID 2>/dev/null || true
    wait $WATCH_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Shutdown complete${NC}"
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for watch process to exit
wait $WATCH_PID