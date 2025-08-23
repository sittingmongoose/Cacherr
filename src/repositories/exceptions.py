"""
Repository exception hierarchy for PlexCacheUltra.

This module defines a comprehensive exception hierarchy for repository operations,
providing specific error types for different failure scenarios. All repository
exceptions inherit from RepositoryError to enable consistent error handling.

Exception Hierarchy:
    RepositoryError (base)
    ├── DataIntegrityError
    │   ├── DuplicateEntryError
    │   └── EntryNotFoundError
    ├── BackupError
    ├── RestoreError
    ├── ValidationError
    ├── ExportError
    ├── ImportError
    ├── MetricsError
    │   ├── AggregationError
    │   └── CleanupError
    └── ConfigurationError

Usage:
    try:
        repository.add_entry(entry)
    except DuplicateEntryError:
        # Handle duplicate entry
        pass
    except ValidationError:
        # Handle validation failure
        pass
    except RepositoryError:
        # Handle any other repository error
        pass
"""

from typing import Optional, Any


class RepositoryError(Exception):
    """
    Base exception for all repository operations.
    
    This is the root exception class for the repository layer, providing
    a common base for all repository-related errors. It includes enhanced
    error context and optional error codes for better error handling.
    
    Attributes:
        message: Human-readable error description
        error_code: Optional error code for programmatic handling
        context: Optional additional context information
        original_error: Original exception that caused this error (if any)
    """
    
    def __init__(
        self, 
        message: str,
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize repository error.
        
        Args:
            message: Human-readable error description
            error_code: Optional error code for programmatic handling
            context: Optional additional context information
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        """Return formatted error string."""
        error_parts = [self.message]
        
        if self.error_code:
            error_parts.append(f"Code: {self.error_code}")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            error_parts.append(f"Context: {context_str}")
        
        if self.original_error:
            error_parts.append(f"Caused by: {self.original_error}")
        
        return " | ".join(error_parts)
    
    def __repr__(self) -> str:
        """Return detailed error representation."""
        return (f"{self.__class__.__name__}(message='{self.message}', "
                f"error_code='{self.error_code}', context={self.context})")


class DataIntegrityError(RepositoryError):
    """
    Raised when data consistency or integrity issues are detected.
    
    This exception is raised when operations would violate data integrity
    constraints, such as referential integrity, uniqueness constraints,
    or data consistency rules.
    """
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="DATA_INTEGRITY", **kwargs)


