"""
Cacherr Configuration Settings.

All configuration uses Pydantic v2.5 models for validation and type safety.
Settings can be loaded from environment variables, JSON files, or both.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field


logger = logging.getLogger(__name__)


class PathMapping(BaseModel):
    """Maps Plex container paths to real filesystem paths.
    
    Allows per-library control over caching behavior for multi-source setups.
    """
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    name: str = Field(default="", description="Human-readable identifier")
    plex_path: str = Field(default="", description="Path as Plex sees it")
    real_path: str = Field(default="", description="Actual filesystem path")
    cache_path: Optional[str] = Field(default=None, description="Cache destination")
    cacheable: bool = Field(default=True, description="Whether files can be cached")
    enabled: bool = Field(default=True, description="Toggle mapping on/off")


class PlexSettings(BaseModel):
    """Plex server connection and behavior settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    url: str = Field(default="", env="PLEX_URL", description="Plex server URL")
    token: str = Field(default="", env="PLEX_TOKEN", description="Plex API token")
    valid_sections: List[int] = Field(default_factory=list, description="Library section IDs to process")
    
    # OnDeck settings
    number_episodes: int = Field(default=5, ge=1, le=50, description="Episodes to cache ahead of OnDeck")
    days_to_monitor: int = Field(default=99, ge=1, le=365, description="Days to consider for OnDeck")
    
    # User settings
    users_toggle: bool = Field(default=True, description="Enable multi-user support")
    skip_ondeck_users: List[str] = Field(default_factory=list, description="Users to skip for OnDeck")
    skip_watchlist_users: List[str] = Field(default_factory=list, description="Users to skip for watchlist")


class WatchlistSettings(BaseModel):
    """Watchlist caching settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    enabled: bool = Field(default=True, description="Enable watchlist caching")
    episodes_per_show: int = Field(default=1, ge=1, le=20, description="Episodes per watchlist show")
    
    # Remote watchlist via RSS
    remote_rss_enabled: bool = Field(default=False, description="Enable remote RSS watchlist")
    remote_rss_url: str = Field(default="", description="Remote watchlist RSS URL")


class TraktSettings(BaseModel):
    """Trakt.tv integration settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    enabled: bool = Field(default=False, description="Enable Trakt integration")
    client_id: str = Field(default="", description="Trakt client ID")
    client_secret: str = Field(default="", description="Trakt client secret")
    trending_movies_count: int = Field(default=10, ge=1, le=100, description="Trending movies to cache")
    check_interval_seconds: int = Field(default=3600, ge=300, description="Seconds between Trakt checks")


class CacheLimitSettings(BaseModel):
    """Cache size limits and eviction settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    # Cache limit (e.g., "250GB", "500MB", "50%", or "" for unlimited)
    cache_limit: str = Field(default="", description="Maximum cache size")
    
    # Eviction strategy
    eviction_mode: str = Field(
        default="none",
        pattern="^(none|fifo|smart)$",
        description="Eviction strategy: none, fifo, or smart"
    )
    eviction_threshold_percent: int = Field(
        default=90, ge=1, le=100,
        description="Start evicting at this % of limit"
    )
    eviction_target_percent: int = Field(
        default=80, ge=1, le=99,
        description="Evict down to this % of limit"
    )
    eviction_min_priority: int = Field(
        default=60, ge=0, le=100,
        description="Only evict files with priority below this (smart mode)"
    )
    eviction_protected_hours: float = Field(
        default=2.0, ge=0,
        description="Don't evict files cached within this many hours"
    )
    
    @field_validator('eviction_target_percent')
    @classmethod
    def target_must_be_less_than_threshold(cls, v, info):
        threshold = info.data.get('eviction_threshold_percent', 90)
        if v >= threshold:
            raise ValueError('eviction_target_percent must be less than eviction_threshold_percent')
        return v
    
    @computed_field
    @property
    def has_limit(self) -> bool:
        return bool(self.cache_limit and self.cache_limit.strip() not in ('', '0'))
    
    @computed_field
    @property
    def eviction_enabled(self) -> bool:
        return self.eviction_mode != 'none' and self.has_limit


class RetentionSettings(BaseModel):
    """Cache retention policy settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    # Minimum retention (protection period after caching)
    min_retention_hours: float = Field(
        default=12.0, ge=0,
        description="Minimum hours before any file can be moved back"
    )
    
    # Watched content retention
    watched_expiry_hours: int = Field(
        default=48, ge=0,
        description="Hours to keep watched content (0 = move immediately)"
    )
    
    # Watchlist retention
    watchlist_retention_days: float = Field(
        default=0, ge=0,
        description="Days to keep watchlist items (0 = keep while on list)"
    )
    
    # Maximum cache time
    max_cache_hours: int = Field(
        default=0, ge=0,
        description="Maximum hours any file can stay cached (0 = unlimited)"
    )
    
    # Protections
    ondeck_protected: bool = Field(default=True, description="Never auto-expire OnDeck items")
    protect_during_playback: bool = Field(default=True, description="Never touch actively playing files")


