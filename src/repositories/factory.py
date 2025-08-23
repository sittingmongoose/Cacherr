"""
Repository factory implementation for PlexCacheUltra.

This module provides the RepositoryFactory class that creates repository
instances based on configuration and environment settings. It integrates
with the dependency injection system to provide configured repositories
throughout the application.

Key Features:
- Configuration-driven repository creation
- Environment-aware path resolution
- Repository instance caching and lifecycle management
- Integration with dependency injection container
- Support for multiple repository backends (currently file-based)
- Comprehensive error handling and validation
"""

from typing import Dict, Any, Optional, Type, TypeVar, Generic
from pathlib import Path
import logging
from enum import Enum

from pydantic import BaseModel, Field, validator

from ..core.repositories import CacheRepository, ConfigRepository, MetricsRepository
from ..config.interfaces import PathConfiguration
from .cache_repository import CacheFileRepository
from .config_repository import ConfigFileRepository  
from .metrics_repository import MetricsFileRepository
from .exceptions import RepositoryError, ConfigurationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RepositoryType(str, Enum):
    """Enumeration of available repository types."""
    CACHE = "cache"
    CONFIG = "config"
    METRICS = "metrics"


class RepositoryBackend(str, Enum):
    """Enumeration of available repository backends."""
    FILE = "file"
    # Future backends could include: DATABASE, REDIS, etc.


class RepositoryConfig(BaseModel):
    """
    Configuration for repository creation.
    
    This model defines the configuration parameters needed to create
    repository instances, including backend selection, file paths,
    and operational settings.
    """
    
    backend: RepositoryBackend = Field(
        default=RepositoryBackend.FILE,
        description="Repository backend type"
    )
    data_file: str = Field(
        description="Path to data file for file-based repositories"
    )
    backup_dir: Optional[str] = Field(
        default=None,
        description="Directory for backup files"
    )
    auto_backup: bool = Field(
        default=True,
        description="Whether to automatically create backups"
    )
    backup_retention_days: int = Field(
        default=30,
        description="Days to retain backup files",
        ge=1,
        le=365
    )
    
    # Repository-specific settings
    cache_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Cache repository specific settings"
    )
    config_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Config repository specific settings"
    )
    metrics_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics repository specific settings"
    )
    
    @validator('data_file')
    def validate_data_file(cls, v):
        """Validate that data file path is not empty."""
        if not v or not v.strip():
            raise ValueError("data_file cannot be empty")
        return v.strip()
    
    @validator('backup_retention_days')
    def validate_retention_days(cls, v):
        """Validate backup retention period."""
        if v < 1:
            raise ValueError("backup_retention_days must be at least 1")
        if v > 365:
            raise ValueError("backup_retention_days cannot exceed 365")
        return v


