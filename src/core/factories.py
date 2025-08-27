"""
Service Factory Pattern implementations for PlexCacheUltra.

This module provides factory classes and functions for creating services with
complex initialization logic, configuration-driven creation, and environment-specific
implementations. Factories decouple service creation from service usage and enable
flexible service instantiation strategies.

The factory pattern is particularly useful for:
- Services requiring complex initialization
- Environment-specific service implementations
- Services with external dependencies (databases, APIs, etc.)
- Services requiring configuration validation before creation
- Services with multiple creation strategies

Example:
    Basic factory usage:
    
    ```python
    factory = MediaServiceFactory(config_provider)
    media_service = factory.create()
    ```
    
    Factory with DI container:
    
    ```python
    container.register_factory(
        MediaService,
        MediaServiceFactory.create_factory(config_provider)
    )
    ```
"""

import logging
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Optional, Dict, Any, Callable, List
from pathlib import Path
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .interfaces import (
    MediaService, FileService, NotificationService, CacheService,
    MediaFileInfo, CacheOperationResult, TestModeAnalysis, NotificationEvent
)
from .repositories import CacheRepository, ConfigRepository, MetricsRepository
from ..config.interfaces import (
    ConfigProvider, EnvironmentConfig, PathConfiguration,
    PlexConfiguration, PathConfigurationModel, PerformanceConfiguration,
    MediaConfiguration, NotificationConfiguration, TestModeConfiguration
)
from .container import IServiceProvider, ServiceLifetime

T = TypeVar('T')
logger = logging.getLogger(__name__)


class FactoryError(Exception):
    """Base exception for factory-related errors."""
    pass


class ServiceCreationError(FactoryError):
    """Raised when service creation fails."""
    
    def __init__(self, service_type: Type, reason: str, inner_exception: Exception = None):
        self.service_type = service_type
        self.reason = reason
        self.inner_exception = inner_exception
        
        message = f"Failed to create service '{service_type.__name__}': {reason}"
        if inner_exception:
            message += f" (Inner exception: {str(inner_exception)})"
        
        super().__init__(message)


class ConfigurationValidationError(FactoryError):
    """Raised when service configuration validation fails."""
    
    def __init__(self, service_type: Type, validation_errors: List[str]):
        self.service_type = service_type
        self.validation_errors = validation_errors
        
        message = f"Configuration validation failed for '{service_type.__name__}': "
        message += ", ".join(validation_errors)
        
        super().__init__(message)


class FactoryConfiguration(BaseModel):
    """
    Configuration for service factories.
    
    Attributes:
        creation_timeout_seconds: Maximum time allowed for service creation
        retry_count: Number of creation attempts on failure
        retry_delay_seconds: Delay between retry attempts
        validate_config_before_creation: Whether to validate configuration before creation
        enable_creation_logging: Whether to log detailed creation information
        fallback_to_default: Whether to fall back to default implementations on failure
    """
    creation_timeout_seconds: int = 30
    retry_count: int = 3
    retry_delay_seconds: int = 1
    validate_config_before_creation: bool = True
    enable_creation_logging: bool = True
    fallback_to_default: bool = False
    
    @field_validator('creation_timeout_seconds', 'retry_count', 'retry_delay_seconds')
    @classmethod
    def validate_positive_values(cls, v):
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class IServiceFactory(ABC, Generic[T]):
    """
    Interface for service factories.
    
    Defines the contract for creating services with validation and error handling.
    """
    
    @abstractmethod
    def create(self, provider: Optional[IServiceProvider] = None) -> T:
        """
        Create a service instance.
        
        Args:
            provider: Optional service provider for dependency resolution
            
        Returns:
            Created service instance
            
        Raises:
            ServiceCreationError: When service creation fails
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> List[str]:
        """
        Validate the configuration required for service creation.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        pass
    
    @abstractmethod
    def can_create(self) -> bool:
        """
        Check if the factory can create a service instance.
        
        Returns:
            True if service can be created, False otherwise
        """
        pass