class RealtimeSettings(BaseModel):
    """Real-time Plex session monitoring settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    enabled: bool = Field(default=True, description="Enable real-time session monitoring")
    check_interval_seconds: int = Field(default=30, ge=5, le=300, description="Seconds between session checks")
    cache_on_play_start: bool = Field(default=True, description="Cache when playback starts")
    min_playback_seconds: int = Field(default=60, ge=0, description="Min playback before caching")
    watched_threshold_percent: int = Field(default=90, ge=50, le=100, description="% watched to mark complete")
    auto_cache_next_episode: bool = Field(default=True, description="Auto-cache next TV episode")


class ReconciliationSettings(BaseModel):
    """Cache reconciliation (self-healing) settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    auto_on_startup: bool = Field(default=True, description="Run reconciliation on startup")
    interval_minutes: int = Field(default=60, ge=0, description="Minutes between checks (0 = disabled)")
    
    check_file_existence: bool = Field(default=True, description="Verify cached files exist")
    check_symlink_integrity: bool = Field(default=True, description="Verify symlinks are valid")
    discover_untracked_files: bool = Field(default=True, description="Find files not in database")
    cleanup_stale_entries: bool = Field(default=True, description="Remove old orphaned entries")
    stale_entry_days: int = Field(default=30, ge=1, description="Days before entry is stale")


class PerformanceSettings(BaseModel):
    """Performance and concurrency settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    max_concurrent_to_cache: int = Field(default=3, ge=1, le=10, description="Concurrent moves to cache")
    max_concurrent_to_array: int = Field(default=1, ge=1, le=5, description="Concurrent moves to array")
    retry_limit: int = Field(default=5, ge=1, le=20, description="Retry attempts for failed operations")
    delay_seconds: int = Field(default=10, ge=1, le=60, description="Delay between retries")


class NotificationSettings(BaseModel):
    """Notification settings (Discord, Slack, Unraid)."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    enabled: bool = Field(default=False, description="Enable notifications")
    webhook_url: str = Field(default="", description="Discord/Slack webhook URL")
    notification_type: str = Field(default="webhook", description="webhook, unraid, or both")
    log_level: str = Field(default="summary", description="Notification level")