class DuplicateEntryError(DataIntegrityError):
    """
    Raised when attempting to create an entry that already exists.
    
    This exception is raised when trying to add data that would violate
    uniqueness constraints, such as duplicate file paths in the cache
    or duplicate configuration keys.
    """
    
    def __init__(self, message: str, duplicate_key: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if duplicate_key:
            context["duplicate_key"] = duplicate_key
        
        super().__init__(message, error_code="DUPLICATE_ENTRY", context=context, **kwargs)
        self.duplicate_key = duplicate_key


class EntryNotFoundError(DataIntegrityError):
    """
    Raised when attempting to access an entry that doesn't exist.
    
    This exception is raised when trying to retrieve, update, or delete
    data that cannot be found in the repository.
    """
    
    def __init__(self, message: str, missing_key: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if missing_key:
            context["missing_key"] = missing_key
        
        super().__init__(message, error_code="ENTRY_NOT_FOUND", context=context, **kwargs)
        self.missing_key = missing_key


class BackupError(RepositoryError):
    """
    Raised when backup operations fail.
    
    This exception is raised when backup creation, validation, or
    related operations fail due to file system issues, permissions,
    or data corruption.
    """
    
    def __init__(self, message: str, backup_path: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if backup_path:
            context["backup_path"] = backup_path
        
        super().__init__(message, error_code="BACKUP_FAILED", context=context, **kwargs)
        self.backup_path = backup_path


class RestoreError(RepositoryError):
    """
    Raised when restore operations fail.
    
    This exception is raised when attempting to restore data from backups
    fails due to corrupted backup files, incompatible formats, or
    file system issues.
    """
    
    def __init__(self, message: str, backup_path: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if backup_path:
            context["backup_path"] = backup_path
        
        super().__init__(message, error_code="RESTORE_FAILED", context=context, **kwargs)
        self.backup_path = backup_path


class ValidationError(RepositoryError):
    """
    Raised when data validation fails.
    
    This exception is raised when attempting to store or process data
    that doesn't meet validation requirements, such as invalid formats,
    missing required fields, or constraint violations.
    """
    
    def __init__(
        self, 
        message: str, 
        validation_errors: Optional[list] = None,
        field_name: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        if validation_errors:
            context["validation_errors"] = validation_errors
        if field_name:
            context["field_name"] = field_name
        
        super().__init__(message, error_code="VALIDATION_FAILED", context=context, **kwargs)
        self.validation_errors = validation_errors or []
        self.field_name = field_name


class ExportError(RepositoryError):
    """
    Raised when data export operations fail.
    
    This exception is raised when attempting to export repository data
    to external formats or files fails due to serialization issues,
    file system problems, or format incompatibilities.
    """
    
    def __init__(self, message: str, export_path: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if export_path:
            context["export_path"] = export_path
        
        super().__init__(message, error_code="EXPORT_FAILED", context=context, **kwargs)
        self.export_path = export_path


class ImportError(RepositoryError):
    """
    Raised when data import operations fail.
    
    This exception is raised when attempting to import data from external
    sources fails due to parsing errors, format incompatibilities, or
    validation failures.
    """
    
    def __init__(self, message: str, import_path: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if import_path:
            context["import_path"] = import_path
        
        super().__init__(message, error_code="IMPORT_FAILED", context=context, **kwargs)
        self.import_path = import_path


class MetricsError(RepositoryError):
    """
    Raised when metrics collection or processing operations fail.
    
    This exception is raised when metrics recording, retrieval, or
    processing operations fail due to data issues, system problems,
    or calculation errors.
    """
    
    def __init__(self, message: str, metric_type: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if metric_type:
            context["metric_type"] = metric_type
        
        super().__init__(message, error_code="METRICS_FAILED", context=context, **kwargs)
        self.metric_type = metric_type


class AggregationError(MetricsError):
    """
    Raised when metrics aggregation operations fail.
    
    This exception is raised when attempting to aggregate or calculate
    metrics fails due to data inconsistencies, calculation errors,
    or insufficient data.
    """
    
    def __init__(self, message: str, aggregation_type: Optional[str] = None, **kwargs):
        context = kwargs.get("context", {})
        if aggregation_type:
            context["aggregation_type"] = aggregation_type
        
        super().__init__(message, error_code="AGGREGATION_FAILED", context=context, **kwargs)
        self.aggregation_type = aggregation_type


class CleanupError(MetricsError):
    """
    Raised when metrics cleanup operations fail.
    
    This exception is raised when attempting to clean up old metrics
    data fails due to file system issues, data dependencies, or
    permission problems.
    """
    
    def __init__(self, message: str, retention_period: Optional[int] = None, **kwargs):
        context = kwargs.get("context", {})
        if retention_period:
            context["retention_period_days"] = retention_period
        
        super().__init__(message, error_code="CLEANUP_FAILED", context=context, **kwargs)
        self.retention_period = retention_period


class ConfigurationError(RepositoryError):
    """
    Raised when configuration operations fail.
    
    This exception is raised when configuration retrieval, storage, or
    validation operations fail due to format issues, permission problems,
    or validation failures.
    """
    
    def __init__(
        self, 
        message: str, 
        config_section: Optional[str] = None,
        config_key: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get("context", {})
        if config_section:
            context["config_section"] = config_section
        if config_key:
            context["config_key"] = config_key
        
        super().__init__(message, error_code="CONFIG_FAILED", context=context, **kwargs)
        self.config_section = config_section
        self.config_key = config_key


# Utility functions for exception handling

def wrap_repository_error(
    operation: str,
    original_error: Exception,
    context: Optional[dict] = None
) -> RepositoryError:
    """
    Wrap a generic exception in a RepositoryError with context.
    
    This utility function helps convert generic exceptions into
    repository-specific errors with additional context information.
    
    Args:
        operation: Description of the operation that failed
        original_error: The original exception
        context: Additional context information
        
    Returns:
        RepositoryError: Wrapped exception with context
        
    Example:
        try:
            # Some file operation
            pass
        except IOError as e:
            raise wrap_repository_error(
                "cache entry creation",
                e,
                {"file_path": "/path/to/file"}
            )
    """
    message = f"Repository operation failed: {operation}"
    
    # Try to provide more specific error types based on original error
    if isinstance(original_error, FileNotFoundError):
        return EntryNotFoundError(
            f"Required file not found during {operation}",
            context=context,
            original_error=original_error
        )
    elif isinstance(original_error, PermissionError):
        return RepositoryError(
            f"Permission denied during {operation}",
            error_code="PERMISSION_DENIED",
            context=context,
            original_error=original_error
        )
    elif isinstance(original_error, OSError):
        return RepositoryError(
            f"System error during {operation}",
            error_code="SYSTEM_ERROR",
            context=context,
            original_error=original_error
        )
    else:
        return RepositoryError(
            message,
            error_code="UNKNOWN_ERROR",
            context=context,
            original_error=original_error
        )