# Import Lists System Design

## Overview

The Import Lists system allows users to automatically cache media from various external sources (Trakt, IMDb, TMDb, RSS, etc.) with configurable settings per list.

Inspired by Radarr's Import Lists feature: https://wiki.servarr.com/radarr/supported

---

## Core Concepts

### List Types
1. **Preset Lists** - Pre-configured popular lists (Trakt Trending, IMDb Top 250, etc.)
2. **Custom Lists** - User-provided URLs or RSS feeds
3. **User Lists** - Lists from user's own accounts (Trakt watchlist, etc.)

### Media Types
- **Movies** - Feature films
- **TV Shows** - Series (caches episodes based on settings)

### Matching
Lists contain media titles/IDs. Cacherr matches them against the user's Plex library to find available media to cache.

---

## Configuration Model

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum

class ListType(str, Enum):
    TRAKT_TRENDING_MOVIES = "trakt_trending_movies"
    TRAKT_POPULAR_MOVIES = "trakt_popular_movies"
    TRAKT_TRENDING_SHOWS = "trakt_trending_shows"
    TRAKT_POPULAR_SHOWS = "trakt_popular_shows"
    TRAKT_USER_WATCHLIST = "trakt_user_watchlist"
    TRAKT_USER_LIST = "trakt_user_list"
    IMDB_TOP_250 = "imdb_top_250"
    IMDB_POPULAR = "imdb_popular"
    TMDB_TRENDING = "tmdb_trending"
    TMDB_POPULAR = "tmdb_popular"
    CUSTOM_RSS = "custom_rss"
    CUSTOM_URL = "custom_url"

class FillMode(str, Enum):
    STRICT = "strict"  # Only cache from top N positions
    FILL = "fill"      # Keep going until N items are cached

class ImportList(BaseModel):
    """Configuration for a single import list."""
    
    # Identity
    id: str = Field(..., description="Unique identifier for this list")
    name: str = Field(..., description="Display name for this list")
    enabled: bool = Field(default=True, description="Whether this list is active")
    
    # List source
    list_type: ListType = Field(..., description="Type of list")
    url: Optional[str] = Field(default=None, description="URL for custom lists")
    
    # Trakt settings (when applicable)
    trakt_username: Optional[str] = Field(default=None, description="Trakt username for user lists")
    trakt_list_name: Optional[str] = Field(default=None, description="Trakt list name for user lists")
    
    # Media filtering
    media_type: Literal["movies", "shows", "both"] = Field(default="both")
    
    # Count settings
    count: int = Field(default=10, ge=1, le=500, description="Number of items to cache")
    fill_mode: FillMode = Field(default=FillMode.STRICT, description="How to handle missing media")
    fill_limit: int = Field(default=100, ge=1, le=1000, description="Max list position to check in fill mode")
    
    # Date filtering
    air_date_within_days: int = Field(
        default=0, ge=0,
        description="Only cache if last aired within X days (0 = disabled)"
    )
    
    # TV Show specific
    episodes_per_show: int = Field(default=1, ge=1, le=20, description="Episodes to cache per show")
    
    # Priority
    priority: int = Field(default=50, ge=0, le=100, description="Priority for eviction (higher = keep longer)")
    
    # Scheduling
    refresh_interval_hours: int = Field(default=6, ge=1, description="Hours between list refreshes")
    last_refresh: Optional[str] = Field(default=None, description="ISO timestamp of last refresh")

class ImportListsSettings(BaseModel):
    """Settings for all import lists."""
    
    enabled: bool = Field(default=True, description="Master toggle for import lists")
    lists: List[ImportList] = Field(default_factory=list, description="Configured lists")
    
    # Global defaults
    default_fill_mode: FillMode = Field(default=FillMode.STRICT)
    default_count: int = Field(default=10)
    default_air_date_within_days: int = Field(default=0)
    
    # API settings
    trakt_client_id: str = Field(default="", description="Trakt API client ID")
    trakt_client_secret: str = Field(default="", description="Trakt API client secret")
    tmdb_api_key: str = Field(default="", description="TMDb API key")
```

---

## Fill Modes Explained

### Strict Mode (`FillMode.STRICT`)
- Request top N items from the list
- Only cache what the user has in their library
- If user only has 5 of top 25, only 5 get cached

**Example:**
```
List: Top 25 Trending Movies
User has: 5 of them
Result: 5 movies cached
```

### Fill Mode (`FillMode.FILL`)
- Request items from list until N are cached
- Keep going down the list to find available media
- Stop at fill_limit to prevent infinite loops

**Example:**
```
List: Top 25 Trending Movies (fill mode, fill_limit=100)
User has: 5 in top 25, but has 20 more in positions 26-100
Result: 25 movies cached (first 5 + 20 more)
```

---

## Air Date Filtering

For lists like "Trending" or "Popular", the user may want to only cache recently aired content.

### Example Use Cases:
- "Only cache trending shows if an episode aired in the last 30 days"
- "Skip movies in the list that came out more than 90 days ago"

### Implementation:
```python
def should_cache_from_list(media_item, list_config: ImportList) -> bool:
    """Check if media passes list filters."""
    
    # Check air date filter
    if list_config.air_date_within_days > 0:
        last_aired = get_last_air_date(media_item)
        if last_aired:
            days_since_aired = (datetime.now() - last_aired).days
            if days_since_aired > list_config.air_date_within_days:
                return False  # Too old
    
    return True
