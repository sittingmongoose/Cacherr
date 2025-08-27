"""
Modern Pydantic v2 configuration models with comprehensive validation.

This module provides robust, type-safe configuration management using Pydantic v2
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
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum

from pydantic import (
    BaseModel, 
    Field, 
    ConfigDict, 
    field_validator,
    model_validator,
    computed_field
)
from pydantic_settings import BaseSettings
from pydantic.types import PositiveInt, NonNegativeInt


class LogLevel(str, Enum):
    """Valid logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfig(BaseModel):
    """
    Logging configuration with validation.
    
    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_files: Maximum number of log files to retain (1-50)
        max_size_mb: Maximum size per log file in MB (1-1000)
    """
    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level for the application"
    )
    max_files: PositiveInt = Field(
        default=5,
        le=50,
        description="Maximum number of log files to retain"
    )
    max_size_mb: PositiveInt = Field(
        default=10,
        le=1000,
        description="Maximum size per log file in MB"
    )

    @field_validator('level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase and valid."""
        return v.upper()


class PlexConfig(BaseModel):
    """
    Plex server configuration with validation.
    
    Attributes:
        url: Plex server URL (must be valid HTTP/HTTPS URL)
        token: Plex authentication token (non-empty string)
        username: Plex username (optional for token auth)
        password: Plex password (optional for token auth)
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    url: str = Field(
        ...,
        min_length=1,
        description="Plex server URL"
    )
    token: str = Field(
        ...,
        min_length=1,
        description="Plex authentication token"
    )
    username: Optional[str] = Field(
        default=None,
        description="Plex username (optional for token auth)"
    )
    password: Optional[str] = Field(
        default=None,
        description="Plex password (optional for token auth)"
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is properly formatted."""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.rstrip('/')


class MediaConfig(BaseModel):
    """
    Media processing configuration with comprehensive validation.
    
    Attributes:
        exit_if_active_session: Exit if Plex sessions are active
        watched_move: Move watched content to array
        users_toggle: Enable per-user processing
        watchlist_toggle: Enable watchlist processing
        days_to_monitor: Days to monitor content (1-999)
        number_episodes: Number of episodes to cache per series (1-100)
        watchlist_episodes: Episodes to cache from watchlists (1-100)
        copy_to_cache: Use copy mode instead of move (default: True)
        delete_from_cache_when_done: Delete from cache when done
        watchlist_cache_expiry: Watchlist cache expiry hours (1-8760)
        watched_cache_expiry: Watched content cache expiry hours (1-8760)
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    exit_if_active_session: bool = Field(
        default=False,
        description="Exit if Plex sessions are active"
    )
    watched_move: bool = Field(
        default=True,
        description="Move watched content to array"
    )
    users_toggle: bool = Field(
        default=True,
        description="Enable per-user processing"
    )
    watchlist_toggle: bool = Field(
        default=True,
        description="Enable watchlist processing"
    )
    days_to_monitor: PositiveInt = Field(
        default=99,
        ge=1,
        le=999,
        description="Days to monitor content"
    )
    number_episodes: PositiveInt = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of episodes to cache per series"
    )
    watchlist_episodes: PositiveInt = Field(
        default=1,
        ge=1,
        le=100,
        description="Episodes to cache from watchlists"
    )
    copy_to_cache: bool = Field(
        default=True,
        description="Use copy mode instead of move (preserves originals)"
    )
    delete_from_cache_when_done: bool = Field(
        default=True,
        description="Delete from cache when done"
    )
    watchlist_cache_expiry: PositiveInt = Field(
        default=6,
        ge=1,
        le=8760,
        description="Watchlist cache expiry hours"
    )
    watched_cache_expiry: PositiveInt = Field(
        default=48,
        ge=1,
        le=8760,
        description="Watched content cache expiry hours"
    )

    @computed_field
    @property
    def cache_mode_description(self) -> str:
        """Human-readable description of cache mode."""
        return "Copy to cache (preserves originals)" if self.copy_to_cache else "Move to cache (frees source space)"


class PathsConfig(BaseModel):
    """
    Path configuration with validation.
    
    Attributes:
        plex_source: Primary Plex source directory
        cache_destination: Cache destination directory
        additional_sources: Additional source directories
        additional_plex_sources: Corresponding Plex sources for additional real sources
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    plex_source: str = Field(
        default="/media",
        min_length=1,
        description="Primary Plex source directory"
    )
    cache_destination: str = Field(
        default="/cache",
        min_length=1,
        description="Cache destination directory"
    )
    additional_sources: List[str] = Field(
        default_factory=list,
        description="Additional source directories"
    )
    additional_plex_sources: List[str] = Field(
        default_factory=list,
        description="Corresponding Plex sources for additional real sources"
    )

    @field_validator('additional_sources', 'additional_plex_sources')
    @classmethod
    def validate_path_lists(cls, v: List[str]) -> List[str]:
        """Ensure all paths are non-empty and properly formatted."""
        return [path.strip() for path in v if path.strip()]

    @model_validator(mode='after')
    def validate_source_parity(self) -> 'PathsConfig':
        """Ensure additional sources and plex sources have matching counts."""
        if len(self.additional_sources) != len(self.additional_plex_sources):
            raise ValueError('additional_sources and additional_plex_sources must have the same length')
        return self


class PerformanceConfig(BaseModel):
    """
    Performance configuration with validation.
    
    Attributes:
        max_concurrent_moves_cache: Max concurrent moves to cache (1-20)
        max_concurrent_moves_array: Max concurrent moves to array (1-10)
        max_concurrent_local_transfers: Max concurrent local transfers (1-20)
        max_concurrent_network_transfers: Max concurrent network transfers (1-5)
    """
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    max_concurrent_moves_cache: PositiveInt = Field(
        default=3,
        ge=1,
        le=20,
        description="Max concurrent moves to cache"
    )
    max_concurrent_moves_array: PositiveInt = Field(
        default=1,
        ge=1,
        le=10,
        description="Max concurrent moves to array"
    )
    max_concurrent_local_transfers: PositiveInt = Field(
        default=3,
        ge=1,
        le=20,
        description="Max concurrent local transfers"
    )
    max_concurrent_network_transfers: PositiveInt = Field(
        default=1,
        ge=1,
        le=5,
        description="Max concurrent network transfers"
    )

    @computed_field
    @property
    def total_max_concurrent(self) -> int:
        """Total maximum concurrent operations."""
        return (
            self.max_concurrent_moves_cache +
            self.max_concurrent_moves_array +
            self.max_concurrent_local_transfers +
            self.max_concurrent_network_transfers
        )
