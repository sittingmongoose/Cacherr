"""
Modern Pydantic v2 configuration package for PlexCacheUltra.

This package provides a complete Pydantic v2-based configuration system with
comprehensive validation, environment variable support, and type safety.
The old dataclass-based configuration has been completely replaced.

Example:
    >>> from src.config import get_config
    >>> config = get_config()
    >>> config.media.copy_to_cache
    True
    >>> config.media.cache_mode_description
    'Copy to cache (preserves originals)'
"""

# Core configuration system (Pydantic v2 based)
from .settings import Config, get_config, reload_config

# Underlying Pydantic models and settings
from .base_settings import CacherrSettings, get_settings, reload_settings
from .pydantic_models import (
    LoggingConfig, PlexConfig, MediaConfig, PathsConfig, PerformanceConfig,
    LogLevel
)

# Performance optimizations
from .performance_optimizations import (
    get_optimized_settings, enable_production_optimizations,
    get_cache_stats, clear_all_caches
)

# Configuration interfaces for dependency injection
from .interfaces import (
    ConfigProvider,
    EnvironmentConfig,
    PathConfiguration,
    PlexConfiguration,
    PathConfigurationModel,
    MediaConfiguration,
    PerformanceConfiguration,
    NotificationConfiguration,
    TestModeConfiguration
)


__all__ = [
    # Primary configuration interface
    'Config', 'get_config', 'reload_config',
    
    # Underlying Pydantic models
    'CacherrSettings', 'get_settings', 'reload_settings',
    'LoggingConfig', 'PlexConfig', 'MediaConfig', 'PathsConfig', 
    'PerformanceConfig', 'LogLevel',
    
    # Performance optimizations
    'get_optimized_settings', 'enable_production_optimizations',
    'get_cache_stats', 'clear_all_caches',
    
    # Configuration interfaces (for DI and type safety)
    'ConfigProvider', 'EnvironmentConfig', 'PathConfiguration',
    'PlexConfiguration', 'PathConfigurationModel', 'MediaConfiguration',
    'PerformanceConfiguration', 'NotificationConfiguration',
    'TestModeConfiguration'
]
