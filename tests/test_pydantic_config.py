"""
Comprehensive tests for Pydantic v2 configuration models.

This test suite follows Python-pro standards with comprehensive coverage,
parametrized tests, fixtures, and performance benchmarks.
"""

import os
import pytest
from typing import Dict, Any
from unittest.mock import patch

from pydantic import ValidationError
from src.config.pydantic_models import (
    LogLevel, LoggingConfig, PlexConfig, MediaConfig, PathsConfig, 
    PerformanceConfig
)
from src.config.base_settings import CacherrSettings, get_settings, reload_settings


class TestLoggingConfig:
    """Test suite for LoggingConfig with comprehensive validation."""

    def test_valid_logging_config(self):
        """Test creation of valid logging configuration."""
        config = LoggingConfig(
            level=LogLevel.INFO,
            max_files=10,
            max_size_mb=50
        )
        assert config.level == LogLevel.INFO
        assert config.max_files == 10
        assert config.max_size_mb == 50

    def test_default_values(self):
        """Test default values are applied correctly."""
        config = LoggingConfig()
        assert config.level == LogLevel.INFO
        assert config.max_files == 5
        assert config.max_size_mb == 10

    @pytest.mark.parametrize("level,expected", [
        ("debug", "DEBUG"),
        ("info", "INFO"),
        ("warning", "WARNING"),
        ("error", "ERROR"),
        ("critical", "CRITICAL"),
    ])
    def test_log_level_normalization(self, level: str, expected: str):
        """Test log level is normalized to uppercase."""
        config = LoggingConfig(level=level)
        assert config.level.value == expected

    @pytest.mark.parametrize("max_files,should_fail", [
        (1, False),
        (50, False),
        (0, True),  # Should fail - not positive
        (51, True),  # Should fail - exceeds limit
        (-1, True),  # Should fail - negative
    ])
    def test_max_files_validation(self, max_files: int, should_fail: bool):
        """Test max_files validation with various values."""
        if should_fail:
            with pytest.raises(ValidationError):
                LoggingConfig(max_files=max_files)
        else:
            config = LoggingConfig(max_files=max_files)
            assert config.max_files == max_files

    def test_frozen_model(self):
        """Test that LoggingConfig is immutable."""
        config = LoggingConfig()
        with pytest.raises(ValidationError):
            config.level = LogLevel.DEBUG

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            LoggingConfig(level=LogLevel.INFO, unknown_field="value")


