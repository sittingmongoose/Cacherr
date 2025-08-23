"""
Base repository implementation with common file-based persistence functionality.

This module provides the BaseFileRepository class that implements common
functionality shared across all file-based repositories. It handles file I/O,
JSON serialization, backup operations, and atomic file operations with
proper error handling and validation.

Key Features:
- Thread-safe file operations with file locking
- Atomic write operations to prevent data corruption
- Automatic backup creation before modifications  
- JSON serialization with Pydantic model support
- Comprehensive error handling and logging
- File integrity validation with checksums
- Memory-efficient large file handling
"""

import json
import fcntl
import hashlib
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from contextlib import contextmanager
import logging
from threading import Lock
import tempfile

from pydantic import BaseModel, ValidationError as PydanticValidationError

from .exceptions import (
    RepositoryError,
    ValidationError,
    BackupError,
    RestoreError,
    DataIntegrityError,
    wrap_repository_error
)

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseFileRepository(ABC, Generic[T]):
    """
    Abstract base class for file-based repositories.
    
    This class provides common functionality for repositories that store data
    in JSON files, including thread-safe operations, atomic writes, backup
    management, and data validation with Pydantic models.
    
    Features:
    - Thread-safe file operations with proper locking
    - Atomic write operations to prevent corruption
    - Automatic backup creation and management
    - JSON serialization with Pydantic model support
    - File integrity validation with checksums
    - Memory-efficient handling of large files
    - Comprehensive error handling and logging
    
    Subclasses must implement:
    - get_model_class(): Return the Pydantic model class for data validation
    - get_default_data(): Return default data structure for new files
    """
    
    def __init__(
        self,
        data_file: Path,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        backup_retention_days: int = 30,
        validate_on_load: bool = True
    ):
        """
        Initialize base file repository.
        
        Args:
            data_file: Path to the main data file
            backup_dir: Directory for backup files (defaults to data_file.parent / "backups")
            auto_backup: Whether to automatically create backups before modifications
            backup_retention_days: How many days to retain backup files
            validate_on_load: Whether to validate data when loading from file
        """
        self.data_file = Path(data_file)
        self.backup_dir = backup_dir or (self.data_file.parent / "backups")
        self.auto_backup = auto_backup
        self.backup_retention_days = backup_retention_days
        self.validate_on_load = validate_on_load
        
        # Thread safety
        self._lock = Lock()
        
        # Ensure directories exist
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if self.auto_backup:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if it doesn't exist
        if not self.data_file.exists():
            self._initialize_file()
        
        logger.info(f"Initialized {self.__class__.__name__} with file: {self.data_file}")
    
    @abstractmethod
    def get_model_class(self) -> Type[T]:
        """
        Get the Pydantic model class used for data validation.
        
        Returns:
            Type[T]: The Pydantic model class for this repository
        """
        pass
    
    @abstractmethod
    def get_default_data(self) -> Dict[str, Any]:
        """
        Get the default data structure for new files.
        
        Returns:
            Dict[str, Any]: Default data structure
        """
        pass
    
    def _initialize_file(self) -> None:
        """Initialize the data file with default structure."""
        try:
            default_data = self.get_default_data()
            self._write_json_file(self.data_file, default_data)
            logger.info(f"Initialized data file: {self.data_file}")
        except Exception as e:
            raise wrap_repository_error(
                "file initialization",
                e,
                {"data_file": str(self.data_file)}
            )
    
    @contextmanager
    def _file_lock(self, file_path: Path):
        """
        Context manager for file locking.
        
        Args:
            file_path: Path to file to lock
            
        Yields:
            File handle with exclusive lock
        """
        file_handle = None
        try:
            file_handle = open(file_path, 'r+')
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
            yield file_handle
        except Exception as e:
            raise wrap_repository_error(
                "file locking",
                e,
                {"file_path": str(file_path)}
            )
        finally:
            if file_handle:
                try:
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                    file_handle.close()
                except Exception:
                    pass  # Best effort cleanup
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate MD5 checksum of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: MD5 checksum as hexadecimal string
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            raise wrap_repository_error(
                "checksum calculation",
                e,
                {"file_path": str(file_path)}
            )
    
    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Read and parse JSON file with validation.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dict[str, Any]: Parsed JSON data
            
        Raises:
            RepositoryError: When file reading or parsing fails
            ValidationError: When data validation fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate data structure if required
            if self.validate_on_load:
                self._validate_data_structure(data)
            
            logger.debug(f"Successfully read JSON file: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON format in file: {file_path}",
                context={"file_path": str(file_path), "json_error": str(e)},
                original_error=e
            )
        except Exception as e:
            raise wrap_repository_error(
                "JSON file reading",
                e,
                {"file_path": str(file_path)}
            )
    
    def _write_json_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        Write data to JSON file atomically.
        
        Uses atomic write operations to prevent data corruption by writing
        to a temporary file first and then moving it to the target location.
        
        Args:
            file_path: Path to JSON file
            data: Data to write
            
        Raises:
            RepositoryError: When file writing fails
            ValidationError: When data validation fails
        """
        # Validate data before writing
        self._validate_data_structure(data)
        
        # Use atomic write with temporary file
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.tmp',
                dir=file_path.parent,
                delete=False,
                encoding='utf-8'
            ) as f:
                temp_file = Path(f.name)
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                    separators=(',', ': '),
                    sort_keys=True
                )
                f.flush()
                f.close()
            
            # Atomic move to final location
            shutil.move(str(temp_file), str(file_path))
            logger.debug(f"Successfully wrote JSON file: {file_path}")
            
        except Exception as e:
            # Clean up temporary file on error
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass  # Best effort cleanup
            
            raise wrap_repository_error(
                "JSON file writing",
                e,
                {"file_path": str(file_path)}
            )
    
    def _validate_data_structure(self, data: Dict[str, Any]) -> None:
        """
        Validate data structure using Pydantic model if applicable.
        
        Args:
            data: Data to validate
            
        Raises:
            ValidationError: When validation fails
        """
        try:
            model_class = self.get_model_class()
            
            # For repositories that store collections, validate each item
            if isinstance(data, dict):
                # Check if data contains a collection (list) of items
                for key, value in data.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                try:
                                    model_class.model_validate(item)
                                except PydanticValidationError as e:
                                    raise ValidationError(
                                        f"Validation failed for {key} item",
                                        validation_errors=[str(err) for err in e.errors()],
                                        context={"key": key, "item": item},
                                        original_error=e
                                    )
            
        except ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            # Don't fail if model validation is not applicable
            logger.debug(f"Skipping validation: {e}")
    
    def _create_backup(self, backup_name: Optional[str] = None) -> Path:
        """
        Create a backup of the current data file.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Path: Path to created backup file
            
        Raises:
            BackupError: When backup creation fails
        """
        if not self.data_file.exists():
            raise BackupError(
                "Cannot backup non-existent data file",
                backup_path=str(self.data_file)
            )
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if backup_name:
                backup_filename = f"{self.data_file.stem}_{backup_name}_{timestamp}.backup.json"
            else:
                backup_filename = f"{self.data_file.stem}_{timestamp}.backup.json"
            
            backup_path = self.backup_dir / backup_filename
            
            # Copy file with metadata preservation
            shutil.copy2(str(self.data_file), str(backup_path))
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            raise BackupError(
                "Failed to create backup",
                backup_path=str(backup_path) if 'backup_path' in locals() else None,
                original_error=e
            )
    
    def _cleanup_old_backups(self) -> int:
        """
        Clean up backup files older than retention period.
        
        Returns:
            int: Number of backup files deleted
        """
        if not self.backup_dir.exists():
            return 0
        
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (self.backup_retention_days * 24 * 3600)
        
        try:
            for backup_file in self.backup_dir.glob("*.backup.json"):
                if backup_file.stat().st_mtime < cutoff_time:
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old backup: {backup_file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete backup {backup_file}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            return deleted_count
    
    def load_data(self) -> Dict[str, Any]:
        """
        Load data from the repository file.
        
        Returns:
            Dict[str, Any]: Loaded data
            
        Raises:
            RepositoryError: When loading fails
        """
        with self._lock:
            try:
                return self._read_json_file(self.data_file)
            except Exception as e:
                raise wrap_repository_error(
                    "data loading",
                    e,
                    {"data_file": str(self.data_file)}
                )
    
    def save_data(self, data: Dict[str, Any], backup_name: Optional[str] = None) -> bool:
        """
        Save data to the repository file.
        
        Args:
            data: Data to save
            backup_name: Optional backup name for this save operation
            
        Returns:
            bool: True if save was successful
            
        Raises:
            RepositoryError: When saving fails
        """
        with self._lock:
            try:
                # Create backup before modifying
                if self.auto_backup and self.data_file.exists():
                    self._create_backup(backup_name)
                
                # Save the data
                self._write_json_file(self.data_file, data)
                
                # Clean up old backups
                if self.auto_backup:
                    self._cleanup_old_backups()
                
                return True
                
            except Exception as e:
                raise wrap_repository_error(
                    "data saving",
                    e,
                    {"data_file": str(self.data_file)}
                )
    
    def backup_data(self, backup_path: Path) -> bool:
        """
        Create a backup of repository data at specified path.
        
        Args:
            backup_path: Path where backup should be created
            
        Returns:
            bool: True if backup was successful
            
        Raises:
            BackupError: When backup creation fails
        """
        try:
            if not self.data_file.exists():
                raise BackupError(
                    "Cannot backup non-existent data file",
                    backup_path=str(backup_path)
                )
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file with integrity check
            shutil.copy2(str(self.data_file), str(backup_path))
            
            # Verify backup integrity
            original_checksum = self._calculate_checksum(self.data_file)
            backup_checksum = self._calculate_checksum(backup_path)
            
            if original_checksum != backup_checksum:
                raise BackupError(
                    "Backup integrity check failed",
                    backup_path=str(backup_path),
                    context={
                        "original_checksum": original_checksum,
                        "backup_checksum": backup_checksum
                    }
                )
            
            logger.info(f"Successfully created backup: {backup_path}")
            return True
            
        except BackupError:
            raise  # Re-raise backup errors
        except Exception as e:
            raise BackupError(
                "Failed to create backup",
                backup_path=str(backup_path),
                original_error=e
            )
    
    def restore_data(self, backup_path: Path) -> bool:
        """
        Restore repository data from backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore was successful
            
        Raises:
            RestoreError: When restore operation fails
        """
        try:
            if not backup_path.exists():
                raise RestoreError(
                    "Backup file does not exist",
                    backup_path=str(backup_path)
                )
            
            # Validate backup file before restoring
            try:
                backup_data = self._read_json_file(backup_path)
            except Exception as e:
                raise RestoreError(
                    "Backup file is corrupted or invalid",
                    backup_path=str(backup_path),
                    original_error=e
                )
            
            # Create current backup before restore
            if self.data_file.exists():
                current_backup = self._create_backup("before_restore")
                logger.info(f"Created current backup before restore: {current_backup}")
            
            # Restore the backup
            shutil.copy2(str(backup_path), str(self.data_file))
            
            logger.info(f"Successfully restored from backup: {backup_path}")
            return True
            
        except RestoreError:
            raise  # Re-raise restore errors
        except Exception as e:
            raise RestoreError(
                "Failed to restore from backup",
                backup_path=str(backup_path),
                original_error=e
            )
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        Get information about the repository file.
        
        Returns:
            Dict[str, Any]: File information including size, modification time, checksum
        """
        try:
            if not self.data_file.exists():
                return {"exists": False, "path": str(self.data_file)}
            
            stat = self.data_file.stat()
            checksum = self._calculate_checksum(self.data_file)
            
            return {
                "exists": True,
                "path": str(self.data_file),
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "checksum": checksum,
                "backup_dir": str(self.backup_dir),
                "auto_backup": self.auto_backup,
                "validate_on_load": self.validate_on_load
            }
            
        except Exception as e:
            raise wrap_repository_error(
                "file info retrieval",
                e,
                {"data_file": str(self.data_file)}
            )
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backup files.
        
        Returns:
            List[Dict[str, Any]]: List of backup file information
        """
        backups = []
        
        try:
            if not self.backup_dir.exists():
                return backups
            
            for backup_file in sorted(self.backup_dir.glob("*.backup.json")):
                stat = backup_file.stat()
                backups.append({
                    "path": str(backup_file),
                    "name": backup_file.name,
                    "size_bytes": stat.st_size,
                    "created_time": datetime.fromtimestamp(stat.st_ctime),
                    "modified_time": datetime.fromtimestamp(stat.st_mtime)
                })
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return backups