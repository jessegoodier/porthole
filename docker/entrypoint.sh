#!/bin/sh
# vim:sw=4:ts=4:et

set -euo pipefail
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# NGINX
/docker-entrypoint.d/entrypoint-nginx.sh
echo -e "${YELLOW}🌐 Starting nginx with generated config...${NC}"
# Start nginx with the generated configuration and create PID file manually
nginx -c /etc/nginx/nginx.conf -g "daemon off;" &
NGINX_PID=$!
echo $NGINX_PID > /tmp/nginx.pid
echo -e "${GREEN}✅ NGINX started with PID: $NGINX_PID${NC}"


# Python app
echo -e "${BLUE}🚀 porthole entrypoint${NC}"
echo "=============================="

# Get startup mode from environment variable (default to "generate")
STARTUP_MODE="${STARTUP_MODE:-generate}"

echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "  Startup Mode: ${STARTUP_MODE}"
echo -e "  Refresh Interval: ${REFRESH_INTERVAL:-300}s"
echo -e "  Debug: ${DEBUG:-false}"
echo -e "  Output Dir: ${OUTPUT_DIR:-/app/output}"
echo ""

uv pip install /app

# Start porthole config watcher to reload on changes
echo -e "${BLUE}👀 Starting nginx config watcher...${NC}"
python3 -m porthole.nginx_reloader &
NGINX_RELOADER_PID=$!

# Start the watch mode for continuous updates
echo -e "${BLUE}👀 Starting watch mode with ${REFRESH_INTERVAL}s interval${NC}"
python3 -m porthole.porthole watch --interval "${REFRESH_INTERVAL}" &
PORTHOLE_PID=$!

# Set up signal handlers
trap "kill $PORTHOLE_PID $NGINX_RELOADER_PID" SIGTERM SIGINT

# Wait for any process to exit
wait $PORTHOLE_PID $NGINX_RELOADER_PID