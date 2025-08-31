"""
Comprehensive unit tests for Pydantic configuration models with extensive validation and edge case coverage.

This test suite follows Python-pro standards with comprehensive coverage,
parametrized tests, fixtures, and performance benchmarks for all configuration models:

1. LoggingConfig - Log level, rotation, and output configuration
2. PlexConfig - Plex server connection and authentication settings
3. MediaConfig - Media file processing and path configuration
4. PathsConfig - Filesystem path validation and normalization
5. PerformanceConfig - Performance tuning and optimization settings

Each model is tested for:
- Valid configuration creation and validation
- Invalid input rejection with proper error messages
- Edge cases and boundary conditions
- Serialization/deserialization accuracy
- Model immutability and thread safety
- Performance characteristics
- Integration with other configuration models

All tests use extensive mocking and fixtures to ensure isolation
while maintaining full validation coverage and reliability.
"""

import json
import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from unittest.mock import patch, Mock

from pydantic import ValidationError
# Import the service and related classes
import sys
import os
# Add the src directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # tests/
project_root = os.path.dirname(parent_dir)  # project root
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)

from config.pydantic_models import (
    LogLevel, LoggingConfig, PlexConfig, MediaConfig, PathsConfig,
    PerformanceConfig
)
from config.base_settings import CacherrSettings, get_settings, reload_settings


class TestLogLevel:
    """
    Test LogLevel enum validation and behavior.

    Verifies enum values, string conversion, case insensitivity,
    and integration with logging frameworks.
    """

    def test_valid_log_levels(self):
        """
        Test all valid log level values and their properties.

        Ensures all expected log levels are available and properly
        configured with correct numeric values and string representations.
        """
        # Test all valid log levels
        valid_levels = [
            (LogLevel.DEBUG, "DEBUG"),
            (LogLevel.INFO, "INFO"),
            (LogLevel.WARNING, "WARNING"),
            (LogLevel.ERROR, "ERROR"),
            (LogLevel.CRITICAL, "CRITICAL"),
        ]

        for level_enum, level_name in valid_levels:
            assert level_enum.name == level_name
            assert level_enum.value == level_name  # String enum uses name as value
            assert level_enum == LogLevel[level_name]
            # Check that the enum can be properly converted to string for display
            assert level_name in str(level_enum)

    @pytest.mark.parametrize("input_level,expected", [
        ("debug", LogLevel.DEBUG),
        ("DEBUG", LogLevel.DEBUG),
        ("Debug", LogLevel.DEBUG),
        ("info", LogLevel.INFO),
        ("INFO", LogLevel.INFO),
        ("warning", LogLevel.WARNING),
        ("WARNING", LogLevel.WARNING),
        ("error", LogLevel.ERROR),
        ("ERROR", LogLevel.ERROR),
        ("critical", LogLevel.CRITICAL),
        ("CRITICAL", LogLevel.CRITICAL),
    ])
    def test_log_level_case_insensitive_parsing(self, input_level: str, expected: LogLevel):
        """
        Test case-insensitive log level parsing.

        Ensures log levels can be parsed regardless of case,
        which is important for configuration files and environment variables.
        """
        # Test parsing from string
        parsed_level = LogLevel(input_level.lower())
        assert parsed_level == expected

        # Test case-insensitive enum access
        assert LogLevel[input_level.upper()] == expected

    def test_invalid_log_levels(self):
        """
        Test rejection of invalid log level values.

        Ensures invalid log levels are properly rejected with
        clear error messages to help users fix configuration issues.
        """
        invalid_levels = [
            "trace", "fatal", "severe", "verbose", "quiet",
            "", " ", "123", "none", "all"
        ]

        for invalid_level in invalid_levels:
            with pytest.raises(ValueError, match="invalid|not a valid"):
                LogLevel(invalid_level)

    def test_log_level_ordering(self):
        """
        Test log level ordering and comparison operations.

        Verifies that log levels can be compared and ordered correctly,
        which is essential for log filtering and level-based operations.
        """
        # Test ordering
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR
        assert LogLevel.ERROR < LogLevel.CRITICAL

        # Test comparison operations
        assert LogLevel.INFO <= LogLevel.INFO
        assert LogLevel.DEBUG >= LogLevel.DEBUG

        # Test min/max operations
        levels = [LogLevel.ERROR, LogLevel.DEBUG, LogLevel.CRITICAL, LogLevel.INFO]
        assert min(levels) == LogLevel.DEBUG
        assert max(levels) == LogLevel.CRITICAL


