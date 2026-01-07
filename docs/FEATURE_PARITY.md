# Cacherr Feature Parity Analysis

## Overview

This document analyzes all features from the original Cacherr/PlexCache codebase and tracks which features need to be implemented in the fresh implementation.

---

## 1. CONFIGURATION SYSTEM

| Feature | Old Code Location | New Implementation | Status |
|---------|-------------------|-------------------|--------|
| **JSON config file** | `config.py:ConfigManager` | `settings.py:CacherrSettings.from_file()` | ✅ Basic |
| **Environment variables** | scattered | `settings.py:CacherrSettings.from_env()` | ✅ Basic |
| **Web GUI config** | Not implemented | Required | ⏳ TODO |
| **Path mappings (multi-source)** | `config.py:PathMapping` | Needs enhancement | ⏳ TODO |
| **Legacy path migration** | `config.py:migrate_path_settings()` | Not needed (fresh start) | ⬜ Skip |
| **Config validation** | `config.py:_validate_*()` | Pydantic validators | ✅ Done |
| **Settings persistence** | `config.py:_save_updated_config()` | `settings.py:save()` | ✅ Done |

---

## 2. PLEX USER MANAGEMENT

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Main account detection** | `plex_api.py:_get_main_account()` | HIGH | ⏳ TODO |
| **Home users (local)** | `plex_api.py:load_user_tokens()` | HIGH | ⏳ TODO |
| **Shared users (remote)** | `plex_api.py:_discover_new_users()` | HIGH | ⏳ TODO |
| **User token caching** | `plex_api.py:UserTokenCache` | MEDIUM | ⏳ TODO |
| **UUID/ID to username mapping** | `plex_api.py:_user_id_to_name` | MEDIUM | ⏳ TODO |
| **Skip users for OnDeck** | `config.py:skip_ondeck` | HIGH | ⏳ TODO |
| **Skip users for Watchlist** | `config.py:skip_watchlist` | HIGH | ⏳ TODO |
| **Per-user settings (NEW)** | Not in old code | HIGH | ⏳ TODO |
| **Last login tracking (NEW)** | Not in old code | MEDIUM | ⏳ TODO |
| **Activity-based filtering (NEW)** | Not in old code | MEDIUM | ⏳ TODO |

### NEW: User Type Separation
The user wants independent settings for:
- **Main user** (admin account)
- **Home users** (local family members)
- **Shared users** (remote friends)

Each user type should have independent toggles for:
- OnDeck caching enabled
- Watchlist caching enabled
- List caching enabled
- Currently watching caching enabled
- Max OnDeck staleness (days)
- Max Watchlist staleness (days)

---

## 3. PLEX API INTEGRATION

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Server connection** | `plex_api.py:PlexManager.connect()` | HIGH | ✅ Done |
| **Rate limiting** | `plex_api.py:PLEX_API_DELAY` | HIGH | ⏳ TODO |
| **API call locking** | `plex_api.py:_api_lock` | HIGH | ⏳ TODO |
| **Offline resilience** | `plex_api.py:_plex_tv_reachable` | MEDIUM | ⏳ TODO |
| **Error logging with codes** | `plex_api.py:_log_api_error()` | MEDIUM | ⏳ TODO |
| **Retry logic** | Throughout | MEDIUM | ⏳ TODO |
| **Active session detection** | `plex_api.py:get_active_sessions()` | HIGH | ✅ Done |

### Configurable API Settings
User requested configurable Plex API ping frequency due to SQLite lock issues:
- **plex_api_delay_ms**: Delay between plex.tv calls (default: 1000ms)
- **plex_api_max_retries**: Max retry attempts (default: 3)
- **plex_session_check_interval**: Seconds between session checks (default: 30)
- **plex_ondeck_refresh_interval**: Seconds between OnDeck refreshes

---

## 4. ONDECK CACHING

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Fetch OnDeck items** | `plex_api.py:get_ondeck_files()` | HIGH | ✅ Basic |
| **Episodes ahead** | `config.py:number_episodes` | HIGH | ✅ Done |
| **Days to monitor** | `config.py:days_to_monitor` | HIGH | ✅ Done |
| **Episode info tracking** | `plex_api.py:OnDeckItem.episode_info` | HIGH | ✅ Done |
| **Current vs prefetched** | `plex_api.py:OnDeckItem.is_current_ondeck` | HIGH | ✅ Done |
| **OnDeck staleness (NEW)** | Not in old code | MEDIUM | ⏳ TODO |
| **Per-user OnDeck settings (NEW)** | Not in old code | MEDIUM | ⏳ TODO |

