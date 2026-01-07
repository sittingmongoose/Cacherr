# User Management System Design

## Overview

Cacherr needs sophisticated user management to handle different types of Plex users with independent settings.

---

## User Types

### 1. Main User (Admin)
- The Plex server owner
- Uses the main Plex token
- Always has access to all features
- Typically the most important user for caching

### 2. Home Users (Local)
- Family members on the same Plex Home
- Share the server locally
- Usually trusted users with similar priorities

### 3. Shared Users (Remote)
- Friends with shared library access
- Access server remotely
- May have different priority levels

---

## User Data Model

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum

class UserType(str, Enum):
    MAIN = "main"
    HOME = "home"
    SHARED = "shared"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"

class UserCachingSettings(BaseModel):
    """Per-user caching settings."""
    
    # OnDeck settings
    ondeck_enabled: bool = Field(default=True, description="Cache this user's OnDeck")
    ondeck_episodes_ahead: int = Field(default=5, ge=1, le=50)
    ondeck_max_stale_days: int = Field(default=30, ge=0, description="0 = no limit")
    
    # Watchlist settings
    watchlist_enabled: bool = Field(default=True, description="Cache this user's watchlist")
    watchlist_episodes_per_show: int = Field(default=1, ge=1, le=20)
    watchlist_max_available_days: int = Field(
        default=0, ge=0, 
        description="Only cache if available for less than X days (0 = no limit)"
    )
    
    # Currently watching
    active_watching_enabled: bool = Field(default=True, description="Cache when user starts playing")
    
    # Import lists (applies to lists where user ownership matters)
    lists_enabled: bool = Field(default=True, description="Include this user's lists")

class PlexUser(BaseModel):
    """Represents a Plex user with caching settings."""
    
    # Identity
    id: str = Field(..., description="Plex user ID")
    username: str = Field(..., description="Display name")
    email: Optional[str] = Field(default=None)
    thumb_url: Optional[str] = Field(default=None, description="Avatar URL")
    
    # Type and status
    user_type: UserType = Field(..., description="main, home, or shared")
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    
    # Token (for API calls as this user)
    token: Optional[str] = Field(default=None, description="User's access token")
    
    # Activity tracking
    last_seen: Optional[datetime] = Field(default=None, description="Last activity")
    last_active_session: Optional[datetime] = Field(default=None, description="Last playback")
    
    # Settings
    settings: UserCachingSettings = Field(default_factory=UserCachingSettings)
    
    # Override defaults (per-user overrides for global settings)
    priority_boost: int = Field(default=0, ge=-50, le=50, description="Priority adjustment")

class UserTypeDefaults(BaseModel):
    """Default settings for each user type."""
    
    user_type: UserType
    settings: UserCachingSettings
    auto_enable_new_users: bool = Field(default=True, description="Auto-enable new users of this type")
    activity_filter_days: int = Field(default=0, ge=0, description="Only include if active within X days")
```

---

## User Management Settings

```python
class UserManagementSettings(BaseModel):
    """Global user management settings."""
    
    # Master toggles
    multi_user_enabled: bool = Field(default=True, description="Enable multi-user support")
    
    # User type defaults
    main_user_defaults: UserCachingSettings = Field(default_factory=UserCachingSettings)
    home_user_defaults: UserCachingSettings = Field(
        default_factory=lambda: UserCachingSettings(
            ondeck_enabled=True,
            watchlist_enabled=True,
            active_watching_enabled=True,
            lists_enabled=True,
        )
    )
    shared_user_defaults: UserCachingSettings = Field(
        default_factory=lambda: UserCachingSettings(
            ondeck_enabled=True,
            watchlist_enabled=False,  # Shared users often have lower priority
            active_watching_enabled=True,
            lists_enabled=False,
        )
    )
    
    # Activity filtering
    main_activity_filter_days: int = Field(default=0, description="0 = always include")
    home_activity_filter_days: int = Field(default=90, description="Only if active in last 90 days")
    shared_activity_filter_days: int = Field(default=30, description="Only if active in last 30 days")
    
    # Auto-management
    auto_discover_users: bool = Field(default=True, description="Automatically discover new users")
    auto_enable_home_users: bool = Field(default=True, description="Auto-enable new home users")
    auto_enable_shared_users: bool = Field(default=False, description="Auto-enable new shared users")
    
    # Token management
    cache_tokens: bool = Field(default=True, description="Cache user tokens to reduce API calls")
    token_cache_hours: int = Field(default=24, ge=1, description="Hours to cache tokens")
    
    # Configured users
    users: List[PlexUser] = Field(default_factory=list)
