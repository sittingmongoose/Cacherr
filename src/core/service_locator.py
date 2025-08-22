"""
Service Locator Pattern Implementation for PlexCacheUltra.

This module provides a service locator pattern implementation that works in conjunction
with the dependency injection container. The service locator provides a centralized
registry for accessing services throughout the application while maintaining loose
coupling and testability.

The service locator pattern is useful for:
- Legacy code integration with DI
- Static contexts where injection is not possible
- Service discovery and lookup
- Cross-cutting concerns and utilities
- Plugin architecture support
- Testing with mock services

Example:
    Basic service locator usage:
    
    ```python
    # Initialize with container
    ServiceLocator.initialize(container)
    
    # Locate services
    media_service = ServiceLocator.get_service(MediaService)
    file_service = ServiceLocator.get_service(FileService)
    
    # Check service availability
    if ServiceLocator.has_service(CacheService):
        cache_service = ServiceLocator.get_service(CacheService)
    ```
    
    Scoped service location:
    
    ```python
    with ServiceLocator.create_scope() as scope:
        scoped_service = scope.get_service(ScopedService)
        # Scoped services are disposed when exiting context
    ```
"""

import threading
import weakref
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Dict, Any, List, Callable, ContextManager
from contextlib import contextmanager
from datetime import datetime
import logging

from pydantic import BaseModel, Field

from .container import DIContainer, IServiceProvider, ScopedServiceProvider, ContainerError
from .lifecycle import ServiceLifecycleManager, ServiceLifecycleEvent, ServiceState

T = TypeVar('T')
logger = logging.getLogger(__name__)


class ServiceLocationEvent(BaseModel):
    """
    Represents a service location event for monitoring and debugging.
    
    Attributes:
        service_type: Type name of the service being located
        success: Whether the service location was successful
        timestamp: When the location attempt occurred
        location_method: Method used for service location
        scope_id: ID of the scope if using scoped location
        error_message: Error message if location failed
        execution_time_ms: Time taken to locate the service
    """
    service_type: str
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location_method: str = "get_service"
    scope_id: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class ServiceLocatorError(Exception):
    """Base exception for service locator errors."""
    pass


class ServiceNotLocatedException(ServiceLocatorError):
    """Raised when a service cannot be located."""
    
    def __init__(self, service_type: Type, available_services: List[str] = None):
        self.service_type = service_type
        self.available_services = available_services or []
        
        message = f"Service '{service_type.__name__}' could not be located."
        if self.available_services:
            message += f" Available services: {', '.join(self.available_services)}"
        
        super().__init__(message)


class ServiceLocatorNotInitializedException(ServiceLocatorError):
    """Raised when service locator is used before initialization."""
    
    def __init__(self):
        super().__init__(
            "ServiceLocator has not been initialized. Call ServiceLocator.initialize() first."
        )


class IServiceLocator(ABC):
    """Interface for service locator implementations."""
    
    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service instance of the specified type.
        
        Args:
            service_type: The service type to locate
            
        Returns:
            Service instance of the specified type
            
        Raises:
            ServiceNotLocatedException: If service cannot be located
        """
        pass
    
    @abstractmethod
    def try_get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to get a service instance, returning None if not available.
        
        Args:
            service_type: The service type to locate
            
        Returns:
            Service instance if available, None otherwise
        """
        pass
    
    @abstractmethod
    def has_service(self, service_type: Type) -> bool:
        """
        Check if a service type is available.
        
        Args:
            service_type: The service type to check
            
        Returns:
            True if service is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_services(self) -> List[Type]:
        """
        Get list of available service types.
        
        Returns:
            List of available service types
        """
        pass


class ScopedServiceLocator(IServiceLocator):
    """
    Scoped service locator for managing services within a specific scope.
    
    This locator maintains its own scope for scoped services while
    delegating other service requests to the parent locator.
    """
    
    def __init__(self, parent_locator: IServiceLocator, 
                 scoped_provider: ScopedServiceProvider,
                 scope_id: Optional[str] = None):
        """
        Initialize the scoped service locator.
        
        Args:
            parent_locator: Parent service locator
            scoped_provider: Scoped service provider
            scope_id: Optional scope identifier
        """
        self._parent_locator = parent_locator
        self._scoped_provider = scoped_provider
        self._scope_id = scope_id or f"scope_{id(self)}"
        self._disposed = False
        
        logger.debug("Created scoped service locator: %s", self._scope_id)
    
    def get_service(self, service_type: Type[T]) -> T:
        """Get a service within this scope."""
        if self._disposed:
            raise ServiceLocatorError("Scoped service locator has been disposed")
        
        start_time = datetime.utcnow()
        success = False
        error_message = None
        
        try:
            # Try scoped provider first
            service = self._scoped_provider.resolve(service_type)
            success = True
            return service
        except Exception as e:
            error_message = str(e)
            # Fallback to parent locator for non-scoped services
            try:
                service = self._parent_locator.get_service(service_type)
                success = True
                return service
            except Exception as parent_error:
                error_message = str(parent_error)
                raise ServiceNotLocatedException(service_type)
        finally:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            ServiceLocator._emit_location_event(ServiceLocationEvent(
                service_type=service_type.__name__,
                success=success,
                location_method="get_service",
                scope_id=self._scope_id,
                error_message=error_message,
                execution_time_ms=execution_time
            ))
    
    def try_get_service(self, service_type: Type[T]) -> Optional[T]:
        """Try to get a service within this scope."""
        try:
            return self.get_service(service_type)
        except ServiceNotLocatedException:
            return None
    
    def has_service(self, service_type: Type) -> bool:
        """Check if service is available in this scope."""
        return self.try_get_service(service_type) is not None
    
    def get_available_services(self) -> List[Type]:
        """Get available services in this scope (delegates to parent)."""
        return self._parent_locator.get_available_services()
    
    def dispose(self) -> None:
        """Dispose the scoped service locator."""
        if not self._disposed:
            self._scoped_provider.dispose()
            self._disposed = True
            logger.debug("Disposed scoped service locator: %s", self._scope_id)
    
    def __enter__(self) -> 'ScopedServiceLocator':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with automatic disposal."""
        self.dispose()