class BaseServiceFactory(IServiceFactory[T], ABC):
    """
    Base implementation for service factories.
    
    Provides common functionality including configuration validation,
    retry logic, and error handling.
    """
    
    def __init__(self, config_provider: ConfigProvider, 
                 factory_config: Optional[FactoryConfiguration] = None):
        """
        Initialize the base service factory.
        
        Args:
            config_provider: Configuration provider for service settings
            factory_config: Factory-specific configuration
        """
        self.config_provider = config_provider
        self.factory_config = factory_config or FactoryConfiguration()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create(self, provider: Optional[IServiceProvider] = None) -> T:
        """Create a service instance with validation and retry logic."""
        if self.factory_config.validate_config_before_creation:
            validation_errors = self.validate_configuration()
            if validation_errors:
                raise ConfigurationValidationError(self.get_service_type(), validation_errors)
        
        if not self.can_create():
            raise ServiceCreationError(
                self.get_service_type(),
                "Factory indicates it cannot create service instance"
            )
        
        last_exception = None
        for attempt in range(self.factory_config.retry_count + 1):
            try:
                if self.factory_config.enable_creation_logging:
                    self._logger.info(
                        "Creating service %s (attempt %d/%d)",
                        self.get_service_type().__name__,
                        attempt + 1,
                        self.factory_config.retry_count + 1
                    )
                
                instance = self._create_instance(provider)
                
                if self.factory_config.enable_creation_logging:
                    self._logger.info(
                        "Successfully created service %s",
                        self.get_service_type().__name__
                    )
                
                return instance
                
            except Exception as e:
                last_exception = e
                self._logger.warning(
                    "Service creation attempt %d failed for %s: %s",
                    attempt + 1,
                    self.get_service_type().__name__,
                    str(e)
                )
                
                if attempt < self.factory_config.retry_count:
                    import time
                    time.sleep(self.factory_config.retry_delay_seconds)
                else:
                    break
        
        # All attempts failed
        if self.factory_config.fallback_to_default:
            try:
                return self._create_default_instance(provider)
            except Exception as fallback_exception:
                self._logger.error(
                    "Fallback creation also failed for %s: %s",
                    self.get_service_type().__name__,
                    str(fallback_exception)
                )
        
        raise ServiceCreationError(
            self.get_service_type(),
            f"All {self.factory_config.retry_count + 1} creation attempts failed",
            last_exception
        )
    
    @abstractmethod
    def _create_instance(self, provider: Optional[IServiceProvider] = None) -> T:
        """Create the actual service instance."""
        pass
    
    @abstractmethod
    def get_service_type(self) -> Type[T]:
        """Get the service type this factory creates."""
        pass
    
    def _create_default_instance(self, provider: Optional[IServiceProvider] = None) -> T:
        """Create a default fallback instance. Override if fallback is supported."""
        raise NotImplementedError("Fallback creation not implemented for this factory")
    
    def can_create(self) -> bool:
        """Default implementation checks if configuration is valid."""
        return len(self.validate_configuration()) == 0


