"""
Cache tracking services for Cacherr.

Provides thread-safe tracking of:
- Cache timestamps (when files were cached)
- Watchlist items (user watchlist tracking)
- OnDeck items (currently watching tracking)
- Priority scoring for smart eviction
"""

import os
import json
import threading
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class EpisodeInfo:
    """Episode information for TV shows."""
    show: str
    season: int
    episode: int
    is_current_ondeck: bool = False


@dataclass
class TrackedFile:
    """Base tracking info for a cached file."""
    file_path: str
    cached_at: datetime
    source: str  # 'ondeck', 'watchlist', 'trakt', 'manual'
    users: List[str] = field(default_factory=list)
    last_seen: Optional[datetime] = None
    watched_at: Optional[datetime] = None
    file_size_bytes: int = 0
    episode_info: Optional[EpisodeInfo] = None
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'source': self.source,
            'users': self.users,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'watched_at': self.watched_at.isoformat() if self.watched_at else None,
            'file_size_bytes': self.file_size_bytes,
            'episode_info': {
                'show': self.episode_info.show,
                'season': self.episode_info.season,
                'episode': self.episode_info.episode,
                'is_current_ondeck': self.episode_info.is_current_ondeck,
            } if self.episode_info else None,
            'access_count': self.access_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackedFile":
        episode_info = None
        if data.get('episode_info'):
            ep = data['episode_info']
            episode_info = EpisodeInfo(
                show=ep.get('show', ''),
                season=ep.get('season', 0),
                episode=ep.get('episode', 0),
                is_current_ondeck=ep.get('is_current_ondeck', False),
            )
        
        return cls(
            file_path=data.get('file_path', ''),
            cached_at=datetime.fromisoformat(data['cached_at']) if data.get('cached_at') else datetime.now(timezone.utc),
            source=data.get('source', 'unknown'),
            users=data.get('users', []),
            last_seen=datetime.fromisoformat(data['last_seen']) if data.get('last_seen') else None,
            watched_at=datetime.fromisoformat(data['watched_at']) if data.get('watched_at') else None,
            file_size_bytes=data.get('file_size_bytes', 0),
            episode_info=episode_info,
            access_count=data.get('access_count', 0),
        )