```

---

## List Providers Implementation

### Trakt Provider
```python
class TraktListProvider:
    """Fetches lists from Trakt.tv API."""
    
    API_BASE = "https://api.trakt.tv"
    
    def __init__(self, client_id: str, client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_trending_movies(self, limit: int = 100) -> List[MediaItem]:
        """Get trending movies."""
        url = f"{self.API_BASE}/movies/trending?limit={limit}"
        return self._fetch_list(url)
    
    def get_popular_movies(self, limit: int = 100) -> List[MediaItem]:
        """Get popular movies."""
        url = f"{self.API_BASE}/movies/popular?limit={limit}"
        return self._fetch_list(url)
    
    def get_trending_shows(self, limit: int = 100) -> List[MediaItem]:
        """Get trending TV shows."""
        url = f"{self.API_BASE}/shows/trending?limit={limit}"
        return self._fetch_list(url)
    
    def get_user_watchlist(self, username: str) -> List[MediaItem]:
        """Get a user's watchlist."""
        url = f"{self.API_BASE}/users/{username}/watchlist"
        return self._fetch_list(url)
    
    def get_user_list(self, username: str, list_name: str) -> List[MediaItem]:
        """Get a specific user list."""
        url = f"{self.API_BASE}/users/{username}/lists/{list_name}/items"
        return self._fetch_list(url)
```

### TMDb Provider
```python
class TMDbListProvider:
    """Fetches lists from TMDb API."""
    
    API_BASE = "https://api.themoviedb.org/3"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_trending(self, media_type: str = "all", time_window: str = "week") -> List[MediaItem]:
        """Get trending content."""
        url = f"{self.API_BASE}/trending/{media_type}/{time_window}?api_key={self.api_key}"
        return self._fetch_list(url)
    
    def get_popular_movies(self) -> List[MediaItem]:
        """Get popular movies."""
        url = f"{self.API_BASE}/movie/popular?api_key={self.api_key}"
        return self._fetch_list(url)
```

### IMDb Provider
```python
class IMDbListProvider:
    """Fetches lists from IMDb (via scraping or API)."""
    
    def get_top_250(self) -> List[MediaItem]:
        """Get IMDb Top 250 movies."""
        # Implementation using IMDb API or scraping
        pass
    
    def get_popular(self, media_type: str = "movies") -> List[MediaItem]:
        """Get IMDb popular content."""
        pass
```

---

## Media Matching

Lists return titles/IDs that need to be matched against the user's Plex library.

### Matching Strategy
1. **IMDb ID** - Most reliable (if available)
2. **TMDb ID** - Very reliable (if available)
3. **TVDB ID** - For TV shows
4. **Title + Year** - Fallback matching

### Implementation
```python
class PlexLibraryMatcher:
    """Matches external media to Plex library items."""
    
    def __init__(self, plex_client: PlexClient):
        self.plex = plex_client
        self._cache = {}  # Cache library for performance
    
    def find_match(self, media_item: MediaItem) -> Optional[PlexMedia]:
        """Find a Plex library item matching the external media."""
        
        # Try IMDb ID first
        if media_item.imdb_id:
            match = self._search_by_guid(f"imdb://{media_item.imdb_id}")
            if match:
                return match
        
        # Try TMDb ID
        if media_item.tmdb_id:
            match = self._search_by_guid(f"tmdb://{media_item.tmdb_id}")
            if match:
                return match
        
        # Fallback to title search
        return self._search_by_title(media_item.title, media_item.year)
    
    def get_available_from_list(
        self, 
        items: List[MediaItem], 
        count: int,
        fill_mode: FillMode,
        fill_limit: int = 100
    ) -> List[PlexMedia]:
        """Get available Plex media from a list."""
        
        matched = []
        checked = 0
        
        for item in items:
            if len(matched) >= count:
                break
            
            if fill_mode == FillMode.STRICT and checked >= count:
                break
            
            if checked >= fill_limit:
                break
            
            match = self.find_match(item)
            if match:
                matched.append(match)
            
            checked += 1
        
        return matched
```

---

## Web UI Design

### Lists Management Page
```
┌─────────────────────────────────────────────────────────────────────┐
│ Import Lists                                           [+ Add List] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ☑ Trakt Trending Movies                         [Edit] [Delete] │ │
│ │   Top 10 movies • Strict mode • Last refresh: 2h ago           │ │
│ │   Currently caching: 8 of 10                                   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ☑ Trakt Popular Shows                           [Edit] [Delete] │ │
│ │   Top 5 shows • Fill mode (limit: 50) • Air date: 30 days     │ │
│ │   Currently caching: 5 of 5 (checked 23 positions)            │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ☐ IMDb Top 250 (disabled)                       [Edit] [Delete] │ │
│ │   Top 25 movies • Strict mode                                   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Add/Edit List Dialog
```
┌─────────────────────────────────────────────────────────────────────┐
│ Add Import List                                              [×]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ List Type: [Trakt Trending Movies ▼]                                │
│                                                                     │
│ Name: [Trakt Trending Movies          ]                             │
│                                                                     │
│ ─── Count Settings ───                                              │
│                                                                     │
│ Items to cache: [10    ]                                            │
│                                                                     │
│ Fill Mode: ( ) Strict - Only cache from top N positions            │
│            (•) Fill - Keep going until N items cached               │
│                                                                     │
│ Max position to check: [100   ] (fill mode only)                    │
│                                                                     │
│ ─── Filtering ───                                                   │
│                                                                     │
│ Only if aired within: [0     ] days (0 = disabled)                  │
│                                                                     │
│ ─── TV Show Settings ───                                            │
│                                                                     │
│ Episodes per show: [1     ]                                         │
│                                                                     │
│ ─── Priority ───                                                    │
│                                                                     │
│ Eviction priority: [50    ] (0-100, higher = keep longer)          │
│                                                                     │
│ ─── Scheduling ───                                                  │
│                                                                     │
│ Refresh every: [6     ] hours                                       │
│                                                                     │
│                                    [Cancel]  [Save]                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

```
GET  /api/lists              - Get all configured lists
POST /api/lists              - Add a new list
GET  /api/lists/:id          - Get a specific list
PUT  /api/lists/:id          - Update a list
DELETE /api/lists/:id        - Delete a list
POST /api/lists/:id/refresh  - Force refresh a list
GET  /api/lists/:id/items    - Get items from a list
GET  /api/lists/presets      - Get available preset list types
```

---

## Database Schema (if using SQLite)

```sql
CREATE TABLE import_lists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    list_type TEXT NOT NULL,
    url TEXT,
    trakt_username TEXT,
    trakt_list_name TEXT,
    media_type TEXT DEFAULT 'both',
    count INTEGER DEFAULT 10,
    fill_mode TEXT DEFAULT 'strict',
    fill_limit INTEGER DEFAULT 100,
    air_date_within_days INTEGER DEFAULT 0,
    episodes_per_show INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 50,
    refresh_interval_hours INTEGER DEFAULT 6,
    last_refresh TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE import_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_id TEXT NOT NULL,
    title TEXT NOT NULL,
    year INTEGER,
    imdb_id TEXT,
    tmdb_id TEXT,
    tvdb_id TEXT,
    media_type TEXT,
    position INTEGER,
    matched_plex_path TEXT,
    cached BOOLEAN DEFAULT 0,
    last_seen TEXT,
    FOREIGN KEY (list_id) REFERENCES import_lists(id)
);
```

---

## Integration with Cache Manager

```python
class ImportListsManager:
    """Manages import lists and their items."""
    
    def __init__(self, settings: ImportListsSettings, plex_client: PlexClient):
        self.settings = settings
        self.plex = plex_client
        self.providers = self._init_providers()
    
    def get_files_to_cache(self) -> List[Tuple[str, str]]:
        """Get all files that should be cached from import lists.
        
        Returns:
            List of (file_path, source) tuples where source is the list ID.
        """
        files = []
        
        for list_config in self.settings.lists:
            if not list_config.enabled:
                continue
            
            # Get items from list
            raw_items = self._fetch_list_items(list_config)
            
            # Filter by air date if configured
            filtered_items = [
                item for item in raw_items
                if self._passes_air_date_filter(item, list_config)
            ]
            
            # Match to Plex library
            matched = self.plex_matcher.get_available_from_list(
                filtered_items,
                count=list_config.count,
                fill_mode=list_config.fill_mode,
                fill_limit=list_config.fill_limit,
            )
            
            # Get file paths
            for plex_media in matched:
                paths = self._get_file_paths(plex_media, list_config)
                for path in paths:
                    files.append((path, f"list:{list_config.id}"))
        
        return files
```

---

## Summary

The Import Lists system provides:
1. **Flexibility** - Multiple list sources (Trakt, TMDb, IMDb, custom)
2. **Control** - Fine-grained settings per list (count, fill mode, air date filter)
3. **Intelligence** - Automatic matching to Plex library
4. **Priority** - Lists can have different eviction priorities
5. **Scheduling** - Independent refresh intervals per list

This allows users to automatically cache trending/popular content without manually maintaining lists.
