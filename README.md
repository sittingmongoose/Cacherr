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
- **Port 5444**: Optimized for Unraid environments (avoids routing conflicts)
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
git clone https://github.com/sittingmongoose/PlexCacheUltra.git
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
CACHE_DESTINATION=/cache
REAL_SOURCE=/mediasource
PLEX_SOURCE=/plexsource

# Additional source support
ADDITIONAL_SOURCES=/mediasource2 /mediasource3 /mediasource4  # Space-separated list
ADDITIONAL_PLEX_SOURCES=/plexsource2 /plexsource3 /plexsource4

# Unraid mapping (optional, defaults work for Unraid):
PUID=99
PGID=100
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
| `CACHE_DESTINATION` | Cache directory for media files | `/cache` |
| `REAL_SOURCE` | Array drive path | `/mediasource` |
| `PLEX_SOURCE` | Plex library path | `/plexsource` |
| `ADDITIONAL_SOURCES` | Space-separated list of additional source directories | `/mediasource2` |
| `ADDITIONAL_PLEX_SOURCES` | Space-separated list of corresponding plex internal paths | `/plexsource2` |
| `CONFIG_DIR` | Application configuration directory | `/config` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WEBHOOK_URL` | Discord/Slack webhook URL | Optional |
| `NOTIFICATION_TYPE` | Notification method | `webhook` |
| `MAX_CONCURRENT_MOVES_CACHE` | Concurrent moves to cache | `3` |
| `MAX_CONCURRENT_MOVES_ARRAY` | Concurrent moves to array | `1` |
| `NUMBER_EPISODES` | Episodes to cache ahead | `5` |
| `DAYS_TO_MONITOR` | Days to monitor onDeck | `99` |
| `WATCHLIST_TOGGLE` | Enable watchlist caching | `true` |
| `WATCHLIST_EPISODES` | Episodes per show in watchlist | `1` |
| `WATCHLIST_CACHE_EXPIRY` | Watchlist cache expiry (hours) | `6` |
| `WATCHED_MOVE` | Move watched content to array | `true` |
| `WATCHED_CACHE_EXPIRY` | Watched cache expiry (hours) | `48` |
| `USERS_TOGGLE` | Enable multi-user support | `true` |
| `EXIT_IF_ACTIVE_SESSION` | Exit on active Plex sessions | `false` |
| `TEST_MODE` | Enable test mode | `false` |
| `TEST_SHOW_FILE_SIZES` | Show individual file sizes in test mode | `true` |
| `TEST_SHOW_TOTAL_SIZE` | Show total size in test mode | `true` |
| `TEST_DRY_RUN` | Don't move files in test mode | `true` |
| `REAL_TIME_WATCH_ENABLED` | Enable real-time Plex watching | `false` |
| `REAL_TIME_WATCH_CHECK_INTERVAL` | Check interval for Plex activity (seconds) | `30` |
| `REAL_TIME_WATCH_AUTO_CACHE_ON_WATCH` | Auto-cache media when watching starts | `true` |
| `REAL_TIME_WATCH_CACHE_ON_COMPLETE` | Cache media when watching completes | `true` |
| `REAL_TIME_WATCH_RESPECT_EXISTING_RULES` | Respect user inclusion and watchlist rules | `true` |
| `REAL_TIME_WATCH_MAX_CONCURRENT_WATCHES` | Maximum concurrent watch operations | `5` |
| `REAL_TIME_WATCH_REMOVE_FROM_CACHE_AFTER_HOURS` | Hours before removing media from cache (0 = never) | `24` |
| `REAL_TIME_WATCH_RESPECT_OTHER_USERS_WATCHLISTS` | Keep media in cache for other users' watchlists | `true` |
| `REAL_TIME_WATCH_EXCLUDE_INACTIVE_USERS_DAYS` | Days of inactivity before excluding users (0 = no exclusion) | `30` |
| `COPY_TO_CACHE` | Copy files to cache instead of moving | `false` |
| `DELETE_FROM_CACHE_WHEN_DONE` | Delete from cache when done (vs moving back) | `true` |
| `USE_SYMLINKS_FOR_CACHE` | Create symlinks so Plex uses cached files | `true` |
| `MOVE_WITH_SYMLINKS` | Enable hybrid move+symlink mode | `false` |
| `DEBUG` | Enable debug mode | `false` |
| `ENABLE_SCHEDULER` | Enable automatic scheduling | `false` |
| `PORT` | Web interface port (container) | `5443` |
| `WEB_PORT` | Web interface port (host) | `5444` (Unraid optimized) |

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

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

The `docker-compose.yml` is now configured with safe defaults for Unraid environments:

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Update and restart
docker-compose pull
docker-compose up -d
```

**Key Features:**
- ✅ **Safe Default Paths** - Won't conflict with Plex
- ✅ **Port 5444** - Avoids Unraid routing issues
- ✅ **No Environment Variables Required** - Built-in defaults
- ✅ **Unraid Optimized** - Designed for Unraid environments

### Using Docker Run

```bash
docker run -d \
  --name plexcache-ultra \
  --restart unless-stopped \
  -p 5444:5443 \
  -e PLEX_URL=https://plex.yourdomain.com \
  -e PLEX_TOKEN=your_token \
  -v /mnt/cache/apps/plexcacheultra:/cache \
  -v /mnt/user/media:/mediasource \
  -v /mnt/user/plex:/plexsource \
  -v /mnt/user/appdata/plexcacheultra/config:/config \
  sittingmongoose/plexcacheultra:dev
```

