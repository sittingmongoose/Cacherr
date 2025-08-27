"""
Dependency Injection Container for PlexCacheUltra.

This module provides a comprehensive IoC (Inversion of Control) container that manages
service registration, resolution, and lifecycle. It implements the dependency injection
pattern to decouple service creation from service usage, improving testability and
maintainability.

The container supports:
- Service registration by interface and implementation
- Singleton and transient service lifetimes
- Automatic dependency resolution
- Factory-based service creation
- Configuration-driven service registration
- Service location pattern
- Lifecycle management with proper cleanup

Example:
    Basic usage:
    
    ```python
    container = DIContainer()
    
    # Register services
    container.register_singleton(MediaService, PlexMediaService)
    container.register_transient(FileService, LocalFileService)
    
    # Resolve services
    media_service = container.resolve(MediaService)
    file_service = container.resolve(FileService)
    ```
    
    Factory-based registration:
    
    ```python
    container.register_factory(
        CacheService,
        lambda c: CacheServiceImpl(
            file_service=c.resolve(FileService),
            config=c.resolve(ConfigProvider)
        )
    )
    ```
"""

import threading
import weakref
from abc import ABC, abstractmethod
from typing import (
    Type, TypeVar, Generic, Dict, Any, Optional, Callable, List, 
    Union, Protocol, runtime_checkable, get_origin, get_args
)
from enum import Enum
from datetime import datetime
import logging
from functools import wraps

from pydantic import BaseModel, Field, field_validator

# Type definitions for better type safety
T = TypeVar('T')
ServiceType = TypeVar('ServiceType')
ImplementationType = TypeVar('ImplementationType')

logger = logging.getLogger(__name__)


