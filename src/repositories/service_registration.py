"""
Service registration for repository implementations.

This module provides utilities to register repository services with the
dependency injection container. It handles the creation of repository
factories and registers them with appropriate lifetimes and dependencies.

Key Features:
- Automatic repository service registration
- Integration with existing DI container
- Configuration-driven repository setup
- Factory pattern registration
- Proper service lifetime management
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ..core.container import DIContainer, ServiceLifetime
from ..core.repositories import CacheRepository, ConfigRepository, MetricsRepository
from ..config.interfaces import PathConfiguration
from .factory import RepositoryFactory, RepositoryType, RepositoryConfig
from .cache_repository import CacheFileRepository
from .config_repository import ConfigFileRepository
from .metrics_repository import MetricsFileRepository

logger = logging.getLogger(__name__)


class RepositoryServiceRegistration:
    """
    Utility class for registering repository services with the DI container.
    
    This class provides methods to register repository services, factories,
    and their dependencies with the dependency injection container. It ensures
    proper service lifetime management and configuration injection.
    
    Features:
    - Automatic registration of all repository types
    - Factory pattern integration with DI container
    - Configuration-driven repository setup
    - Service lifetime management
    - Proper dependency injection setup
    
    Usage:
        registration = RepositoryServiceRegistration(container, path_config)
        registration.register_all_repositories()
        
        # Or register individual repositories
        registration.register_cache_repository()
        registration.register_config_repository()
        registration.register_metrics_repository()
    """
    
    def __init__(
        self,
        container: DIContainer,
        path_configuration: Optional[PathConfiguration] = None,
        repository_configs: Optional[Dict[RepositoryType, RepositoryConfig]] = None
    ):
        """
        Initialize repository service registration.
        
        Args:
            container: Dependency injection container
            path_configuration: Path configuration for repository paths
            repository_configs: Custom repository configurations
        """
        self.container = container
        self.path_configuration = path_configuration
        self.repository_configs = repository_configs
        
        logger.info("Initialized repository service registration")
    
    def register_repository_factory(self) -> None:
        """Register the repository factory as a singleton service."""
        def create_repository_factory(container: DIContainer) -> RepositoryFactory:
            """Factory function to create RepositoryFactory instance."""
            path_config = container.try_resolve(PathConfiguration)
            
            if path_config is None:
                logger.warning("PathConfiguration not found in container, using minimal default")
                # Create a minimal path configuration if not available
                from ..config.interfaces import PathConfigurationModel
                
                class MinimalPathConfiguration:
                    def get_default_paths(self) -> PathConfigurationModel:
                        return PathConfigurationModel(
                            plex_source="/media",
                            cache_destination="/cache"
                        )
                
                path_config = MinimalPathConfiguration()
            
            factory = RepositoryFactory(
                path_configuration=path_config,
                default_config=self.repository_configs
            )
            
            logger.info("Created RepositoryFactory instance")
            return factory
        
        # Register factory as singleton
        self.container.register_factory(
            RepositoryFactory,
            create_repository_factory,
            ServiceLifetime.SINGLETON
        )
        
        logger.info("Registered RepositoryFactory as singleton service")
    
    def register_cache_repository(self) -> None:
        """Register cache repository service."""
        def create_cache_repository(container: DIContainer) -> CacheRepository:
            """Factory function to create cache repository."""
            factory = container.resolve(RepositoryFactory)
            repository = factory.get_or_create_repository(RepositoryType.CACHE)
            
            logger.info("Created CacheRepository instance")
            return repository
        
        # Register as singleton (repositories maintain their own data)
        self.container.register_factory(
            CacheRepository,
            create_cache_repository,
            ServiceLifetime.SINGLETON
        )
        
        logger.info("Registered CacheRepository service")
    
    def register_config_repository(self) -> None:
        """Register configuration repository service."""
        def create_config_repository(container: DIContainer) -> ConfigRepository:
            """Factory function to create configuration repository."""
            factory = container.resolve(RepositoryFactory)
            repository = factory.get_or_create_repository(RepositoryType.CONFIG)
            
            logger.info("Created ConfigRepository instance")
            return repository
        
        # Register as singleton
        self.container.register_factory(
            ConfigRepository,
            create_config_repository,
            ServiceLifetime.SINGLETON
        )
        
        logger.info("Registered ConfigRepository service")
    
    def register_metrics_repository(self) -> None:
        """Register metrics repository service."""
        def create_metrics_repository(container: DIContainer) -> MetricsRepository:
            """Factory function to create metrics repository."""
            factory = container.resolve(RepositoryFactory)
            repository = factory.get_or_create_repository(RepositoryType.METRICS)
            
            logger.info("Created MetricsRepository instance")
            return repository
        
        # Register as singleton
        self.container.register_factory(
            MetricsRepository,
            create_metrics_repository,
            ServiceLifetime.SINGLETON
        )
        
        logger.info("Registered MetricsRepository service")
    
    def register_all_repositories(self) -> None:
        """
        Register all repository services with the container.
        
        This method registers:
        1. RepositoryFactory as a singleton
        2. CacheRepository service
        3. ConfigRepository service  
        4. MetricsRepository service
        
        All repositories are registered as singletons since they manage
        their own data and state.
        """
        logger.info("Starting registration of all repository services")
        
        # Register factory first (required by other services)
        self.register_repository_factory()
        
        # Register individual repositories
        self.register_cache_repository()
        self.register_config_repository()
        self.register_metrics_repository()
        
        logger.info("Completed registration of all repository services")
    
    def register_concrete_implementations(self) -> None:
        """
        Register concrete repository implementations directly.
        
        This method registers the concrete repository classes directly
        without going through the factory. Useful for scenarios where
        specific implementations are needed.
        """
        logger.info("Registering concrete repository implementations")
        
        # Register concrete cache repository
        def create_cache_file_repository(container: DIContainer) -> CacheFileRepository:
            path_config = container.resolve(PathConfiguration)
            default_paths = path_config.get_default_paths()
            data_dir = Path(default_paths.cache_destination).parent / "data"
            
            return CacheFileRepository(
                data_file=data_dir / "cache_data.json",
                auto_backup=True
            )
        
        self.container.register_factory(
            CacheFileRepository,
            create_cache_file_repository,
            ServiceLifetime.SINGLETON
        )
        
        # Register concrete config repository
        def create_config_file_repository(container: DIContainer) -> ConfigFileRepository:
            path_config = container.resolve(PathConfiguration)
            default_paths = path_config.get_default_paths()
            data_dir = Path(default_paths.cache_destination).parent / "data"
            
            return ConfigFileRepository(
                data_file=data_dir / "config_data.json",
                auto_backup=True,
                max_history_entries=50
            )
        
        self.container.register_factory(
            ConfigFileRepository,
            create_config_file_repository,
            ServiceLifetime.SINGLETON
        )
        
        # Register concrete metrics repository
        def create_metrics_file_repository(container: DIContainer) -> MetricsFileRepository:
            path_config = container.resolve(PathConfiguration)
            default_paths = path_config.get_default_paths()
            data_dir = Path(default_paths.cache_destination).parent / "data"
            
            return MetricsFileRepository(
                data_file=data_dir / "metrics_data.json",
                auto_backup=True,
                metrics_retention_days=90,
                activity_retention_days=365
            )
        
        self.container.register_factory(
            MetricsFileRepository,
            create_metrics_file_repository,
            ServiceLifetime.SINGLETON
        )
        
        logger.info("Completed registration of concrete repository implementations")
    
    def validate_registrations(self) -> Dict[str, bool]:
        """
        Validate that all repository services can be resolved.
        
        Returns:
            Dict[str, bool]: Validation results for each service
        """
        validation_results = {}
        
        # Test RepositoryFactory
        try:
            factory = self.container.resolve(RepositoryFactory)
            validation_results["RepositoryFactory"] = factory is not None
        except Exception as e:
            logger.error(f"Failed to resolve RepositoryFactory: {e}")
            validation_results["RepositoryFactory"] = False
        
        # Test CacheRepository
        try:
            cache_repo = self.container.resolve(CacheRepository)
            validation_results["CacheRepository"] = cache_repo is not None
        except Exception as e:
            logger.error(f"Failed to resolve CacheRepository: {e}")
            validation_results["CacheRepository"] = False
        
        # Test ConfigRepository
        try:
            config_repo = self.container.resolve(ConfigRepository)
            validation_results["ConfigRepository"] = config_repo is not None
        except Exception as e:
            logger.error(f"Failed to resolve ConfigRepository: {e}")
            validation_results["ConfigRepository"] = False
        
        # Test MetricsRepository
        try:
            metrics_repo = self.container.resolve(MetricsRepository)
            validation_results["MetricsRepository"] = metrics_repo is not None
        except Exception as e:
            logger.error(f"Failed to resolve MetricsRepository: {e}")
            validation_results["MetricsRepository"] = False
        
        # Log validation summary
        successful = sum(validation_results.values())
        total = len(validation_results)
        logger.info(f"Repository service validation: {successful}/{total} services resolved successfully")
        
        if successful < total:
            failed_services = [name for name, result in validation_results.items() if not result]
            logger.warning(f"Failed to resolve services: {', '.join(failed_services)}")
        
        return validation_results
    
    def get_registration_status(self) -> Dict[str, Any]:
        """
        Get status information about repository service registrations.
        
        Returns:
            Dict[str, Any]: Status information
        """
        status = {
            "factory_registered": False,
            "cache_repository_registered": False,
            "config_repository_registered": False,
            "metrics_repository_registered": False,
            "validation_results": {},
            "total_repository_services": 0
        }
        
        # Check if services are registered (this is a simplified check)
        try:
            self.container.resolve(RepositoryFactory)
            status["factory_registered"] = True
        except Exception:
            pass
        
        try:
            self.container.resolve(CacheRepository)
            status["cache_repository_registered"] = True
        except Exception:
            pass
        
        try:
            self.container.resolve(ConfigRepository)
            status["config_repository_registered"] = True
        except Exception:
            pass
        
        try:
            self.container.resolve(MetricsRepository)
            status["metrics_repository_registered"] = True
        except Exception:
            pass
        
        # Count total registered repository services
        registered_count = sum([
            status["factory_registered"],
            status["cache_repository_registered"],
            status["config_repository_registered"],
            status["metrics_repository_registered"]
        ])
        status["total_repository_services"] = registered_count
        
        # Run validation if any services are registered
        if registered_count > 0:
            status["validation_results"] = self.validate_registrations()
        
        return status


def register_repository_services(
    container: DIContainer,
    path_configuration: Optional[PathConfiguration] = None,
    repository_configs: Optional[Dict[RepositoryType, RepositoryConfig]] = None,
    include_concrete_implementations: bool = False
) -> RepositoryServiceRegistration:
    """
    Convenience function to register all repository services.
    
    Args:
        container: Dependency injection container
        path_configuration: Path configuration for repository paths
        repository_configs: Custom repository configurations
        include_concrete_implementations: Whether to also register concrete implementations
        
    Returns:
        RepositoryServiceRegistration: Registration utility instance
    """
    registration = RepositoryServiceRegistration(
        container=container,
        path_configuration=path_configuration,
        repository_configs=repository_configs
    )
    
    # Register all repository services
    registration.register_all_repositories()
    
    # Optionally register concrete implementations
    if include_concrete_implementations:
        registration.register_concrete_implementations()
    
    # Validate registrations
    validation_results = registration.validate_registrations()
    
    if all(validation_results.values()):
        logger.info("All repository services registered and validated successfully")
    else:
        logger.warning("Some repository services failed validation")
    
    return registration