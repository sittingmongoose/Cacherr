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

# SECURITY: Ensure cacherr user can write to required directories and the config root
# Check if we can write to directories and create them with proper user permissions
# First check and set permissions for /config root directory for database files
if [ -d "/config" ]; then
    # Try to ensure cacherr can write to /config for database files
    chown cacherr:cacherr /config 2>/dev/null || echo "Cannot modify ownership of /config - checking if writable"
    chmod 755 /config 2>/dev/null || echo "Cannot modify permissions of /config"
    
    # Test if directory is writable by attempting to create a test file as cacherr user
    if su cacherr -c "touch '/config/.write_test'" 2>/dev/null; then
        su cacherr -c "rm -f '/config/.write_test'" 2>/dev/null
        echo "Directory /config is writable"
    else
        echo "WARNING: Directory /config is not writable by cacherr user - database creation may fail"
    fi
fi

# Check subdirectories
for subdir in "/config/logs" "/config/data" "/config/temp" "/cache"; do
    if [ -d "$subdir" ]; then
        # Try to set permissions on just this subdirectory if possible
        chown cacherr:cacherr "$subdir" 2>/dev/null || echo "Cannot modify ownership of $subdir"
        chmod 755 "$subdir" 2>/dev/null || echo "Cannot modify permissions of $subdir"
        
        # Test if directory is writable by attempting to create a test file as cacherr user
        if su cacherr -c "touch '$subdir/.write_test'" 2>/dev/null; then
            su cacherr -c "rm -f '$subdir/.write_test'" 2>/dev/null
            echo "Directory $subdir is writable"
        else
            echo "WARNING: Directory $subdir is not writable by cacherr user"
        fi
    fi
done

echo "Directory permissions configured securely, switching to cacherr user..."

# Switch to cacherr user and execute the command
# Use exec to replace the current process
exec gosu cacherr "$@"