class MediaServiceFactory(BaseServiceFactory[MediaService]):
    """
    Factory for creating MediaService implementations.
    
    Creates appropriate MediaService implementation based on configuration
    and environment. Supports Plex integration with validation and fallbacks.
    """
    
    def __init__(self, config_provider: ConfigProvider, 
                 factory_config: Optional[FactoryConfiguration] = None):
        super().__init__(config_provider, factory_config)
        self._plex_config: Optional[PlexConfiguration] = None
    
    def validate_configuration(self) -> List[str]:
        """Validate Plex configuration for MediaService creation."""
        errors = []
        
        try:
            plex_url = self.config_provider.get_string("PLEX_URL")
            if not plex_url:
                errors.append("PLEX_URL is required")
            elif not plex_url.startswith(('http://', 'https://')):
                errors.append("PLEX_URL must be a valid URL")
            
            plex_token = self.config_provider.get_string("PLEX_TOKEN")
            if not plex_token:
                errors.append("PLEX_TOKEN is required")
            elif len(plex_token) < 10:
                errors.append("PLEX_TOKEN appears to be invalid")
            
            # Validate optional parameters
            timeout = self.config_provider.get_int("PLEX_TIMEOUT", 30)
            if timeout <= 0:
                errors.append("PLEX_TIMEOUT must be positive")
            
            retry_limit = self.config_provider.get_int("PLEX_RETRY_LIMIT", 3)
            if retry_limit < 0:
                errors.append("PLEX_RETRY_LIMIT must be non-negative")
            
            # Create configuration object for validation
            if not errors:
                self._plex_config = PlexConfiguration(
                    url=plex_url,
                    token=plex_token,
                    timeout=timeout,
                    retry_limit=retry_limit,
                    retry_delay=self.config_provider.get_int("PLEX_RETRY_DELAY", 5)
                )
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def _create_instance(self, provider: Optional[IServiceProvider] = None) -> MediaService:
        """Create MediaService implementation."""
        if not self._plex_config:
            # Re-validate to populate config
            validation_errors = self.validate_configuration()
            if validation_errors:
                raise ServiceCreationError(
                    MediaService,
                    f"Invalid configuration: {', '.join(validation_errors)}"
                )
        
        # Import the actual implementation here to avoid circular imports
        try:
            from ..core.plex_operations import PlexOperations
            
            # Create PlexOperations instance with configuration
            media_service = PlexOperations()
            
            # Configure the service (this would depend on the actual implementation)
            if hasattr(media_service, 'configure'):
                media_service.configure(self._plex_config)
            
            return media_service
            
        except ImportError as e:
            raise ServiceCreationError(
                MediaService,
                f"Failed to import PlexOperations: {str(e)}",
                e
            )
        except Exception as e:
            raise ServiceCreationError(
                MediaService,
                f"Failed to create PlexOperations instance: {str(e)}",
                e
            )
    
    def get_service_type(self) -> Type[MediaService]:
        return MediaService
    
    @staticmethod
    def create_factory(config_provider: ConfigProvider) -> Callable[[IServiceProvider], MediaService]:
        """Create a factory function for DI container registration."""
        factory_instance = MediaServiceFactory(config_provider)
        return lambda provider: factory_instance.create(provider)