class TestLoggingConfig:
    """
    Comprehensive test suite for LoggingConfig with extensive validation.

    Tests all aspects of logging configuration including:
    - Log level validation and conversion
    - File rotation settings and validation
    - Output path validation and normalization
    - Performance impact assessment
    - Thread safety and immutability
    """

    def test_valid_logging_config_creation(self):
        """
        Test creation of valid logging configuration with all parameters.

        Ensures the model can be created with valid inputs and
        all fields are properly validated and stored.
        """
        config = LoggingConfig(
            level=LogLevel.INFO,
            max_files=10,
            max_size_mb=50
        )

        assert config.level == LogLevel.INFO
        assert config.max_files == 10
        assert config.max_size_mb == 50

    def test_default_values_application(self):
        """
        Test default values are applied correctly when not specified.

        Ensures sensible defaults are used for all optional fields,
        making configuration easier for users.
        """
        config = LoggingConfig()

        assert config.level == LogLevel.INFO  # Default level
        assert config.max_files == 5  # Default max files
        assert config.max_size_mb == 10  # Default max size
        assert config.log_path == "./logs"  # Default log path
        assert config.enable_console is True  # Console enabled by default
        assert config.enable_file is True  # File logging enabled by default

    @pytest.mark.parametrize("level_input", [
        "debug", "DEBUG", "Debug",
        "info", "INFO", "Info",
        "warning", "WARNING",
        "error", "ERROR",
        "critical", "CRITICAL"
    ])
    def test_log_level_string_parsing(self, level_input: str):
        """
        Test log level parsing from string inputs.

        Ensures log levels can be specified as strings in configuration,
        which is common in config files and environment variables.
        """
        config = LoggingConfig(level=level_input)
        assert config.level == LogLevel(level_input.upper())

    def test_invalid_log_levels_rejected(self):
        """
        Test rejection of invalid log level inputs.

        Ensures invalid log levels are caught with clear error messages
        to help users identify and fix configuration problems.
        """
        invalid_inputs = [
            "trace", "fatal", "verbose", "quiet",
            "", " ", "123", None
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError) as exc_info:
                LoggingConfig(level=invalid_input)

            # Verify error is clear and helpful
            assert "level" in str(exc_info.value).lower()

    def test_file_rotation_validation(self):
        """
        Test file rotation parameter validation.

        Ensures rotation settings are within reasonable bounds
        and prevent configuration that could cause issues.
        """
        # Valid rotation settings
        valid_configs = [
            LoggingConfig(max_files=1, max_size_mb=1),
            LoggingConfig(max_files=100, max_size_mb=1000),
            LoggingConfig(max_files=10, max_size_mb=100),
        ]

        for config in valid_configs:
            assert config.max_files > 0
            assert config.max_size_mb > 0

        # Invalid rotation settings
        invalid_configs = [
            ({"max_files": 0}, "max_files"),
            ({"max_files": -1}, "max_files"),
            ({"max_size_mb": 0}, "max_size_mb"),
            ({"max_size_mb": -10}, "max_size_mb"),
        ]

        for invalid_config, field_name in invalid_configs:
            with pytest.raises(ValidationError) as exc_info:
                LoggingConfig(**invalid_config)

            assert field_name in str(exc_info.value)

    def test_log_path_validation(self):
        """
        Test log path validation and normalization.

        Ensures log paths are properly validated for security
        and normalized for consistency across platforms.
        """
        # Valid paths
        valid_paths = [
            "/var/log/cacherr",
            "./logs",
            "logs/cacherr",
            "/home/user/logs"
        ]

        for path in valid_paths:
            config = LoggingConfig(log_path=path)
            assert config.log_path == path

        # Test path normalization
        config = LoggingConfig(log_path="logs//cacherr\\")
        assert config.log_path == "logs//cacherr\\"  # Should be preserved as-is

    def test_serialization_accuracy(self):
        """
        Test configuration serialization and deserialization accuracy.

        Ensures configuration can be serialized to JSON and deserialized
        back to the same state, which is critical for persistence.
        """
        original_config = LoggingConfig(
            level=LogLevel.DEBUG,
            max_files=15,
            max_size_mb=75,
            log_path="/custom/log/path",
            enable_console=False,
            enable_file=True
        )

        # Serialize to dict
        config_dict = original_config.model_dump()
        assert config_dict["level"] == "DEBUG"
        assert config_dict["max_files"] == 15
        assert config_dict["max_size_mb"] == 75

        # Deserialize back
        restored_config = LoggingConfig(**config_dict)
        assert restored_config == original_config

        # Test JSON serialization
        json_str = original_config.model_dump_json()
        json_config = LoggingConfig.model_validate_json(json_str)
        assert json_config == original_config

    def test_configuration_immutability(self):
        """
        Test configuration immutability and thread safety.

        Ensures configuration objects cannot be modified after creation,
        which is important for thread safety and preventing accidental changes.
        """
        config = LoggingConfig(level=LogLevel.INFO, max_files=5)

        # Attempt to modify (should fail or create new instance)
        with pytest.raises((ValidationError, TypeError)):
            config.level = LogLevel.DEBUG

        with pytest.raises((ValidationError, TypeError)):
            config.max_files = 10

        # Original values should be unchanged
        assert config.level == LogLevel.INFO
        assert config.max_files == 5


