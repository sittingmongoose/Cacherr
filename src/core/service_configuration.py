"""
Configuration-Driven Service Resolution for PlexCacheUltra.

This module provides configuration-driven service registration and resolution
capabilities for the dependency injection container. It allows services to be
configured and wired through configuration files, environment variables, and
programmatic configuration builders.

The configuration system supports:
- Environment-specific service configurations
- Factory registration through configuration
- Service lifetime management via configuration
- Conditional service registration
- Configuration validation and error reporting
- Dynamic service swapping based on environment
- Service composition and dependency wiring

Example:
    Configuration-driven container setup:
    
    ```python
    config_builder = ServiceConfigurationBuilder()
    config_builder.from_environment()
    config_builder.from_config_file("services.yaml")
    
    container = config_builder.build_container()
    ```
    
    Programmatic service configuration:
    
    ```python
    service_config = ServiceConfiguration()
    service_config.register_service(
        MediaService,
        implementation="PlexMediaService",
        lifetime=ServiceLifetime.SINGLETON,
        dependencies=["ConfigProvider"]
    )
    ```
"""

import os
import yaml
import json
import logging
from abc import ABC, abstractmethod
from typing import (
    Type, Dict, Any, Optional, List, Union, Callable, 
    get_type_hints, get_origin, get_args
)
from pathlib import Path
from enum import Enum
import importlib
import inspect

from pydantic import BaseModel, Field, field_validator, ValidationError

from .container import DIContainer, ServiceLifetime, IServiceProvider
from .factories import (
    IServiceFactory, ServiceFactoryRegistry, 
    MediaServiceFactory, FileServiceFactory, NotificationServiceFactory, CacheServiceFactory
)
from .interfaces import MediaService, FileService, NotificationService, CacheService
from .repositories import CacheRepository, ConfigRepository, MetricsRepository
from ..config.interfaces import ConfigProvider, EnvironmentConfig, PathConfiguration

logger = logging.getLogger(__name__)


class ServiceImplementationStrategy(Enum):
    """Strategy for determining service implementations."""
    TYPE_BASED = "type_based"      # Use explicit type specification
    FACTORY_BASED = "factory_based"  # Use factory functions
    AUTO_DISCOVERY = "auto_discovery"  # Automatic discovery based on interfaces
    ENVIRONMENT = "environment"    # Environment-specific selection


