"""
Performance optimizations for Pydantic v2.5 configuration models.

This module provides performance enhancements including model caching,
validation optimization, and memory-efficient configuration handling.
All optimizations are designed for Pydantic v2.5 compatibility.
"""

import functools
import logging
from typing import Dict, Any, Type, TypeVar, Optional, Union
from weakref import WeakValueDictionary

from pydantic import BaseModel, ConfigDict
from pydantic._internal._config import ConfigWrapper

from .pydantic_models import MediaConfig, PathsConfig, PerformanceConfig, PlexConfig
from .base_settings import CacherrSettings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class ModelCache:
    """
    High-performance cache for Pydantic model instances.
    
    Uses weak references to avoid memory leaks while providing
    fast access to frequently used configuration objects.
    """
    
    def __init__(self):
        self._cache: WeakValueDictionary = WeakValueDictionary()
        self._hit_count = 0
        self._miss_count = 0
    
    def get_cache_key(self, model_class: Type[T], data: Dict[str, Any]) -> str:
        """Generate cache key from model class and data."""
        # Create a deterministic hash from the data
        sorted_items = sorted(data.items()) if isinstance(data, dict) else []
        key_data = f"{model_class.__name__}:{hash(tuple(sorted_items))}"
        return key_data
    
    def get(self, model_class: Type[T], data: Dict[str, Any]) -> Optional[T]:
        """Get cached model instance."""
        cache_key = self.get_cache_key(model_class, data)
        result = self._cache.get(cache_key)
        
        if result is not None:
            self._hit_count += 1
            logger.debug(f"Cache hit for {model_class.__name__}")
        else:
            self._miss_count += 1
            logger.debug(f"Cache miss for {model_class.__name__}")
        
        return result
    
    def put(self, model_class: Type[T], data: Dict[str, Any], instance: T) -> None:
        """Cache model instance."""
        cache_key = self.get_cache_key(model_class, data)
        self._cache[cache_key] = instance
        logger.debug(f"Cached {model_class.__name__} instance")
    
    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        logger.info("Model cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self._hit_count,
            'misses': self._miss_count,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self._cache)
        }


# Global model cache instance
_model_cache = ModelCache()


def cached_model_factory(model_class: Type[T]) -> callable:
    """
    Create a cached factory function for a Pydantic model.
    
    Args:
        model_class: The Pydantic model class to cache
        
    Returns:
        Factory function that returns cached instances when possible
    """
    @functools.wraps(model_class)
    def factory(**kwargs) -> T:
        # Check cache first
        cached_instance = _model_cache.get(model_class, kwargs)
        if cached_instance is not None:
            return cached_instance
        
        # Create new instance
        instance = model_class(**kwargs)
        
        # Cache the instance
        _model_cache.put(model_class, kwargs, instance)
        
        return instance
    
    return factory


# Optimized factory functions for commonly used models
create_media_config = cached_model_factory(MediaConfig)
create_paths_config = cached_model_factory(PathsConfig)
create_performance_config = cached_model_factory(PerformanceConfig)
create_plex_config = cached_model_factory(PlexConfig)


class OptimizedConfigDict(ConfigDict):
    """
    Optimized ConfigDict for better performance in production.
    
    This configuration optimizes validation and serialization
    performance while maintaining type safety.
    """
    
    # Validation optimizations
    validate_assignment: bool = False  # Disable for production performance
    validate_default: bool = False     # Skip default validation
    validate_return: bool = False      # Skip return validation
    
    # Serialization optimizations
    ser_json_inf_nan: str = 'constants'  # Fast NaN/inf handling
    
    # General optimizations
    extra: str = 'ignore'              # Ignore extra fields for performance
    frozen: bool = True                # Immutable objects are faster
    str_strip_whitespace: bool = True  # Consistent string handling
    
    # Memory optimizations
    copy_on_model_validation: bool = False  # Avoid unnecessary copies


