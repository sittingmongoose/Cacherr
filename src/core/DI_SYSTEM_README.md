# PlexCacheUltra Dependency Injection System

## Overview

Phase 2 of the architectural refactoring has implemented a comprehensive Dependency Injection (DI) system for PlexCacheUltra. This system provides a robust foundation for managing service dependencies, lifecycles, and configurations throughout the application.

## Architecture Components

### 1. Dependency Injection Container (`container.py`)

The core DI container provides service registration and resolution with support for:

- **Service Lifetimes**: Singleton, Transient, and Scoped services
- **Automatic Dependency Injection**: Constructor injection with type annotations
- **Factory Pattern Support**: Complex service creation through factories
- **Thread Safety**: All operations are thread-safe
- **Circular Dependency Detection**: Prevents infinite resolution loops
- **Lifecycle Management**: Proper disposal and cleanup

#### Key Classes:
- `DIContainer`: Main container implementation
- `ServiceRegistration`: Service registration metadata
- `ServiceResolutionContext`: Context tracking for resolution chains
- `ScopedServiceProvider`: Manages scoped service instances

#### Usage Example:
```python
from src.core.container import DIContainer, ServiceLifetime
from src.core.interfaces import MediaService, FileService

# Create container
container = DIContainer()

# Register services
container.register_singleton(MediaService, PlexMediaService)
container.register_transient(FileService, LocalFileService)

# Factory registration
container.register_factory(
    CacheService,
    lambda provider: CacheServiceImpl(
        file_service=provider.resolve(FileService),
        media_service=provider.resolve(MediaService)
    ),
    ServiceLifetime.SINGLETON
)

# Resolve services
media_service = container.resolve(MediaService)
cache_service = container.resolve(CacheService)
```

### 2. Service Factory Pattern (`factories.py`)

Factories enable complex service creation with configuration validation:

- **Configuration-Driven Creation**: Services created based on configuration
- **Validation**: Pre-creation configuration validation
- **Retry Logic**: Automatic retry on creation failures
- **Environment Awareness**: Different implementations for different environments

#### Key Classes:
- `IServiceFactory`: Factory interface
- `BaseServiceFactory`: Base implementation with common functionality
- `MediaServiceFactory`: Creates Plex media services
- `FileServiceFactory`: Creates file operation services
- `NotificationServiceFactory`: Creates notification services
- `CacheServiceFactory`: Creates cache management services
- `ServiceFactoryRegistry`: Centralized factory management

#### Usage Example:
```python
from src.core.factories import MediaServiceFactory, register_default_factories

# Create factory with configuration
config_provider = MyConfigProvider()
factory = MediaServiceFactory(config_provider)

# Validate configuration
errors = factory.validate_configuration()
if not errors:
    media_service = factory.create()

# Register default factories
register_default_factories(config_provider)
```

### 3. Service Lifecycle Management (`lifecycle.py`)

Comprehensive lifecycle management for services:

- **Dependency-Ordered Startup**: Services start in dependency order
- **Parallel Startup**: Independent services start in parallel
- **Health Monitoring**: Continuous health checking with recovery
- **Graceful Shutdown**: Coordinated shutdown in reverse dependency order
- **Event Notifications**: Lifecycle events for monitoring

#### Key Classes:
- `ServiceLifecycleManager`: Main lifecycle coordinator
- `ServiceDescriptor`: Service metadata and configuration
- `ILifecycleAware`: Interface for lifecycle-aware services
- `IHealthCheckable`: Interface for health-checkable services
- `ServiceLifecycleEvent`: Lifecycle event data
- `HealthCheck`: Health check result data