**Note:** The container now uses safe default paths that won't conflict with Plex. No additional environment variables are required.

### Unraid Docker Template

For Unraid users, the container is now optimized with safe defaults. Simply:

1. **Set Volume Paths:**
   - `/mnt/cache/apps/plexcacheultra` → `/cache`
   - `/mnt/user/media` → `/mediasource`
   - `/mnt/user/plex` → `/plexsource`
   - `/mnt/user/appdata/plexcacheultra/config` → `/config`

2. **Set Port Mapping:** `5444:5443`

3. **Set WebUI:** `http://[IP]:5444`

4. **Optional:** Set `PLEX_URL` and `PLEX_TOKEN` if you want Plex integration

**No environment variables needed** - Safe defaults are built-in and won't interfere with Plex!

### 🐳 Unraid-Specific Setup

#### Quick Start (Zero Configuration)
1. **Import Template:** Download `plexcacheultra-unraid-template.xml` and import via Docker → Add Container → Template
2. **Or Manual Setup:** Set Repository to `sittingmongoose/plexcacheultra:dev`
3. **Start Container:** Click Apply - no additional configuration needed!

#### Directory Setup (if needed)
```bash
mkdir -p /mnt/cache/apps/plexcacheultra
mkdir -p /mnt/user/media
mkdir -p /mnt/user/plex
mkdir -p /mnt/user/appdata/plexcacheultra/config
chown -R nobody:users /mnt/cache/apps/plexcacheultra
chown -R nobody:users /mnt/user/media
chown -R nobody:users /mnt/user/plex
chown -R nobody:users /mnt/user/appdata/plexcacheultra/config
```

#### Unraid Optimizations
- **Port 5444:** Avoids Unraid routing conflicts
- **Automatic Permissions:** No more "Permission denied" errors
- **Safe Paths:** Won't interfere with existing Plex installation
- **Health Checks:** Built-in Docker health monitoring
- **Zero Config:** Works out of the box with safe defaults

**📖 For detailed Unraid setup instructions, see the Unraid Docker Template section below**

## 🌐 Web Dashboard

The web dashboard provides a comprehensive interface with three main tabs:

### Dashboard Tab
- **Real-time Status**: Current system status and operations
- **Statistics**: Files moved, cache usage, performance metrics
- **Manual Control**: Trigger cache operations manually
- **🆕 Test Mode Control**: Run test mode operations
- **🆕 Real-Time Watcher Control**: Start/stop Plex activity monitoring
- **Scheduler Control**: Start/stop automatic scheduling
- **🆕 Test Results Display**: Detailed test mode analysis
- **🆕 Watcher Status**: Real-time monitoring statistics and watch history

### Settings Tab
- **🆕 Configuration Management**: View and modify all settings through web forms
- **🆕 Real-time Validation**: Validate paths, permissions, and Plex connections
- **🆕 Path Testing**: Check if directories exist and are accessible
- **🆕 Plex Connection Testing**: Verify Plex server connectivity and authentication
- **🆕 Real-Time Watcher Settings**: Configure Plex activity monitoring behavior
- **🆕 Settings Reset**: Restore default configuration values
- **🆕 Form-based Editing**: Easy-to-use forms for all configuration options

### Logs Tab
- **Live Logs**: Real-time application logs
- **Configuration Display**: Current settings and path mappings
- **Manual Operations**: Trigger cache operations on demand
- **🆕 Test Mode Operations**: Preview operations without moving files
- **Scheduler Management**: Control automatic execution
- **🆕 Enhanced File Analysis**: View file sizes, totals, and operation previews

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Permission Denied Errors
**Problem:** `ERROR:root:Failed to start PlexCacheUltra: [Errno 13] Permission denied: '/config/logs'`

**Solution:** The container now handles permissions automatically. No manual configuration needed.

#### Plex Service Restarting
**Problem:** Plex service restarts when PlexCacheUltra starts

**Solution:** The container now uses safe default paths that won't conflict with Plex:
- Cache: `/mnt/cache/apps/plexcacheultra` (dedicated directory)
- Media: `/mnt/user/media` (separate from Plex media)
- Plex Source: `/mnt/user/plex` (read-only access)

#### Unraid Web GUI Issues
**Problem:** Web GUI redirects to malformed URLs like `@https://192.168.50.119:1444/5444`

**Solution:** 
1. Set Host Port to `5444` (not 5443)
2. Set WebUI to `http://[IP]:5444`
3. Container Port remains `5443`

#### Container Won't Start
**Problem:** Container exits immediately with permission errors

**Solution:** The entrypoint script now handles all permission issues automatically. Container runs as root initially, then switches to `plexcache` user.

## 🔄 How It Works

### 1. Media Discovery
- **OnDeck Media**: Automatically detects what users are currently watching
- **Watchlist Media**: Caches items from user watchlists
- **🆕 Additional Sources**: Scans mounted shares and remote sources for matching media
- **Smart Prediction**: Caches next episodes in TV series

### 2. Intelligent Caching
- **🆕 Flexible Destinations**: Move media to custom cache locations
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
- **🆕 Test Mode**: Preview operations with detailed analysis
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
tail -f /mnt/user/appdata/plexcacheultra/config/logs/plexcache_ultra.log
```

## 📁 Project Structure

```
PlexCacheUltra/
├── src/
│   ├── config/          # Configuration management
│   ├── core/            # Core application logic
│   └── __init__.py
├── main.py              # Main application entry point
├── Dockerfile           # Docker container definition
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
├── dashboard.html       # Web interface
└── README.md           # This file
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