```

---

## User Discovery

```python
class UserDiscoveryService:
    """Discovers and classifies Plex users."""
    
    def __init__(self, plex_client: PlexClient, settings: UserManagementSettings):
        self.plex = plex_client
        self.settings = settings
        self._token_cache = UserTokenCache()
    
    async def discover_users(self) -> List[PlexUser]:
        """Discover all users from Plex."""
        users = []
        
        # Get main account
        main_account = await self._get_main_account()
        users.append(self._create_user(
            id=main_account.id,
            username=main_account.title,
            email=main_account.email,
            user_type=UserType.MAIN,
            token=self.plex.token,
        ))
        
        # Get home users (local)
        home_users = await self._get_home_users()
        for user in home_users:
            users.append(self._create_user(
                id=user.id,
                username=user.title,
                user_type=UserType.HOME,
                token=await self._get_user_token(user),
            ))
        
        # Get shared users (remote/friends)
        shared_users = await self._get_shared_users()
        for user in shared_users:
            users.append(self._create_user(
                id=user.id,
                username=user.title,
                user_type=UserType.SHARED,
                token=await self._get_user_token(user),
            ))
        
        return users
    
    def _create_user(self, **kwargs) -> PlexUser:
        """Create user with appropriate defaults."""
        user_type = kwargs.get('user_type', UserType.SHARED)
        
        # Get default settings for this user type
        if user_type == UserType.MAIN:
            defaults = self.settings.main_user_defaults
        elif user_type == UserType.HOME:
            defaults = self.settings.home_user_defaults
        else:
            defaults = self.settings.shared_user_defaults
        
        return PlexUser(
            settings=defaults.model_copy(),
            **kwargs
        )
    
    def should_include_user(self, user: PlexUser) -> bool:
        """Check if user should be included based on activity filter."""
        if user.user_type == UserType.MAIN:
            filter_days = self.settings.main_activity_filter_days
        elif user.user_type == UserType.HOME:
            filter_days = self.settings.home_activity_filter_days
        else:
            filter_days = self.settings.shared_activity_filter_days
        
        if filter_days == 0:
            return True  # No filter
        
        if not user.last_seen:
            return False  # Never seen, exclude
        
        days_since = (datetime.now() - user.last_seen).days
        return days_since <= filter_days
```

---

## Activity Tracking

```python
class UserActivityTracker:
    """Tracks user activity for filtering."""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self._data = self._load()
    
    def record_activity(self, user_id: str, activity_type: str = "seen"):
        """Record user activity."""
        now = datetime.now()
        
        if user_id not in self._data:
            self._data[user_id] = {}
        
        self._data[user_id]['last_seen'] = now.isoformat()
        
        if activity_type == "playback":
            self._data[user_id]['last_playback'] = now.isoformat()
        
        self._save()
    
    def get_last_seen(self, user_id: str) -> Optional[datetime]:
        """Get when user was last seen."""
        if user_id in self._data and 'last_seen' in self._data[user_id]:
            return datetime.fromisoformat(self._data[user_id]['last_seen'])
        return None
    
    def get_inactive_users(self, days: int) -> List[str]:
        """Get users inactive for more than X days."""
        cutoff = datetime.now() - timedelta(days=days)
        inactive = []
        
        for user_id, data in self._data.items():
            last_seen = data.get('last_seen')
            if last_seen:
                if datetime.fromisoformat(last_seen) < cutoff:
                    inactive.append(user_id)
            else:
                inactive.append(user_id)
        
        return inactive