class TestPlexConfig:
    """Test suite for PlexConfig with URL validation."""

    @pytest.fixture
    def valid_plex_data(self) -> Dict[str, Any]:
        """Fixture providing valid Plex configuration data."""
        return {
            "url": "http://localhost:32400",
            "token": "test_token_123",
            "username": "testuser",
            "password": "testpass"
        }

    def test_valid_plex_config(self, valid_plex_data):
        """Test creation of valid Plex configuration."""
        config = PlexConfig(**valid_plex_data)
        assert config.url == "http://localhost:32400"
        assert config.token == "test_token_123"
        assert config.username == "testuser"
        assert config.password == "testpass"

    @pytest.mark.parametrize("url,expected", [
        ("http://localhost:32400", "http://localhost:32400"),
        ("https://plex.example.com:443", "https://plex.example.com:443"),
        ("http://192.168.1.100:32400/", "http://192.168.1.100:32400"),  # Trailing slash removed
    ])
    def test_url_normalization(self, url: str, expected: str):
        """Test URL normalization removes trailing slashes."""
        config = PlexConfig(url=url, token="test_token")
        assert config.url == expected

    @pytest.mark.parametrize("invalid_url", [
        "localhost:32400",  # Missing protocol
        "ftp://localhost:32400",  # Wrong protocol
        "",  # Empty string
        "   ",  # Whitespace only
    ])
    def test_invalid_url_validation(self, invalid_url: str):
        """Test that invalid URLs raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PlexConfig(url=invalid_url, token="test_token")
        assert "URL must start with http:// or https://" in str(exc_info.value)

    def test_required_fields(self):
        """Test that required fields must be provided."""
        with pytest.raises(ValidationError):
            PlexConfig()  # Missing url and token

    def test_optional_fields(self):
        """Test that username and password are optional."""
        config = PlexConfig(url="http://localhost:32400", token="test_token")
        assert config.username is None
        assert config.password is None

    def test_string_strip_whitespace(self):
        """Test that whitespace is stripped from string fields."""
        config = PlexConfig(
            url="  http://localhost:32400  ",
            token="  test_token  ",
            username="  testuser  "
        )
        assert config.url == "http://localhost:32400"
        assert config.token == "test_token"
        assert config.username == "testuser"


class TestMediaConfig:
    """Test suite for MediaConfig with business logic validation."""

    def test_default_values_reflect_new_behavior(self):
        """Test that default values reflect copy-first behavior."""
        config = MediaConfig()
        assert config.copy_to_cache is True  # New default
        assert config.delete_from_cache_when_done is True
        assert config.number_episodes == 5
        assert config.watchlist_episodes == 1

    def test_computed_field_cache_mode_description(self):
        """Test computed field returns correct description."""
        copy_config = MediaConfig(copy_to_cache=True)
        move_config = MediaConfig(copy_to_cache=False)
        
        assert copy_config.cache_mode_description == "Copy to cache (preserves originals)"
        assert move_config.cache_mode_description == "Move to cache (frees source space)"

    @pytest.mark.parametrize("field,value,should_fail", [
        ("days_to_monitor", 1, False),
        ("days_to_monitor", 999, False),
        ("days_to_monitor", 0, True),  # Below minimum
        ("days_to_monitor", 1000, True),  # Above maximum
        ("number_episodes", 1, False),
        ("number_episodes", 100, False),
        ("number_episodes", 0, True),  # Below minimum
        ("number_episodes", 101, True),  # Above maximum
        ("watchlist_cache_expiry", 1, False),
        ("watchlist_cache_expiry", 8760, False),  # 1 year
        ("watchlist_cache_expiry", 0, True),  # Below minimum
        ("watchlist_cache_expiry", 8761, True),  # Above maximum
    ])
    def test_field_validation_ranges(self, field: str, value: int, should_fail: bool):
        """Test field validation with various values."""
        kwargs = {field: value}
        if should_fail:
            with pytest.raises(ValidationError):
                MediaConfig(**kwargs)
        else:
            config = MediaConfig(**kwargs)
            assert getattr(config, field) == value

    def test_validate_assignment(self):
        """Test that assignment validation works."""
        config = MediaConfig()
        with pytest.raises(ValidationError):
            config.days_to_monitor = 0  # Invalid value


class TestPathsConfig:
    """Test suite for PathsConfig with path validation."""

    def test_valid_paths_config(self):
        """Test creation of valid paths configuration."""
        config = PathsConfig(
            plex_source="/media",
            cache_destination="/cache",
            additional_sources=["/nas1", "/nas2"],
            additional_plex_sources=["/plexnas1", "/plexnas2"]
        )
        assert config.plex_source == "/media"
        assert config.cache_destination == "/cache"
        assert config.additional_sources == ["/nas1", "/nas2"]
        assert config.additional_plex_sources == ["/plexnas1", "/plexnas2"]

    def test_path_list_validation(self):
        """Test that empty strings are filtered from path lists."""
        config = PathsConfig(
            additional_sources=["  /nas1  ", "", "  ", "/nas2"],
            additional_plex_sources=["/plexnas1", "", "/plexnas2", "  "]
        )
        assert config.additional_sources == ["/nas1", "/nas2"]
        assert config.additional_plex_sources == ["/plexnas1", "/plexnas2"]

    def test_source_parity_validation(self):
        """Test that additional sources and plex sources must have matching counts."""
        with pytest.raises(ValidationError) as exc_info:
            PathsConfig(
                additional_sources=["/nas1", "/nas2"],
                additional_plex_sources=["/plexnas1"]  # Mismatched count
            )
        assert "must have the same length" in str(exc_info.value)

    def test_source_parity_validation_passes(self):
        """Test that matching counts pass validation."""
        config = PathsConfig(
            additional_sources=["/nas1", "/nas2"],
            additional_plex_sources=["/plexnas1", "/plexnas2"]
        )
        assert len(config.additional_sources) == len(config.additional_plex_sources)


class TestPerformanceConfig:
    """Test suite for PerformanceConfig with computed properties."""

    def test_default_performance_values(self):
        """Test default performance configuration values."""
        config = PerformanceConfig()
        assert config.max_concurrent_moves_cache == 3
        assert config.max_concurrent_moves_array == 1
        assert config.max_concurrent_local_transfers == 3
        assert config.max_concurrent_network_transfers == 1

    def test_computed_total_max_concurrent(self):
        """Test computed field for total maximum concurrent operations."""
        config = PerformanceConfig(
            max_concurrent_moves_cache=5,
            max_concurrent_moves_array=2,
            max_concurrent_local_transfers=10,
            max_concurrent_network_transfers=3
        )
        assert config.total_max_concurrent == 20  # 5 + 2 + 10 + 3

    @pytest.mark.parametrize("field,min_val,max_val", [
        ("max_concurrent_moves_cache", 1, 20),
        ("max_concurrent_moves_array", 1, 10),
        ("max_concurrent_local_transfers", 1, 20),
        ("max_concurrent_network_transfers", 1, 5),
    ])
    def test_concurrency_limits(self, field: str, min_val: int, max_val: int):
        """Test concurrency field limits."""
        # Test minimum valid value
        config = PerformanceConfig(**{field: min_val})
        assert getattr(config, field) == min_val
        
        # Test maximum valid value
        config = PerformanceConfig(**{field: max_val})
        assert getattr(config, field) == max_val
        
        # Test below minimum fails
        with pytest.raises(ValidationError):
            PerformanceConfig(**{field: min_val - 1})
        
        # Test above maximum fails
        with pytest.raises(ValidationError):
            PerformanceConfig(**{field: max_val + 1})

    def test_frozen_model(self):
        """Test that PerformanceConfig is immutable."""
        config = PerformanceConfig()
        with pytest.raises(ValidationError):
            config.max_concurrent_moves_cache = 10


class TestCacherrSettings:
    """Test suite for CacherrSettings with environment variable handling."""

    @pytest.fixture
    def clean_env(self):
        """Fixture that cleans environment variables before and after tests."""
        # Store original env vars
        original_env = dict(os.environ)
        
        # Clean test-related env vars
        test_vars = [
            'PLEX_URL', 'PLEX_TOKEN', 'COPY_TO_CACHE', 'NUMBER_EPISODES',
            'MAX_CONCURRENT_MOVES_CACHE', 'LOG_LEVEL', 'TEST_MODE'
        ]
        for var in test_vars:
            os.environ.pop(var, None)
        
        yield
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    def test_default_settings_copy_to_cache_true(self, clean_env):
        """Test that default settings use copy_to_cache=True."""
        settings = CacherrSettings()
        assert settings.copy_to_cache is True
        assert settings.plex_url == "http://localhost:32400"
        assert settings.number_episodes == 5
        assert settings.log_level == LogLevel.INFO

    def test_environment_variable_loading(self, clean_env):
        """Test loading configuration from environment variables."""
        # Set environment variables
        os.environ.update({
            'PLEX_URL': 'https://plex.example.com:32400',
            'PLEX_TOKEN': 'env_token_123',
            'COPY_TO_CACHE': 'false',
            'NUMBER_EPISODES': '10',
            'MAX_CONCURRENT_MOVES_CACHE': '5',
            'LOG_LEVEL': 'DEBUG'
        })
        
        settings = CacherrSettings()
        assert settings.plex_url == 'https://plex.example.com:32400'
        assert settings.plex_token == 'env_token_123'
        assert settings.copy_to_cache is False
        assert settings.number_episodes == 10
        assert settings.max_concurrent_moves_cache == 5
        assert settings.log_level == LogLevel.DEBUG

    @pytest.mark.parametrize("env_value,expected", [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
    ])
    def test_boolean_env_var_parsing(self, clean_env, env_value: str, expected: bool):
        """Test boolean environment variable parsing."""
        os.environ['COPY_TO_CACHE'] = env_value
        settings = CacherrSettings()
        assert settings.copy_to_cache is expected

    def test_comma_separated_list_parsing(self, clean_env):
        """Test parsing comma-separated environment variables."""
        os.environ.update({
            'ADDITIONAL_SOURCES': '/nas1, /nas2 , /nas3',
            'ADDITIONAL_PLEX_SOURCES': '/plexnas1,/plexnas2, /plexnas3 '
        })
        
        settings = CacherrSettings()
        assert settings.additional_sources == ['/nas1', '/nas2', '/nas3']
        assert settings.additional_plex_sources == ['/plexnas1', '/plexnas2', '/plexnas3']

    def test_invalid_env_var_validation(self, clean_env):
        """Test that invalid environment variables raise ValidationError."""
        os.environ['NUMBER_EPISODES'] = 'invalid_number'
        with pytest.raises(ValidationError):
            CacherrSettings()

    def test_get_config_methods(self, clean_env):
        """Test convenience methods for getting typed config objects."""
        os.environ.update({
            'PLEX_URL': 'http://test:32400',
            'PLEX_TOKEN': 'test_token',
            'COPY_TO_CACHE': 'true',
            'NUMBER_EPISODES': '7'
        })
        
        settings = CacherrSettings()
        
        # Test Plex config
        plex_config = settings.get_plex_config()
        assert isinstance(plex_config, PlexConfig)
        assert plex_config.url == 'http://test:32400'
        assert plex_config.token == 'test_token'
        
        # Test Media config
        media_config = settings.get_media_config()
        assert isinstance(media_config, MediaConfig)
        assert media_config.copy_to_cache is True
        assert media_config.number_episodes == 7
        
        # Test Paths config
        paths_config = settings.get_paths_config()
        assert isinstance(paths_config, PathsConfig)
        
        # Test Performance config
        perf_config = settings.get_performance_config()
        assert isinstance(perf_config, PerformanceConfig)

    def test_model_dump_for_api(self, clean_env):
        """Test API-compatible model dump format."""
        settings = CacherrSettings()
        api_data = settings.model_dump_for_api()
        
        # Verify nested structure
        assert 'plex' in api_data
        assert 'media' in api_data
        assert 'paths' in api_data
        assert 'performance' in api_data
        
        # Verify specific values
        assert api_data['media']['copy_to_cache'] is True
        assert api_data['plex']['url'] == 'http://localhost:32400'

    def test_settings_singleton_pattern(self, clean_env):
        """Test that get_settings() implements singleton pattern."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Same instance

    def test_reload_settings(self, clean_env):
        """Test settings reload functionality."""
        # Get initial settings
        settings1 = get_settings()
        original_episodes = settings1.number_episodes
        
        # Change environment and reload
        os.environ['NUMBER_EPISODES'] = '15'
        settings2 = reload_settings()
        
        assert settings2.number_episodes == 15
        assert settings2.number_episodes != original_episodes

    @pytest.mark.benchmark
    def test_settings_creation_performance(self, clean_env, benchmark):
        """Benchmark settings creation performance."""
        def create_settings():
            return CacherrSettings()
        
        result = benchmark(create_settings)
        assert isinstance(result, CacherrSettings)

    @pytest.mark.benchmark
    def test_validation_performance(self, clean_env, benchmark):
        """Benchmark validation performance with complex configuration."""
        complex_config = {
            'plex_url': 'https://plex.example.com:32400',
            'plex_token': 'very_long_token_' * 10,
            'additional_sources': [f'/nas{i}' for i in range(10)],
            'additional_plex_sources': [f'/plexnas{i}' for i in range(10)],
            'number_episodes': 50,
            'days_to_monitor': 365,
        }
        
        def create_complex_settings():
            return CacherrSettings(**complex_config)
        
        result = benchmark(create_complex_settings)
        assert isinstance(result, CacherrSettings)


# Performance benchmarks
@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmarks for Pydantic models."""
    
    def test_model_creation_benchmark(self, benchmark):
        """Benchmark model creation performance."""
        def create_media_config():
            return MediaConfig(
                days_to_monitor=100,
                number_episodes=10,
                copy_to_cache=True,
                delete_from_cache_when_done=True
            )
        
        result = benchmark(create_media_config)
        assert isinstance(result, MediaConfig)
    
    def test_model_validation_benchmark(self, benchmark):
        """Benchmark model validation performance."""
        data = {
            'days_to_monitor': 50,
            'number_episodes': 5,
            'watchlist_episodes': 2,
            'copy_to_cache': True,
            'delete_from_cache_when_done': True,
            'watchlist_cache_expiry': 12,
            'watched_cache_expiry': 72
        }
        
        def validate_media_config():
            return MediaConfig(**data)
        
        result = benchmark(validate_media_config)
        assert isinstance(result, MediaConfig)
    
    def test_model_dump_benchmark(self, benchmark):
        """Benchmark model serialization performance."""
        config = MediaConfig()
        
        def dump_model():
            return config.model_dump()
        
        result = benchmark(dump_model)
        assert isinstance(result, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only'])