---

## 5. WATCHLIST CACHING

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Fetch watchlist items** | `plex_api.py:get_watchlist_files()` | HIGH | ✅ Basic |
| **Episodes per show** | `config.py:watchlist_episodes` | HIGH | ✅ Done |
| **Remote RSS watchlist** | `plex_api.py:_parse_rss_response()` | MEDIUM | ⏳ TODO |
| **Watchlist retention days** | `config.py:watchlist_retention_days` | HIGH | ✅ Done |
| **Watchlist tracker** | `file_operations.py:WatchlistTracker` | HIGH | ✅ Done |
| **Availability date filtering (NEW)** | Not in old code | MEDIUM | ⏳ TODO |
| **Per-user watchlist settings (NEW)** | Not in old code | MEDIUM | ⏳ TODO |

---

## 6. IMPORT LISTS SYSTEM (NEW - Radarr-style)

This is a NEW feature requested by user. Needs full design.

### List Sources
| Source | Type | Priority |
|--------|------|----------|
| **Trakt Trending Movies** | Movies | HIGH |
| **Trakt Popular Movies** | Movies | HIGH |
| **Trakt Trending Shows** | TV | HIGH |
| **Trakt Popular Shows** | TV | HIGH |
| **Trakt User Watchlist** | Both | MEDIUM |
| **Trakt User Lists** | Both | MEDIUM |
| **IMDb Top 250** | Movies | MEDIUM |
| **IMDb Popular** | Both | MEDIUM |
| **TMDb Trending** | Both | MEDIUM |
| **TMDb Popular** | Both | MEDIUM |
| **Custom RSS** | Both | MEDIUM |
| **Custom URL** | Both | LOW |

### List Settings
| Setting | Description | Default |
|---------|-------------|---------|
| **count** | Max items from list | 10 |
| **mode** | "strict" (only top N) or "fill" (keep going until N available) | "strict" |
| **fill_limit** | Max position in list to check when fill mode | 100 |
| **air_date_filter** | Only cache if aired within X days | 0 (disabled) |
| **enabled** | Toggle list on/off | true |
| **priority** | List priority for eviction | 50 |

---

## 7. CACHE RETENTION & EVICTION

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Cache retention hours** | `config.py:cache_retention_hours` | HIGH | ✅ Done |
| **Cache size limit** | `config.py:cache_limit` | HIGH | ✅ Done |
| **Limit parsing (GB/MB/%)** | `config.py:_parse_cache_limit()` | HIGH | ✅ Done |
| **Eviction mode (smart/fifo/none)** | `config.py:cache_eviction_mode` | HIGH | ✅ Done |
| **Eviction threshold %** | `config.py:cache_eviction_threshold_percent` | HIGH | ✅ Done |
| **Eviction min priority** | `config.py:eviction_min_priority` | HIGH | ✅ Done |
| **Move watched content** | `config.py:watched_move` | HIGH | ✅ Done |

---

## 8. PRIORITY SCORING

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Base scoring (0-100)** | `file_operations.py:CachePriorityManager` | HIGH | ✅ Done |
| **Source type bonus** | +20 ondeck, +0 watchlist | HIGH | ✅ Done |
| **User count bonus** | +5 per user (max +15) | HIGH | ✅ Done |
| **Cache recency bonus** | +5 to +15 based on hours | HIGH | ✅ Done |
| **Watchlist age factor** | +10 fresh, -10 if >60 days | MEDIUM | ✅ Done |
| **OnDeck age factor** | +10 recent, -10 stale | MEDIUM | ✅ Done |
| **Episode position bonus** | +15 current, +10 next | HIGH | ✅ Done |
| **Currently playing protection** | Score = 100 | HIGH | ✅ Done |

---

## 9. FILE OPERATIONS

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Atomic symlink creation** | Throughout file_operations.py | HIGH | ✅ Done |
| **.plexcached backup system** | `file_operations.py:PLEXCACHED_EXTENSION` | HIGH | ✅ Done |
| **Subtitle handling** | `file_operations.py:SubtitleFinder` | HIGH | ✅ Done |
| **Multi-path modifier** | `file_operations.py:MultiPathModifier` | MEDIUM | ⏳ TODO |
| **Concurrent moves (cache)** | `config.py:max_concurrent_moves_cache` | HIGH | ✅ Done |
| **Concurrent moves (array)** | `config.py:max_concurrent_moves_array` | HIGH | ✅ Done |
| **Retry logic** | `config.py:retry_limit, delay` | MEDIUM | ⏳ TODO |
| **Permissions setting** | `config.py:permissions` | LOW | ⏳ TODO |