class RepositoryFactory:
    """
    Factory class for creating repository instances.
    
    This factory creates repository instances based on configuration
    and integrates with the dependency injection system. It provides
    a centralized way to create and configure repositories throughout
    the application.
    
    Features:
    - Configuration-driven repository creation
    - Environment-aware path resolution
    - Repository instance caching for performance
    - Integration with dependency injection container
    - Support for multiple repository backends
    - Comprehensive error handling and logging
    
    Usage:
        factory = RepositoryFactory(path_config)
        
        # Create cache repository
        cache_repo = factory.create_cache_repository(config)
        
        # Create all repositories with default config
        repositories = factory.create_all_repositories()
        
        # Get cached repository instance
        cache_repo = factory.get_repository("cache")
    """
    
    def __init__(
        self,
        path_configuration: PathConfiguration,
        default_config: Optional[Dict[RepositoryType, RepositoryConfig]] = None
    ):
        """
        Initialize repository factory.
        
        Args:
            path_configuration: Path configuration for environment-aware paths
            default_config: Default repository configurations
        """
        self.path_configuration = path_configuration
        self.default_config = default_config or self._get_default_configurations()
        
        # Cache for repository instances
        self._repository_cache: Dict[RepositoryType, Any] = {}
        
        logger.info("Initialized RepositoryFactory")
    
    def _get_default_configurations(self) -> Dict[RepositoryType, RepositoryConfig]:
        """Get default repository configurations."""
        # Get default paths and use cache_destination as data directory
        default_paths = self.path_configuration.get_default_paths()
        data_dir = Path(default_paths.cache_destination).parent / "data"
        backup_dir = data_dir / "backups"
        
        return {
            RepositoryType.CACHE: RepositoryConfig(
                backend=RepositoryBackend.FILE,
                data_file=str(data_dir / "cache_data.json"),
                backup_dir=str(backup_dir / "cache"),
                auto_backup=True,
                backup_retention_days=30,
                cache_settings={}
            ),
            RepositoryType.CONFIG: RepositoryConfig(
                backend=RepositoryBackend.FILE,
                data_file=str(data_dir / "config_data.json"),
                backup_dir=str(backup_dir / "config"),
                auto_backup=True,
                backup_retention_days=60,
                config_settings={
                    "max_history_entries": 50
                }
            ),
            RepositoryType.METRICS: RepositoryConfig(
                backend=RepositoryBackend.FILE,
                data_file=str(data_dir / "metrics_data.json"),
                backup_dir=str(backup_dir / "metrics"),
                auto_backup=True,
                backup_retention_days=30,
                metrics_settings={
                    "metrics_retention_days": 90,
                    "activity_retention_days": 365
                }
            )
        }
    
    def create_cache_repository(
        self,
        config: Optional[RepositoryConfig] = None
    ) -> CacheRepository:
        """
        Create a cache repository instance.
        
        Args:
            config: Repository configuration (uses default if not provided)
            
        Returns:
            CacheRepository: Configured cache repository instance
            
        Raises:
            RepositoryError: When repository creation fails
        """
        if config is None:
            config = self.default_config[RepositoryType.CACHE]
        
        try:
            if config.backend == RepositoryBackend.FILE:
                return CacheFileRepository(
                    data_file=Path(config.data_file),
                    backup_dir=Path(config.backup_dir) if config.backup_dir else None,
                    auto_backup=config.auto_backup,
                    backup_retention_days=config.backup_retention_days
                )
            else:
                raise RepositoryError(
                    f"Unsupported repository backend: {config.backend}",
                    error_code="UNSUPPORTED_BACKEND",
                    context={"backend": config.backend, "repository_type": "cache"}
                )
                
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(
                "Failed to create cache repository",
                error_code="REPOSITORY_CREATION_FAILED",
                context={"repository_type": "cache", "backend": config.backend},
                original_error=e
            )
    
    def create_config_repository(
        self,
        config: Optional[RepositoryConfig] = None
    ) -> ConfigRepository:
        """
        Create a configuration repository instance.
        
        Args:
            config: Repository configuration (uses default if not provided)
            
        Returns:
            ConfigRepository: Configured configuration repository instance
            
        Raises:
            RepositoryError: When repository creation fails
        """
        if config is None:
            config = self.default_config[RepositoryType.CONFIG]
        
        try:
            if config.backend == RepositoryBackend.FILE:
                max_history_entries = config.config_settings.get("max_history_entries", 50)
                
                return ConfigFileRepository(
                    data_file=Path(config.data_file),
                    backup_dir=Path(config.backup_dir) if config.backup_dir else None,
                    auto_backup=config.auto_backup,
                    backup_retention_days=config.backup_retention_days,
                    max_history_entries=max_history_entries
                )
            else:
                raise RepositoryError(
                    f"Unsupported repository backend: {config.backend}",
                    error_code="UNSUPPORTED_BACKEND",
                    context={"backend": config.backend, "repository_type": "config"}
                )
                
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(
                "Failed to create config repository",
                error_code="REPOSITORY_CREATION_FAILED",
                context={"repository_type": "config", "backend": config.backend},
                original_error=e
            )
    
    def create_metrics_repository(
        self,
        config: Optional[RepositoryConfig] = None
    ) -> MetricsRepository:
        """
        Create a metrics repository instance.
        
        Args:
            config: Repository configuration (uses default if not provided)
            
        Returns:
            MetricsRepository: Configured metrics repository instance
            
        Raises:
            RepositoryError: When repository creation fails
        """
        if config is None:
            config = self.default_config[RepositoryType.METRICS]
        
        try:
            if config.backend == RepositoryBackend.FILE:
                metrics_retention_days = config.metrics_settings.get("metrics_retention_days", 90)
                activity_retention_days = config.metrics_settings.get("activity_retention_days", 365)
                
                return MetricsFileRepository(
                    data_file=Path(config.data_file),
                    backup_dir=Path(config.backup_dir) if config.backup_dir else None,
                    auto_backup=config.auto_backup,
                    backup_retention_days=config.backup_retention_days,
                    metrics_retention_days=metrics_retention_days,
                    activity_retention_days=activity_retention_days
                )
            else:
                raise RepositoryError(
                    f"Unsupported repository backend: {config.backend}",
                    error_code="UNSUPPORTED_BACKEND",
                    context={"backend": config.backend, "repository_type": "metrics"}
                )
                
        except Exception as e:
            if isinstance(e, RepositoryError):
                raise
            raise RepositoryError(
                "Failed to create metrics repository",
                error_code="REPOSITORY_CREATION_FAILED",
                context={"repository_type": "metrics", "backend": config.backend},
                original_error=e
            )
    
    def create_all_repositories(
        self,
        configs: Optional[Dict[RepositoryType, RepositoryConfig]] = None
    ) -> Dict[RepositoryType, Any]:
        """
        Create all repository instances.
        
        Args:
            configs: Repository configurations (uses defaults if not provided)
            
        Returns:
            Dict[RepositoryType, Any]: Dictionary of repository instances
            
        Raises:
            RepositoryError: When any repository creation fails
        """
        if configs is None:
            configs = self.default_config
        
        repositories = {}
        creation_errors = []
        
        # Create cache repository
        try:
            repositories[RepositoryType.CACHE] = self.create_cache_repository(
                configs.get(RepositoryType.CACHE)
            )
            logger.info("Created cache repository")
        except Exception as e:
            creation_errors.append(f"Cache repository: {e}")
            logger.error(f"Failed to create cache repository: {e}")
        
        # Create config repository
        try:
            repositories[RepositoryType.CONFIG] = self.create_config_repository(
                configs.get(RepositoryType.CONFIG)
            )
            logger.info("Created config repository")
        except Exception as e:
            creation_errors.append(f"Config repository: {e}")
            logger.error(f"Failed to create config repository: {e}")
        
        # Create metrics repository
        try:
            repositories[RepositoryType.METRICS] = self.create_metrics_repository(
                configs.get(RepositoryType.METRICS)
            )
            logger.info("Created metrics repository")
        except Exception as e:
            creation_errors.append(f"Metrics repository: {e}")
            logger.error(f"Failed to create metrics repository: {e}")
        
        if not repositories:
            raise RepositoryError(
                "Failed to create any repositories",
                error_code="ALL_REPOSITORIES_FAILED",
                context={"errors": creation_errors}
            )
        
        if creation_errors:
            logger.warning(f"Some repositories failed to create: {creation_errors}")
        
        return repositories
    
    def get_or_create_repository(
        self,
        repository_type: RepositoryType,
        config: Optional[RepositoryConfig] = None,
        use_cache: bool = True
    ) -> Any:
        """
        Get or create a repository instance with caching.
        
        Args:
            repository_type: Type of repository to create
            config: Repository configuration
            use_cache: Whether to use cached instances
            
        Returns:
            Repository instance of requested type
            
        Raises:
            RepositoryError: When repository creation fails
        """
        # Check cache first
        if use_cache and repository_type in self._repository_cache:
            logger.debug(f"Returning cached {repository_type} repository")
            return self._repository_cache[repository_type]
        
        # Create new repository
        if repository_type == RepositoryType.CACHE:
            repository = self.create_cache_repository(config)
        elif repository_type == RepositoryType.CONFIG:
            repository = self.create_config_repository(config)
        elif repository_type == RepositoryType.METRICS:
            repository = self.create_metrics_repository(config)
        else:
            raise RepositoryError(
                f"Unknown repository type: {repository_type}",
                error_code="UNKNOWN_REPOSITORY_TYPE",
                context={"repository_type": repository_type}
            )
        
        # Cache the instance
        if use_cache:
            self._repository_cache[repository_type] = repository
            logger.debug(f"Cached {repository_type} repository instance")
        
        return repository
    
    def clear_cache(self, repository_type: Optional[RepositoryType] = None) -> None:
        """
        Clear repository instance cache.
        
        Args:
            repository_type: Specific repository type to clear (clears all if None)
        """
        if repository_type is None:
            self._repository_cache.clear()
            logger.info("Cleared all repository cache")
        else:
            self._repository_cache.pop(repository_type, None)
            logger.info(f"Cleared {repository_type} repository cache")
    
    def validate_configuration(
        self,
        config: RepositoryConfig,
        repository_type: RepositoryType
    ) -> bool:
        """
        Validate repository configuration.
        
        Args:
            config: Repository configuration to validate
            repository_type: Type of repository
            
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ConfigurationError: When configuration is invalid
        """
        try:
            # Validate basic configuration
            config.model_validate(config.model_dump())
            
            # Validate paths exist or can be created
            data_file_path = Path(config.data_file)
            data_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config.backup_dir:
                backup_dir_path = Path(config.backup_dir)
                backup_dir_path.mkdir(parents=True, exist_ok=True)
            
            # Repository-specific validation
            if repository_type == RepositoryType.CONFIG:
                max_history = config.config_settings.get("max_history_entries", 50)
                if not isinstance(max_history, int) or max_history < 1:
                    raise ConfigurationError(
                        "max_history_entries must be a positive integer",
                        config_section="config_settings",
                        config_key="max_history_entries"
                    )
            
            elif repository_type == RepositoryType.METRICS:
                metrics_retention = config.metrics_settings.get("metrics_retention_days", 90)
                activity_retention = config.metrics_settings.get("activity_retention_days", 365)
                
                if not isinstance(metrics_retention, int) or metrics_retention < 1:
                    raise ConfigurationError(
                        "metrics_retention_days must be a positive integer",
                        config_section="metrics_settings",
                        config_key="metrics_retention_days"
                    )
                
                if not isinstance(activity_retention, int) or activity_retention < 1:
                    raise ConfigurationError(
                        "activity_retention_days must be a positive integer",
                        config_section="metrics_settings",
                        config_key="activity_retention_days"
                    )
            
            logger.debug(f"Configuration validated for {repository_type} repository")
            return True
            
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Configuration validation failed for {repository_type} repository",
                config_section=str(repository_type),
                original_error=e
            )
    
    def get_repository_status(self) -> Dict[str, Any]:
        """
        Get status information for all repositories.
        
        Returns:
            Dict[str, Any]: Repository status information
        """
        status = {
            "cached_repositories": list(self._repository_cache.keys()),
            "default_configurations": {
                repo_type.value: {
                    "backend": config.backend.value,
                    "data_file": config.data_file,
                    "auto_backup": config.auto_backup,
                    "backup_retention_days": config.backup_retention_days
                }
                for repo_type, config in self.default_config.items()
            },
            "factory_initialized": True,
            "path_configuration": {
                "default_paths": self.path_configuration.get_default_paths().model_dump()
            }
        }
        
        # Add file information for cached repositories
        for repo_type, repository in self._repository_cache.items():
            if hasattr(repository, 'get_file_info'):
                try:
                    status[f"{repo_type.value}_file_info"] = repository.get_file_info()
                except Exception as e:
                    status[f"{repo_type.value}_file_info"] = {"error": str(e)}
        
        return status
    
    def create_repository_from_config_dict(
        self,
        repository_type: RepositoryType,
        config_dict: Dict[str, Any]
    ) -> Any:
        """
        Create repository from configuration dictionary.
        
        Args:
            repository_type: Type of repository to create
            config_dict: Configuration dictionary
            
        Returns:
            Repository instance
            
        Raises:
            ConfigurationError: When configuration is invalid
            RepositoryError: When repository creation fails
        """
        try:
            # Create configuration object from dictionary
            config = RepositoryConfig.model_validate(config_dict)
            
            # Validate configuration
            self.validate_configuration(config, repository_type)
            
            # Create repository
            return self.get_or_create_repository(repository_type, config, use_cache=False)
            
        except Exception as e:
            if isinstance(e, (ConfigurationError, RepositoryError)):
                raise
            raise ConfigurationError(
                f"Failed to create {repository_type} repository from config dict",
                config_section=str(repository_type),
                original_error=e
            )