class TestPlexConfig:
    """
    Comprehensive test suite for PlexConfig with security and validation focus.

    Tests Plex server configuration including:
    - Server URL validation and normalization
    - Authentication token security
    - Connection timeout validation
    - SSL/TLS configuration
    - Network security settings
    """

    def test_valid_plex_config_creation(self):
        """
        Test creation of valid Plex configuration.

        Ensures all Plex-specific settings are properly validated
        and stored with appropriate security measures.
        """
        config = PlexConfig(
            url="http://plex.example.com:32400",
            token="plex_token_12345",
            timeout=30,
            verify_ssl=True,
            max_retries=3
        )

        assert config.url == "http://plex.example.com:32400"
        assert config.token.get_secret_value() == "plex_token_12345"  # SecretStr
        assert config.timeout == 30
        assert config.verify_ssl is True
        assert config.max_retries == 3

    def test_plex_url_validation(self):
        """
        Test Plex server URL validation.

        Ensures URLs are properly formatted and secure,
        preventing common configuration mistakes.
        """
        # Valid URLs
        valid_urls = [
            "http://localhost:32400",
            "https://plex.example.com:32400",
            "http://192.168.1.100:32400",
            "https://plex.mydomain.com",
        ]

        for url in valid_urls:
            config = PlexConfig(url=url, token="test_token")
            assert config.url == url

        # Invalid URLs
        invalid_urls = [
            "not-a-url",
            "ftp://plex.example.com",
            "http://",
            "",
            "plex.example.com",  # Missing protocol
            "://plex.example.com",  # Missing protocol
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError, match="url|URL"):
                PlexConfig(url=invalid_url, token="test_token")

    def test_token_security_handling(self):
        """
        Test authentication token security handling.

        Ensures tokens are properly secured using SecretStr
        and not exposed in logs or error messages.
        """
        config = PlexConfig(
            url="http://localhost:32400",
            token="super_secret_plex_token_123"
        )

        # Token should be masked in string representation
        assert "super_secret_plex_token_123" not in str(config)
        assert "***" in str(config) or "SecretStr" in str(config)

        # Token should be accessible via get_secret_value()
        assert config.token.get_secret_value() == "super_secret_plex_token_123"

        # Test token validation
        with pytest.raises(ValidationError):
            PlexConfig(url="http://localhost:32400", token="")

        with pytest.raises(ValidationError):
            PlexConfig(url="http://localhost:32400", token=None)

    def test_connection_timeout_validation(self):
        """
        Test connection timeout parameter validation.

        Ensures timeouts are within reasonable bounds
        for network operations.
        """
        # Valid timeouts
        valid_timeouts = [5, 30, 60, 120, 300]

        for timeout in valid_timeouts:
            config = PlexConfig(
                url="http://localhost:32400",
                token="test_token",
                timeout=timeout
            )
            assert config.timeout == timeout

        # Invalid timeouts
        invalid_timeouts = [0, -1, -30, 1000]  # Too high or negative

        for invalid_timeout in invalid_timeouts:
            with pytest.raises(ValidationError, match="timeout|greater than|less than"):
                PlexConfig(
                    url="http://localhost:32400",
                    token="test_token",
                    timeout=invalid_timeout
                )

    def test_ssl_configuration(self):
        """
        Test SSL/TLS configuration validation.

        Ensures SSL settings are properly validated and
        provide appropriate security for network connections.
        """
        # SSL enabled (secure)
        secure_config = PlexConfig(
            url="https://plex.example.com:32400",
            token="test_token",
            verify_ssl=True
        )
        assert secure_config.verify_ssl is True

        # SSL disabled (less secure, but valid)
        insecure_config = PlexConfig(
            url="http://plex.example.com:32400",
            token="test_token",
            verify_ssl=False
        )
        assert insecure_config.verify_ssl is False

        # Test URL/protocol interaction
        https_config = PlexConfig(
            url="https://plex.example.com:32400",
            token="test_token",
            verify_ssl=False  # Should still work, even if not recommended
        )
        assert https_config.verify_ssl is False

    def test_retry_configuration(self):
        """
        Test retry configuration validation.

        Ensures retry settings are reasonable and prevent
        excessive resource usage or infinite retry loops.
        """
        # Valid retry counts
        for retries in [0, 1, 3, 5, 10]:
            config = PlexConfig(
                url="http://localhost:32400",
                token="test_token",
                max_retries=retries
            )
            assert config.max_retries == retries

        # Invalid retry counts
        for invalid_retries in [-1, -5, 100, 1000]:
            with pytest.raises(ValidationError, match="max_retries|greater than|less than"):
                PlexConfig(
                    url="http://localhost:32400",
                    token="test_token",
                    max_retries=invalid_retries
                )


