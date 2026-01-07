# Development Task Breakdown

## Overview

This document outlines tasks for implementing Cacherr, organized by which AI assistant should handle them based on complexity and capabilities.

**Models:**
- **Claude Code (Opus)** - Complex architecture, core systems, quality code
- **Codex (GPT-4)** - Medium complexity, good code quality
- **Cursor (Fast model)** - Simple tasks, boilerplate, repetitive work

---

## Task Dependency Graph

```
                    ┌─────────────────────────────────────────┐
                    │          PHASE 1: FOUNDATION            │
                    │            (Must be first)               │
                    └─────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
    ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
    │   Task 1.1   │           │   Task 1.2   │           │   Task 1.3   │
    │   Settings   │           │  Plex Client │           │    Database  │
    │   System     │           │  Rate Limit  │           │    Schema    │
    │ (Claude Code)│           │ (Claude Code)│           │   (Codex)    │
    └──────────────┘           └──────────────┘           └──────────────┘
           │                           │                           │
           └───────────────────────────┴───────────────────────────┘
                                       │
                    ┌─────────────────────────────────────────┐
                    │          PHASE 2: CORE SYSTEMS          │
                    │        (Depends on Phase 1)             │
                    └─────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
    ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
    │   Task 2.1   │           │   Task 2.2   │           │   Task 2.3   │
    │     User     │           │   Import     │           │    Cache     │
    │  Management  │           │    Lists     │           │   Manager    │
    │ (Claude Code)│           │ (Claude Code)│           │ (Claude Code)│
    └──────────────┘           └──────────────┘           └──────────────┘
           │                           │                           │
           └───────────────────────────┴───────────────────────────┘
                                       │
                    ┌─────────────────────────────────────────┐
                    │          PHASE 3: API & WEBSOCKET       │
                    │        (Depends on Phase 2)             │
                    └─────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
    ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
    │   Task 3.1   │           │   Task 3.2   │           │   Task 3.3   │
    │   REST API   │           │  WebSocket   │           │    Event     │
    │   Endpoints  │           │   Server     │           │ Broadcaster  │
    │   (Codex)    │           │ (Claude Code)│           │   (Codex)    │
    └──────────────┘           └──────────────┘           └──────────────┘
           │                           │                           │
           └───────────────────────────┴───────────────────────────┘
                                       │
                    ┌─────────────────────────────────────────┐
                    │          PHASE 4: FRONTEND              │
                    │        (Depends on Phase 3)             │
                    └─────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
    ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
    │   Task 4.1   │           │   Task 4.2   │           │   Task 4.3   │
    │  Dashboard   │           │   Settings   │           │    Lists     │
    │     UI       │           │   Pages      │           │   Manager    │
    │ (Claude Code)│           │ (Claude Code)│           │ (Claude Code)│
    └──────────────┘           └──────────────┘           └──────────────┘
           │                           │                           │
           └───────────────────────────┴───────────────────────────┘
                                       │
                    ┌─────────────────────────────────────────┐
                    │          PHASE 5: POLISH                │
                    │        (Depends on Phase 4)             │
                    └─────────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           ▼                           ▼                           ▼
    ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
    │   Task 5.1   │           │   Task 5.2   │           │   Task 5.3   │
    │    Tests     │           │    Docs      │           │   Docker     │
    │              │           │              │           │   Polish     │
    │   (Codex)    │           │   (Cursor)   │           │   (Cursor)   │
    └──────────────┘           └──────────────┘           └──────────────┘
```

---

## PHASE 1: Foundation (Week 1)

### Task 1.1: Enhanced Settings System
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 4-6 hours
**Blocks:** All Phase 2 tasks

**Description:**
Enhance the Pydantic settings system to support all new features including user type settings, import lists configuration, and WebGUI persistence.

**Files to Create/Modify:**
- `src/config/settings.py` - Complete rewrite with all settings
- `src/config/defaults.py` - Default configurations
- `src/config/migrations.py` - Settings migration from old versions

