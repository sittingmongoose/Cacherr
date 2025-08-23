"""
Unit tests for the dependency injection container system.

This module provides comprehensive tests for the DIContainer class,
service registration, resolution, and lifecycle management.
"""

import pytest
import threading
import time
from typing import Protocol, runtime_checkable
from unittest.mock import Mock, MagicMock, patch

from src.core.container import (
    DIContainer, ServiceLifetime, ServiceRegistration, ServiceResolutionContext,
    ScopedServiceProvider, ContainerError, ServiceNotRegisteredException,
    CircularDependencyException, ServiceCreationException,
    MaxResolutionDepthExceededException, IServiceProvider
)


# Test interfaces and implementations
@runtime_checkable
class ITestService(Protocol):
    """Test service interface."""
    def do_work(self) -> str: ...


class TestService:
    """Test service implementation."""
    def __init__(self, dependency: str = "default"):
        self.dependency = dependency
        self.created_at = time.time()
    
    def do_work(self) -> str:
        return f"Working with {self.dependency}"


class TestServiceWithDependency:
    """Test service with dependency injection."""
    def __init__(self, test_service: ITestService):
        self.test_service = test_service
    
    def do_complex_work(self) -> str:
        return f"Complex: {self.test_service.do_work()}"


class DisposableTestService:
    """Test service with dispose method."""
    def __init__(self):
        self.disposed = False
    
    def dispose(self):
        self.disposed = True


class CircularDependencyA:
    """Service A that depends on B for circular dependency testing."""
    def __init__(self, service_b: 'CircularDependencyB'):
        self.service_b = service_b


class CircularDependencyB:
    """Service B that depends on A for circular dependency testing."""  
    def __init__(self, service_a: CircularDependencyA):
        self.service_a = service_a


