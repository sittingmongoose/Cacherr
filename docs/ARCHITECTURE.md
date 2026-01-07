# Cacherr Architecture Overview

## Project Structure

```
cacherr/
├── main.py                      # Application entry point
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Docker Compose configuration
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── README.md                    # Project readme
│
├── docker/
│   └── cacherr.xml              # Unraid Docker template
│
├── src/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Pydantic settings models
│   │   ├── defaults.py          # Default configuration values
│   │   └── migrations.py        # Settings migration
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.py            # SQLAlchemy models
│   │   ├── migrations.py        # Database migrations
│   │   └── repository.py        # Data access layer
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cache_manager.py     # Central cache orchestrator
│   │   ├── file_operations.py   # Atomic file operations
│   │   ├── plex_client.py       # Rate-limited Plex API client
│   │   ├── trackers.py          # Cache/Watchlist/OnDeck trackers
│   │   ├── lock.py              # Instance lock
│   │   ├── user_manager.py      # User discovery and management
│   │   ├── activity_tracker.py  # User activity tracking
│   │   └── broadcaster.py       # Event broadcaster
│   │
│   ├── lists/
│   │   ├── __init__.py
│   │   ├── manager.py           # Import lists manager
│   │   ├── matcher.py           # Plex library matcher
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── base.py          # Base provider class
│   │       ├── trakt.py         # Trakt.tv provider
│   │       ├── tmdb.py          # TMDb provider
│   │       ├── imdb.py          # IMDb provider
│   │       └── rss.py           # RSS/Custom URL provider
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py            # Flask REST API routes
│   │   ├── websocket.py         # Flask-SocketIO WebSocket handler
│   │   └── events.py            # Event type definitions
│   │
│   └── services/
│       ├── __init__.py
│       ├── notifications.py     # Notification handlers
│       └── unraid.py            # Unraid-specific utilities
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   │
│   └── src/
│       ├── main.tsx             # React entry point
│       ├── App.tsx              # Main app component
│       │
│       ├── types/
│       │   └── cache.ts         # TypeScript type definitions
│       │
│       ├── services/
│       │   └── api.ts           # API service
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts  # WebSocket hook
│       │   └── useApi.ts        # API hooks
│       │
│       ├── pages/
│       │   ├── Dashboard.tsx    # Main dashboard
│       │   ├── Users.tsx        # User management
│       │   ├── ImportLists.tsx  # Import lists management
│       │   ├── Settings.tsx     # Settings page
│       │   └── settings/        # Settings sub-pages
│       │       ├── GeneralSettings.tsx
│       │       ├── PlexSettings.tsx
│       │       ├── CacheSettings.tsx
│       │       ├── RetentionSettings.tsx
│       │       ├── NotificationSettings.tsx
│       │       └── PathMappings.tsx
│       │
│       └── components/
│           ├── StatsCards.tsx
│           ├── ActiveOperations.tsx
│           ├── SessionList.tsx
│           ├── CachedFilesList.tsx
│           ├── ActivityFeed.tsx
│           ├── UserCard.tsx
│           ├── UserSettingsDialog.tsx
│           ├── ListCard.tsx
│           └── AddListDialog.tsx
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_settings.py
│   ├── test_plex_client.py
│   ├── test_user_manager.py
│   ├── test_import_lists.py
│   ├── test_cache_manager.py
│   └── test_api.py
│
└── docs/
    ├── README.md                # Docs index
    ├── ARCHITECTURE.md          # This file
    ├── FEATURE_PARITY.md        # Feature comparison with old code
    ├── USER_MANAGEMENT_DESIGN.md
    ├── IMPORT_LISTS_DESIGN.md
    ├── REALTIME_WEBGUI_DESIGN.md
    ├── TASKS.md                 # Development task breakdown
    ├── INSTALLATION.md
    ├── CONFIGURATION.md
    ├── API.md
    └── TROUBLESHOOTING.md
```

---

## Core Components

### 1. Cache Manager (`src/core/cache_manager.py`)
The central orchestrator that coordinates all caching operations.

**Responsibilities:**
- Run cache cycles (OnDeck → Watchlist → Lists → Retention → Eviction)
- Integrate user management
- Integrate import lists
- Enforce cache limits
- Calculate priorities
- Emit events for real-time updates

**Key Methods:**
```python
class CacheManager:
    def run_cache_cycle(self) -> CacheCycleResult
    def get_ondeck_files(self) -> List[Tuple[str, str, str, int]]
    def get_watchlist_files(self) -> List[Tuple[str, str, str, int]]
    def get_import_list_files(self) -> List[Tuple[str, str, str, int]]
    def enforce_cache_limits(self) -> EvictionResult
    def check_retention(self) -> RetentionResult
    def reconcile(self) -> ReconciliationResult
```

### 2. Plex Client (`src/core/plex_client.py`)
Rate-limited Plex API client to prevent server overload.

**Key Features:**
- Configurable rate limiting (ms between calls, max per minute)
- Token caching for users
- Automatic retry with exponential backoff
- User discovery (main, home, shared)

