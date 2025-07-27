#!/bin/bash

# OpenResty configuration file watcher and reloader
# This script monitors for changes in nginx configuration files and reload triggers
# and reloads OpenResty when changes are detected

set -euo pipefail

# Configuration
WATCH_DIR=${WATCH_DIR:-"/app/generated-output"}
LOG_PREFIX="openresty-watcher"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$LOG_PREFIX] $1"
}

reload_openresty() {
    log "Configuration change detected, testing and reloading..."
    
    # Test configuration first
    if /opt/bitnami/openresty/bin/openresty -t; then
        # Configuration is valid, reload
        /opt/bitnami/openresty/bin/openresty -s reload
        log "Configuration reloaded successfully"
    else
        log "ERROR: Configuration test failed, not reloading"
    fi
}

# Check if inotify-tools is available
if ! command -v inotifywait &> /dev/null; then
    log "ERROR: inotifywait not found. Please install inotify-tools package."
    exit 1
fi

# Ensure watch directory exists
if [ ! -d "$WATCH_DIR" ]; then
    log "ERROR: Watch directory does not exist: $WATCH_DIR"
    exit 1
fi

log "Starting OpenResty configuration watcher on directory: $WATCH_DIR"

# Watch for file modifications
while inotifywait -e modify,create,move "$WATCH_DIR" --format '%w%f %e'; do
    # Check if the modified file is a config file or trigger file
    if [[ "$file" == *.conf ]] || [[ "$file" == *nginx-reload.trigger ]]; then
        reload_openresty
    fi
done