"""
Repository interfaces for PlexCacheUltra data access layer.

This module defines the repository interfaces that abstract data access
operations from the business logic. Repositories handle persistence,
caching of application state, and metrics collection while maintaining
clean separation of concerns.

Following the Repository pattern, these interfaces define contracts for
data access without specifying implementation details.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class CacheEntry(BaseModel):
    """Represents a cached file entry with metadata."""
    file_path: str
    cache_path: str
    original_size: int
    cached_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    operation_type: str  # "move", "copy", "symlink"
    checksum: Optional[str] = None


class WatchedItem(BaseModel):
    """Represents a watched media item."""
    file_path: str
    title: str
    watched_at: datetime
    user: str
    progress: float  # 0.0 to 1.0
    duration: Optional[int] = None  # in seconds
    media_type: str  # "movie", "episode", "show"


class UserActivity(BaseModel):
    """Represents user activity information."""
    username: str
    last_seen: datetime
    watch_count: int
    total_watch_time: int  # in seconds
    favorite_genres: List[str] = []
    is_active: bool = True


class MetricsData(BaseModel):
    """Represents performance and usage metrics."""
    timestamp: datetime
    operation_type: str
    files_processed: int
    bytes_processed: int
    duration_seconds: float
    success_rate: float
    errors: List[str] = []


class ConfigurationItem(BaseModel):
    """Represents a configuration setting."""
    section: str
    key: str
    value: Any
    last_updated: datetime
    updated_by: str = "system"
    is_persistent: bool = True


class CacheRepository(ABC):
    """
    Repository interface for cache data access and management.
    
    Handles persistence of cache state, file tracking, and cache metadata.
    Provides methods for querying cache contents and managing cache lifecycle.
    
    Raises:
        RepositoryError: When data access operations fail
        DataIntegrityError: When data consistency issues occur
    """
    
    @abstractmethod
    def add_cache_entry(self, entry: CacheEntry) -> bool:
        """
        Add a new cache entry to the repository.
        
        Args:
            entry: CacheEntry to add
            
        Returns:
            True if entry added successfully, False otherwise
            
        Raises:
            DuplicateEntryError: When entry already exists
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def get_cache_entry(self, file_path: str) -> Optional[CacheEntry]:
        """
        Retrieve a cache entry by file path.
        
        Args:
            file_path: Original file path to look up
            
        Returns:
            CacheEntry if found, None otherwise
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def update_cache_entry(self, file_path: str, **updates) -> bool:
        """
        Update an existing cache entry.
        
        Args:
            file_path: File path of entry to update
            **updates: Fields to update
            
        Returns:
            True if update successful, False otherwise
            
        Raises:
            EntryNotFoundError: When entry doesn't exist
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def remove_cache_entry(self, file_path: str) -> bool:
        """
        Remove a cache entry from the repository.
        
        Args:
            file_path: File path of entry to remove
            
        Returns:
            True if removal successful, False otherwise
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def list_cache_entries(self, limit: Optional[int] = None,
                          offset: int = 0, filters: Optional[Dict] = None) -> List[CacheEntry]:
        """
        List cache entries with optional filtering and pagination.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            filters: Optional filters to apply
            
        Returns:
            List of CacheEntry objects
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics and summary information.
        
        Returns:
            Dictionary with cache statistics including:
            - total_entries: Total number of cached files
            - total_size: Total size of cached files
            - oldest_entry: Timestamp of oldest cache entry
            - newest_entry: Timestamp of newest cache entry
            - operation_counts: Count by operation type
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def find_entries_by_age(self, max_age_hours: int) -> List[CacheEntry]:
        """
        Find cache entries older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            List of CacheEntry objects older than max_age_hours
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def find_entries_by_access_pattern(self, min_days_since_access: int) -> List[CacheEntry]:
        """
        Find cache entries that haven't been accessed recently.
        
        Args:
            min_days_since_access: Minimum days since last access
            
        Returns:
            List of CacheEntry objects not accessed recently
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def backup_cache_metadata(self, backup_path: Path) -> bool:
        """
        Create a backup of cache metadata.
        
        Args:
            backup_path: Path where backup should be stored
            
        Returns:
            True if backup successful, False otherwise
            
        Raises:
            BackupError: When backup operation fails
        """
        pass
    
    @abstractmethod
    def restore_cache_metadata(self, backup_path: Path) -> bool:
        """
        Restore cache metadata from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore successful, False otherwise
            
        Raises:
            RestoreError: When restore operation fails
        """
        pass


