# Unraid Permission Troubleshooting Guide

## The Problem
You're getting these errors on Unraid:
```
usermod: no changes
chown: changing ownership of '/app/logs': Operation not permitted
chown: changing ownership of '/app/data': Operation not permitted
```

## Root Cause
On Unraid, the container is trying to change ownership of mounted volume directories (`./data` and `./logs`) which are already owned by the host system. The container user doesn't have permission to change ownership of these mounted directories.

## Solution 1: Use the Simple Entrypoint (Recommended)

### Step 1: Use the simple entrypoint
```bash
# Copy the simple entrypoint
cp docker-entrypoint-simple.sh docker-entrypoint.sh
```

### Step 2: Rebuild and restart
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

## Solution 2: Use the Alternative Dockerfile

### Step 1: Use the Unraid-specific Dockerfile
```bash
# Copy the alternative Dockerfile
cp Dockerfile.unraid Dockerfile
```

### Step 2: Rebuild and restart
```bash
docker-compose down
docker-compose rm -f
docker-compose build --no-cache
docker-compose up -d
```

## Solution 3: Fix Host Permissions

### Step 1: Run the test script
```bash
chmod +x test-unraid-setup.sh
sudo ./test-unraid-setup.sh
```

### Step 2: Manually fix permissions
```bash
# Create directories if they don't exist
mkdir -p ./data ./logs

# Set ownership to match your PUID/PGID (usually 99:100 on Unraid)
sudo chown -R 99:100 ./data ./logs
sudo chmod -R 755 ./data ./logs
```

## Solution 4: User Mapping with Special Entrypoint (NEW - Try This!)

### Step 1: Add user mapping to docker-compose.yml
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

### Step 2: Use the user-compatible entrypoint and Dockerfile
```bash
# Copy the user-compatible files
cp docker-entrypoint-user.sh docker-entrypoint.sh
cp Dockerfile.user Dockerfile
```

### Step 3: Rebuild and restart
```bash
docker-compose down
docker-compose rm -f
docker-compose build --no-cache
docker-compose up -d
```

## Solution 5: Use Docker Run Instead of Docker Compose

### Create a simple run command
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

## Environment Variables for Unraid

### Create a .env file
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

## Debugging Steps

### 1. Check container logs
```bash
docker-compose logs -f plexcache-ultra
```

### 2. Check container status
```bash
docker-compose ps
```

### 3. Enter container to debug
```bash
docker-compose exec plexcache-ultra bash
```

### 4. Check user inside container
```bash
docker-compose exec plexcache-ultra id
docker-compose exec plexcache-ultra whoami
```

## Common Unraid Issues

### Issue: Container won't start
- Check if ports are already in use
- Verify PUID/PGID exist on host
- Check Docker daemon status

### Issue: Permission denied on mounted volumes
- Host directories don't exist
- Wrong ownership on host directories
- SELinux/AppArmor restrictions

### Issue: User/group modification fails
- Container running as non-root
- Host user/group doesn't exist
- UID/GID conflicts

### Issue: Entrypoint permission denied
- Container running as non-root user from start
- Entrypoint script not executable by all users
- Use Solution 4 (User Mapping with Special Entrypoint)

## Final Notes

1. **Always run test-unraid-setup.sh first** to verify your environment
2. **Use the simple entrypoint** for fewer permission issues
3. **Check host permissions** before starting the container
4. **Verify PUID/PGID** match your Unraid user/group
5. **Rebuild without cache** when making changes
6. **Solution 4 is best for user mapping approach**

## Still Having Issues?

If none of these solutions work:

1. Check Unraid Community Applications for similar containers
2. Verify Docker version compatibility
3. Check Unraid system logs
4. Consider running as root temporarily for testing
5. Post logs in the Unraid forums