**Requirements:**
```python
# Must support these configuration sections:
- PlexSettings (url, token, rate limiting)
- UserManagementSettings (per-type defaults, activity filtering)
- CacheLimitSettings (size, eviction, thresholds)
- RetentionSettings (per-source retention)
- ImportListsSettings (list configurations)
- WebGuiSettings (refresh rate, theme)
- NotificationSettings (webhooks, unraid)
- PathMappingSettings (multi-source support)

# Must support:
- JSON file persistence
- Environment variable override
- WebGUI modification & save
- Settings validation
- Migration from old format
```

**Prompt for Claude Code:**
```
Read docs/FEATURE_PARITY.md, docs/USER_MANAGEMENT_DESIGN.md, and 
docs/IMPORT_LISTS_DESIGN.md. Then implement a comprehensive Pydantic v2 
settings system in src/config/settings.py that supports all documented 
features. Include validation, JSON persistence, environment variable 
override, and WebGUI save capability. Reference the existing settings.py 
as a starting point but expand significantly.
```

---

### Task 1.2: Rate-Limited Plex Client
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 4-6 hours
**Blocks:** Task 2.1, 2.2, 2.3
**Can Parallel With:** Task 1.1, 1.3

**Description:**
Create a Plex API client with configurable rate limiting to prevent SQLite lock issues.

**Files to Create/Modify:**
- `src/core/plex_client.py` - Complete rewrite

**Requirements:**
```python
# Must implement:
- Configurable min request interval (ms)
- Configurable max requests per minute
- Request queuing and throttling
- Retry logic with exponential backoff
- Token caching for users
- Error handling with specific status codes
- User discovery (main, home, shared)
- OnDeck fetching per user
- Watchlist fetching per user
- Active session monitoring
- Media library searching (for import lists matching)
```

**Prompt for Claude Code:**
```
Read docs/USER_MANAGEMENT_DESIGN.md and docs/REALTIME_WEBGUI_DESIGN.md 
(rate limiting section). Implement a rate-limited Plex client in 
src/core/plex_client.py using plexapi. Must support configurable rate 
limits, user token management, and all methods needed for OnDeck, 
Watchlist, sessions, and library search. Include proper error handling 
and logging. The rate limiting must be thread-safe.
```

---

### Task 1.3: Database Schema
**Assignee:** Codex
**Complexity:** Medium
**Estimated Time:** 2-3 hours
**Blocks:** Task 2.1, 2.2
**Can Parallel With:** Task 1.1, 1.2

**Description:**
Create SQLite database schema and migration system for persistent data.

**Files to Create:**
- `src/db/schema.py` - SQLAlchemy models
- `src/db/migrations.py` - Database migrations
- `src/db/repository.py` - Data access layer

**Requirements:**
```sql
-- Tables needed:
- users (id, username, type, status, settings_json, last_seen)
- import_lists (id, name, type, config_json, last_refresh)
- import_list_items (list_id, title, ids_json, matched_path, cached)
- cache_tracking (file_path, source, cached_at, users_json, priority)
- activity_log (timestamp, event_type, details_json)
```

**Prompt for Codex:**
```
Create SQLite database schema using SQLAlchemy in src/db/. Include 
models for users, import_lists, import_list_items, cache_tracking, 
and activity_log. Add a migrations system and repository pattern 
for data access. See docs/USER_MANAGEMENT_DESIGN.md and 
docs/IMPORT_LISTS_DESIGN.md for schema requirements.
```

---

## PHASE 2: Core Systems (Week 2)

### Task 2.1: User Management System
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 6-8 hours
**Depends On:** Task 1.1, 1.2, 1.3
**Blocks:** Task 2.3, 3.1

**Description:**
Implement complete user management with Main/Home/Shared classification.

