"""
Cache Manager - Central coordinator for Cacherr.

Integrates all cache management components:
- Real-time Plex session monitoring
- OnDeck/Watchlist/Trakt caching
- Cache limits and smart eviction
- Retention policy enforcement
- Self-healing reconciliation

This is the main entry point for cache operations.
"""

import os
import time
import shutil
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .trackers import (
    CacheTimestampTracker,
    WatchlistTracker,
    OnDeckTracker,
    CachePriorityScorer,
    EpisodeInfo,
)
from .file_operations import (
    AtomicFileOperations,
    SubtitleFinder,
    OperationResult,
    format_bytes,
)
from .plex_client import PlexClient, OnDeckItem, WatchlistItem, ActiveSession


logger = logging.getLogger(__name__)


class CacheHealth(str, Enum):
    """Cache health status levels."""
    HEALTHY = "healthy"      # < 75% of limit
    MODERATE = "moderate"    # 75-89% of limit
    WARNING = "warning"      # 90-95% of limit
    CRITICAL = "critical"    # > 95% of limit
    UNLIMITED = "unlimited"  # No limit set


@dataclass
class CacheStats:
    """Current cache statistics."""
    total_size_bytes: int = 0
    limit_bytes: int = 0
    used_percent: float = 0.0
    file_count: int = 0
    health: CacheHealth = CacheHealth.UNLIMITED
    
    # Breakdown by source
    ondeck_count: int = 0
    ondeck_bytes: int = 0
    watchlist_count: int = 0
    watchlist_bytes: int = 0
    trakt_count: int = 0
    trakt_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_size_bytes': self.total_size_bytes,
            'total_size_human': format_bytes(self.total_size_bytes),
            'limit_bytes': self.limit_bytes,
            'limit_human': format_bytes(self.limit_bytes) if self.limit_bytes > 0 else 'Unlimited',
            'used_percent': round(self.used_percent, 1),
            'file_count': self.file_count,
            'health': self.health.value,
            'breakdown': {
                'ondeck': {'count': self.ondeck_count, 'bytes': self.ondeck_bytes},
                'watchlist': {'count': self.watchlist_count, 'bytes': self.watchlist_bytes},
                'trakt': {'count': self.trakt_count, 'bytes': self.trakt_bytes},
            }
        }


@dataclass
class EvictionResult:
    """Result of an eviction operation."""
    needed: bool = False
    performed: bool = False
    files_evicted: int = 0
    bytes_freed: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'needed': self.needed,
            'performed': self.performed,
            'files_evicted': self.files_evicted,
            'bytes_freed': self.bytes_freed,
            'bytes_freed_human': format_bytes(self.bytes_freed),
            'errors': self.errors,
        }


@dataclass
class ReconciliationResult:
    """Result of cache reconciliation."""
    files_checked: int = 0
    orphaned_found: int = 0
    untracked_found: int = 0
    stale_removed: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'files_checked': self.files_checked,
            'orphaned_found': self.orphaned_found,
            'untracked_found': self.untracked_found,
            'stale_removed': self.stale_removed,
            'errors': self.errors,
        }


