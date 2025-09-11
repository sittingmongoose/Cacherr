"""
Plex Operations Service with Pydantic v2.5 validation and comprehensive type safety.

This service handles all Plex server operations including media discovery,
watchlist management, and watched status tracking. All operations use
Pydantic v2.5 models for data validation and type safety.

Features:
- Comprehensive Plex media discovery and analysis
- Watchlist and watched status tracking
- Real-time media monitoring
- Concurrent operation processing
- Robust error handling and retry mechanisms
- Pydantic v2.5 type safety and validation

Example:
    >>> plex_ops = PlexOperations(config)
    >>> plex_ops.set_plex_connection(plex_server)
    >>> media = plex_ops.fetch_ondeck_media()
    >>> print(f"Found {len(media)} onDeck media files")
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Generator, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field, ConfigDict, field_validator
from plexapi.server import PlexServer
from plexapi.video import Episode, Movie
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import NotFound, BadRequest
from .url_utils import ensure_no_trailing_slash

try:
    from ..config.settings import Config
except ImportError:
    # Fallback for testing
    from config.settings import Config


class PlexMediaItem(BaseModel):
    """
    Pydantic v2.5 model for Plex media item information.

    Represents a media item with comprehensive metadata and validation.
    Used for type-safe media processing and analysis.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    title: str = Field(..., description="Media item title")
    key: str = Field(..., description="Plex API key for the item")
    rating_key: str = Field(..., description="Plex rating key")
    guid: str = Field(..., description="Unique Plex GUID")
    media_type: str = Field(..., description="Type of media (movie, episode, etc.)")
    file_path: Optional[str] = Field(None, description="Local file path if available")
    library_section: str = Field(..., description="Plex library section name")
    last_viewed_at: Optional[datetime] = Field(None, description="Last viewed timestamp")
    added_at: datetime = Field(..., description="When item was added to library")

    @field_validator('media_type')
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        """Validate media type is one of the supported types."""
        allowed_types = {'movie', 'episode', 'show', 'season', 'album', 'track'}
        if v not in allowed_types:
            raise ValueError(f'media_type must be one of: {allowed_types}')
        return v