```

---

## Web UI Design

### Users Management Page
```
┌─────────────────────────────────────────────────────────────────────┐
│ User Management                                      [Refresh Users]│
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ─── Main User ───                                                   │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ [👤] AdminUser                               [Active] [Settings]│ │
│ │     OnDeck: ✓   Watchlist: ✓   Lists: ✓   Watching: ✓         │ │
│ │     Last active: 5 minutes ago                                 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ─── Home Users ─── [Defaults] [Activity: 90 days ▼]                 │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ [👤] FamilyMember1                           [Active] [Settings]│ │
│ │     OnDeck: ✓   Watchlist: ✓   Lists: ✓   Watching: ✓         │ │
│ │     Last active: 2 hours ago                                   │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ [👤] FamilyMember2                           [Active] [Settings]│ │
│ │     OnDeck: ✓   Watchlist: ✓   Lists: ☐   Watching: ✓         │ │
│ │     Last active: 1 day ago                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ─── Shared Users ─── [Defaults] [Activity: 30 days ▼]               │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ [👤] Friend1                                 [Active] [Settings]│ │
│ │     OnDeck: ✓   Watchlist: ☐   Lists: ☐   Watching: ✓         │ │
│ │     Last active: 3 days ago                                    │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ [👤] Friend2                               [Inactive] [Settings]│ │
│ │     OnDeck: ✓   Watchlist: ☐   Lists: ☐   Watching: ✓         │ │
│ │     Last active: 45 days ago (excluded by filter)              │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ [👤] Friend3                               [Disabled] [Settings]│ │
│ │     Manually disabled                                          │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### User Settings Dialog
```
┌─────────────────────────────────────────────────────────────────────┐
│ User Settings: FamilyMember1 (Home)                          [×]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Status: (•) Active  ( ) Inactive  ( ) Disabled                      │
│                                                                     │
│ ─── OnDeck ───                                                      │
│ [✓] Cache OnDeck items                                              │
│     Episodes ahead: [5     ]                                        │
│     Max stale days: [30    ] (0 = no limit)                        │
│                                                                     │
│ ─── Watchlist ───                                                   │
│ [✓] Cache Watchlist items                                           │
│     Episodes per show: [1     ]                                     │
│     Max available days: [0     ] (0 = no limit)                    │
│                                                                     │
│ ─── Active Watching ───                                             │
│ [✓] Cache when user starts playing                                  │
│                                                                     │
│ ─── Import Lists ───                                                │
│ [✓] Include this user's personal lists                              │
│                                                                     │
│ ─── Priority ───                                                    │
│ Priority boost: [-10   ] (-50 to +50, 0 = default)                 │
│     Note: Lower priority files evicted first                       │
│                                                                     │
│                                    [Cancel]  [Save]                 │
└─────────────────────────────────────────────────────────────────────┘
```

