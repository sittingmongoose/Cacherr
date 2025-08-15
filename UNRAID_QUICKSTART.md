# PlexCacheUltra - Unraid Quick Start

## What This Fixes
- Removes complex entrypoint scripts that cause permission errors
- Simplifies Docker setup for Unraid
- Eliminates user/group permission issues

## Quick Setup

1. **Copy files to your Unraid server** (e.g., `/mnt/user/appdata/PlexCacheUltra/`)

2. **Create environment file:**
   ```bash
   cp env.simple .env
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

## What Changed
- **Removed**: Complex entrypoint scripts, multiple Dockerfile variants
- **Simplified**: Single Dockerfile that runs as root (no permission issues)
- **Streamlined**: One docker-compose.yml file
- **Easy setup**: Simple startup script for Unraid

## Access
- Web interface: `http://your-server-ip:5443`
- Check logs: `docker-compose logs -f`
- Stop: `docker-compose down`

## Troubleshooting

### If Docker Build Fails
1. **Check file permissions:**
   ```bash
   chmod 644 Dockerfile
   chmod 644 docker-compose.yml
   ```

2. **Verify you're in the right directory:**
   ```bash
   pwd
   ls -la
   ```

3. **Try building manually:**
   ```bash
   docker build -t plexcache-ultra .
   ```

### Permission Issues
1. Make sure `start-unraid.sh` is executable: `chmod +x start-unraid.sh`
2. Check that your paths in `.env` are correct
3. Ensure Docker has access to your media directories

## Why This Works Better
- No complex user/group switching
- No entrypoint script permission issues
- Simple, reliable container startup
- Standard Docker practices that work on all systems