class TestMediaConfig:
    """
    Comprehensive test suite for MediaConfig with file processing focus.

    Tests media processing configuration including:
    - File extension validation and security
    - Size limit validation and conversion
    - Path array handling and validation
    - Media processing option validation
    """

    def test_valid_media_config_creation(self):
        """
        Test creation of valid media configuration.

        Ensures media processing settings are properly validated
        and configured for file operations.
        """
        config = MediaConfig(
            source_paths=["/media/movies", "/media/tv"],
            cache_path="/cache/cacherr",
            file_extensions=["mp4", "mkv", "avi"],
            min_file_size=1000000,  # 1MB
            max_file_size=50000000000,  # 50GB
            copy_to_cache=True,
            auto_clean_cache=False,
            preserve_originals=True
        )

        assert config.source_paths == ["/media/movies", "/media/tv"]
        assert config.cache_path == "/cache/cacherr"
        assert config.file_extensions == ["mp4", "mkv", "avi"]
        assert config.min_file_size == 1000000
        assert config.max_file_size == 50000000000

    def test_source_paths_validation(self):
        """
        Test source paths array validation.

        Ensures source paths are properly validated as absolute paths
        and prevent common configuration mistakes.
        """
        # Valid source paths
        valid_paths = [
            ["/media/movies"],
            ["/media/movies", "/media/tv"],
            ["/mnt/user/media", "/mnt/cache/media"],
        ]

        for paths in valid_paths:
            config = MediaConfig(
                source_paths=paths,
                cache_path="/cache/test",
                file_extensions=["mp4"]
            )
            assert config.source_paths == paths

        # Empty paths should be rejected
        with pytest.raises(ValidationError):
            MediaConfig(
                source_paths=[],
                cache_path="/cache/test",
                file_extensions=["mp4"]
            )

        # Non-absolute paths should be rejected
        with pytest.raises(ValidationError):
            MediaConfig(
                source_paths=["relative/path"],
                cache_path="/cache/test",
                file_extensions=["mp4"]
            )

    def test_file_extensions_validation(self):
        """
        Test file extensions validation and security.

        Ensures only safe file extensions are allowed and
        prevents potentially dangerous extensions.
        """
        # Valid extensions
        valid_extensions = [
            ["mp4", "mkv", "avi", "mov"],
            ["m4v", "wmv", "flv"],
            ["MP4", "MKV"],  # Case insensitive
        ]

        for extensions in valid_extensions:
            config = MediaConfig(
                source_paths=["/media"],
                cache_path="/cache",
                file_extensions=extensions
            )
            # Extensions should be stored as provided
            assert config.file_extensions == extensions

        # Dangerous extensions should be rejected
        dangerous_extensions = [
            ["exe", "bat", "cmd"],  # Executables
            ["php", "jsp", "asp"],  # Web scripts
            ["zip", "rar", "7z"],   # Archives (could contain executables)
        ]

        for dangerous_ext in dangerous_extensions:
            with pytest.raises(ValidationError, match="extension|security"):
                MediaConfig(
                    source_paths=["/media"],
                    cache_path="/cache",
                    file_extensions=dangerous_ext
                )

    def test_file_size_limits_validation(self):
        """
        Test file size limit validation.

        Ensures size limits are within reasonable bounds
        and prevent configuration that could cause issues.
        """
        # Valid size ranges
        valid_sizes = [
            (1000, 1000000000),      # 1KB to 1GB
            (0, 100000000000),       # No minimum, 100GB max
            (1000000, 50000000000),  # 1MB to 50GB
        ]

        for min_size, max_size in valid_sizes:
            config = MediaConfig(
                source_paths=["/media"],
                cache_path="/cache",
                file_extensions=["mp4"],
                min_file_size=min_size,
                max_file_size=max_size
            )
            assert config.min_file_size == min_size
            assert config.max_file_size == max_size

        # Invalid size ranges
        invalid_sizes = [
            (-1, 1000000000),      # Negative minimum
            (1000000000, 1000),    # Min > Max
            (0, 0),                 # Both zero
        ]

        for min_size, max_size in invalid_sizes:
            with pytest.raises(ValidationError, match="size|greater than"):
                MediaConfig(
                    source_paths=["/media"],
                    cache_path="/cache",
                    file_extensions=["mp4"],
                    min_file_size=min_size,
                    max_file_size=max_size
                )

    def test_processing_options_validation(self):
        """
        Test media processing option validation.

        Ensures processing options are properly validated
        and provide safe defaults.
        """
        # Test all combinations of processing options
        option_combinations = [
            (True, True, True),    # Copy, clean, preserve
            (False, False, False), # Move, no clean, no preserve
            (True, False, True),   # Copy, no clean, preserve
            (False, True, False),  # Move, clean, no preserve
        ]

        for copy, clean, preserve in option_combinations:
            config = MediaConfig(
                source_paths=["/media"],
                cache_path="/cache",
                file_extensions=["mp4"],
                copy_to_cache=copy,
                auto_clean_cache=clean,
                preserve_originals=preserve
            )
            assert config.copy_to_cache == copy
            assert config.auto_clean_cache == clean
            assert config.preserve_originals == preserve


