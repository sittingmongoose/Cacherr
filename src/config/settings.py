import os
import json
import logging
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoggingConfig:
    level: str
    max_files: int
    max_size_mb: int

@dataclass
class PlexConfig:
    url: str
    token: str
    username: str
    password: str

@dataclass
class CacheConfig:
    source_paths: List[str]
    destination_path: str
    max_cache_size_gb: int
    test_mode: bool

@dataclass
class RealTimeWatchConfig:
    enabled: bool
    check_interval: int
    # Backwards-compatible/expanded flags
    cache_when_watching: bool
    auto_cache_on_watch: bool = False
    cache_on_complete: bool = True
    respect_existing_rules: bool = True
    remove_from_cache_after_hours: int = 24
    respect_other_users_watchlists: bool = True
    exclude_inactive_users_days: int = 30

@dataclass
class TraktConfig:
    enabled: bool
    client_id: str
    client_secret: str
    trending_movies_count: int
    check_interval: int

@dataclass
class WebConfig:
    host: str
    port: int
    debug: bool
    enable_scheduler: bool = False

@dataclass
class MediaConfig:
    exit_if_active_session: bool
    watched_move: bool
    users_toggle: bool
    watchlist_toggle: bool
    days_to_monitor: int
    number_episodes: int
    watchlist_episodes: int
    # New: Copy vs Move behavior
    copy_to_cache: bool
    delete_from_cache_when_done: bool
    # New: Cache access method
    use_symlinks_for_cache: bool
    # New: Hybrid mode - Move + Symlink
    move_with_symlinks: bool
    # Cache expiry settings (with defaults)
    watchlist_cache_expiry: int = 6
    watched_cache_expiry: int = 48

@dataclass
class PathsConfig:
    plex_source: str
    cache_destination: str
    additional_sources: List[str]
    additional_plex_sources: List[str]  # New: corresponding plex sources for additional real sources

@dataclass
class TestModeConfig:
    enabled: bool
    show_file_sizes: bool
    show_total_size: bool
    dry_run: bool

@dataclass
class PerformanceConfig:
    max_concurrent_moves_cache: int
    max_concurrent_moves_array: int
    # Per-source concurrency control
    max_concurrent_local_transfers: int
    max_concurrent_network_transfers: int

@dataclass
class NotificationConfig:
    webhook_url: Optional[str]
    webhook_headers: dict