class FileServiceFactory(BaseServiceFactory[FileService]):
    """
    Factory for creating FileService implementations.
    
    Creates file service with path validation and performance configuration.
    """
    
    def __init__(self, config_provider: ConfigProvider, 
                 path_config: Optional[PathConfiguration] = None,
                 factory_config: Optional[FactoryConfiguration] = None):
        super().__init__(config_provider, factory_config)
        self.path_config = path_config
        self._performance_config: Optional[PerformanceConfiguration] = None
    
    def validate_configuration(self) -> List[str]:
        """Validate file service configuration."""
        errors = []
        
        try:
            # Validate required paths
            cache_destination = self.config_provider.get_string("CACHE_DESTINATION")
            if not cache_destination:
                errors.append("CACHE_DESTINATION is required")
            elif self.path_config and not self.path_config.validate_path(
                cache_destination, must_exist=False, must_be_writable=True
            ):
                errors.append("CACHE_DESTINATION is not accessible or writable")
            
            plex_source = self.config_provider.get_string("PLEX_SOURCE")
            if not plex_source:
                errors.append("PLEX_SOURCE is required")
            elif self.path_config and not self.path_config.validate_path(
                plex_source, must_exist=True, must_be_readable=True
            ):
                errors.append("PLEX_SOURCE is not accessible or readable")
            
            # Validate performance settings
            max_concurrent_cache = self.config_provider.get_int("MAX_CONCURRENT_MOVES_CACHE", 5)
            max_concurrent_array = self.config_provider.get_int("MAX_CONCURRENT_MOVES_ARRAY", 2)
            
            if max_concurrent_cache <= 0 or max_concurrent_array <= 0:
                errors.append("Concurrent move limits must be positive")
            
            # Create performance configuration
            self._performance_config = PerformanceConfiguration(
                max_concurrent_moves_cache=max_concurrent_cache,
                max_concurrent_moves_array=max_concurrent_array,
                max_concurrent_local_transfers=self.config_provider.get_int(
                    "MAX_CONCURRENT_LOCAL_TRANSFERS", 5
                ),
                max_concurrent_network_transfers=self.config_provider.get_int(
                    "MAX_CONCURRENT_NETWORK_TRANSFERS", 2
                ),
                chunk_size_mb=self.config_provider.get_int("CHUNK_SIZE_MB", 64),
                timeout_seconds=self.config_provider.get_int("OPERATION_TIMEOUT", 300)
            )
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def _create_instance(self, provider: Optional[IServiceProvider] = None) -> FileService:
        """Create FileService implementation."""
        if not self._performance_config:
            validation_errors = self.validate_configuration()
            if validation_errors:
                raise ServiceCreationError(
                    FileService,
                    f"Invalid configuration: {', '.join(validation_errors)}"
                )
        
        try:
            from ..core.file_operations import FileOperations
            
            # Create FileOperations instance
            file_service = FileOperations()
            
            # Configure the service if it supports configuration
            if hasattr(file_service, 'configure'):
                file_service.configure(self._performance_config)
            
            return file_service
            
        except ImportError as e:
            raise ServiceCreationError(
                FileService,
                f"Failed to import FileOperations: {str(e)}",
                e
            )
        except Exception as e:
            raise ServiceCreationError(
                FileService,
                f"Failed to create FileOperations instance: {str(e)}",
                e
            )
    
    def get_service_type(self) -> Type[FileService]:
        return FileService
    
    @staticmethod
    def create_factory(config_provider: ConfigProvider, 
                      path_config: Optional[PathConfiguration] = None) -> Callable[[IServiceProvider], FileService]:
        """Create a factory function for DI container registration."""
        factory_instance = FileServiceFactory(config_provider, path_config)
        return lambda provider: factory_instance.create(provider)


class NotificationServiceFactory(BaseServiceFactory[NotificationService]):
    """
    Factory for creating NotificationService implementations.
    
    Creates notification service with webhook validation and configuration.
    """
    
    def __init__(self, config_provider: ConfigProvider, 
                 factory_config: Optional[FactoryConfiguration] = None):
        super().__init__(config_provider, factory_config)
        self._notification_config: Optional[NotificationConfiguration] = None
    
    def validate_configuration(self) -> List[str]:
        """Validate notification service configuration."""
        errors = []
        
        try:
            webhook_url = self.config_provider.get_string("WEBHOOK_URL")
            
            # Webhook is optional, but if provided, validate it
            if webhook_url and not webhook_url.startswith(('http://', 'https://')):
                errors.append("WEBHOOK_URL must be a valid URL if provided")
            
            # Validate notification settings
            rate_limit = self.config_provider.get_int("NOTIFICATION_RATE_LIMIT_MINUTES", 5)
            if rate_limit < 0:
                errors.append("NOTIFICATION_RATE_LIMIT_MINUTES must be non-negative")
            
            # Create notification configuration
            self._notification_config = NotificationConfiguration(
                webhook_url=webhook_url,
                enable_success_notifications=self.config_provider.get_bool(
                    "ENABLE_SUCCESS_NOTIFICATIONS", True
                ),
                enable_error_notifications=self.config_provider.get_bool(
                    "ENABLE_ERROR_NOTIFICATIONS", True
                ),
                enable_summary_notifications=self.config_provider.get_bool(
                    "ENABLE_SUMMARY_NOTIFICATIONS", True
                ),
                rate_limit_minutes=rate_limit
            )
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def _create_instance(self, provider: Optional[IServiceProvider] = None) -> NotificationService:
        """Create NotificationService implementation."""
        if not self._notification_config:
            validation_errors = self.validate_configuration()
            if validation_errors:
                raise ServiceCreationError(
                    NotificationService,
                    f"Invalid configuration: {', '.join(validation_errors)}"
                )
        
        try:
            from ..core.notifications import NotificationManager
            
            # Create NotificationManager instance
            notification_service = NotificationManager()
            
            # Configure the service
            if hasattr(notification_service, 'configure'):
                notification_service.configure(self._notification_config)
            
            return notification_service
            
        except ImportError as e:
            raise ServiceCreationError(
                NotificationService,
                f"Failed to import NotificationManager: {str(e)}",
                e
            )
        except Exception as e:
            raise ServiceCreationError(
                NotificationService,
                f"Failed to create NotificationManager instance: {str(e)}",
                e
            )
    
    def get_service_type(self) -> Type[NotificationService]:
        return NotificationService
    
    @staticmethod
    def create_factory(config_provider: ConfigProvider) -> Callable[[IServiceProvider], NotificationService]:
        """Create a factory function for DI container registration."""
        factory_instance = NotificationServiceFactory(config_provider)
        return lambda provider: factory_instance.create(provider)