#### Usage Example:
```python
from src.core.lifecycle import ServiceLifecycleManager, get_global_lifecycle_manager

# Create lifecycle manager
lifecycle_manager = ServiceLifecycleManager(
    health_check_enabled=True,
    health_check_interval=60.0
)

# Register services with dependencies
config_id = lifecycle_manager.register_service(config_service)
media_id = lifecycle_manager.register_service(
    media_service, 
    dependencies=[config_id]
)

# Start all services
await lifecycle_manager.start_all(parallel=True)

# Monitor health
health_status = lifecycle_manager.get_health_status()

# Graceful shutdown
await lifecycle_manager.shutdown_all()
```

### 4. Configuration-Driven Service Resolution (`service_configuration.py`)

Enables services to be configured through files and environment variables:

- **Multiple Configuration Sources**: Files, environment variables, programmatic
- **Environment-Specific Configurations**: Different setups per environment
- **Validation**: Comprehensive configuration validation
- **Conflict Resolution**: Priority-based service registration

#### Key Classes:
- `ServiceConfiguration`: Complete service configuration
- `ServiceRegistrationInfo`: Individual service registration details
- `ServiceConfigurationBuilder`: Fluent builder for configurations
- `FileServiceConfigurationProvider`: File-based configuration
- `EnvironmentServiceConfigurationProvider`: Environment-based configuration

#### Usage Example:
```python
from src.core.service_configuration import ServiceConfigurationBuilder

# Build configuration from multiple sources
builder = ServiceConfigurationBuilder()
builder.from_file("config/services.yaml")
builder.from_environment()
builder.register_service(
    MediaService,
    factory_type=MediaServiceFactory,
    lifetime=ServiceLifetime.SINGLETON
)

# Build configured container
container = builder.build_container(config_provider)
```

### 5. Service Locator Pattern (`service_locator.py`)

Provides centralized service access throughout the application:

- **Global Access**: Access services from any part of the application
- **Scoped Services**: Temporary service scopes with automatic cleanup
- **Event Monitoring**: Service location event tracking
- **Testing Support**: Easy mocking and service replacement for tests

#### Key Classes:
- `ServiceLocator`: Main service locator (singleton)
- `ScopedServiceLocator`: Scoped service access
- `IServiceLocator`: Service locator interface
- `ServiceLocationEvent`: Location event data

#### Usage Example:
```python
from src.core.service_locator import ServiceLocator, get_service, service_scope

# Initialize with container
ServiceLocator.initialize(container)

# Locate services
media_service = ServiceLocator.get_service(MediaService)
file_service = get_service(FileService)  # Convenience function

# Check availability
if ServiceLocator.has_service(CacheService):
    cache_service = ServiceLocator.get_service(CacheService)

# Scoped access
with service_scope() as scope:
    scoped_service = scope.get_service(ScopedService)
    # Automatically disposed when exiting scope
```

## Integration with Existing Code

### Phase 1 Interfaces

The DI system builds upon the interfaces created in Phase 1:

- **Service Interfaces**: `MediaService`, `FileService`, `NotificationService`, `CacheService`
- **Repository Interfaces**: `CacheRepository`, `ConfigRepository`, `MetricsRepository`
- **Configuration Interfaces**: `ConfigProvider`, `EnvironmentConfig`, `PathConfiguration`

### Existing Implementations

Current implementations can be gradually migrated to use the DI system:

- `PlexOperations` → Implements `MediaService`
- `FileOperations` → Implements `FileService`
- `NotificationManager` → Implements `NotificationService`
- `CacherrEngine` → Implements `CacheService`

## Configuration

### Service Configuration File

Services can be configured through YAML files (see `config/services.yaml`):

```yaml
version: "1.0"
default_environment: "production"

environments:
  production:
    services:
      - service_type: "MediaService"
        factory_type: "MediaServiceFactory"
        lifetime: "singleton"
        dependencies: ["ConfigProvider"]
        enabled: true
```

### Environment Variables

Services can be configured through environment variables:

