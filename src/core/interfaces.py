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


class OperationResult(BaseModel):
    """Represents a single file operation result."""
    id: str
    operation_id: str
    file_path: str
    filename: str
    source_path: str
    destination_path: Optional[str] = None
    operation_type: str  # cache, array, delete, copy, move
    status: str  # pending, processing, completed, failed, skipped
    reason: str  # watchlist, ondeck, watched, trakt, continue_watching, manual
    triggered_by_user: Optional[str] = None
    file_size_bytes: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    parent_operation_id: Optional[str] = None  # For batch operations


class BatchOperation(BaseModel):
    """Represents a batch operation containing multiple file operations."""
    id: str
    operation_type: str  # cache_batch, array_batch, cleanup_batch
    status: str  # pending, running, completed, failed, cancelled
    test_mode: bool
    triggered_by: str  # scheduler, manual, watcher
    triggered_by_user: Optional[str] = None
    reason: str  # scheduled, user_request, auto_cleanup, trakt_sync
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_files: int
    files_processed: int = 0
    files_successful: int = 0
    files_failed: int = 0
    total_size_bytes: int
    bytes_processed: int = 0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Additional context


class UserOperationContext(BaseModel):
    """Context for user-triggered operations."""
    user_id: Optional[str] = None
    plex_username: Optional[str] = None
    session_id: Optional[str] = None
    trigger_source: str  # web_ui, api, scheduler, watcher
    client_info: Optional[Dict[str, Any]] = None


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
                   config: Optional['FileOperationConfig'] = None) -> 'CacheOperationResult':
        """
        Move or copy files using atomic operations that never interrupt Plex playback.
        
        All operations use atomic cache redirection to ensure seamless Plex streaming:
        - Files are copied/moved to destination
        - Original files are atomically replaced with symlinks to cache
        - Plex seamlessly switches to reading from fast cache storage
        - Zero interruption to active playback sessions
        
        Args:
            files: List of files to process
            source_dir: Source directory path
            dest_dir: Destination directory path  
            config: FileOperationConfig with operation settings
            
        Returns:
            CacheOperationResult with detailed operation results
            
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


class ResultsService(ABC):
    """
    Interface for operation results tracking and management.
    
    Manages the lifecycle of operations, tracks file-level results,
    provides historical data, and supports multi-user attribution.
    Integrates with WebSocket for real-time updates.
    
    Raises:
        ResultsError: When results operations fail
        StorageError: When persistence operations fail
    """
    
    @abstractmethod
    def create_batch_operation(self, operation_type: str, test_mode: bool = False,
                             triggered_by: str = "manual", user_context: Optional[UserOperationContext] = None,
                             reason: str = "user_request", metadata: Optional[Dict[str, Any]] = None) -> BatchOperation:
        """
        Create a new batch operation.
        
        Args:
            operation_type: Type of batch operation
            test_mode: Whether this is a test mode operation
            triggered_by: Who/what triggered the operation
            user_context: User context if triggered by a user
            reason: Reason for the operation
            metadata: Additional operation metadata
            
        Returns:
            BatchOperation instance
        """
        pass
    
    @abstractmethod
    def add_file_operation(self, batch_id: str, file_path: str, operation_type: str,
                          reason: str, source_path: str, destination_path: Optional[str] = None,
                          file_size_bytes: int = 0, user_id: Optional[str] = None) -> OperationResult:
        """
        Add a file operation to a batch.
        
        Args:
            batch_id: ID of the parent batch operation
            file_path: Path to the file being operated on
            operation_type: Type of operation
            reason: Reason for the operation
            source_path: Source file path
            destination_path: Destination file path (if applicable)
            file_size_bytes: Size of the file
            user_id: User who triggered the operation
            
        Returns:
            OperationResult instance
        """
        pass
    
    @abstractmethod
    def update_operation_status(self, operation_id: str, status: str,
                               error_message: Optional[str] = None, 
                               completed_at: Optional[datetime] = None) -> bool:
        """
        Update the status of an operation.
        
        Args:
            operation_id: ID of the operation to update
            status: New status
            error_message: Error message if operation failed
            completed_at: Completion timestamp
            
        Returns:
            True if update successful
        """
        pass
    
    @abstractmethod
    def update_batch_progress(self, batch_id: str, files_processed: int,
                            files_successful: int, files_failed: int,
                            bytes_processed: int) -> bool:
        """
        Update batch operation progress.
        
        Args:
            batch_id: ID of the batch operation
            files_processed: Number of files processed
            files_successful: Number of successful operations
            files_failed: Number of failed operations
            bytes_processed: Bytes processed
            
        Returns:
            True if update successful
        """
        pass
    
    @abstractmethod
    def get_active_operations(self, user_id: Optional[str] = None) -> List[BatchOperation]:
        """
        Get currently active operations.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of active batch operations
        """
        pass
    
    @abstractmethod
    def get_operation_history(self, limit: int = 50, offset: int = 0,
                            user_id: Optional[str] = None,
                            operation_type: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Tuple[List[BatchOperation], int]:
        """
        Get operation history with pagination and filtering.
        
        Args:
            limit: Number of operations to return
            offset: Number of operations to skip
            user_id: Optional user filter
            operation_type: Optional operation type filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Tuple of (operations list, total count)
        """
        pass
    
    @abstractmethod
    def get_operation_details(self, operation_id: str) -> Tuple[BatchOperation, List[OperationResult]]:
        """
        Get detailed information about a specific operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Tuple of (batch operation, file operations list)
        """
        pass
    
    @abstractmethod
    def get_user_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get statistics for a specific user.
        
        Args:
            user_id: User ID
            days: Number of days to include in statistics
            
        Returns:
            Dictionary with user statistics
        """
        pass
    
    @abstractmethod
    def cleanup_old_results(self, days_to_keep: int = 90) -> int:
        """
        Clean up old operation results.
        
        Args:
            days_to_keep: Number of days of results to keep
            
        Returns:
            Number of operations cleaned up
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