class ServiceLifetime(Enum):
    """Defines the lifetime of services in the container."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceRegistration(BaseModel):
    """
    Represents a service registration in the DI container.
    
    Attributes:
        service_type: The interface or abstract class type
        implementation_type: The concrete implementation type (optional for factories)
        factory: Factory function for creating service instances (optional)
        lifetime: Service lifetime management strategy
        instance: Cached instance for singleton services (optional)
        dependencies: List of dependency types this service requires
        is_factory_registration: Whether this is a factory-based registration
        registration_time: When this service was registered
        resolve_count: Number of times this service has been resolved
    """
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    instance: Optional[Any] = None
    dependencies: List[Type] = Field(default_factory=list)
    is_factory_registration: bool = False
    registration_time: datetime = Field(default_factory=datetime.utcnow)
    resolve_count: int = 0
    
    class Config:
        arbitrary_types_allowed = True
        
    @field_validator('factory', 'implementation_type')
    @classmethod
    def validate_factory_or_implementation(cls, v, info):
        """Ensure either factory or implementation_type is provided."""
        values = info.data
        if 'factory' in values and values['factory'] is not None:
            return v
        if 'implementation_type' in values and values['implementation_type'] is not None:
            return v
        if v is None and ('factory' not in values or values['factory'] is None):
            raise ValueError("Either factory or implementation_type must be provided")
        return v


class ServiceResolutionContext(BaseModel):
    """
    Context information for service resolution operations.
    
    Tracks the resolution chain to detect circular dependencies and
    provide detailed error information.
    """
    requesting_service: Optional[Type] = None
    resolution_chain: List[Type] = Field(default_factory=list)
    resolution_depth: int = 0
    max_resolution_depth: int = 50
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_to_chain(self, service_type: Type) -> 'ServiceResolutionContext':
        """Add a service type to the resolution chain."""
        new_chain = self.resolution_chain.copy()
        new_chain.append(service_type)
        
        return ServiceResolutionContext(
            requesting_service=self.requesting_service,
            resolution_chain=new_chain,
            resolution_depth=self.resolution_depth + 1,
            max_resolution_depth=self.max_resolution_depth
        )
    
    def has_circular_dependency(self, service_type: Type) -> bool:
        """Check if adding this service type would create a circular dependency."""
        return service_type in self.resolution_chain
    
    def is_max_depth_exceeded(self) -> bool:
        """Check if maximum resolution depth has been exceeded."""
        return self.resolution_depth >= self.max_resolution_depth


@runtime_checkable
class IServiceProvider(Protocol):
    """Protocol for service providers that can resolve dependencies."""
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance of the specified type."""
        ...
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve a service, returning None if not registered."""
        ...


class ContainerError(Exception):
    """Base exception for container-related errors."""
    pass


class ServiceNotRegisteredException(ContainerError):
    """Raised when attempting to resolve an unregistered service."""
    
    def __init__(self, service_type: Type, available_services: List[str] = None):
        self.service_type = service_type
        self.available_services = available_services or []
        
        message = f"Service '{service_type.__name__}' is not registered in the container."
        if self.available_services:
            message += f" Available services: {', '.join(self.available_services)}"
        
        super().__init__(message)


class CircularDependencyException(ContainerError):
    """Raised when a circular dependency is detected during service resolution."""
    
    def __init__(self, resolution_chain: List[Type]):
        self.resolution_chain = resolution_chain
        chain_names = " -> ".join(service.__name__ for service in resolution_chain)
        message = f"Circular dependency detected: {chain_names}"
        super().__init__(message)


class ServiceCreationException(ContainerError):
    """Raised when service creation fails."""
    
    def __init__(self, service_type: Type, inner_exception: Exception):
        self.service_type = service_type
        self.inner_exception = inner_exception
        message = f"Failed to create service '{service_type.__name__}': {str(inner_exception)}"
        super().__init__(message)


class MaxResolutionDepthExceededException(ContainerError):
    """Raised when maximum resolution depth is exceeded."""
    
    def __init__(self, max_depth: int, resolution_chain: List[Type]):
        self.max_depth = max_depth
        self.resolution_chain = resolution_chain
        chain_names = " -> ".join(service.__name__ for service in resolution_chain)
        message = f"Maximum resolution depth ({max_depth}) exceeded. Chain: {chain_names}"
        super().__init__(message)


class DIContainer(IServiceProvider):
    """
    Dependency Injection Container for managing service registration and resolution.
    
    This container implements the IoC pattern with support for various service lifetimes,
    automatic dependency injection, factory-based service creation, and lifecycle management.
    
    Features:
    - Thread-safe service registration and resolution
    - Singleton, transient, and scoped service lifetimes
    - Automatic constructor injection
    - Factory-based service creation
    - Circular dependency detection
    - Service locator pattern support
    - Comprehensive error handling and diagnostics
    - Configuration-driven service registration
    
    Thread Safety:
        This container is thread-safe for both registration and resolution operations.
        Singleton instances are created with double-checked locking to ensure thread safety.
    """
    
    def __init__(self, max_resolution_depth: int = 50):
        """
        Initialize the DI container.
        
        Args:
            max_resolution_depth: Maximum depth for dependency resolution chains
        """
        self._services: Dict[Type, ServiceRegistration] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._max_resolution_depth = max_resolution_depth
        self._disposed = False
        self._creation_callbacks: Dict[Type, List[Callable[[Any], None]]] = {}
        self._disposal_callbacks: Dict[Type, List[Callable[[Any], None]]] = {}
        
        # Keep weak references to created instances for cleanup
        self._created_instances: weakref.WeakSet = weakref.WeakSet()
        
        logger.info("DIContainer initialized with max resolution depth: %d", max_resolution_depth)
    
    def register_singleton(self, service_type: Type[ServiceType], 
                          implementation_type: Type[ImplementationType]) -> 'DIContainer':
        """
        Register a service with singleton lifetime.
        
        Singleton services are created once and reused for all subsequent requests.
        
        Args:
            service_type: The interface or abstract class type
            implementation_type: The concrete implementation type
            
        Returns:
            Self for method chaining
            
        Raises:
            ContainerError: If registration fails
            ValueError: If types are invalid
            
        Example:
            ```python
            container.register_singleton(MediaService, PlexMediaService)
            ```
        """
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    def register_transient(self, service_type: Type[ServiceType], 
                          implementation_type: Type[ImplementationType]) -> 'DIContainer':
        """
        Register a service with transient lifetime.
        
        Transient services are created fresh for each request.
        
        Args:
            service_type: The interface or abstract class type
            implementation_type: The concrete implementation type
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            container.register_transient(FileService, LocalFileService)
            ```
        """
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=ServiceLifetime.TRANSIENT
        )
    
    def register_scoped(self, service_type: Type[ServiceType], 
                       implementation_type: Type[ImplementationType]) -> 'DIContainer':
        """
        Register a service with scoped lifetime.
        
        Scoped services are created once per scope. In this implementation,
        scope is typically per operation or request.
        
        Args:
            service_type: The interface or abstract class type
            implementation_type: The concrete implementation type
            
        Returns:
            Self for method chaining
        """
        return self._register_service(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=ServiceLifetime.SCOPED
        )
    
    def register_factory(self, service_type: Type[ServiceType], 
                        factory: Callable[[IServiceProvider], ServiceType],
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DIContainer':
        """
        Register a service using a factory function.
        
        Factory registration allows for complex service creation logic
        and provides access to the service provider for dependency resolution.
        
        Args:
            service_type: The interface or abstract class type
            factory: Factory function that creates the service instance
            lifetime: Service lifetime (default: transient)
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            container.register_factory(
                CacheService,
                lambda provider: CacheServiceImpl(
                    file_service=provider.resolve(FileService),
                    config=provider.resolve(ConfigProvider)
                ),
                ServiceLifetime.SINGLETON
            )
            ```
        """
        return self._register_service(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime
        )
    
    def register_instance(self, service_type: Type[ServiceType], 
                         instance: ServiceType) -> 'DIContainer':
        """
        Register a pre-created instance as a singleton service.
        
        Args:
            service_type: The interface or abstract class type
            instance: The pre-created instance
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            config = MyConfig()
            container.register_instance(ConfigProvider, config)
            ```
        """
        if not isinstance(instance, service_type):
            raise ValueError(f"Instance is not of type {service_type.__name__}")
        
        registration = ServiceRegistration(
            service_type=service_type,
            implementation_type=type(instance),
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance,
            is_factory_registration=False
        )
        
        with self._lock:
            self._ensure_not_disposed()
            self._services[service_type] = registration
            self._created_instances.add(instance)
        
        logger.info("Registered pre-created instance for service: %s", service_type.__name__)
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance of the specified type.
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            Service instance of the specified type
            
        Raises:
            ServiceNotRegisteredException: If service is not registered
            CircularDependencyException: If circular dependency detected
            ServiceCreationException: If service creation fails
            MaxResolutionDepthExceededException: If resolution depth exceeded
            
        Example:
            ```python
            media_service = container.resolve(MediaService)
            ```
        """
        context = ServiceResolutionContext(max_resolution_depth=self._max_resolution_depth)
        return self._resolve_with_context(service_type, context)
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """
        Try to resolve a service, returning None if not registered.
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            Service instance if registered, None otherwise
        """
        try:
            return self.resolve(service_type)
        except ServiceNotRegisteredException:
            return None
        except Exception as e:
            logger.warning("Failed to resolve service %s: %s", service_type.__name__, str(e))
            return None
    
    def is_registered(self, service_type: Type) -> bool:
        """
        Check if a service type is registered in the container.
        
        Args:
            service_type: The service type to check
            
        Returns:
            True if service is registered, False otherwise
        """
        with self._lock:
            return service_type in self._services
    
    def get_registered_services(self) -> List[Type]:
        """
        Get a list of all registered service types.
        
        Returns:
            List of registered service types
        """
        with self._lock:
            return list(self._services.keys())
    
    def get_service_info(self, service_type: Type) -> Optional[ServiceRegistration]:
        """
        Get detailed information about a registered service.
        
        Args:
            service_type: The service type to get info for
            
        Returns:
            ServiceRegistration if service is registered, None otherwise
        """
        with self._lock:
            return self._services.get(service_type)
    
    def add_creation_callback(self, service_type: Type, 
                             callback: Callable[[Any], None]) -> 'DIContainer':
        """
        Add a callback to be executed after service creation.
        
        Args:
            service_type: The service type to add callback for
            callback: Callback function that receives the created instance
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            if service_type not in self._creation_callbacks:
                self._creation_callbacks[service_type] = []
            self._creation_callbacks[service_type].append(callback)
        
        return self
    
    def add_disposal_callback(self, service_type: Type, 
                             callback: Callable[[Any], None]) -> 'DIContainer':
        """
        Add a callback to be executed before service disposal.
        
        Args:
            service_type: The service type to add callback for
            callback: Callback function that receives the instance to dispose
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            if service_type not in self._disposal_callbacks:
                self._disposal_callbacks[service_type] = []
            self._disposal_callbacks[service_type].append(callback)
        
        return self
    
    def create_scope(self) -> 'ScopedServiceProvider':
        """
        Create a new service scope for scoped services.
        
        Returns:
            ScopedServiceProvider that manages scoped service instances
        """
        return ScopedServiceProvider(self)
    
    def dispose(self) -> None:
        """
        Dispose the container and all its managed instances.
        
        This method should be called when the application shuts down
        to ensure proper cleanup of resources.
        """
        with self._lock:
            if self._disposed:
                return
            
            logger.info("Disposing DIContainer...")
            
            # Dispose all singleton instances
            for registration in self._services.values():
                if registration.instance and registration.lifetime == ServiceLifetime.SINGLETON:
                    self._dispose_instance(registration.service_type, registration.instance)
            
            # Clear all registrations and instances
            self._services.clear()
            self._scoped_instances.clear()
            self._creation_callbacks.clear()
            self._disposal_callbacks.clear()
            
            self._disposed = True
            logger.info("DIContainer disposed successfully")
    
    def _register_service(self, service_type: Type, implementation_type: Type = None,
                         factory: Callable = None, lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'DIContainer':
        """Internal method for service registration."""
        self._ensure_not_disposed()
        
        if not service_type:
            raise ValueError("service_type cannot be None")
        
        if implementation_type is None and factory is None:
            raise ValueError("Either implementation_type or factory must be provided")
        
        if implementation_type and factory:
            raise ValueError("Cannot specify both implementation_type and factory")
        
        # Validate implementation type inheritance
        if implementation_type and not issubclass(implementation_type, service_type):
            # Allow duck typing for protocols and abstract classes
            if not (hasattr(service_type, '__abstractmethods__') or hasattr(service_type, '_is_protocol')):
                logger.warning(
                    "Implementation type %s does not inherit from service type %s. "
                    "This may cause runtime errors.",
                    implementation_type.__name__, service_type.__name__
                )
        
        registration = ServiceRegistration(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=lifetime,
            is_factory_registration=factory is not None
        )
        
        with self._lock:
            self._services[service_type] = registration
        
        logger.info(
            "Registered service: %s -> %s (%s, %s)",
            service_type.__name__,
            implementation_type.__name__ if implementation_type else "factory",
            lifetime.value,
            "factory" if factory else "type"
        )
        
        return self
    
    def _resolve_with_context(self, service_type: Type[T], context: ServiceResolutionContext) -> T:
        """Internal method for service resolution with context tracking."""
        self._ensure_not_disposed()
        
        # Check for circular dependencies
        if context.has_circular_dependency(service_type):
            raise CircularDependencyException(context.resolution_chain + [service_type])
        
        # Check for maximum resolution depth
        if context.is_max_depth_exceeded():
            raise MaxResolutionDepthExceededException(
                context.max_resolution_depth, 
                context.resolution_chain
            )
        
        # Get service registration
        with self._lock:
            if service_type not in self._services:
                available_services = [s.__name__ for s in self._services.keys()]
                raise ServiceNotRegisteredException(service_type, available_services)
            
            registration = self._services[service_type]
            registration.resolve_count += 1
        
        # Update context for this resolution
        new_context = context.add_to_chain(service_type)
        
        try:
            # Handle different lifetimes
            if registration.lifetime == ServiceLifetime.SINGLETON:
                return self._resolve_singleton(registration, new_context)
            elif registration.lifetime == ServiceLifetime.SCOPED:
                return self._resolve_scoped(registration, new_context)
            else:  # TRANSIENT
                return self._create_instance(registration, new_context)
                
        except Exception as e:
            if isinstance(e, ContainerError):
                raise
            raise ServiceCreationException(service_type, e)
    
    def _resolve_singleton(self, registration: ServiceRegistration, 
                          context: ServiceResolutionContext) -> Any:
        """Resolve a singleton service with double-checked locking."""
        if registration.instance is not None:
            return registration.instance
        
        with self._lock:
            # Double-checked locking
            if registration.instance is not None:
                return registration.instance
            
            instance = self._create_instance(registration, context)
            registration.instance = instance
            self._created_instances.add(instance)
            
            return instance
    
    def _resolve_scoped(self, registration: ServiceRegistration, 
                       context: ServiceResolutionContext) -> Any:
        """Resolve a scoped service."""
        service_type = registration.service_type
        
        with self._lock:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]
            
            instance = self._create_instance(registration, context)
            self._scoped_instances[service_type] = instance
            self._created_instances.add(instance)
            
            return instance
    
    def _create_instance(self, registration: ServiceRegistration, 
                        context: ServiceResolutionContext) -> Any:
        """Create a new service instance."""
        try:
            if registration.factory:
                # Use factory function
                instance = registration.factory(self)
            else:
                # Use constructor injection
                instance = self._create_with_constructor_injection(
                    registration.implementation_type, context
                )
            
            # Execute creation callbacks
            self._execute_creation_callbacks(registration.service_type, instance)
            
            # Track instance for cleanup if not singleton (handled separately)
            if registration.lifetime != ServiceLifetime.SINGLETON:
                self._created_instances.add(instance)
            
            logger.debug("Created instance of %s", registration.service_type.__name__)
            return instance
            
        except Exception as e:
            logger.error(
                "Failed to create instance of %s: %s", 
                registration.service_type.__name__, str(e)
            )
            raise
    
    def _create_with_constructor_injection(self, implementation_type: Type, 
                                         context: ServiceResolutionContext) -> Any:
        """Create instance using constructor injection."""
        import inspect
        
        # Get constructor signature
        try:
            constructor = implementation_type.__init__
            sig = inspect.signature(constructor)
        except (AttributeError, ValueError) as e:
            logger.warning(
                "Cannot inspect constructor for %s: %s. Creating with no arguments.",
                implementation_type.__name__, str(e)
            )
            return implementation_type()
        
        # Resolve constructor parameters
        args = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # Skip parameters with default values if not registered
            if param.annotation == inspect.Parameter.empty:
                if param.default != inspect.Parameter.empty:
                    continue
                else:
                    logger.warning(
                        "Parameter '%s' in %s has no type annotation and no default value. Skipping.",
                        param_name, implementation_type.__name__
                    )
                    continue
            
            param_type = param.annotation
            
            # Try to resolve dependency
            try:
                dependency = self._resolve_with_context(param_type, context)
                args[param_name] = dependency
            except ServiceNotRegisteredException:
                if param.default != inspect.Parameter.empty:
                    # Use default value if dependency not registered
                    continue
                else:
                    logger.warning(
                        "Cannot resolve dependency '%s' (%s) for %s and no default value provided",
                        param_name, param_type.__name__, implementation_type.__name__
                    )
                    raise
        
        return implementation_type(**args)
    
    def _execute_creation_callbacks(self, service_type: Type, instance: Any) -> None:
        """Execute creation callbacks for a service instance."""
        callbacks = self._creation_callbacks.get(service_type, [])
        for callback in callbacks:
            try:
                callback(instance)
            except Exception as e:
                logger.error(
                    "Creation callback failed for %s: %s", 
                    service_type.__name__, str(e)
                )
    
    def _dispose_instance(self, service_type: Type, instance: Any) -> None:
        """Dispose a service instance with callbacks."""
        # Execute disposal callbacks
        callbacks = self._disposal_callbacks.get(service_type, [])
        for callback in callbacks:
            try:
                callback(instance)
            except Exception as e:
                logger.error(
                    "Disposal callback failed for %s: %s", 
                    service_type.__name__, str(e)
                )
        
        # Call dispose method if available
        if hasattr(instance, 'dispose'):
            try:
                instance.dispose()
            except Exception as e:
                logger.error(
                    "Failed to dispose instance of %s: %s", 
                    service_type.__name__, str(e)
                )
    
    def _ensure_not_disposed(self) -> None:
        """Ensure the container has not been disposed."""
        if self._disposed:
            raise ContainerError("Container has been disposed")
    
    def __enter__(self) -> 'DIContainer':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with automatic disposal."""
        self.dispose()


class ScopedServiceProvider(IServiceProvider):
    """
    Service provider for managing scoped service instances.
    
    This provider maintains its own scope for scoped services while
    delegating singleton and transient resolutions to the parent container.
    """
    
    def __init__(self, parent_container: DIContainer):
        """
        Initialize the scoped service provider.
        
        Args:
            parent_container: Parent DI container
        """
        self._parent_container = parent_container
        self._scoped_instances: Dict[Type, Any] = {}
        self._disposed = False
        
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service within this scope."""
        if self._disposed:
            raise ContainerError("Scoped provider has been disposed")
        
        # Check if we have a scoped instance
        if service_type in self._scoped_instances:
            return self._scoped_instances[service_type]
        
        # Get registration from parent
        registration = self._parent_container.get_service_info(service_type)
        if not registration:
            return self._parent_container.resolve(service_type)
        
        if registration.lifetime == ServiceLifetime.SCOPED:
            # Create scoped instance
            context = ServiceResolutionContext(
                max_resolution_depth=self._parent_container._max_resolution_depth
            )
            instance = self._parent_container._create_instance(registration, context)
            self._scoped_instances[service_type] = instance
            return instance
        else:
            # Delegate to parent for singleton/transient
            return self._parent_container.resolve(service_type)
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve a service within this scope."""
        try:
            return self.resolve(service_type)
        except Exception:
            return None
    
    def dispose(self) -> None:
        """Dispose all scoped instances."""
        if self._disposed:
            return
        
        for service_type, instance in self._scoped_instances.items():
            self._parent_container._dispose_instance(service_type, instance)
        
        self._scoped_instances.clear()
        self._disposed = True
    
    def __enter__(self) -> 'ScopedServiceProvider':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with automatic disposal."""
        self.dispose()


def inject(service_type: Type[T]) -> Callable[[Callable], Callable]:
    """
    Decorator for injecting dependencies into functions or methods.
    
    Args:
        service_type: The service type to inject
        
    Returns:
        Decorator function
        
    Example:
        ```python
        @inject(MediaService)
        def process_media(media_service: MediaService):
            # media_service will be automatically injected
            pass
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This requires a global container reference or service locator
            # Implementation would depend on how the global container is managed
            raise NotImplementedError(
                "Injection decorator requires global container configuration"
            )
        return wrapper
    return decorator