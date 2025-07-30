#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting porthole with nginx${NC}"
echo "=============================================="

# Ensure output directory exists
mkdir -p /app/generated-output /app/web-root

# Get refresh interval from environment variable (default 300 seconds)
REFRESH_INTERVAL="${REFRESH_INTERVAL:-300}"

# Set working directory
cd /app

# Initial service discovery and configuration generation
echo -e "${YELLOW}🔍 Performing initial service discovery...${NC}"
python3 -m porthole.porthole generate --output-dir /app/generated-output || {
    echo -e "${RED}❌ Initial service discovery failed, continuing anyway...${NC}"
}

echo -e "${GREEN}✅ Initial configuration complete${NC}"

# Copy static files to shared configs (should already be done by init container)
echo -e "${YELLOW}📁 Ensuring static files are available...${NC}"
if [ ! -f "/app/web-root/index.html" ]; then
    echo -e "${YELLOW}📁 Copying static files from source...${NC}"
    cp -r /app/src/porthole/static/* /app/web-root/ || {
        echo -e "${RED}❌ Failed to copy static files${NC}"
    }
fi

# Check if nginx config was generated and start nginx
if [ -f "/app/generated-output/nginx.conf" ]; then
    echo -e "${YELLOW}🌐 Starting nginx with generated config...${NC}"
    # Create PID file directory if it doesn't exist (use tmp instead of /var/run)
    mkdir -p /tmp
    # Start nginx with the generated configuration and create PID file manually
    nginx -c /app/generated-output/nginx.conf -g "daemon off;" &
    NGINX_PID=$!
    # Write the PID to the expected location for reload operations
    echo $NGINX_PID > /tmp/nginx.pid
    echo -e "${GREEN}✅ Nginx started with PID: $NGINX_PID${NC}"
else
    echo -e "${RED}❌ Nginx configuration not found, starting with default config...${NC}"
    # Create PID file directory if it doesn't exist (use tmp instead of /var/run)
    mkdir -p /tmp
    # Start nginx with default configuration on port 7070
    nginx -g "daemon off;" &
    NGINX_PID=$!
    # Write the PID to the expected location for reload operations
    echo $NGINX_PID > /tmp/nginx.pid
    echo -e "${GREEN}✅ Nginx started with default config, PID: $NGINX_PID${NC}"
fi

# Start nginx config watcher to reload on changes
echo -e "${BLUE}👀 Starting nginx config watcher...${NC}"
python3 -m porthole.nginx_reloader &
WATCHER_PID=$!

# Start the watch mode for continuous updates
echo -e "${BLUE}👀 Starting watch mode with ${REFRESH_INTERVAL}s interval${NC}"
python3 -m porthole.porthole watch --interval "${REFRESH_INTERVAL}" &
WATCH_PID=$!

# Function to cleanup background processes
cleanup() {
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $WATCH_PID 2>/dev/null || true
    kill $WATCHER_PID 2>/dev/null || true
    kill $NGINX_PID 2>/dev/null || true
    nginx -s quit 2>/dev/null || true
    # Clean up PID file
    rm -f /tmp/nginx.pid 2>/dev/null || true
    wait $WATCH_PID 2>/dev/null || true
    wait $WATCHER_PID 2>/dev/null || true
    wait $NGINX_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Shutdown complete${NC}"
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for any process to exit
wait $WATCH_PID $WATCHER_PID $NGINX_PID 