class PathSettings(BaseModel):
    """File path settings."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    cache_destination: str = Field(default="/cache", description="Cache drive path")
    config_directory: str = Field(default="/config", description="Config file directory")
    logs_directory: str = Field(default="/config/logs", description="Log file directory")
    
    # Path mappings for multi-source support
    path_mappings: List[PathMapping] = Field(default_factory=list, description="Path mappings")
    
    # Legacy single-path support (deprecated)
    plex_source: str = Field(default="", description="Legacy: Plex library path")
    real_source: str = Field(default="", description="Legacy: Array drive path")


class CacherrSettings(BaseModel):
    """Main Cacherr settings combining all subsections."""
    model_config = ConfigDict(validate_default=True, extra='ignore')
    
    # Subsections
    plex: PlexSettings = Field(default_factory=PlexSettings)
    watchlist: WatchlistSettings = Field(default_factory=WatchlistSettings)
    trakt: TraktSettings = Field(default_factory=TraktSettings)
    cache_limits: CacheLimitSettings = Field(default_factory=CacheLimitSettings)
    retention: RetentionSettings = Field(default_factory=RetentionSettings)
    realtime: RealtimeSettings = Field(default_factory=RealtimeSettings)
    reconciliation: ReconciliationSettings = Field(default_factory=ReconciliationSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    
    # General settings
    debug: bool = Field(default=False, description="Enable debug mode")
    dry_run: bool = Field(default=False, description="Simulate operations without moving files")
    exit_if_active_session: bool = Field(default=True, description="Exit if Plex has active sessions")
    
    @classmethod
    def from_env(cls) -> "CacherrSettings":
        """Create settings from environment variables."""
        return cls(
            plex=PlexSettings(
                url=os.getenv("PLEX_URL", ""),
                token=os.getenv("PLEX_TOKEN", ""),
                number_episodes=int(os.getenv("NUMBER_EPISODES", "5")),
                days_to_monitor=int(os.getenv("DAYS_TO_MONITOR", "99")),
                users_toggle=os.getenv("USERS_TOGGLE", "true").lower() == "true",
            ),
            watchlist=WatchlistSettings(
                enabled=os.getenv("WATCHLIST_TOGGLE", "true").lower() == "true",
                episodes_per_show=int(os.getenv("WATCHLIST_EPISODES", "1")),
            ),
            trakt=TraktSettings(
                enabled=os.getenv("TRAKT_ENABLED", "false").lower() == "true",
                client_id=os.getenv("TRAKT_CLIENT_ID", ""),
                client_secret=os.getenv("TRAKT_CLIENT_SECRET", ""),
                trending_movies_count=int(os.getenv("TRAKT_TRENDING_MOVIES_COUNT", "10")),
            ),
            cache_limits=CacheLimitSettings(
                cache_limit=os.getenv("CACHE_LIMIT", ""),
                eviction_mode=os.getenv("CACHE_EVICTION_MODE", "none"),
                eviction_threshold_percent=int(os.getenv("CACHE_EVICTION_THRESHOLD", "90")),
                eviction_target_percent=int(os.getenv("CACHE_EVICTION_TARGET", "80")),
                eviction_min_priority=int(os.getenv("CACHE_EVICTION_MIN_PRIORITY", "60")),
            ),
            retention=RetentionSettings(
                min_retention_hours=float(os.getenv("MIN_RETENTION_HOURS", "12")),
                watched_expiry_hours=int(os.getenv("WATCHED_CACHE_EXPIRY", "48")),
                watchlist_retention_days=float(os.getenv("WATCHLIST_RETENTION_DAYS", "0")),
                ondeck_protected=os.getenv("ONDECK_PROTECTED", "true").lower() == "true",
            ),
            realtime=RealtimeSettings(
                enabled=os.getenv("REALTIME_ENABLED", "true").lower() == "true",
                check_interval_seconds=int(os.getenv("REALTIME_CHECK_INTERVAL", "30")),
                cache_on_play_start=os.getenv("CACHE_ON_PLAY_START", "true").lower() == "true",
                min_playback_seconds=int(os.getenv("MIN_PLAYBACK_SECONDS", "60")),
            ),
            reconciliation=ReconciliationSettings(
                auto_on_startup=os.getenv("AUTO_RECONCILE_ON_STARTUP", "true").lower() == "true",
                interval_minutes=int(os.getenv("RECONCILE_INTERVAL_MINUTES", "60")),
            ),
            performance=PerformanceSettings(
                max_concurrent_to_cache=int(os.getenv("MAX_CONCURRENT_MOVES_CACHE", "3")),
                max_concurrent_to_array=int(os.getenv("MAX_CONCURRENT_MOVES_ARRAY", "1")),
            ),
            notifications=NotificationSettings(
                webhook_url=os.getenv("WEBHOOK_URL", ""),
                notification_type=os.getenv("NOTIFICATION_TYPE", "webhook"),
            ),
            paths=PathSettings(
                cache_destination=os.getenv("CACHE_DESTINATION", "/cache"),
                config_directory=os.getenv("CONFIG_DIR", "/config"),
                plex_source=os.getenv("PLEX_SOURCE", ""),
                real_source=os.getenv("REAL_SOURCE", ""),
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
        )
    
    @classmethod
    def from_file(cls, path: str) -> "CacherrSettings":
        """Load settings from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.model_validate(data)
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "CacherrSettings":
        """Load settings from file (if exists) merged with environment variables.
        
        Priority: Environment variables > JSON file > Defaults
        """
        # Start with defaults
        settings = cls()
        
        # Load from file if it exists
        if config_path and Path(config_path).exists():
            try:
                file_settings = cls.from_file(config_path)
                settings = file_settings
                logger.info(f"Loaded settings from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load settings from {config_path}: {e}")
        
        # Override with environment variables
        env_settings = cls.from_env()
        
        # Merge: env overrides file where env is non-empty
        if env_settings.plex.url:
            settings.plex.url = env_settings.plex.url
        if env_settings.plex.token:
            settings.plex.token = env_settings.plex.token
        
        # Continue merging other non-default env values as needed...
        
        return settings
    
    def save(self, path: str) -> None:
        """Save settings to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2, default=str)
        logger.info(f"Saved settings to {path}")