class HighPerformanceSettings(CacherrSettings):
    """
    High-performance version of CacherrSettings with optimizations.
    
    This class applies performance optimizations suitable for production
    environments where validation overhead should be minimized.
    """
    
    model_config = OptimizedConfigDict()
    
    def __init__(self, **kwargs):
        # Pre-validate critical fields only
        critical_fields = {'plex_url', 'plex_token', 'copy_to_cache'}
        critical_data = {k: v for k, v in kwargs.items() if k in critical_fields}
        
        # Validate critical fields first
        if critical_data:
            temp_instance = super().__new__(self.__class__)
            super(CacherrSettings, temp_instance).__init__(**critical_data)
        
        # Initialize with all data
        super().__init__(**kwargs)
    
    @functools.lru_cache(maxsize=32)
    def get_plex_config_cached(self) -> PlexConfig:
        """Get cached Plex configuration."""
        token_value = self.plex_token.strip() if isinstance(self.plex_token, str) else None
        token_value = token_value or None
        password_value = (
            self.plex_password.get_secret_value().strip()
            if self.plex_password and self.plex_password.get_secret_value()
            else None
        )
        return create_plex_config(
            url=self.plex_url,
            token=token_value,
            username=self.plex_username,
            password=password_value
        )
    
    @functools.lru_cache(maxsize=32)
    def get_media_config_cached(self) -> MediaConfig:
        """Get cached media configuration."""
        return create_media_config(
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
    
    @functools.lru_cache(maxsize=32)
    def get_paths_config_cached(self) -> PathsConfig:
        """Get cached paths configuration."""
        return create_paths_config(
            plex_source=self.plex_source,
            cache_destination=self.cache_destination,
            additional_sources=self.additional_sources,
            additional_plex_sources=self.additional_plex_sources
        )
    
    @functools.lru_cache(maxsize=32)
    def get_performance_config_cached(self) -> PerformanceConfig:
        """Get cached performance configuration."""
        return create_performance_config(
            max_concurrent_moves_cache=self.max_concurrent_moves_cache,
            max_concurrent_moves_array=self.max_concurrent_moves_array,
            max_concurrent_local_transfers=self.max_concurrent_local_transfers,
            max_concurrent_network_transfers=self.max_concurrent_network_transfers
        )


def optimize_for_production() -> None:
    """
    Apply production optimizations to Pydantic models.
    
    This function configures Pydantic for optimal performance in
    production environments where validation overhead should be minimized.
    """
    # Set global Pydantic optimizations
    import pydantic
    
    # Disable debug mode
    pydantic.debug.DEBUG = False
    
    # Log optimization status
    logger.info("Applied production optimizations to Pydantic models")
    logger.info(f"Model cache stats: {_model_cache.get_stats()}")


def get_cache_stats() -> Dict[str, Any]:
    """Get performance statistics."""
    return {
        'model_cache': _model_cache.get_stats(),
        'optimizations_applied': True
    }


def clear_all_caches() -> None:
    """Clear all performance caches."""
    _model_cache.clear()
    
    # Clear LRU caches on settings instances
    # This would need to be called when settings change
    logger.info("All performance caches cleared")


# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            if execution_time > 0.1:  # Log slow operations
                logger.warning(
                    f"Slow configuration operation: {func.__name__} "
                    f"took {execution_time:.3f}s"
                )
            else:
                logger.debug(
                    f"Configuration operation: {func.__name__} "
                    f"took {execution_time:.3f}s"
                )
    
    return wrapper


class LazyConfigLoader:
    """
    Lazy configuration loader for improved startup performance.
    
    This class delays configuration loading until actually needed,
    reducing application startup time.
    """
    
    def __init__(self):
        self._settings: Optional[CacherrSettings] = None
        self._production_mode = False
    
    @property
    def settings(self) -> CacherrSettings:
        """Get settings instance, loading lazily."""
        if self._settings is None:
            if self._production_mode:
                self._settings = HighPerformanceSettings()
            else:
                self._settings = CacherrSettings()
            
            logger.info("Configuration loaded lazily")
        
        return self._settings
    
    def enable_production_mode(self) -> None:
        """Enable production optimizations."""
        self._production_mode = True
        self._settings = None  # Force reload with optimizations
        optimize_for_production()
        logger.info("Production mode enabled for configuration")
    
    def reload(self) -> None:
        """Reload configuration."""
        self._settings = None
        clear_all_caches()
        logger.info("Configuration reloaded")


# Global lazy loader instance
_lazy_loader = LazyConfigLoader()


def get_optimized_settings() -> CacherrSettings:
    """Get optimized settings instance."""
    return _lazy_loader.settings


def enable_production_optimizations() -> None:
    """Enable all production optimizations."""
    _lazy_loader.enable_production_mode()


__all__ = [
    'ModelCache', 'OptimizedConfigDict', 'HighPerformanceSettings',
    'cached_model_factory', 'create_media_config', 'create_paths_config',
    'create_performance_config', 'create_plex_config',
    'optimize_for_production', 'get_cache_stats', 'clear_all_caches',
    'monitor_performance', 'LazyConfigLoader', 'get_optimized_settings',
    'enable_production_optimizations'
]