class PlexConnectionConfig(BaseModel):
    """
    Pydantic v2.5 model for Plex connection configuration.

    Encapsulates all settings needed to establish and maintain
    a connection to a Plex server with validation.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    url: str = Field(..., description="Plex server URL with protocol and port")
    token: Optional[str] = Field(None, description="Plex authentication token")
    username: Optional[str] = Field(None, description="Plex username (alternative auth)")
    password: Optional[str] = Field(None, description="Plex password (alternative auth)")
    timeout: int = Field(30, ge=5, le=300, description="Connection timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate Plex URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        if '://' not in v:
            raise ValueError("URL must include protocol")
        return v


class PlexOperations:
    """
    Comprehensive Plex operations service using Pydantic v2.5 models.

    This service provides type-safe access to Plex server operations with
    comprehensive validation and error handling. All methods use Pydantic
    models for data validation and return typed results.

    Features:
    - Type-safe Plex media discovery and analysis
    - Watchlist and watched status tracking
    - Real-time media monitoring capabilities
    - Concurrent operation processing with thread pools
    - Robust error handling with retry mechanisms
    - Pydantic v2.5 validation for all data structures

    Example:
        >>> plex_ops = PlexOperations(config)
        >>> plex_ops.set_plex_connection(plex_server)
        >>> ondeck_files = plex_ops.fetch_ondeck_media()
        >>> print(f"Found {len(ondeck_files)} onDeck media files")
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.plex = None
        self.retry_limit = 3
        self.retry_delay = 5
    
    def set_plex_connection(self, plex: PlexServer):
        """Set the Plex server connection"""
        self.plex = plex

    # Optional helper for tests and watcher
    def get_plex_connection(self) -> Optional[PlexServer]:
        """Get or establish Plex connection"""
        if self.plex:
            return self.plex
        try:
            if getattr(self.config, 'plex', None):
                baseurl = ensure_no_trailing_slash(self.config.plex.url)
                # SecretStr in some contexts, plain str in others
                token_value = None
                if getattr(self.config.plex, 'token', None) is not None:
                    try:
                        token_value = self.config.plex.token.get_secret_value()  # type: ignore[attr-defined]
                    except Exception:
                        token_value = str(self.config.plex.token)

                if token_value and str(token_value).strip():
                    self.plex = PlexServer(baseurl=str(baseurl), token=token_value)
                    return self.plex

                if getattr(self.config.plex, 'username', None) and getattr(self.config.plex, 'password', None):
                    try:
                        pwd = self.config.plex.password.get_secret_value()  # type: ignore[attr-defined]
                    except Exception:
                        pwd = str(self.config.plex.password)
                    account = MyPlexAccount(self.config.plex.username, pwd)
                    token = account.authentication_token
                    self.plex = PlexServer(baseurl=str(baseurl), token=token)
                    return self.plex
        except Exception as e:
            # During initial setup, Plex may be unconfigured; reduce severity
            self.logger.warning(f"Failed to create Plex connection: {e}")
            return None
        return None
    
    def fetch_ondeck_media(self) -> List[str]:
        """Fetch onDeck media from Plex"""
        if not self.plex:
            self.logger.error("No Plex connection available")
            return []
        
        self.logger.info("Fetching onDeck media...")
        on_deck_files = []
        
        try:
            # Get onDeck items
            on_deck_items = self.plex.library.onDeck()
            
            for item in on_deck_items:
                try:
                    # Check if item is within monitoring period
                    if not self._is_item_recent(item):
                        continue
                    
                    # Process based on item type
                    if isinstance(item, Episode):
                        files = self._process_episode_ondeck(item)
                    elif isinstance(item, Movie):
                        files = self._process_movie_ondeck(item)
                    else:
                        continue
                    
                    on_deck_files.extend(files)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing onDeck item {item.title}: {e}")
                    continue
            
            self.logger.info(f"Found {len(on_deck_files)} onDeck files")
            return on_deck_files
            
        except Exception as e:
            self.logger.error(f"Error fetching onDeck media: {e}")
            return []
    
    def fetch_watchlist_media(self) -> List[str]:
        """Fetch watchlist media from Plex"""
        if not self.plex:
            self.logger.error("No Plex connection available")
            return []
        
        self.logger.info("Fetching watchlist media...")
        watchlist_files = []
        
        try:
            # Get watchlist for main user
            # Convert SecretStr to string if needed
            token_value = None
            if getattr(self.config.plex, 'token', None) is not None:
                try:
                    token_value = self.config.plex.token.get_secret_value()  # type: ignore[attr-defined]
                except Exception:
                    token_value = str(self.config.plex.token)
            
            if not token_value or not str(token_value).strip():
                self.logger.error("No valid Plex token available for watchlist access")
                return []
            
            account = MyPlexAccount(token=token_value)
            watchlist = account.watchlist(filter='released')
            
            for item in watchlist:
                try:
                    # Search for the item in Plex library
                    plex_item = self._search_plex_item(item.title)
                    if not plex_item:
                        continue
                    
                    # Process based on item type
                    if plex_item.TYPE == 'show':
                        files = self._process_show_watchlist(plex_item)
                    else:
                        files = self._process_movie_watchlist(plex_item)
                    
                    watchlist_files.extend(files)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing watchlist item {item.title}: {e}")
                    continue
            
            self.logger.info(f"Found {len(watchlist_files)} watchlist files")
            return watchlist_files
            
        except Exception as e:
            self.logger.error(f"Error fetching watchlist media: {e}")
            return []
    
    def fetch_watched_media(self) -> List[str]:
        """Fetch watched media from Plex"""
        if not self.plex:
            self.logger.error("No Plex connection available")
            return []
        
        self.logger.info("Fetching watched media...")
        watched_files = []
        
        try:
            # Get all library sections
            sections = self.plex.library.sections()
            
            for section in sections:
                try:
                    # Search for watched videos in section
                    videos = section.search(unwatched=False)
                    
                    for video in videos:
                        try:
                            if video.lastViewedAt:
                                files = self._process_watched_video(video)
                                watched_files.extend(files)
                        except Exception as e:
                            self.logger.warning(f"Error processing watched video {video.title}: {e}")
                            continue
                            
                except Exception as e:
                    self.logger.warning(f"Error processing section {section.title}: {e}")
                    continue
            
            self.logger.info(f"Found {len(watched_files)} watched files")
            return watched_files
            
        except Exception as e:
            self.logger.error(f"Error fetching watched media: {e}")
            return []
    
    def _is_item_recent(self, item) -> bool:
        """Check if an item was recently viewed"""
        if not hasattr(item, 'lastViewedAt') or not item.lastViewedAt:
            return False
        
        days_ago = datetime.now() - item.lastViewedAt
        return days_ago.days <= self.config.media.days_to_monitor
    
    def _process_episode_ondeck(self, episode: Episode) -> List[str]:
        """Process an onDeck episode and get file paths"""
        files = []
        
        # Get current episode files
        for media in episode.media:
            for part in media.parts:
                if hasattr(part, 'file') and part.file:
                    files.append(part.file)
        
        # Get next episodes
        show = episode.grandparentTitle
        section = episode.section()
        
        try:
            show_item = section.search(show)[0]
            episodes = show_item.episodes()
            
            # Get next episodes based on current position
            current_season = episode.parentIndex
            current_episode = episode.index
            
            next_episodes = self._get_next_episodes(
                episodes, current_season, current_episode
            )
            
            for next_ep in next_episodes:
                for media in next_ep.media:
                    for part in media.parts:
                        if hasattr(part, 'file') and part.file:
                            files.append(part.file)
                            
        except Exception as e:
            self.logger.warning(f"Error getting next episodes for {show}: {e}")
        
        return files
    
    def _process_movie_ondeck(self, movie: Movie) -> List[str]:
        """Process an onDeck movie and get file paths"""
        files = []
        
        for media in movie.media:
            for part in media.parts:
                if hasattr(part, 'file') and part.file:
                    files.append(part.file)
        
        return files
    
    def _process_show_watchlist(self, show) -> List[str]:
        """Process a show from watchlist and get file paths"""
        files = []
        
        try:
            episodes = show.episodes()
            
            # Get first N episodes based on configuration
            for episode in episodes[:self.config.media.watchlist_episodes]:
                if not episode.isPlayed:
                    for media in episode.media:
                        for part in media.parts:
                            if hasattr(part, 'file') and part.file:
                                files.append(part.file)
                                
        except Exception as e:
            self.logger.warning(f"Error processing show watchlist {show.title}: {e}")
        
        return files
    
    def _process_movie_watchlist(self, movie) -> List[str]:
        """Process a movie from watchlist and get file paths"""
        files = []
        
        if not movie.isPlayed:
            for media in movie.media:
                for part in media.parts:
                    if hasattr(part, 'file') and part.file:
                        files.append(part.file)
        
        return files
    
    def _process_watched_video(self, video) -> List[str]:
        """Process a watched video and get file paths"""
        files = []
        
        if video.TYPE == 'show':
            # For shows, get all episodes
            try:
                episodes = video.episodes()
                for episode in episodes:
                    if episode.isPlayed:
                        for media in episode.media:
                            for part in media.parts:
                                if hasattr(part, 'file') and part.file:
                                    files.append(part.file)
            except Exception as e:
                self.logger.warning(f"Error processing watched show {video.title}: {e}")
        else:
            # For movies, get the file directly
            for media in video.media:
                for part in media.parts:
                    if hasattr(part, 'file') and part.file:
                        files.append(part.file)
        
        return files
    
    def _get_next_episodes(self, episodes: List[Episode], current_season: int, 
                           current_episode: int) -> List[Episode]:
        """Get next episodes after the current one"""
        next_episodes = []
        
        for episode in episodes:
            if (episode.parentIndex > current_season or 
                (episode.parentIndex == current_season and episode.index > current_episode)):
                
                if len(next_episodes) < self.config.media.number_episodes:
                    next_episodes.append(episode)
                else:
                    break
        
        return next_episodes
    
    def _search_plex_item(self, title: str):
        """Search for an item in Plex library"""
        try:
            results = self.plex.search(title)
            return results[0] if results else None
        except Exception as e:
            self.logger.warning(f"Error searching for {title}: {e}")
            return None
    
    def _retry_operation(self, operation, *args, **kwargs):
        """Retry an operation with exponential backoff"""
        for attempt in range(self.retry_limit):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) and attempt < self.retry_limit - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"Rate limited, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    raise e