class CacheServiceFactory(BaseServiceFactory[CacheService]):
    """
    Factory for creating CacheService implementations.
    
    Creates cache service with dependency resolution and configuration validation.
    """
    
    def __init__(self, config_provider: ConfigProvider, 
                 factory_config: Optional[FactoryConfiguration] = None):
        super().__init__(config_provider, factory_config)
        self._media_config: Optional[MediaConfiguration] = None
    
    def validate_configuration(self) -> List[str]:
        """Validate cache service configuration."""
        errors = []
        
        try:
            # Validate media configuration
            days_to_monitor = self.config_provider.get_int("DAYS_TO_MONITOR", 99)
            number_episodes = self.config_provider.get_int("NUMBER_EPISODES", 5)
            watchlist_episodes = self.config_provider.get_int("WATCHLIST_EPISODES", 1)
            
            if days_to_monitor <= 0:
                errors.append("DAYS_TO_MONITOR must be positive")
            if number_episodes <= 0:
                errors.append("NUMBER_EPISODES must be positive")
            if watchlist_episodes <= 0:
                errors.append("WATCHLIST_EPISODES must be positive")
            
            # Create media configuration
            self._media_config = MediaConfiguration(
                exit_if_active_session=self.config_provider.get_bool("EXIT_IF_ACTIVE_SESSION", False),
                watched_move=self.config_provider.get_bool("WATCHED_MOVE", True),
                users_toggle=self.config_provider.get_bool("USERS_TOGGLE", True),
                watchlist_toggle=self.config_provider.get_bool("WATCHLIST_TOGGLE", True),
                days_to_monitor=days_to_monitor,
                number_episodes=number_episodes,
                watchlist_episodes=watchlist_episodes,
                copy_to_cache=self.config_provider.get_bool("COPY_TO_CACHE", True),
                delete_from_cache_when_done=self.config_provider.get_bool(
                    "DELETE_FROM_CACHE_WHEN_DONE", True
                ),
                use_symlinks_for_cache=self.config_provider.get_bool("USE_SYMLINKS_FOR_CACHE", True),
                move_with_symlinks=self.config_provider.get_bool("MOVE_WITH_SYMLINKS", False)
            )
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def _create_instance(self, provider: Optional[IServiceProvider] = None) -> CacheService:
        """Create CacheService implementation."""
        if not self._media_config:
            validation_errors = self.validate_configuration()
            if validation_errors:
                raise ServiceCreationError(
                    CacheService,
                    f"Invalid configuration: {', '.join(validation_errors)}"
                )
        
        if not provider:
            raise ServiceCreationError(
                CacheService,
                "Service provider is required for CacheService creation"
            )
        
        try:
            # Resolve dependencies
            file_service = provider.resolve(FileService)
            notification_service = provider.resolve(NotificationService)
            
            # Import and create the cache service implementation
            from ..core.plex_cache_engine import CacherrEngine
            
            cache_service = CacherrEngine()
            
            # Configure dependencies if the service supports it
            if hasattr(cache_service, 'configure_dependencies'):
                cache_service.configure_dependencies(
                    file_service=file_service,
                    notification_service=notification_service,
                    media_config=self._media_config
                )
            
            return cache_service
            
        except Exception as e:
            raise ServiceCreationError(
                CacheService,
                f"Failed to create CacheService instance: {str(e)}",
                e
            )
    
    def get_service_type(self) -> Type[CacheService]:
        return CacheService
    
    @staticmethod
    def create_factory(config_provider: ConfigProvider) -> Callable[[IServiceProvider], CacheService]:
        """Create a factory function for DI container registration."""
        factory_instance = CacheServiceFactory(config_provider)
        return lambda provider: factory_instance.create(provider)