class Config:
    """
    Application configuration class.
    
    Loads configuration from environment variables and persistent JSON files.
    Provides validation and management of all application settings.
    """
    
    def __init__(self):
        # Setup logger first
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing configuration system")
        self._init_system()
    
    def _init_system(self):
        """Initialize configuration system."""
        # Load persistent config file path
        self.config_file = Path("/config/cacherr_config.json")
        
        self.logging = self._load_logging_config()
        self.plex = self._load_plex_config()
        self.cache = self._load_cache_config()
        self.real_time_watch = self._load_real_time_watch_config()
        self.trakt = self._load_trakt_config()
        self.web = self._load_web_config()
        self.media = self._load_media_config()
        self.paths = self._load_paths_config()
        self.test_mode = self._load_test_mode_config()
        self.notifications = self._load_notification_config()
        self.performance = self._load_performance_config()

    def _load_persistent_config(self) -> dict:
        """Load persistent configuration from JSON file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load persistent config: {e}")
        return {}

    def _save_persistent_config(self, config_data: dict):
        """Save configuration to JSON file"""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save persistent config: {e}")

    def _get_setting_value(self, env_key: str, default: str, persistent_key: str = None, prefer_persistent: bool = False) -> str:
        """Get setting value with configurable priority"""
        
        if prefer_persistent and persistent_key:
            # For user-configurable settings: persistent config > environment variable > default
            persistent_config = self._load_persistent_config()
            
            # Handle nested keys (e.g., 'plex.url' -> persistent_config['plex']['url'])
            if '.' in persistent_key:
                section, key = persistent_key.split('.', 1)
                if section in persistent_config and key in persistent_config[section]:
                    return str(persistent_config[section][key])
            elif persistent_key in persistent_config:
                return str(persistent_config[persistent_key])
            
            # Fall back to environment variable if not in persistent config
            env_value = os.getenv(env_key)
            if env_value:
                return env_value
        else:
            # Default behavior: environment variable > persistent config > default
            env_value = os.getenv(env_key)
            if env_value:
                return env_value
            
            # Then try persistent config
            if persistent_key:
                persistent_config = self._load_persistent_config()
                # Handle nested keys
                if '.' in persistent_key:
                    section, key = persistent_key.split('.', 1)
                    if section in persistent_config and key in persistent_config[section]:
                        return str(persistent_config[section][key])
                elif persistent_key in persistent_config:
                    return str(persistent_config[persistent_key])
        
        # Finally use default
        return default

    def _get_setting_bool(self, env_key: str, default: bool, persistent_key: str = None) -> bool:
        """Get boolean setting value with priority: environment variable > persistent config > default"""
        value = self._get_setting_value(env_key, str(default), persistent_key)
        return value.lower() == 'true'

    def _get_setting_int(self, env_key: str, default: int, persistent_key: str = None) -> int:
        """Get integer setting value with priority: environment variable > persistent config > default"""
        value = self._get_setting_value(env_key, str(default), persistent_key)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _load_logging_config(self) -> LoggingConfig:
        def _to_int(value: str, default: int) -> int:
            try:
                return int(value)
            except Exception:
                return default
        return LoggingConfig(
            level=os.getenv('LOGGING_LEVEL', 'INFO'),
            max_files=_to_int(os.getenv('LOGGING_MAX_FILES', '5'), 5),
            max_size_mb=_to_int(os.getenv('LOGGING_MAX_SIZE_MB', '10'), 10)
        )

    def _load_plex_config(self) -> PlexConfig:
        return PlexConfig(
            url=self._get_setting_value('PLEX_URL', '', 'plex.url', prefer_persistent=True),
            token=self._get_setting_value('PLEX_TOKEN', '', 'plex.token', prefer_persistent=True),
            username=self._get_setting_value('PLEX_USERNAME', '', 'plex.username', prefer_persistent=True),
            password=self._get_setting_value('PLEX_PASSWORD', '', 'plex.password', prefer_persistent=True)
        )

    def _load_cache_config(self) -> CacheConfig:
        # Backwards compatibility for legacy env names used by tests and older setups
        legacy_sources = os.getenv('CACHE_SOURCE_PATHS')
        legacy_dest = os.getenv('CACHE_DESTINATION_PATH')
        legacy_test_mode = os.getenv('CACHE_TEST_MODE')

        # Get source paths from multiple possible env vars
        source_paths: List[str] = []
        if legacy_sources:
            source_paths = [s.strip() for s in legacy_sources.split(',') if s.strip()]
        else:
            # Dynamic path resolution based on environment
            if self._is_likely_docker():
                source_paths.append('/mediasource')  # Docker volume mapping
            else:
                # For non-Docker, try to detect Plex installation
                plex_paths = [
                    '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Media',
                    'C:\\ProgramData\\Plex Media Server\\Media',
                    os.path.expanduser('~/Plex Media Server/Media')
                ]
                for path in plex_paths:
                    if os.path.exists(path):
                        source_paths.append(path)
                        break
                else:
                    source_paths.append('/mediasource')  # Fallback
            
            if os.getenv('ADDITIONAL_SOURCES'):
                source_paths.extend([s.strip() for s in os.getenv('ADDITIONAL_SOURCES').split() if s.strip()])

        # If no sources defined, use dynamic default
        if not source_paths:
            if self._is_likely_docker():
                source_paths = ['/mediasource']
            else:
                source_paths = ['/tmp/mediasource']  # Safe fallback

        # Dynamic destination path
        if legacy_dest:
            destination_path = legacy_dest
        else:
            destination_path = self._get_setting_value('CACHE_DESTINATION', 
                '/cache' if self._is_likely_docker() else '/tmp/cache', 
                'cache.destination')
        
        test_mode = (legacy_test_mode.lower() == 'true') if legacy_test_mode else self._get_setting_bool('TEST_MODE', False, 'test_mode.enabled')

        return CacheConfig(
            source_paths=source_paths,
            destination_path=destination_path,
            max_cache_size_gb=self._get_setting_int('CACHE_MAX_SIZE_GB', 100, 'cache.max_cache_size_gb'),
            test_mode=test_mode
        )
    
    def _is_likely_docker(self) -> bool:
        """Simple Docker detection for legacy system."""
        return (
            os.path.exists('/.dockerenv') or
            os.getenv('DOCKER_CONTAINER') is not None or
            os.path.exists('/proc/1/cgroup') and 'docker' in open('/proc/1/cgroup', 'r').read().lower()
        )

    def _load_real_time_watch_config(self) -> RealTimeWatchConfig:
        # Support both old and new env var names
        cache_when_watching = os.getenv('REAL_TIME_WATCH_CACHE_WHEN_WATCHING', 'false').lower() == 'true'
        auto_cache_on_watch = os.getenv('REAL_TIME_WATCH_AUTO_CACHE_ON_WATCH', 'false').lower() == 'true'
        cache_on_complete = os.getenv('REAL_TIME_WATCH_CACHE_ON_COMPLETE', 'true').lower() == 'true'
        respect_existing_rules = os.getenv('REAL_TIME_WATCH_RESPECT_EXISTING_RULES', 'true').lower() == 'true'

        # safe int parsing
        def _to_int(value: str, default: int) -> int:
            try:
                return int(value)
            except Exception:
                return default
        return RealTimeWatchConfig(
            enabled=os.getenv('REAL_TIME_WATCH_ENABLED', 'false').lower() == 'true',
            check_interval=_to_int(os.getenv('REAL_TIME_WATCH_CHECK_INTERVAL', '30'), 30),
            cache_when_watching=auto_cache_on_watch,
            auto_cache_on_watch=auto_cache_on_watch,
            cache_on_complete=cache_on_complete,
            respect_existing_rules=respect_existing_rules,
            remove_from_cache_after_hours=_to_int(os.getenv('REAL_TIME_WATCH_REMOVE_FROM_CACHE_AFTER_HOURS', '24'), 24),
            respect_other_users_watchlists=os.getenv('REAL_TIME_WATCH_RESPECT_OTHER_USERS_WATCHLISTS', 'true').lower() == 'true',
            exclude_inactive_users_days=_to_int(os.getenv('REAL_TIME_WATCH_EXCLUDE_INACTIVE_USERS_DAYS', '30'), 30)
        )

    def _load_trakt_config(self) -> TraktConfig:
        def _to_int(value: str, default: int) -> int:
            try:
                return int(value)
            except Exception:
                return default
        return TraktConfig(
            enabled=os.getenv('TRAKT_ENABLED', 'false').lower() == 'true',
            client_id=os.getenv('TRAKT_CLIENT_ID', ''),
            client_secret=os.getenv('TRAKT_CLIENT_SECRET', ''),
            trending_movies_count=_to_int(os.getenv('TRAKT_TRENDING_MOVIES_COUNT', '10'), 10),
            check_interval=_to_int(os.getenv('TRAKT_CHECK_INTERVAL', '3600'), 3600)  # Default: 1 hour
        )

    def _load_web_config(self) -> WebConfig:
        def _to_int(value: str, default: int) -> int:
            try:
                return int(value)
            except Exception:
                return default
        return WebConfig(
            host=os.getenv('WEB_HOST', '0.0.0.0'),
            port=_to_int(os.getenv('WEB_PORT', os.getenv('PORT', '5443')), 5443),
            debug=os.getenv('WEB_DEBUG', os.getenv('DEBUG', 'false')).lower() == 'true',
            enable_scheduler=os.getenv('ENABLE_SCHEDULER', 'false').lower() == 'true'
        )

    def _load_media_config(self) -> MediaConfig:
        persistent_config = self._load_persistent_config()
        media_config = persistent_config.get('media', {})
        
        # Load from persistent config first, fall back to environment variables
        def get_bool(key, env_key, default='false'):
            value = media_config.get(key)
            if value is not None:
                return bool(value) if isinstance(value, bool) else str(value).lower() == 'true'
            return os.getenv(env_key, default).lower() == 'true'
        
        def get_int(key, env_key, default):
            value = media_config.get(key)
            if value is not None:
                return int(value)
            return int(os.getenv(env_key, str(default)))
        
        return MediaConfig(
            exit_if_active_session=get_bool('exit_if_active_session', 'EXIT_IF_ACTIVE_SESSION', 'false'),
            watched_move=get_bool('watched_move', 'WATCHED_MOVE', 'true'),
            users_toggle=get_bool('users_toggle', 'USERS_TOGGLE', 'true'),
            watchlist_toggle=get_bool('watchlist_toggle', 'WATCHLIST_TOGGLE', 'true'),
            days_to_monitor=get_int('days_to_monitor', 'DAYS_TO_MONITOR', 99),
            number_episodes=get_int('number_episodes', 'NUMBER_EPISODES', 5),
            watchlist_episodes=get_int('watchlist_episodes', 'WATCHLIST_EPISODES', 1),
            # New: Copy vs Move behavior
            copy_to_cache=get_bool('copy_to_cache', 'COPY_TO_CACHE', 'false'),
            delete_from_cache_when_done=get_bool('delete_from_cache_when_done', 'DELETE_FROM_CACHE_WHEN_DONE', 'true'),
            # New: Cache access method
            use_symlinks_for_cache=get_bool('use_symlinks_for_cache', 'USE_SYMLINKS_FOR_CACHE', 'true'),
            # New: Hybrid mode - Move + Symlink
            move_with_symlinks=get_bool('move_with_symlinks', 'MOVE_WITH_SYMLINKS', 'false')
        )

    def _load_paths_config(self) -> PathsConfig:
        # Clean up additional sources - remove empty strings
        additional_sources = []
        if os.getenv('ADDITIONAL_SOURCES'):
            additional_sources = [s.strip() for s in os.getenv('ADDITIONAL_SOURCES').split() if s.strip()]
        
        # Clean up additional plex sources - remove empty strings
        additional_plex_sources = []
        if os.getenv('ADDITIONAL_PLEX_SOURCES'):
            additional_plex_sources = [s.strip() for s in os.getenv('ADDITIONAL_PLEX_SOURCES').split() if s.strip()]
        
        return PathsConfig(
            plex_source=os.getenv('PLEX_SOURCE', '/media'),
            cache_destination=os.getenv('CACHE_DESTINATION', ''),
            additional_sources=additional_sources,
            additional_plex_sources=additional_plex_sources
        )

    def _load_test_mode_config(self) -> TestModeConfig:
        persistent_config = self._load_persistent_config()
        test_mode_config = persistent_config.get('test_mode', {})
        
        # Load from persistent config first, fall back to environment variables
        enabled = test_mode_config.get('enabled', os.getenv('TEST_MODE', 'false').lower() == 'true')
        show_file_sizes = test_mode_config.get('show_file_sizes', os.getenv('TEST_SHOW_FILE_SIZES', 'true').lower() == 'true')
        show_total_size = test_mode_config.get('show_total_size', os.getenv('TEST_SHOW_TOTAL_SIZE', 'true').lower() == 'true')
        dry_run = test_mode_config.get('dry_run', True)  # Test mode should always be safe - no file movement
        
        return TestModeConfig(
            enabled=enabled,
            show_file_sizes=show_file_sizes,
            show_total_size=show_total_size,
            dry_run=dry_run
        )

    def _load_performance_config(self) -> PerformanceConfig:
        def _to_int(value: str, default: int) -> int:
            try:
                return int(value)
            except Exception:
                return default
        return PerformanceConfig(
            max_concurrent_moves_cache=_to_int(os.getenv('MAX_CONCURRENT_MOVES_CACHE', '5'), 5),
            max_concurrent_moves_array=_to_int(os.getenv('MAX_CONCURRENT_MOVES_ARRAY', '2'), 2),
            # Per-source concurrency control
            max_concurrent_local_transfers=_to_int(os.getenv('MAX_CONCURRENT_LOCAL_TRANSFERS', '5'), 5),
            max_concurrent_network_transfers=_to_int(os.getenv('MAX_CONCURRENT_NETWORK_TRANSFERS', '2'), 2)
        )

    def _load_notification_config(self) -> NotificationConfig:
        webhook_url = os.getenv('WEBHOOK_URL')
        webhook_headers = {}
        
        # Parse webhook headers if provided
        webhook_headers_str = os.getenv('WEBHOOK_HEADERS', '')
        if webhook_headers_str:
            try:
                # Expected format: "key1:value1,key2:value2"
                for header in webhook_headers_str.split(','):
                    if ':' in header:
                        key, value = header.split(':', 1)
                        webhook_headers[key.strip()] = value.strip()
            except Exception:
                pass
        
        return NotificationConfig(
            webhook_url=webhook_url,
            webhook_headers=webhook_headers
        )

    def validate(self) -> bool:
        """Validate the configuration"""
        try:
            # Validation
            # Basic validation - check required fields
            # Note: PLEX_URL and PLEX_TOKEN can be configured via web interface
            # so they're not required at startup
            
            # Enhanced path validation
            for source_path in self.cache.source_paths:
                if not self._is_likely_docker() and not os.path.exists(source_path):
                    self.logger.warning(f"Source path does not exist: {source_path}")
            
            # Check cache destination is writable
            cache_dir = Path(self.cache.destination_path)
            if not self._is_likely_docker():
                try:
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    test_file = cache_dir / '.write_test'
                    test_file.touch()
                    test_file.unlink()
                except (PermissionError, OSError) as e:
                    self.logger.error(f"Cache destination not writable: {cache_dir} - {e}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def reload(self):
        """Reload configuration from environment variables and persistent config"""
        self.plex = self._load_plex_config()
        self.cache = self._load_cache_config()
        self.real_time_watch = self._load_real_time_watch_config()
        self.trakt = self._load_trakt_config()
        self.web = self._load_web_config()
        self.media = self._load_media_config()
        self.paths = self._load_paths_config()
        self.test_mode = self._load_test_mode_config()
        self.notifications = self._load_notification_config()
        self.performance = self._load_performance_config()
        
        self.logger.info("Configuration reloaded from environment variables and persistent config")

    def update_persistent_config(self, section: str, key: str, value):
        """Update a setting in persistent configuration"""
        try:
            persistent_config = self._load_persistent_config()
            
            if section not in persistent_config:
                persistent_config[section] = {}
            
            persistent_config[section][key] = value
            
            self._save_persistent_config(persistent_config)
            
            # Reload the specific section
            if section == 'plex':
                self.plex = self._load_plex_config()
            elif section == 'cache':
                self.cache = self._load_cache_config()
            elif section == 'real_time_watch':
                self.real_time_watch = self._load_real_time_watch_config()
            elif section == 'trakt':
                self.trakt = self._load_trakt_config()
            elif section == 'web':
                self.web = self._load_web_config()
            elif section == 'media':
                self.media = self._load_media_config()
            elif section == 'paths':
                self.paths = self._load_paths_config()
            elif section == 'test_mode':
                self.test_mode = self._load_test_mode_config()
            elif section == 'notifications':
                self.notifications = self._load_notification_config()
            elif section == 'performance':
                self.performance = self._load_performance_config()
            
            self.logger.info(f"Updated persistent config: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update persistent config: {e}")
            return False

    def to_dict(self):
        """Convert configuration to dictionary for API responses"""
        return {
            'logging': {
                'level': self.logging.level,
                'max_files': self.logging.max_files,
                'max_size_mb': self.logging.max_size_mb
            },
            'plex': {
                'url': self.plex.url,
                'token': '***' if self.plex.token else '',
                'username': self.plex.username,
                'password': '***' if self.plex.password else ''
            },
            'cache': {
                'source_paths': self.cache.source_paths,
                'destination_path': self.cache.destination_path,
                'max_cache_size_gb': self.cache.max_cache_size_gb,
                'test_mode': self.cache.test_mode
            },
            'real_time_watch': {
                'enabled': self.real_time_watch.enabled,
                'check_interval': self.real_time_watch.check_interval,
                'cache_when_watching': self.real_time_watch.cache_when_watching,
                'remove_from_cache_after_hours': self.real_time_watch.remove_from_cache_after_hours,
                'respect_other_users_watchlists': self.real_time_watch.respect_other_users_watchlists,
                'exclude_inactive_users_days': self.real_time_watch.exclude_inactive_users_days
            },
            'trakt': {
                'enabled': self.trakt.enabled,
                'client_id': '***' if self.trakt.client_id else '',
                'client_secret': '***' if self.trakt.client_secret else '',
                'trending_movies_count': self.trakt.trending_movies_count,
                'check_interval': self.trakt.check_interval
            },
            'web': {
                'host': self.web.host,
                'port': self.web.port,
                'debug': self.web.debug,
                'enable_scheduler': getattr(self.web, 'enable_scheduler', False)
            },
            'media': {
                'exit_if_active_session': self.media.exit_if_active_session,
                'watched_move': self.media.watched_move,
                'users_toggle': self.media.users_toggle,
                'watchlist_toggle': self.media.watchlist_toggle,
                'days_to_monitor': self.media.days_to_monitor,
                'number_episodes': self.media.number_episodes,
                'watchlist_episodes': self.media.watchlist_episodes,
                'copy_to_cache': self.media.copy_to_cache,
                'delete_from_cache_when_done': self.media.delete_from_cache_when_done,
                'use_symlinks_for_cache': self.media.use_symlinks_for_cache,
                'move_with_symlinks': self.media.move_with_symlinks
            },
            'paths': {
                'plex_source': self.paths.plex_source,
                'cache_destination': self.paths.cache_destination
                # Note: additional_sources and additional_plex_sources are only configurable via Docker environment variables
            },
            'test_mode': {
                'enabled': self.test_mode.enabled,
                'show_file_sizes': self.test_mode.show_file_sizes,
                'show_total_size': self.test_mode.show_total_size,
                'dry_run': self.test_mode.dry_run
            },
            'performance': {
                'max_concurrent_moves_cache': self.performance.max_concurrent_moves_cache,
                'max_concurrent_moves_array': self.performance.max_concurrent_moves_array,
                'max_concurrent_local_transfers': self.performance.max_concurrent_local_transfers,
                'max_concurrent_network_transfers': self.performance.max_concurrent_network_transfers
            },
            'notifications': {
                'webhook_url': self.notifications.webhook_url,
                'webhook_headers': self.notifications.webhook_headers
            }
        }
