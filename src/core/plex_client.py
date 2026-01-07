"""
Plex API Integration for Cacherr.

Provides:
- Plex server connection
- OnDeck media discovery
- Watchlist fetching
- Active session monitoring
- Watched status detection
"""

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Set, Dict, Any, Tuple
from dataclasses import dataclass, field

try:
    from plexapi.server import PlexServer
    from plexapi.myplex import MyPlexAccount
    from plexapi.video import Movie, Show, Episode
    PLEXAPI_AVAILABLE = True
except ImportError:
    PLEXAPI_AVAILABLE = False
    PlexServer = None


logger = logging.getLogger(__name__)


@dataclass
class OnDeckItem:
    """Represents an OnDeck media item."""
    file_path: str
    username: str
    media_title: str
    media_type: str  # 'movie' or 'episode'
    is_current_ondeck: bool = True
    episode_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'username': self.username,
            'media_title': self.media_title,
            'media_type': self.media_type,
            'is_current_ondeck': self.is_current_ondeck,
            'episode_info': self.episode_info,
        }


@dataclass
class WatchlistItem:
    """Represents a watchlist media item."""
    file_path: str
    username: str
    media_title: str
    media_type: str
    added_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'username': self.username,
            'media_title': self.media_title,
            'media_type': self.media_type,
            'added_at': self.added_at.isoformat() if self.added_at else None,
        }


@dataclass
class ActiveSession:
    """Represents an active Plex playback session."""
    session_key: str
    user_id: str
    username: str
    media_title: str
    media_type: str
    file_path: str
    state: str  # 'playing', 'paused', 'buffering'
    view_offset_ms: int
    duration_ms: int
    
    @property
    def progress_percent(self) -> float:
        if self.duration_ms <= 0:
            return 0.0
        return (self.view_offset_ms / self.duration_ms) * 100


