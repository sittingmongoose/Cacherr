import os
import json
import logging
import shutil
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Set, Generator, Tuple, Optional, Dict
from dataclasses import dataclass

from plexapi.server import PlexServer
from plexapi.video import Episode, Movie
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import NotFound, BadRequest

try:
    from ..config.settings import Config
    from .notifications import NotificationManager
    from .file_operations import FileOperations
    from .plex_operations import PlexOperations
    from .plex_watcher import PlexWatcher
    from .trakt_watcher import TraktWatcher
except ImportError:
    # Fallback for testing
    from config.settings import Config
    from core.notifications import NotificationManager
    from core.file_operations import FileOperations
    from core.plex_operations import PlexOperations
    from core.plex_watcher import PlexWatcher
    from core.trakt_watcher import TraktWatcher

@dataclass
class CacheStats:
    """Statistics for cache operations"""
    files_moved_to_cache: int = 0
    files_moved_to_array: int = 0
    total_size_moved: int = 0
    start_time: datetime = None
    end_time: datetime = None
    
    @property
    def execution_time(self) -> str:
        """Calculate and format execution time"""
        if not self.start_time or not self.end_time:
            return "Unknown"
        
        duration = self.end_time - self.start_time
        total_seconds = int(duration.total_seconds())
        
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
        
        return ", ".join(parts) if parts else "0 seconds"

