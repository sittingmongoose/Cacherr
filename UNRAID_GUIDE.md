# PlexCacheUltra - Complete Unraid Guide

## Table of Contents
1. [Quick Start Setup](#quick-start-setup)
2. [Path Configuration (CRITICAL)](#path-configuration-critical)
3. [Docker Setup](#docker-setup)
4. [Troubleshooting](#troubleshooting)
5. [Advanced Configuration](#advanced-configuration)

---

## Quick Start Setup

### What This Fixes
- Removes complex entrypoint scripts that cause permission errors
- Simplifies Docker setup for Unraid
- Eliminates user/group permission issues

### Quick Setup Steps

1. **Copy files to your Unraid server** (e.g., `/mnt/user/appdata/PlexCacheUltra/`)

2. **Create environment file:**
   ```bash
   cp env.example .env
   ```

3. **Edit `.env` file with your settings:**
   ```bash
   nano .env
   ```
   
   **Required settings:**
   - `PLEX_URL`: Your Plex server URL (e.g., `http://192.168.1.100:32400`)
   - `PLEX_TOKEN`: Your Plex token
   - `CACHE_DIR`: Cache directory path (e.g., `/mnt/cache`)
   - `REAL_SOURCE`: Your media source (e.g., `/mnt/user`)
   - `PLEX_SOURCE`: Plex media path (e.g., `/media`)

4. **Start the container:**
   ```bash
   chmod +x start-unraid.sh
   ./start-unraid.sh
   ```

### What Changed
- **Removed**: Complex entrypoint scripts, multiple Dockerfile variants
- **Simplified**: Single Dockerfile that runs as root (no permission issues)
- **Streamlined**: One docker-compose.yml file
- **Easy setup**: Simple startup script for Unraid

### Access
- Web interface: `http://your-server-ip:5443`
- Check logs: `docker-compose logs -f`
- Stop: `docker-compose down`

---

## Path Configuration (CRITICAL)

### Understanding Plex Sources

PlexCacheUltra needs to understand **two different path systems** to work correctly:

1. **Plex Internal Paths** - What Plex thinks the file paths are
2. **Real Filesystem Paths** - Where the files actually exist on your Unraid server

### The Problem

When you mount additional sources in your Plex Docker container, Plex sees files at paths like:
- `/media/Movies/Avatar.mkv`
- `/media/TV/Show/S01E01.mkv`

But on your Unraid server, these files are actually at:
- `/mnt/user/Movies/Avatar.mkv`
- `/mnt/user/TV/Show/S01E01.mkv`

### Required Configuration

You **MUST** set both of these environment variables correctly:

```bash
# What Plex thinks the path is (internal to Plex container)
PLEX_SOURCE=/media

# Where the files actually are on your Unraid server
REAL_SOURCE=/mnt/user
```

### Example Docker Compose Configuration

```yaml
version: '3.8'

services:
  plexcache-ultra:
    build: .
    container_name: plexcache-ultra
    restart: unless-stopped
    ports:
      - "5443:5443"
    environment:
      - PLEX_URL=${PLEX_URL}
      - PLEX_TOKEN=${PLEX_TOKEN}
      - CACHE_DIR=${CACHE_DIR:-/mnt/cache}
      - REAL_SOURCE=${REAL_SOURCE:-/mnt/user}      # ← YOUR ACTUAL MEDIA LOCATION
      - PLEX_SOURCE=${PLEX_SOURCE:-/media}         # ← WHAT PLEX SEES INTERNALLY
      - ADDITIONAL_SOURCES=${ADDITIONAL_SOURCES:-}  # ← EXTRA MOUNTS IF NEEDED
    volumes:
      - ${CACHE_DIR:-/mnt/cache}:${CACHE_DIR:-/mnt/cache}:rw
      - ${REAL_SOURCE:-/mnt/user}:${REAL_SOURCE:-/mnt/user}:rw
      - ${PLEX_SOURCE:-/media}:${PLEX_SOURCE:-/media}:ro
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
```

### How It Works

1. **Plex reports**: `/media/Movies/Avatar.mkv`
2. **System converts**: `/media/Movies/Avatar.mkv` → `/mnt/user/Movies/Avatar.mkv`
3. **File operations**: Performed on the real filesystem path
4. **Cache operations**: Files moved/copied to cache directory

### Common Unraid Paths

| Plex Internal Path | Unraid Real Path | Use Case |
|-------------------|------------------|----------|
| `/media` | `/mnt/user` | Main media share |
| `/media` | `/mnt/cache` | Cache-optimized media |
| `/media` | `/mnt/disk1` | Single disk setup |
| `/media` | `/mnt/remote_share` | Remote/NAS mount |

---

## Docker Setup

### Environment Variables for Unraid

Create a `.env` file:
```bash
# Copy the example
cp env.example .env

# Edit with your Unraid values
nano .env
```

### Typical Unraid values
```bash
PUID=99
PGID=100
CACHE_DIR=/mnt/cache
REAL_SOURCE=/mnt/user
PLEX_SOURCE=/media
```

### Additional Sources

If you have multiple media locations, you can add them. **IMPORTANT**: You must provide **both** the real source paths AND the corresponding plex source paths:

```bash
# Comma-separated list of additional source directories
ADDITIONAL_SOURCES=/mnt/remote_share,/mnt/nas_media

# Comma-separated list of corresponding plex internal paths
ADDITIONAL_PLEX_SOURCES=/media2,/media3
```

### How Additional Sources Work

The system creates a mapping between plex internal paths and real filesystem paths:

| Plex Internal Path | Unraid Real Path | Use Case |
|-------------------|------------------|----------|
| `/media` | `/mnt/user` | Main media share |
| `/media2` | `/mnt/remote_share` | Remote/NAS mount |
| `/media3` | `/mnt/nas_media` | Additional NAS mount |

### Example Configuration

```bash
# Main plex source mapping
PLEX_SOURCE=/media
REAL_SOURCE=/mnt/user

# Additional source mappings
ADDITIONAL_SOURCES=/mnt/remote_share,/mnt/nas_media,/mnt/backup_media
ADDITIONAL_PLEX_SOURCES=/media2,/media3,/media4
```

### ⚠️ Important Rules

1. **Count must match**: The number of `ADDITIONAL_SOURCES` must equal the number of `ADDITIONAL_PLEX_SOURCES`
2. **Order matters**: The first additional source maps to the first additional plex source, and so on
3. **No duplicates**: Each plex source path should be unique
4. **Test first**: Always test with a few files before running full operations

---

## Troubleshooting

### Common Permission Issues

You might get these errors on Unraid:
```
usermod: no changes
chown: changing ownership of '/app/logs': Operation not permitted
chown: changing ownership of '/app/data': Operation not permitted
```

### Root Cause
On Unraid, the container is trying to change ownership of mounted volume directories (`./data` and `./logs`) which are already owned by the host system. The container user doesn't have permission to change ownership of these mounted directories.

### Solution 1: Use the Simple Entrypoint (Recommended)

1. **Use the simple entrypoint:**
   ```bash
   # Copy the simple entrypoint
   cp docker-entrypoint-simple.sh docker-entrypoint.sh
   ```

2. **Rebuild and restart:**
   ```bash
   # Stop container
   docker-compose down

   # Remove old container
   docker-compose rm -f

   # Rebuild
   docker-compose build --no-cache

   # Start
   docker-compose up -d
   ```

### Solution 2: Fix Host Permissions

1. **Run the test script:**
   ```bash
   chmod +x test-unraid-setup.sh
   sudo ./test-unraid-setup.sh
   ```

2. **Manually fix permissions:**
   ```bash
   # Create directories if they don't exist
   mkdir -p ./data ./logs

   # Set ownership to match your PUID/PGID (usually 99:100 on Unraid)
   sudo chown -R 99:100 ./data ./logs
   sudo chmod -R 755 ./data ./logs
   ```

### Solution 3: User Mapping with Special Entrypoint

1. **Add user mapping to docker-compose.yml:**
   ```yaml
   services:
     plexcache-ultra:
       build: .
       container_name: plexcache-ultra
       restart: unless-stopped
       user: "${PUID}:${PGID}"  # Add this line
       ports:
         - "5443:5443"
       # ... rest of your configuration
   ```

2. **Use the user-compatible entrypoint and Dockerfile:**
   ```bash
   # Copy the user-compatible files
   cp docker-entrypoint-user.sh docker-entrypoint.sh
   cp Dockerfile.user Dockerfile
   ```

3. **Rebuild and restart:**
   ```bash
   docker-compose down
   docker-compose rm -f
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Solution 4: Use Docker Run Instead of Docker Compose

Create a simple run command:
```bash
docker run -d \
  --name plexcache-ultra \
  --restart unless-stopped \
  -p 5443:5443 \
  -e PUID=99 \
  -e PGID=100 \
  -e PLEX_URL=your_plex_url \
  -e PLEX_TOKEN=your_plex_token \
  -v /mnt/cache:/mnt/cache:rw \
  -v /mnt/user:/mnt/user:rw \
  -v /media:/media:ro \
  -v ./data:/app/data:rw \
  -v ./logs:/app/logs:rw \
  plexcache-ultra:latest
```

---

## Advanced Configuration

### Verification Steps

1. **Check your Plex container mounts:**
   ```bash
   docker exec -it your-plex-container ls -la /media
   ```

2. **Verify the real paths exist:**
   ```bash
   ls -la /mnt/user/Movies
   ls -la /mnt/user/TV
   ```

3. **Test the conversion:**
   - Plex path: `/media/Movies/Avatar.mkv`
   - Should convert to: `/mnt/user/Movies/Avatar.mkv`
   - File should exist at the converted path

### Debugging Steps

1. **Check container logs:**
   ```bash
   docker-compose logs -f plexcache-ultra
   ```

2. **Check container status:**
   ```bash
   docker-compose ps
   ```

3. **Enter container to debug:**
   ```bash
   docker-compose exec plexcache-ultra bash
   ```

4. **Check user inside container:**
   ```bash
   docker-compose exec plexcache-ultra id
   docker-compose exec plexcache-ultra whoami
   ```

### Common Unraid Issues

#### Issue: Container won't start
- Check if ports are already in use
- Verify PUID/PGID exist on host
- Check Docker daemon status

#### Issue: Permission denied on mounted volumes
- Host directories don't exist
- Wrong ownership on host directories
- SELinux/AppArmor restrictions

#### Issue: User/group modification fails
- Container running as non-root
- Host user/group doesn't exist
- UID/GID conflicts

#### Issue: Entrypoint permission denied
- Container running as non-root user from start
- Entrypoint script not executable by all users
- Use Solution 3 (User Mapping with Special Entrypoint)

### Example .env File

```bash
# Plex Configuration
PLEX_URL=http://192.168.1.100:32400
PLEX_TOKEN=your-plex-token-here

# Path Configuration (CRITICAL FOR UNRAID)
PLEX_SOURCE=/media                    # What Plex sees
REAL_SOURCE=/mnt/user                 # Where files actually are
CACHE_DIR=/mnt/cache                  # Cache location
ADDITIONAL_SOURCES=/mnt/remote_share  # Extra sources

# Other settings...
LOG_LEVEL=INFO
NUMBER_EPISODES=5
DAYS_TO_MONITOR=99
```

---

## Final Notes

1. **Always run test-unraid-setup.sh first** to verify your environment
2. **Use the simple entrypoint** for fewer permission issues
3. **Check host permissions** before starting the container
4. **Verify PUID/PGID** match your Unraid user/group
5. **Rebuild without cache** when making changes
6. **Solution 3 is best for user mapping approach**

## Key Points

✅ **ALWAYS set both `PLEX_SOURCE` and `REAL_SOURCE`**  
✅ **`PLEX_SOURCE` should match your Plex container mounts**  
✅ **`REAL_SOURCE` should point to actual Unraid filesystem paths**  
✅ **Test with a few files before running full operations**  
✅ **Check logs for path conversion errors**  

This configuration ensures PlexCacheUltra can properly translate between Plex's internal paths and your actual filesystem, enabling all caching operations to work correctly.

## Still Having Issues?

If none of these solutions work:

1. Check Unraid Community Applications for similar containers
2. Verify Docker version compatibility
3. Check Unraid system logs
4. Consider running as root temporarily for testing
5. Post logs in the Unraid forums
