# Migration Guide: PlexCache → PlexCacheUltra

This guide will help you migrate from the original PlexCache script to the new Docker-optimized PlexCacheUltra system.

## 🚀 What's New in PlexCacheUltra

### Major Improvements
- **Docker-First Design**: Built specifically for containerized deployment
- **Web Dashboard**: Beautiful web interface for monitoring and control
- **Environment-Based Configuration**: No more editing Python files
- **Better Error Handling**: Comprehensive logging and error recovery
- **Health Monitoring**: Docker health checks and monitoring endpoints
- **Scheduled Operations**: Automatic periodic execution
- **Modern Architecture**: Clean separation of concerns and modular design

### 🆕 New Features in v2.1

**Enhanced Real-Time Plex Watching:**
- **Cache Removal Timing**: Automatically remove media from cache after a configurable time period
- **Watchlist Respect**: Keep media in cache if other users have it in their watchlists
- **User Inactivity Exclusion**: Exclude users from caching decisions based on configurable inactivity thresholds
- **Enhanced Dashboard**: Real-time display of cache removal schedule and user activity status

**Flexible Destination Paths:**
- Specify custom cache destinations independent of main cache directory
- Support for different storage locations and drive configurations
- Enhanced path resolution and validation

**Multiple Source Support:**
- Access media from additional mounted shares and network drives
- Automatic scanning of multiple source locations
- Improved media discovery and file matching

**Test Mode:**
- Preview operations without moving files
- Detailed file size analysis and totals
- Safe operation planning and validation

**🆕 Trakt.tv Integration:**
- Automatically cache trending movies from Trakt.tv
- Dynamic monitoring of trending movie lists
- Configurable movie count and check intervals
- Full web dashboard integration

**🆕 Copy vs Move Modes with Symlink Integration:**
- **COPY_TO_CACHE**: Choose between copying or moving files to cache
- **DELETE_FROM_CACHE_WHEN_DONE**: Delete from cache instead of moving back
- **USE_SYMLINKS_FOR_CACHE**: Create symlinks so Plex automatically uses cached files
- **Two Workflows**: Traditional move mode vs. copy+symlink mode for automatic Plex cache usage

### Key Benefits
- **Easier Deployment**: One command to start with Docker Compose
- **Better Monitoring**: Real-time status and statistics
- **Simplified Configuration**: Environment variables instead of code changes
- **Improved Reliability**: Better error handling and recovery
- **Cross-Platform**: Works on any system with Docker
- **🆕 Safe Operation Planning**: Test mode for previewing operations
- **🆕 Flexible Storage**: Custom destinations and multiple sources
- **🆕 Automatic Plex Cache Usage**: Symlink integration for transparent cache access

## 📋 Migration Steps

### Step 1: Backup Your Current Setup

```bash
# Backup your current PlexCache files
cp plexcache_settings.json plexcache_settings.json.backup
cp plexcache.py plexcache.py.backup
```

### Step 2: Use the Migration Script

The easiest way to migrate is to use the included migration script:

```bash
# Run the migration script
python migrate_from_old.py
```

This will:
- Read your existing `plexcache_settings.json`
- Convert all settings to environment variables
- Create a `.env` file ready for PlexCacheUltra
- Include new optional features for configuration

### Step 3: Review and Update Configuration

After running the migration script, review the generated `.env` file:

```bash
# Edit the .env file with your actual values
nano .env
```

**Important**: Update these values with your actual configuration:
- `PLEX_URL`: Your Plex server URL
- `PLEX_TOKEN`: Your Plex API token
- `CACHE_DIR`: Your cache drive path (usually `/mnt/cache`)
- `REAL_SOURCE`: Your array drive path (usually `/mnt/user`)
- `PLEX_SOURCE`: Your Plex library path (usually `/media`)