### 3. User Manager (`src/core/user_manager.py`)
Manages Plex users and their caching settings.

**Key Features:**
- User classification (Main/Home/Shared)
- Per-user caching settings
- Activity-based filtering
- User type defaults

### 4. Import Lists Manager (`src/lists/manager.py`)
Radarr-style import lists system.

**Key Features:**
- Multiple providers (Trakt, TMDb, IMDb, RSS)
- Strict vs Fill mode
- Air date filtering
- Plex library matching

### 5. Event Broadcaster (`src/core/broadcaster.py`)
Broadcasts events to WebSocket clients.

**Event Types:**
- `status` - System status
- `stats` - Cache statistics
- `operation_progress` - File operation progress
- `operation_complete` - File operation completion
- `session_*` - Plex session events
- `log` - Log messages
- `cycle_*` - Cache cycle progress

---

## Data Flow

### Cache Cycle Flow
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Cache Cycle                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. GET ONDECK                                                               │
│     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                 │
│     │ User Manager│────▶│ Plex Client │────▶│ Apply Filters│                │
│     │ (per user)  │     │ (rate limit)│     │ (staleness) │                 │
│     └─────────────┘     └─────────────┘     └─────────────┘                 │
│                                                    │                         │
│                                                    ▼                         │
│  2. GET WATCHLIST                            ┌─────────────┐                 │
│     (same flow)                              │ Merge Files │                 │
│                                              │ + Priorities│                 │
│  3. GET IMPORT LISTS                         └─────────────┘                 │
│     ┌─────────────┐     ┌─────────────┐           │                         │
│     │Lists Manager│────▶│Library Match│───────────┘                         │
│     └─────────────┘     └─────────────┘                                     │
│                                                    │                         │
│                                                    ▼                         │
│  4. CACHE FILES                              ┌─────────────┐                 │
│     ┌─────────────┐                          │  Atomic     │                 │
│     │File Ops     │◀─────────────────────────│  Copy +     │                 │
│     │(progress)   │                          │  Symlink    │                 │
│     └─────────────┘                          └─────────────┘                 │
│           │                                        │                         │
│           ▼                                        ▼                         │
│  5. EMIT EVENTS                              6. RETENTION CHECK              │
│     ┌─────────────┐                          ┌─────────────┐                 │
│     │ Broadcaster │                          │ Move back   │                 │
│     │ (WebSocket) │                          │ watched/old │                 │
│     └─────────────┘                          └─────────────┘                 │
│                                                    │                         │
│                                                    ▼                         │
│                                              7. EVICTION                     │
│                                              ┌─────────────┐                 │
│                                              │ If over     │                 │
│                                              │ limit, evict│                 │
│                                              │ low priority│                 │
│                                              └─────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Real-Time Update Flow
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Real-Time Updates                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   BACKEND                                         FRONTEND                   │
│                                                                              │
│   ┌─────────────┐                              ┌─────────────┐              │
│   │Cache Manager│                              │  Dashboard  │              │
│   │             │                              │             │              │
│   │ operation() │                              │ useWebSocket│              │
│   └─────┬───────┘                              └──────▲──────┘              │
│         │                                            │                       │
│         │ emit                                       │ receive               │
│         ▼                                            │                       │
│   ┌─────────────┐        WebSocket           ┌─────────────┐               │
│   │ Broadcaster │ ─────────────────────────▶ │   Client    │               │
│   └─────────────┘                            └─────────────┘               │
│                                                                              │
│   Events:                                    Updates:                        │
│   - operation_progress                       - Progress bars                 │
│   - operation_complete                       - File list                     │
│   - stats                                    - Stats cards                   │
│   - session_*                                - Session list                  │
│   - log                                      - Activity feed                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Hierarchy

```
1. Default values (in Pydantic models)
      ↓
2. JSON config file (/config/cacherr.json)
      ↓
3. Environment variables (override file)
      ↓
4. WebGUI changes (saved back to JSON)
```

---

## API Design

### REST Endpoints
All REST endpoints return consistent JSON:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed",
  "error": "",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### WebSocket Events
All WebSocket events follow this format:
```json
{
  "type": "event_type",
  "timestamp": "2024-01-15T12:00:00Z",
  "data": { ... }
}
```

---

## Key Design Decisions

### 1. Why Pydantic for Settings?
- Type validation built-in
- JSON serialization/deserialization
- Environment variable support
- Clear schema definition
- IDE autocompletion

### 2. Why Flask-SocketIO for WebSocket?
- Integrates seamlessly with Flask REST API
- Handles reconnection automatically
- Room/namespace support for future features
- Works with standard WebSocket clients

### 3. Why SQLite for Persistent Data?
- No external database needed
- File-based, easy to backup
- Good enough performance for this use case
- SQLAlchemy ORM for type safety

### 4. Why Atomic Operations?
- Plex file descriptors stay valid
- No playback interruption
- Symlinks invisible to Plex
- Can recover from failures

### 5. Why User Type Separation?
- Different trust levels
- Different caching priorities
- Independent activity filtering
- Flexible configuration
