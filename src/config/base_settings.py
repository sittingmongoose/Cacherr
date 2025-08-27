"""
Pydantic BaseSettings implementation for environment variable handling.

This module provides robust environment variable configuration using Pydantic v2
BaseSettings with proper validation, type conversion, and documentation.

Example:
    >>> settings = CacherrSettings()
    >>> settings.plex.url
    'http://localhost:32400'
    >>> settings.media.copy_to_cache
    True
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from pydantic import Field, SecretStr, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from pydantic.types import PositiveInt

from .pydantic_models import (
    LoggingConfig, PlexConfig, MediaConfig, PathsConfig, PerformanceConfig,
    LogLevel
)


class CacherrSettings(BaseSettings):
    """
    Main application settings loaded from environment variables.
    
    This class uses Pydantic BaseSettings to automatically load configuration
    from environment variables with proper type conversion and validation.
    
    Environment Variable Naming:
        - Nested settings use underscore separation
        - Example: PLEX_URL maps to plex.url
        - Boolean values: 'true'/'false', '1'/'0', 'yes'/'no'
        - Lists: comma-separated values
    
    Example:
        >>> import os
        >>> os.environ['PLEX_URL'] = 'http://plex.example.com:32400'
        >>> os.environ['COPY_TO_CACHE'] = 'true'
        >>> settings = CacherrSettings()
        >>> settings.plex.url
        'http://plex.example.com:32400'
        >>> settings.media.copy_to_cache
        True
    """
    
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        validate_assignment=True,
        extra='ignore',  # Ignore unknown environment variables
        # Enable nested env var support
        env_nested_delimiter='__'
    )

    # =============================================================================
    # PLEX CONFIGURATION
    # =============================================================================
    plex_url: str = Field(
        default="http://localhost:32400",
        description="Plex server URL",
        env='PLEX_URL'
    )
    plex_token: str = Field(
        default="",
        description="Plex authentication token",
        env='PLEX_TOKEN'
    )
    plex_username: Optional[str] = Field(
        default=None,
        description="Plex username (optional)",
        env='PLEX_USERNAME'
    )
    plex_password: Optional[SecretStr] = Field(
        default=None,
        description="Plex password (optional)",
        env='PLEX_PASSWORD'
    )
    
    # =============================================================================
    # PATH CONFIGURATION
    # =============================================================================
    config_dir: str = Field(
        default="/config",
        description="Configuration directory",
        env='CONFIG_DIR'
    )
    real_source: str = Field(
        default="/media",
        description="Real source directory",
        env='REAL_SOURCE'
    )
    plex_source: str = Field(
        default="/media",
        description="Plex source directory",
        env='PLEX_SOURCE'
    )
    cache_destination: str = Field(
        default="/cache",
        description="Cache destination directory",
        env='CACHE_DESTINATION'
    )
    additional_sources: List[str] = Field(
        default_factory=list,
        description="Additional source directories (comma-separated)",
        env='ADDITIONAL_SOURCES'
    )
    additional_plex_sources: List[str] = Field(
        default_factory=list,
        description="Additional Plex source directories (comma-separated)",
        env='ADDITIONAL_PLEX_SOURCES'
    )
    
    # =============================================================================
    # MEDIA SETTINGS
    # =============================================================================
    number_episodes: PositiveInt = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of episodes to cache per series",
        env='NUMBER_EPISODES'
    )
    days_to_monitor: PositiveInt = Field(
        default=99,
        ge=1,
        le=999,
        description="Days to monitor content",
        env='DAYS_TO_MONITOR'
    )
    watchlist_toggle: bool = Field(
        default=True,
        description="Enable watchlist processing",
        env='WATCHLIST_TOGGLE'
    )
    watchlist_episodes: PositiveInt = Field(
        default=1,
        ge=1,
        le=100,
        description="Episodes to cache from watchlists",
        env='WATCHLIST_EPISODES'
    )
    watchlist_cache_expiry: PositiveInt = Field(
        default=6,
        ge=1,
        le=8760,
        description="Watchlist cache expiry in hours",
        env='WATCHLIST_CACHE_EXPIRY'
    )
    watched_move: bool = Field(
        default=True,
        description="Move watched content to array",
        env='WATCHED_MOVE'
    )
    watched_cache_expiry: PositiveInt = Field(
        default=48,
        ge=1,
        le=8760,
        description="Watched content cache expiry in hours",
        env='WATCHED_CACHE_EXPIRY'
    )
    users_toggle: bool = Field(
        default=True,
        description="Enable per-user processing",
        env='USERS_TOGGLE'
    )
    exit_if_active_session: bool = Field(
        default=False,
        description="Exit if Plex sessions are active",
        env='EXIT_IF_ACTIVE_SESSION'
    )
    
    # =============================================================================
    # CACHE BEHAVIOR SETTINGS (with new defaults)
    # =============================================================================
    copy_to_cache: bool = Field(
        default=True,  # New default: Copy instead of move
        description="Copy files to cache instead of moving (preserves originals)",
        env='COPY_TO_CACHE'
    )
    delete_from_cache_when_done: bool = Field(
        default=True,
        description="Delete from cache when done",
        env='DELETE_FROM_CACHE_WHEN_DONE'
    )
    
    # =============================================================================
    # PERFORMANCE SETTINGS
    # =============================================================================
    max_concurrent_moves_cache: PositiveInt = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum concurrent moves to cache",
        env='MAX_CONCURRENT_MOVES_CACHE'
    )
    max_concurrent_moves_array: PositiveInt = Field(
        default=1,
        ge=1,
        le=10,
        description="Maximum concurrent moves to array",
        env='MAX_CONCURRENT_MOVES_ARRAY'
    )
    max_concurrent_local_transfers: PositiveInt = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum concurrent local transfers",
        env='MAX_CONCURRENT_LOCAL_TRANSFERS'
    )
    max_concurrent_network_transfers: PositiveInt = Field(
        default=1,
        ge=1,
        le=5,
        description="Maximum concurrent network transfers",
        env='MAX_CONCURRENT_NETWORK_TRANSFERS'
    )
    
    # =============================================================================
    # REAL-TIME WATCHING
    # =============================================================================
    real_time_watch_enabled: bool = Field(
        default=False,
        description="Enable real-time watching",
        env='REAL_TIME_WATCH_ENABLED'
    )
    real_time_watch_check_interval: PositiveInt = Field(
        default=30,
        ge=5,
        le=3600,
        description="Real-time watch check interval in seconds",
        env='REAL_TIME_WATCH_CHECK_INTERVAL'
    )
    real_time_watch_auto_cache_on_watch: bool = Field(
        default=True,
        description="Auto cache when watching starts",
        env='REAL_TIME_WATCH_AUTO_CACHE_ON_WATCH'
    )
    real_time_watch_cache_on_complete: bool = Field(
        default=True,
        description="Cache when watching completes",
        env='REAL_TIME_WATCH_CACHE_ON_COMPLETE'
    )
    real_time_watch_respect_existing_rules: bool = Field(
        default=True,
        description="Respect existing cache rules",
        env='REAL_TIME_WATCH_RESPECT_EXISTING_RULES'
    )
    real_time_watch_max_concurrent_watches: PositiveInt = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent watches",
        env='REAL_TIME_WATCH_MAX_CONCURRENT_WATCHES'
    )
    real_time_watch_remove_from_cache_after_hours: int = Field(
        default=24,
        ge=0,
        description="Hours to keep in cache after watching (0 = forever)",
        env='REAL_TIME_WATCH_REMOVE_FROM_CACHE_AFTER_HOURS'
    )
    real_time_watch_respect_other_users_watchlists: bool = Field(
        default=True,
        description="Respect other users' watchlists",
        env='REAL_TIME_WATCH_RESPECT_OTHER_USERS_WATCHLISTS'
    )
    real_time_watch_exclude_inactive_users_days: int = Field(
        default=30,
        ge=0,
        description="Days before excluding inactive users (0 = never)",
        env='REAL_TIME_WATCH_EXCLUDE_INACTIVE_USERS_DAYS'
    )
    
    # =============================================================================
    # TRAKT.TV INTEGRATION
    # =============================================================================
    trakt_enabled: bool = Field(
        default=False,
        description="Enable Trakt.tv integration",
        env='TRAKT_ENABLED'
    )
    trakt_client_id: Optional[str] = Field(
        default=None,
        description="Trakt.tv client ID",
        env='TRAKT_CLIENT_ID'
    )
    trakt_client_secret: Optional[SecretStr] = Field(
        default=None,
        description="Trakt.tv client secret",
        env='TRAKT_CLIENT_SECRET'
    )
    trakt_trending_movies_count: PositiveInt = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of trending movies to fetch",
        env='TRAKT_TRENDING_MOVIES_COUNT'
    )
    trakt_check_interval: PositiveInt = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Trakt check interval in seconds",
        env='TRAKT_CHECK_INTERVAL'
    )
    
    # =============================================================================
    # TEST MODE SETTINGS
    # =============================================================================
    test_mode: bool = Field(
        default=False,
        description="Enable test mode (dry run)",
        env='TEST_MODE'
    )
    test_show_file_sizes: bool = Field(
        default=True,
        description="Show file sizes in test output",
        env='TEST_SHOW_FILE_SIZES'
    )
    test_show_total_size: bool = Field(
        default=True,
        description="Show total size calculations",
        env='TEST_SHOW_TOTAL_SIZE'
    )
    
    # =============================================================================
    # WEB INTERFACE SETTINGS
    # =============================================================================
    web_host: str = Field(
        default="0.0.0.0",
        description="Web interface host",
        env='WEB_HOST'
    )
    web_port: PositiveInt = Field(
        default=5445,
        ge=1,
        le=65535,
        description="Web interface port",
        env='WEB_PORT'
    )
    port: PositiveInt = Field(
        default=5445,
        ge=1,
        le=65535,
        description="Application port (alias for web_port)",
        env='PORT'
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        env='DEBUG'
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level",
        env='LOG_LEVEL'
    )
    enable_scheduler: bool = Field(
        default=False,
        description="Enable task scheduler",
        env='ENABLE_SCHEDULER'
    )
    
    # =============================================================================
    # NOTIFICATIONS
    # =============================================================================
    webhook_url: Optional[str] = Field(
        default=None,
        description="Webhook URL for notifications",
        env='WEBHOOK_URL'
    )
    notification_type: str = Field(
        default="webhook",
        description="Notification type",
        env='NOTIFICATION_TYPE'
    )
    
    # =============================================================================
    # CONTAINER CONFIGURATION
    # =============================================================================
    tz: str = Field(
        default="UTC",
        description="Timezone",
        env='TZ'
    )

    # =============================================================================
    # FIELD VALIDATORS
    # =============================================================================
    
    @field_validator('additional_sources', 'additional_plex_sources', mode='before')
    @classmethod
    def parse_comma_separated(cls, v) -> List[str]:
        """Parse comma-separated environment variables into lists."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        elif isinstance(v, list):
            return v
        return []

    @field_validator('plex_url')
    @classmethod
    def validate_plex_url(cls, v: str) -> str:
        """Validate and normalize Plex URL."""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Plex URL must start with http:// or https://')
        return v.rstrip('/')

    @field_validator('webhook_url')
    @classmethod
    def validate_webhook_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate webhook URL if provided."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Webhook URL must start with http:// or https://')
        return v

    @field_validator('log_level', mode='before')
    @classmethod
    def normalize_log_level(cls, v) -> str:
        """Normalize log level to uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v

    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    
    def get_plex_config(self) -> PlexConfig:
        """Get Plex configuration as a validated model."""
        return PlexConfig(
            url=self.plex_url,
            token=self.plex_token,
            username=self.plex_username,
            password=self.plex_password.get_secret_value() if self.plex_password else None
        )

    def get_media_config(self) -> MediaConfig:
        """Get media configuration as a validated model."""
        return MediaConfig(
            exit_if_active_session=self.exit_if_active_session,
            watched_move=self.watched_move,
            users_toggle=self.users_toggle,
            watchlist_toggle=self.watchlist_toggle,
            days_to_monitor=self.days_to_monitor,
            number_episodes=self.number_episodes,
            watchlist_episodes=self.watchlist_episodes,
            copy_to_cache=self.copy_to_cache,
            delete_from_cache_when_done=self.delete_from_cache_when_done,
            watchlist_cache_expiry=self.watchlist_cache_expiry,
            watched_cache_expiry=self.watched_cache_expiry
        )

    def get_paths_config(self) -> PathsConfig:
        """Get paths configuration as a validated model."""
        return PathsConfig(
            plex_source=self.plex_source,
            cache_destination=self.cache_destination,
            additional_sources=self.additional_sources,
            additional_plex_sources=self.additional_plex_sources
        )

    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration as a validated model."""
        return PerformanceConfig(
            max_concurrent_moves_cache=self.max_concurrent_moves_cache,
            max_concurrent_moves_array=self.max_concurrent_moves_array,
            max_concurrent_local_transfers=self.max_concurrent_local_transfers,
            max_concurrent_network_transfers=self.max_concurrent_network_transfers
        )

    def model_dump_for_api(self) -> Dict[str, Any]:
        """
        Dump model for API consumption with nested structure.
        
        Returns:
            Dictionary with nested configuration structure matching the old format
        """
        return {
            'plex': {
                'url': self.plex_url,
                'token': self.plex_token,
                'username': self.plex_username,
            },
            'paths': {
                'plex_source': self.plex_source,
                'cache_destination': self.cache_destination,
                'additional_sources': self.additional_sources,
                'additional_plex_sources': self.additional_plex_sources,
            },
            'media': {
                'exit_if_active_session': self.exit_if_active_session,
                'watched_move': self.watched_move,
                'users_toggle': self.users_toggle,
                'watchlist_toggle': self.watchlist_toggle,
                'days_to_monitor': self.days_to_monitor,
                'number_episodes': self.number_episodes,
                'watchlist_episodes': self.watchlist_episodes,
                'copy_to_cache': self.copy_to_cache,
                'delete_from_cache_when_done': self.delete_from_cache_when_done,
                'watchlist_cache_expiry': self.watchlist_cache_expiry,
                'watched_cache_expiry': self.watched_cache_expiry,
            },
            'performance': {
                'max_concurrent_moves_cache': self.max_concurrent_moves_cache,
                'max_concurrent_moves_array': self.max_concurrent_moves_array,
                'max_concurrent_local_transfers': self.max_concurrent_local_transfers,
                'max_concurrent_network_transfers': self.max_concurrent_network_transfers,
            },
            'real_time_watch': {
                'enabled': self.real_time_watch_enabled,
                'check_interval': self.real_time_watch_check_interval,
                'auto_cache_on_watch': self.real_time_watch_auto_cache_on_watch,
                'cache_on_complete': self.real_time_watch_cache_on_complete,
                'respect_existing_rules': self.real_time_watch_respect_existing_rules,
                'max_concurrent_watches': self.real_time_watch_max_concurrent_watches,
                'remove_from_cache_after_hours': self.real_time_watch_remove_from_cache_after_hours,
                'respect_other_users_watchlists': self.real_time_watch_respect_other_users_watchlists,
                'exclude_inactive_users_days': self.real_time_watch_exclude_inactive_users_days,
            },
            'trakt': {
                'enabled': self.trakt_enabled,
                'client_id': self.trakt_client_id,
                'client_secret': self.trakt_client_secret.get_secret_value() if self.trakt_client_secret else None,
                'trending_movies_count': self.trakt_trending_movies_count,
                'check_interval': self.trakt_check_interval,
            },
            'test_mode': {
                'enabled': self.test_mode,
                'show_file_sizes': self.test_show_file_sizes,
                'show_total_size': self.test_show_total_size,
            },
            'logging': {
                'level': self.log_level.value,
            },
            'debug': self.debug,
            'web_host': self.web_host,
            'web_port': self.web_port,
        }


# Global settings instance - will be instantiated on first import
_settings: Optional[CacherrSettings] = None


def get_settings() -> CacherrSettings:
    """
    Get the global settings instance.
    
    This function implements the singleton pattern for settings,
    ensuring consistent configuration across the application.
    
    Returns:
        The global CacherrSettings instance
    """
    global _settings
    if _settings is None:
        _settings = CacherrSettings()
    return _settings


def reload_settings() -> CacherrSettings:
    """
    Reload settings from environment variables.
    
    Useful for testing or when environment variables change.
    
    Returns:
        Newly loaded CacherrSettings instance
    """
    global _settings
    _settings = CacherrSettings()
    return _settings