**🆕 Trakt.tv Setup** (Optional):
If you want to enable Trakt.tv integration:
1. Visit [Trakt.tv API Applications](https://trakt.tv/oauth/applications)
2. Create a new application
3. Copy your Client ID and Client Secret
4. Set `TRAKT_ENABLED=true` and add your credentials

**🆕 New Optional Configuration**:
- `CACHE_DESTINATION`: Custom destination for cached media (optional)
- `ADDITIONAL_SOURCES`: Comma-separated list of additional source directories
- `TEST_MODE`: Enable test mode for safe operation preview
- `TRAKT_ENABLED`: Enable Trakt.tv trending movies integration
- `TRAKT_CLIENT_ID`: Your Trakt.tv API client ID
- `TRAKT_CLIENT_SECRET`: Your Trakt.tv API client secret
- `TRAKT_TRENDING_MOVIES_COUNT`: Number of trending movies to cache
- `TRAKT_CHECK_INTERVAL`: How often to check for new trending movies

**🆕 Copy vs Move Modes**:
- `COPY_TO_CACHE`: Copy files to cache instead of moving (preserves originals)
- `DELETE_FROM_CACHE_WHEN_DONE`: Delete from cache when done (vs moving back)
- `USE_SYMLINKS_FOR_CACHE`: Create symlinks so Plex automatically uses cached files
- `MOVE_WITH_SYMLINKS`: Enable hybrid move+symlink mode (frees source space + Plex cache)

### Step 4: Deploy PlexCacheUltra

#### Option A: Using Docker Compose (Recommended)

```bash
# Start PlexCacheUltra
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option B: Using the Startup Script

```bash
# On Linux/macOS
./start.sh start

# On Windows
start.bat start

# Check status
./start.sh status  # Linux/macOS
start.bat status   # Windows
```

#### Option C: Manual Docker Commands

```bash
# Build the image
docker build -t plexcache-ultra .

# Run the container
docker run -d \
  --name plexcache-ultra \
  --restart unless-stopped \
  -p 5443:5443 \
  --env-file .env \
  -v /mnt/cache:/mnt/cache \
  -v /mnt/user:/mnt/user \
  -v /media:/media \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  plexcache-ultra:latest
```

### Step 5: Access the Web Dashboard

Open your browser and navigate to:
```
http://your-server:5443
```

## 🆕 Understanding Copy vs Move Modes

### Traditional Move Mode (Default)
This is how the original PlexCache worked:
```bash
# Files are moved to cache
COPY_TO_CACHE=false
USE_SYMLINKS_FOR_CACHE=false

# Workflow:
# 1. Move file from /mnt/user/Movie.mkv → /mnt/cache/Movie.mkv
# 2. Plex continues reading from /mnt/user/Movie.mkv (file not there)
# 3. After watching, move file back: /mnt/cache/Movie.mkv → /mnt/user/Movie.mkv
```

**Limitation**: Plex doesn't actually use the cached files - it still tries to read from the original location.

### 🆕 Copy + Symlink Mode (Recommended)
New workflow that makes Plex automatically use cached files:
```bash
# Files are copied to cache and symlinks created
COPY_TO_CACHE=true
DELETE_FROM_CACHE_WHEN_DONE=true
USE_SYMLINKS_FOR_CACHE=true

# Workflow:
# 1. Copy file from /mnt/user/Movie.mkv → /mnt/cache/Movie.mkv
# 2. Create symlink: /mnt/user/Movie.mkv → /mnt/cache/Movie.mkv
# 3. Plex follows symlink and reads from fast cache!
# 4. After watching, delete from cache and remove symlink
# 5. Original file remains untouched in /mnt/user/Movie.mkv
```

**Benefits**:
- ✅ **Plex automatically uses cache** - no manual path updates
- ✅ **Originals preserved** - source files never moved
- ✅ **Perfect for NAS setups** - network shares remain untouched
- ✅ **Multiple users** - same files accessible from multiple locations

### 🆕 Move + Symlink Mode (Hybrid - Best of Both Worlds)
New workflow that combines space savings with Plex cache benefits:
```bash
# Files are moved to cache and symlinks created back
COPY_TO_CACHE=false
DELETE_FROM_CACHE_WHEN_DONE=true
USE_SYMLINKS_FOR_CACHE=false  # Not used in hybrid mode
MOVE_WITH_SYMLINKS=true

# Workflow:
# 1. Move file from /mnt/user/Movie.mkv → /mnt/cache/Movie.mkv
# 2. Create symlink back: /mnt/user/Movie.mkv → /mnt/cache/Movie.mkv
# 3. Plex follows symlink and reads from fast cache!
# 4. After watching, delete from cache and remove symlink
# 5. Source space is freed, but Plex library remains intact
```

**Benefits**:
- ✅ **Plex automatically uses cache** - no manual path updates
- ✅ **Frees source space** - files moved to cache, not copied
- ✅ **No library scans** - Plex follows symlinks without triggering rescans
- ✅ **Best performance** - combines space savings with cache benefits
- ✅ **Perfect for limited storage** - maximize cache usage while keeping Plex happy

## 🔄 Configuration Mapping

### Old Settings → New Environment Variables

| Old Setting | New Variable | Default Value |
|-------------|--------------|---------------|
| `PLEX_URL` | `PLEX_URL` | Required |
| `PLEX_TOKEN` | `PLEX_TOKEN` | Required |
| `cache_dir` | `CACHE_DIR` | `/mnt/cache` |
| `real_source` | `REAL_SOURCE` | `/mnt/user` |
| `plex_source` | `PLEX_SOURCE` | `/media` |
| `number_episodes` | `NUMBER_EPISODES` | `5` |
| `days_to_monitor` | `DAYS_TO_MONITOR` | `99` |
| `watchlist_toggle` | `WATCHLIST_TOGGLE` | `true` |
| `watchlist_episodes` | `WATCHLIST_EPISODES` | `1` |
| `watchlist_cache_expiry` | `