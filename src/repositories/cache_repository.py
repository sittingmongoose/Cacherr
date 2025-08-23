"""
Cache repository implementation for PlexCacheUltra.

This module provides the CacheFileRepository class that implements the
CacheRepository interface using file-based JSON persistence. It manages
cache entry data, provides efficient querying capabilities, and maintains
cache statistics and metadata.

Key Features:
- File-based JSON persistence with atomic operations
- Efficient indexing for fast lookups and queries
- Cache statistics and analytics
- Age-based and access-pattern-based queries
- Thread-safe operations with proper locking
- Automatic backup and recovery capabilities
- Data integrity validation with checksums
"""

from typing import List, Dict, Optional, Any, Type
from datetime import datetime, timedelta
from pathlib import Path
import logging

from pydantic import BaseModel, Field

from ..core.repositories import CacheRepository, CacheEntry
from .base_repository import BaseFileRepository
from .exceptions import (
    DuplicateEntryError,
    EntryNotFoundError,
    RepositoryError,
    ValidationError,
    wrap_repository_error
)

logger = logging.getLogger(__name__)


class CacheData(BaseModel):
    """
    Root data model for cache repository persistence.
    
    This model defines the structure of the cache data file,
    containing all cache entries and metadata.
    """
    
    version: str = Field(default="1.0", description="Data format version")
    created_at: datetime = Field(default_factory=datetime.now, description="Repository creation time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last modification time")
    entries: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Cache entries indexed by file path"
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Cache statistics and metadata"
    )
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CacheFileRepository(BaseFileRepository[CacheEntry], CacheRepository):
    """
    File-based implementation of CacheRepository interface.
    
    This repository stores cache entries in a JSON file with efficient
    indexing and querying capabilities. It provides thread-safe operations,
    automatic backups, and comprehensive error handling.
    
    Features:
    - JSON file-based persistence with atomic operations
    - Efficient file path indexing for O(1) lookups
    - Cache statistics calculation and maintenance
    - Age-based and access-pattern queries
    - Thread-safe operations with file locking
    - Automatic backup creation and cleanup
    - Data integrity validation and error recovery
    
    Usage:
        cache_repo = CacheFileRepository(
            data_file=Path("/path/to/cache_data.json"),
            auto_backup=True
        )
        
        # Add cache entry
        entry = CacheEntry(
            file_path="/media/movie.mkv",
            cache_path="/cache/movie.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        cache_repo.add_cache_entry(entry)
        
        # Query entries
        entries = cache_repo.list_cache_entries(limit=10)
        stats = cache_repo.get_cache_statistics()
    """
    
    def __init__(
        self,
        data_file: Path,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        backup_retention_days: int = 30
    ):
        """
        Initialize cache file repository.
        
        Args:
            data_file: Path to cache data JSON file
            backup_dir: Directory for backup files
            auto_backup: Whether to automatically create backups
            backup_retention_days: Days to retain backup files
        """
        super().__init__(
            data_file=data_file,
            backup_dir=backup_dir,
            auto_backup=auto_backup,
            backup_retention_days=backup_retention_days,
            validate_on_load=True
        )
    
    def get_model_class(self) -> Type[CacheEntry]:
        """Get the Pydantic model class for cache entries."""
        return CacheEntry
    
    def get_default_data(self) -> Dict[str, Any]:
        """Get default data structure for new cache files."""
        return CacheData().model_dump()
    
    def _update_statistics(self, data: Dict[str, Any]) -> None:
        """
        Update cache statistics in the data structure.
        
        Args:
            data: Cache data dictionary to update
        """
        try:
            entries = data.get("entries", {})
            now = datetime.now()
            
            # Calculate basic statistics
            total_entries = len(entries)
            total_size = sum(entry.get("original_size", 0) for entry in entries.values())
            
            # Operation type counts
            operation_counts = {}
            for entry in entries.values():
                op_type = entry.get("operation_type", "unknown")
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            
            # Age statistics
            if entries:
                cache_times = [
                    datetime.fromisoformat(entry["cached_at"])
                    for entry in entries.values()
                    if "cached_at" in entry
                ]
                oldest_entry = min(cache_times) if cache_times else now
                newest_entry = max(cache_times) if cache_times else now
            else:
                oldest_entry = now
                newest_entry = now
            
            # Access statistics
            total_access_count = sum(entry.get("access_count", 0) for entry in entries.values())
            
            # Update statistics
            data["statistics"] = {
                "total_entries": total_entries,
                "total_size_bytes": total_size,
                "oldest_entry": oldest_entry.isoformat(),
                "newest_entry": newest_entry.isoformat(),
                "operation_counts": operation_counts,
                "total_access_count": total_access_count,
                "last_calculated": now.isoformat()
            }
            data["last_updated"] = now.isoformat()
            
        except Exception as e:
            logger.warning(f"Failed to update cache statistics: {e}")
    
    def _entry_to_dict(self, entry: CacheEntry) -> Dict[str, Any]:
        """Convert CacheEntry to dictionary for storage."""
        return entry.model_dump()
    
    def _dict_to_entry(self, data: Dict[str, Any]) -> CacheEntry:
        """Convert dictionary to CacheEntry."""
        return CacheEntry.model_validate(data)
    
    def add_cache_entry(self, entry: CacheEntry) -> bool:
        """
        Add a new cache entry to the repository.
        
        Args:
            entry: CacheEntry to add
            
        Returns:
            bool: True if entry added successfully
            
        Raises:
            DuplicateEntryError: When entry already exists
            ValidationError: When entry data is invalid
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            
            # Check for duplicate
            if entry.file_path in data["entries"]:
                raise DuplicateEntryError(
                    f"Cache entry already exists for file: {entry.file_path}",
                    duplicate_key=entry.file_path
                )
            
            # Add the entry
            data["entries"][entry.file_path] = self._entry_to_dict(entry)
            
            # Update statistics
            self._update_statistics(data)
            
            # Save data
            self.save_data(data, "add_entry")
            
            logger.info(f"Added cache entry: {entry.file_path}")
            return True
            
        except (DuplicateEntryError, ValidationError):
            raise  # Re-raise specific errors
        except Exception as e:
            raise wrap_repository_error(
                "cache entry addition",
                e,
                {"file_path": entry.file_path}
            )
    
    def get_cache_entry(self, file_path: str) -> Optional[CacheEntry]:
        """
        Retrieve a cache entry by file path.
        
        Args:
            file_path: Original file path to look up
            
        Returns:
            Optional[CacheEntry]: CacheEntry if found, None otherwise
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            entry_data = data["entries"].get(file_path)
            
            if entry_data is None:
                return None
            
            return self._dict_to_entry(entry_data)
            
        except Exception as e:
            raise wrap_repository_error(
                "cache entry retrieval",
                e,
                {"file_path": file_path}
            )
    
    def update_cache_entry(self, file_path: str, **updates) -> bool:
        """
        Update an existing cache entry.
        
        Args:
            file_path: File path of entry to update
            **updates: Fields to update
            
        Returns:
            bool: True if update successful
            
        Raises:
            EntryNotFoundError: When entry doesn't exist
            ValidationError: When update data is invalid
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            
            # Check if entry exists
            if file_path not in data["entries"]:
                raise EntryNotFoundError(
                    f"Cache entry not found for file: {file_path}",
                    missing_key=file_path
                )
            
            # Get current entry and update it
            entry_data = data["entries"][file_path]
            entry = self._dict_to_entry(entry_data)
            
            # Apply updates
            for field, value in updates.items():
                if hasattr(entry, field):
                    setattr(entry, field, value)
                else:
                    logger.warning(f"Unknown field in update: {field}")
            
            # Validate updated entry
            entry = CacheEntry.model_validate(entry.model_dump())
            
            # Store updated entry
            data["entries"][file_path] = self._entry_to_dict(entry)
            
            # Update statistics
            self._update_statistics(data)
            
            # Save data
            self.save_data(data, "update_entry")
            
            logger.info(f"Updated cache entry: {file_path}")
            return True
            
        except (EntryNotFoundError, ValidationError):
            raise  # Re-raise specific errors
        except Exception as e:
            raise wrap_repository_error(
                "cache entry update",
                e,
                {"file_path": file_path, "updates": updates}
            )
    
    def remove_cache_entry(self, file_path: str) -> bool:
        """
        Remove a cache entry from the repository.
        
        Args:
            file_path: File path of entry to remove
            
        Returns:
            bool: True if removal successful
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            
            # Remove entry if it exists
            removed = data["entries"].pop(file_path, None) is not None
            
            if removed:
                # Update statistics
                self._update_statistics(data)
                
                # Save data
                self.save_data(data, "remove_entry")
                
                logger.info(f"Removed cache entry: {file_path}")
            
            return removed
            
        except Exception as e:
            raise wrap_repository_error(
                "cache entry removal",
                e,
                {"file_path": file_path}
            )
    
    def list_cache_entries(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[Dict] = None
    ) -> List[CacheEntry]:
        """
        List cache entries with optional filtering and pagination.
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            filters: Optional filters to apply:
                - operation_type: Filter by operation type
                - min_size: Minimum file size
                - max_size: Maximum file size
                - cached_after: Cached after this date
                - cached_before: Cached before this date
                - has_checksum: Whether entry has checksum
                
        Returns:
            List[CacheEntry]: List of matching cache entries
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            entries = []
            
            # Convert all entries to objects
            for entry_data in data["entries"].values():
                try:
                    entry = self._dict_to_entry(entry_data)
                    entries.append(entry)
                except Exception as e:
                    logger.warning(f"Skipping invalid entry: {e}")
            
            # Apply filters
            if filters:
                entries = self._apply_filters(entries, filters)
            
            # Sort by cached_at (newest first)
            entries.sort(key=lambda x: x.cached_at, reverse=True)
            
            # Apply pagination
            if offset > 0:
                entries = entries[offset:]
            if limit is not None:
                entries = entries[:limit]
            
            return entries
            
        except Exception as e:
            raise wrap_repository_error(
                "cache entry listing",
                e,
                {"limit": limit, "offset": offset, "filters": filters}
            )
    
    def _apply_filters(self, entries: List[CacheEntry], filters: Dict) -> List[CacheEntry]:
        """Apply filters to cache entries."""
        filtered_entries = entries
        
        # Operation type filter
        if "operation_type" in filters:
            op_type = filters["operation_type"]
            filtered_entries = [e for e in filtered_entries if e.operation_type == op_type]
        
        # Size filters
        if "min_size" in filters:
            min_size = filters["min_size"]
            filtered_entries = [e for e in filtered_entries if e.original_size >= min_size]
        
        if "max_size" in filters:
            max_size = filters["max_size"]
            filtered_entries = [e for e in filtered_entries if e.original_size <= max_size]
        
        # Date filters
        if "cached_after" in filters:
            cached_after = filters["cached_after"]
            if isinstance(cached_after, str):
                cached_after = datetime.fromisoformat(cached_after)
            filtered_entries = [e for e in filtered_entries if e.cached_at >= cached_after]
        
        if "cached_before" in filters:
            cached_before = filters["cached_before"]
            if isinstance(cached_before, str):
                cached_before = datetime.fromisoformat(cached_before)
            filtered_entries = [e for e in filtered_entries if e.cached_at <= cached_before]
        
        # Checksum filter
        if "has_checksum" in filters:
            has_checksum = filters["has_checksum"]
            if has_checksum:
                filtered_entries = [e for e in filtered_entries if e.checksum is not None]
            else:
                filtered_entries = [e for e in filtered_entries if e.checksum is None]
        
        return filtered_entries
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics and summary information.
        
        Returns:
            Dict[str, Any]: Cache statistics
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            
            # Ensure statistics are up to date
            self._update_statistics(data)
            
            return data.get("statistics", {})
            
        except Exception as e:
            raise wrap_repository_error(
                "cache statistics retrieval",
                e,
                {}
            )
    
    def find_entries_by_age(self, max_age_hours: int) -> List[CacheEntry]:
        """
        Find cache entries older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            List[CacheEntry]: Entries older than max_age_hours
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            filters = {"cached_before": cutoff_time}
            return self.list_cache_entries(filters=filters)
            
        except Exception as e:
            raise wrap_repository_error(
                "age-based entry search",
                e,
                {"max_age_hours": max_age_hours}
            )
    
    def find_entries_by_access_pattern(self, min_days_since_access: int) -> List[CacheEntry]:
        """
        Find cache entries that haven't been accessed recently.
        
        Args:
            min_days_since_access: Minimum days since last access
            
        Returns:
            List[CacheEntry]: Entries not accessed recently
            
        Raises:
            RepositoryError: When data access fails
        """
        try:
            data = self.load_data()
            cutoff_time = datetime.now() - timedelta(days=min_days_since_access)
            
            old_access_entries = []
            
            for entry_data in data["entries"].values():
                try:
                    entry = self._dict_to_entry(entry_data)
                    
                    # Check if never accessed or not accessed recently
                    if (entry.last_accessed is None or 
                        entry.last_accessed < cutoff_time):
                        old_access_entries.append(entry)
                        
                except Exception as e:
                    logger.warning(f"Skipping invalid entry during access pattern search: {e}")
            
            # Sort by last accessed (oldest first)
            old_access_entries.sort(
                key=lambda x: x.last_accessed or datetime.min,
                reverse=False
            )
            
            return old_access_entries
            
        except Exception as e:
            raise wrap_repository_error(
                "access-pattern-based entry search",
                e,
                {"min_days_since_access": min_days_since_access}
            )
    
    def backup_cache_metadata(self, backup_path: Path) -> bool:
        """
        Create a backup of cache metadata.
        
        Args:
            backup_path: Path where backup should be stored
            
        Returns:
            bool: True if backup successful
            
        Raises:
            BackupError: When backup operation fails
        """
        return self.backup_data(backup_path)
    
    def restore_cache_metadata(self, backup_path: Path) -> bool:
        """
        Restore cache metadata from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore successful
            
        Raises:
            RestoreError: When restore operation fails
        """
        return self.restore_data(backup_path)
    
    def get_entries_by_operation_type(self, operation_type: str) -> List[CacheEntry]:
        """
        Get all cache entries for a specific operation type.
        
        Args:
            operation_type: Operation type to filter by
            
        Returns:
            List[CacheEntry]: Entries with matching operation type
        """
        filters = {"operation_type": operation_type}
        return self.list_cache_entries(filters=filters)
    
    def get_entries_by_size_range(
        self,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None
    ) -> List[CacheEntry]:
        """
        Get cache entries within a size range.
        
        Args:
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            
        Returns:
            List[CacheEntry]: Entries within size range
        """
        filters = {}
        if min_size is not None:
            filters["min_size"] = min_size
        if max_size is not None:
            filters["max_size"] = max_size
        
        return self.list_cache_entries(filters=filters)
    
    def update_access_time(self, file_path: str) -> bool:
        """
        Update the last accessed time for a cache entry.
        
        Args:
            file_path: File path of entry to update
            
        Returns:
            bool: True if update successful
        """
        now = datetime.now()
        return self.update_cache_entry(
            file_path,
            last_accessed=now,
            access_count=None  # Will be handled by the update logic
        )
    
    def increment_access_count(self, file_path: str) -> bool:
        """
        Increment the access count for a cache entry.
        
        Args:
            file_path: File path of entry to update
            
        Returns:
            bool: True if update successful
        """
        try:
            entry = self.get_cache_entry(file_path)
            if entry is None:
                return False
            
            return self.update_cache_entry(
                file_path,
                access_count=entry.access_count + 1,
                last_accessed=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to increment access count for {file_path}: {e}")
            return False