**Files to Create:**
- `src/core/user_manager.py` - User discovery and management
- `src/core/user_settings.py` - Per-user settings handling
- `src/core/activity_tracker.py` - Activity tracking

**Requirements:**
- Discover users from Plex (main, home, shared)
- Per-user caching settings
- Activity-based filtering
- User type defaults
- Enable/disable users
- Priority boost per user
- Last seen tracking

**Prompt for Claude Code:**
```
Read docs/USER_MANAGEMENT_DESIGN.md thoroughly. Implement the complete 
user management system including UserDiscoveryService, UserActivityTracker, 
and per-user settings. Users should be classified as main/home/shared 
with independent caching settings. Support activity-based filtering 
(only cache for users active in last X days). Integrate with the 
rate-limited Plex client from Task 1.2.
```

---

### Task 2.2: Import Lists System
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 8-10 hours
**Depends On:** Task 1.1, 1.2, 1.3
**Blocks:** Task 2.3
**Can Parallel With:** Task 2.1

**Description:**
Implement Radarr-style import lists with multiple providers.

**Files to Create:**
- `src/lists/manager.py` - Import lists manager
- `src/lists/providers/base.py` - Base provider class
- `src/lists/providers/trakt.py` - Trakt provider
- `src/lists/providers/tmdb.py` - TMDb provider
- `src/lists/providers/imdb.py` - IMDb provider
- `src/lists/providers/rss.py` - RSS/custom URL provider
- `src/lists/matcher.py` - Plex library matcher

**Requirements:**
- Configurable count per list
- Strict vs Fill mode
- Air date filtering
- Episodes per show setting
- Priority per list
- Refresh scheduling
- Plex library matching (IMDb ID, TMDb ID, title)

**Prompt for Claude Code:**
```
Read docs/IMPORT_LISTS_DESIGN.md thoroughly. Implement the complete 
import lists system with providers for Trakt (trending, popular, user 
lists), TMDb (trending, popular), IMDb (top 250), and custom RSS. 
Implement the Strict/Fill modes for handling missing media. Include 
air date filtering and Plex library matching. The system should support 
both movies and TV shows.
```

---

### Task 2.3: Enhanced Cache Manager
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 6-8 hours
**Depends On:** Task 1.1, 1.2, 2.1, 2.2
**Blocks:** Task 3.1, 3.2

**Description:**
Integrate all systems into the central cache manager.

**Files to Modify:**
- `src/core/cache_manager.py` - Complete rewrite

**Requirements:**
- Integrate user management (per-user OnDeck/Watchlist)
- Integrate import lists
- User-aware priority scoring
- Staleness filtering (OnDeck age, Watchlist availability age)
- Event emission for WebSocket
- Progress tracking for operations

**Prompt for Claude Code:**
```
Rewrite src/core/cache_manager.py to integrate the user management 
system (Task 2.1) and import lists system (Task 2.2). The cache 
manager should respect per-user settings, apply staleness filters, 
calculate user-aware priorities, and emit events for real-time WebGUI 
updates. Reference docs/FEATURE_PARITY.md for all required features.
```

---

## PHASE 3: API & WebSocket (Week 3)

### Task 3.1: REST API Endpoints
**Assignee:** Codex
**Complexity:** Medium
**Estimated Time:** 4-5 hours
**Depends On:** Task 2.1, 2.2, 2.3
**Blocks:** Task 4.1, 4.2, 4.3
**Can Parallel With:** Task 3.2, 3.3

**Description:**
Create comprehensive REST API for all operations.

**Files to Modify:**
- `src/api/routes.py` - Expand with all endpoints