class PlexCacheUltraEngine:
    """Main engine for PlexCacheUltra operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.stats = CacheStats()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.notification_manager = NotificationManager(config)
        self.file_operations = FileOperations(config)
        self.plex_operations = PlexOperations(config)
        
        # Initialize watchers if enabled
        self.plex_watcher = None
        self.trakt_watcher = None
        
        if config.real_time_watch.enabled:
            self.plex_watcher = PlexWatcher(config, self.plex_operations, self.file_operations)
            self.logger.info("Real-time Plex watcher initialized")
        
        if config.trakt.enabled:
            self.trakt_watcher = TraktWatcher(config, self)
            self.logger.info("Trakt.tv watcher initialized")
        
        # Cache files
        self.cache_dir = Path("/app/cache")
        self.watchlist_cache_file = self.cache_dir / "watchlist_cache.json"
        self.watched_cache_file = self.cache_dir / "watched_cache.json"
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize Plex connection
        self.plex = None
        self._connect_to_plex()
        # Provide Plex connection to operations helper
        try:
            self.plex_operations.set_plex_connection(self.plex)
        except Exception:
            pass
        
        # Media collections
        self.media_to_cache: List[str] = []
        self.media_to_array: List[str] = []
        self.files_to_skip: Set[str] = []
        
        # Test mode results
        self.test_results: Dict = {}
        
    def _connect_to_plex(self):
        """Establish connection to Plex server"""
        if not self.config.plex.url:
            raise ValueError("PLEX_URL is not configured. Please configure it via the web interface.")
        
        if not self.config.plex.token:
            raise ValueError("PLEX_TOKEN is not configured. Please configure it via the web interface.")
        
        try:
            self.plex = PlexServer(self.config.plex.url, self.config.plex.token)
            self.logger.info(f"Connected to Plex server: {self.config.plex.url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Plex server: {e}")
            raise
    
    def run(self, test_mode: bool = False) -> bool:
        """Main execution method"""
        self.stats.start_time = datetime.now()
        
        if test_mode:
            self.logger.info("Starting PlexCacheUltra execution in TEST MODE")
        else:
            self.logger.info("Starting PlexCacheUltra execution")
        
        try:
            # Check for active sessions
            if self._should_exit_due_to_active_sessions():
                return False
            
            # Fetch media for caching
            self._fetch_media_for_caching()
            
            # Fetch watched media for array movement
            if self.config.media.watched_move:
                self._fetch_watched_media()
            
            if test_mode:
                # Run in test mode - analyze files without moving
                self._execute_test_mode()
            else:
                # Execute file movements
                self._execute_cache_operations()
            
            # Generate summary
            self._generate_summary(test_mode)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during execution: {e}")
            self.notification_manager.send_error_notification(f"PlexCacheUltra execution failed: {e}")
            return False
        finally:
            self.stats.end_time = datetime.now()
            self.logger.info(f"Execution completed in {self.stats.execution_time}")
    
    def _should_exit_due_to_active_sessions(self) -> bool:
        """Check if we should exit due to active Plex sessions"""
        if not self.config.media.exit_if_active_session:
            return False
        
        try:
            sessions = self.plex.sessions()
            if sessions:
                self.logger.warning("Active Plex session detected, exiting as configured")
                return True
        except Exception as e:
            self.logger.warning(f"Could not check for active sessions: {e}")
        
        return False
    
    def _fetch_media_for_caching(self):
        """Fetch media that should be moved to cache"""
        self.logger.info("Fetching media for caching...")
        
        # Fetch onDeck media
        ondeck_media = self.plex_operations.fetch_ondeck_media()
        self.media_to_cache.extend(ondeck_media)
        
        # Fetch watchlist media if enabled
        if self.config.media.watchlist_toggle:
            watchlist_media = self.plex_operations.fetch_watchlist_media()
            self.media_to_cache.extend(watchlist_media)
        
        # Process file paths
        self.media_to_cache = self.file_operations.process_file_paths(self.media_to_cache)
        
        # Scan additional sources for matching media
        additional_files = self.file_operations.scan_additional_sources(self.media_to_cache)
        if additional_files:
            self.media_to_cache.extend(additional_files)
            self.logger.info(f"Added {len(additional_files)} files from additional sources")
        
        # Add subtitles
        subtitle_files = self.file_operations.find_subtitle_files(self.media_to_cache)
        self.media_to_cache.extend(subtitle_files)
        
        self.logger.info(f"Found {len(self.media_to_cache)} files to cache")
    
    def _fetch_watched_media(self):
        """Fetch watched media that should be moved to array"""
        self.logger.info("Fetching watched media...")
        
        watched_media = self.plex_operations.fetch_watched_media()
        self.media_to_array = self.file_operations.process_file_paths(watched_media)
        
        # Add subtitles
        subtitle_files = self.file_operations.find_subtitle_files(self.media_to_array)
        self.media_to_array.extend(subtitle_files)
        
        self.logger.info(f"Found {len(self.media_to_array)} watched files to move to array")
    
    def _execute_test_mode(self):
        """Execute test mode - analyze files without moving them"""
        self.logger.info("Executing test mode analysis...")
        
        # Analyze files for cache operation
        if self.media_to_cache:
            cache_analysis = self.file_operations.analyze_files_for_test_mode(
                self.media_to_cache, "cache"
            )
            self.test_results['cache_operation'] = cache_analysis
            self.logger.info(f"Test mode: {cache_analysis['file_count']} files would be moved to cache")
            self.logger.info(f"Test mode: Total size would be {cache_analysis['total_size_readable']}")
        
        # Analyze files for array operation
        if self.media_to_array and self.config.media.watched_move:
            array_analysis = self.file_operations.analyze_files_for_test_mode(
                self.media_to_array, "array"
            )
            self.test_results['array_operation'] = array_analysis
            self.logger.info(f"Test mode: {array_analysis['file_count']} files would be moved to array")
            self.logger.info(f"Test mode: Total size would be {array_analysis['total_size_readable']}")
    
    def _execute_cache_operations(self):
        """Execute the actual file movement operations"""
        # Move files to cache
        if self.media_to_cache:
            self._move_files_to_cache()
        
        # Move watched files to array
        if self.media_to_array and self.config.media.watched_move:
            self._move_files_to_array()
    
    def _move_files_to_cache(self):
        """Move files from array to cache"""
        self.logger.info("Moving files to cache...")
        
        # Filter files that should be moved to cache
        files_to_cache = self.file_operations.filter_files_for_cache(self.media_to_cache)
        
        if not files_to_cache:
            self.logger.info("No files need to be moved to cache")
            return
        
        # Check available space in cache destination
        cache_dest = self.config.paths.cache_destination or '/cache'  # Hardcoded Docker volume mapping
        if not self.file_operations.check_available_space(files_to_cache, cache_dest):
            self.logger.error("Insufficient space in cache destination directory")
            return
        
        # Execute moves, copies, or move+symlink
        moved_count, total_size = self.file_operations.move_files(
            files_to_cache,
            '/mediasource',  # Hardcoded Docker volume mapping
            cache_dest,
            self.config.performance.max_concurrent_moves_cache,
            dry_run=self.config.test_mode.dry_run,
            copy_mode=self.config.media.copy_to_cache,
            move_with_symlinks=self.config.media.move_with_symlinks
        )
        
        self.stats.files_moved_to_cache = moved_count
        self.stats.total_size_moved += total_size
        
        if self.config.media.move_with_symlinks:
            operation = "move+symlink"
        elif self.config.media.copy_to_cache:
            operation = "copy"
        else:
            operation = "move"
        if self.config.test_mode.dry_run:
            self.logger.info(f"DRY RUN: Would {operation} {moved_count} files to cache ({total_size} bytes)")
        else:
            self.logger.info(f"{operation.capitalize()}d {moved_count} files to cache ({total_size} bytes)")
    
    def _move_files_to_array(self):
        """Move watched files from cache to array or delete them from cache"""
        self.logger.info("Moving watched files to array...")
        
        # Filter files that should be moved to array
        files_to_array = self.file_operations.filter_files_for_array(self.media_to_array)
        
        if not files_to_array:
            self.logger.info("No files need to be moved to array")
            return
        
        # Check available space
        if not self.file_operations.check_available_space(files_to_array, '/mediasource'):  # Hardcoded Docker volume mapping
            self.logger.error("Insufficient space in array directory")
            return
        
        # Execute moves from cache to array or delete from cache
        cache_dest = self.config.paths.cache_destination or '/cache'  # Hardcoded Docker volume mapping
        if self.config.media.copy_to_cache and self.config.media.delete_from_cache_when_done:
            # Delete from cache instead of moving back
            moved_count, total_size = self.file_operations.delete_files(
                files_to_array,
                self.config.performance.max_concurrent_moves_array
            )
            operation = "delete"
        else:
            # Move back to array
            moved_count, total_size = self.file_operations.move_files(
                files_to_array,
                cache_dest,
                '/mediasource',  # Hardcoded Docker volume mapping
                self.config.performance.max_concurrent_moves_array,
                dry_run=self.config.test_mode.dry_run
            )
            operation = "move"
        
        self.stats.files_moved_to_array = moved_count
        self.stats.total_size_moved += total_size
        
        if self.config.test_mode.dry_run:
            self.logger.info(f"DRY RUN: Would {operation} {moved_count} files from cache ({total_size} bytes)")
        else:
            self.logger.info(f"{operation.capitalize()}d {moved_count} files from cache ({total_size} bytes)")
    
    def _generate_summary(self, test_mode: bool = False):
        """Generate and send execution summary"""
        if test_mode:
            summary = (
                f"PlexCacheUltra TEST MODE execution completed in {self.stats.execution_time}. "
                f"Files analyzed for cache: {len(self.media_to_cache)}, "
                f"Files analyzed for array: {len(self.media_to_array)}"
            )
        else:
            summary = (
                f"PlexCacheUltra execution completed in {self.stats.execution_time}. "
                f"Files moved to cache: {self.stats.files_moved_to_cache}, "
                f"Files moved to array: {self.stats.files_moved_to_array}, "
                f"Total size moved: {self.stats.total_size_moved} bytes"
            )
        
        self.logger.info(summary)
        if not test_mode:
            self.notification_manager.send_summary_notification(summary)
    
    def get_status(self) -> dict:
        """Get current status information"""
        status_data = {
            'status': 'running' if self.stats.start_time and not self.stats.end_time else 'idle',
            'last_execution': {
                'start_time': self.stats.start_time.isoformat() if self.stats.start_time else None,
                'end_time': self.stats.end_time.isoformat() if self.stats.end_time else None,
                'execution_time': self.stats.execution_time,
                'files_moved_to_cache': self.stats.files_moved_to_cache,
                'files_moved_to_array': self.stats.files_moved_to_array,
                'total_size_moved': self.stats.total_size_moved
            },
            'pending_operations': {
                'files_to_cache': len(self.media_to_cache),
                'files_to_array': len(self.media_to_array)
            },
            'real_time_watcher': {
                'enabled': self.config.real_time_watch.enabled,
                'active': self.is_real_time_watching(),
                'stats': self.get_watcher_stats()
            },
            'configuration': self.config.to_dict()
        }
        
        # Add test mode results if available
        if self.test_results:
            status_data['test_results'] = self.test_results
        
        return status_data
    
    def get_test_results(self) -> dict:
        """Get test mode results"""
        return self.test_results if self.test_results else {}
    
    def start_real_time_watching(self) -> bool:
        """Start real-time Plex watching"""
        if not self.config.real_time_watch.enabled:
            self.logger.warning("Real-time watching is disabled in configuration")
            return False
        
        try:
            success = self.plex_watcher.start_watching()
            if success:
                self.logger.info("Real-time Plex watching started successfully")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start real-time watching: {e}")
            return False
    
    def stop_real_time_watching(self) -> bool:
        """Stop real-time Plex watching"""
        try:
            success = self.plex_watcher.stop_watching()
            if success:
                self.logger.info("Real-time Plex watching stopped successfully")
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to stop real-time watching: {e}")
            return False
    
    def is_real_time_watching(self) -> bool:
        """Check if real-time watching is active"""
        return self.plex_watcher.is_watching()
    
    def get_watcher_stats(self) -> Dict:
        """Get real-time watcher statistics"""
        stats = {}
        
        if self.plex_watcher:
            stats['plex_watcher'] = self.plex_watcher.get_stats()
        
        if self.trakt_watcher:
            stats['trakt_watcher'] = self.trakt_watcher.get_stats()
        
        return stats
    
    def get_cache_removal_schedule(self) -> Dict:
        """Get the current cache removal schedule from the watcher"""
        if not self.plex_watcher:
            return {}
        return self.plex_watcher.get_cache_removal_schedule()
    
    def get_user_activity_status(self) -> Dict:
        """Get the current user activity status from the watcher"""
        if not self.plex_watcher:
            return {}
        return self.plex_watcher.get_user_activity_status()
    
    def get_watch_history(self) -> dict:
        """Get the history of watched media from real-time watcher"""
        return self.plex_watcher.get_watch_history()
    
    def clear_watch_history(self):
        """Clear the watch history from real-time watcher"""
        if self.plex_watcher:
            self.plex_watcher.clear_watch_history()
    
    def start_all_watchers(self):
        """Start all enabled watchers"""
        if self.plex_watcher:
            self.plex_watcher.start_watching()
        
        if self.trakt_watcher:
            self.trakt_watcher.start_watching()
        
        self.logger.info("Started all enabled watchers")
    
    def stop_all_watchers(self):
        """Stop all running watchers"""
        if self.plex_watcher:
            self.plex_watcher.stop_watching()
        
        if self.trakt_watcher:
            self.trakt_watcher.stop_watching()
        
        self.logger.info("Stopped all watchers")
    
    def get_trakt_trending_movies(self) -> List[Dict]:
        """Get current trending movies from Trakt watcher"""
        if self.trakt_watcher:
            return self.trakt_watcher.get_trending_movies()
        return []
    
    def get_trakt_stats(self) -> Dict:
        """Get Trakt watcher statistics"""
        if self.trakt_watcher:
            return self.trakt_watcher.get_stats()
        return {}
    
    def start_plex_watcher(self):
        """Start the Plex watcher"""
        if self.plex_watcher:
            self.plex_watcher.start_watching()
            return True
        return False
    
    def stop_plex_watcher(self):
        """Stop the Plex watcher"""
        if self.plex_watcher:
            self.plex_watcher.stop_watching()
            return True
        return False
    
    def start_trakt_watcher(self):
        """Start the Trakt watcher"""
        if self.trakt_watcher:
            self.trakt_watcher.start_watching()
            return True
        return False
    
    def stop_trakt_watcher(self):
        """Stop the Trakt watcher"""
        if self.trakt_watcher:
            self.trakt_watcher.stop_watching()
            return True
        return False
    
    def clear_plex_watch_history(self):
        """Clear Plex watcher history"""
        if self.plex_watcher:
            self.plex_watcher.clear_watch_history()
            return True
        return False
    
    def clear_trakt_history(self):
        """Clear Trakt watcher history"""
        if self.trakt_watcher:
            self.trakt_watcher.clear_history()
            return True
        return False
    
    def scan_and_cache_media(self, test_mode: bool = None) -> Dict:
        """Scan source paths and cache media files"""
        if test_mode is None:
            test_mode = self.config.cache.test_mode
        
        self.logger.info(f"Starting media scan and cache operation (test_mode: {test_mode})")
        
        # Implementation would go here
        # For now, return placeholder stats
        return {
            'status': 'completed',
            'test_mode': test_mode,
            'files_processed': 0,
            'files_cached': 0,
            'total_size_gb': 0.0
        }
    
    def get_cache_status(self) -> Dict:
        """Get current cache status and statistics"""
        return {
            'cache_directory': str(self.cache_dir),
            'source_paths': [str(p) for p in self.config.cache.source_paths],
            'stats': self.stats,
            'watchers': self.get_watcher_stats()
        }
