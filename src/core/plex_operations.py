import logging
import time
from datetime import datetime, timedelta
from typing import List, Generator, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from plexapi.server import PlexServer
from plexapi.video import Episode, Movie
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import NotFound, BadRequest

try:
    from ..config.settings import Config
except ImportError:
    # Fallback for testing
    from config.settings import Config

class PlexOperations:
    """Handles Plex API operations for PlexCacheUltra"""
    
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
            if self.config.plex.token:
                self.plex = PlexServer(baseurl=self.config.plex.url, token=self.config.plex.token)
                return self.plex
            if self.config.plex.username and self.config.plex.password:
                account = MyPlexAccount(self.config.plex.username, self.config.plex.password)
                token = account.authentication_token
                self.plex = PlexServer(baseurl=self.config.plex.url, token=token)
                return self.plex
        except Exception as e:
            self.logger.error(f"Failed to create Plex connection: {e}")
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
            account = MyPlexAccount(token=self.config.plex.token)
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
