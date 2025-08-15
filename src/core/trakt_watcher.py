import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class TraktMovie:
    """Represents a movie from Trakt.tv"""
    trakt_id: int
    title: str
    year: int
    slug: str
    added_at: datetime
    last_updated: datetime

class TraktWatcher:
    """Monitors trending movies from Trakt.tv and manages caching recommendations"""
    
    def __init__(self, config, cache_engine):
        self.config = config
        self.cache_engine = cache_engine
        self.logger = logging.getLogger(__name__)
        
        # Trakt API configuration
        self.base_url = "https://api.trakt.tv"
        self.headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': config.trakt.client_id
        }
        
        # State management
        self.trending_movies: Dict[int, TraktMovie] = {}
        self.previous_trending_ids: Set[int] = set()
        self.watching_thread: Optional[threading.Thread] = None
        self.watching_running = False
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'movies_added': 0,
            'movies_removed': 0,
            'last_check': None,
            'last_update': None,
            'errors': 0
        }
        
        # Cache file for persistence
        self.cache_file = Path("trakt_trending_cache.json")
        self._load_cache()
        
        self.logger.info("TraktWatcher initialized")
    
    def start_watching(self):
        """Start monitoring Trakt.tv trending movies"""
        if self.watching_running:
            self.logger.warning("TraktWatcher is already running")
            return
        
        if not self.config.trakt.enabled:
            self.logger.warning("Trakt integration is disabled in configuration")
            return
        
        if not self.config.trakt.client_id:
            self.logger.error("Trakt client ID is required to start watching")
            return
        
        self.watching_running = True
        self.watching_thread = threading.Thread(target=self._trending_monitor_loop, daemon=True)
        self.watching_thread.start()
        self.logger.info("Started Trakt trending movies monitoring")
    
    def stop_watching(self):
        """Stop monitoring Trakt.tv trending movies"""
        if not self.watching_running:
            return
        
        self.watching_running = False
        if self.watching_thread and self.watching_thread.is_alive():
            self.watching_thread.join(timeout=5)
        
        self.logger.info("Stopped Trakt trending movies monitoring")
    
    def _trending_monitor_loop(self):
        """Main loop for monitoring trending movies"""
        while self.watching_running:
            try:
                self._check_trending_movies()
                time.sleep(self.config.trakt.check_interval)
            except Exception as e:
                self.logger.error(f"Error in trending monitor loop: {e}")
                self.stats['errors'] += 1
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _check_trending_movies(self):
        """Fetch and process trending movies from Trakt.tv"""
        try:
            self.logger.debug("Checking Trakt.tv trending movies")
            
            # Fetch trending movies
            response = requests.get(
                f"{self.base_url}/movies/trending",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            trending_data = response.json()
            current_trending_ids = set()
            
            # Process trending movies
            for item in trending_data[:self.config.trakt.trending_movies_count]:
                movie_data = item['movie']
                trakt_id = movie_data['ids']['trakt']
                current_trending_ids.add(trakt_id)
                
                # Check if this is a new movie or needs updating
                if trakt_id not in self.trending_movies:
                    self._add_trending_movie(movie_data)
                else:
                    self._update_trending_movie(movie_data)
            
            # Remove movies that are no longer trending
            removed_ids = self.previous_trending_ids - current_trending_ids
            for trakt_id in removed_ids:
                self._remove_trending_movie(trakt_id)
            
            # Update state
            self.previous_trending_ids = current_trending_ids
            self.stats['total_checks'] += 1
            self.stats['last_check'] = datetime.now().isoformat()
            
            # Save cache
            self._save_cache()
            
            self.logger.info(f"Processed {len(current_trending_ids)} trending movies")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch trending movies from Trakt.tv: {e}")
            self.stats['errors'] += 1
        except Exception as e:
            self.logger.error(f"Unexpected error checking trending movies: {e}")
            self.stats['errors'] += 1
    
    def _add_trending_movie(self, movie_data: dict):
        """Add a new trending movie to the list"""
        trakt_id = movie_data['ids']['trakt']
        now = datetime.now()
        
        movie = TraktMovie(
            trakt_id=trakt_id,
            title=movie_data['title'],
            year=movie_data['year'],
            slug=movie_data['ids']['slug'],
            added_at=now,
            last_updated=now
        )
        
        self.trending_movies[trakt_id] = movie
        self.stats['movies_added'] += 1
        self.stats['last_update'] = now.isoformat()
        
        self.logger.info(f"Added trending movie: {movie.title} ({movie.year})")
        
        # Trigger caching for this movie
        self._trigger_caching_for_movie(movie)
    
    def _update_trending_movie(self, movie_data: dict):
        """Update an existing trending movie"""
        trakt_id = movie_data['ids']['trakt']
        if trakt_id in self.trending_movies:
            movie = self.trending_movies[trakt_id]
            movie.last_updated = datetime.now()
            self.stats['last_update'] = datetime.now().isoformat()
    
    def _remove_trending_movie(self, trakt_id: int):
        """Remove a movie that is no longer trending"""
        if trakt_id in self.trending_movies:
            movie = self.trending_movies[trakt_id]
            self.logger.info(f"Removed trending movie: {movie.title} ({movie.year})")
            del self.trending_movies[trakt_id]
            self.stats['movies_removed'] += 1
            self.stats['last_update'] = datetime.now().isoformat()
    
    def _trigger_caching_for_movie(self, movie: TraktMovie):
        """Trigger caching for a trending movie"""
        try:
            # This would integrate with the cache engine to add the movie to the cache list
            # For now, we'll log the action
            self.logger.info(f"Triggered caching for trending movie: {movie.title}")
            
            # TODO: Integrate with cache engine to add movie to cache list
            # self.cache_engine.add_movie_to_cache(movie)
            
        except Exception as e:
            self.logger.error(f"Failed to trigger caching for movie {movie.title}: {e}")
    
    def get_trending_movies(self) -> List[Dict]:
        """Get current trending movies for API display"""
        return [
            {
                'trakt_id': movie.trakt_id,
                'title': movie.title,
                'year': movie.year,
                'slug': movie.slug,
                'added_at': movie.added_at.isoformat(),
                'last_updated': movie.last_updated.isoformat()
            }
            for movie in self.trending_movies.values()
        ]
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            **self.stats,
            'trending_movies_count': len(self.trending_movies),
            'is_watching': self.watching_running
        }
    
    def clear_history(self):
        """Clear all history and statistics"""
        self.trending_movies.clear()
        self.previous_trending_ids.clear()
        self.stats = {
            'total_checks': 0,
            'movies_added': 0,
            'movies_removed': 0,
            'last_check': None,
            'last_update': None,
            'errors': 0
        }
        self._save_cache()
        self.logger.info("Cleared Trakt watcher history")
    
    def _load_cache(self):
        """Load trending movies from cache file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    
                # Restore trending movies
                for movie_data in data.get('trending_movies', []):
                    movie = TraktMovie(
                        trakt_id=movie_data['trakt_id'],
                        title=movie_data['title'],
                        year=movie_data['year'],
                        slug=movie_data['slug'],
                        added_at=datetime.fromisoformat(movie_data['added_at']),
                        last_updated=datetime.fromisoformat(movie_data['last_updated'])
                    )
                    self.trending_movies[movie.trakt_id] = movie
                
                # Restore previous trending IDs
                self.previous_trending_ids = set(data.get('previous_trending_ids', []))
                
                # Restore stats
                stats_data = data.get('stats', {})
                for key, value in stats_data.items():
                    if key in self.stats:
                        if key in ['last_check', 'last_update'] and value:
                            try:
                                self.stats[key] = datetime.fromisoformat(value).isoformat()
                            except ValueError:
                                self.stats[key] = value
                        else:
                            self.stats[key] = value
                
                self.logger.info(f"Loaded {len(self.trending_movies)} trending movies from cache")
                
        except Exception as e:
            self.logger.warning(f"Failed to load Trakt cache: {e}")
    
    def _save_cache(self):
        """Save trending movies to cache file"""
        try:
            data = {
                'trending_movies': [
                    {
                        'trakt_id': movie.trakt_id,
                        'title': movie.title,
                        'year': movie.year,
                        'slug': movie.slug,
                        'added_at': movie.added_at.isoformat(),
                        'last_updated': movie.last_updated.isoformat()
                    }
                    for movie in self.trending_movies.values()
                ],
                'previous_trending_ids': list(self.previous_trending_ids),
                'stats': self.stats
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save Trakt cache: {e}")
    
    def is_watching(self) -> bool:
        """Check if the watcher is currently running"""
        return self.watching_running