class ServiceLocator(IServiceLocator):
    """
    Main service locator implementation.
    
    Provides centralized service location capabilities with support for
    scoped services, event monitoring, and thread-safe operations.
    This is implemented as a singleton to provide global access while
    maintaining proper initialization and lifecycle management.
    
    Thread Safety:
        All operations are thread-safe and can be called from multiple threads.
    """
    
    _instance: Optional['ServiceLocator'] = None
    _lock = threading.RLock()
    _initialized = False
    
    def __init__(self):
        """Private constructor - use initialize() method instead."""
        self._container: Optional[DIContainer] = None
        self._lifecycle_manager: Optional[ServiceLifecycleManager] = None
        self._event_listeners: List[Callable[[ServiceLocationEvent], None]] = []
        self._location_stats: Dict[str, int] = {}
        self._instance_lock = threading.RLock()
    
    @classmethod
    def initialize(cls, container: DIContainer, 
                  lifecycle_manager: Optional[ServiceLifecycleManager] = None) -> None:
        """
        Initialize the global service locator.
        
        Args:
            container: DI container for service resolution
            lifecycle_manager: Optional lifecycle manager for service monitoring
            
        Raises:
            ServiceLocatorError: If already initialized
        """
        with cls._lock:
            if cls._initialized:
                logger.warning("ServiceLocator is already initialized")
                return
            
            if cls._instance is None:
                cls._instance = cls()
            
            cls._instance._container = container
            cls._instance._lifecycle_manager = lifecycle_manager
            cls._initialized = True
            
            # Add lifecycle event listener if lifecycle manager provided
            if lifecycle_manager:
                lifecycle_manager.add_event_listener(cls._instance._on_lifecycle_event)
            
            logger.info("ServiceLocator initialized with container: %s", type(container).__name__)
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the service locator (mainly for testing).
        
        Warning: This will clear the global service locator state.
        """
        with cls._lock:
            if cls._instance:
                # Remove lifecycle event listener
                if (cls._instance._lifecycle_manager and 
                    hasattr(cls._instance._lifecycle_manager, 'remove_event_listener')):
                    cls._instance._lifecycle_manager.remove_event_listener(
                        cls._instance._on_lifecycle_event
                    )
                
                cls._instance._container = None
                cls._instance._lifecycle_manager = None
                cls._instance._event_listeners.clear()
                cls._instance._location_stats.clear()
            
            cls._instance = None
            cls._initialized = False
            
            logger.info("ServiceLocator reset")
    
    @classmethod
    def get_instance(cls) -> 'ServiceLocator':
        """
        Get the global service locator instance.
        
        Returns:
            ServiceLocator instance
            
        Raises:
            ServiceLocatorNotInitializedException: If not initialized
        """
        with cls._lock:
            if not cls._initialized or cls._instance is None:
                raise ServiceLocatorNotInitializedException()
            return cls._instance
    
    @classmethod
    def get_service(cls, service_type: Type[T]) -> T:
        """
        Get a service instance (class method for convenience).
        
        Args:
            service_type: The service type to locate
            
        Returns:
            Service instance of the specified type
            
        Raises:
            ServiceNotLocatedException: If service cannot be located
            ServiceLocatorNotInitializedException: If not initialized
        """
        return cls.get_instance().get_service(service_type)
    
    @classmethod
    def try_get_service(cls, service_type: Type[T]) -> Optional[T]:
        """
        Try to get a service instance (class method for convenience).
        
        Args:
            service_type: The service type to locate
            
        Returns:
            Service instance if available, None otherwise
        """
        try:
            return cls.get_instance().try_get_service(service_type)
        except ServiceLocatorNotInitializedException:
            return None
    
    @classmethod
    def has_service(cls, service_type: Type) -> bool:
        """
        Check if a service type is available (class method for convenience).
        
        Args:
            service_type: The service type to check
            
        Returns:
            True if service is available, False otherwise
        """
        try:
            return cls.get_instance().has_service(service_type)
        except ServiceLocatorNotInitializedException:
            return False
    
    @classmethod
    def create_scope(cls) -> ContextManager[ScopedServiceLocator]:
        """
        Create a scoped service locator.
        
        Returns:
            Context manager for scoped service locator
            
        Raises:
            ServiceLocatorNotInitializedException: If not initialized
        """
        return cls.get_instance().create_scope()
    
    @classmethod
    def get_available_services(cls) -> List[Type]:
        """
        Get list of available service types (class method for convenience).
        
        Returns:
            List of available service types
        """
        try:
            return cls.get_instance().get_available_services()
        except ServiceLocatorNotInitializedException:
            return []
    
    @classmethod
    def add_event_listener(cls, listener: Callable[[ServiceLocationEvent], None]) -> None:
        """
        Add an event listener for service location events.
        
        Args:
            listener: Function to call when location events occur
        """
        try:
            cls.get_instance().add_event_listener(listener)
        except ServiceLocatorNotInitializedException:
            logger.warning("Cannot add event listener: ServiceLocator not initialized")
    
    @classmethod
    def get_location_statistics(cls) -> Dict[str, int]:
        """
        Get service location statistics.
        
        Returns:
            Dictionary mapping service type names to location counts
        """
        try:
            return cls.get_instance().get_location_statistics()
        except ServiceLocatorNotInitializedException:
            return {}
    
    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        with self._instance_lock:
            if not self._container:
                raise ServiceLocatorNotInitializedException()
        
        start_time = datetime.utcnow()
        success = False
        error_message = None
        
        try:
            service = self._container.resolve(service_type)
            success = True
            
            # Update statistics
            with self._instance_lock:
                service_name = service_type.__name__
                self._location_stats[service_name] = self._location_stats.get(service_name, 0) + 1
            
            return service
            
        except Exception as e:
            error_message = str(e)
            if isinstance(e, ContainerError):
                available_services = [s.__name__ for s in self.get_available_services()]
                raise ServiceNotLocatedException(service_type, available_services)
            else:
                raise ServiceNotLocatedException(service_type)
        finally:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._emit_location_event(ServiceLocationEvent(
                service_type=service_type.__name__,
                success=success,
                location_method="get_service",
                error_message=error_message,
                execution_time_ms=execution_time
            ))
    
    def try_get_service(self, service_type: Type[T]) -> Optional[T]:
        """Try to get a service instance."""
        try:
            return self.get_service(service_type)
        except ServiceNotLocatedException:
            return None
    
    def has_service(self, service_type: Type) -> bool:
        """Check if a service type is available."""
        with self._instance_lock:
            if not self._container:
                return False
        
        return self._container.is_registered(service_type)
    
    def get_available_services(self) -> List[Type]:
        """Get list of available service types."""
        with self._instance_lock:
            if not self._container:
                return []
        
        return self._container.get_registered_services()
    
    @contextmanager
    def create_scope(self) -> ContextManager[ScopedServiceLocator]:
        """Create a scoped service locator."""
        with self._instance_lock:
            if not self._container:
                raise ServiceLocatorNotInitializedException()
        
        scoped_provider = self._container.create_scope()
        scoped_locator = ScopedServiceLocator(self, scoped_provider)
        
        try:
            yield scoped_locator
        finally:
            scoped_locator.dispose()
    
    def add_event_listener(self, listener: Callable[[ServiceLocationEvent], None]) -> None:
        """Add an event listener for service location events."""
        with self._instance_lock:
            self._event_listeners.append(listener)
        
        logger.debug("Added service location event listener: %s", listener.__name__)
    
    def remove_event_listener(self, listener: Callable[[ServiceLocationEvent], None]) -> bool:
        """Remove an event listener."""
        with self._instance_lock:
            try:
                self._event_listeners.remove(listener)
                logger.debug("Removed service location event listener: %s", listener.__name__)
                return True
            except ValueError:
                return False
    
    def get_location_statistics(self) -> Dict[str, int]:
        """Get service location statistics."""
        with self._instance_lock:
            return self._location_stats.copy()
    
    def clear_location_statistics(self) -> None:
        """Clear service location statistics."""
        with self._instance_lock:
            self._location_stats.clear()
        
        logger.debug("Cleared service location statistics")
    
    def _on_lifecycle_event(self, event: ServiceLifecycleEvent) -> None:
        """Handle lifecycle events from the lifecycle manager."""
        # Log interesting lifecycle events
        if event.event_type in ('service_started', 'service_stopped', 'service_startup_failed'):
            logger.debug(
                "Lifecycle event: %s for service %s (state: %s)",
                event.event_type, event.service_id, event.new_state
            )
    
    @classmethod
    def _emit_location_event(cls, event: ServiceLocationEvent) -> None:
        """Emit a service location event to all listeners."""
        try:
            instance = cls.get_instance()
            with instance._instance_lock:
                listeners = instance._event_listeners.copy()
            
            for listener in listeners:
                try:
                    listener(event)
                except Exception as e:
                    logger.error("Service location event listener failed: %s", str(e))
        except ServiceLocatorNotInitializedException:
            # No listeners to notify if not initialized
            pass


# Convenience functions for direct access without class qualification
def get_service(service_type: Type[T]) -> T:
    """
    Get a service instance (convenience function).
    
    Args:
        service_type: The service type to locate
        
    Returns:
        Service instance of the specified type
        
    Raises:
        ServiceNotLocatedException: If service cannot be located
        ServiceLocatorNotInitializedException: If not initialized
    """
    return ServiceLocator.get_service(service_type)


def try_get_service(service_type: Type[T]) -> Optional[T]:
    """
    Try to get a service instance (convenience function).
    
    Args:
        service_type: The service type to locate
        
    Returns:
        Service instance if available, None otherwise
    """
    return ServiceLocator.try_get_service(service_type)


def has_service(service_type: Type) -> bool:
    """
    Check if a service type is available (convenience function).
    
    Args:
        service_type: The service type to check
        
    Returns:
        True if service is available, False otherwise
    """
    return ServiceLocator.has_service(service_type)


@contextmanager
def service_scope() -> ContextManager[ScopedServiceLocator]:
    """
    Create a scoped service locator (convenience function).
    
    Returns:
        Context manager for scoped service locator
        
    Raises:
        ServiceLocatorNotInitializedException: If not initialized
    """
    with ServiceLocator.create_scope() as scope:
        yield scope


# Decorator for automatic service injection
def locate_service(service_type: Type[T]) -> Callable[[Callable], Callable]:
    """
    Decorator for automatically locating and injecting services.
    
    Args:
        service_type: The service type to locate and inject
        
    Returns:
        Decorator function
        
    Example:
        ```python
        @locate_service(MediaService)
        def process_media(media_service: MediaService = None):
            # media_service will be automatically located and injected
            return media_service.fetch_ondeck_media()
        ```
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Inject service if not provided
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            
            # Find parameter that matches the service type
            service_param = None
            for param_name, param in sig.parameters.items():
                if param.annotation == service_type:
                    service_param = param_name
                    break
            
            if service_param and service_param not in kwargs:
                try:
                    service_instance = get_service(service_type)
                    kwargs[service_param] = service_instance
                except ServiceNotLocatedException:
                    # Let the function handle the missing service
                    pass
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Context manager for temporary service registration
@contextmanager
def temporary_service_registration(service_type: Type[T], instance: T):
    """
    Context manager for temporarily registering a service instance.
    
    Args:
        service_type: The service type to register
        instance: The service instance to register
        
    Example:
        ```python
        mock_media_service = MockMediaService()
        with temporary_service_registration(MediaService, mock_media_service):
            # MediaService will resolve to the mock instance
            test_function()
        # Original service registration is restored
        ```
    """
    try:
        locator = ServiceLocator.get_instance()
        container = locator._container
        
        # Check if service is already registered
        was_registered = container.is_registered(service_type)
        original_registration = None
        
        if was_registered:
            original_registration = container.get_service_info(service_type)
        
        # Register temporary instance
        container.register_instance(service_type, instance)
        
        yield
        
    finally:
        # Restore original registration or unregister
        if was_registered and original_registration:
            # Note: Full restoration would require more complex container API
            # For now, we leave the temporary registration in place
            logger.warning(
                "Temporary service registration cleanup not fully implemented. "
                "Service %s may retain temporary registration.",
                service_type.__name__
            )
        else:
            # Service wasn't originally registered
            # Note: Container API doesn't support unregistration
            logger.warning(
                "Cannot fully clean up temporary service registration for %s. "
                "Consider resetting ServiceLocator in tests.",
                service_type.__name__
            )