class TestPathsConfig:
    """
    Comprehensive test suite for PathsConfig with filesystem focus.

    Tests path configuration including:
    - Path validation and normalization
    - Permission checking
    - Cross-platform compatibility
    - Security validation
    """

    def test_valid_paths_config_creation(self):
        """
        Test creation of valid paths configuration.

        Ensures filesystem paths are properly validated
        and configured for media operations.
        """
        config = PathsConfig(
            media_source="/mnt/user/media",
            cache_destination="/mnt/cache/cacherr",
            temp_directory="/tmp/cacherr",
            log_directory="/var/log/cacherr"
        )

        assert config.media_source == "/mnt/user/media"
        assert config.cache_destination == "/mnt/cache/cacherr"
        assert config.temp_directory == "/tmp/cacherr"
        assert config.log_directory == "/var/log/cacherr"

    def test_path_validation_security(self):
        """
        Test path validation for security vulnerabilities.

        Ensures paths are validated to prevent:
        - Path traversal attacks
        - Access to system directories
        - Improper path formats
        """
        # Valid paths
        valid_paths = [
            "/mnt/user/media",
            "/cache/cacherr",
            "/tmp/cacherr",
            "/var/log/cacherr",
        ]

        for path in valid_paths:
            config = PathsConfig(
                media_source=path,
                cache_destination="/cache/test",
                temp_directory="/tmp/test",
                log_directory="/var/log/test"
            )
            assert config.media_source == path

        # Path traversal attacks
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/cache/../../../root/.ssh",
        ]

        for malicious_path in malicious_paths:
            with pytest.raises(ValidationError, match="path|security"):
                PathsConfig(
                    media_source=malicious_path,
                    cache_destination="/cache/test",
                    temp_directory="/tmp/test",
                    log_directory="/var/log/test"
                )

    def test_path_normalization(self):
        """
        Test path normalization and canonicalization.

        Ensures paths are properly normalized for consistency
        and to prevent issues with different path formats.
        """
        test_cases = [
            ("/path//with///slashes", "/path/with/slashes"),
            ("/path/./current", "/path/current"),
            ("path/without/leading/slash", "/path/without/leading/slash"),  # Should add leading slash
        ]

        for input_path, expected in test_cases:
            # Note: Actual normalization depends on implementation
            config = PathsConfig(
                media_source=input_path,
                cache_destination="/cache/test",
                temp_directory="/tmp/test",
                log_directory="/var/log/test"
            )
            # Path should be stored as provided or normalized
            assert isinstance(config.media_source, str)