class PlexClient:
    """
    Plex API client for Cacherr.
    
    Handles all Plex API interactions including:
    - Server connection and authentication
    - OnDeck discovery for all users
    - Watchlist fetching (local and RSS)
    - Active session monitoring
    - Watched status detection
    """
    
    def __init__(self,
                 url: str,
                 token: str,
                 valid_sections: Optional[List[int]] = None):
        """
        Initialize Plex client.
        
        Args:
            url: Plex server URL (e.g., http://192.168.1.100:32400)
            token: Plex authentication token
            valid_sections: Library section IDs to process (None = all)
        """
        if not PLEXAPI_AVAILABLE:
            raise ImportError("plexapi package not installed. Install with: pip install plexapi")
        
        self.url = url
        self.token = token
        self.valid_sections = valid_sections or []
        self._server: Optional[PlexServer] = None
        self._account: Optional[MyPlexAccount] = None
    
    def connect(self) -> bool:
        """Connect to Plex server."""
        try:
            self._server = PlexServer(self.url, self.token)
            logger.info(f"Connected to Plex server: {self._server.friendlyName}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Plex: {e}")
            return False
    
    @property
    def server(self) -> PlexServer:
        if not self._server:
            raise RuntimeError("Not connected to Plex server")
        return self._server
    
    def get_ondeck(self,
                   number_episodes: int = 5,
                   days_to_monitor: int = 99,
                   skip_users: Optional[List[str]] = None) -> List[OnDeckItem]:
        """
        Get OnDeck items for all users.
        
        Args:
            number_episodes: Episodes to include ahead of current
            days_to_monitor: Only include recently watched shows
            skip_users: Users to exclude
            
        Returns:
            List of OnDeckItem objects
        """
        skip_users = set(skip_users or [])
        items = []
        
        # Get main user's OnDeck
        main_items = self._get_user_ondeck(
            self.server,
            username="Main",
            number_episodes=number_episodes,
            days_to_monitor=days_to_monitor
        )
        items.extend(main_items)
        
        # Get other users' OnDeck
        try:
            account = MyPlexAccount(token=self.token)
            for user in account.users():
                if user.title in skip_users:
                    continue
                
                try:
                    user_token = user.get_token(self.server.machineIdentifier)
                    user_server = PlexServer(self.url, user_token)
                    
                    user_items = self._get_user_ondeck(
                        user_server,
                        username=user.title,
                        number_episodes=number_episodes,
                        days_to_monitor=days_to_monitor
                    )
                    items.extend(user_items)
                except Exception as e:
                    logger.warning(f"Could not get OnDeck for {user.title}: {e}")
        except Exception as e:
            logger.warning(f"Could not get other users' OnDeck: {e}")
        
        return items
    
    def _get_user_ondeck(self,
                         server: PlexServer,
                         username: str,
                         number_episodes: int,
                         days_to_monitor: int) -> List[OnDeckItem]:
        """Get OnDeck items for a specific user."""
        items = []
        
        try:
            for video in server.library.onDeck():
                # Filter by section if configured
                if self.valid_sections and video.librarySectionID not in self.valid_sections:
                    continue
                
                if video.type == 'episode':
                    items.extend(self._process_ondeck_episode(
                        video, username, number_episodes
                    ))
                elif video.type == 'movie':
                    items.extend(self._process_ondeck_movie(video, username))
        except Exception as e:
            logger.error(f"Error getting OnDeck for {username}: {e}")
        
        return items
    
    def _process_ondeck_episode(self,
                                 episode,
                                 username: str,
                                 number_episodes: int) -> List[OnDeckItem]:
        """Process an OnDeck episode and get next episodes."""
        items = []
        show = episode.show()
        
        # Current OnDeck episode
        for media in episode.media:
            for part in media.parts:
                if part.file:
                    items.append(OnDeckItem(
                        file_path=part.file,
                        username=username,
                        media_title=f"{show.title} - {episode.title}",
                        media_type='episode',
                        is_current_ondeck=True,
                        episode_info={
                            'show': show.title,
                            'season': episode.parentIndex,
                            'episode': episode.index,
                        }
                    ))
        
        # Get next episodes
        try:
            all_episodes = show.episodes()
            current_season = episode.parentIndex
            current_episode = episode.index
            
            next_count = 0
            for ep in all_episodes:
                if ep.parentIndex is None or ep.index is None:
                    continue
                
                is_after_current = (
                    ep.parentIndex > current_season or
                    (ep.parentIndex == current_season and ep.index > current_episode)
                )
                
                if is_after_current and next_count < number_episodes:
                    for media in ep.media:
                        for part in media.parts:
                            if part.file:
                                items.append(OnDeckItem(
                                    file_path=part.file,
                                    username=username,
                                    media_title=f"{show.title} - {ep.title}",
                                    media_type='episode',
                                    is_current_ondeck=False,
                                    episode_info={
                                        'show': show.title,
                                        'season': ep.parentIndex,
                                        'episode': ep.index,
                                    }
                                ))
                    next_count += 1
        except Exception as e:
            logger.warning(f"Could not get next episodes: {e}")
        
        return items
    
    def _process_ondeck_movie(self, movie, username: str) -> List[OnDeckItem]:
        """Process an OnDeck movie."""
        items = []
        
        for media in movie.media:
            for part in media.parts:
                if part.file:
                    items.append(OnDeckItem(
                        file_path=part.file,
                        username=username,
                        media_title=movie.title,
                        media_type='movie',
                        is_current_ondeck=True,
                    ))
        
        return items
    
    def get_watchlist(self,
                      episodes_per_show: int = 1,
                      skip_users: Optional[List[str]] = None) -> List[WatchlistItem]:
        """
        Get watchlist items for all users.
        
        Args:
            episodes_per_show: Episodes to include per TV show
            skip_users: Users to exclude
            
        Returns:
            List of WatchlistItem objects
        """
        skip_users = set(skip_users or [])
        items = []
        
        try:
            account = MyPlexAccount(token=self.token)
            
            # Main user watchlist
            items.extend(self._get_user_watchlist(
                account, "Main", episodes_per_show
            ))
            
            # Other users
            for user in account.users():
                if user.title in skip_users:
                    continue
                
                try:
                    items.extend(self._get_user_watchlist(
                        user, user.title, episodes_per_show
                    ))
                except Exception as e:
                    logger.warning(f"Could not get watchlist for {user.title}: {e}")
        except Exception as e:
            logger.error(f"Error getting watchlists: {e}")
        
        return items
    
    def _get_user_watchlist(self,
                            account_or_user,
                            username: str,
                            episodes_per_show: int) -> List[WatchlistItem]:
        """Get watchlist for a specific user."""
        items = []
        
        try:
            watchlist = account_or_user.watchlist()
            
            for item in watchlist:
                added_at = getattr(item, 'addedAt', None)
                
                if item.type == 'movie':
                    # Find in library
                    for section in self.server.library.sections():
                        if section.type == 'movie':
                            try:
                                results = section.search(title=item.title)
                                for movie in results:
                                    for media in movie.media:
                                        for part in media.parts:
                                            if part.file:
                                                items.append(WatchlistItem(
                                                    file_path=part.file,
                                                    username=username,
                                                    media_title=item.title,
                                                    media_type='movie',
                                                    added_at=added_at,
                                                ))
                            except:
                                pass
                
                elif item.type == 'show':
                    # Get first N unwatched episodes
                    for section in self.server.library.sections():
                        if section.type == 'show':
                            try:
                                results = section.search(title=item.title)
                                for show in results:
                                    episode_count = 0
                                    for episode in show.episodes():
                                        if episode_count >= episodes_per_show:
                                            break
                                        if not episode.isPlayed:
                                            for media in episode.media:
                                                for part in media.parts:
                                                    if part.file:
                                                        items.append(WatchlistItem(
                                                            file_path=part.file,
                                                            username=username,
                                                            media_title=f"{show.title} - {episode.title}",
                                                            media_type='episode',
                                                            added_at=added_at,
                                                        ))
                                            episode_count += 1
                            except:
                                pass
        except Exception as e:
            logger.warning(f"Error getting watchlist for {username}: {e}")
        
        return items
    
    def get_active_sessions(self) -> List[ActiveSession]:
        """Get currently active playback sessions."""
        sessions = []
        
        try:
            for session in self.server.sessions():
                file_path = None
                
                # Get file path
                if hasattr(session, 'media'):
                    for media in session.media:
                        if hasattr(media, 'parts'):
                            for part in media.parts:
                                if hasattr(part, 'file') and part.file:
                                    file_path = part.file
                                    break
                        if file_path:
                            break
                
                if not file_path:
                    continue
                
                # Get user info
                username = "Unknown"
                user_id = "unknown"
                if hasattr(session, 'usernames') and session.usernames:
                    username = session.usernames[0]
                    user_id = username
                elif hasattr(session, 'user') and session.user:
                    username = getattr(session.user, 'title', 'Unknown')
                    user_id = str(getattr(session.user, 'id', username))
                
                # Get state
                state = getattr(session, 'state', 'unknown').lower()
                
                # Get title
                if session.type == 'episode':
                    title = f"{getattr(session, 'grandparentTitle', 'Unknown')} - {getattr(session, 'title', 'Unknown')}"
                else:
                    title = getattr(session, 'title', 'Unknown')
                
                sessions.append(ActiveSession(
                    session_key=str(session.sessionKey),
                    user_id=user_id,
                    username=username,
                    media_title=title,
                    media_type=session.type,
                    file_path=file_path,
                    state=state,
                    view_offset_ms=getattr(session, 'viewOffset', 0) or 0,
                    duration_ms=getattr(session, 'duration', 0) or 0,
                ))
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
        
        return sessions
    
    def get_active_file_paths(self) -> Set[str]:
        """Get set of file paths currently being played."""
        return {s.file_path for s in self.get_active_sessions()}
    
    def has_active_sessions(self) -> bool:
        """Check if there are any active playback sessions."""
        try:
            return len(self.server.sessions()) > 0
        except:
            return False
    
    def get_watched_files(self, library_section_ids: Optional[List[int]] = None) -> List[str]:
        """Get list of watched file paths."""
        watched = []
        section_ids = library_section_ids or self.valid_sections
        
        try:
            for section in self.server.library.sections():
                if section_ids and section.key not in section_ids:
                    continue
                
                if section.type == 'movie':
                    for movie in section.search(unwatched=False):
                        for media in movie.media:
                            for part in media.parts:
                                if part.file:
                                    watched.append(part.file)
                
                elif section.type == 'show':
                    for show in section.all():
                        for episode in show.episodes():
                            if episode.isPlayed:
                                for media in episode.media:
                                    for part in media.parts:
                                        if part.file:
                                            watched.append(part.file)
        except Exception as e:
            logger.error(f"Error getting watched files: {e}")
        
        return watched


class TraktClient:
    """
    Trakt.tv API client for trending content.
    """
    
    API_BASE = "https://api.trakt.tv"
    
    def __init__(self, client_id: str, client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_trending_movies(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get trending movies from Trakt."""
        import urllib.request
        import json
        
        try:
            url = f"{self.API_BASE}/movies/trending?limit={count}"
            
            request = urllib.request.Request(url)
            request.add_header('Content-Type', 'application/json')
            request.add_header('trakt-api-version', '2')
            request.add_header('trakt-api-key', self.client_id)
            
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode())
            
            movies = []
            for item in data:
                movie = item.get('movie', {})
                movies.append({
                    'title': movie.get('title', ''),
                    'year': movie.get('year'),
                    'imdb_id': movie.get('ids', {}).get('imdb'),
                    'tmdb_id': movie.get('ids', {}).get('tmdb'),
                    'watchers': item.get('watchers', 0),
                })
            
            return movies
        except Exception as e:
            logger.error(f"Error fetching Trakt trending: {e}")
            return []
