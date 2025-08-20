# Cacherr - Docker-optimized Plex media caching system
__version__ = "2.0.0"

# Make core modules accessible at package level
from .core.plex_cache_engine import CacherrEngine
from .config.settings import Config

__all__ = ['CacherrEngine', 'Config']
