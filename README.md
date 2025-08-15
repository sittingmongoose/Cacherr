# PlexCacheUltra 🎬

A Docker-optimized Plex media caching system designed specifically for Unraid environments. PlexCacheUltra automatically moves frequently accessed media files to fast cache drives and moves watched content back to slower array drives, optimizing your Plex streaming performance.

## ✨ Features

- **Docker-First Design**: Built from the ground up for containerized deployment
- **Unraid Optimized**: Specifically designed for Unraid's cache/array architecture
- **Smart Caching**: Automatically caches onDeck and watchlist media
- **Intelligent Movement**: Moves watched content back to array drives
- **Web Dashboard**: Beautiful web interface for monitoring and control
- **Scheduled Operations**: Configurable automatic execution
- **Multi-User Support**: Handles multiple Plex users and their preferences
- **Subtitle Handling**: Automatically includes subtitle files in operations
- **Notification System**: Discord, Slack, and Unraid notifications
- **Health Monitoring**: Docker health checks and monitoring endpoints
- **🆕 Flexible Destination Paths**: Specify custom destinations for cached media
- **🆕 Multiple Source Support**: Access media from mounted shares and remote sources
- **🆕 Test Mode**: Preview operations without moving files, showing sizes and totals
- **🆕 Real-Time Plex Watching**: Monitor Plex activity in real-time for dynamic caching decisions
- **🆕 Trakt.tv Integration**: Automatically cache trending movies from Trakt.tv
- **🆕 Copy vs Move Modes**: Choose between moving files or copying to cache
- **🆕 Symlink Integration**: Make Plex automatically use cached files

### Trakt.tv Integration