**Endpoints Needed:**
```
# Health & Status
GET  /api/health
GET  /api/status

# Cache Operations
GET  /api/cache/stats
GET  /api/cache/files
POST /api/cache/cycle
POST /api/cache/reconcile
POST /api/cache/evict
DELETE /api/cache/file/:path

# Users
GET  /api/users
GET  /api/users/:id
PUT  /api/users/:id
POST /api/users/:id/enable
POST /api/users/:id/disable
POST /api/users/refresh
GET  /api/users/types/defaults
PUT  /api/users/types/defaults

# Import Lists
GET  /api/lists
POST /api/lists
GET  /api/lists/:id
PUT  /api/lists/:id
DELETE /api/lists/:id
POST /api/lists/:id/refresh
GET  /api/lists/:id/items
GET  /api/lists/presets

# Sessions
GET  /api/sessions

# Configuration
GET  /api/config
PUT  /api/config
GET  /api/config/schema
```

**Prompt for Codex:**
```
Expand src/api/routes.py with comprehensive REST endpoints for users, 
import lists, cache operations, and configuration. Follow the endpoint 
list in TASKS.md Task 3.1. Use Flask blueprints and include proper 
error handling, validation, and CORS support. Return consistent 
JSON responses.
```

---

### Task 3.2: WebSocket Server
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 4-5 hours
**Depends On:** Task 2.3
**Blocks:** Task 4.1
**Can Parallel With:** Task 3.1, 3.3

**Description:**
Implement Flask-SocketIO for real-time updates.

**Files to Create:**
- `src/api/websocket.py` - WebSocket handler
- `src/api/events.py` - Event definitions

**Requirements:**
- Connection handling
- Event subscription
- Client tracking
- Reconnection support
- Event types: status, stats, operation_progress, operation_complete, session, log, cycle

**Prompt for Claude Code:**
```
Read docs/REALTIME_WEBGUI_DESIGN.md. Implement WebSocket server using 
Flask-SocketIO in src/api/websocket.py. Support all event types 
documented: status, stats, operation_progress, operation_complete, 
session_start/update/end, log, cycle_start/progress/complete. 
Include proper connection handling and client tracking.
```

---

### Task 3.3: Event Broadcaster
**Assignee:** Codex
**Complexity:** Medium
**Estimated Time:** 2-3 hours
**Depends On:** Task 2.3
**Can Parallel With:** Task 3.1, 3.2

**Description:**
Create event broadcaster to emit events to WebSocket clients.

**Files to Create:**
- `src/core/broadcaster.py` - Event broadcaster

**Requirements:**
- Thread-safe event emission
- Progress tracking for file copies
- Log forwarding
- Cycle progress reporting

**Prompt for Codex:**
```
Create src/core/broadcaster.py that broadcasts events to WebSocket 
clients. Include methods for emitting status, stats, operation progress, 
operation completion, session events, logs, and cycle progress. 
Reference docs/REALTIME_WEBGUI_DESIGN.md for event schemas.
```

---

## PHASE 4: Frontend (Week 4)

### Task 4.1: Dashboard UI
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 8-10 hours
**Depends On:** Task 3.1, 3.2
**Can Parallel With:** Task 4.2, 4.3

**Description:**
Create the main dashboard with real-time updates.

