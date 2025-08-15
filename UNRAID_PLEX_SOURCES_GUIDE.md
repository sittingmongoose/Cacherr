# PlexCacheUltra - Unraid Plex Sources Configuration Guide

## Understanding Plex Sources

PlexCacheUltra needs to understand **two different path systems** to work correctly:

1. **Plex Internal Paths** - What Plex thinks the file paths are
2. **Real Filesystem Paths** - Where the files actually exist on your Unraid server

## The Problem

When you mount additional sources in your Plex Docker container, Plex sees files at paths like:
- `/media/Movies/Avatar.mkv`
- `/media/TV/Show/S01E01.mkv`

But on your Unraid server, these files are actually at:
- `/mnt/user/Movies/Avatar.mkv`
- `/mnt/user/TV/Show/S01E01.mkv`

## Required Configuration

You **MUST** set both of these environment variables correctly:

```bash
# What Plex thinks the path is (internal to Plex container)
PLEX_SOURCE=/media

# Where the files actually are on your Unraid server
REAL_SOURCE=/mnt/user
```

## Example Docker Compose Configuration

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

## How It Works

1. **Plex reports**: `/media/Movies/Avatar.mkv`
2. **System converts**: `/media/Movies/Avatar.mkv` → `/mnt/user/Movies/Avatar.mkv`
3. **File operations**: Performed on the real filesystem path
4. **Cache operations**: Files moved/copied to cache directory

## Common Unraid Paths

| Plex Internal Path | Unraid Real Path | Use Case |
|-------------------|------------------|----------|
| `/media` | `/mnt/user` | Main media share |
| `/media` | `/mnt/cache` | Cache-optimized media |
| `/media` | `/mnt/disk1` | Single disk setup |
| `/media` | `/mnt/remote_share` | Remote/NAS mount |

## Additional Sources

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

This means:
- Plex sees `/media/Movies/Avatar.mkv` → maps to `/mnt/user/Movies/Avatar.mkv`
- Plex sees `/media2/Movies/Inception.mkv` → maps to `/mnt/remote_share/Movies/Inception.mkv`
- Plex sees `/media3/TV/Show/S01E01.mkv` → maps to `/mnt/nas_media/TV/Show/S01E01.mkv`
- Plex sees `/media4/Anime/Attack.mkv` → maps to `/mnt/backup_media/Anime/Attack.mkv`

### ⚠️ Important Rules

1. **Count must match**: The number of `ADDITIONAL_SOURCES` must equal the number of `ADDITIONAL_PLEX_SOURCES`
2. **Order matters**: The first additional source maps to the first additional plex source, and so on
3. **No duplicates**: Each plex source path should be unique
4. **Test first**: Always test with a few files before running full operations

## Verification Steps

1. **Check your Plex container mounts**:
   ```bash
   docker exec -it your-plex-container ls -la /media
   ```

2. **Verify the real paths exist**:
   ```bash
   ls -la /mnt/user/Movies
   ls -la /mnt/user/TV
   ```

3. **Test the conversion**:
   - Plex path: `/media/Movies/Avatar.mkv`
   - Should convert to: `/mnt/user/Movies/Avatar.mkv`
   - File should exist at the converted path

## Troubleshooting

### "File not found" errors
- Check that `REAL_SOURCE` points to where your files actually are
- Verify `PLEX_SOURCE` matches what Plex sees internally
- Ensure the container has read access to your media directories

### Cache operations not working
- Verify both source paths are correctly configured
- Check that the cache directory is writable
- Ensure file permissions allow the container to read/write

### Performance issues
- Use SSD cache for frequently accessed media
- Consider using `ADDITIONAL_SOURCES` for different storage tiers
- Monitor the logs for any path conversion errors

## Example .env File

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

## Key Points

✅ **ALWAYS set both `PLEX_SOURCE` and `REAL_SOURCE`**  
✅ **`PLEX_SOURCE` should match your Plex container mounts**  
✅ **`REAL_SOURCE` should point to actual Unraid filesystem paths**  
✅ **Test with a few files before running full operations**  
✅ **Check logs for path conversion errors**  

This configuration ensures PlexCacheUltra can properly translate between Plex's internal paths and your actual filesystem, enabling all caching operations to work correctly.
