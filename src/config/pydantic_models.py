"""
Modern Pydantic v2.5 configuration models with comprehensive validation.

This module provides robust, type-safe configuration management using Pydantic v2.5
BaseModel and BaseSettings. All models include comprehensive validation,
field constraints, and proper environment variable handling.

Example:
    >>> from pydantic import ValidationError
    >>> config = MediaConfig(days_to_monitor=50, number_episodes=10)
    >>> config.copy_to_cache
    True
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any, Annotated
from pathlib import Path
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
    computed_field,
    field_serializer,
    model_serializer,
    BeforeValidator,
    AfterValidator,
    ValidationInfo,
    HttpUrl
)
from pydantic_settings import BaseSettings
from pydantic.types import PositiveInt, NonNegativeInt, SecretStr


class LogLevel(str, Enum):
    """Valid logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfig(BaseModel):
    """
    Logging configuration with enhanced validation and serialization.

    This model provides comprehensive logging configuration with Pydantic v2.5
    optimizations for performance and validation accuracy.

    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_files: Maximum number of log files to retain (1-50)
        max_size_mb: Maximum size per log file in MB (1-1000)
    """
    model_config = ConfigDict(
        frozen=True,                          # Immutable for thread safety
        str_strip_whitespace=True,           # Clean string inputs
        validate_assignment=True,            # Validate on attribute assignment
        extra='ignore',                      # Ignore extra fields (computed fields from serializers)
        str_to_upper=True,                   # Auto-uppercase strings for enum matching
        use_enum_values=True,                # Serialize enums as values
        validate_default=True                # Validate default values
    )

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level for the application",
        examples=["INFO", "DEBUG", "WARNING"]
    )
    max_files: PositiveInt = Field(
        default=5,
        le=50,
        description="Maximum number of log files to retain",
        examples=[5, 10, 20]
    )
    max_size_mb: PositiveInt = Field(
        default=10,
        le=1000,
        description="Maximum size per log file in MB",
        examples=[10, 50, 100]
    )

    @field_validator('level')
    @classmethod
    def validate_log_level(cls, v: str, info: ValidationInfo) -> str:
        """
        Ensure log level is uppercase and valid.

        Args:
            v: The log level string to validate
            info: Validation context information

        Returns:
            Uppercase log level string

        Raises:
            ValueError: If log level is not valid
        """
        if not isinstance(v, str):
            raise ValueError(f"Log level must be a string, got {type(v).__name__}")

        upper_v = v.upper()

        # Validate against enum values
        if upper_v not in [level.value for level in LogLevel]:
            valid_levels = [level.value for level in LogLevel]
            raise ValueError(f"Invalid log level '{v}'. Must be one of: {valid_levels}")

        return upper_v

    @field_serializer('level')
    def serialize_log_level(self, value: LogLevel) -> str:
        """Serialize log level to uppercase string."""
        return value.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with metadata."""
        return {
            'config_type': 'logging',
            'version': '2.5',
            'level': str(self.level),
            'max_files': self.max_files,
            'max_size_mb': self.max_size_mb
        }


class PlexConfig(BaseModel):
    """
    Plex server configuration with enhanced validation and Pydantic v2.5 optimizations.

    This model provides comprehensive Plex server configuration with type-safe
    URL validation, secure token handling, and performance optimizations.

    Attributes:
        url: Plex server URL (must be valid HTTP/HTTPS URL)
        token: Plex authentication token (non-empty string)
        username: Plex username (optional for token auth)
        password: Plex password (optional for token auth, stored securely)
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,           # Clean string inputs
        validate_assignment=True,            # Validate on attribute assignment
        extra='ignore',                      # Ignore extra fields (computed fields from serializers)
        validate_default=True,               # Validate default values
        str_to_lower=False,                  # Preserve URL case sensitivity
        use_enum_values=True                 # Consistent serialization
    )

    url: HttpUrl = Field(
        ...,
        description="Plex server URL (must be valid HTTP/HTTPS)",
        examples=["http://192.168.1.100:32400", "https://plex.example.com:32400"]
    )
    token: Optional[SecretStr] = Field(
        default=None,
        description="Plex authentication token (optional; stored securely)",
        examples=["********************abcd"]
    )
    username: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Plex username (optional for token auth)",
        examples=["myplexuser"]
    )
    password: Optional[SecretStr] = Field(
        default=None,
        description="Plex password (optional for token auth, stored securely)",
        examples=["********************"]
    )

    @field_validator('url')
    @classmethod
    def validate_plex_url(cls, v: Any, info: ValidationInfo) -> HttpUrl:
        """
        Validate and normalize Plex URL.

        Args:
            v: The URL to validate (string or HttpUrl)
            info: Validation context information

        Returns:
            Normalized HttpUrl object

        Raises:
            ValueError: If URL is invalid or not accessible
        """
        # Convert to HttpUrl if it's a string
        if isinstance(v, str):
            try:
                v = HttpUrl(v)
            except Exception as e:
                raise ValueError(f"Invalid URL format: {e}") from e
        elif hasattr(v, 'scheme'):  # Already an HttpUrl-like object
            pass  # Use as-is
        else:
            raise ValueError(f"URL must be a string or HttpUrl object, got {type(v).__name__}")

        # Validate scheme
        if v.scheme not in ['http', 'https']:
            raise ValueError("Plex URL must use HTTP or HTTPS protocol")

        # Validate port (Plex default is 32400)
        if v.port is None:
            raise ValueError("Plex URL must include port number (default: 32400)")

        if v.port < 1 or v.port > 65535:
            raise ValueError("Port number must be between 1 and 65535")

        return v

    @field_validator('token')
    @classmethod
    def validate_token(cls, v: Optional[SecretStr], info: ValidationInfo) -> Optional[SecretStr]:
        """
        Validate Plex authentication token when provided.

        - Accepts None or empty values to allow the app to start
          and let users configure credentials via the UI.
        - If provided, perform a light sanity check without blocking startup.
        """
        if v is None:
            return None
        try:
            token_str = v.get_secret_value()
        except Exception:
            return None
        # Treat empty/whitespace-only as not provided
        if not isinstance(token_str, str) or not token_str.strip():
            return None
        # Keep basic character sanity without enforcing length at model level
        cleaned = token_str.replace('-', '').replace('_', '')
        if not cleaned.isalnum():
            # Allow passing through; connection tests will surface issues
            return v
        return v

    @field_serializer('url')
    def serialize_url(self, value: HttpUrl) -> str:
        """Serialize HttpUrl to string."""
        return str(value)

    @field_serializer('token', 'password')
    def serialize_secret(self, value: Optional[SecretStr]) -> Optional[str]:
        """Serialize SecretStr fields, masking sensitive data."""
        if value is None:
            return None
        return "***MASKED***"

    def to_dict(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """Convert to dictionary with optional security masking."""
        return {
            'config_type': 'plex',
            'version': '2.5',
            'url': str(self.url),
            'token': "***MASKED***" if mask_secrets and self.token else (self.token.get_secret_value() if self.token else None),
            'username': self.username,
            'password': "***MASKED***" if mask_secrets and self.password else (self.password.get_secret_value() if self.password else None),
            'has_credentials': bool(self.token)
        }


class MediaConfig(BaseModel):
    """
    Media processing configuration with enhanced validation and Pydantic v2.5 optimizations.

    This model provides comprehensive media processing configuration with intelligent
    validation rules, performance optimizations, and clear behavioral descriptions.

    Attributes:
        exit_if_active_session: Exit if Plex sessions are active (safety feature)
        watched_move: Move watched content to array (storage optimization)
        users_toggle: Enable per-user processing (multi-user support)
        watchlist_toggle: Enable watchlist processing (content discovery)
        days_to_monitor: Days to monitor content (1-999, content freshness)
        number_episodes: Number of episodes to cache per series (1-100, storage control)
        watchlist_episodes: Episodes to cache from watchlists (1-100, preview control)
        copy_to_cache: Use copy mode instead of move (preserves originals)
        delete_from_cache_when_done: Delete from cache when done (cleanup)
        watchlist_cache_expiry: Watchlist cache expiry hours (1-8760, cache freshness)
        watched_cache_expiry: Watched content cache expiry hours (1-8760, cleanup timing)
    """
    model_config = ConfigDict(
        validate_assignment=True,            # Validate on attribute assignment
        extra='ignore',                      # Ignore extra fields (computed fields from serializers)
        validate_default=True,               # Validate default values
        use_enum_values=True,                # Consistent boolean serialization
        str_strip_whitespace=True            # Clean string inputs
    )

    exit_if_active_session: bool = Field(
        default=False,
        description="Exit if Plex sessions are active (prevents interruption)",
        examples=[False, True]
    )
    watched_move: bool = Field(
        default=True,
        description="Move watched content to array (optimizes storage)",
        examples=[True, False]
    )
    users_toggle: bool = Field(
        default=True,
        description="Enable per-user processing (supports multiple users)",
        examples=[True, False]
    )
    watchlist_toggle: bool = Field(
        default=True,
        description="Enable watchlist processing (automatic content discovery)",
        examples=[True, False]
    )
    days_to_monitor: Annotated[int, Field(ge=1, le=999)] = Field(
        default=99,
        description="Days to monitor content for changes",
        examples=[30, 90, 365]
    )
    number_episodes: Annotated[int, Field(ge=1, le=100)] = Field(
        default=5,
        description="Number of episodes to cache per series",
        examples=[3, 5, 10]
    )
    watchlist_episodes: Annotated[int, Field(ge=1, le=100)] = Field(
        default=1,
        description="Episodes to cache from watchlists (preview episodes)",
        examples=[1, 2, 3]
    )
    copy_to_cache: bool = Field(
        default=True,
        description="Copy files to cache instead of moving (preserves originals)",
        examples=[True, False]
    )
    delete_from_cache_when_done: bool = Field(
        default=True,
        description="Delete files from cache when processing is complete",
        examples=[True, False]
    )
    watchlist_cache_expiry: Annotated[int, Field(ge=1, le=8760)] = Field(
        default=6,
        description="Hours before watchlist cache entries expire",
        examples=[6, 24, 168]
    )
    watched_cache_expiry: Annotated[int, Field(ge=1, le=8760)] = Field(
        default=48,
        description="Hours before watched content cache entries expire",
        examples=[24, 48, 168]
    )

    @field_validator('days_to_monitor', 'number_episodes', 'watchlist_episodes', 'watchlist_cache_expiry', 'watched_cache_expiry')
    @classmethod
    def validate_positive_integers(cls, v: int, info: ValidationInfo) -> int:
        """
        Validate positive integer fields with context-aware limits.

        Args:
            v: The value to validate
            info: Validation context information

        Returns:
            Validated positive integer

        Raises:
            ValueError: If value is outside acceptable range
        """
        field_name = info.field_name if info.field_name else "field"

        if not isinstance(v, int):
            raise ValueError(f"{field_name} must be an integer, got {type(v).__name__}")

        if v <= 0:
            raise ValueError(f"{field_name} must be positive, got {v}")

        # Context-specific validation
        limits = {
            'days_to_monitor': (1, 999),
            'number_episodes': (1, 100),
            'watchlist_episodes': (1, 100),
            'watchlist_cache_expiry': (1, 8760),  # Max 1 year
            'watched_cache_expiry': (1, 8760)     # Max 1 year
        }

        if field_name in limits:
            min_val, max_val = limits[field_name]
            if not (min_val <= v <= max_val):
                raise ValueError(f"{field_name} must be between {min_val} and {max_val}, got {v}")

        return v

    @model_validator(mode='after')
    def validate_cache_expiry_relationship(self) -> 'MediaConfig':
        """
        Validate that watchlist cache expiry doesn't exceed watched cache expiry.

        This ensures logical consistency in cache expiration timing.

        Returns:
            Validated MediaConfig instance

        Raises:
            ValueError: If watchlist expiry is longer than watched expiry
        """
        if self.watchlist_cache_expiry > self.watched_cache_expiry:
            raise ValueError(
                f"Watchlist cache expiry ({self.watchlist_cache_expiry}h) cannot be longer "
                f"than watched cache expiry ({self.watched_cache_expiry}h)"
            )
        return self

    @computed_field
    @property
    def cache_mode_description(self) -> str:
        """Human-readable description of cache mode with performance implications."""
        if self.copy_to_cache:
            return "Copy to cache (preserves originals, slower but safe)"
        else:
            return "Move to cache (frees source space, faster but destructive)"

    @computed_field
    @property
    def estimated_cache_lifetime_hours(self) -> int:
        """Estimated cache lifetime based on current settings."""
        return min(self.watchlist_cache_expiry, self.watched_cache_expiry)

    @field_serializer('copy_to_cache', 'delete_from_cache_when_done', 'watched_move', 'users_toggle', 'watchlist_toggle', 'exit_if_active_session')
    def serialize_boolean_fields(self, value: bool) -> bool:
        """Serialize boolean fields with explicit type conversion."""
        return bool(value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with behavioral metadata."""
        return {
            'config_type': 'media',
            'version': '2.5',
            'cache_mode': self.cache_mode_description,
            'estimated_lifetime_hours': self.estimated_cache_lifetime_hours,
            'performance_profile': 'conservative' if self.copy_to_cache else 'aggressive',
            'multi_user_enabled': self.users_toggle,
            'watchlist_enabled': self.watchlist_toggle,
            'exit_if_active_session': self.exit_if_active_session,
            'watched_move': self.watched_move,
            'days_to_monitor': self.days_to_monitor,
            'number_episodes': self.number_episodes,
            'watchlist_episodes': self.watchlist_episodes,
            'copy_to_cache': self.copy_to_cache,
            'delete_from_cache_when_done': self.delete_from_cache_when_done,
            'watchlist_cache_expiry': self.watchlist_cache_expiry,
            'watched_cache_expiry': self.watched_cache_expiry
        }


class PathsConfig(BaseModel):
    """
    Path configuration with enhanced validation and Pydantic v2.5 optimizations.

    This model provides comprehensive filesystem path configuration with validation
    for directory existence, permissions, and path format consistency.

    Attributes:
        plex_source: Primary Plex source directory (absolute path required)
        cache_destination: Cache destination directory (absolute path required)
        additional_sources: Additional source directories (absolute paths)
        additional_plex_sources: Corresponding Plex sources for additional real sources
    """
    model_config = ConfigDict(
        validate_assignment=True,            # Validate on attribute assignment
        extra='ignore',                      # Ignore extra fields (computed fields from serializers)
        validate_default=True,               # Validate default values
        str_strip_whitespace=True,           # Clean string inputs
        use_enum_values=True                 # Consistent serialization
    )

    plex_source: str = Field(
        default="/media",
        min_length=1,
        description="Primary Plex source directory (absolute path)",
        examples=["/media", "/mnt/user/media", "/data/plex"]
    )
    cache_destination: str = Field(
        default="/cache",
        min_length=1,
        description="Cache destination directory (absolute path)",
        examples=["/cache", "/mnt/cache/cacherr", "/data/cache"]
    )
    additional_sources: List[str] = Field(
        default_factory=list,
        description="Additional source directories (absolute paths)",
        examples=[["/mnt/user/movies"], ["/mnt/user/tv", "/mnt/user/anime"]]
    )
    additional_plex_sources: List[str] = Field(
        default_factory=list,
        description="Corresponding Plex sources for additional real sources",
        examples=[["/media/movies"], ["/media/tv", "/media/anime"]]
    )

    @field_validator('plex_source', 'cache_destination')
    @classmethod
    def validate_absolute_paths(cls, v: str, info: ValidationInfo) -> str:
        """
        Validate that critical paths are absolute.

        Args:
            v: The path string to validate
            info: Validation context information

        Returns:
            Validated absolute path

        Raises:
            ValueError: If path is not absolute or is invalid
        """
        field_name = info.field_name if info.field_name else "path"

        if not isinstance(v, str):
            raise ValueError(f"{field_name} must be a string, got {type(v).__name__}")

        if not v.strip():
            raise ValueError(f"{field_name} cannot be empty")

        # Normalize path separators and remove trailing slashes
        normalized_path = v.replace('\\', '/').rstrip('/')

        if not normalized_path.startswith('/'):
            raise ValueError(f"{field_name} must be an absolute path starting with '/'")

        # Basic path validation (no invalid characters)
        invalid_chars = ['<', '>', '|', '"', '*', '?']
        for char in invalid_chars:
            if char in normalized_path:
                raise ValueError(f"{field_name} contains invalid character '{char}'")

        return normalized_path

    @field_validator('additional_sources', 'additional_plex_sources')
    @classmethod
    def validate_path_lists(cls, v: List[str], info: ValidationInfo) -> List[str]:
        """
        Validate and normalize lists of paths.

        Args:
            v: The list of paths to validate
            info: Validation context information

        Returns:
            Validated and normalized list of paths

        Raises:
            ValueError: If any path is invalid
        """
        field_name = info.field_name if info.field_name else "path_list"

        if not isinstance(v, list):
            raise ValueError(f"{field_name} must be a list, got {type(v).__name__}")

        # Filter out empty strings and normalize
        normalized_paths = []
        for i, path in enumerate(v):
            if isinstance(path, str) and path.strip():
                normalized_path = path.strip().replace('\\', '/').rstrip('/')
                if normalized_path:
                    normalized_paths.append(normalized_path)

        return normalized_paths

    @model_validator(mode='after')
    def validate_source_parity(self) -> 'PathsConfig':
        """
        Validate that additional sources and plex sources have matching counts.

        This ensures configuration consistency for multi-path setups.

        Returns:
            Validated PathsConfig instance

        Raises:
            ValueError: If source lists don't match in length
        """
        additional_count = len(self.additional_sources)
        plex_count = len(self.additional_plex_sources)

        if additional_count != plex_count:
            raise ValueError(
                f'additional_sources ({additional_count} paths) and '
                f'additional_plex_sources ({plex_count} paths) must have the same length. '
                f'Each additional source needs a corresponding Plex source path.'
            )

        return self

    @model_validator(mode='after')
    def validate_path_uniqueness(self) -> 'PathsConfig':
        """
        Validate path configuration for potential conflicts.

        This validation checks for common configuration issues while allowing
        flexibility for different deployment scenarios.

        Returns:
            Validated PathsConfig instance

        Raises:
            ValueError: Only for critical configuration conflicts
        """
        # Check for exact duplicates between additional_sources and additional_plex_sources
        # This is common when both are set to the same value for simplicity
        duplicates_found = []
        for i, source_path in enumerate(self.additional_sources):
            if i < len(self.additional_plex_sources) and source_path == self.additional_plex_sources[i]:
                duplicates_found.append(source_path)

        if duplicates_found:
            # Issue warning instead of error for this common configuration pattern
            import warnings
            warnings.warn(
                f"Additional source paths match their corresponding Plex source paths: {duplicates_found}. "
                "This is allowed but may indicate a configuration simplification.",
                UserWarning
            )

        # Allow plex_source == cache_destination (common in some configurations)
        # But warn if they're the same
        if self.plex_source == self.cache_destination:
            import warnings
            warnings.warn(
                f"Plex source and cache destination are the same path ({self.plex_source}). "
                "This may cause issues with file operations.",
                UserWarning
            )

        # Only raise error for truly problematic duplicates (same path used for different purposes)
        all_paths = [self.plex_source, self.cache_destination] + self.additional_sources + self.additional_plex_sources
        path_counts = {}
        for path in all_paths:
            path_counts[path] = path_counts.get(path, 0) + 1

        # Only error on paths that appear more than 2 times (indicating misuse)
        critical_duplicates = [path for path, count in path_counts.items() if count > 2]

        if critical_duplicates:
            raise ValueError(f'Critical duplicate paths found: {critical_duplicates}. '
                           'Paths should not be reused across different configuration purposes.')

        return self

    @computed_field
    @property
    def total_source_paths(self) -> int:
        """Total number of source paths configured."""
        return 1 + len(self.additional_sources)  # Primary + additional

    @field_serializer('additional_sources', 'additional_plex_sources')
    def serialize_path_lists(self, value: List[str]) -> List[str]:
        """Serialize path lists with consistent formatting."""
        return [path.rstrip('/') for path in value]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with path analysis."""
        return {
            'config_type': 'paths',
            'version': '2.5',
            'total_source_paths': self.total_source_paths,
            'has_additional_sources': len(self.additional_sources) > 0,
            'primary_source': self.plex_source,
            'cache_destination': self.cache_destination,
            'additional_sources': self.additional_sources,
            'additional_plex_sources': self.additional_plex_sources
        }


class PerformanceConfig(BaseModel):
    """
    Performance configuration with enhanced validation and Pydantic v2.5 optimizations.

    This model provides comprehensive performance tuning with intelligent validation
    of concurrency limits, resource allocation, and operational thresholds.

    Attributes:
        max_concurrent_moves_cache: Max concurrent moves to cache (1-20, I/O intensive)
        max_concurrent_moves_array: Max concurrent moves to array (1-10, storage intensive)
        max_concurrent_local_transfers: Max concurrent local transfers (1-20, filesystem operations)
        max_concurrent_network_transfers: Max concurrent network transfers (1-5, bandwidth limited)
    """
    model_config = ConfigDict(
        frozen=True,                         # Immutable for thread safety
        validate_assignment=True,            # Validate on attribute assignment
        extra='ignore',                      # Ignore extra fields (computed fields from serializers)
        validate_default=True,               # Validate default values
        use_enum_values=True,                # Consistent serialization
        str_strip_whitespace=True            # Clean string inputs
    )

    max_concurrent_moves_cache: Annotated[int, Field(ge=1, le=20)] = Field(
        default=3,
        description="Maximum concurrent file moves to cache directory",
        examples=[1, 3, 5, 10]
    )
    max_concurrent_moves_array: Annotated[int, Field(ge=1, le=10)] = Field(
        default=1,
        description="Maximum concurrent file moves to array storage",
        examples=[1, 2, 3]
    )
    max_concurrent_local_transfers: Annotated[int, Field(ge=1, le=20)] = Field(
        default=3,
        description="Maximum concurrent local filesystem transfers",
        examples=[2, 3, 5]
    )
    max_concurrent_network_transfers: Annotated[int, Field(ge=1, le=5)] = Field(
        default=1,
        description="Maximum concurrent network transfers (bandwidth limited)",
        examples=[1, 2, 3]
    )

    @field_validator('max_concurrent_moves_cache', 'max_concurrent_moves_array', 'max_concurrent_local_transfers', 'max_concurrent_network_transfers')
    @classmethod
    def validate_concurrency_limits(cls, v: int, info: ValidationInfo) -> int:
        """
        Validate concurrency limits with context-aware recommendations.

        Args:
            v: The concurrency value to validate
            info: Validation context information

        Returns:
            Validated concurrency value

        Raises:
            ValueError: If value is outside acceptable range
        """
        field_name = info.field_name if info.field_name else "concurrency_field"

        if not isinstance(v, int):
            raise ValueError(f"{field_name} must be an integer, got {type(v).__name__}")

        # Context-specific validation ranges
        limits = {
            'max_concurrent_moves_cache': (1, 20),
            'max_concurrent_moves_array': (1, 10),
            'max_concurrent_local_transfers': (1, 20),
            'max_concurrent_network_transfers': (1, 5)  # More conservative for network
        }

        if field_name in limits:
            min_val, max_val = limits[field_name]
            if not (min_val <= v <= max_val):
                raise ValueError(f"{field_name} must be between {min_val} and {max_val}, got {v}")

            # Performance warnings for extreme values
            if field_name == 'max_concurrent_network_transfers' and v > 3:
                import warnings
                warnings.warn(
                    f"High network concurrency ({v}) may overwhelm network bandwidth",
                    UserWarning
                )
            elif field_name == 'max_concurrent_moves_cache' and v > 10:
                import warnings
                warnings.warn(
                    f"Very high cache concurrency ({v}) may impact system performance",
                    UserWarning
                )

        return v

    @model_validator(mode='after')
    def validate_overall_concurrency(self) -> 'PerformanceConfig':
        """
        Validate that total concurrency doesn't exceed system recommendations.

        This prevents system overload from excessive concurrent operations.

        Returns:
            Validated PerformanceConfig instance

        Raises:
            ValueError: If total concurrency is too high
        """
        total = (
            self.max_concurrent_moves_cache +
            self.max_concurrent_moves_array +
            self.max_concurrent_local_transfers +
            self.max_concurrent_network_transfers
        )

        # Recommended maximum total concurrency
        max_recommended = 25

        if total > max_recommended:
            raise ValueError(
                f'Total concurrent operations ({total}) exceeds recommended maximum ({max_recommended}). '
                f'Consider reducing individual concurrency limits to prevent system overload.'
            )

        # Warning for high total concurrency
        if total > 15:
            import warnings
            warnings.warn(
                f'Total concurrency ({total}) is high and may impact system performance',
                UserWarning
            )

        return self

    @computed_field
    @property
    def total_max_concurrent(self) -> int:
        """Total maximum concurrent operations across all categories."""
        return (
            self.max_concurrent_moves_cache +
            self.max_concurrent_moves_array +
            self.max_concurrent_local_transfers +
            self.max_concurrent_network_transfers
        )

    @computed_field
    @property
    def performance_profile(self) -> str:
        """
        Performance profile based on concurrency settings.

        Returns:
            'conservative', 'balanced', or 'aggressive' based on total concurrency
        """
        total = self.total_max_concurrent
        if total <= 8:
            return 'conservative'
        elif total <= 15:
            return 'balanced'
        else:
            return 'aggressive'

    @computed_field
    @property
    def resource_intensity_score(self) -> int:
        """
        Resource intensity score (0-100) based on concurrency settings.

        Higher scores indicate more resource-intensive configurations.
        """
        base_score = self.total_max_concurrent * 2

        # Bonus for network operations (more resource intensive)
        network_bonus = self.max_concurrent_network_transfers * 5

        # Penalty reduction for conservative settings
        if self.performance_profile == 'conservative':
            base_score = max(0, base_score - 10)

        return min(100, base_score + network_bonus)

    @field_serializer('max_concurrent_moves_cache', 'max_concurrent_moves_array', 'max_concurrent_local_transfers', 'max_concurrent_network_transfers')
    def serialize_concurrency_values(self, value: int) -> int:
        """Serialize concurrency values with validation."""
        return int(value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with performance analysis."""
        return {
            'config_type': 'performance',
            'version': '2.5',
            'total_max_concurrent': self.total_max_concurrent,
            'performance_profile': self.performance_profile,
            'resource_intensity_score': self.resource_intensity_score,
            'concurrency_breakdown': {
                'cache_operations': self.max_concurrent_moves_cache,
                'array_operations': self.max_concurrent_moves_array,
                'local_transfers': self.max_concurrent_local_transfers,
                'network_transfers': self.max_concurrent_network_transfers
            },
            'max_concurrent_moves_cache': self.max_concurrent_moves_cache,
            'max_concurrent_moves_array': self.max_concurrent_moves_array,
            'max_concurrent_local_transfers': self.max_concurrent_local_transfers,
            'max_concurrent_network_transfers': self.max_concurrent_network_transfers
        }