**Files to Create:**
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/components/StatsCards.tsx`
- `frontend/src/components/ActiveOperations.tsx`
- `frontend/src/components/SessionList.tsx`
- `frontend/src/components/CachedFilesList.tsx`
- `frontend/src/components/ActivityFeed.tsx`
- `frontend/src/hooks/useWebSocket.ts`

**Requirements:**
- Cache stats display
- Active operations with progress bars
- Real-time session monitoring
- Cached files table
- Live activity feed
- WebSocket integration
- Configurable refresh rate
- Responsive design

**Prompt for Claude Code:**
```
Read docs/REALTIME_WEBGUI_DESIGN.md. Create the main Dashboard UI in 
React with TypeScript. Include real-time updates via WebSocket, 
stats cards, active operations with progress bars, session list, 
cached files table, and activity feed. Use Tailwind CSS for styling. 
Make it responsive for mobile. Reference frontend/src/types/cache.ts 
for type definitions.
```

---

### Task 4.2: Settings Pages
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 6-8 hours
**Depends On:** Task 3.1
**Can Parallel With:** Task 4.1, 4.3

**Description:**
Create settings pages for all configuration.

**Files to Create:**
- `frontend/src/pages/Settings.tsx`
- `frontend/src/pages/settings/GeneralSettings.tsx`
- `frontend/src/pages/settings/PlexSettings.tsx`
- `frontend/src/pages/settings/CacheSettings.tsx`
- `frontend/src/pages/settings/RetentionSettings.tsx`
- `frontend/src/pages/settings/NotificationSettings.tsx`
- `frontend/src/pages/settings/PathMappings.tsx`

**Requirements:**
- All settings from design docs
- Form validation
- Save/reset functionality
- Path mapping editor
- Test connection button

**Prompt for Claude Code:**
```
Create comprehensive settings pages in React for all Cacherr 
configuration. Include General, Plex, Cache, Retention, Notifications, 
and Path Mappings sections. Add form validation, save/reset buttons, 
and a test connection feature. Use Tailwind CSS and make forms 
user-friendly with helpful descriptions.
```

---

### Task 4.3: Users & Lists Management UI
**Assignee:** Claude Code (Opus)
**Complexity:** High
**Estimated Time:** 6-8 hours
**Depends On:** Task 3.1
**Can Parallel With:** Task 4.1, 4.2

**Description:**
Create UI for user management and import lists.

**Files to Create:**
- `frontend/src/pages/Users.tsx`
- `frontend/src/components/UserCard.tsx`
- `frontend/src/components/UserSettingsDialog.tsx`
- `frontend/src/components/UserTypeDefaults.tsx`
- `frontend/src/pages/ImportLists.tsx`
- `frontend/src/components/ListCard.tsx`
- `frontend/src/components/AddListDialog.tsx`
- `frontend/src/components/ListItemsPreview.tsx`

**Requirements:**
- User list grouped by type (Main/Home/Shared)
- User enable/disable toggle
- Per-user settings dialog
- Activity filtering controls
- Import lists management
- Add/edit list dialogs
- List presets selection
- Items preview

**Prompt for Claude Code:**
```
Read docs/USER_MANAGEMENT_DESIGN.md and docs/IMPORT_LISTS_DESIGN.md.
Create Users page showing all Plex users grouped by type (Main/Home/Shared)
with enable/disable toggles, activity indicators, and settings dialogs.
Create Import Lists page with list management, add/edit dialogs 
supporting all list types and settings. Use Tailwind CSS.
```

---

## PHASE 5: Polish (Week 5)

### Task 5.1: Unit & Integration Tests
**Assignee:** Codex
**Complexity:** Medium
**Estimated Time:** 6-8 hours
**Depends On:** All Phase 2-4 tasks

**Files to Create:**
- `tests/test_settings.py`
- `tests/test_plex_client.py`
- `tests/test_user_manager.py`
- `tests/test_import_lists.py`
- `tests/test_cache_manager.py`
- `tests/test_api.py`

**Prompt for Codex:**
```
Create comprehensive unit tests using pytest for settings, plex client, 
user manager, import lists, cache manager, and API endpoints. 
Include mock Plex server responses. Aim for 80%+ coverage on 
core business logic.
```

---

### Task 5.2: Documentation
**Assignee:** Cursor
**Complexity:** Low
**Estimated Time:** 3-4 hours
**Depends On:** All Phase 2-4 tasks
**Can Parallel With:** Task 5.1, 5.3

**Files to Create/Update:**
- `README.md` - Main readme
- `docs/INSTALLATION.md`
- `docs/CONFIGURATION.md`
- `docs/API.md`
- `docs/TROUBLESHOOTING.md`

**Prompt for Cursor:**
```
Update README.md with installation instructions, quick start guide, 
and feature overview. Create INSTALLATION.md with Docker setup, 
CONFIGURATION.md with all settings explained, API.md with endpoint 
documentation, and TROUBLESHOOTING.md with common issues and solutions.
```

---

### Task 5.3: Docker & Deployment Polish
**Assignee:** Cursor
**Complexity:** Low
**Estimated Time:** 2-3 hours
**Depends On:** All Phase 2-4 tasks
**Can Parallel With:** Task 5.1, 5.2

**Files to Update:**
- `Dockerfile`
- `docker-compose.yml`
- `docker/cacherr.xml`
- `.dockerignore`
- `entrypoint.sh`

**Prompt for Cursor:**
```
Polish Docker configuration: optimize Dockerfile for smaller image, 
ensure docker-compose.yml has all necessary mounts documented, 
verify Unraid XML template works, create entrypoint.sh for proper 
startup, and add .dockerignore for efficient builds.
```

---

## Parallel Execution Summary

### Week 1 (Foundation)
```
Day 1-2: Task 1.1 (Claude Code) ─┬─ Task 1.2 (Claude Code) ─┬─ Task 1.3 (Codex)
                                 │                          │
                                 └──────────────────────────┴─────────────────┐
                                                                              ▼
                                                                      Phase 1 Complete
