# Cacherr Project Context

## Project Overview

Cacherr is a Docker-optimized Plex media caching system designed specifically for Unraid environments. It automatically moves frequently accessed media files to fast cache drives and moves watched content back to slower array drives, optimizing Plex streaming performance.

### Key Features
- Docker-first design built for containerized deployment
- Smart caching of onDeck and watchlist media
- Atomic operations for zero-interruption real-time caching
- Web dashboard for monitoring and control
- Scheduled operations and multi-user support
- Subtitle handling and notification system
- Trakt.tv integration for trending movies
- Copy vs Move modes with atomic operations and symlink integration

### Technologies
- Python 3.x
- Flask web framework
- Pydantic v2 for configuration management
- PlexAPI for Plex server integration
- Docker and Docker Compose for deployment
- Unraid-optimized paths and configurations

## Project Structure

```
Cacherr/
├── src/                 # Source code
│   ├── config/          # Configuration management with Pydantic v2
│   ├── core/            # Core application logic
│   ├── web/             # Flask web application
│   ├── scheduler/       # Task scheduling system
│   └── __init__.py
├── main.py              # Main application entry point
├── Dockerfile           # Docker container definition
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
└── README.md            # Project documentation
```

## Building and Running

### Prerequisites
- Docker and Docker Compose
- Unraid system with cache and array drives
- Plex Media Server with API token

### Quick Start
1. Clone the repository
2. Copy `env.example` to `.env` and configure:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```
3. Deploy with Docker Compose:
   ```bash
   docker-compose up -d
   ```
4. Access the web dashboard at `http://your-server:5445`

### Docker Deployment
The recommended deployment method uses Docker Compose with Unraid-optimized defaults:
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

### Environment Variables
Key configuration variables:
- `PLEX_URL`: Your Plex server URL
- `PLEX_TOKEN`: Your Plex API token
- `CACHE_DESTINATION`: Cache directory (default: `/cache`)
- `REAL_SOURCE`: Array drive path (default: `/mediasource`)
- `PLEX_SOURCE`: Plex library path (default: `/plexsource`)
- `COPY_TO_CACHE`: Copy files to cache instead of moving (default: `true`)
- `TEST_MODE`: Enable test mode (default: `false`)

See README.md for a complete list of configuration options.

## Development Conventions

### Configuration System
Cacherr uses a modern Pydantic v2 configuration system:
- Type-safe configuration with comprehensive validation
- Environment variable support with clear precedence
- Web-configurable settings with persistent storage
- Computed fields for dynamic configuration descriptions

### Code Structure
- Modular architecture with dependency injection
- Service-oriented design with clear interfaces
- Comprehensive logging and error handling
- Type hints throughout the codebase

### Testing
- Unit tests for core functionality
- Integration tests for Plex and file operations
- Test mode for safe operation analysis

### Web Interface
- Flask-based web application with blueprints
- REST API for programmatic access
- Real-time dashboard with status monitoring
- Configuration management through web forms

## Common Operations

### Running in Test Mode
To safely analyze operations without moving files:
```bash
# Set TEST_MODE=true in your environment
TEST_MODE=true docker-compose up -d
# View results in the web dashboard
```

### Configuration Management
- Web-configured settings are saved to `/config/cacherr_config.json`
- Docker environment variables take precedence over web configuration
- Configuration can be reloaded without restarting the container

### Monitoring and Troubleshooting
- View application logs: `docker-compose logs -f`
- Check health status: `curl http://localhost:5445/health`
- Monitor cache status through the web dashboard