The application can automatically monitor and cache trending movies from [Trakt.tv](https://trakt.tv/movies/trending). This feature:

- Fetches the current trending movies list from Trakt.tv
- Automatically adds new trending movies to the cache list
- Removes movies that are no longer trending
- Configurable number of movies to include (default: 10)
- Configurable check interval (default: 1 hour)
- Respects existing caching rules and user preferences

#### Configuration

To enable Trakt.tv integration, set the following environment variables:

```bash
# Trakt.tv Integration
TRAKT_ENABLED=true
TRAKT_CLIENT_ID=your_trakt_client_id
TRAKT_CLIENT_SECRET=your_trakt_client_secret
TRAKT_TRENDING_MOVIES_COUNT=10
TRAKT_CHECK_INTERVAL=3600
```

#### Getting Trakt.tv API Credentials

1. Visit [Trakt.tv API Applications](https://trakt.tv/oauth/applications)
2. Create a new application
3. Note your Client ID and Client Secret
4. Add these credentials to your environment variables

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Unraid system with cache and array drives
- Plex Media Server
- Plex API token

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/PlexCacheUltra.git
cd PlexCacheUltra
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```bash
# Plex Configuration
PLEX_URL=https://plex.yourdomain.com
PLEX_TOKEN=your_plex_token_here

# Path Configuration (Unraid defaults)
CACHE_DIR=/mnt/cache
REAL_SOURCE=/mnt/user
PLEX_SOURCE=/media

# New: Flexible destination configuration
CACHE_DESTINATION=/mnt/cache/media  # Optional: Custom destination for cached media

# New: Multiple source support
ADDITIONAL_SOURCES=/mnt/remote_share,/mnt/nas_media  # Comma-separated list

# Unraid mapping (optional, defaults work for Unraid):
PUID=99
PGID=100

# New: Test mode configuration
TEST_MODE=false                    # Enable test mode (analyze without moving)
TEST_SHOW_FILE_SIZES=true         # Show individual file sizes
TEST_SHOW_TOTAL_SIZE=true         # Show total size
TEST_DRY_RUN=true                 # Don't actually move files

# New: Copy vs Move behavior
COPY_TO_CACHE=false                    # Copy files to cache instead of moving
DELETE_FROM_CACHE_WHEN_DONE=true       # Delete from cache when done (vs moving back)
USE_SYMLINKS_FOR_CACHE=true            # Create symlinks so Plex uses cached files
MOVE_WITH_SYMLINKS=false               # Enable hybrid move+symlink mode

# Optional: Enable scheduler
ENABLE_SCHEDULER=true
```

### 3. Deploy with Docker Compose

```bash
docker-compose up -d
```

### 4. Access the Web Dashboard

Open your browser and navigate to: `http://your-server:5443`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PLEX_URL` | Your Plex server URL | Required |
| `PLEX_TOKEN` | Your Plex API token | Required |
| `CACHE_DIR` | Cache drive path | `/mnt/cache` |
| `REAL_SOURCE` | Array drive path | `/mnt/user` |
| `PLEX_SOURCE` | Plex library path | `/media` |
| **🆕 `CACHE_DESTINATION`** | **Custom destination for cached media** | **`CACHE_DIR`** |
| **🆕 `ADDITIONAL_SOURCES`** | **Comma-separated list of additional source directories** | **None** |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WEBHOOK_URL` | Discord/Slack webhook URL | Optional |
| `NOTIFICATION_TYPE` | Notification method | `webhook` |
| `MAX_CONCURRENT_MOVES_CACHE` | Concurrent moves to cache | `5` |
| `MAX_CONCURRENT_MOVES_ARRAY` | Concurrent moves to array | `2` |
| `NUMBER_EPISODES` | Episodes to cache ahead | `5` |
| `DAYS_TO_MONITOR` | Days to monitor onDeck | `99` |
| `WATCHLIST_TOGGLE` | Enable watchlist caching | `true` |
| `WATCHLIST_EPISODES` | Episodes per show in watchlist | `1` |
| `WATCHLIST_CACHE_EXPIRY` | Watchlist cache expiry (hours) | `6` |
| `WATCHED_MOVE` | Move watched content to array | `true` |
| `WATCHED_CACHE_EXPIRY` | Watched cache expiry (hours) | `48` |
| `USERS_TOGGLE` | Enable multi-user support | `true` |
| `EXIT_IF_ACTIVE_SESSION` | Exit on active Plex sessions | `false` |
| **🆕 `TEST_MODE`** | **Enable test mode** | **`false`** |
| **🆕 `TEST_SHOW_FILE_SIZES`** | **Show individual file sizes in test mode** | **`true`** |
| **🆕 `TEST_SHOW_TOTAL_SIZE`** | **Show total size in test mode** | **`true`** |
| **🆕 `TEST_DRY_RUN`** | **Don't move files in test mode** | **`true`** |
| **🆕 `REAL_TIME_WATCH_ENABLED`** | **Enable real-time Plex watching** | **`false`** |
| **🆕 `REAL_TIME_WATCH_CHECK_INTERVAL`** | **Check interval for Plex activity (seconds)** | **`30`** |
| **🆕 `REAL_TIME_WATCH_AUTO_CACHE_ON_WATCH`** | **Auto-cache media when watching starts** | **`true`** |
| **🆕 `REAL_TIME_WATCH_CACHE_ON_COMPLETE`** | **Cache media when watching completes** | **`true`** |
| **🆕 `REAL_TIME_WATCH_RESPECT_EXISTING_RULES`** | **Respect user inclusion and watchlist rules** | **`true`** |
| **🆕 `REAL_TIME_WATCH_MAX_CONCURRENT_WATCHES`** | **Maximum concurrent watch operations** | **`5`** |
| **🆕 `REAL_TIME_WATCH_REMOVE_FROM_CACHE_AFTER_HOURS`** | **Hours before removing media from cache (0 = never)** | **`24`** |
| **🆕 `REAL_TIME_WATCH_RESPECT_OTHER_USERS_WATCHLISTS`** | **Keep media in cache for other users' watchlists** | **`true`** |
| **🆕 `REAL_TIME_WATCH_EXCLUDE_INACTIVE_USERS_DAYS`** | **Days of inactivity before excluding users (0 = no exclusion)** | **`30`** |
| **🆕 `COPY_TO_CACHE`** | **Copy files to cache instead of moving** | **`false`** |
| **🆕 `DELETE_FROM_CACHE_WHEN_DONE`** | **Delete from cache when done (vs moving back)** | **`true`** |
| **🆕 `USE_SYMLINKS_FOR_CACHE`** | **Create symlinks so Plex uses cached files** | **`true`** |
| **🆕 `MOVE_WITH_SYMLINKS`** | **Enable hybrid move+symlink mode** | **`false`** |
| `DEBUG` | Enable debug mode | `false` |
| `ENABLE_SCHEDULER` | Enable automatic scheduling | `false` |
| `PORT` | Web interface port | `5443` |

### Trakt.tv Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TRAKT_ENABLED` | Enable Trakt.tv integration | `false` |
| `TRAKT_CLIENT_ID` | Trakt.tv API client ID | (required if enabled) |
| `TRAKT_CLIENT_SECRET` | Trakt.tv API client secret | (required if enabled) |
| `TRAKT_TRENDING_MOVIES_COUNT` | Number of trending movies to cache | `10` |
| `TRAKT_CHECK_INTERVAL` | Check interval in seconds | `3600` (1 hour) |

### Unraid-Specific Paths

For Unraid systems, the default paths are:

- **Cache Drive**: `/mnt/cache` - Fast SSD/NVMe storage
- **Array Drive**: `/mnt/user` - Slower parity-protected storage
- **Plex Source**: `/media` - Path Plex sees for libraries

On Unraid, recommended user and group mappings are:

- `PUID=99` (user `nobody`)
- `PGID=100` (group `users`)

These are exposed as environment variables and applied at container start so mounted volumes are owned correctly.

### 🆕 New Configuration Options

#### Flexible Destination Paths

You can now specify a custom destination for cached media that's different from your main cache directory:

```bash
# Cache media to a specific subdirectory
CACHE_DESTINATION=/mnt/cache/media

# Cache media to a different drive entirely
CACHE_DESTINATION=/mnt/ssd/plex_cache
```

#### Multiple Source Support

Access media from additional mounted shares, network drives, or remote sources:

```bash
# Multiple comma-separated sources
ADDITIONAL_SOURCES=/mnt/remote_share,/mnt/nas_media,/mnt/backup_drive

# Network shares
ADDITIONAL_SOURCES=/mnt/smb_share,/mnt/nfs_media
```

The system will automatically scan these sources for media files that match your current media list.

#### Test Mode

Preview operations without actually moving files:

```bash
# Enable test mode
TEST_MODE=true

# Configure test mode behavior
TEST_SHOW_FILE_SIZES=true      # Show individual file sizes
TEST_SHOW_TOTAL_SIZE=true      # Show total size
TEST_DRY_RUN=true              # Don't move files (always true in test mode)
```

Test mode provides detailed analysis of what would be moved, including:
- File counts and individual file sizes
- Total size calculations
- Source and destination paths
- Operation previews

#### Copy vs Move Modes

PlexCacheUltra supports three different workflows for caching media:

**Traditional Move Mode (Default):**
```bash
COPY_TO_CACHE=false                    # Move files to cache
DELETE_FROM_CACHE_WHEN_DONE=false      # Move files back when done
USE_SYMLINKS_FOR_CACHE=false           # Don't create symlinks
MOVE_WITH_SYMLINKS=false               # Don't use hybrid mode
```
- Files are moved from source to cache
- After watching, files are moved back to source
- Plex continues reading from original paths

**🆕 Copy + Symlink Mode (Recommended):**
```bash
COPY_TO_CACHE=true                     # Copy files to cache
DELETE_FROM_CACHE_WHEN_DONE=true       # Delete from cache when done
USE_SYMLINKS_FOR_CACHE=true            # Create symlinks for Plex
MOVE_WITH_SYMLINKS=false               # Don't use hybrid mode
```
- Files are copied to cache (originals preserved)
- Symlinks are created pointing to cached files
- **Plex automatically uses cached files** (follows symlinks)
- After watching, cached files are deleted, symlinks removed
- Originals remain untouched in their locations

**🆕 Move + Symlink Mode (Hybrid - Best of Both Worlds):**
```bash
COPY_TO_CACHE=false                    # Move files to cache
DELETE_FROM_CACHE_WHEN_DONE=true       # Delete from cache when done
USE_SYMLINKS_FOR_CACHE=false           # Not used in hybrid mode
MOVE_WITH_SYMLINKS=true                # Enable hybrid move+symlink mode
```
- Files are moved from source to cache (freeing source space)
- Symlinks are created back to original locations
- **Plex automatically uses cached files** (follows symlinks)
- After watching, cached files are deleted, symlinks removed
- Source space is freed, but Plex library remains intact

**Why Use Copy + Symlink Mode?**
- ✅ **Plex automatically uses cache** - no manual path updates
- ✅ **Preserves originals** - source files never moved
- ✅ **Instant cache access** - symlinks provide transparent redirection
- ✅ **Perfect for NAS setups** - network shares remain untouched
- ✅ **Multiple users** - same files accessible from multiple locations

**Why Use Move + Symlink Mode?**
- ✅ **Plex automatically uses cache** - no manual path updates
- ✅ **Frees source space** - files moved to cache, not copied
- ✅ **No library scans** - Plex follows symlinks without triggering rescans
- ✅ **Best performance** - combines space savings with cache benefits
- ✅ **Perfect for limited storage** - maximize cache usage while keeping Plex happy

## 📁 Project Structure

```
PlexCacheUltra/
├── src/
│   ├── config/          # Configuration management
│   ├── core/            # Core application logic
│   └── __init__.py
├── config/              # Configuration files
├── data/                # Persistent data storage
├── logs/                # Application logs
├── main.py              # Main application entry point
├── Dockerfile           # Docker container definition
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
└── README.md           # This file
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Start the service
docker compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Update and restart
docker compose pull
docker compose up -d
```

### Using Docker Run

```bash
docker run -d \
  --name plexcache-ultra \
  --restart unless-stopped \
  -p 5443:5443 \
  -e PUID=99 -e PGID=100 \
  -e PLEX_URL=https://plex.yourdomain.com \
  -e PLEX_TOKEN=your_token \
  -e CACHE_DESTINATION=/mnt/cache/media \
  -e ADDITIONAL_SOURCES=/mnt/remote_share,/mnt/nas_media \
  -e TEST_MODE=false \
  -v /mnt/cache:/mnt/cache \
  -v /mnt/user:/mnt/user \
  -v /media:/media \
  -v /mnt/remote_share:/mnt/remote_share:ro \
  -v /mnt/nas_media:/mnt/nas_media:ro \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  plexcache-ultra:latest
```

## 🌐 Web Dashboard

The web dashboard provides a comprehensive interface with three main tabs:

### Dashboard Tab
- **Real-time Status**: Current system status and operations
- **Statistics**: Files moved, cache usage, performance metrics
- **Manual Control**: Trigger cache operations manually
- **🆕 Test Mode Control**: Run test mode operations**
- **🆕 Real-Time Watcher Control**: Start/stop Plex activity monitoring**
- **Scheduler Control**: Start/stop automatic scheduling
- **🆕 Test Results Display**: Detailed test mode analysis**
- **🆕 Watcher Status**: Real-time monitoring statistics and watch history**

### Settings Tab
- **🆕 Configuration Management**: View and modify all settings through web forms**
- **🆕 Real-time Validation**: Validate paths, permissions, and Plex connections**
- **🆕 Path Testing**: Check if directories exist and are accessible**
- **🆕 Plex Connection Testing**: Verify Plex server connectivity and authentication**
- **🆕 Real-Time Watcher Settings**: Configure Plex activity monitoring behavior**
- **🆕 Settings Reset**: Restore default configuration values**
- **🆕 Form-based Editing**: Easy-to-use forms for all configuration options**

### Logs Tab
- **Live Logs**: Real-time application logs
- **Configuration Display**: Current settings and path mappings
- **Manual Operations**: Trigger cache operations on demand
- **🆕 Test Mode Operations**: Preview operations without moving files**
- **Scheduler Management**: Control automatic execution
- **🆕 Enhanced File Analysis**: View file sizes, totals, and operation previews**

## 🔄 How It Works

### 1. Media Discovery
- **OnDeck Media**: Automatically detects what users are currently watching
- **Watchlist Media**: Caches items from user watchlists
- **🆕 Additional Sources**: Scans mounted shares and remote sources for matching media**
- **Smart Prediction**: Caches next episodes in TV series

### 2. Intelligent Caching
- **🆕 Flexible Destinations**: Move media to custom cache locations**
- **Cache Priority**: Moves frequently accessed media to fast cache drives
- **Subtitle Support**: Automatically includes subtitle files
- **Space Management**: Checks available space before operations
- **Concurrent Operations**: Parallel file movements for performance

### 3. Array Management
- **Watched Content**: Moves completed media back to array drives
- **Cache Cleanup**: Frees up cache space for new content
- **Efficient Movement**: Optimized file transfer operations

### 4. Monitoring & Control
- **Web Interface**: Real-time dashboard and control
- **🆕 Test Mode**: Preview operations with detailed analysis**
- **Scheduled Execution**: Automatic periodic operations
- **Health Checks**: Docker health monitoring
- **Notifications**: Status updates via webhooks

### 🆕 New Workflow Features

#### Test Mode Execution

1. **Analysis Phase**: System analyzes what would be moved without touching files
2. **Size Calculation**: Computes individual file sizes and total requirements
3. **Path Preview**: Shows source and destination paths for all operations
4. **Summary Report**: Provides comprehensive overview of pending operations
5. **Safe Preview**: No files are moved, allowing safe operation planning

#### Real-Time Plex Watching

The system can now monitor Plex activity in real-time through the Plex API to make dynamic caching decisions:

```bash
# Enable real-time watching
REAL_TIME_WATCH_ENABLED=true

# Configure cache removal timing
REAL_TIME_WATCH_REMOVE_FROM_CACHE_AFTER_HOURS=24  # Remove after 24 hours

# Respect other users' watchlists
REAL_TIME_WATCH_RESPECT_OTHER_USERS_WATCHLISTS=true

# Exclude inactive users
REAL_TIME_WATCH_EXCLUDE_INACTIVE_USERS_DAYS=30    # Exclude after 30 days inactive
```

**Key Features:**
- **Automatic Caching**: Cache media when users start watching or complete watching
- **Smart Cache Management**: Automatically remove media from cache after a configurable time period
- **Watchlist Respect**: Keep media in cache if other users have it in their watchlists
- **User Activity Tracking**: Exclude inactive users from caching decisions based on configurable inactivity thresholds
- **Real-time Monitoring**: Continuous monitoring of Plex sessions with configurable check intervals
- **Comprehensive Dashboard**: Real-time display of watcher status, cache removal schedule, and user activity

**Cache Removal Logic:**
- Media is scheduled for removal when caching begins
- Removal time is configurable (0 = never remove automatically)
- Items can be kept in cache if they're in other users' watchlists
- User inactivity is tracked and configurable exclusion periods can be set

#### Multiple Source Integration

1. **Source Discovery**: Automatically detects additional mounted sources
2. **Media Matching**: Finds media files that match current caching requirements
3. **Unified Operations**: Treats all sources equally in caching operations
4. **Flexible Destinations**: Can move media to custom cache locations

## 📊 Performance Optimization

### Concurrent Operations
- Configurable concurrent file movements
- Separate limits for cache and array operations
- Thread pool management for optimal performance

### Space Management
- Pre-operation space verification
- Automatic directory creation
- Permission preservation

### 🆕 Enhanced Source Management
- **Parallel Source Scanning**: Efficient scanning of multiple sources
- **Smart Path Resolution**: Intelligent handling of different source types
- **Flexible Destination Mapping**: Custom destination path support

### Error Handling
- Retry mechanisms for failed operations
- Graceful degradation on errors
- Comprehensive logging and monitoring

## 🔍 Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure Docker has access to mounted volumes
   - Check file permissions on cache and array drives

2. **Plex Connection Failed**
   - Verify PLEX_URL and PLEX_TOKEN
   - Check network connectivity to Plex server

3. **Insufficient Space**
   - Monitor cache drive space
   - Adjust cache expiry settings
   - Check for large media files

4. **File Movement Failures**
   - Verify source and destination paths
   - Check for file locks or active usage
   - Review concurrent operation limits

5. **🆕 Additional Source Issues**
   - Verify ADDITIONAL_SOURCES paths exist and are accessible
   - Check permissions on mounted shares
   - Ensure network connectivity for remote sources

6. **🆕 Test Mode Issues**
   - Verify TEST_MODE configuration
   - Check file permissions for analysis operations
   - Review test mode results in web dashboard

7. **🆕 Copy/Symlink Mode Issues**
   - Verify USE_SYMLINKS_FOR_CACHE is enabled for automatic Plex cache usage
   - Check symlink permissions and creation
   - Ensure Plex can follow symlinks to cached files
   - Verify COPY_TO_CACHE and DELETE_FROM_CACHE_WHEN_DONE settings

### Debug Mode

Enable debug mode by setting `DEBUG=true` in your environment:

```bash
DEBUG=true docker-compose up -d
```

### 🆕 Test Mode Debugging

Use test mode to safely analyze operations:

```bash
# Enable test mode for safe analysis
TEST_MODE=true
TEST_DRY_RUN=true

# Check test results in web dashboard
# View detailed file analysis without moving files
```

### 🆕 Real-Time Watcher Issues

Troubleshoot real-time Plex watching:

```bash
# Enable real-time watching
REAL_TIME_WATCH_ENABLED=true
REAL_TIME_WATCH_CHECK_INTERVAL=30

# Check watcher status in web dashboard
# Verify Plex connection and permissions
# Monitor watcher logs for activity
```

**Common Watcher Issues:**
- **No Activity Detected**: Check Plex connection and user permissions
- **High CPU Usage**: Increase check interval to reduce polling frequency
- **Missing Media**: Verify media paths and file permissions
- **Rule Conflicts**: Check user inclusion and watchlist settings

### Logs

View application logs:

```bash
# Docker Compose
docker-compose logs -f

# Docker Run
docker logs -f plexcache-ultra

# Direct file access
tail -f logs/plexcache_ultra.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original PlexCache script by bexem
- Plex API integration via plexapi
- Docker containerization best practices
- Unraid community for testing and feedback

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: This README and inline code comments

---

**PlexCacheUltra** - Optimize your Plex experience with intelligent media caching! 🎬✨

**🆕 New in v2.1**: Flexible destinations, multiple sources, comprehensive test mode, real-time Plex watching, and copy-to-cache with symlink integration for automatic Plex cache usage!
