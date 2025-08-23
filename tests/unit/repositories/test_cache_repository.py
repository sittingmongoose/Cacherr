"""
Unit tests for cache repository implementation.

This module provides comprehensive tests for the CacheFileRepository
including data persistence, querying, statistics, and error handling.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import json
from unittest.mock import Mock, patch

from src.core.repositories import CacheRepository, CacheEntry
from src.repositories.cache_repository import CacheFileRepository, CacheData
from src.repositories.exceptions import (
    DuplicateEntryError, EntryNotFoundError, RepositoryError,
    ValidationError, DataIntegrityError
)


class TestCacheEntry:
    """Test cases for CacheEntry model."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation with required fields."""
        entry = CacheEntry(
            file_path="/media/movies/test.mkv",
            cache_path="/cache/test.mkv",
            original_size=1000000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        assert entry.file_path == "/media/movies/test.mkv"
        assert entry.cache_path == "/cache/test.mkv"
        assert entry.original_size == 1000000000
        assert entry.operation_type == "move"
        assert isinstance(entry.cached_at, datetime)
        assert entry.file_hash is None
        assert entry.metadata == {}
        assert entry.last_accessed is None
    
    def test_cache_entry_with_optional_fields(self):
        """Test CacheEntry creation with optional fields."""
        now = datetime.now()
        entry = CacheEntry(
            file_path="/media/movies/test.mkv",
            cache_path="/cache/test.mkv", 
            original_size=1000000000,
            cached_at=now,
            operation_type="copy",
            file_hash="abc123def456",
            metadata={"title": "Test Movie", "year": 2021},
            last_accessed=now
        )
        
        assert entry.file_hash == "abc123def456"
        assert entry.metadata["title"] == "Test Movie"
        assert entry.metadata["year"] == 2021
        assert entry.last_accessed == now
    
    def test_cache_entry_validation(self):
        """Test CacheEntry field validation."""
        # Test negative size validation
        with pytest.raises(Exception):  # Pydantic validation error
            CacheEntry(
                file_path="/test.mkv",
                cache_path="/cache/test.mkv",
                original_size=-1,  # Invalid
                cached_at=datetime.now(),
                operation_type="move"
            )
    
    def test_cache_entry_equality(self):
        """Test CacheEntry equality comparison."""
        entry1 = CacheEntry(
            file_path="/media/test.mkv",
            cache_path="/cache/test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        entry2 = CacheEntry(
            file_path="/media/test.mkv",  # Same file path
            cache_path="/cache/test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="copy"  # Different operation type
        )
        
        entry3 = CacheEntry(
            file_path="/media/different.mkv",  # Different file path
            cache_path="/cache/different.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        # Entries with same file_path should be equal
        assert entry1 == entry2
        assert entry1 != entry3


class TestCacheData:
    """Test cases for CacheData model."""
    
    def test_cache_data_creation(self):
        """Test CacheData creation with defaults."""
        data = CacheData()
        
        assert data.version == "1.0"
        assert isinstance(data.created_at, datetime)
        assert isinstance(data.last_updated, datetime)
        assert data.entries == {}
        assert data.statistics == {}
    
    def test_cache_data_serialization(self):
        """Test CacheData JSON serialization."""
        data = CacheData(
            entries={
                "/test.mkv": {
                    "cache_path": "/cache/test.mkv",
                    "original_size": 1000000,
                    "operation_type": "move"
                }
            },
            statistics={"total_files": 1, "total_size": 1000000}
        )
        
        json_str = data.json()
        assert "/test.mkv" in json_str
        assert "total_files" in json_str
        
        # Should be able to parse back
        parsed_data = CacheData.parse_raw(json_str)
        assert parsed_data.entries == data.entries
        assert parsed_data.statistics == data.statistics


class TestCacheFileRepository:
    """Test cases for CacheFileRepository."""
    
    def test_repository_creation(self, temp_dir: Path):
        """Test repository creation."""
        data_file = temp_dir / "cache_test.json"
        repo = CacheFileRepository(data_file=data_file)
        
        assert repo.data_file == data_file
        assert repo.auto_backup is True
        assert not data_file.exists()  # File not created until first write
    
    def test_add_cache_entry(self, test_cache_repository: CacheFileRepository):
        """Test adding cache entry."""
        repo = test_cache_repository
        entry = CacheEntry(
            file_path="/media/test.mkv",
            cache_path="/cache/test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        repo.add_cache_entry(entry)
        
        # Verify entry was added
        retrieved_entry = repo.get_cache_entry("/media/test.mkv")
        assert retrieved_entry is not None
        assert retrieved_entry.file_path == entry.file_path
        assert retrieved_entry.cache_path == entry.cache_path
    
    def test_add_duplicate_entry(self, test_cache_repository: CacheFileRepository):
        """Test adding duplicate cache entry raises error."""
        repo = test_cache_repository
        entry = CacheEntry(
            file_path="/media/duplicate.mkv",
            cache_path="/cache/duplicate.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        # Add first time - should succeed
        repo.add_cache_entry(entry)
        
        # Add second time - should raise error
        with pytest.raises(DuplicateEntryError):
            repo.add_cache_entry(entry)
    
    def test_get_cache_entry(self, test_cache_repository: CacheFileRepository):
        """Test getting cache entry by file path."""
        repo = test_cache_repository
        
        # Non-existent entry should return None
        result = repo.get_cache_entry("/nonexistent.mkv")
        assert result is None
        
        # Add entry and retrieve
        entry = CacheEntry(
            file_path="/media/get_test.mkv",
            cache_path="/cache/get_test.mkv",
            original_size=500000,
            cached_at=datetime.now(),
            operation_type="copy"
        )
        repo.add_cache_entry(entry)
        
        retrieved = repo.get_cache_entry("/media/get_test.mkv")
        assert retrieved is not None
        assert retrieved.file_path == entry.file_path
    
    def test_update_cache_entry(self, test_cache_repository: CacheFileRepository):
        """Test updating existing cache entry."""
        repo = test_cache_repository
        
        # Add initial entry
        entry = CacheEntry(
            file_path="/media/update_test.mkv",
            cache_path="/cache/update_test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        repo.add_cache_entry(entry)
        
        # Update entry
        updated_entry = CacheEntry(
            file_path="/media/update_test.mkv",  # Same path
            cache_path="/cache/update_test.mkv",
            original_size=1000000,
            cached_at=entry.cached_at,
            operation_type="move",
            last_accessed=datetime.now(),  # New field
            metadata={"updated": True}  # New metadata
        )
        repo.update_cache_entry(updated_entry)
        
        # Verify update
        retrieved = repo.get_cache_entry("/media/update_test.mkv")
        assert retrieved.last_accessed is not None
        assert retrieved.metadata["updated"] is True
    
    def test_update_nonexistent_entry(self, test_cache_repository: CacheFileRepository):
        """Test updating non-existent entry raises error."""
        repo = test_cache_repository
        
        entry = CacheEntry(
            file_path="/media/nonexistent.mkv",
            cache_path="/cache/nonexistent.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        with pytest.raises(EntryNotFoundError):
            repo.update_cache_entry(entry)
    
    def test_remove_cache_entry(self, test_cache_repository: CacheFileRepository):
        """Test removing cache entry."""
        repo = test_cache_repository
        
        # Add entry
        entry = CacheEntry(
            file_path="/media/remove_test.mkv",
            cache_path="/cache/remove_test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        repo.add_cache_entry(entry)
        
        # Remove entry
        success = repo.remove_cache_entry("/media/remove_test.mkv")
        assert success is True
        
        # Verify removal
        retrieved = repo.get_cache_entry("/media/remove_test.mkv")
        assert retrieved is None
    
    def test_remove_nonexistent_entry(self, test_cache_repository: CacheFileRepository):
        """Test removing non-existent entry returns False."""
        repo = test_cache_repository
        
        result = repo.remove_cache_entry("/media/nonexistent.mkv")
        assert result is False
    
    def test_list_cache_entries(self, test_cache_repository: CacheFileRepository, sample_cache_entries: list):
        """Test listing cache entries."""
        repo = test_cache_repository
        
        # Add sample entries
        for entry in sample_cache_entries:
            repo.add_cache_entry(entry)
        
        # List all entries
        all_entries = repo.list_cache_entries()
        assert len(all_entries) == 3
        
        # List with limit
        limited_entries = repo.list_cache_entries(limit=2)
        assert len(limited_entries) == 2
    
    def test_list_entries_by_age(self, test_cache_repository: CacheFileRepository):
        """Test listing entries by age."""
        repo = test_cache_repository
        now = datetime.now()
        
        # Add entries with different ages
        old_entry = CacheEntry(
            file_path="/media/old.mkv",
            cache_path="/cache/old.mkv",
            original_size=1000000,
            cached_at=now - timedelta(days=10),
            operation_type="move"
        )
        
        new_entry = CacheEntry(
            file_path="/media/new.mkv",
            cache_path="/cache/new.mkv",
            original_size=1000000,
            cached_at=now - timedelta(hours=1),
            operation_type="move"
        )
        
        repo.add_cache_entry(old_entry)
        repo.add_cache_entry(new_entry)
        
        # Get entries older than 5 days
        old_entries = repo.get_entries_older_than(timedelta(days=5))
        assert len(old_entries) == 1
        assert old_entries[0].file_path == "/media/old.mkv"
    
    def test_list_entries_by_size(self, test_cache_repository: CacheFileRepository):
        """Test listing entries by size criteria."""
        repo = test_cache_repository
        
        # Add entries with different sizes
        small_entry = CacheEntry(
            file_path="/media/small.mkv",
            cache_path="/cache/small.mkv",
            original_size=100000000,  # 100MB
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        large_entry = CacheEntry(
            file_path="/media/large.mkv",
            cache_path="/cache/large.mkv",
            original_size=5000000000,  # 5GB
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        repo.add_cache_entry(small_entry)
        repo.add_cache_entry(large_entry)
        
        # Get entries larger than 1GB
        large_entries = repo.get_entries_larger_than(1000000000)
        assert len(large_entries) == 1
        assert large_entries[0].file_path == "/media/large.mkv"
        
        # Get entries smaller than 1GB
        small_entries = repo.get_entries_smaller_than(1000000000)
        assert len(small_entries) == 1
        assert small_entries[0].file_path == "/media/small.mkv"
    
    def test_get_cache_statistics(self, test_cache_repository: CacheFileRepository, sample_cache_entries: list):
        """Test getting cache statistics."""
        repo = test_cache_repository
        
        # Add sample entries
        for entry in sample_cache_entries:
            repo.add_cache_entry(entry)
        
        stats = repo.get_cache_statistics()
        
        assert stats["total_files"] == 3
        assert stats["total_size"] == 4300000000  # Sum of all sizes
        assert "by_operation_type" in stats
        assert stats["by_operation_type"]["move"] == 2  # Two move operations
        assert stats["by_operation_type"]["copy"] == 1  # One copy operation
        assert "average_file_size" in stats
    
    def test_get_recently_accessed_entries(self, test_cache_repository: CacheFileRepository):
        """Test getting recently accessed entries."""
        repo = test_cache_repository
        now = datetime.now()
        
        # Add entries with different access times
        recent_entry = CacheEntry(
            file_path="/media/recent.mkv",
            cache_path="/cache/recent.mkv",
            original_size=1000000,
            cached_at=now - timedelta(days=5),
            operation_type="move",
            last_accessed=now - timedelta(hours=1)  # Recently accessed
        )
        
        old_access_entry = CacheEntry(
            file_path="/media/old_access.mkv",
            cache_path="/cache/old_access.mkv",
            original_size=1000000,
            cached_at=now - timedelta(days=5),
            operation_type="move",
            last_accessed=now - timedelta(days=10)  # Old access
        )
        
        no_access_entry = CacheEntry(
            file_path="/media/no_access.mkv",
            cache_path="/cache/no_access.mkv",
            original_size=1000000,
            cached_at=now - timedelta(days=5),
            operation_type="move"
            # No last_accessed
        )
        
        repo.add_cache_entry(recent_entry)
        repo.add_cache_entry(old_access_entry)
        repo.add_cache_entry(no_access_entry)
        
        # Get recently accessed entries (within last 5 days)
        recent_entries = repo.get_recently_accessed_entries(timedelta(days=5))
        assert len(recent_entries) == 1
        assert recent_entries[0].file_path == "/media/recent.mkv"
    
    def test_file_persistence(self, temp_dir: Path):
        """Test that data persists to file correctly."""
        data_file = temp_dir / "persistence_test.json"
        repo = CacheFileRepository(data_file=data_file, auto_backup=False)
        
        # Add entry
        entry = CacheEntry(
            file_path="/media/persist_test.mkv",
            cache_path="/cache/persist_test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        repo.add_cache_entry(entry)
        
        # Force save
        repo._save_data()
        
        # Verify file exists and contains data
        assert data_file.exists()
        
        # Load with new repository instance
        repo2 = CacheFileRepository(data_file=data_file, auto_backup=False)
        retrieved = repo2.get_cache_entry("/media/persist_test.mkv")
        
        assert retrieved is not None
        assert retrieved.file_path == entry.file_path
    
    def test_backup_creation(self, temp_dir: Path):
        """Test automatic backup creation."""
        data_file = temp_dir / "backup_test.json"
        repo = CacheFileRepository(data_file=data_file, auto_backup=True, backup_count=2)
        
        # Add entry to trigger file creation
        entry = CacheEntry(
            file_path="/media/backup_test.mkv",
            cache_path="/cache/backup_test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        repo.add_cache_entry(entry)
        
        # Force backup creation by adding more entries
        for i in range(3):
            test_entry = CacheEntry(
                file_path=f"/media/test_{i}.mkv",
                cache_path=f"/cache/test_{i}.mkv",
                original_size=1000000,
                cached_at=datetime.now(),
                operation_type="move"
            )
            repo.add_cache_entry(test_entry)
            repo._save_data()  # Force save to trigger backup
        
        # Check if backup files were created
        backup_files = list(temp_dir.glob("backup_test.json.backup.*"))
        assert len(backup_files) > 0
    
    def test_error_handling_corrupted_file(self, temp_dir: Path):
        """Test error handling with corrupted data file."""
        data_file = temp_dir / "corrupted_test.json"
        
        # Create corrupted JSON file
        with open(data_file, 'w') as f:
            f.write('{"invalid": json content')
        
        # Repository should handle corrupted file gracefully
        repo = CacheFileRepository(data_file=data_file, auto_backup=False)
        
        # Should start with empty data despite corrupted file
        entries = repo.list_cache_entries()
        assert len(entries) == 0
    
    def test_concurrent_access(self, temp_dir: Path):
        """Test repository behavior under concurrent access."""
        import threading
        import time
        
        data_file = temp_dir / "concurrent_test.json"
        repo = CacheFileRepository(data_file=data_file, auto_backup=False)
        
        results = []
        errors = []
        
        def add_entries(thread_id: int):
            try:
                for i in range(5):
                    entry = CacheEntry(
                        file_path=f"/media/thread_{thread_id}_file_{i}.mkv",
                        cache_path=f"/cache/thread_{thread_id}_file_{i}.mkv",
                        original_size=1000000,
                        cached_at=datetime.now(),
                        operation_type="move"
                    )
                    repo.add_cache_entry(entry)
                    results.append(f"thread_{thread_id}_file_{i}")
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=add_entries, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 15  # 3 threads * 5 entries each
        
        # Verify all entries were added
        all_entries = repo.list_cache_entries()
        assert len(all_entries) == 15


class TestCacheRepositoryEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_file_path(self, test_cache_repository: CacheFileRepository):
        """Test handling of empty file paths."""
        repo = test_cache_repository
        
        with pytest.raises(ValueError):
            CacheEntry(
                file_path="",  # Empty path
                cache_path="/cache/test.mkv",
                original_size=1000000,
                cached_at=datetime.now(),
                operation_type="move"
            )
    
    def test_very_large_files(self, test_cache_repository: CacheFileRepository):
        """Test handling of very large file sizes."""
        repo = test_cache_repository
        
        large_entry = CacheEntry(
            file_path="/media/huge_file.mkv",
            cache_path="/cache/huge_file.mkv",
            original_size=100000000000000,  # 100TB
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        # Should handle large sizes without issues
        repo.add_cache_entry(large_entry)
        retrieved = repo.get_cache_entry("/media/huge_file.mkv")
        assert retrieved.original_size == 100000000000000
    
    def test_special_characters_in_paths(self, test_cache_repository: CacheFileRepository):
        """Test handling of special characters in file paths."""
        repo = test_cache_repository
        
        special_entry = CacheEntry(
            file_path="/media/movies/Test Movie (2021) [4K]/movie file - special chars & symbols.mkv",
            cache_path="/cache/Test Movie (2021) [4K]/movie file - special chars & symbols.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        repo.add_cache_entry(special_entry)
        retrieved = repo.get_cache_entry("/media/movies/Test Movie (2021) [4K]/movie file - special chars & symbols.mkv")
        assert retrieved is not None
        assert retrieved.file_path == special_entry.file_path
    
    def test_unicode_paths(self, test_cache_repository: CacheFileRepository):
        """Test handling of Unicode characters in paths."""
        repo = test_cache_repository
        
        unicode_entry = CacheEntry(
            file_path="/media/movies/映画/テスト.mkv",  # Japanese characters
            cache_path="/cache/映画/テスト.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        
        repo.add_cache_entry(unicode_entry)
        retrieved = repo.get_cache_entry("/media/movies/映画/テスト.mkv")
        assert retrieved is not None
        assert retrieved.file_path == unicode_entry.file_path
    
    def test_repository_with_readonly_file(self, temp_dir: Path):
        """Test repository behavior with read-only data file."""
        data_file = temp_dir / "readonly_test.json"
        
        # Create initial file
        repo = CacheFileRepository(data_file=data_file, auto_backup=False)
        entry = CacheEntry(
            file_path="/media/readonly_test.mkv",
            cache_path="/cache/readonly_test.mkv",
            original_size=1000000,
            cached_at=datetime.now(),
            operation_type="move"
        )
        repo.add_cache_entry(entry)
        
        # Make file read-only
        import stat
        data_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        
        try:
            # Create new repository instance
            repo2 = CacheFileRepository(data_file=data_file, auto_backup=False)
            
            # Should be able to read existing data
            retrieved = repo2.get_cache_entry("/media/readonly_test.mkv")
            assert retrieved is not None
            
            # But adding new entry should raise error
            new_entry = CacheEntry(
                file_path="/media/new_test.mkv",
                cache_path="/cache/new_test.mkv",
                original_size=1000000,
                cached_at=datetime.now(),
                operation_type="move"
            )
            
            with pytest.raises(RepositoryError):
                repo2.add_cache_entry(new_entry)
                
        finally:
            # Restore write permissions for cleanup
            try:
                data_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            except:
                pass