class ServiceRegistrationInfo(BaseModel):
    """
    Information about a service registration.
    
    Attributes:
        service_type: Name or type of the service interface
        implementation_type: Name or type of the implementation (optional for factories)
        factory_type: Name or type of the factory class (optional)
        factory_method: Method name for factory creation (optional)
        lifetime: Service lifetime strategy
        dependencies: List of dependency service names
        implementation_strategy: Strategy for determining implementation
        environment_conditions: Conditions for environment-specific registration
        configuration_section: Configuration section for service settings
        initialization_parameters: Parameters for service initialization
        enabled: Whether this service registration is enabled
        priority: Priority for conflict resolution (higher wins)
    """
    service_type: str
    implementation_type: Optional[str] = None
    factory_type: Optional[str] = None
    factory_method: Optional[str] = "create"
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[str] = Field(default_factory=list)
    implementation_strategy: ServiceImplementationStrategy = ServiceImplementationStrategy.TYPE_BASED
    environment_conditions: Dict[str, Any] = Field(default_factory=dict)
    configuration_section: Optional[str] = None
    initialization_parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    
    class Config:
        use_enum_values = True
    
    @field_validator('service_type')
    @classmethod
    def validate_service_type(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("service_type must be a non-empty string")
        return v
    
    @field_validator('implementation_type', 'factory_type')
    @classmethod
    def validate_implementation_strategy(cls, v, info):
        values = info.data
        strategy = values.get('implementation_strategy')
        implementation_type = values.get('implementation_type')
        factory_type = values.get('factory_type')
        
        if strategy == ServiceImplementationStrategy.TYPE_BASED and not implementation_type:
            raise ValueError("implementation_type is required for TYPE_BASED strategy")
        elif strategy == ServiceImplementationStrategy.FACTORY_BASED and not factory_type:
            raise ValueError("factory_type is required for FACTORY_BASED strategy")
        
        return v


class EnvironmentServiceConfiguration(BaseModel):
    """
    Environment-specific service configuration.
    
    Attributes:
        environment_name: Name of the environment
        services: List of service registrations for this environment
        default_lifetime: Default service lifetime for this environment
        auto_discovery_enabled: Whether to enable auto-discovery
        factory_search_paths: Paths to search for factory implementations
        configuration_overrides: Configuration overrides for this environment
    """
    environment_name: str
    services: List[ServiceRegistrationInfo] = Field(default_factory=list)
    default_lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    auto_discovery_enabled: bool = False
    factory_search_paths: List[str] = Field(default_factory=list)
    configuration_overrides: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class ServiceConfiguration(BaseModel):
    """
    Complete service configuration for the application.
    
    Attributes:
        version: Configuration version for compatibility checking
        default_environment: Default environment name
        environments: Environment-specific configurations
        global_services: Services available in all environments
        factory_registry_config: Configuration for factory registry
        container_config: Configuration for DI container
    """
    version: str = "1.0"
    default_environment: str = "production"
    environments: Dict[str, EnvironmentServiceConfiguration] = Field(default_factory=dict)
    global_services: List[ServiceRegistrationInfo] = Field(default_factory=list)
    factory_registry_config: Dict[str, Any] = Field(default_factory=dict)
    container_config: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('environments')
    @classmethod
    def validate_default_environment_exists(cls, v, info):
        values = info.data
        default_env = values.get('default_environment')
        if default_env and default_env not in v:
            raise ValueError(f"Default environment '{default_env}' not found in environments")
        return v


class ConfigurationError(Exception):
    """Base exception for configuration-related errors."""
    pass


class ServiceResolutionError(ConfigurationError):
    """Raised when service resolution from configuration fails."""
    
    def __init__(self, service_name: str, reason: str, inner_exception: Exception = None):
        self.service_name = service_name
        self.reason = reason
        self.inner_exception = inner_exception
        
        message = f"Failed to resolve service '{service_name}': {reason}"
        if inner_exception:
            message += f" (Inner exception: {str(inner_exception)})"
        
        super().__init__(message)


class IServiceConfigurationProvider(ABC):
    """Interface for service configuration providers."""
    
    @abstractmethod
    def load_configuration(self) -> ServiceConfiguration:
        """
        Load service configuration.
        
        Returns:
            ServiceConfiguration instance
            
        Raises:
            ConfigurationError: When configuration loading fails
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, config: ServiceConfiguration) -> List[str]:
        """
        Validate service configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation error messages
        """
        pass


class FileServiceConfigurationProvider(IServiceConfigurationProvider):
    """Service configuration provider that loads from files."""
    
    def __init__(self, config_path: Union[str, Path], format: str = "auto"):
        """
        Initialize the file configuration provider.
        
        Args:
            config_path: Path to the configuration file
            format: Configuration format ("yaml", "json", or "auto")
        """
        self.config_path = Path(config_path)
        self.format = format
        
    def load_configuration(self) -> ServiceConfiguration:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.format == "auto":
                    format_type = self.config_path.suffix.lower()
                else:
                    format_type = f".{self.format}"
                
                if format_type in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif format_type == '.json':
                    data = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported configuration format: {format_type}")
            
            return ServiceConfiguration(**data)
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to parse configuration file: {str(e)}")
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def validate_configuration(self, config: ServiceConfiguration) -> List[str]:
        """Validate file-based configuration."""
        errors = []
        
        # Validate service type references
        all_services = config.global_services.copy()
        for env_config in config.environments.values():
            all_services.extend(env_config.services)
        
        service_names = {service.service_type for service in all_services}
        
        for service in all_services:
            # Check dependency references
            for dependency in service.dependencies:
                if dependency not in service_names:
                    errors.append(
                        f"Service '{service.service_type}' has unknown dependency: '{dependency}'"
                    )
            
            # Validate implementation strategy consistency
            if (service.implementation_strategy == ServiceImplementationStrategy.TYPE_BASED and 
                not service.implementation_type):
                errors.append(
                    f"Service '{service.service_type}' uses TYPE_BASED strategy but has no implementation_type"
                )
            
            if (service.implementation_strategy == ServiceImplementationStrategy.FACTORY_BASED and 
                not service.factory_type):
                errors.append(
                    f"Service '{service.service_type}' uses FACTORY_BASED strategy but has no factory_type"
                )
        
        return errors


class EnvironmentServiceConfigurationProvider(IServiceConfigurationProvider):
    """Service configuration provider that loads from environment variables."""
    
    def __init__(self, prefix: str = "PLEXCACHEULTRA_SERVICE_", 
                 environment_provider: Optional[EnvironmentConfig] = None):
        """
        Initialize the environment configuration provider.
        
        Args:
            prefix: Prefix for environment variable names
            environment_provider: Optional environment configuration provider
        """
        self.prefix = prefix
        self.environment_provider = environment_provider
    
    def load_configuration(self) -> ServiceConfiguration:
        """Load configuration from environment variables."""
        try:
            # Determine current environment
            current_env = os.getenv('ENVIRONMENT', 'production')
            
            # Load basic configuration
            config = ServiceConfiguration(
                default_environment=current_env,
                environments={current_env: EnvironmentServiceConfiguration(environment_name=current_env)}
            )
            
            # Load service registrations from environment
            self._load_service_registrations(config, current_env)
            
            return config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load environment configuration: {str(e)}")
    
    def validate_configuration(self, config: ServiceConfiguration) -> List[str]:
        """Validate environment-based configuration."""
        errors = []
        
        # Check if environment is detected correctly
        if self.environment_provider:
            try:
                detected_env = self.environment_provider.detect_environment()
                if detected_env not in config.environments:
                    errors.append(f"Detected environment '{detected_env}' not configured")
            except Exception as e:
                errors.append(f"Environment detection failed: {str(e)}")
        
        return errors
    
    def _load_service_registrations(self, config: ServiceConfiguration, environment: str) -> None:
        """Load service registrations from environment variables."""
        env_config = config.environments[environment]
        
        # Check for specific service configurations
        service_configs = [
            ("MEDIA_SERVICE", MediaService.__name__, "MediaServiceFactory"),
            ("FILE_SERVICE", FileService.__name__, "FileServiceFactory"),
            ("NOTIFICATION_SERVICE", NotificationService.__name__, "NotificationServiceFactory"),
            ("CACHE_SERVICE", CacheService.__name__, "CacheServiceFactory"),
        ]
        
        for env_key, service_type, default_factory in service_configs:
            implementation = os.getenv(f"{self.prefix}{env_key}_IMPLEMENTATION")
            factory_type = os.getenv(f"{self.prefix}{env_key}_FACTORY", default_factory)
            lifetime_str = os.getenv(f"{self.prefix}{env_key}_LIFETIME", "singleton")
            enabled = os.getenv(f"{self.prefix}{env_key}_ENABLED", "true").lower() == "true"
            
            if enabled:
                try:
                    lifetime = ServiceLifetime(lifetime_str.lower())
                except ValueError:
                    lifetime = ServiceLifetime.SINGLETON
                
                service_registration = ServiceRegistrationInfo(
                    service_type=service_type,
                    implementation_type=implementation,
                    factory_type=factory_type,
                    lifetime=lifetime,
                    implementation_strategy=ServiceImplementationStrategy.FACTORY_BASED,
                    enabled=enabled
                )
                
                env_config.services.append(service_registration)


class ServiceConfigurationBuilder:
    """
    Builder for creating service configurations from multiple sources.
    
    Supports loading configurations from files, environment variables,
    and programmatic registration. Provides validation and conflict resolution.
    """
    
    def __init__(self):
        self._providers: List[IServiceConfigurationProvider] = []
        self._service_registrations: List[ServiceRegistrationInfo] = []
        self._environment_overrides: Dict[str, Dict[str, Any]] = {}
        self._validation_enabled = True
    
    def from_file(self, config_path: Union[str, Path], format: str = "auto") -> 'ServiceConfigurationBuilder':
        """
        Add a file configuration provider.
        
        Args:
            config_path: Path to configuration file
            format: File format ("yaml", "json", or "auto")
            
        Returns:
            Self for method chaining
        """
        provider = FileServiceConfigurationProvider(config_path, format)
        self._providers.append(provider)
        return self
    
    def from_environment(self, prefix: str = "PLEXCACHEULTRA_SERVICE_",
                        environment_provider: Optional[EnvironmentConfig] = None) -> 'ServiceConfigurationBuilder':
        """
        Add an environment variable configuration provider.
        
        Args:
            prefix: Prefix for environment variable names
            environment_provider: Optional environment configuration provider
            
        Returns:
            Self for method chaining
        """
        provider = EnvironmentServiceConfigurationProvider(prefix, environment_provider)
        self._providers.append(provider)
        return self
    
    def register_service(self, service_type: Type, implementation_type: Optional[Type] = None,
                        factory_type: Optional[Type] = None, factory_method: str = "create",
                        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
                        dependencies: Optional[List[str]] = None,
                        environment_conditions: Optional[Dict[str, Any]] = None,
                        enabled: bool = True, priority: int = 0) -> 'ServiceConfigurationBuilder':
        """
        Register a service programmatically.
        
        Args:
            service_type: Service interface type
            implementation_type: Implementation type (optional for factories)
            factory_type: Factory type (optional)
            factory_method: Factory method name
            lifetime: Service lifetime
            dependencies: List of dependency service names
            environment_conditions: Conditions for environment-specific registration
            enabled: Whether the service is enabled
            priority: Priority for conflict resolution
            
        Returns:
            Self for method chaining
        """
        strategy = ServiceImplementationStrategy.TYPE_BASED
        if factory_type:
            strategy = ServiceImplementationStrategy.FACTORY_BASED
        
        registration = ServiceRegistrationInfo(
            service_type=service_type.__name__,
            implementation_type=implementation_type.__name__ if implementation_type else None,
            factory_type=factory_type.__name__ if factory_type else None,
            factory_method=factory_method,
            lifetime=lifetime,
            dependencies=dependencies or [],
            implementation_strategy=strategy,
            environment_conditions=environment_conditions or {},
            enabled=enabled,
            priority=priority
        )
        
        self._service_registrations.append(registration)
        return self
    
    def set_environment_override(self, environment: str, key: str, value: Any) -> 'ServiceConfigurationBuilder':
        """
        Set an environment-specific configuration override.
        
        Args:
            environment: Environment name
            key: Configuration key
            value: Configuration value
            
        Returns:
            Self for method chaining
        """
        if environment not in self._environment_overrides:
            self._environment_overrides[environment] = {}
        self._environment_overrides[environment][key] = value
        return self
    
    def disable_validation(self) -> 'ServiceConfigurationBuilder':
        """
        Disable configuration validation.
        
        Returns:
            Self for method chaining
        """
        self._validation_enabled = False
        return self
    
    def build_configuration(self) -> ServiceConfiguration:
        """
        Build the final service configuration from all providers.
        
        Returns:
            Merged ServiceConfiguration
            
        Raises:
            ConfigurationError: When configuration building fails
        """
        # Load configurations from all providers
        configurations = []
        for provider in self._providers:
            try:
                config = provider.load_configuration()
                configurations.append(config)
            except Exception as e:
                logger.error("Failed to load configuration from provider %s: %s", 
                           type(provider).__name__, str(e))
                if self._validation_enabled:
                    raise
        
        # Merge configurations
        merged_config = self._merge_configurations(configurations)
        
        # Add programmatic registrations
        if self._service_registrations:
            merged_config.global_services.extend(self._service_registrations)
        
        # Apply environment overrides
        self._apply_environment_overrides(merged_config)
        
        # Validate final configuration
        if self._validation_enabled:
            validation_errors = self._validate_merged_configuration(merged_config)
            if validation_errors:
                raise ConfigurationError(f"Configuration validation failed: {'; '.join(validation_errors)}")
        
        return merged_config
    
    def build_container(self, config_provider: Optional[ConfigProvider] = None) -> DIContainer:
        """
        Build a configured DI container.
        
        Args:
            config_provider: Optional configuration provider for service factories
            
        Returns:
            Configured DIContainer instance
            
        Raises:
            ConfigurationError: When container building fails
        """
        configuration = self.build_configuration()
        return self._build_container_from_configuration(configuration, config_provider)
    
    def _merge_configurations(self, configurations: List[ServiceConfiguration]) -> ServiceConfiguration:
        """Merge multiple configurations into one."""
        if not configurations:
            return ServiceConfiguration()
        
        if len(configurations) == 1:
            return configurations[0]
        
        # Use first configuration as base
        merged = configurations[0].copy(deep=True)
        
        # Merge with subsequent configurations
        for config in configurations[1:]:
            # Merge environments
            for env_name, env_config in config.environments.items():
                if env_name in merged.environments:
                    # Merge services, prioritizing higher priority registrations
                    existing_services = {s.service_type: s for s in merged.environments[env_name].services}
                    
                    for service in env_config.services:
                        if (service.service_type not in existing_services or 
                            service.priority > existing_services[service.service_type].priority):
                            existing_services[service.service_type] = service
                    
                    merged.environments[env_name].services = list(existing_services.values())
                else:
                    merged.environments[env_name] = env_config
            
            # Merge global services
            existing_global = {s.service_type: s for s in merged.global_services}
            for service in config.global_services:
                if (service.service_type not in existing_global or 
                    service.priority > existing_global[service.service_type].priority):
                    existing_global[service.service_type] = service
            
            merged.global_services = list(existing_global.values())
        
        return merged
    
    def _apply_environment_overrides(self, config: ServiceConfiguration) -> None:
        """Apply environment-specific overrides to the configuration."""
        for env_name, overrides in self._environment_overrides.items():
            if env_name in config.environments:
                config.environments[env_name].configuration_overrides.update(overrides)
    
    def _validate_merged_configuration(self, config: ServiceConfiguration) -> List[str]:
        """Validate the merged configuration."""
        errors = []
        
        # Validate with all providers
        for provider in self._providers:
            try:
                provider_errors = provider.validate_configuration(config)
                errors.extend(provider_errors)
            except Exception as e:
                errors.append(f"Validation failed for provider {type(provider).__name__}: {str(e)}")
        
        # Additional validation for merged configuration
        errors.extend(self._validate_service_conflicts(config))
        errors.extend(self._validate_circular_dependencies(config))
        
        return errors
    
    def _validate_service_conflicts(self, config: ServiceConfiguration) -> List[str]:
        """Validate for service registration conflicts."""
        errors = []
        
        # Check for duplicate service registrations within each environment
        for env_name, env_config in config.environments.items():
            all_services = config.global_services + env_config.services
            service_counts = {}
            
            for service in all_services:
                if not service.enabled:
                    continue
                    
                service_type = service.service_type
                if service_type in service_counts:
                    service_counts[service_type] += 1
                else:
                    service_counts[service_type] = 1
            
            for service_type, count in service_counts.items():
                if count > 1:
                    errors.append(f"Environment '{env_name}' has {count} registrations for service '{service_type}'")
        
        return errors
    
    def _validate_circular_dependencies(self, config: ServiceConfiguration) -> List[str]:
        """Validate for circular dependencies in service registrations."""
        errors = []
        
        for env_name, env_config in config.environments.items():
            all_services = config.global_services + env_config.services
            enabled_services = [s for s in all_services if s.enabled]
            
            # Build dependency graph
            dependency_graph = {}
            for service in enabled_services:
                dependency_graph[service.service_type] = service.dependencies
            
            # Check for circular dependencies using DFS
            def has_circular_dependency(service_type: str, visited: set, rec_stack: set) -> bool:
                visited.add(service_type)
                rec_stack.add(service_type)
                
                for dependency in dependency_graph.get(service_type, []):
                    if dependency not in visited:
                        if has_circular_dependency(dependency, visited, rec_stack):
                            return True
                    elif dependency in rec_stack:
                        return True
                
                rec_stack.remove(service_type)
                return False
            
            visited = set()
            for service in enabled_services:
                if service.service_type not in visited:
                    if has_circular_dependency(service.service_type, visited, set()):
                        errors.append(f"Circular dependency detected in environment '{env_name}' involving service '{service.service_type}'")
        
        return errors
    
    def _build_container_from_configuration(self, config: ServiceConfiguration, 
                                          config_provider: Optional[ConfigProvider] = None) -> DIContainer:
        """Build DI container from service configuration."""
        # Determine current environment
        current_env = os.getenv('ENVIRONMENT', config.default_environment)
        if current_env not in config.environments:
            current_env = config.default_environment
        
        # Get container configuration
        container_config = config.container_config
        max_resolution_depth = container_config.get('max_resolution_depth', 50)
        
        # Create container
        container = DIContainer(max_resolution_depth=max_resolution_depth)
        
        # Get services for current environment
        env_config = config.environments.get(current_env)
        all_services = config.global_services.copy()
        if env_config:
            all_services.extend(env_config.services)
        
        # Filter enabled services
        enabled_services = [s for s in all_services if s.enabled]
        
        # Register services
        type_cache = {}  # Cache for resolved types
        
        for service_info in enabled_services:
            try:
                self._register_service_in_container(
                    container, service_info, config_provider, type_cache
                )
            except Exception as e:
                logger.error(
                    "Failed to register service '%s': %s", 
                    service_info.service_type, str(e)
                )
                if self._validation_enabled:
                    raise ServiceResolutionError(
                        service_info.service_type, 
                        f"Registration failed: {str(e)}", 
                        e
                    )
        
        logger.info(
            "Built DI container with %d services for environment '%s'",
            len(enabled_services), current_env
        )
        
        return container
    
    def _register_service_in_container(self, container: DIContainer, 
                                     service_info: ServiceRegistrationInfo,
                                     config_provider: Optional[ConfigProvider],
                                     type_cache: Dict[str, Type]) -> None:
        """Register a single service in the container."""
        # Resolve service type
        service_type = self._resolve_type(service_info.service_type, type_cache)
        
        if service_info.implementation_strategy == ServiceImplementationStrategy.TYPE_BASED:
            # Direct type registration
            implementation_type = self._resolve_type(service_info.implementation_type, type_cache)
            
            if service_info.lifetime == ServiceLifetime.SINGLETON:
                container.register_singleton(service_type, implementation_type)
            elif service_info.lifetime == ServiceLifetime.SCOPED:
                container.register_scoped(service_type, implementation_type)
            else:
                container.register_transient(service_type, implementation_type)
                
        elif service_info.implementation_strategy == ServiceImplementationStrategy.FACTORY_BASED:
            # Factory-based registration
            factory_class = self._resolve_type(service_info.factory_type, type_cache)
            
            # Create factory function
            if config_provider:
                factory_method = getattr(factory_class, service_info.factory_method)
                if callable(factory_method):
                    factory_function = factory_method(config_provider)
                else:
                    raise ServiceResolutionError(
                        service_info.service_type,
                        f"Factory method '{service_info.factory_method}' is not callable"
                    )
            else:
                # Use default factory instantiation
                factory_instance = factory_class()
                factory_function = lambda provider: factory_instance.create(provider)
            
            container.register_factory(service_type, factory_function, service_info.lifetime)
        
        else:
            raise ServiceResolutionError(
                service_info.service_type,
                f"Unsupported implementation strategy: {service_info.implementation_strategy}"
            )
    
    def _resolve_type(self, type_name: str, type_cache: Dict[str, Type]) -> Type:
        """Resolve a type name to an actual type object."""
        if type_name in type_cache:
            return type_cache[type_name]
        
        try:
            # Try to resolve as a fully qualified name
            if '.' in type_name:
                module_name, class_name = type_name.rsplit('.', 1)
                module = importlib.import_module(module_name)
                type_obj = getattr(module, class_name)
            else:
                # Try to resolve from known modules
                known_modules = [
                    'src.core.interfaces',
                    'src.core.repositories', 
                    'src.core.factories',
                    'src.core.plex_operations',
                    'src.core.file_operations',
                    'src.core.notifications',
                    'src.core.plex_cache_engine',
                    'src.config.interfaces'
                ]
                
                type_obj = None
                for module_name in known_modules:
                    try:
                        module = importlib.import_module(module_name)
                        if hasattr(module, type_name):
                            type_obj = getattr(module, type_name)
                            break
                    except ImportError:
                        continue
                
                if type_obj is None:
                    raise ImportError(f"Could not resolve type '{type_name}'")
            
            type_cache[type_name] = type_obj
            return type_obj
            
        except Exception as e:
            raise ServiceResolutionError(
                type_name,
                f"Failed to resolve type: {str(e)}",
                e
            )