class TestDIContainer:
    """Test cases for DIContainer."""
    
    def test_container_initialization(self, clean_container: DIContainer):
        """Test container initialization with default parameters."""
        container = clean_container
        
        assert container is not None
        assert not container._disposed
        assert len(container.get_registered_services()) == 0
        assert container._max_resolution_depth == 50
    
    def test_container_initialization_with_custom_params(self):
        """Test container initialization with custom parameters."""
        container = DIContainer(max_resolution_depth=10)
        try:
            assert container._max_resolution_depth == 10
        finally:
            container.dispose()
    
    def test_register_singleton(self, clean_container: DIContainer):
        """Test singleton service registration."""
        container = clean_container
        
        container.register_singleton(ITestService, TestService)
        
        assert container.is_registered(ITestService)
        registration = container.get_service_info(ITestService)
        assert registration is not None
        assert registration.lifetime == ServiceLifetime.SINGLETON
        assert registration.implementation_type == TestService
    
    def test_register_transient(self, clean_container: DIContainer):
        """Test transient service registration."""
        container = clean_container
        
        container.register_transient(ITestService, TestService)
        
        assert container.is_registered(ITestService)
        registration = container.get_service_info(ITestService)
        assert registration is not None
        assert registration.lifetime == ServiceLifetime.TRANSIENT
        assert registration.implementation_type == TestService
    
    def test_register_scoped(self, clean_container: DIContainer):
        """Test scoped service registration."""
        container = clean_container
        
        container.register_scoped(ITestService, TestService)
        
        assert container.is_registered(ITestService)
        registration = container.get_service_info(ITestService)
        assert registration is not None
        assert registration.lifetime == ServiceLifetime.SCOPED
        assert registration.implementation_type == TestService
    
    def test_register_factory(self, clean_container: DIContainer):
        """Test factory-based service registration."""
        container = clean_container
        
        factory = lambda provider: TestService("factory-created")
        container.register_factory(ITestService, factory, ServiceLifetime.SINGLETON)
        
        assert container.is_registered(ITestService)
        registration = container.get_service_info(ITestService)
        assert registration is not None
        assert registration.lifetime == ServiceLifetime.SINGLETON
        assert registration.is_factory_registration
        assert registration.factory is not None
    
    def test_register_instance(self, clean_container: DIContainer):
        """Test instance registration."""
        container = clean_container
        instance = TestService("pre-created")
        
        container.register_instance(ITestService, instance)
        
        assert container.is_registered(ITestService)
        registration = container.get_service_info(ITestService)
        assert registration is not None
        assert registration.lifetime == ServiceLifetime.SINGLETON
        assert registration.instance is instance
    
    def test_register_instance_type_validation(self, clean_container: DIContainer):
        """Test instance registration with type validation."""
        container = clean_container
        invalid_instance = "not a TestService"
        
        with pytest.raises(ValueError):
            container.register_instance(ITestService, invalid_instance)
    
    def test_resolve_singleton(self, clean_container: DIContainer):
        """Test singleton service resolution."""
        container = clean_container
        container.register_singleton(ITestService, TestService)
        
        # First resolution
        service1 = container.resolve(ITestService)
        assert service1 is not None
        assert isinstance(service1, TestService)
        
        # Second resolution should return same instance
        service2 = container.resolve(ITestService)
        assert service1 is service2
        
        # Verify resolution count
        registration = container.get_service_info(ITestService)
        assert registration.resolve_count == 2
    
    def test_resolve_transient(self, clean_container: DIContainer):
        """Test transient service resolution."""
        container = clean_container
        container.register_transient(ITestService, TestService)
        
        # First resolution
        service1 = container.resolve(ITestService)
        assert service1 is not None
        assert isinstance(service1, TestService)
        
        # Second resolution should return different instance
        service2 = container.resolve(ITestService)
        assert service1 is not service2
        assert service1.created_at != service2.created_at
    
    def test_resolve_factory(self, clean_container: DIContainer):
        """Test factory-based service resolution."""
        container = clean_container
        
        factory_call_count = 0
        def test_factory(provider):
            nonlocal factory_call_count
            factory_call_count += 1
            return TestService(f"factory-call-{factory_call_count}")
        
        container.register_factory(ITestService, test_factory, ServiceLifetime.TRANSIENT)
        
        service1 = container.resolve(ITestService)
        service2 = container.resolve(ITestService)
        
        assert factory_call_count == 2
        assert service1.dependency == "factory-call-1"
        assert service2.dependency == "factory-call-2"
    
    def test_resolve_with_dependency_injection(self, clean_container: DIContainer):
        """Test service resolution with automatic dependency injection."""
        container = clean_container
        
        container.register_singleton(ITestService, TestService)
        container.register_singleton(TestServiceWithDependency, TestServiceWithDependency)
        
        service = container.resolve(TestServiceWithDependency)
        
        assert service is not None
        assert isinstance(service, TestServiceWithDependency)
        assert service.test_service is not None
        assert isinstance(service.test_service, TestService)
        assert service.do_complex_work() == "Complex: Working with default"
    
    def test_resolve_unregistered_service(self, clean_container: DIContainer):
        """Test resolution of unregistered service raises exception."""
        container = clean_container
        
        with pytest.raises(ServiceNotRegisteredException) as exc_info:
            container.resolve(ITestService)
        
        assert "not registered" in str(exc_info.value)
        assert ITestService.__name__ in str(exc_info.value)
    
    def test_try_resolve(self, clean_container: DIContainer):
        """Test try_resolve method."""
        container = clean_container
        
        # Unregistered service should return None
        result = container.try_resolve(ITestService)
        assert result is None
        
        # Registered service should return instance
        container.register_singleton(ITestService, TestService)
        result = container.try_resolve(ITestService)
        assert result is not None
        assert isinstance(result, TestService)
    
    def test_circular_dependency_detection(self, clean_container: DIContainer):
        """Test circular dependency detection."""
        container = clean_container
        
        container.register_singleton(CircularDependencyA, CircularDependencyA)
        container.register_singleton(CircularDependencyB, CircularDependencyB)
        
        with pytest.raises(CircularDependencyException) as exc_info:
            container.resolve(CircularDependencyA)
        
        assert "Circular dependency detected" in str(exc_info.value)
    
    def test_max_resolution_depth(self):
        """Test maximum resolution depth protection."""
        container = DIContainer(max_resolution_depth=2)
        try:
            container.register_singleton(CircularDependencyA, CircularDependencyA)
            container.register_singleton(CircularDependencyB, CircularDependencyB)
            
            with pytest.raises(MaxResolutionDepthExceededException) as exc_info:
                container.resolve(CircularDependencyA)
            
            assert "Maximum resolution depth" in str(exc_info.value)
        finally:
            container.dispose()
    
    def test_service_creation_exception(self, clean_container: DIContainer):
        """Test service creation exception handling."""
        container = clean_container
        
        class FailingService:
            def __init__(self):
                raise RuntimeError("Service creation failed")
        
        container.register_singleton(FailingService, FailingService)
        
        with pytest.raises(ServiceCreationException) as exc_info:
            container.resolve(FailingService)
        
        assert "Failed to create service" in str(exc_info.value)
        assert "Service creation failed" in str(exc_info.value)
    
    def test_thread_safety(self, clean_container: DIContainer):
        """Test thread safety of container operations."""
        container = clean_container
        container.register_singleton(ITestService, TestService)
        
        services = []
        threads = []
        
        def resolve_service():
            service = container.resolve(ITestService)
            services.append(service)
        
        # Create multiple threads that resolve the same singleton
        for _ in range(10):
            thread = threading.Thread(target=resolve_service)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All resolved services should be the same instance (singleton)
        assert len(services) == 10
        first_service = services[0]
        for service in services[1:]:
            assert service is first_service
    
    def test_creation_callbacks(self, clean_container: DIContainer):
        """Test service creation callbacks."""
        container = clean_container
        callback_calls = []
        
        def creation_callback(instance):
            callback_calls.append(instance)
        
        container.add_creation_callback(ITestService, creation_callback)
        container.register_singleton(ITestService, TestService)
        
        service = container.resolve(ITestService)
        
        assert len(callback_calls) == 1
        assert callback_calls[0] is service
    
    def test_disposal_callbacks(self, clean_container: DIContainer):
        """Test service disposal callbacks."""
        container = clean_container
        callback_calls = []
        
        def disposal_callback(instance):
            callback_calls.append(instance)
        
        service = DisposableTestService()
        container.register_instance(DisposableTestService, service)
        container.add_disposal_callback(DisposableTestService, disposal_callback)
        
        container.dispose()
        
        assert len(callback_calls) == 1
        assert callback_calls[0] is service
        assert service.disposed  # Service's own dispose method should be called too
    
    def test_container_disposal(self, clean_container: DIContainer):
        """Test container disposal and cleanup."""
        container = clean_container
        
        # Register a disposable service
        service = DisposableTestService()
        container.register_instance(DisposableTestService, service)
        
        # Dispose container
        container.dispose()
        
        assert container._disposed
        assert service.disposed
        assert len(container.get_registered_services()) == 0
        
        # Operations on disposed container should raise exception
        with pytest.raises(ContainerError):
            container.resolve(DisposableTestService)
    
    def test_context_manager(self):
        """Test container as context manager."""
        service = DisposableTestService()
        
        with DIContainer() as container:
            container.register_instance(DisposableTestService, service)
            resolved = container.resolve(DisposableTestService)
            assert resolved is service
            assert not service.disposed
        
        # After exiting context, container should be disposed
        assert service.disposed
    
    def test_get_registered_services(self, clean_container: DIContainer):
        """Test getting list of registered services."""
        container = clean_container
        
        assert len(container.get_registered_services()) == 0
        
        container.register_singleton(ITestService, TestService)
        container.register_transient(TestServiceWithDependency, TestServiceWithDependency)
        
        services = container.get_registered_services()
        assert len(services) == 2
        assert ITestService in services
        assert TestServiceWithDependency in services


