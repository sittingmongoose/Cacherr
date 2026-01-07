# Cacherr Documentation

## Overview

Cacherr is an intelligent Plex media caching system for Unraid that automatically moves frequently accessed media to fast SSD storage based on what users are watching.

---

## Documentation Index

### Design Documents

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Project structure and component overview |
| [FEATURE_PARITY.md](FEATURE_PARITY.md) | Feature comparison with original codebase |
| [USER_MANAGEMENT_DESIGN.md](USER_MANAGEMENT_DESIGN.md) | Main/Home/Shared user classification |
| [IMPORT_LISTS_DESIGN.md](IMPORT_LISTS_DESIGN.md) | Radarr-style import lists system |
| [REALTIME_WEBGUI_DESIGN.md](REALTIME_WEBGUI_DESIGN.md) | WebSocket real-time updates |

### Development

| Document | Description |
|----------|-------------|
| [TASKS.md](TASKS.md) | Development task breakdown for Claude Code/Codex/Cursor |

### User Guides (To Be Created)

| Document | Description |
|----------|-------------|
| INSTALLATION.md | Docker setup instructions |
| CONFIGURATION.md | All settings explained |
| API.md | REST API documentation |
| TROUBLESHOOTING.md | Common issues and solutions |

---

## Quick Links

### For Developers

1. Start with [ARCHITECTURE.md](ARCHITECTURE.md) to understand the codebase
2. Check [TASKS.md](TASKS.md) for implementation tasks
3. Review feature requirements in [FEATURE_PARITY.md](FEATURE_PARITY.md)

### For AI Assistants (Claude Code, Codex, Cursor)

When implementing features, always read:
1. The relevant design document first
2. [ARCHITECTURE.md](ARCHITECTURE.md) for project structure
3. [TASKS.md](TASKS.md) for specific task requirements

---

## Key Concepts

### User Types
- **Main User** - Plex server owner (highest priority)
- **Home Users** - Family members on same Plex Home
- **Shared Users** - Friends with remote access

### Cache Sources
- **OnDeck** - Currently watching episodes
- **Watchlist** - User watchlists
- **Import Lists** - External lists (Trakt, IMDb, etc.)
- **Active Watching** - Currently playing media

### Priority Scoring (0-100)
Higher score = keep longer, lower score = evict first
- Active playback: 100 (never evict)
- OnDeck: +20 base
- Watchlist: +10 base
- User count: +5 per user
- Recency bonuses
- Episode position bonuses

### Atomic Operations
Files are cached without interrupting playback:
1. Copy to cache
2. Create backup
3. Atomic rename original → backup
4. Create symlink original → cache
5. Plex never sees interruption

---

## Configuration Philosophy

- **Docker config**: Only what MUST be in Docker (volume mounts, ports)
- **WebGUI**: Everything else (Plex settings, cache limits, users, lists)
- **Environment variables**: Initial setup only, can be changed in WebGUI

---

## Getting Help

- GitHub Issues: [cacherr/cacherr/issues](https://github.com/cacherr/cacherr/issues)
- Unraid Forums: TBD
- Discord: TBD