### User Type Defaults Dialog
```
┌─────────────────────────────────────────────────────────────────────┐
│ Default Settings for Shared Users                            [×]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ These defaults apply to new shared users and can be overridden     │
│ per-user in their individual settings.                             │
│                                                                     │
│ ─── Activity Filter ───                                             │
│ Only include users active in the last: [30    ] days               │
│     (0 = include all users regardless of activity)                 │
│                                                                     │
│ ─── Auto-Enable ───                                                 │
│ [ ] Automatically enable new shared users                          │
│                                                                     │
│ ─── Default Caching Settings ───                                    │
│ [✓] OnDeck enabled          Episodes ahead: [5     ]               │
│ [ ] Watchlist enabled       Episodes per show: [1     ]            │
│ [✓] Active watching enabled                                        │
│ [ ] Lists enabled                                                   │
│                                                                     │
│                                    [Cancel]  [Save]                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

```
GET    /api/users                - Get all users
GET    /api/users/:id            - Get a specific user
PUT    /api/users/:id            - Update user settings
POST   /api/users/:id/enable     - Enable a user
POST   /api/users/:id/disable    - Disable a user
POST   /api/users/refresh        - Refresh user list from Plex
GET    /api/users/types/defaults - Get defaults for each user type
PUT    /api/users/types/defaults - Update defaults for a user type
GET    /api/users/activity       - Get user activity summary
```

---

## Integration with Cache Manager

```python
class CacheManager:
    """Updated cache manager with user-aware caching."""
    
    def __init__(self, ...):
        ...
        self.user_manager = UserDiscoveryService(self.plex, self.settings.users)
    
    def get_ondeck_files(self) -> List[Tuple[str, str]]:
        """Get OnDeck files respecting user settings."""
        files = []
        
        for user in self.user_manager.get_active_users():
            if not user.settings.ondeck_enabled:
                continue
            
            if not self.user_manager.should_include_user(user):
                continue
            
            # Get OnDeck for this user
            ondeck = self.plex.get_ondeck_for_user(
                user,
                episodes_ahead=user.settings.ondeck_episodes_ahead,
                max_stale_days=user.settings.ondeck_max_stale_days,
            )
            
            for item in ondeck:
                # Apply user's priority boost
                priority = self._calculate_priority(item) + user.priority_boost
                files.append((item.file_path, "ondeck", user.username, priority))
        
        return files
    
    def get_watchlist_files(self) -> List[Tuple[str, str]]:
        """Get Watchlist files respecting user settings."""
        files = []
        
        for user in self.user_manager.get_active_users():
            if not user.settings.watchlist_enabled:
                continue
            
            if not self.user_manager.should_include_user(user):
                continue
            
            # Get Watchlist for this user
            watchlist = self.plex.get_watchlist_for_user(
                user,
                episodes_per_show=user.settings.watchlist_episodes_per_show,
                max_available_days=user.settings.watchlist_max_available_days,
            )
            
            for item in watchlist:
                priority = self._calculate_priority(item) + user.priority_boost
                files.append((item.file_path, "watchlist", user.username, priority))
        
        return files
```

---

## Database Schema

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT,
    thumb_url TEXT,
    user_type TEXT NOT NULL,  -- 'main', 'home', 'shared'
    status TEXT DEFAULT 'active',  -- 'active', 'inactive', 'disabled'
    token TEXT,
    last_seen TEXT,
    last_active_session TEXT,
    priority_boost INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE user_settings (
    user_id TEXT PRIMARY KEY,
    ondeck_enabled BOOLEAN DEFAULT 1,
    ondeck_episodes_ahead INTEGER DEFAULT 5,
    ondeck_max_stale_days INTEGER DEFAULT 30,
    watchlist_enabled BOOLEAN DEFAULT 1,
    watchlist_episodes_per_show INTEGER DEFAULT 1,
    watchlist_max_available_days INTEGER DEFAULT 0,
    active_watching_enabled BOOLEAN DEFAULT 1,
    lists_enabled BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE user_type_defaults (
    user_type TEXT PRIMARY KEY,
    settings_json TEXT,  -- JSON blob of UserCachingSettings
    activity_filter_days INTEGER DEFAULT 0,
    auto_enable_new BOOLEAN DEFAULT 1
);
```

---

## Summary

The User Management system provides:

1. **User Classification** - Main, Home, Shared user types
2. **Per-User Settings** - Independent OnDeck, Watchlist, Lists, Watching settings
3. **Activity Filtering** - Only cache for recently active users
4. **Type Defaults** - Configure defaults per user type
5. **Priority Adjustment** - Boost or reduce priority per user
6. **Staleness Filtering** - Don't cache stale OnDeck items
7. **Availability Filtering** - Don't cache old watchlist items
8. **Auto-Discovery** - Automatically find new users
9. **Manual Override** - Enable/disable specific users
