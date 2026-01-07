# Cacherr

**Intelligent Plex Media Caching for Unraid**

Cacherr automatically moves frequently accessed Plex media to fast SSD storage based on what users are watching, then moves it back when it's no longer needed.

---

## Features

- **OnDeck Caching** - Cache episodes ahead of what users are watching
- **Watchlist Caching** - Cache items from user watchlists
- **Import Lists** - Cache trending content from Trakt, IMDb, TMDb
- **Multi-User Support** - Independent settings for Main, Home, and Shared users
- **Smart Eviction** - Priority-based cache cleanup when space is needed
- **Real-Time Dashboard** - Live progress bars and activity monitoring
- **Atomic Operations** - Zero-interruption caching (invisible to Plex)
- **Cache Limits** - Set size limits like "250GB" or "50%"

---

## Quick Start

### Docker Compose

```yaml
services:
  cacherr:
    image: cacherr/cacherr:latest
    container_name: cacherr
    ports:
      - "5445:5445"
    volumes:
      - /mnt/user/appdata/cacherr:/config
      - /mnt/cache/cacherr_media:/cache
      - /mnt/user/media:/media:rw
    environment:
      - TZ=America/New_York
      - PUID=99
      - PGID=100
      - PLEX_URL=http://192.168.1.100:32400
      - PLEX_TOKEN=your-token-here
```

### Unraid

1. Go to Apps → Search "Cacherr"
2. Install from Community Applications
3. Configure volumes and Plex credentials
4. Start container
5. Open WebUI at `http://your-server:5445`

---

## Configuration

All configuration is done through the WebGUI. Docker only needs:

| Volume | Purpose |
|--------|---------|
| `/config` | Configuration and database |
| `/cache` | SSD cache destination |
| `/media` | Your Plex media location(s) |

---

## How It Works

### Atomic Caching

```
Original State:
/media/Movies/Movie.mkv (on array)

After Caching:
/media/Movies/Movie.mkv → symlink to cache
/media/Movies/.Movie.mkv.plexcached (backup)
/cache/Movies/Movie.mkv (actual file)
```

Plex file descriptors remain valid throughout - no playback interruption.

### Priority Scoring

Each cached file gets a priority score (0-100):

| Factor | Score |
|--------|-------|
| Active playback | 100 (never evict) |
| OnDeck source | +20 |
| Watchlist source | +10 |
| Multiple users | +5 per user |
| Recently cached | +5 to +15 |
| Current episode | +15 |

When cache is full, lowest priority files are evicted first.

### User Types

| Type | Description | Default |
|------|-------------|---------|
| Main | Server owner | All features enabled |
| Home | Family members | All features enabled |
| Shared | Remote friends | OnDeck only |

Each user type can have independent settings for OnDeck, Watchlist, Lists, and Currently Watching.

---

## Documentation

See the [docs/](docs/) folder for detailed documentation:

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Feature Parity Analysis](docs/FEATURE_PARITY.md)
- [User Management Design](docs/USER_MANAGEMENT_DESIGN.md)
- [Import Lists Design](docs/IMPORT_LISTS_DESIGN.md)
- [Real-Time WebGUI Design](docs/REALTIME_WEBGUI_DESIGN.md)
- [Development Tasks](docs/TASKS.md)

---

## Development Status

This is a fresh implementation combining the best features from the original Cacherr/PlexCache with new enhancements.

### Implemented
- ✅ Core architecture
- ✅ Configuration system (Pydantic)
- ✅ Atomic file operations
- ✅ Priority scoring
- ✅ Cache tracking
- ✅ REST API framework
- ✅ Docker configuration

### In Progress
- ⏳ User management system
- ⏳ Import lists system
- ⏳ WebSocket real-time updates
- ⏳ React frontend

---

## Contributing

See [docs/TASKS.md](docs/TASKS.md) for the development task breakdown.

---

## License

MIT License - See LICENSE file for details.

---

## Credits

Originally based on [PlexCache](https://github.com/original/plexcache) with significant enhancements.
