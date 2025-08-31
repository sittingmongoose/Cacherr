"""
Modern Pydantic v2.5 configuration system for Cacherr.

This module provides a consolidated, production-ready configuration system using
Pydantic v2.5 patterns with comprehensive validation, environment variable support,
and type safety. All legacy configuration systems have been removed.

Example:
    >>> config = Config()
    >>> config.media.copy_to_cache
    True
    >>> config.plex.url
    'http://localhost:32400'
    >>> config.save_updates({'media': {'copy_to_cache': False}})
"""

import json
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from pydantic import ValidationError

from .base_settings import CacherrSettings, get_settings
from .pydantic_models import (
    LoggingConfig, PlexConfig, MediaConfig, PathsConfig, PerformanceConfig,
    LogLevel
)
from .performance_optimizations import get_optimized_settings, monitor_performance

logger = logging.getLogger(__name__)


class Config:
    """
    Modern Pydantic-based configuration system.
    
    This class provides a clean, type-safe configuration interface using
    Pydantic v2 models with comprehensive validation and environment variable
    support. It completely replaces the old dataclass-based configuration.
    
    Attributes:
        settings: The underlying Pydantic settings model
        plex: Validated Plex server configuration
        media: Validated media processing configuration
        paths: Validated path configuration
        performance: Validated performance configuration
        logging: Validated logging configuration
        
    Example:
        >>> config = Config()
        >>> config.media.copy_to_cache
        True
        >>> config.media.cache_mode_description
        'Copy to cache (preserves originals)'
    """
    
    def __init__(self, settings: Optional[CacherrSettings] = None, use_optimizations: bool = True):
        """
        Initialize modern configuration system.
        
        Args:
            settings: Optional CacherrSettings instance
            use_optimizations: Whether to use performance optimizations
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing modern Pydantic v2 configuration system")
        
        # Use optimized settings in production, regular settings in development
        if use_optimizations:
            self.settings = settings or get_optimized_settings()
        else:
            self.settings = settings or get_settings()
        
        # Configuration file path
        self.config_file = Path(self.settings.config_dir) / "cacherr_config.json"
        
        # Initialize typed configuration objects
        self._initialize_configurations()
        
        # Load persistent overrides
        self._load_persistent_overrides()
    
    @monitor_performance
    def _initialize_configurations(self) -> None:
        """Initialize all configuration objects from settings."""
        try:
            # Core configurations using Pydantic models
            self.plex = self.settings.get_plex_config()
            self.media = self.settings.get_media_config() 
            self.paths = self.settings.get_paths_config()
            self.performance = self.settings.get_performance_config()
            
            # Logging configuration
            self.logging = LoggingConfig(
                level=self.settings.log_level,
                max_files=5,
                max_size_mb=10
            )
            
            # Additional configurations for API compatibility
            self.real_time_watch = self._build_real_time_watch_config()
            self.trakt = self._build_trakt_config()
            self.web = self._build_web_config()
            self.test_mode = self._build_test_mode_config()
            self.notifications = self._build_notification_config()
            
            # Legacy compatibility properties
            self.cache = self._build_cache_config()
            
        except ValidationError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}") from e
    
    def _build_real_time_watch_config(self) -> 'RealTimeWatchConfiguration':
        """Build real-time watch configuration."""
        from .interfaces import RealTimeWatchConfiguration
        
        return RealTimeWatchConfiguration(
            enabled=self.settings.real_time_watch_enabled,
            check_interval=self.settings.real_time_watch_check_interval,
            auto_cache_on_watch=self.settings.real_time_watch_auto_cache_on_watch,
            cache_on_complete=self.settings.real_time_watch_cache_on_complete,
            respect_existing_rules=self.settings.real_time_watch_respect_existing_rules,
            max_concurrent_watches=self.settings.real_time_watch_max_concurrent_watches,
            remove_from_cache_after_hours=self.settings.real_time_watch_remove_from_cache_after_hours,
            respect_other_users_watchlists=self.settings.real_time_watch_respect_other_users_watchlists,
            exclude_inactive_users_days=self.settings.real_time_watch_exclude_inactive_users_days,
        )
    
    def _build_trakt_config(self) -> 'TraktConfiguration':
        """Build Trakt.tv configuration."""
        from .interfaces import TraktConfiguration
        
        return TraktConfiguration(
            enabled=self.settings.trakt_enabled,
            client_id=self.settings.trakt_client_id,
            client_secret=self.settings.trakt_client_secret.get_secret_value() if self.settings.trakt_client_secret else None,
            trending_movies_count=self.settings.trakt_trending_movies_count,
            check_interval=self.settings.trakt_check_interval,
        )
    
    def _build_web_config(self) -> 'WebConfiguration':
        """Build web server configuration."""
        from .interfaces import WebConfiguration
        
        return WebConfiguration(
            host=self.settings.web_host,
            port=self.settings.web_port,
            debug=self.settings.debug,
            enable_scheduler=self.settings.enable_scheduler,
        )
    
    def _build_test_mode_config(self) -> Dict[str, Any]:
        """Build test mode configuration."""
        return {
            'enabled': self.settings.test_mode,
            'show_file_sizes': self.settings.test_show_file_sizes,
            'show_total_size': self.settings.test_show_total_size,
            'dry_run': self.settings.test_mode,
        }
    
    def _build_notification_config(self) -> 'NotificationConfiguration':
        """Build notification configuration."""
        from .interfaces import NotificationConfiguration
        
        return NotificationConfiguration(
            enabled=True,  # Default to enabled
            webhook_url=self.settings.webhook_url,
            webhook_headers={},  # Default empty headers
            notification_levels=['error', 'warning', 'info'],
            rate_limit_minutes=5
        )
    
    def _build_cache_config(self) -> Dict[str, Any]:
        """Build cache configuration for legacy compatibility."""
        return {
            'source_paths': self.paths.additional_sources,
            'destination_path': self.paths.cache_destination,
            'max_cache_size_gb': 0,  # Not implemented in new system
            'test_mode': self.test_mode['enabled']
        }
    
    @monitor_performance
    def _load_persistent_overrides(self) -> None:
        """Load persistent configuration overrides from JSON file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    persistent_config = json.load(f)
                self._apply_overrides(persistent_config)
                self.logger.info("Loaded persistent configuration overrides")
        except Exception as e:
            self.logger.warning(f"Failed to load persistent overrides: {e}")
    
    def _apply_overrides(self, overrides: Dict[str, Any]) -> None:
        """
        Apply configuration overrides with validation.
        
        Args:
            overrides: Dictionary of configuration overrides
        """
        # Apply media configuration overrides
        if 'media' in overrides:
            try:
                # Exclude all computed fields when dumping model data to prevent serialization issues
                media_data = self.media.model_dump(exclude={
                    'cache_mode_description',
                    'estimated_cache_lifetime_hours'
                })
                media_data.update(overrides['media'])
                self.media = MediaConfig(**media_data)
                self.logger.debug("Applied media configuration overrides")
            except ValidationError as e:
                self.logger.warning(f"Invalid media override: {e}")

        # Apply performance configuration overrides
        if 'performance' in overrides:
            try:
                # Exclude all computed fields when dumping model data to prevent serialization issues
                perf_data = self.performance.model_dump(exclude={
                    'total_max_concurrent',
                    'performance_profile',
                    'resource_intensity_score',
                    'concurrency_breakdown'
                })
                perf_data.update(overrides['performance'])
                self.performance = PerformanceConfig(**perf_data)
                self.logger.debug("Applied performance configuration overrides")
            except ValidationError as e:
                self.logger.warning(f"Invalid performance override: {e}")
        
        # Apply plex configuration overrides
        if 'plex' in overrides:
            try:
                # Exclude computed fields when dumping model data to prevent serialization issues
                plex_data = self.plex.model_dump(exclude={
                    'has_credentials',
                    'config_type',
                    'version'
                })
                plex_data.update(overrides['plex'])
                self.plex = PlexConfig(**plex_data)
                self.logger.debug("Applied plex configuration overrides")
            except ValidationError as e:
                self.logger.warning(f"Invalid plex override: {e}")

        # Apply paths configuration overrides
        if 'paths' in overrides:
            try:
                # Exclude computed fields when dumping model data to prevent serialization issues
                paths_data = self.paths.model_dump(exclude={
                    'total_source_paths',
                    'has_additional_sources',
                    'primary_source',
                    'config_type',
                    'version'
                })
                paths_data.update(overrides['paths'])
                self.paths = PathsConfig(**paths_data)
                self.logger.debug("Applied paths configuration overrides")
            except ValidationError as e:
                self.logger.warning(f"Invalid paths override: {e}")

        # Apply logging configuration overrides
        if 'logging' in overrides:
            try:
                # Exclude computed fields when dumping model data to prevent serialization issues
                logging_data = self.logging.model_dump(exclude={
                    'config_type',
                    'version'
                })
                logging_data.update(overrides['logging'])
                self.logging = LogLevel(**logging_data)
                self.logger.debug("Applied logging configuration overrides")
            except ValidationError as e:
                self.logger.warning(f"Invalid logging override: {e}")

        # Apply other overrides
        for section, section_overrides in overrides.items():
            if section in ['real_time_watch', 'trakt', 'web', 'test_mode', 'notifications']:
                if hasattr(self, section):
                    current_config = getattr(self, section)
                    if hasattr(current_config, 'model_dump'):  # Pydantic model
                        try:
                            # Exclude computed fields if any
                            exclude_fields = set()
                            if section == 'real_time_watch':
                                # No computed fields for RealTimeWatchConfiguration
                                pass
                            elif section == 'trakt':
                                # No computed fields for TraktConfiguration
                                pass
                            elif section == 'web':
                                # No computed fields for WebConfiguration
                                pass
                            elif section == 'notifications':
                                # No computed fields for NotificationConfiguration
                                pass

                            config_data = current_config.model_dump(exclude=exclude_fields)
                            config_data.update(section_overrides)

                            # Recreate the appropriate model
                            if section == 'real_time_watch':
                                from .interfaces import RealTimeWatchConfiguration
                                setattr(self, section, RealTimeWatchConfiguration(**config_data))
                            elif section == 'trakt':
                                from .interfaces import TraktConfiguration
                                setattr(self, section, TraktConfiguration(**config_data))
                            elif section == 'web':
                                from .interfaces import WebConfiguration
                                setattr(self, section, WebConfiguration(**config_data))
                            elif section == 'notifications':
                                from .interfaces import NotificationConfiguration
                                setattr(self, section, NotificationConfiguration(**config_data))

                            self.logger.debug(f"Applied {section} configuration overrides")
                        except ValidationError as e:
                            self.logger.warning(f"Invalid {section} override: {e}")
                    elif isinstance(current_config, dict):  # Legacy dict support
                        current_config.update(section_overrides)
    
    @monitor_performance
    def save_updates(self, updates: Dict[str, Any]) -> None:
        """
        Save configuration updates with validation and persistence.
        
        Args:
            updates: Dictionary of configuration updates
            
        Raises:
            ValueError: If validation fails for any update
        """
        try:
            # Validate updates before saving
            self._validate_updates(updates)
            
            # Apply updates to current configuration
            self._apply_overrides(updates)
            
            # Save to persistent storage
            self._save_to_file(updates)
            
            self.logger.info("Configuration updates saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration updates: {e}")
            raise
    
    def _validate_updates(self, updates: Dict[str, Any]) -> None:
        """
        Validate configuration updates.
        
        Args:
            updates: Dictionary of updates to validate
            
        Raises:
            ValueError: If any update is invalid
        """
        # Validate media updates
        if 'media' in updates:
            try:
                # Exclude computed fields when dumping model data
                media_data = self.media.model_dump(exclude={'cache_mode_description'})
                media_data.update(updates['media'])
                MediaConfig(**media_data)  # Validate without assigning
            except ValidationError as e:
                raise ValueError(f"Invalid media configuration: {e}") from e
        
        # Validate performance updates
        if 'performance' in updates:
            try:
                # Exclude computed fields when dumping model data
                perf_data = self.performance.model_dump(exclude={'total_max_concurrent'})
                perf_data.update(updates['performance'])
                PerformanceConfig(**perf_data)  # Validate without assigning
            except ValidationError as e:
                raise ValueError(f"Invalid performance configuration: {e}") from e
        
        # Validate other configuration updates
        for section, section_updates in updates.items():
            if section in ['real_time_watch', 'trakt', 'web', 'notifications']:
                if hasattr(self, section):
                    current_config = getattr(self, section)
                    if hasattr(current_config, 'model_dump'):  # Pydantic model
                        try:
                            config_data = current_config.model_dump()
                            config_data.update(section_updates)
                            
                            # Validate with appropriate model
                            if section == 'real_time_watch':
                                from .interfaces import RealTimeWatchConfiguration
                                RealTimeWatchConfiguration(**config_data)
                            elif section == 'trakt':
                                from .interfaces import TraktConfiguration
                                TraktConfiguration(**config_data)
                            elif section == 'web':
                                from .interfaces import WebConfiguration
                                WebConfiguration(**config_data)
                            elif section == 'notifications':
                                from .interfaces import NotificationConfiguration
                                NotificationConfiguration(**config_data)
                        except ValidationError as e:
                            raise ValueError(f"Invalid {section} configuration: {e}") from e
    
    def _save_to_file(self, updates: Dict[str, Any]) -> None:
        """
        Save updates to persistent configuration file.
        
        Args:
            updates: Dictionary of updates to save
        """
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing configuration
            existing_config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    existing_config = json.load(f)
            
            # Merge updates
            existing_config.update(updates)
            
            # Save merged configuration
            with open(self.config_file, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration file: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export complete configuration as dictionary, excluding computed fields.

        This method ensures that computed fields are not included in the exported
        configuration to prevent Pydantic validation errors when loading.

        Returns:
            Dictionary representation of all configuration sections
        """
        return {
            'plex': self.plex.model_dump(exclude={'has_credentials'}),
            'media': self.media.model_dump(exclude={'cache_mode_description', 'estimated_lifetime_hours', 'performance_profile', 'multi_user_enabled', 'watchlist_enabled'}),
            'paths': self.paths.model_dump(exclude={'total_source_paths', 'has_additional_sources', 'primary_source'}),
            'performance': self.performance.model_dump(exclude={'total_max_concurrent', 'performance_profile', 'resource_intensity_score', 'concurrency_breakdown'}),
            'logging': self.logging.model_dump(exclude={'config_type', 'version'}),
            'real_time_watch': self.real_time_watch.model_dump() if hasattr(self.real_time_watch, 'model_dump') else self.real_time_watch,
            'trakt': self.trakt.model_dump() if hasattr(self.trakt, 'model_dump') else self.trakt,
            'web': self.web.model_dump() if hasattr(self.web, 'model_dump') else self.web,
            'test_mode': self.test_mode,
            'notifications': self.notifications.model_dump() if hasattr(self.notifications, 'model_dump') else self.notifications,
            'cache': self.cache,  # Legacy compatibility
            'debug': self.settings.debug,
        }
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Validate entire configuration and return detailed results.
        
        Returns:
            Dictionary with validation results for each section
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sections': {}
        }
        
        # Validate Pydantic model sections
        sections = [
            ('plex', self.plex),
            ('media', self.media),
            ('paths', self.paths),
            ('performance', self.performance),
            ('logging', self.logging),
        ]
        
        for section_name, config_obj in sections:
            try:
                # Re-validate using Pydantic, excluding all computed fields to prevent serialization issues
                if section_name == 'plex':
                    # Exclude computed fields for PlexConfig
                    dump_data = config_obj.model_dump(exclude={
                        'has_credentials', 'config_type', 'version'
                    })
                elif section_name == 'media':
                    # Exclude computed fields for MediaConfig
                    dump_data = config_obj.model_dump(exclude={
                        'cache_mode_description', 'estimated_cache_lifetime_hours',
                        'config_type', 'version', 'cache_mode', 'performance_profile',
                        'multi_user_enabled', 'watchlist_enabled'
                    })
                elif section_name == 'paths':
                    # Exclude computed fields for PathsConfig
                    dump_data = config_obj.model_dump(exclude={
                        'total_source_paths', 'has_additional_sources', 'primary_source',
                        'config_type', 'version'
                    })
                elif section_name == 'performance':
                    # Exclude computed fields for PerformanceConfig
                    dump_data = config_obj.model_dump(exclude={
                        'total_max_concurrent', 'performance_profile', 'resource_intensity_score',
                        'concurrency_breakdown', 'config_type', 'version'
                    })
                elif section_name == 'logging':
                    # Exclude computed fields for LogLevel
                    dump_data = config_obj.model_dump(exclude={
                        'config_type', 'version'
                    })
                else:
                    # No computed fields to exclude for other configs
                    dump_data = config_obj.model_dump()

                config_obj.model_validate(dump_data)
                results['sections'][section_name] = {
                    'valid': True,
                    'errors': [],
                    'model_class': config_obj.__class__.__name__
                }
            except ValidationError as e:
                results['valid'] = False
                errors = [str(error) for error in e.errors()]
                results['errors'].extend(errors)
                results['sections'][section_name] = {
                    'valid': False,
                    'errors': errors,
                    'model_class': config_obj.__class__.__name__
                }
        
        return results
    
    def reload(self) -> None:
        """Reload configuration from environment variables and files."""
        self.logger.info("Reloading configuration")
        
        # Reload settings from environment
        from .base_settings import reload_settings
        self.settings = reload_settings()
        
        # Reinitialize configurations
        self._initialize_configurations()
        self._load_persistent_overrides()
        
        self.logger.info("Configuration reloaded successfully")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for monitoring/debugging.
        
        Returns:
            Summary of key configuration values and validation status
        """
        validation_results = self.validate_all()
        
        return {
            'valid': validation_results['valid'],
            'error_count': len(validation_results['errors']),
            'sections_count': len(validation_results['sections']),
            'key_settings': {
                'copy_to_cache': self.media.copy_to_cache,
                'cache_mode': self.media.cache_mode_description,
                'plex_url': self.plex.url,
                'cache_destination': self.paths.cache_destination,
                'max_concurrent_cache': self.performance.max_concurrent_moves_cache,
                'log_level': self.logging.level,
                'debug_mode': self.settings.debug,
            },
            'validation_details': validation_results['sections']
        }
    
    # Convenience properties for common access patterns
    @property
    def debug(self) -> bool:
        """Whether debug mode is enabled."""
        return self.settings.debug
    
    @property
    def test_mode_enabled(self) -> bool:
        """Whether test mode is enabled."""
        return self.test_mode['enabled']
    
    @property
    def copy_to_cache_enabled(self) -> bool:
        """Whether copy to cache mode is enabled."""
        return self.media.copy_to_cache


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        The global Config instance with Pydantic v2 validation
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Reload the global configuration.
    
    Returns:
        Newly loaded Config instance
    """
    global _config
    _config = Config()
    return _config
