import time
import threading
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from plexapi.server import PlexServer
from plexapi.video import Movie, Show, Episode
from plexapi.library import Library
from plexapi.myplex import MyPlexAccount
from plexapi.media import Media
from plexapi.exceptions import PlexApiException

class PlexWatcher:
    """Real-time Plex activity watcher for dynamic caching decisions"""
    
    def __init__(self, config, plex_operations, file_operations):
        self.config = config
        self.plex_operations = plex_operations
        self.file_operations = file_operations
        self.logger = logging.getLogger(__name__)
        
        self.watching = False
        self.watcher_thread = None
        self.last_activity_check = {}
        self.current_sessions = {}
        self.watch_history = {}
        self.callback = None
        
        # Cache removal scheduling
        self.cache_removal_schedule = {}  # media_key -> removal_timestamp
        self.removal_thread = None
        self.removal_running = False
        
        # User activity tracking
        self.user_last_activity = {}  # username -> last_activity_timestamp
        
        # Statistics
        self.stats = {
            'total_watches_detected': 0,
            'total_cache_operations': 0,
            'total_media_cached': 0,
            'total_media_removed': 0,
            'last_activity': None,
            'current_active_sessions': 0,
            'scheduled_removals': 0
        }
    
    def start_watching(self, callback: Optional[Callable] = None):
        """Start the real-time watching service"""
        if self.watching:
            self.logger.warning("Plex watcher is already running")
            return False
        
        self.callback = callback
        self.watching = True
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()
        
        # Start cache removal monitoring
        self._start_cache_removal_monitor()
        
        self.logger.info(f"Started Plex real-time watcher (check interval: {self.config.real_time_watch.check_interval}s)")
        return True
    
    def stop_watching(self):
        """Stop the real-time watching service"""
        if not self.watching:
            self.logger.warning("Plex watcher is not running")
            return False
        
        self.watching = False
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.watcher_thread.join(timeout=5)
        
        # Stop cache removal monitoring
        self._stop_cache_removal_monitor()
        
        self.logger.info("Stopped Plex real-time watcher")
        return True
    
    def is_watching(self) -> bool:
        """Check if the watcher is currently active"""
        return self.watching
    
    def get_stats(self) -> Dict:
        """Get current watcher statistics"""
        stats = self.stats.copy()
        stats['scheduled_removals'] = len(self.cache_removal_schedule)
        return stats
    
    def _start_cache_removal_monitor(self):
        """Start the cache removal monitoring thread"""
        if self.removal_running:
            return
        
        self.removal_running = True
        self.removal_thread = threading.Thread(target=self._cache_removal_loop, daemon=True)
        self.removal_thread.start()
        self.logger.info("Started cache removal monitor")
    
    def _stop_cache_removal_monitor(self):
        """Stop the cache removal monitoring thread"""
        if not self.removal_running:
            return
        
        self.removal_running = False
        if self.removal_thread and self.removal_thread.is_alive():
            self.removal_thread.join(timeout=5)
        self.logger.info("Stopped cache removal monitor")
    
    def _cache_removal_loop(self):
        """Monitor and execute scheduled cache removals"""
        while self.removal_running:
            try:
                current_time = time.time()
                removals_to_process = []
                
                # Check for items ready to be removed
                for media_key, removal_time in self.cache_removal_schedule.items():
                    if current_time >= removal_time:
                        removals_to_process.append(media_key)
                
                # Process removals
                for media_key in removals_to_process:
                    self._remove_media_from_cache(media_key)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in cache removal loop: {e}")
                time.sleep(60)
    
    def _schedule_cache_removal(self, media_key: str, media_title: str):
        """Schedule a media item for removal from cache"""
        if self.config.real_time_watch.remove_from_cache_after_hours <= 0:
            return  # No removal scheduled
        
        removal_time = time.time() + (self.config.real_time_watch.remove_from_cache_after_hours * 3600)
        self.cache_removal_schedule[media_key] = removal_time
        
        self.logger.info(f"Scheduled removal of {media_title} from cache in {self.config.real_time_watch.remove_from_cache_after_hours} hours")
        self.stats['scheduled_removals'] = len(self.cache_removal_schedule)
    
    def _remove_media_from_cache(self, media_key: str):
        """Remove a media item from cache"""
        try:
            # Remove from schedule
            if media_key in self.cache_removal_schedule:
                del self.cache_removal_schedule[media_key]
            
            # Here you would implement the actual cache removal logic
            # For now, we'll just log it
            self.logger.info(f"Removing media {media_key} from cache (scheduled removal)")
            
            # Update stats
            self.stats['total_media_removed'] += 1
            self.stats['scheduled_removals'] = len(self.cache_removal_schedule)
            
        except Exception as e:
            self.logger.error(f"Error removing media {media_key} from cache: {e}")
    
    def _check_user_activity(self, username: str) -> bool:
        """Check if a user has been active within the configured time period"""
        if self.config.real_time_watch.exclude_inactive_users_days <= 0:
            return True  # No inactivity check
        
        current_time = time.time()
        if username not in self.user_last_activity:
            return False  # User has never been active
        
        days_since_activity = (current_time - self.user_last_activity[username]) / 86400
        return days_since_activity <= self.config.real_time_watch.exclude_inactive_users_days
    
    def _update_user_activity(self, username: str):
        """Update the last activity timestamp for a user"""
        self.user_last_activity[username] = time.time()
    
    def _should_keep_in_cache_for_other_users(self, media) -> bool:
        """Check if media should remain in cache for other users' watchlists"""
        if not self.config.real_time_watch.respect_other_users_watchlists:
            return False
        
        try:
            # Get all users
            plex = self.plex_operations.get_plex_connection()
            if not plex:
                return False
            
            # Check if any other users have this media in their watchlist
            # This is a simplified check - you might want to implement more sophisticated logic
            for user in plex.users():
                if user.username != media.username:  # Skip the current user
                    # Check if media is in user's watchlist
                    # This would need to be implemented based on your watchlist logic
                    pass
            
            return False  # Placeholder - implement actual watchlist checking
            
        except Exception as e:
            self.logger.error(f"Error checking other users' watchlists: {e}")
            return False
    
    def _watch_loop(self):
        """Main watching loop that continuously monitors Plex activity"""
        while self.watching:
            try:
                self._check_plex_activity()
                time.sleep(self.config.real_time_watch.check_interval)
            except Exception as e:
                self.logger.error(f"Error in Plex watcher loop: {e}")
                time.sleep(10)  # Wait a bit before retrying
    
    def _check_plex_activity(self):
        """Check for new Plex activity and trigger appropriate actions"""
        try:
            # Get current sessions
            current_sessions = self._get_current_sessions()
            
            # Check for new watch activity
            new_activity = self._detect_new_activity(current_sessions)
            
            if new_activity:
                self._handle_new_activity(new_activity)
            
            # Update current sessions
            self.current_sessions = current_sessions
            self.stats['current_active_sessions'] = len(current_sessions)
            self.stats['last_activity'] = time.time()
            
        except Exception as e:
            self.logger.error(f"Error checking Plex activity: {e}")
    
    def _get_current_sessions(self) -> Dict:
        """Get current active Plex sessions"""
        try:
            plex = self.plex_operations.get_plex_connection()
            if not plex:
                return {}
            
            sessions = plex.sessions()
            session_data = {}
            
            for session in sessions:
                session_id = session.sessionKey
                username = session.username if hasattr(session, 'username') else 'Unknown'
                
                # Update user activity
                self._update_user_activity(username)
                
                session_data[session_id] = {
                    'user': username,
                    'media': session.media,
                    'state': session.state if hasattr(session, 'state') else 'unknown',
                    'progress': getattr(session, 'viewOffset', 0),
                    'duration': getattr(session, 'duration', 0),
                    'timestamp': time.time()
                }
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Error getting current sessions: {e}")
            return {}
    
    def _detect_new_activity(self, current_sessions: Dict) -> List[Dict]:
        """Detect new watch activity by comparing with previous sessions"""
        new_activity = []
        
        for session_id, session_data in current_sessions.items():
            if session_id not in self.last_activity_check:
                # New session started
                new_activity.append({
                    'type': 'session_started',
                    'session_id': session_id,
                    'data': session_data
                })
                self.stats['total_watches_detected'] += 1
            else:
                # Check for progress updates
                old_session = self.last_activity_check[session_id]
                if session_data['progress'] > old_session['progress']:
                    new_activity.append({
                        'type': 'progress_update',
                        'session_id': session_id,
                        'data': session_data,
                        'old_progress': old_session['progress']
                    })
        
        # Check for completed sessions
        for session_id in self.last_activity_check:
            if session_id not in current_sessions:
                # Session ended
                old_session = self.last_activity_check[session_id]
                if old_session['progress'] > 0:
                    new_activity.append({
                        'type': 'session_ended',
                        'session_id': session_id,
                        'data': old_session
                    })
        
        return new_activity
    
    def _handle_new_activity(self, new_activity: List[Dict]):
        """Handle new activity and trigger appropriate caching decisions"""
        for activity in new_activity:
            try:
                if activity['type'] == 'session_started' and self.config.real_time_watch.auto_cache_on_watch:
                    self._handle_session_started(activity)
                elif activity['type'] == 'session_ended' and self.config.real_time_watch.cache_on_complete:
                    self._handle_session_ended(activity)
                elif activity['type'] == 'progress_update':
                    self._handle_progress_update(activity)
                
                # Call callback if provided
                if self.callback:
                    self.callback(activity)
                    
            except Exception as e:
                self.logger.error(f"Error handling activity {activity['type']}: {e}")
    
    def _handle_session_started(self, activity: Dict):
        """Handle when a new viewing session starts"""
        session_data = activity['data']
        media = session_data['media']
        username = session_data['user']
        
        if not media:
            return
        
        # Check user inactivity
        if not self._check_user_activity(username):
            self.logger.debug(f"Skipping cache for {username} - user inactive for {self.config.real_time_watch.exclude_inactive_users_days} days")
            return
        
        # Check if we should cache this media based on existing rules
        if not self._should_cache_media(media, username):
            self.logger.debug(f"Skipping cache for media {media.title} (rules check failed)")
            return
        
        self.logger.info(f"New watch session started for {media.title} by {username}")
        
        # Trigger caching operation
        self._trigger_caching(media, f"Watch started by {username}")
        
        # Schedule removal from cache
        media_key = getattr(media, 'ratingKey', str(media))
        self._schedule_cache_removal(media_key, media.title)
    
    def _handle_session_ended(self, activity: Dict):
        """Handle when a viewing session ends"""
        session_data = activity['data']
        media = session_data['media']
        username = session_data['user']
        
        if not media:
            return
        
        # Check user inactivity
        if not self._check_user_activity(username):
            self.logger.debug(f"Skipping cache for {username} - user inactive for {self.config.real_time_watch.exclude_inactive_users_days} days")
            return
        
        # Check if media was watched significantly
        progress_percent = (session_data['progress'] / session_data['duration']) * 100 if session_data['duration'] > 0 else 0
        
        if progress_percent < 80:  # Only cache if watched more than 80%
            self.logger.debug(f"Session ended but progress was only {progress_percent:.1f}% - not caching")
            return
        
        if not self._should_cache_media(media, username):
            self.logger.debug(f"Skipping cache for completed media {media.title} (rules check failed)")
            return
        
        self.logger.info(f"Watch session completed for {media.title} by {username} ({progress_percent:.1f}% watched)")
        
        # Check if we should keep it in cache for other users
        if self._should_keep_in_cache_for_other_users(media):
            self.logger.info(f"Keeping {media.title} in cache for other users' watchlists")
            # Remove from removal schedule if it was scheduled
            media_key = getattr(media, 'ratingKey', str(media))
            if media_key in self.cache_removal_schedule:
                del self.cache_removal_schedule[media_key]
                self.stats['scheduled_removals'] = len(self.cache_removal_schedule)
        else:
            # Trigger caching operation
            self._trigger_caching(media, f"Watch completed by {username} ({progress_percent:.1f}% watched)")
            
            # Schedule removal from cache
            media_key = getattr(media, 'ratingKey', str(media))
            self._schedule_cache_removal(media_key, media.title)
    
    def _handle_progress_update(self, activity: Dict):
        """Handle progress updates during viewing"""
        # This could be used for more sophisticated caching decisions
        # For now, we'll just log significant progress milestones
        session_data = activity['data']
        old_progress = activity['old_progress']
        new_progress = session_data['progress']
        
        if session_data['duration'] > 0:
            old_percent = (old_progress / session_data['duration']) * 100
            new_percent = (new_progress / session_data['duration']) * 100
            
            # Log progress milestones
            if int(old_percent / 25) != int(new_percent / 25):
                self.logger.debug(f"Progress milestone: {session_data['media'].title} at {new_percent:.1f}%")
    
    def _should_cache_media(self, media, username: str) -> bool:
        """Check if media should be cached based on existing rules"""
        if not self.config.real_time_watch.respect_existing_rules:
            return True
        
        try:
            # Check user inclusion rules
            if self.config.media.users_toggle:
                # This would need to be implemented based on your user inclusion logic
                # For now, we'll assume all users are included
                pass
            
            # Check watchlist rules
            if self.config.media.watchlist_toggle:
                # Check if media is in user's watchlist
                # This would need to be implemented based on your watchlist logic
                pass
            
            # Check if media is already cached
            if self._is_media_cached(media):
                self.logger.debug(f"Media {media.title} is already cached")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking cache rules for {media.title}: {e}")
            return False
    
    def _is_media_cached(self, media) -> bool:
        """Check if media is already in cache"""
        try:
            # This would need to be implemented based on your cache checking logic
            # For now, we'll assume it's not cached
            return False
        except Exception as e:
            self.logger.error(f"Error checking if media is cached: {e}")
            return False
    
    def _trigger_caching(self, media, reason: str):
        """Trigger a caching operation for the specified media"""
        try:
            self.logger.info(f"Triggering cache for {media.title} - Reason: {reason}")
            
            # Add to watch history
            media_key = getattr(media, 'ratingKey', str(media))
            self.watch_history[media_key] = {
                'title': getattr(media, 'title', 'Unknown'),
                'type': type(media).__name__,
                'reason': reason,
                'timestamp': time.time()
            }
            
            # Update stats
            self.stats['total_cache_operations'] += 1
            self.stats['total_media_cached'] += 1
            
            # Here you would integrate with your existing caching engine
            # For now, we'll just log the action
            self.logger.info(f"Would cache {media.title} to {self.config.paths.cache_destination}")
            
        except Exception as e:
            self.logger.error(f"Error triggering cache for {media.title}: {e}")
    
    def get_watch_history(self) -> Dict:
        """Get the history of watched media"""
        return self.watch_history.copy()
    
    def clear_watch_history(self):
        """Clear the watch history"""
        self.watch_history.clear()
        self.stats['total_watches_detected'] = 0
        self.stats['total_cache_operations'] = 0
        self.stats['total_media_cached'] = 0
        self.stats['total_media_removed'] = 0
    
    def get_cache_removal_schedule(self) -> Dict:
        """Get the current cache removal schedule"""
        return self.cache_removal_schedule.copy()
    
    def get_user_activity_status(self) -> Dict:
        """Get the current user activity status"""
        current_time = time.time()
        user_status = {}
        
        for username, last_activity in self.user_last_activity.items():
            days_since = (current_time - last_activity) / 86400
            is_active = days_since <= self.config.real_time_watch.exclude_inactive_users_days
            user_status[username] = {
                'last_activity': last_activity,
                'days_since': days_since,
                'is_active': is_active
            }
        
        return user_status
