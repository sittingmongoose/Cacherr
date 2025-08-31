"""
Comprehensive unit tests for FileOperations service.

This test suite covers all FileOperations functionality including:
- File path processing and mapping
- Atomic file operations (copy/move)
- Cache directory management
- Subtitle file handling
- Concurrent operations
- Error handling and edge cases
- Performance benchmarking

All tests use comprehensive mocking and temporary directories
to avoid filesystem side effects while maintaining full coverage.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

import pytest

# Import the service and models
import sys
sys.path.append('/mnt/user/Cursor/Cacherr/src')

from core.file_operations import (
    FileOperations,
    FileOperationConfig,
    FileOperationResult
)
from config.settings import Config


@pytest.mark.unit
class TestFileOperationConfig:
    """Test Pydantic models for file operation configuration."""

    def test_valid_config_creation(self):
        """Test creation of valid FileOperationConfig."""
        config = FileOperationConfig(
            max_concurrent=5,
            dry_run=False,
            copy_mode=True
        )

        assert config.max_concurrent == 5
        assert config.dry_run is False
        assert config.copy_mode is True

    def test_config_with_defaults(self):
        """Test config with default values."""
        config = FileOperationConfig()

        assert config.max_concurrent is None
        assert config.dry_run is False
        assert config.copy_mode is False

    def test_frozen_model_immutability(self):
        """Test that FileOperationConfig is immutable."""
        config = FileOperationConfig(dry_run=True)

        # Attempting to modify should raise ValidationError
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            config.dry_run = False


@pytest.mark.unit
class TestFileOperationResult:
    """Test file operation result model."""

    def test_success_result(self):
        """Test successful file operation result."""
        result = FileOperationResult(
            success=True,
            file_size=1000000,
            source_path="/source/file.mp4",
            destination_path="/dest/file.mp4"
        )

        assert result.success is True
        assert result.file_size == 1000000
        assert result.source_path == "/source/file.mp4"
        assert result.destination_path == "/dest/file.mp4"
        assert result.error_message is None

    def test_failure_result(self):
        """Test failed file operation result."""
        result = FileOperationResult(
            success=False,
            file_size=0,
            source_path="/source/file.mp4",
            destination_path="/dest/file.mp4",
            error_message="File not found"
        )

        assert result.success is False
        assert result.error_message == "File not found"


@pytest.mark.unit
class TestFileOperations:
    """Comprehensive test suite for FileOperations service."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        config = Mock(spec=Config)

        # Mock paths configuration
        config.paths = Mock()
        config.paths.plex_source = "/plex"
        config.paths.cache_destination = "/cache"
        config.paths.additional_sources = ["/nas1", "/nas2"]
        config.paths.additional_plex_sources = ["/plexnas1", "/plexnas2"]

        return config

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for file operations."""
        temp_path = Path(tempfile.mkdtemp(prefix="cacherr_test_"))
        try:
            yield temp_path
        finally:
            shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def file_operations(self, mock_config):
        """Create FileOperations instance with mock config."""
        return FileOperations(mock_config)

    def test_initialization(self, file_operations, mock_config):
        """Test FileOperations initialization."""
        assert file_operations.config == mock_config
        assert hasattr(file_operations, 'logger')
        assert file_operations.subtitle_extensions == [".srt", ".vtt", ".sbv", ".sub", ".idx"]

    def test_process_file_paths_empty_list(self, file_operations):
        """Test process_file_paths with empty input."""
        result = file_operations.process_file_paths([])
        assert result == []

    def test_process_file_paths_none_input(self, file_operations):
        """Test process_file_paths with None input."""
        result = file_operations.process_file_paths(None)
        assert result == []

    def test_process_file_paths_whitespace_only(self, file_operations):
        """Test process_file_paths filters out whitespace-only entries."""
        input_files = ["/valid/path.mp4", "", "   ", "\t", "/another/valid.mp4"]
        result = file_operations.process_file_paths(input_files)

        assert len(result) == 2
        assert "/valid/path.mp4" in result
        assert "/another/valid.mp4" in result

    def test_process_file_paths_basic_mapping(self, file_operations, mock_config):
        """Test basic Plex to system path mapping."""
        # Mock the config to have simple mapping
        mock_config.paths.plex_source = "/plex"
        mock_config.paths.additional_sources = []
        mock_config.paths.additional_plex_sources = []

        # Create a Docker-style hardcoded mapping
        with patch.object(file_operations, '_get_docker_source_mapping', return_value={
            "/plex": "/mediasource"
        }):
            input_files = ["/plex/movies/movie.mp4", "/plex/tv/show.mp4"]
            result = file_operations.process_file_paths(input_files)

            assert len(result) == 2
            assert "/mediasource/movies/movie.mp4" in result
            assert "/mediasource/tv/show.mp4" in result

    def test_process_file_paths_additional_sources(self, file_operations, mock_config):
        """Test mapping with additional source paths."""
        input_files = ["/plexnas1/movies/movie.mp4", "/plexnas2/tv/show.mp4"]
        result = file_operations.process_file_paths(input_files)

        assert len(result) == 2
        assert "/nas1/movies/movie.mp4" in result
        assert "/nas2/tv/show.mp4" in result

    def test_process_file_paths_no_mapping_found(self, file_operations, mock_config):
        """Test handling of paths that don't match any mapping."""
        input_files = ["/unknown/path/movie.mp4"]
        result = file_operations.process_file_paths(input_files)

        # Should return original path if no mapping found
        assert len(result) == 1
        assert "/unknown/path/movie.mp4" in result

    def test_process_file_paths_mixed_mappings(self, file_operations, mock_config):
        """Test processing files with mixed mapping requirements."""
        input_files = [
            "/plex/movies/movie1.mp4",      # Maps to /mediasource
            "/plexnas1/movies/movie2.mp4",  # Maps to /nas1
            "/unknown/movie3.mp4",          # No mapping
        ]

        with patch.object(file_operations, '_get_docker_source_mapping', return_value={
            "/plex": "/mediasource"
        }):
            result = file_operations.process_file_paths(input_files)

            assert len(result) == 3
            assert "/mediasource/movies/movie1.mp4" in result
            assert "/nas1/movies/movie2.mp4" in result
            assert "/unknown/movie3.mp4" in result

    def test_get_docker_source_mapping(self, file_operations, mock_config):
        """Test Docker source mapping generation."""
        mapping = file_operations._get_docker_source_mapping()

        expected = {
            "/plex": "/mediasource",
            "/plexnas1": "/nas1",
            "/plexnas2": "/nas2"
        }

        assert mapping == expected

    def test_get_docker_source_mapping_empty_additional(self, file_operations):
        """Test Docker mapping with no additional sources."""
        # Mock config with no additional sources
        file_operations.config.paths.additional_sources = []
        file_operations.config.paths.additional_plex_sources = []

        mapping = file_operations._get_docker_source_mapping()

        expected = {
            "/plex": "/mediasource"
        }

        assert mapping == expected

    def test_get_docker_source_mapping_mismatched_lengths(self, file_operations, mock_config):
        """Test handling of mismatched additional source lengths."""
        # Mock mismatched lengths
        mock_config.paths.additional_sources = ["/nas1"]
        mock_config.paths.additional_plex_sources = ["/plexnas1", "/plexnas2"]

        with patch.object(file_operations.logger, 'warning') as mock_warning:
            mapping = file_operations._get_docker_source_mapping()

            # Should use shorter length
            expected = {
                "/plex": "/mediasource",
                "/plexnas1": "/nas1"
            }

            assert mapping == expected
            mock_warning.assert_called_once()

    def test_copy_file_atomic_success(self, file_operations, temp_dir):
        """Test successful atomic file copy operation."""
        # Create source and destination directories
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create test file
        test_file = source_dir / "test.mp4"
        test_content = b"test video content" * 1000  # Larger content
        test_file.write_bytes(test_content)

        source_path = str(test_file)
        dest_path = str(dest_dir / "test.mp4")

        result = file_operations.copy_file_atomic(source_path, dest_path)

        assert result.success is True
        assert result.file_size == len(test_content)
        assert result.source_path == source_path
        assert result.destination_path == dest_path

        # Verify file was copied
        assert (dest_dir / "test.mp4").exists()
        assert (dest_dir / "test.mp4").read_bytes() == test_content

    def test_copy_file_atomic_source_not_found(self, file_operations, temp_dir):
        """Test atomic copy with non-existent source file."""
        dest_dir = temp_dir / "dest"
        dest_dir.mkdir()

        source_path = str(temp_dir / "nonexistent.mp4")
        dest_path = str(dest_dir / "test.mp4")

        result = file_operations.copy_file_atomic(source_path, dest_path)

        assert result.success is False
        assert "Source file does not exist" in result.error_message
        assert not (dest_dir / "test.mp4").exists()

    def test_copy_file_atomic_destination_exists(self, file_operations, temp_dir):
        """Test atomic copy when destination already exists."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create source file
        source_file = source_dir / "test.mp4"
        source_file.write_text("source content")

        # Create existing destination file
        dest_file = dest_dir / "test.mp4"
        dest_file.write_text("existing content")

        result = file_operations.copy_file_atomic(str(source_file), str(dest_file))

        assert result.success is False
        assert "Destination already exists" in result.error_message
        # Original destination content should be preserved
        assert dest_file.read_text() == "existing content"

    def test_copy_file_atomic_dry_run(self, file_operations, temp_dir):
        """Test atomic copy in dry-run mode."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create test file
        test_file = source_dir / "test.mp4"
        test_file.write_text("test content")

        # Configure dry run
        config = FileOperationConfig(dry_run=True)

        result = file_operations.copy_file_atomic(
            str(test_file),
            str(dest_dir / "test.mp4"),
            config
        )

        assert result.success is True
        assert result.file_size == len("test content")
        # File should not actually be copied in dry run
        assert not (dest_dir / "test.mp4").exists()

    def test_move_file_atomic_success(self, file_operations, temp_dir):
        """Test successful atomic file move operation."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create test file
        test_file = source_dir / "test.mp4"
        test_content = b"test video content"
        test_file.write_bytes(test_content)

        source_path = str(test_file)
        dest_path = str(dest_dir / "test.mp4")

        result = file_operations.move_file_atomic(source_path, dest_path)

        assert result.success is True
        assert result.file_size == len(test_content)
        assert result.source_path == source_path
        assert result.destination_path == dest_path

        # Verify file was moved (not copied)
        assert not test_file.exists()
        assert (dest_dir / "test.mp4").exists()
        assert (dest_dir / "test.mp4").read_bytes() == test_content

    def test_move_file_atomic_same_directory(self, file_operations, temp_dir):
        """Test atomic move within same directory."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        # Create test file
        test_file = source_dir / "test.mp4"
        test_file.write_text("test content")

        source_path = str(test_file)
        dest_path = str(source_dir / "renamed.mp4")

        result = file_operations.move_file_atomic(source_path, dest_path)

        assert result.success is True
        assert not test_file.exists()
        assert (source_dir / "renamed.mp4").exists()

    def test_create_cache_directory_success(self, file_operations, temp_dir):
        """Test successful cache directory creation."""
        cache_path = temp_dir / "cache" / "subdir"
        result = file_operations.create_cache_directory(str(cache_path))

        assert result is True
        assert cache_path.exists()
        assert cache_path.is_dir()

    def test_create_cache_directory_already_exists(self, file_operations, temp_dir):
        """Test cache directory creation when directory already exists."""
        cache_path = temp_dir / "existing"
        cache_path.mkdir()

        result = file_operations.create_cache_directory(str(cache_path))

        assert result is True
        assert cache_path.exists()

    def test_create_cache_directory_permission_error(self, file_operations):
        """Test cache directory creation with permission error."""
        # Try to create directory in root (should fail without permissions)
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            result = file_operations.create_cache_directory("/root/forbidden")

            assert result is False

    def test_get_file_info_success(self, file_operations, temp_dir):
        """Test successful file info retrieval."""
        # Create test file
        test_file = temp_dir / "test.mp4"
        test_content = b"x" * 1000  # 1000 bytes
        test_file.write_bytes(test_content)

        file_info = file_operations.get_file_info(str(test_file))

        assert file_info is not None
        assert file_info.file_path == str(test_file)
        assert file_info.filename == "test.mp4"
        assert file_info.file_size_bytes == 1000
        assert file_info.file_size_readable == "1.0 KB"

    def test_get_file_info_not_found(self, file_operations):
        """Test file info retrieval for non-existent file."""
        file_info = file_operations.get_file_info("/nonexistent/file.mp4")

        assert file_info is None

    def test_validate_cache_space_success(self, file_operations, temp_dir):
        """Test successful cache space validation."""
        # Create cache directory with sufficient space
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()

        # Create a small test file
        test_file = temp_dir / "test.mp4"
        test_file.write_text("x" * 100)  # Small file

        result = file_operations.validate_cache_space(str(cache_dir), str(test_file))

        assert result is True

    def test_validate_cache_space_insufficient(self, file_operations, temp_dir):
        """Test cache space validation with insufficient space."""
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()

        # Create a very large file (simulate)
        test_file = temp_dir / "large.mp4"
        test_file.write_text("x" * 1000000)  # 1MB file

        # Mock statvfs to return very little free space
        with patch('os.statvfs') as mock_statvfs:
            mock_statvfs.return_value.f_bavail = 100  # Very little space
            mock_statvfs.return_value.f_frsize = 1024

            result = file_operations.validate_cache_space(str(cache_dir), str(test_file))

            assert result is False

    def test_find_subtitle_files(self, file_operations, temp_dir):
        """Test subtitle file discovery."""
        # Create media file and subtitle files
        media_file = temp_dir / "movie.mp4"
        media_file.write_text("video content")

        subtitle_files = [
            temp_dir / "movie.srt",
            temp_dir / "movie.vtt",
            temp_dir / "movie.sub",  # Should be found
            temp_dir / "movie.txt",  # Should not be found
        ]

        for sub_file in subtitle_files:
            sub_file.write_text("subtitle content")

        found_subs = file_operations.find_subtitle_files(str(media_file))

        expected_subs = [
            str(temp_dir / "movie.srt"),
            str(temp_dir / "movie.vtt"),
            str(temp_dir / "movie.sub")
        ]

        assert len(found_subs) == 3
        for expected_sub in expected_subs:
            assert expected_sub in found_subs

    def test_find_subtitle_files_no_subtitles(self, file_operations, temp_dir):
        """Test subtitle discovery when no subtitle files exist."""
        media_file = temp_dir / "movie.mp4"
        media_file.write_text("video content")

        found_subs = file_operations.find_subtitle_files(str(media_file))

        assert found_subs == []

    def test_cleanup_temp_files(self, file_operations, temp_dir):
        """Test cleanup of temporary files."""
        # Create some temp files
        temp_files = []
        for i in range(3):
            temp_file = temp_dir / f"temp_{i}.tmp"
            temp_file.write_text(f"temp content {i}")
            temp_files.append(str(temp_file))

        # Create a non-temp file that should not be deleted
        keep_file = temp_dir / "keep.mp4"
        keep_file.write_text("keep this")

        result = file_operations.cleanup_temp_files(str(temp_dir))

        assert result == 3  # 3 temp files deleted

        # Verify temp files are gone
        for temp_file in temp_files:
            assert not Path(temp_file).exists()

        # Verify non-temp file is still there
        assert keep_file.exists()

    def test_get_directory_stats(self, file_operations, temp_dir):
        """Test directory statistics calculation."""
        # Create test directory structure
        movies_dir = temp_dir / "movies"
        movies_dir.mkdir()

        # Create some files
        files = []
        total_size = 0
        for i in range(5):
            file_path = movies_dir / f"movie_{i}.mp4"
            size = (i + 1) * 1000  # Different sizes
            file_path.write_bytes(b"x" * size)
            files.append(str(file_path))
            total_size += size

        stats = file_operations.get_directory_stats(str(movies_dir))

        assert stats.total_files == 5
        assert stats.total_size_bytes == total_size
        assert stats.total_size_readable.endswith("KB")
        assert len(stats.file_list) == 5
        assert all(f in stats.file_list for f in files)

    def test_get_directory_stats_empty_directory(self, file_operations, temp_dir):
        """Test directory stats for empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        stats = file_operations.get_directory_stats(str(empty_dir))

        assert stats.total_files == 0
        assert stats.total_size_bytes == 0
        assert stats.file_list == []

    @pytest.mark.performance
    def test_file_operation_performance(self, file_operations, temp_dir, benchmark):
        """Benchmark file operation performance."""
        # Create test files
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        test_files = []
        for i in range(10):
            test_file = source_dir / f"test_{i}.mp4"
            test_file.write_bytes(b"x" * 10000)  # 10KB each
            test_files.append(test_file)

        def benchmark_operations():
            results = []
            for test_file in test_files:
                result = file_operations.copy_file_atomic(
                    str(test_file),
                    str(dest_dir / test_file.name)
                )
                results.append(result)
            return results

        results = benchmark(benchmark_operations)

        assert len(results) == 10
        assert all(r.success for r in results)

    @pytest.mark.parametrize("concurrent_limit", [1, 2, 5, 10])
    def test_concurrent_operations_limit(self, file_operations, temp_dir, concurrent_limit):
        """Test concurrent file operations with different limits."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create test files
        test_files = []
        for i in range(concurrent_limit * 2):  # More files than limit
            test_file = source_dir / f"test_{i}.mp4"
            test_file.write_text(f"content {i}")
            test_files.append(test_file)

        config = FileOperationConfig(max_concurrent=concurrent_limit)

        results = file_operations.process_files_batch(
            [str(f) for f in test_files],
            str(dest_dir),
            config
        )

        assert len(results) == len(test_files)
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(test_files)

    def test_error_handling_comprehensive(self, file_operations):
        """Test comprehensive error handling across all operations."""
        # Test with invalid paths
        assert file_operations.copy_file_atomic("", "") is None
        assert file_operations.move_file_atomic("", "") is None
        assert file_operations.get_file_info("") is None
        assert file_operations.get_directory_stats("") is None

        # Test with None inputs
        assert file_operations.process_file_paths(None) == []
        assert file_operations.find_subtitle_files("") == []

    def test_atomic_operation_rollback(self, file_operations, temp_dir):
        """Test that failed operations are properly rolled back."""
        source_dir = temp_dir / "source"
        dest_dir = temp_dir / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()

        # Create test file
        test_file = source_dir / "test.mp4"
        test_file.write_bytes(b"x" * 10000)

        # Mock os.rename to fail
        with patch('os.rename', side_effect=OSError("Disk full")):
            result = file_operations.move_file_atomic(
                str(test_file),
                str(dest_dir / "test.mp4")
            )

            assert result.success is False
            assert "Disk full" in result.error_message
            # Source file should still exist (rollback)
            assert test_file.exists()
            # Destination file should not exist
            assert not (dest_dir / "test.mp4").exists()