- `PLEXCACHEULTRA_SERVICE_MEDIA_SERVICE_IMPLEMENTATION`
- `PLEXCACHEULTRA_SERVICE_MEDIA_SERVICE_LIFETIME`
- `PLEXCACHEULTRA_SERVICE_MEDIA_SERVICE_ENABLED`

## Testing

### Mock Services

The DI system facilitates testing with mock services:

```python
# Create container with mock services
container = DIContainer()
container.register_instance(MediaService, MockMediaService())

# Use with service locator
ServiceLocator.initialize(container)

# Tests will use mock services
service = get_service(MediaService)  # Returns MockMediaService
```

### Temporary Registrations

Use temporary service registrations for isolated tests:

```python
from src.core.service_locator import temporary_service_registration

mock_service = MockMediaService()
with temporary_service_registration(MediaService, mock_service):
    # MediaService resolves to mock within this scope
    test_function()
# Original registration restored
```

## Examples

### Complete Example

See `src/core/di_example.py` for comprehensive examples demonstrating:

1. Basic container usage
2. Factory-based registration
3. Lifecycle management
4. Service locator usage
5. Configuration-driven setup

Run the examples:

```python
python src/core/di_example.py
```

### Real-World Integration

```python
# Application startup
from src.core import (
    ServiceConfigurationBuilder, ServiceLocator, 
    get_global_lifecycle_manager, register_default_factories
)

# Build configuration
builder = ServiceConfigurationBuilder()
builder.from_file("config/services.yaml")
builder.from_environment()

# Create configured container
container = builder.build_container(config_provider)

# Initialize service locator
ServiceLocator.initialize(container)

# Setup lifecycle management
lifecycle_manager = get_global_lifecycle_manager()
for service_type in container.get_registered_services():
    if hasattr(service_type, '__lifecycle_aware__'):
        service_instance = container.resolve(service_type)
        lifecycle_manager.register_service(service_instance)

# Start all services
await lifecycle_manager.start_all()

# Application ready to serve requests
# Services available through ServiceLocator.get_service() or get_service()

# Graceful shutdown
await lifecycle_manager.shutdown_all()
container.dispose()
ServiceLocator.reset()
```

## Benefits

1. **Loose Coupling**: Services depend on interfaces, not concrete implementations
2. **Testability**: Easy to replace services with mocks for testing
3. **Configuration**: Services can be configured without code changes
4. **Lifecycle Management**: Proper startup/shutdown ordering and health monitoring
5. **Environment Flexibility**: Different service implementations per environment
6. **Maintainability**: Clear separation of concerns and dependency management

## Next Steps

With Phase 2 complete, the application is ready for Phase 3: refactoring `main.py` into focused modules that utilize this DI system for clean, maintainable service management.

The DI system provides the foundation for:
- Web application module using injected services
- Background task scheduler with service dependencies
- Clean application bootstrap sequence
- Modular architecture with clear boundaries

## Error Handling

The DI system provides comprehensive error handling:

- `ContainerError`: Base container errors
- `ServiceNotRegisteredException`: Service not found
- `CircularDependencyException`: Circular dependency detected
- `ServiceCreationException`: Service creation failed
- `ConfigurationError`: Configuration issues
- `LifecycleError`: Service lifecycle problems

All errors include detailed context for debugging and resolution.

## Performance Considerations

- **Singleton Optimization**: Singletons cached after first resolution
- **Thread Safety**: Minimal locking for high-concurrency scenarios
- **Lazy Resolution**: Services created only when needed
- **Scoped Cleanup**: Automatic resource cleanup for scoped services
- **Health Check Efficiency**: Configurable intervals and timeouts

## Compatibility

The DI system is designed to be:
- **amdx64 Unraid Compatible**: All components work in Docker containers
- **Python 3.8+**: Uses modern Python features with backward compatibility
- **Pydantic Integration**: Full type safety and validation
- **Async Support**: Compatible with asyncio-based operations

This completes the Phase 2 implementation of the dependency injection system for PlexCacheUltra.