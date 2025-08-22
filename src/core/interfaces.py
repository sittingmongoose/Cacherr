"""
Core service interfaces for PlexCacheUltra.

This module defines the foundational interfaces that establish clear contracts
for the major services within the PlexCacheUltra system. These interfaces
enable dependency injection, improve testability, and support modular
architecture patterns.

Each interface follows the Interface Segregation Principle, defining only
the methods that clients actually need.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from pydantic import BaseModel
from plexapi.server import PlexServer


class MediaFileInfo(BaseModel):
    """Information about a media file for type safety."""
    path: str
    size_bytes: int
    filename: str
    directory: str
    size_readable: str


class CacheOperationResult(BaseModel):
    """Result of a cache operation for type safety."""
    success: bool
    files_processed: int
    total_size_bytes: int
    total_size_readable: str
    operation_type: str
    errors: List[str] = []
    warnings: List[str] = []


class TestModeAnalysis(BaseModel):
    """Analysis results for test mode operations."""
    files: List[str]
    total_size: int
    total_size_readable: str
    file_details: List[MediaFileInfo]
    operation_type: str
    file_count: int


class NotificationEvent(BaseModel):
    """Represents a notification event for type safety."""
    level: str  # info, warning, error, success, summary
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class MediaService(ABC):
    """
    Interface for Plex media operations.
    
    Provides methods for fetching different types of media from Plex server,
    including onDeck content, watchlist items, and watched media. Handles
    connection management and error recovery.
    
    Raises:
        ConnectionError: When unable to connect to Plex server
        AuthenticationError: When Plex authentication fails
        MediaFetchError: When media fetching operations fail
    """
    
    @abstractmethod
    def set_plex_connection(self, plex: PlexServer) -> None:
        """
        Set the Plex server connection.
        
        Args:
            plex: Configured PlexServer instance
            
        Raises:
            ValueError: If plex connection is invalid
        """
        pass
    
    @abstractmethod
    def get_plex_connection(self) -> Optional[PlexServer]:
        """
        Get or establish Plex connection.
        
        Returns:
            PlexServer instance if connection successful, None otherwise
            
        Raises:
            ConnectionError: When unable to establish connection
        """
        pass
    
    @abstractmethod
    def fetch_ondeck_media(self) -> List[str]:
        """
        Fetch onDeck media from Plex.
        
        Returns list of file paths for onDeck content, including current episodes
        and next episodes in sequence. Filters content based on configured
        monitoring period.
        
        Returns:
            List of absolute file paths to onDeck media
            
        Raises:
            MediaFetchError: When unable to fetch onDeck content
        """
        pass
    
    @abstractmethod
    def fetch_watchlist_media(self) -> List[str]:
        """
        Fetch watchlist media from Plex.
        
        Returns file paths for items in user's Plex watchlist, limited by
        configuration settings for episodes per show.
        
        Returns:
            List of absolute file paths to watchlist media
            
        Raises:
            MediaFetchError: When unable to fetch watchlist content
        """
        pass
    
    @abstractmethod
    def fetch_watched_media(self) -> List[str]:
        """
        Fetch watched media from Plex.
        
        Returns file paths for media that has been marked as watched,
        used for moving content from cache back to array storage.
        
        Returns:
            List of absolute file paths to watched media
            
        Raises:
            MediaFetchError: When unable to fetch watched content
        """
        pass


class FileService(ABC):
    """
    Interface for file operations and management.
    
    Handles all file system operations including path processing, file movement,
    copying, symlink creation, and space management. Supports concurrent
    operations with configurable performance settings.
    
    Raises:
        FileOperationError: When file operations fail
        InsufficientSpaceError: When destination lacks required space
        PermissionError: When lacking file system permissions
    """
    
    @abstractmethod
    def process_file_paths(self, files: List[str]) -> List[str]:
        """
        Process file paths to convert from Plex paths to actual system paths.
        
        Converts Plex mount paths to real system paths using configured
        source mappings. Essential for Docker environments where Plex
        sees different paths than the host system.
        
        Args:
            files: List of Plex file paths to convert
            
        Returns:
            List of converted system file paths
            
        Raises:
            PathMappingError: When path conversion fails
        """
        pass
    
    @abstractmethod
    def scan_additional_sources(self, media_files: List[str]) -> List[str]:
        """
        Scan additional sources for media files.
        
        Searches configured additional source directories for media files
        that match the provided media files by stem name. Used for finding
        content on network shares or additional storage locations.
        
        Args:
            media_files: Reference files to match against
            
        Returns:
            List of matching files found in additional sources
            
        Raises:
            ScanError: When unable to scan additional sources
        """
        pass
    
    @abstractmethod
    def find_subtitle_files(self, media_files: List[str]) -> List[str]:
        """
        Find subtitle files for the given media files.
        
        Searches for subtitle files (srt, vtt, etc.) that correspond to
        the provided media files. Uses filename matching to associate
        subtitles with their media files.
        
        Args:
            media_files: List of media file paths to find subtitles for
            
        Returns:
            List of subtitle file paths
            
        Raises:
            SubtitleScanError: When subtitle scanning fails
        """
        pass
    
    @abstractmethod
    def filter_files_for_cache(self, files: List[str]) -> List[str]:
        """
        Filter files that should be moved to cache.
        
        Determines which files are eligible for cache movement based on
        current location, cache status, and configuration rules.
        
        Args:
            files: List of file paths to evaluate
            
        Returns:
            List of files that should be moved to cache
        """
        pass
    
    @abstractmethod
    def filter_files_for_array(self, files: List[str]) -> List[str]:
        """
        Filter files that should be moved to array.
        
        Determines which files should be moved from cache back to array
        storage, typically for watched content or cache cleanup.
        
        Args:
            files: List of file paths to evaluate
            
        Returns:
            List of files that should be moved to array
        """
        pass
    
    @abstractmethod
    def analyze_files_for_test_mode(self, files: List[str], operation_type: str = "cache") -> TestModeAnalysis:
        """
        Analyze files for test mode without performing operations.
        
        Provides detailed analysis of what would happen during file operations
        without actually moving files. Used for dry-run scenarios and planning.
        
        Args:
            files: List of file paths to analyze
            operation_type: Type of operation ("cache" or "array")
            
        Returns:
            TestModeAnalysis with detailed file information
            
        Raises:
            AnalysisError: When file analysis fails
        """
        pass
    
    @abstractmethod
    def check_available_space(self, files: List[str], destination: str) -> bool:
        """
        Check if there's enough space in the destination directory.
        
        Calculates total size of files and compares with available space
        in destination to prevent incomplete operations due to disk space.
        
        Args:
            files: List of files that would be moved
            destination: Destination directory path
            
        Returns:
            True if sufficient space available, False otherwise
            
        Raises:
            SpaceCheckError: When unable to check available space
        """
        pass
    
    @abstractmethod
    def move_files(self, files: List[str], source_dir: str, dest_dir: str,
                   max_concurrent: Optional[int] = None, dry_run: bool = False,
                   copy_mode: bool = False, create_symlinks: bool = False,
                   move_with_symlinks: bool = False) -> Tuple[int, int]:
        """
        Move or copy files with concurrent operations.
        
        Performs file operations with configurable concurrency and operation
        modes. Supports move, copy, symlink creation, and hybrid move+symlink.
        
        Args:
            files: List of files to process
            source_dir: Source directory path
            dest_dir: Destination directory path
            max_concurrent: Maximum concurrent operations (None for auto-detect)
            dry_run: If True, don't actually move files
            copy_mode: If True, copy instead of move
            create_symlinks: If True, create symlinks instead of moving
            move_with_symlinks: If True, move and create symlinks back
            
        Returns:
            Tuple of (files_processed, total_bytes_moved)
            
        Raises:
            FileOperationError: When file operations fail
            ConcurrencyError: When concurrent operations fail
        """
        pass
    
    @abstractmethod
    def delete_files(self, files: List[str], max_concurrent: Optional[int] = None) -> Tuple[int, int]:
        """
        Delete files with concurrent operations.
        
        Safely deletes files with configurable concurrency settings.
        Used for cache cleanup and watched content removal.
        
        Args:
            files: List of file paths to delete
            max_concurrent: Maximum concurrent deletions
            
        Returns:
            Tuple of (files_deleted, total_bytes_freed)
            
        Raises:
            DeletionError: When file deletion fails
        """
        pass
    
    @abstractmethod
    def get_file_size_readable(self, size_bytes: int) -> str:
        """
        Convert file size to human readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Human readable size string (e.g., "1.5GB")
        """
        pass


class NotificationService(ABC):
    """
    Interface for notification management.
    
    Handles sending notifications through various channels including webhooks,
    Discord, Slack, and system notifications. Supports different notification
    levels and structured messaging.
    
    Raises:
        NotificationError: When notification sending fails
        ConfigurationError: When notification configuration is invalid
    """
    
    @abstractmethod
    def send_notification(self, message: str, level: str = "info") -> bool:
        """
        Send a notification using the configured method.
        
        Args:
            message: Notification message content
            level: Notification level (info, warning, error, success, summary)
            
        Returns:
            True if notification sent successfully, False otherwise
            
        Raises:
            NotificationError: When notification sending fails
        """
        pass
    
    @abstractmethod
    def send_summary_notification(self, message: str) -> bool:
        """
        Send a summary notification.
        
        Args:
            message: Summary message content
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_error_notification(self, message: str, details: Optional[Dict] = None) -> bool:
        """
        Send an error notification.
        
        Args:
            message: Error message content
            details: Optional additional error details
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_warning_notification(self, message: str) -> bool:
        """
        Send a warning notification.
        
        Args:
            message: Warning message content
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_success_notification(self, message: str) -> bool:
        """
        Send a success notification.
        
        Args:
            message: Success message content
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_cache_operation_notification(self, operation_type: str, details: Dict) -> bool:
        """
        Send a structured cache operation notification.
        
        Args:
            operation_type: Type of cache operation performed
            details: Operation details including file counts and sizes
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_webhook_config(self) -> bool:
        """
        Validate webhook configuration.
        
        Returns:
            True if webhook configuration is valid, False otherwise
        """
        pass