class ServiceFactoryRegistry:
    """
    Registry for managing service factories.
    
    Provides centralized registration and retrieval of service factories,
    enabling configuration-driven service creation and factory management.
    """
    
    def __init__(self):
        self._factories: Dict[Type, IServiceFactory] = {}
        self._factory_configs: Dict[Type, FactoryConfiguration] = {}
        
    def register_factory(self, service_type: Type[T], factory: IServiceFactory[T],
                        factory_config: Optional[FactoryConfiguration] = None) -> None:
        """
        Register a factory for a service type.
        
        Args:
            service_type: The service type the factory creates
            factory: The factory instance
            factory_config: Optional factory-specific configuration
        """
        self._factories[service_type] = factory
        if factory_config:
            self._factory_configs[service_type] = factory_config
        
        logger.info("Registered factory for service type: %s", service_type.__name__)
    
    def get_factory(self, service_type: Type[T]) -> Optional[IServiceFactory[T]]:
        """
        Get a factory for a service type.
        
        Args:
            service_type: The service type to get factory for
            
        Returns:
            Factory instance if registered, None otherwise
        """
        return self._factories.get(service_type)
    
    def has_factory(self, service_type: Type) -> bool:
        """Check if a factory is registered for a service type."""
        return service_type in self._factories
    
    def create_service(self, service_type: Type[T], 
                      provider: Optional[IServiceProvider] = None) -> T:
        """
        Create a service using its registered factory.
        
        Args:
            service_type: The service type to create
            provider: Optional service provider for dependency resolution
            
        Returns:
            Created service instance
            
        Raises:
            FactoryError: If no factory is registered or creation fails
        """
        factory = self.get_factory(service_type)
        if not factory:
            raise FactoryError(f"No factory registered for service type: {service_type.__name__}")
        
        return factory.create(provider)
    
    def get_registered_services(self) -> List[Type]:
        """Get list of service types with registered factories."""
        return list(self._factories.keys())
    
    def validate_all_configurations(self) -> Dict[Type, List[str]]:
        """
        Validate configurations for all registered factories.
        
        Returns:
            Dictionary mapping service types to their validation errors
        """
        validation_results = {}
        
        for service_type, factory in self._factories.items():
            try:
                errors = factory.validate_configuration()
                validation_results[service_type] = errors
            except Exception as e:
                validation_results[service_type] = [f"Validation failed: {str(e)}"]
        
        return validation_results
    
    def clear(self) -> None:
        """Clear all registered factories."""
        self._factories.clear()
        self._factory_configs.clear()


# Global factory registry instance
factory_registry = ServiceFactoryRegistry()


def register_default_factories(config_provider: ConfigProvider, 
                              path_config: Optional[PathConfiguration] = None) -> None:
    """
    Register default factories for core services.
    
    Args:
        config_provider: Configuration provider for service settings
        path_config: Optional path configuration for file service
    """
    factory_registry.register_factory(
        MediaService,
        MediaServiceFactory(config_provider)
    )
    
    factory_registry.register_factory(
        FileService,
        FileServiceFactory(config_provider, path_config)
    )
    
    factory_registry.register_factory(
        NotificationService,
        NotificationServiceFactory(config_provider)
    )
    
    factory_registry.register_factory(
        CacheService,
        CacheServiceFactory(config_provider)
    )
    
    logger.info("Registered default factories for core services")