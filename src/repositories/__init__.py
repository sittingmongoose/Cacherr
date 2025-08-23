"""
Repository implementations for PlexCacheUltra data access layer.

This module provides concrete implementations of the repository patterns
defined in core.repositories. All repositories follow the same architectural
patterns with proper error handling, validation, and integration with the
dependency injection system.

Available repositories:
- CacheFileRepository: File-based cache data persistence
- ConfigFileRepository: File-based configuration persistence  
- MetricsFileRepository: File-based metrics data persistence
- RepositoryFactory: Factory for creating repository instances

Exception hierarchy:
- RepositoryError: Base repository exception
- DataIntegrityError: Data consistency issues
- BackupError: Backup operation failures
- RestoreError: Restore operation failures
- ValidationError: Data validation failures
"""

from .exceptions import (
    RepositoryError,
    DataIntegrityError,
    DuplicateEntryError,
    EntryNotFoundError,
    BackupError,
    RestoreError,
    ValidationError,
    ExportError,
    ImportError,
    MetricsError,
    AggregationError,
    CleanupError,
    ConfigurationError
)

from .base_repository import BaseFileRepository
from .cache_repository import CacheFileRepository
from .config_repository import ConfigFileRepository
from .metrics_repository import MetricsFileRepository
from .factory import RepositoryFactory, RepositoryType, RepositoryConfig, RepositoryBackend
from .service_registration import RepositoryServiceRegistration, register_repository_services

__all__ = [
    # Exception classes
    "RepositoryError",
    "DataIntegrityError",
    "DuplicateEntryError",
    "EntryNotFoundError",
    "BackupError",
    "RestoreError",
    "ValidationError",
    "ExportError",
    "ImportError",
    "MetricsError",
    "AggregationError",
    "CleanupError",
    "ConfigurationError",
    
    # Repository implementations
    "BaseFileRepository",
    "CacheFileRepository",
    "ConfigFileRepository", 
    "MetricsFileRepository",
    
    # Factory and configuration
    "RepositoryFactory",
    "RepositoryType",
    "RepositoryConfig",
    "RepositoryBackend",
    
    # Service registration
    "RepositoryServiceRegistration",
    "register_repository_services"
]