class BaseTracker:
    """Base class for thread-safe JSON file trackers."""
    
    def __init__(self, tracker_file: str, tracker_name: str = "tracker"):
        self.tracker_file = tracker_file
        self._tracker_name = tracker_name
        self._lock = threading.RLock()
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self) -> None:
        """Load tracker data from file."""
        try:
            if os.path.exists(self.tracker_file):
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                self._post_load()
                logger.debug(f"Loaded {len(self._data)} {self._tracker_name} entries")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load {self._tracker_name} file: {e}")
            self._data = {}
    
    def _post_load(self) -> None:
        """Hook for subclasses to process data after loading."""
        pass
    
    def _save(self) -> None:
        """Save tracker data to file."""
        try:
            # Ensure directory exists
            Path(self.tracker_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except IOError as e:
            logger.error(f"Could not save {self._tracker_name} file: {e}")
    
    def get_entry(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get entry for a file path."""
        with self._lock:
            if file_path in self._data:
                return self._data[file_path].copy()
            # Try matching by filename only
            filename = os.path.basename(file_path)
            for stored_path, entry in self._data.items():
                if os.path.basename(stored_path) == filename:
                    return entry.copy()
            return None
    
    def remove_entry(self, file_path: str) -> bool:
        """Remove entry for a file path."""
        with self._lock:
            if file_path in self._data:
                del self._data[file_path]
                self._save()
                return True
            return False
    
    def get_all_entries(self) -> Dict[str, Dict[str, Any]]:
        """Get all entries."""
        with self._lock:
            return self._data.copy()
    
    def count(self) -> int:
        """Get number of entries."""
        with self._lock:
            return len(self._data)


class CacheTimestampTracker(BaseTracker):
    """Tracks when files were cached and their source.
    
    Used for cache retention - files cached recently won't be moved back.
    """
    
    def __init__(self, tracker_file: str):
        super().__init__(tracker_file, "cache_timestamp")
    
    def _post_load(self) -> None:
        """Migrate old format (plain string) to new format (dict)."""
        migrated = False
        new_data = {}
        
        for path, value in self._data.items():
            if isinstance(value, str):
                # Old format: just a timestamp string
                new_data[path] = {
                    'cached_at': value,
                    'source': 'unknown'
                }
                migrated = True
            elif isinstance(value, dict):
                new_data[path] = value
        
        if migrated:
            self._data = new_data
            self._save()
            logger.info("Migrated timestamp file to new format")
    
    def record(self, file_path: str, source: str = "unknown", file_size: int = 0) -> None:
        """Record when a file was cached. Never overwrites existing."""
        with self._lock:
            if file_path in self._data:
                logger.debug(f"Timestamp already exists: {file_path}")
                return
            
            self._data[file_path] = {
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'source': source,
                'file_size_bytes': file_size,
            }
            self._save()
            logger.debug(f"Recorded cache timestamp: {file_path} (source: {source})")
    
    def is_within_retention(self, file_path: str, retention_hours: float) -> bool:
        """Check if file is still within retention period."""
        with self._lock:
            entry = self._data.get(file_path)
            if not entry:
                return False
            
            try:
                cached_at = entry.get('cached_at')
                if isinstance(cached_at, str):
                    cached_time = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
                else:
                    return False
                
                now = datetime.now(timezone.utc)
                if cached_time.tzinfo is None:
                    cached_time = cached_time.replace(tzinfo=timezone.utc)
                
                age_hours = (now - cached_time).total_seconds() / 3600
                return age_hours < retention_hours
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid timestamp for {file_path}: {e}")
                return False
    
    def get_age_hours(self, file_path: str) -> float:
        """Get how many hours the file has been cached."""
        with self._lock:
            entry = self._data.get(file_path)
            if not entry:
                return -1
            
            try:
                cached_at = entry.get('cached_at')
                if isinstance(cached_at, str):
                    cached_time = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    if cached_time.tzinfo is None:
                        cached_time = cached_time.replace(tzinfo=timezone.utc)
                    return (now - cached_time).total_seconds() / 3600
            except (ValueError, TypeError):
                pass
            return -1
    
    def get_source(self, file_path: str) -> str:
        """Get the source (ondeck/watchlist/etc) for a cached file."""
        entry = self.get_entry(file_path)
        if entry:
            return entry.get('source', 'unknown')
        return 'unknown'
    
    def cleanup_missing_files(self) -> int:
        """Remove entries for files that no longer exist."""
        with self._lock:
            missing = [p for p in self._data if not os.path.exists(p)]
            for path in missing:
                del self._data[path]
            if missing:
                self._save()
                logger.info(f"Cleaned up {len(missing)} stale timestamp entries")
            return len(missing)


class WatchlistTracker(BaseTracker):
    """Tracks watchlist items and their users.
    
    Used for watchlist retention - files auto-expire X days after being added.
    """
    
    def __init__(self, tracker_file: str):
        super().__init__(tracker_file, "watchlist")
    
    def update_entry(self, file_path: str, username: str, 
                     watchlisted_at: Optional[datetime] = None) -> None:
        """Update or create entry for a watchlist item."""
        with self._lock:
            now = datetime.now(timezone.utc)
            
            if file_path in self._data:
                entry = self._data[file_path]
                # Add user if not already present
                if username not in entry.get('users', []):
                    entry.setdefault('users', []).append(username)
                entry['last_seen'] = now.isoformat()
                
                # Update watchlisted_at if newer
                if watchlisted_at:
                    existing = entry.get('watchlisted_at')
                    if existing:
                        try:
                            existing_dt = datetime.fromisoformat(existing.replace('Z', '+00:00'))
                            if watchlisted_at.tzinfo is None:
                                watchlisted_at = watchlisted_at.replace(tzinfo=timezone.utc)
                            if watchlisted_at > existing_dt:
                                entry['watchlisted_at'] = watchlisted_at.isoformat()
                        except ValueError:
                            entry['watchlisted_at'] = watchlisted_at.isoformat()
                    else:
                        entry['watchlisted_at'] = watchlisted_at.isoformat()
            else:
                self._data[file_path] = {
                    'watchlisted_at': (watchlisted_at or now).isoformat(),
                    'users': [username],
                    'last_seen': now.isoformat(),
                }
            
            self._save()
    
    def get_user_count(self, file_path: str) -> int:
        """Get number of users with this file on their watchlist."""
        entry = self.get_entry(file_path)
        if entry:
            return len(entry.get('users', []))
        return 0
    
    def get_days_on_watchlist(self, file_path: str) -> float:
        """Get days since file was first added to a watchlist."""
        entry = self.get_entry(file_path)
        if not entry:
            return -1
        
        try:
            watchlisted_at = entry.get('watchlisted_at')
            if watchlisted_at:
                dt = datetime.fromisoformat(watchlisted_at.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return (now - dt).total_seconds() / 86400
        except (ValueError, TypeError):
            pass
        return -1
    
    def cleanup_stale(self, max_days: int = 7) -> int:
        """Remove entries not seen in max_days."""
        with self._lock:
            now = datetime.now(timezone.utc)
            stale = []
            
            for path, entry in self._data.items():
                last_seen = entry.get('last_seen')
                if last_seen:
                    try:
                        dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        days = (now - dt).total_seconds() / 86400
                        if days > max_days:
                            stale.append(path)
                    except ValueError:
                        stale.append(path)
                else:
                    stale.append(path)
            
            for path in stale:
                del self._data[path]
            
            if stale:
                self._save()
                logger.info(f"Cleaned up {len(stale)} stale watchlist entries")
            
            return len(stale)


class OnDeckTracker(BaseTracker):
    """Tracks OnDeck items, users, and episode positions.
    
    OnDeck status is ephemeral - cleared at start of each run.
    """
    
    def __init__(self, tracker_file: str):
        super().__init__(tracker_file, "ondeck")
    
    def update_entry(self, file_path: str, username: str,
                     episode_info: Optional[EpisodeInfo] = None,
                     is_current_ondeck: bool = True) -> None:
        """Update or create entry for an OnDeck item."""
        with self._lock:
            now = datetime.now(timezone.utc)
            
            if file_path in self._data:
                entry = self._data[file_path]
                if username not in entry.get('users', []):
                    entry.setdefault('users', []).append(username)
                entry['last_seen'] = now.isoformat()
            else:
                self._data[file_path] = {
                    'users': [username],
                    'last_seen': now.isoformat(),
                }
            
            if episode_info:
                self._data[file_path]['episode_info'] = {
                    'show': episode_info.show,
                    'season': episode_info.season,
                    'episode': episode_info.episode,
                    'is_current_ondeck': is_current_ondeck,
                }
            
            self._save()
    
    def get_user_count(self, file_path: str) -> int:
        """Get number of users with this file on their OnDeck."""
        entry = self.get_entry(file_path)
        if entry:
            return len(entry.get('users', []))
        return 0
    
    def get_episode_info(self, file_path: str) -> Optional[EpisodeInfo]:
        """Get episode info for a file."""
        entry = self.get_entry(file_path)
        if entry and entry.get('episode_info'):
            ep = entry['episode_info']
            return EpisodeInfo(
                show=ep.get('show', ''),
                season=ep.get('season', 0),
                episode=ep.get('episode', 0),
                is_current_ondeck=ep.get('is_current_ondeck', False),
            )
        return None
    
    def get_ondeck_positions(self, show_name: str) -> List[Tuple[int, int]]:
        """Get all current OnDeck positions for a show.
        
        Returns list of (season, episode) tuples.
        """
        with self._lock:
            positions = []
            show_lower = show_name.lower()
            
            for path, entry in self._data.items():
                ep_info = entry.get('episode_info')
                if ep_info and ep_info.get('is_current_ondeck'):
                    if ep_info.get('show', '').lower() == show_lower:
                        season = ep_info.get('season')
                        episode = ep_info.get('episode')
                        if season is not None and episode is not None:
                            positions.append((season, episode))
            
            return positions
    
    def get_earliest_ondeck(self, show_name: str) -> Optional[Tuple[int, int]]:
        """Get earliest OnDeck position for a show (for eviction calculations)."""
        positions = self.get_ondeck_positions(show_name)
        if positions:
            positions.sort()
            return positions[0]
        return None
    
    def clear_for_run(self) -> None:
        """Clear all entries at start of a run (OnDeck is ephemeral)."""
        with self._lock:
            self._data = {}
            self._save()
            logger.debug("Cleared OnDeck tracker for new run")
    
    def cleanup_stale(self, max_days: int = 1) -> int:
        """Remove entries not seen in max_days (shorter than watchlist)."""
        with self._lock:
            now = datetime.now(timezone.utc)
            stale = []
            
            for path, entry in self._data.items():
                last_seen = entry.get('last_seen')
                if last_seen:
                    try:
                        dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        days = (now - dt).total_seconds() / 86400
                        if days > max_days:
                            stale.append(path)
                    except ValueError:
                        stale.append(path)
                else:
                    stale.append(path)
            
            for path in stale:
                del self._data[path]
            
            if stale:
                self._save()
                logger.debug(f"Cleaned up {len(stale)} stale OnDeck entries")
            
            return len(stale)


class CachePriorityScorer:
    """Calculates priority scores for smart eviction.
    
    Priority Score (0-100, higher = keep longer):
    - Base: 50
    - Active playback: 100 (never evict)
    - Source: OnDeck +20, Watchlist +10, Trakt +5
    - User count: +5 per user (max +15)
    - Recency: Recently cached +10 to +20
    - Age: Old files -10 to -20
    - Episode position: Current OnDeck +15, Next episodes +10
    """
    
    SOURCE_SCORES = {
        'active_watching': 50,  # Currently playing - never evict
        'ondeck': 20,
        'continue_watching': 15,
        'watchlist': 10,
        'trakt': 5,
        'manual': 0,
        'unknown': 0,
    }
    
    @classmethod
    def calculate(cls, 
                  entry: Dict[str, Any],
                  actively_playing: bool = False,
                  number_episodes_setting: int = 5) -> int:
        """Calculate priority score for a cached file.
        
        Args:
            entry: Tracker entry dict
            actively_playing: Whether file is currently being played
            number_episodes_setting: NUMBER_EPISODES config setting
            
        Returns:
            Priority score 0-100
        """
        if actively_playing:
            return 100  # Never evict playing files
        
        score = 50  # Base score
        
        # Source bonus
        source = entry.get('source', 'unknown')
        score += cls.SOURCE_SCORES.get(source, 0)
        
        # User count bonus (+5 per user, max +15)
        user_count = len(entry.get('users', []))
        score += min(user_count * 5, 15)
        
        # Recency bonus/penalty
        cached_at = entry.get('cached_at')
        if cached_at:
            try:
                dt = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                hours = (now - dt).total_seconds() / 3600
                
                if hours < 2:
                    score += 20
                elif hours < 6:
                    score += 15
                elif hours < 24:
                    score += 10
                elif hours < 72:
                    score += 5
                elif hours > 168:  # > 1 week
                    score -= 10
                elif hours > 336:  # > 2 weeks
                    score -= 20
            except (ValueError, TypeError):
                pass
        
        # Episode position bonus
        ep_info = entry.get('episode_info')
        if ep_info:
            is_current = ep_info.get('is_current_ondeck', False)
            if is_current:
                score += 15
            else:
                # Future episodes get smaller bonus
                episode_ahead = ep_info.get('episodes_ahead', 0)
                if 0 < episode_ahead <= max(1, number_episodes_setting // 2):
                    score += 10
        
        # Access count bonus
        access_count = entry.get('access_count', 0)
        score += min(access_count * 2, 10)
        
        return max(0, min(100, score))
    
    @classmethod
    def get_eviction_candidates(cls,
                                entries: Dict[str, Dict[str, Any]],
                                target_bytes: int,
                                min_priority: int = 60,
                                actively_playing_files: Optional[Set[str]] = None,
                                protected_hours: float = 2.0) -> List[Tuple[str, int, int]]:
        """Get files to evict to free target_bytes.
        
        Returns list of (path, priority, size_bytes) sorted by priority ascending.
        Only returns files with priority < min_priority.
        """
        if actively_playing_files is None:
            actively_playing_files = set()
        
        candidates = []
        now = datetime.now(timezone.utc)
        
        for path, entry in entries.items():
            # Skip actively playing
            if path in actively_playing_files:
                continue
            
            # Skip recently cached (protected period)
            cached_at = entry.get('cached_at')
            if cached_at:
                try:
                    dt = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    hours = (now - dt).total_seconds() / 3600
                    if hours < protected_hours:
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Calculate priority
            is_playing = path in actively_playing_files
            priority = cls.calculate(entry, actively_playing=is_playing)
            
            # Only consider files below min_priority
            if priority < min_priority:
                size = entry.get('file_size_bytes', 0)
                candidates.append((path, priority, size))
        
        # Sort by priority ascending (lowest first)
        candidates.sort(key=lambda x: x[1])
        
        # Select enough to meet target
        selected = []
        freed = 0
        for path, priority, size in candidates:
            if freed >= target_bytes:
                break
            selected.append((path, priority, size))
            freed += size
        
        return selected
