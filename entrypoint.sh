#!/bin/bash
set -e

echo "Entrypoint script starting..."

# Always run as root initially to ensure proper directory setup
if [ "$(id -u)" != "0" ]; then
    echo "Entrypoint must run as root to set up directories properly"
    exit 1
fi

echo "Running as root, setting up directories..."

# SECURITY: Create necessary directories without modifying mounted volumes
# Only create subdirectories within potentially mounted paths
mkdir -p /config/logs /config/data /config/temp /cache 2>/dev/null || true

# SECURITY CRITICAL: Only set ownership on application directory
# NEVER modify ownership of /config or /cache as they may be mounted from host
if [ -d "/app" ] && [ ! -L "/app" ]; then
    echo "Setting ownership on application directory: /app"
    chown -R cacherr:cacherr /app
else
    echo "WARNING: /app not found or is a symlink - skipping ownership change"
fi

# SECURITY: Ensure cacherr user can write to required subdirectories without
# changing ownership of potentially mounted parent directories
# Check if we can write to subdirectories and create them with proper user
for subdir in "/config/logs" "/config/data" "/config/temp" "/cache"; do
    if [ -d "$subdir" ]; then
        # Test if directory is writable by attempting to create a test file
        if touch "$subdir/.write_test" 2>/dev/null; then
            rm -f "$subdir/.write_test"
            echo "Directory $subdir is writable"
        else
            echo "WARNING: Directory $subdir is not writable by cacherr user"
            # Try to set permissions on just this subdirectory if possible
            chown cacherr:cacherr "$subdir" 2>/dev/null || echo "Cannot modify ownership of $subdir"
            chmod 755 "$subdir" 2>/dev/null || echo "Cannot modify permissions of $subdir"
        fi
    fi
done

echo "Directory permissions configured securely, switching to cacherr user..."

# Switch to cacherr user and execute the command
# Use exec to replace the current process
exec gosu cacherr "$@"