---

## 10. TRACKING SYSTEM

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Cache timestamp tracker** | `file_operations.py:CacheTimestampTracker` | HIGH | ✅ Done |
| **Watchlist tracker** | `file_operations.py:WatchlistTracker` | HIGH | ✅ Done |
| **OnDeck tracker** | `file_operations.py:OnDeckTracker` | HIGH | ✅ Done |
| **Episode info storage** | In OnDeck tracker | HIGH | ✅ Done |
| **User tracking per file** | In all trackers | HIGH | ✅ Done |
| **Stale entry cleanup** | `*_tracker.cleanup_stale_entries()` | MEDIUM | ✅ Done |

---

## 11. SYSTEM FEATURES

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Instance lock** | `system_utils.py:SingleInstanceLock` | HIGH | ✅ Done |
| **Unraid mover detection** | `plexcache_app.py:_is_mover_running()` | MEDIUM | ⏳ TODO |
| **Unraid mover exclusions** | `plexcache_app.py:_update_unraid_mover_exclusions()` | MEDIUM | ⏳ TODO |
| **Dry-run mode** | Throughout | HIGH | ✅ Done |
| **Debug mode** | `config.py:debug` | HIGH | ✅ Done |
| **Exit if active session** | `config.py:exit_if_active_session` | MEDIUM | ✅ Done |

---

## 12. NOTIFICATIONS

| Feature | Old Code Location | Priority | Status |
|---------|-------------------|----------|--------|
| **Discord webhook** | `config.py:NotificationConfig` | MEDIUM | ⏳ TODO |
| **Slack webhook** | `config.py:NotificationConfig` | MEDIUM | ⏳ TODO |
| **Unraid notifications** | `config.py:notification_type` | MEDIUM | ⏳ TODO |
| **Notification levels** | `config.py:unraid_level, webhook_level` | MEDIUM | ⏳ TODO |

---

## 13. WEB INTERFACE (NEW/ENHANCED)

| Feature | Old Code | Priority | Status |
|---------|----------|----------|--------|
| **Dashboard** | Minimal | HIGH | ⏳ TODO |
| **Real-time updates** | None | HIGH | ⏳ TODO |
| **WebSocket support** | None | HIGH | ⏳ TODO |
| **Configurable refresh rate** | None | MEDIUM | ⏳ TODO |
| **User management UI** | None | HIGH | ⏳ TODO |
| **Import Lists UI** | None | HIGH | ⏳ TODO |
| **Progress bars** | Broken | HIGH | ⏳ TODO |
| **Live activity feed** | None | MEDIUM | ⏳ TODO |
| **Config editor** | None | HIGH | ⏳ TODO |
| **Mobile responsive** | Unknown | MEDIUM | ⏳ TODO |

---

## 14. DOCKER CONFIGURATION

| Feature | Priority | Status |
|---------|----------|--------|
| **Multi-source volume mounts** | HIGH | ⏳ TODO |
| **Cache volume mount** | HIGH | ✅ Done |
| **Config volume mount** | HIGH | ✅ Done |
| **Port mapping** | HIGH | ✅ Done |
| **Health check** | HIGH | ✅ Done |
| **Unraid XML template** | HIGH | ⏳ TODO |
| **Environment variables (minimal)** | HIGH | ✅ Done |

---

## Summary

### Critical Missing Features (Must Have)
1. ⏳ User management (Main/Home/Shared distinction with per-type settings)
2. ⏳ Import Lists system (Radarr-style)
3. ⏳ Real-time WebGUI updates (WebSocket)
4. ⏳ Plex API rate limiting
5. ⏳ Multi-path source support
6. ⏳ Unraid mover integration
7. ⏳ Notifications

### Important Missing Features (Should Have)
1. ⏳ Activity-based user filtering (last login X days)
2. ⏳ Air date / availability filtering for lists
3. ⏳ Per-user independent settings
4. ⏳ RSS watchlist support
5. ⏳ Offline resilience

### Nice to Have
1. ⏳ Mobile responsive UI
2. ⏳ Configurable refresh rates
3. ⏳ Live activity feed
4. ⏳ File permissions setting

---

## Next Steps

1. **Design**: User management system with Main/Home/Shared types
2. **Design**: Import Lists system (Radarr-inspired)
3. **Implement**: Plex API rate limiting and retry logic
4. **Implement**: WebSocket for real-time updates
5. **Create**: Unraid XML template
6. **Delegate**: Frontend to Claude Code