class ConfigRepository(ABC):
    """
    Repository interface for configuration management.
    
    Handles persistent storage and retrieval of configuration settings,
    supporting both environment variables and persistent configuration files.
    Manages configuration versioning and audit trails.
    
    Raises:
        ConfigurationError: When configuration operations fail
        ValidationError: When configuration validation fails
    """
    
    @abstractmethod
    def get_configuration(self, section: str, key: str) -> Optional[ConfigurationItem]:
        """
        Retrieve a configuration item.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            
        Returns:
            ConfigurationItem if found, None otherwise
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def set_configuration(self, item: ConfigurationItem) -> bool:
        """
        Store a configuration item.
        
        Args:
            item: ConfigurationItem to store
            
        Returns:
            True if storage successful, False otherwise
            
        Raises:
            ValidationError: When configuration item is invalid
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def get_section_configuration(self, section: str) -> Dict[str, Any]:
        """
        Retrieve all configuration items for a section.
        
        Args:
            section: Configuration section name
            
        Returns:
            Dictionary of key-value pairs for the section
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def update_configuration(self, section: str, key: str, value: Any,
                           updated_by: str = "system") -> bool:
        """
        Update a configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            value: New configuration value
            updated_by: Who/what updated the configuration
            
        Returns:
            True if update successful, False otherwise
            
        Raises:
            ValidationError: When configuration value is invalid
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def delete_configuration(self, section: str, key: str) -> bool:
        """
        Delete a configuration item.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def list_sections(self) -> List[str]:
        """
        List all configuration sections.
        
        Returns:
            List of section names
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def export_configuration(self, file_path: Path) -> bool:
        """
        Export configuration to a file.
        
        Args:
            file_path: Path where configuration should be exported
            
        Returns:
            True if export successful, False otherwise
            
        Raises:
            ExportError: When export operation fails
        """
        pass
    
    @abstractmethod
    def import_configuration(self, file_path: Path, merge: bool = True) -> bool:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to configuration file
            merge: If True, merge with existing config; if False, replace
            
        Returns:
            True if import successful, False otherwise
            
        Raises:
            ImportError: When import operation fails
            ValidationError: When imported configuration is invalid
        """
        pass
    
    @abstractmethod
    def get_configuration_history(self, section: str, key: str,
                                 limit: int = 10) -> List[ConfigurationItem]:
        """
        Get configuration change history.
        
        Args:
            section: Configuration section name
            key: Configuration key name
            limit: Maximum number of history entries to return
            
        Returns:
            List of ConfigurationItem objects representing change history
            
        Raises:
            RepositoryError: When data access fails
        """
        pass


class MetricsRepository(ABC):
    """
    Repository interface for metrics and statistics tracking.
    
    Handles collection, storage, and retrieval of performance metrics,
    usage statistics, and operational data. Supports time-series data
    and aggregation queries for monitoring and analytics.
    
    Raises:
        MetricsError: When metrics operations fail
        AggregationError: When data aggregation fails
    """
    
    @abstractmethod
    def record_metric(self, metric: MetricsData) -> bool:
        """
        Record a performance metric.
        
        Args:
            metric: MetricsData to record
            
        Returns:
            True if recording successful, False otherwise
            
        Raises:
            ValidationError: When metric data is invalid
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def get_metrics(self, operation_type: Optional[str] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[MetricsData]:
        """
        Retrieve metrics with optional filtering.
        
        Args:
            operation_type: Filter by operation type
            start_time: Filter metrics after this time
            end_time: Filter metrics before this time
            limit: Maximum number of metrics to return
            
        Returns:
            List of MetricsData objects
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def get_aggregated_metrics(self, operation_type: Optional[str] = None,
                              time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Get aggregated metrics for a time window.
        
        Args:
            operation_type: Filter by operation type
            time_window_hours: Time window for aggregation
            
        Returns:
            Dictionary with aggregated metrics including:
            - total_operations: Total number of operations
            - total_files: Total files processed
            - total_bytes: Total bytes processed
            - average_duration: Average operation duration
            - success_rate: Overall success rate
            - error_summary: Summary of errors
            
        Raises:
            AggregationError: When data aggregation fails
        """
        pass
    
    @abstractmethod
    def record_user_activity(self, activity: UserActivity) -> bool:
        """
        Record user activity information.
        
        Args:
            activity: UserActivity to record
            
        Returns:
            True if recording successful, False otherwise
            
        Raises:
            ValidationError: When activity data is invalid
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def get_user_activities(self, username: Optional[str] = None,
                           days_back: int = 30) -> List[UserActivity]:
        """
        Get user activity information.
        
        Args:
            username: Filter by specific username (None for all users)
            days_back: Number of days to look back
            
        Returns:
            List of UserActivity objects
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def record_watched_item(self, item: WatchedItem) -> bool:
        """
        Record a watched media item.
        
        Args:
            item: WatchedItem to record
            
        Returns:
            True if recording successful, False otherwise
            
        Raises:
            ValidationError: When watched item data is invalid
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def get_watched_items(self, user: Optional[str] = None,
                         media_type: Optional[str] = None,
                         days_back: int = 30) -> List[WatchedItem]:
        """
        Get watched media items.
        
        Args:
            user: Filter by specific user
            media_type: Filter by media type
            days_back: Number of days to look back
            
        Returns:
            List of WatchedItem objects
            
        Raises:
            RepositoryError: When data access fails
        """
        pass
    
    @abstractmethod
    def cleanup_old_metrics(self, retention_days: int = 90) -> int:
        """
        Clean up old metric data beyond retention period.
        
        Args:
            retention_days: Number of days to retain metrics
            
        Returns:
            Number of metric records deleted
            
        Raises:
            CleanupError: When cleanup operation fails
        """
        pass
    
    @abstractmethod
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """
        Get system health and performance metrics.
        
        Returns:
            Dictionary with system health metrics including:
            - disk_usage: Disk usage statistics
            - memory_usage: Memory usage statistics
            - operation_rates: Current operation rates
            - error_rates: Current error rates
            - cache_hit_rates: Cache performance metrics
            
        Raises:
            MetricsError: When unable to collect system metrics
        """
        pass