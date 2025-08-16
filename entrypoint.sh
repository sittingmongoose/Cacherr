#!/bin/bash
set -e

# Always run as root initially to ensure proper directory setup
if [ "$(id -u)" != "0" ]; then
    echo "Entrypoint must run as root to set up directories properly"
    exit 1
fi

# Ensure config directories exist and have proper permissions
mkdir -p /config/logs /config/data /cache

# Set proper ownership for all directories
chown -R plexcache:plexcache /app /config /cache

# Switch to plexcache user and execute the command
exec gosu plexcache "$@"
