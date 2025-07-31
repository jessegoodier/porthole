#!/bin/sh
# vim:sw=4:ts=4:et

set -euo pipefail
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# NGINX config
# https://github.com/nginx/docker-nginx-unprivileged/blob/main/stable/debian/docker-entrypoint.sh
entrypoint_log() {
    if [ -z "${NGINX_ENTRYPOINT_QUIET_LOGS:-}" ]; then
        echo -e "${GREEN}$@${NC}"
    fi
}

if /usr/bin/find "/docker-entrypoint.d/" -mindepth 1 -maxdepth 1 -type f -print -quit 2>/dev/null | read v; then
    entrypoint_log "$0: found nginx startup script in /docker-entrypoint.d/ , will attempt to perform configuration"

    # only run scripts that start with a number
    find "/docker-entrypoint.d/" -follow -type f -name "[0-9]*" -print | sort -V | while read -r f; do
        # Goal is to tune worker processes for kubernetes using standard nginx scripts
        entrypoint_log "$0: Launching $f";
        "$f"
    done

    entrypoint_log "$0: Configuration complete; ready for start up"
fi

echo -e "${YELLOW}📁 Copying nginx config from source...${NC}"
cp -r /app/src/porthole/nginx/* /etc/nginx/ || {
    echo -e "${RED}❌ Failed to copy nginx config${NC}"
}
touch /app/generated-output/locations.conf