```

### Week 2 (Core Systems)
```
Day 3-5: Task 2.1 (Claude Code) ──┬── Task 2.2 (Claude Code)
                                  │
                                  └───────────┬───────────────────────────────┐
                                              ▼                               │
Day 6-7:                          Task 2.3 (Claude Code) ◄────────────────────┘
```

### Week 3 (API & WebSocket)
```
Day 8-10: Task 3.1 (Codex) ──┬── Task 3.2 (Claude Code) ──┬── Task 3.3 (Codex)
                             │                             │
                             └─────────────────────────────┴──────────────────┐
                                                                              ▼
                                                                      Phase 3 Complete
```

### Week 4 (Frontend)
```
Day 11-14: Task 4.1 (Claude Code) ──┬── Task 4.2 (Claude Code) ──┬── Task 4.3 (Claude Code)
                                    │                             │
                                    └─────────────────────────────┴────────────────────────┐
                                                                                           ▼
                                                                                   Phase 4 Complete
```

### Week 5 (Polish)
```
Day 15-17: Task 5.1 (Codex) ──┬── Task 5.2 (Cursor) ──┬── Task 5.3 (Cursor)
                              │                        │
                              └────────────────────────┴──────────────────────┐
                                                                              ▼
                                                                         DONE! 🎉
```

---

## Quick Reference

| Task | Assignee | Depends On | Can Parallel |
|------|----------|------------|--------------|
| 1.1 Settings | Claude Code | - | 1.2, 1.3 |
| 1.2 Plex Client | Claude Code | - | 1.1, 1.3 |
| 1.3 Database | Codex | - | 1.1, 1.2 |
| 2.1 Users | Claude Code | 1.1, 1.2, 1.3 | 2.2 |
| 2.2 Lists | Claude Code | 1.1, 1.2, 1.3 | 2.1 |
| 2.3 Cache Mgr | Claude Code | 2.1, 2.2 | - |
| 3.1 REST API | Codex | 2.3 | 3.2, 3.3 |
| 3.2 WebSocket | Claude Code | 2.3 | 3.1, 3.3 |
| 3.3 Broadcaster | Codex | 2.3 | 3.1, 3.2 |
| 4.1 Dashboard | Claude Code | 3.1, 3.2 | 4.2, 4.3 |
| 4.2 Settings UI | Claude Code | 3.1 | 4.1, 4.3 |
| 4.3 Users/Lists UI | Claude Code | 3.1 | 4.1, 4.2 |
| 5.1 Tests | Codex | Phase 4 | 5.2, 5.3 |
| 5.2 Docs | Cursor | Phase 4 | 5.1, 5.3 |
| 5.3 Docker | Cursor | Phase 4 | 5.1, 5.2 |