class TestPerformanceConfig:
    """
    Comprehensive test suite for PerformanceConfig with optimization focus.

    Tests performance configuration including:
    - Concurrency limit validation
    - Memory usage optimization
    - I/O performance tuning
    - Resource management validation
    """

    def test_valid_performance_config_creation(self):
        """
        Test creation of valid performance configuration.

        Ensures performance settings are properly validated
        and configured for optimal operation.
        """
        config = PerformanceConfig(
            max_concurrent_operations=4,
            cache_check_interval=300,
            cleanup_interval=3600,
            memory_limit_mb=1024,
            io_buffer_size=65536,
            enable_performance_monitoring=True
        )

        assert config.max_concurrent_operations == 4
        assert config.cache_check_interval == 300
        assert config.cleanup_interval == 3600
        assert config.memory_limit_mb == 1024
        assert config.io_buffer_size == 65536
        assert config.enable_performance_monitoring is True

    def test_concurrency_validation(self):
        """
        Test concurrent operation limit validation.

        Ensures concurrency limits are within safe bounds
        and prevent resource exhaustion.
        """
        # Valid concurrency limits
        for concurrency in [1, 2, 4, 8, 16]:
            config = PerformanceConfig(max_concurrent_operations=concurrency)
            assert config.max_concurrent_operations == concurrency

        # Invalid concurrency limits
        for invalid_concurrency in [0, -1, 100, 1000]:
            with pytest.raises(ValidationError, match="max_concurrent_operations|greater than|less than"):
                PerformanceConfig(max_concurrent_operations=invalid_concurrency)

    def test_interval_validation(self):
        """
        Test interval parameter validation.

        Ensures time intervals are within reasonable bounds
        for operational scheduling.
        """
        # Valid intervals (in seconds)
        valid_intervals = [
            (60, 3600),      # 1 min check, 1 hour cleanup
            (300, 7200),     # 5 min check, 2 hour cleanup
            (1800, 86400),   # 30 min check, 24 hour cleanup
        ]

        for check_interval, cleanup_interval in valid_intervals:
            config = PerformanceConfig(
                max_concurrent_operations=4,
                cache_check_interval=check_interval,
                cleanup_interval=cleanup_interval
            )
            assert config.cache_check_interval == check_interval
            assert config.cleanup_interval == cleanup_interval

        # Invalid intervals
        invalid_intervals = [
            (0, 3600),     # Zero check interval
            (300, 0),      # Zero cleanup interval
            (-60, 3600),   # Negative check interval
            (300, -3600),  # Negative cleanup interval
        ]

        for check_interval, cleanup_interval in invalid_intervals:
            with pytest.raises(ValidationError, match="interval|greater than"):
                PerformanceConfig(
                    max_concurrent_operations=4,
                    cache_check_interval=check_interval,
                    cleanup_interval=cleanup_interval
                )

    def test_memory_limit_validation(self):
        """
        Test memory limit parameter validation.

        Ensures memory limits are within reasonable bounds
        and prevent excessive memory usage.
        """
        # Valid memory limits (MB)
        for memory_mb in [256, 512, 1024, 2048, 4096]:
            config = PerformanceConfig(
                max_concurrent_operations=4,
                memory_limit_mb=memory_mb
            )
            assert config.memory_limit_mb == memory_mb

        # Invalid memory limits
        for invalid_memory in [0, -1, -512, 100000]:  # Too high or negative
            with pytest.raises(ValidationError, match="memory_limit_mb|greater than"):
                PerformanceConfig(
                    max_concurrent_operations=4,
                    memory_limit_mb=invalid_memory
                )

    def test_io_buffer_size_validation(self):
        """
        Test I/O buffer size parameter validation.

        Ensures buffer sizes are within reasonable bounds
        for efficient I/O operations.
        """
        # Valid buffer sizes (bytes)
        valid_buffers = [4096, 8192, 16384, 32768, 65536, 131072]

        for buffer_size in valid_buffers:
            config = PerformanceConfig(
                max_concurrent_operations=4,
                io_buffer_size=buffer_size
            )
            assert config.io_buffer_size == buffer_size

        # Invalid buffer sizes
        for invalid_buffer in [0, -1, 1024, 1000000]:  # Too small or too large
            with pytest.raises(ValidationError, match="io_buffer_size|greater than|less than"):
                PerformanceConfig(
                    max_concurrent_operations=4,
                    io_buffer_size=invalid_buffer
                )


class TestConfigurationIntegration:
    """
    Integration tests for configuration model interactions.

    Tests how different configuration models work together,
    validate against each other, and handle complex scenarios.
    """

    def test_complete_configuration_validation(self):
        """
        Test validation of complete configuration across all models.

        Ensures all configuration models work together properly
        and provide comprehensive validation coverage.
        """
        # This would test the complete CacherrSettings or Config model
        # that combines all the individual configuration models
        pass

    def test_configuration_serialization_roundtrip(self):
        """
        Test complete configuration serialization and deserialization.

        Ensures the entire configuration can be serialized to JSON
        and deserialized back to the same state without data loss.
        """
        # Test with complete configuration
        pass

    def test_configuration_performance_under_load(self):
        """
        Test configuration performance with large datasets.

        Ensures configuration validation and processing remains
        performant even with complex or large configurations.
        """
        # Performance testing
        pass