class TestScopedServiceProvider:
    """Test cases for ScopedServiceProvider."""
    
    def test_scoped_provider_creation(self, clean_container: DIContainer):
        """Test scoped service provider creation."""
        container = clean_container
        scoped_provider = container.create_scope()
        
        assert scoped_provider is not None
        assert isinstance(scoped_provider, ScopedServiceProvider)
        assert scoped_provider._parent_container is container
        assert not scoped_provider._disposed
    
    def test_scoped_service_resolution(self, clean_container: DIContainer):
        """Test scoped service resolution."""
        container = clean_container
        container.register_scoped(ITestService, TestService)
        
        with container.create_scope() as scope1:
            with container.create_scope() as scope2:
                # Resolve service in different scopes
                service1 = scope1.resolve(ITestService)
                service2 = scope2.resolve(ITestService)
                
                # Services should be different instances (different scopes)
                assert service1 is not service2
                
                # Resolving again in same scope should return same instance
                service1_again = scope1.resolve(ITestService)
                assert service1 is service1_again
    
    def test_scoped_provider_singleton_delegation(self, clean_container: DIContainer):
        """Test that scoped provider delegates singleton resolution to parent."""
        container = clean_container
        container.register_singleton(ITestService, TestService)
        
        with container.create_scope() as scoped_provider:
            service = scoped_provider.resolve(ITestService)
            parent_service = container.resolve(ITestService)
            
            # Should be the same singleton instance
            assert service is parent_service
    
    def test_scoped_provider_disposal(self, clean_container: DIContainer):
        """Test scoped provider disposal."""
        container = clean_container
        container.register_scoped(DisposableTestService, DisposableTestService)
        
        scoped_provider = container.create_scope()
        service = scoped_provider.resolve(DisposableTestService)
        
        assert not service.disposed
        
        scoped_provider.dispose()
        
        assert scoped_provider._disposed
        assert service.disposed
    
    def test_scoped_provider_context_manager(self, clean_container: DIContainer):
        """Test scoped provider as context manager."""
        container = clean_container
        container.register_scoped(DisposableTestService, DisposableTestService)
        
        service = None
        with container.create_scope() as scoped_provider:
            service = scoped_provider.resolve(DisposableTestService)
            assert not service.disposed
        
        # After exiting context, scoped service should be disposed
        assert service.disposed