class CacheService(ABC):
    """
    Interface for cache management operations.
    
    Manages the caching lifecycle including cache population, cleanup,
    and statistics tracking. Coordinates between file operations and
    configuration to implement caching policies.
    
    Raises:
        CacheError: When cache operations fail
        CacheFullError: When cache space is insufficient
    """
    
    @abstractmethod
    def execute_cache_operation(self, files: List[str], operation_type: str,
                               dry_run: bool = False) -> CacheOperationResult:
        """
        Execute a cache operation on the provided files.
        
        Args:
            files: List of file paths to process
            operation_type: Type of operation ("cache", "array", "delete")
            dry_run: If True, perform analysis without actual operations
            
        Returns:
            CacheOperationResult with operation details and statistics
            
        Raises:
            CacheError: When cache operation fails
            ValidationError: When input validation fails
        """
        pass
    
    @abstractmethod
    def analyze_cache_impact(self, files: List[str], operation_type: str) -> TestModeAnalysis:
        """
        Analyze the impact of a cache operation without executing it.
        
        Args:
            files: List of file paths to analyze
            operation_type: Type of operation to analyze
            
        Returns:
            TestModeAnalysis with detailed impact analysis
        """
        pass
    
    @abstractmethod
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get current cache statistics and usage information.
        
        Returns:
            Dictionary containing cache statistics including:
            - Current usage
            - Available space
            - File counts
            - Recent operations
            
        Raises:
            StatisticsError: When unable to gather statistics
        """
        pass
    
    @abstractmethod
    def validate_cache_space(self, required_bytes: int) -> bool:
        """
        Validate that sufficient cache space is available.
        
        Args:
            required_bytes: Number of bytes required for operation
            
        Returns:
            True if sufficient space available, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup_cache(self, max_age_hours: Optional[int] = None) -> CacheOperationResult:
        """
        Clean up old or watched content from cache.
        
        Args:
            max_age_hours: Maximum age for cache files (None for default)
            
        Returns:
            CacheOperationResult with cleanup statistics
            
        Raises:
            CleanupError: When cache cleanup fails
        """
        pass