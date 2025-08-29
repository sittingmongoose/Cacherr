# Cacherr - Integrated Docker Setup

This Docker setup provides a complete PlexCache solution with web interface, WebSocket real-time monitoring, and automated testing.

## 🚀 Quick Start

### Start the Web Interface (Recommended)
```bash
# Build and start the web server
docker-compose up --build plexcache

# Access the web interface
open http://localhost:5000
```

### Run Traditional CLI Mode
```bash
# Run one-time caching operation
docker-compose --profile cli up plexcache-cli
```

### Run Tests
```bash
# Run WebSocket tests
docker-compose --profile test up playwright
```

## 📋 Services

### `plexcache` (Main Web Service)
- **Port**: 5000
- **Features**:
  - Web interface for PlexCache control
  - Real-time WebSocket monitoring
  - REST API endpoints
  - Health checks
- **Usage**: `docker-compose up plexcache`

### `plexcache-cli` (Command Line Mode)
- **Features**:
  - Traditional PlexCache command-line operation
  - One-time caching execution
  - Batch processing
- **Usage**: `docker-compose --profile cli up plexcache-cli`

### `playwright` (Testing)
- **Port**: 9323 (UI mode)
- **Features**:
  - Automated WebSocket testing
  - Cross-browser compatibility testing
  - API endpoint validation
- **Usage**: `docker-compose --profile test up playwright`

## 🔧 Configuration

### Environment Variables
```bash
DEBUG=true          # Enable debug mode
PLEX_URL=...        # Your Plex server URL
PLEX_TOKEN=...      # Your Plex authentication token
```

### Volumes
- `./plexcache_settings.json` → PlexCache configuration
- `/mnt/user/system/plexcache` → PlexCache data directory
- `./logs` → Application logs

## 🌐 Web Interface Features

### Real-time Monitoring
- Live cache operation status
- WebSocket connection monitoring
- Real-time statistics updates
- Activity logging

### Control Panel
- Start/Stop cache operations
- View connected clients
- Monitor system health
- Access logs and statistics

### API Endpoints
```
GET  /                    # Web interface
GET  /api/health          # Health check
GET  /api/status          # System status
POST /api/start-cache     # Start caching
POST /api/stop-cache      # Stop caching
```

## 🧪 Testing

### Automated Testing
```bash
# Run all WebSocket tests
docker-compose --profile test up playwright

# Run with UI mode for debugging
docker-compose --profile test up playwright-ui
```

### Manual Testing
```bash
# Check health endpoint
curl http://localhost:5000/api/health

# Start cache operation
curl -X POST http://localhost:5000/api/start-cache

# Get system status
curl http://localhost:5000/api/status
```

## 📁 Project Structure

```
plexcache/
├── Dockerfile              # Main application container
├── Dockerfile.test         # Testing container
├── docker-compose.yml      # Multi-service orchestration
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies (for testing)
├── plexcache.py           # Main application (integrated)
├── plexcache_settings.json # Configuration
├── e2e/                   # End-to-end tests
│   └── websocket.spec.ts  # WebSocket tests
├── src/                   # WebSocket server components
└── logs/                  # Application logs
```

## 🔄 Usage Modes

### 1. Web Server Mode (Default)
```bash
docker-compose up plexcache
```
- Runs continuous web server
- WebSocket real-time monitoring
- Web-based control panel
- REST API access

### 2. CLI Mode (One-time operations)
```bash
docker-compose --profile cli up plexcache-cli
```
- Traditional command-line execution
- Batch processing
- Scheduled operations
- Background services

### 3. Development Mode
```bash
docker-compose up --build
```
- Auto-rebuild on changes
- Debug logging enabled
- Development tools included

## 🏥 Health Checks

The container includes built-in health checks:
- HTTP endpoint monitoring
- WebSocket connectivity
- Service availability
- Automatic restart on failure

## 📊 Monitoring

### Logs
```bash
# View application logs
docker-compose logs plexcache

# Follow logs in real-time
docker-compose logs -f plexcache
```

### Metrics
- WebSocket client connections
- Cache operation status
- System performance metrics
- Error rates and alerts

## 🔒 Security

- Container runs as non-root user
- Minimal attack surface
- CORS enabled for web interface
- Secure WebSocket connections

## 🚀 Deployment

### Production Deployment
```bash
# Build optimized image
docker-compose build --no-cache

# Deploy with restart policy
docker-compose up -d

# Enable automatic updates
docker-compose up -d --pull
```

### High Availability
```yaml
# Example docker-compose.override.yml
version: '3.8'
services:
  plexcache:
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
```

## 🐛 Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check logs
docker-compose logs plexcache

# Verify configuration
docker-compose config
```

**WebSocket connection fails**
```bash
# Test WebSocket manually
curl -I http://localhost:5000
docker-compose exec plexcache curl -f http://localhost:5000/api/health
```

**Permission issues**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 /mnt/user/system/plexcache
```

### Debug Mode
```bash
# Enable debug logging
DEBUG=true docker-compose up plexcache

# View detailed logs
docker-compose logs -f --tail=100 plexcache
```

## 📚 Additional Resources

- [PlexCache Documentation](https://github.com/bexem/PlexCache)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Playwright Testing](https://playwright.dev/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**🎯 Ready to use!** Start with `docker-compose up plexcache` and visit `http://localhost:5000`