class TestServiceRegistration:
    """Test cases for ServiceRegistration model."""
    
    def test_service_registration_creation(self):
        """Test ServiceRegistration model creation."""
        registration = ServiceRegistration(
            service_type=ITestService,
            implementation_type=TestService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        assert registration.service_type == ITestService
        assert registration.implementation_type == TestService
        assert registration.lifetime == ServiceLifetime.SINGLETON
        assert not registration.is_factory_registration
        assert registration.resolve_count == 0
    
    def test_service_registration_factory(self):
        """Test ServiceRegistration with factory."""
        factory = lambda provider: TestService()
        registration = ServiceRegistration(
            service_type=ITestService,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        assert registration.service_type == ITestService
        assert registration.factory is factory
        assert registration.lifetime == ServiceLifetime.TRANSIENT
        assert registration.is_factory_registration
    
    def test_service_registration_validation(self):
        """Test ServiceRegistration validation."""
        # Should raise error when neither factory nor implementation_type is provided
        with pytest.raises(ValueError):
            ServiceRegistration(
                service_type=ITestService,
                lifetime=ServiceLifetime.SINGLETON
            )


class TestServiceResolutionContext:
    """Test cases for ServiceResolutionContext."""
    
    def test_context_creation(self):
        """Test context creation with default values."""
        context = ServiceResolutionContext()
        
        assert context.requesting_service is None
        assert context.resolution_chain == []
        assert context.resolution_depth == 0
        assert context.max_resolution_depth == 50
    
    def test_add_to_chain(self):
        """Test adding service to resolution chain."""
        context = ServiceResolutionContext()
        new_context = context.add_to_chain(ITestService)
        
        assert new_context.resolution_chain == [ITestService]
        assert new_context.resolution_depth == 1
        
        # Original context should be unchanged
        assert context.resolution_chain == []
        assert context.resolution_depth == 0
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection in context."""
        context = ServiceResolutionContext()
        context = context.add_to_chain(ITestService)
        
        assert not context.has_circular_dependency(TestService)
        assert context.has_circular_dependency(ITestService)
    
    def test_max_depth_detection(self):
        """Test maximum depth detection."""
        context = ServiceResolutionContext(max_resolution_depth=2)
        
        assert not context.is_max_depth_exceeded()
        
        context = context.add_to_chain(ITestService)
        assert not context.is_max_depth_exceeded()
        
        context = context.add_to_chain(TestService)
        assert context.is_max_depth_exceeded()