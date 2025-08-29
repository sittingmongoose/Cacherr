"""
Example usage of the Dependency Injection system for Cacherr.

This module demonstrates how to use the various DI components including
container setup, service registration, lifecycle management, and service location.

This serves as both documentation and a working example of the DI system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

# Configure logging for the example
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_container_usage():
    """
    Demonstrate basic DI container usage with manual service registration.
    """
    print("=== Basic DI Container Usage ===")
    
    from src.core.container import DIContainer, ServiceLifetime
    from src.core.interfaces import MediaService, FileService, NotificationService
    
    # Create container
    container = DIContainer()
    
    # Note: These would normally be actual implementations
    # For the example, we'll use mock classes
    
    class MockMediaService:
        def __init__(self):
            self.name = "MockMediaService"
        
        def fetch_ondeck_media(self):
            return ["mock_file1.mkv", "mock_file2.mkv"]
    
    class MockFileService:
        def __init__(self, media_service: MediaService):
            self.media_service = media_service
            self.name = "MockFileService"
        
        def process_file_paths(self, files):
            return [f"/processed/{f}" for f in files]
    
    class MockNotificationService:
        def __init__(self):
            self.name = "MockNotificationService"
        
        def send_notification(self, message, level="info"):
            print(f"NOTIFICATION [{level}]: {message}")
            return True
    
    try:
        # Register services
        container.register_singleton(MediaService, MockMediaService)
        container.register_transient(FileService, MockFileService)  # Will inject MediaService
        container.register_singleton(NotificationService, MockNotificationService)
        
        # Resolve services
        media_service = container.resolve(MediaService)
        file_service = container.resolve(FileService)
        notification_service = container.resolve(NotificationService)
        
        print(f"Resolved MediaService: {media_service.name}")
        print(f"Resolved FileService: {file_service.name}")
        print(f"Resolved NotificationService: {notification_service.name}")
        
        # Test service interaction
        files = media_service.fetch_ondeck_media()
        processed_files = file_service.process_file_paths(files)
        notification_service.send_notification(f"Processed {len(processed_files)} files")
        
        # Verify singleton behavior
        media_service2 = container.resolve(MediaService)
        print(f"Singleton check: {media_service is media_service2}")
        
        # Verify transient behavior
        file_service2 = container.resolve(FileService)
        print(f"Transient check: {file_service is file_service2}")
        
    except Exception as e:
        print(f"Error in basic container usage: {e}")
        import traceback
        traceback.print_exc()
    finally:
        container.dispose()


def example_factory_based_registration():
    """
    Demonstrate factory-based service registration.
    """
    print("\n=== Factory-Based Service Registration ===")
    
    from src.core.container import DIContainer, ServiceLifetime
    from src.core.factories import ServiceFactoryRegistry, FactoryConfiguration
    from src.core.interfaces import MediaService, NotificationService
    
    class MockConfigProvider:
        def get_string(self, key, default=None, section=None):
            config_values = {
                "PLEX_URL": "http://localhost:32400",
                "PLEX_TOKEN": "mock_token_12345",
                "WEBHOOK_URL": "http://localhost:5445/webhook"
            }
            return config_values.get(key, default)
        
        def get_int(self, key, default=None, section=None):
            config_values = {
                "PLEX_TIMEOUT": 30,
                "PLEX_RETRY_LIMIT": 3,
                "NOTIFICATION_RATE_LIMIT_MINUTES": 5
            }
            return config_values.get(key, default)
        
        def get_bool(self, key, default=None, section=None):
            config_values = {
                "ENABLE_SUCCESS_NOTIFICATIONS": True,
                "ENABLE_ERROR_NOTIFICATIONS": True
            }
            return config_values.get(key, default)
    
    # Create factory with mock config
    config_provider = MockConfigProvider()
    
    # Create container with factory registration
    container = DIContainer()
    
    try:
        # Register using factory pattern
        def media_service_factory(provider):
            # In real implementation, this would create actual PlexOperations
            class MockPlexOperations:
                def __init__(self):
                    self.name = "MockPlexOperations"
                    self.configured = True
                
                def fetch_ondeck_media(self):
                    return ["factory_file1.mkv", "factory_file2.mkv"]
            
            return MockPlexOperations()
        
        def notification_service_factory(provider):
            # In real implementation, this would create actual NotificationManager
            class MockNotificationManager:
                def __init__(self):
                    self.name = "MockNotificationManager"
                    self.webhook_url = config_provider.get_string("WEBHOOK_URL")
                
                def send_notification(self, message, level="info"):
                    print(f"WEBHOOK NOTIFICATION [{level}]: {message}")
                    return True
            
            return MockNotificationManager()
        
        # Register factories
        container.register_factory(MediaService, media_service_factory, ServiceLifetime.SINGLETON)
        container.register_factory(NotificationService, notification_service_factory, ServiceLifetime.SINGLETON)
        
        # Resolve services
        media_service = container.resolve(MediaService)
        notification_service = container.resolve(NotificationService)
        
        print(f"Factory-created MediaService: {media_service.name}")
        print(f"Factory-created NotificationService: {notification_service.name}")
        
        # Test services
        files = media_service.fetch_ondeck_media()
        notification_service.send_notification(f"Factory created service processed {len(files)} files")
        
    except Exception as e:
        print(f"Error in factory-based registration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        container.dispose()


async def example_lifecycle_management():
    """
    Demonstrate service lifecycle management.
    """
    print("\n=== Service Lifecycle Management ===")
    
    from src.core.lifecycle import (
        ServiceLifecycleManager, ILifecycleAware, IHealthCheckable,
        HealthCheck, HealthStatus
    )
    
    class MockLifecycleService(ILifecycleAware, IHealthCheckable):
        def __init__(self, name: str):
            self.name = name
            self.initialized = False
            self.started = False
            self.health_check_count = 0
        
        async def initialize(self) -> bool:
            print(f"Initializing {self.name}")
            await asyncio.sleep(0.1)  # Simulate initialization work
            self.initialized = True
            return True
        
        async def start(self) -> bool:
            print(f"Starting {self.name}")
            await asyncio.sleep(0.1)  # Simulate startup work
            self.started = True
            return True
        
        async def stop(self) -> bool:
            print(f"Stopping {self.name}")
            await asyncio.sleep(0.1)  # Simulate shutdown work
            self.started = False
            return True
        
        async def dispose(self) -> None:
            print(f"Disposing {self.name}")
            self.initialized = False
            self.started = False
        
        async def check_health(self) -> HealthCheck:
            self.health_check_count += 1
            status = HealthStatus.HEALTHY if self.started else HealthStatus.UNHEALTHY
            
            return HealthCheck(
                service_id=self.name,
                status=status,
                response_time_ms=10.0,
                details={"check_count": self.health_check_count}
            )
    
    # Create lifecycle manager
    lifecycle_manager = ServiceLifecycleManager(
        health_check_enabled=True,
        health_check_interval=2.0  # Short interval for demo
    )
    
    # Event listener for lifecycle events
    def on_lifecycle_event(event):
        print(f"Lifecycle Event: {event.service_id} -> {event.event_type} (state: {event.new_state})")
    
    lifecycle_manager.add_event_listener(on_lifecycle_event)
    
    try:
        # Register services with dependencies
        config_service = MockLifecycleService("ConfigService")
        media_service = MockLifecycleService("MediaService")
        cache_service = MockLifecycleService("CacheService")
        
        config_id = lifecycle_manager.register_service(
            config_service, 
            service_id="config_service"
        )
        
        media_id = lifecycle_manager.register_service(
            media_service,
            service_id="media_service",
            dependencies=["config_service"]
        )
        
        cache_id = lifecycle_manager.register_service(
            cache_service,
            service_id="cache_service", 
            dependencies=["media_service", "config_service"]
        )
        
        print(f"Registered services: {config_id}, {media_id}, {cache_id}")
        
        # Start all services
        print("\nStarting all services...")
        startup_results = await lifecycle_manager.start_all(parallel=True)
        print(f"Startup results: {startup_results}")
        
        # Check service states
        print("\nService states after startup:")
        states = lifecycle_manager.get_all_service_states()
        for service_id, state in states.items():
            print(f"  {service_id}: {state}")
        
        # Wait a bit for health checks
        print("\nWaiting for health checks...")
        await asyncio.sleep(3)
        
        # Get health status
        health_status = lifecycle_manager.get_health_status()
        print("\nHealth status:")
        for service_id, health in health_status.items():
            print(f"  {service_id}: {health.status} (checks: {health.details.get('check_count', 0)})")
        
        # Shutdown all services
        print("\nShutting down all services...")
        shutdown_results = await lifecycle_manager.shutdown_all()
        print(f"Shutdown results: {shutdown_results}")
        
    except Exception as e:
        print(f"Error in lifecycle management: {e}")
        import traceback
        traceback.print_exc()


def example_service_locator():
    """
    Demonstrate service locator pattern usage.
    """
    print("\n=== Service Locator Pattern ===")
    
    from src.core.container import DIContainer
    from src.core.service_locator import ServiceLocator, get_service, has_service, service_scope
    from src.core.interfaces import MediaService, FileService
    
    class MockMediaService:
        def __init__(self):
            self.name = "MockMediaService"
        
        def fetch_ondeck_media(self):
            return ["locator_file1.mkv"]
    
    class MockFileService:
        def __init__(self):
            self.name = "MockFileService"
        
        def process_file_paths(self, files):
            return [f"/locator/{f}" for f in files]
    
    # Create and configure container
    container = DIContainer()
    container.register_singleton(MediaService, MockMediaService)
    container.register_transient(FileService, MockFileService)
    
    try:
        # Initialize service locator
        ServiceLocator.initialize(container)
        
        # Use service locator directly
        print("Using ServiceLocator class methods:")
        media_service = ServiceLocator.get_service(MediaService)
        print(f"Located MediaService: {media_service.name}")
        
        # Use convenience functions
        print("\nUsing convenience functions:")
        file_service = get_service(FileService)
        print(f"Located FileService: {file_service.name}")
        
        # Check service availability
        print(f"Has MediaService: {has_service(MediaService)}")
        print(f"Has CacheService: {has_service('NonexistentService')}")  # Should be False
        
        # Use scoped service locator
        print("\nUsing scoped service locator:")
        with service_scope() as scope:
            scoped_file_service = scope.get_service(FileService)
            print(f"Scoped FileService: {scoped_file_service.name}")
            # Scoped services are automatically disposed when exiting context
        
        # Test service interaction through locator
        files = media_service.fetch_ondeck_media()
        processed_files = file_service.process_file_paths(files)
        print(f"Processed files: {processed_files}")
        
    except Exception as e:
        print(f"Error in service locator: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        container.dispose()
        ServiceLocator.reset()


def example_configuration_driven_setup():
    """
    Demonstrate configuration-driven container setup.
    """
    print("\n=== Configuration-Driven Container Setup ===")
    
    from src.core.service_configuration import (
        ServiceConfigurationBuilder, ServiceConfiguration,
        ServiceRegistrationInfo, ServiceImplementationStrategy,
        EnvironmentServiceConfigurationProvider
    )
    from src.core.container import ServiceLifetime
    
    # Mock configuration provider
    class MockConfigProvider:
        def get_string(self, key, default=None, section=None):
            return {
                "PLEX_URL": "http://localhost:32400",
                "PLEX_TOKEN": "mock_token",
                "CACHE_DESTINATION": "/cache",
                "PLEX_SOURCE": "/media"
            }.get(key, default)
        
        def get_int(self, key, default=None, section=None):
            return {
                "MAX_CONCURRENT_MOVES_CACHE": 5,
                "MAX_CONCURRENT_MOVES_ARRAY": 2
            }.get(key, default)
        
        def get_bool(self, key, default=None, section=None):
            return {
                "ENABLE_SUCCESS_NOTIFICATIONS": True
            }.get(key, default)
    
    config_provider = MockConfigProvider()
    
    try:
        # Build configuration programmatically
        builder = ServiceConfigurationBuilder()
        
        # Add environment-based configuration
        builder.from_environment()
        
        # Add programmatic service registrations
        from src.core.interfaces import MediaService, FileService, NotificationService
        
        builder.register_service(
            MediaService,
            factory_type=type("MediaServiceFactory", (), {}),  # Mock factory type
            lifetime=ServiceLifetime.SINGLETON,
            enabled=True,
            priority=1
        )
        
        builder.register_service(
            FileService,
            factory_type=type("FileServiceFactory", (), {}),  # Mock factory type
            lifetime=ServiceLifetime.TRANSIENT,
            dependencies=["MediaService"],
            enabled=True,
            priority=1
        )
        
        # Build configuration
        service_config = builder.build_configuration()
        
        print(f"Built configuration with {len(service_config.global_services)} global services")
        print(f"Available environments: {list(service_config.environments.keys())}")
        
        # Display service registrations
        for service in service_config.global_services:
            print(f"  Service: {service.service_type} ({service.lifetime})")
            if service.dependencies:
                print(f"    Dependencies: {service.dependencies}")
        
        # Note: Full container building would require actual factory implementations
        print("Configuration built successfully (container building skipped for mock example)")
        
    except Exception as e:
        print(f"Error in configuration-driven setup: {e}")
        import traceback
        traceback.print_exc()


async def run_all_examples():
    """Run all DI system examples."""
    print("PlexCacheUltra Dependency Injection System Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_container_usage()
        example_factory_based_registration()
        await example_lifecycle_management()
        example_service_locator()
        example_configuration_driven_setup()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(run_all_examples())