#!/bin/bash
set -e

echo "Entrypoint script starting..."

# Always run as root initially to ensure proper directory setup
if [ "$(id -u)" != "0" ]; then
    echo "Entrypoint must run as root to set up directories properly"
    exit 1
fi

echo "Running as root, setting up directories..."

# Ensure config directories exist and have proper permissions
mkdir -p /config/logs /config/data /cache

# Set proper ownership for all directories
chown -R plexcache:plexcache /app /config /cache

echo "Directories set up, switching to plexcache user..."

# Switch to plexcache user and execute the command
# Use exec to replace the current process
exec gosu plexcache "$@"
