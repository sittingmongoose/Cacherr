# Core functionality package for Cacherr

# Import main classes for easier access
from .plex_cache_engine import CacherrEngine
from .plex_operations import PlexOperations
from .plex_watcher import PlexWatcher
from .trakt_watcher import TraktWatcher
from .file_operations import FileOperations
from .notifications import NotificationManager

__all__ = [
    'CacherrEngine',
    'PlexOperations', 
    'PlexWatcher',
    'TraktWatcher',
    'FileOperations',
    'NotificationManager'
]