class CacheManager:
    """
    Central cache management coordinator.
    
    Handles:
    - Proactive caching (OnDeck, Watchlist, Trakt)
    - Real-time session monitoring
    - Cache limit enforcement
    - Retention policies
    - Self-healing reconciliation
    """
    
    def __init__(self,
                 plex_client: PlexClient,
                 file_ops: AtomicFileOperations,
                 config: Any,
                 config_dir: str = "/config"):
        """
        Initialize cache manager.
        
        Args:
            plex_client: Configured PlexClient instance
            file_ops: AtomicFileOperations instance
            config: CacherrSettings configuration
            config_dir: Directory for tracker files
        """
        self.plex = plex_client
        self.file_ops = file_ops
        self.config = config
        self.config_dir = Path(config_dir)
        
        # Initialize trackers
        self.timestamp_tracker = CacheTimestampTracker(
            str(self.config_dir / "cache_timestamps.json")
        )
        self.watchlist_tracker = WatchlistTracker(
            str(self.config_dir / "watchlist_tracker.json")
        )
        self.ondeck_tracker = OnDeckTracker(
            str(self.config_dir / "ondeck_tracker.json")
        )
        
        # State
        self._running = False
        self._lock = threading.RLock()
        self._active_sessions: Dict[str, ActiveSession] = {}
        self._session_monitor_thread: Optional[threading.Thread] = None
        
        # Parse cache limit
        self._limit_bytes = self._parse_limit(config.cache_limits.cache_limit)
        
        logger.info("Cache manager initialized")
    
    def _parse_limit(self, limit_str: str) -> int:
        """Parse cache limit string to bytes."""
        if not limit_str or limit_str.strip() in ('', '0'):
            return 0
        
        limit_str = limit_str.strip().upper()
        
        try:
            if limit_str.endswith('%'):
                # Percentage of cache drive
                percent = int(limit_str[:-1])
                cache_path = self.config.paths.cache_destination
                if os.path.exists(cache_path):
                    total = shutil.disk_usage(cache_path).total
                    return int(total * percent / 100)
                return 0
            
            # Size with units
            multipliers = {
                'TB': 1024**4,
                'GB': 1024**3,
                'MB': 1024**2,
                'KB': 1024,
            }
            
            for suffix, mult in multipliers.items():
                if limit_str.endswith(suffix):
                    size = float(limit_str[:-len(suffix)])
                    return int(size * mult)
            
            # No unit = GB
            return int(float(limit_str) * 1024**3)
            
        except (ValueError, TypeError):
            logger.warning(f"Invalid cache_limit: {limit_str}")
            return 0
    
    def start(self) -> bool:
        """Start cache manager background services."""
        if self._running:
            return True
        
        try:
            # Connect to Plex
            if not self.plex.connect():
                logger.error("Failed to connect to Plex")
                return False
            
            # Run initial reconciliation
            if self.config.reconciliation.auto_on_startup:
                logger.info("Running startup reconciliation...")
                self.reconcile()
            
            # Start session monitor
            if self.config.realtime.enabled:
                self._running = True
                self._session_monitor_thread = threading.Thread(
                    target=self._session_monitor_loop,
                    name="cacherr-session-monitor",
                    daemon=True
                )
                self._session_monitor_thread.start()
                logger.info("Real-time session monitor started")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start cache manager: {e}")
            return False
    
    def stop(self) -> None:
        """Stop cache manager background services."""
        self._running = False
        
        if self._session_monitor_thread and self._session_monitor_thread.is_alive():
            self._session_monitor_thread.join(timeout=10)
        
        logger.info("Cache manager stopped")
    
    def run_cache_cycle(self) -> Dict[str, Any]:
        """
        Run a complete cache cycle:
        1. Get OnDeck items
        2. Get Watchlist items
        3. Get Trakt trending (if enabled)
        4. Cache new items
        5. Check retention and move-back
        6. Enforce cache limits
        
        Returns:
            Summary of operations performed
        """
        start_time = time.time()
        summary = {
            'ondeck_items': 0,
            'watchlist_items': 0,
            'trakt_items': 0,
            'files_cached': 0,
            'bytes_cached': 0,
            'files_restored': 0,
            'bytes_restored': 0,
            'eviction': None,
            'errors': [],
        }
        
        try:
            # Check for active sessions
            if self.config.exit_if_active_session and self.plex.has_active_sessions():
                logger.info("Active Plex sessions detected, skipping cache cycle")
                summary['skipped'] = 'active_sessions'
                return summary
            
            # Get active file paths (never touch these)
            active_files = self.plex.get_active_file_paths()
            
            # Clear OnDeck tracker for fresh run
            self.ondeck_tracker.clear_for_run()
            
            # Get OnDeck items
            ondeck_items = self.plex.get_ondeck(
                number_episodes=self.config.plex.number_episodes,
                days_to_monitor=self.config.plex.days_to_monitor,
                skip_users=self.config.plex.skip_ondeck_users,
            )
            summary['ondeck_items'] = len(ondeck_items)
            
            # Get Watchlist items
            watchlist_items = []
            if self.config.watchlist.enabled:
                watchlist_items = self.plex.get_watchlist(
                    episodes_per_show=self.config.watchlist.episodes_per_show,
                    skip_users=self.config.plex.skip_watchlist_users,
                )
                summary['watchlist_items'] = len(watchlist_items)
            
            # TODO: Get Trakt trending items
            
            # Collect all files to cache
            files_to_cache = self._collect_files_to_cache(
                ondeck_items, watchlist_items, active_files
            )
            
            # Cache files
            if files_to_cache:
                results = self._cache_files(files_to_cache)
                summary['files_cached'] = sum(1 for r in results if r.success)
                summary['bytes_cached'] = sum(r.bytes_transferred for r in results if r.success)
            
            # Check retention and move files back
            restore_results = self._check_retention_and_restore(active_files)
            summary['files_restored'] = sum(1 for r in restore_results if r.success)
            summary['bytes_restored'] = sum(r.bytes_transferred for r in restore_results if r.success)
            
            # Enforce cache limits
            if self.config.cache_limits.eviction_enabled:
                eviction = self._enforce_cache_limits(active_files)
                summary['eviction'] = eviction.to_dict()
            
        except Exception as e:
            logger.error(f"Cache cycle error: {e}")
            summary['errors'].append(str(e))
        
        summary['duration_seconds'] = round(time.time() - start_time, 2)
        return summary
    
    def _collect_files_to_cache(self,
                                 ondeck_items: List[OnDeckItem],
                                 watchlist_items: List[WatchlistItem],
                                 active_files: Set[str]) -> List[Tuple[str, str]]:
        """
        Collect files that need to be cached.
        
        Returns list of (file_path, source) tuples.
        """
        files_to_cache = []
        seen_paths = set()
        
        # OnDeck items
        for item in ondeck_items:
            if item.file_path in seen_paths:
                continue
            if item.file_path in active_files:
                continue
            if self._is_already_cached(item.file_path):
                continue
            
            files_to_cache.append((item.file_path, 'ondeck'))
            seen_paths.add(item.file_path)
            
            # Update tracker
            episode_info = None
            if item.episode_info:
                episode_info = EpisodeInfo(
                    show=item.episode_info.get('show', ''),
                    season=item.episode_info.get('season', 0),
                    episode=item.episode_info.get('episode', 0),
                    is_current_ondeck=item.is_current_ondeck,
                )
            self.ondeck_tracker.update_entry(
                item.file_path,
                item.username,
                episode_info=episode_info,
                is_current_ondeck=item.is_current_ondeck,
            )
        
        # Watchlist items (lower priority, added after ondeck)
        for item in watchlist_items:
            if item.file_path in seen_paths:
                continue
            if item.file_path in active_files:
                continue
            if self._is_already_cached(item.file_path):
                continue
            
            files_to_cache.append((item.file_path, 'watchlist'))
            seen_paths.add(item.file_path)
            
            # Update tracker
            self.watchlist_tracker.update_entry(
                item.file_path,
                item.username,
                watchlisted_at=item.added_at,
            )
        
        # Add subtitles
        all_files = []
        for path, source in files_to_cache:
            all_files.append((path, source))
            for subtitle in SubtitleFinder.find_subtitles(path):
                if subtitle not in seen_paths:
                    all_files.append((subtitle, source))
                    seen_paths.add(subtitle)
        
        return all_files
    
    def _cache_files(self, files: List[Tuple[str, str]]) -> List[OperationResult]:
        """Cache a list of files."""
        results = []
        
        for file_path, source in files:
            result = self.file_ops.copy_to_cache_atomic(file_path)
            results.append(result)
            
            if result.success:
                # Record timestamp
                file_size = 0
                try:
                    file_size = Path(result.dest_path).stat().st_size
                except:
                    pass
                
                self.timestamp_tracker.record(
                    file_path,
                    source=source,
                    file_size=file_size
                )
        
        return results
    
    def _check_retention_and_restore(self, active_files: Set[str]) -> List[OperationResult]:
        """Check retention policies and restore expired files."""
        results = []
        
        # Get all tracked files
        entries = self.timestamp_tracker.get_all_entries()
        
        for file_path, entry in entries.items():
            # Skip active files
            if file_path in active_files:
                continue
            
            # Check if file should be restored
            should_restore, reason = self._should_restore(file_path, entry)
            
            if should_restore:
                logger.info(f"Restoring: {Path(file_path).name} ({reason})")
                result = self.file_ops.restore_to_array(file_path)
                results.append(result)
                
                if result.success:
                    self.timestamp_tracker.remove_entry(file_path)
        
        return results
    
    def _should_restore(self, file_path: str, entry: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if a file should be restored to array.
        
        Returns (should_restore, reason).
        """
        # Check minimum retention
        min_hours = self.config.retention.min_retention_hours
        if self.timestamp_tracker.is_within_retention(file_path, min_hours):
            return False, "within_min_retention"
        
        source = entry.get('source', 'unknown')
        
        # Check if still on OnDeck
        if self.ondeck_tracker.get_entry(file_path):
            if self.config.retention.ondeck_protected:
                return False, "ondeck_protected"
        
        # Check if still on watchlist
        if self.watchlist_tracker.get_entry(file_path):
            days = self.watchlist_tracker.get_days_on_watchlist(file_path)
            retention_days = self.config.retention.watchlist_retention_days
            if retention_days <= 0 or days < retention_days:
                return False, "on_watchlist"
        
        # Check watched status (TODO: implement watched tracking)
        
        # Check maximum cache time
        max_hours = self.config.retention.max_cache_hours
        if max_hours > 0:
            age_hours = self.timestamp_tracker.get_age_hours(file_path)
            if age_hours >= max_hours:
                return True, "max_cache_time"
        
        # If not on any list and past min retention, restore
        if not self.ondeck_tracker.get_entry(file_path) and \
           not self.watchlist_tracker.get_entry(file_path):
            return True, "no_longer_needed"
        
        return False, "keep"
    
    def _enforce_cache_limits(self, active_files: Set[str]) -> EvictionResult:
        """Enforce cache size limits through eviction."""
        result = EvictionResult()
        
        if self._limit_bytes <= 0:
            return result  # No limit
        
        # Get current cache size
        stats = self.get_cache_stats()
        
        # Check if eviction needed
        threshold_bytes = self._limit_bytes * self.config.cache_limits.eviction_threshold_percent / 100
        if stats.total_size_bytes < threshold_bytes:
            return result  # Under threshold
        
        result.needed = True
        
        # Calculate how much to free
        target_bytes = self._limit_bytes * self.config.cache_limits.eviction_target_percent / 100
        bytes_to_free = stats.total_size_bytes - target_bytes
        
        logger.info(f"Cache eviction needed: {format_bytes(bytes_to_free)} to free")
        
        # Get eviction candidates
        entries = self.timestamp_tracker.get_all_entries()
        candidates = CachePriorityScorer.get_eviction_candidates(
            entries,
            target_bytes=int(bytes_to_free),
            min_priority=self.config.cache_limits.eviction_min_priority,
            actively_playing_files=active_files,
            protected_hours=self.config.cache_limits.eviction_protected_hours,
        )
        
        if not candidates:
            logger.warning("No eviction candidates found")
            return result
        
        # Evict files
        for path, priority, size in candidates:
            logger.info(f"Evicting (priority {priority}): {Path(path).name}")
            op_result = self.file_ops.restore_to_array(path)
            
            if op_result.success:
                result.files_evicted += 1
                result.bytes_freed += size
                self.timestamp_tracker.remove_entry(path)
            else:
                result.errors.append(f"Failed to evict {path}: {op_result.error}")
        
        result.performed = True
        logger.info(f"Eviction complete: {result.files_evicted} files, {format_bytes(result.bytes_freed)} freed")
        
        return result
    
    def get_cache_stats(self) -> CacheStats:
        """Get current cache statistics."""
        stats = CacheStats()
        stats.limit_bytes = self._limit_bytes
        
        cache_path = Path(self.config.paths.cache_destination)
        if not cache_path.exists():
            return stats
        
        # Calculate total size
        total_size = 0
        file_count = 0
        
        for entry in self.timestamp_tracker.get_all_entries().values():
            size = entry.get('file_size_bytes', 0)
            total_size += size
            file_count += 1
            
            source = entry.get('source', 'unknown')
            if source == 'ondeck':
                stats.ondeck_count += 1
                stats.ondeck_bytes += size
            elif source == 'watchlist':
                stats.watchlist_count += 1
                stats.watchlist_bytes += size
            elif source == 'trakt':
                stats.trakt_count += 1
                stats.trakt_bytes += size
        
        stats.total_size_bytes = total_size
        stats.file_count = file_count
        
        # Calculate health
        if stats.limit_bytes > 0:
            stats.used_percent = (stats.total_size_bytes / stats.limit_bytes) * 100
            
            if stats.used_percent >= 95:
                stats.health = CacheHealth.CRITICAL
            elif stats.used_percent >= 90:
                stats.health = CacheHealth.WARNING
            elif stats.used_percent >= 75:
                stats.health = CacheHealth.MODERATE
            else:
                stats.health = CacheHealth.HEALTHY
        
        return stats
    
    def reconcile(self) -> ReconciliationResult:
        """
        Run cache reconciliation to fix tracking inconsistencies.
        
        Checks:
        - Files in tracker but not on disk (orphaned entries)
        - Files on cache but not tracked (untracked files)
        - Stale entries
        """
        result = ReconciliationResult()
        
        try:
            # Check for orphaned entries
            entries = self.timestamp_tracker.get_all_entries()
            result.files_checked = len(entries)
            
            for path in list(entries.keys()):
                if not os.path.exists(path) and not os.path.islink(path):
                    result.orphaned_found += 1
                    logger.warning(f"Orphaned entry: {path}")
                    self.timestamp_tracker.remove_entry(path)
            
            # Cleanup stale entries
            result.stale_removed = self.timestamp_tracker.cleanup_missing_files()
            result.stale_removed += self.watchlist_tracker.cleanup_stale()
            result.stale_removed += self.ondeck_tracker.cleanup_stale()
            
            logger.info(
                f"Reconciliation complete: {result.files_checked} checked, "
                f"{result.orphaned_found} orphaned, {result.stale_removed} stale removed"
            )
            
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")
            result.errors.append(str(e))
        
        return result
    
    def _is_already_cached(self, file_path: str) -> bool:
        """Check if a file is already cached."""
        path = Path(file_path)
        
        # Check if symlink pointing to cache
        if path.is_symlink():
            target = os.path.realpath(file_path)
            cache_path = str(Path(self.config.paths.cache_destination).resolve())
            if target.startswith(cache_path):
                return True
        
        # Check tracker
        if self.timestamp_tracker.get_entry(file_path):
            return True
        
        return False
    
    def _session_monitor_loop(self) -> None:
        """Background loop for monitoring Plex sessions."""
        logger.debug("Session monitor loop started")
        
        while self._running:
            try:
                self._check_sessions()
            except Exception as e:
                logger.error(f"Session monitor error: {e}")
            
            # Sleep in small increments for responsive shutdown
            for _ in range(self.config.realtime.check_interval_seconds):
                if not self._running:
                    break
                time.sleep(1)
        
        logger.debug("Session monitor loop ended")
    
    def _check_sessions(self) -> None:
        """Check current Plex sessions and trigger caching if needed."""
        sessions = self.plex.get_active_sessions()
        current_keys = {s.session_key for s in sessions}
        
        with self._lock:
            # Handle new sessions
            for session in sessions:
                if session.session_key not in self._active_sessions:
                    self._handle_new_session(session)
                else:
                    self._update_session(session)
            
            # Handle ended sessions
            ended = set(self._active_sessions.keys()) - current_keys
            for key in ended:
                self._handle_ended_session(key)
    
    def _handle_new_session(self, session: ActiveSession) -> None:
        """Handle a new playback session."""
        self._active_sessions[session.session_key] = session
        logger.info(f"New session: {session.username} watching '{session.media_title}'")
        
        # Trigger cache if configured
        if self.config.realtime.cache_on_play_start:
            if not self._is_already_cached(session.file_path):
                logger.info(f"Caching during playback: {session.media_title}")
                self.file_ops.copy_to_cache_atomic(session.file_path)
                self.timestamp_tracker.record(session.file_path, source='active_watching')
    
    def _update_session(self, session: ActiveSession) -> None:
        """Update an existing session."""
        self._active_sessions[session.session_key] = session
        
        # Check if marked as watched
        threshold = self.config.realtime.watched_threshold_percent
        if session.progress_percent >= threshold:
            logger.debug(f"Marked watched: {session.media_title} ({session.progress_percent:.1f}%)")
    
    def _handle_ended_session(self, session_key: str) -> None:
        """Handle a session that has ended."""
        session = self._active_sessions.pop(session_key, None)
        if session:
            logger.info(
                f"Session ended: {session.username} finished '{session.media_title}' "
                f"({session.progress_percent:.1f}%)"
            )
    
    def get_active_file_paths(self) -> Set[str]:
        """Get file paths of currently playing media."""
        with self._lock:
            return {s.file_path for s in self._active_sessions.values()}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current cache manager status."""
        stats = self.get_cache_stats()
        
        return {
            'running': self._running,
            'stats': stats.to_dict(),
            'active_sessions': len(self._active_sessions),
            'tracked_files': self.timestamp_tracker.count(),
            'ondeck_entries': self.ondeck_tracker.count(),
            'watchlist_entries': self.watchlist_tracker.count(),
        }
