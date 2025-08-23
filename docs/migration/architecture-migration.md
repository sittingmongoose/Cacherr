# PlexCacheUltra Architecture Migration Guide

This guide provides comprehensive instructions for developers working with the new PlexCacheUltra architecture after the major refactoring completed in phases 1-6 of the architectural improvement project.

## Table of Contents
- [Migration Overview](#migration-overview)
- [Key Changes Summary](#key-changes-summary)
- [Development Environment Setup](#development-environment-setup)
- [Code Migration Patterns](#code-migration-patterns)
- [Testing Strategy Changes](#testing-strategy-changes)
- [Deployment Changes](#deployment-changes)
- [Common Migration Issues](#common-migration-issues)
- [Backward Compatibility](#backward-compatibility)

## Migration Overview

The PlexCacheUltra project has undergone a comprehensive architectural refactoring that transforms it from a monolithic structure to a modern, modular architecture based on proven design patterns. This migration affects all aspects of the codebase and development workflow.

### What Changed
- **Monolithic `main.py`** → **Modular application structure**
- **Direct dependencies** → **Dependency injection container**
- **Direct operations** → **Command pattern implementation**
- **Direct data access** → **Repository pattern abstraction**
- **Hard-coded configuration** → **Environment-aware configuration management**

### Migration Timeline
This migration was completed through six phases:
1. **Phase 1**: Interface extraction and service contracts
2. **Phase 2**: Dependency injection container implementation
3. **Phase 3**: Application modularization (web/scheduler separation)
4. **Phase 4**: Command pattern implementation
5. **Phase 5**: Repository pattern implementation
6. **Phase 6**: Configuration management overhaul

## Key Changes Summary

### 1. Project Structure Changes

**Before:**
```
src/
├── main.py              # 900+ line monolithic file
├── config.py           # Simple configuration
├── plex_operations.py  # Direct operations
└── utils/              # Utility functions
```

**After:**
```
src/
├── application.py                    # Application bootstrap
├── config/                          # Configuration management
│   ├── __init__.py
│   ├── settings.py
│   ├── factory.py
│   ├── validators.py
│   └── migrations.py
├── core/                           # Core services and DI
│   ├── __init__.py
│   ├── container.py               # DI container
│   ├── interfaces.py              # Service interfaces
│   ├── commands/                  # Command pattern
│   └── ...
├── repositories/                   # Data access layer
│   ├── __init__.py
│   ├── cache_repository.py
│   ├── config_repository.py
│   └── ...
├── web/                           # Web application
│   ├── __init__.py
│   ├── app.py                    # Flask factory
│   ├── routes/
│   └── middleware/
└── scheduler/                     # Background tasks
    ├── __init__.py
    ├── task_scheduler.py
    └── tasks/
```

### 2. Application Startup Changes

**Before:**
```python
# Old monolithic startup
if __name__ == "__main__":
    # Initialize everything in main.py
    config = load_config()
    app = Flask(__name__)
    # ... 900+ lines of setup
```

**After:**
```python
# New modular startup
from src.application import create_application

# Development
app_context = create_development_application()
app_context.start()

# Production
app_context = create_production_application()
app_context.start()

# Testing
app_context = create_test_application()
```

### 3. Service Access Changes

**Before:**
```python
# Direct service access
from src.plex_operations import PlexService
from src.file_utils import FileService

plex_service = PlexService(config)
file_service = FileService()
```

**After:**
```python
# Dependency injection
from src.core.interfaces import MediaService, FileService

# Through application context
media_service = app_context.get_service(MediaService)
file_service = app_context.get_service(FileService)

# Through DI container
container = app_context.container
media_service = container.resolve(MediaService)
```

### 4. Configuration Access Changes

**Before:**
```python
# Direct config access
from src.config import Config

config = Config()
cache_dir = config.CACHE_DIR
```

**After:**
```python
# Through dependency injection
from src.config.settings import Config

config = app_context.get_service(Config)
cache_dir = config.cache_directory

# Or with automatic path resolution
cache_dir = config.get_cache_directory()  # Environment-aware
```

## Development Environment Setup

### Prerequisites
Ensure you have the new development dependencies:

```bash
pip install -r requirements.txt
```

Key new dependencies:
- `pydantic>=1.8.0` - Data validation and serialization
- `pytest>=6.0.0` - Enhanced testing framework
- `pytest-asyncio` - Async testing support

### IDE Configuration
Update your IDE/editor configuration:

1. **Python Path**: Ensure `src/` is in your Python path
2. **Type Checking**: Enable type checking for better development experience
3. **Import Resolution**: Update import resolution for new module structure

### Environment Variables
New environment variables for enhanced configuration:

```bash
# Environment detection (optional - auto-detected)
PLEXCACHE_ENVIRONMENT=development|production|test|docker

# Override default paths (optional)
PLEXCACHE_CONFIG_DIR=/custom/config
PLEXCACHE_DATA_DIR=/custom/data

# Enable debug features
PLEXCACHE_DEBUG=true
```

## Code Migration Patterns

### 1. Service Registration Pattern

**New Pattern - Register Services:**
```python
from src.core.container import DIContainer, ServiceLifetime
from src.core.interfaces import MediaService
from src.implementations.plex_media_service import PlexMediaService

# Register services in container
container = DIContainer()
container.register_singleton(MediaService, PlexMediaService)
```

### 2. Service Resolution Pattern

**New Pattern - Resolve Dependencies:**
```python
# In service classes, use constructor injection
class CacheOperationService:
    def __init__(self, 
                 media_service: MediaService,
                 file_service: FileService,
                 cache_repository: CacheRepository):
        self.media_service = media_service
        self.file_service = file_service
        self.cache_repository = cache_repository
```

### 3. Command Pattern Implementation

**Replace Direct Operations:**
```python
# OLD: Direct operation
def move_file_to_cache(file_path, cache_path):
    shutil.move(file_path, cache_path)
    update_database(file_path, cache_path)

# NEW: Command pattern
from src.core.commands.cache_commands import MoveFileCommand

command = MoveFileCommand(
    source_path=file_path,
    destination_path=cache_path,
    operation_type="move_to_cache"
)

result = command_service.execute_command(command)
if result.success:
    print(f"File moved successfully: {result.message}")
```

### 4. Repository Pattern Usage

**Replace Direct Data Access:**
```python
# OLD: Direct file/database access
def save_cache_entry(file_path, cache_info):
    with open("cache_data.json", "w") as f:
        json.dump(data, f)

# NEW: Repository pattern
from src.core.repositories import CacheEntry

entry = CacheEntry(
    file_path=file_path,
    cache_path=cache_info["path"],
    original_size=cache_info["size"],
    cached_at=datetime.now(),
    operation_type="move"
)

cache_repository.add_cache_entry(entry)
```

### 5. Configuration Pattern

**Replace Direct Configuration:**
```python
# OLD: Hard-coded paths and settings
CACHE_DIR = "/cache"
ARRAY_DIR = "/array"

# NEW: Environment-aware configuration
config = container.resolve(Config)
cache_dir = config.get_cache_directory()  # Auto-detects environment
array_dir = config.get_array_directory()
```

## Testing Strategy Changes

### 1. New Test Structure

**Test Directory Organization:**
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── core/               # Core service tests
│   ├── repositories/       # Repository tests
│   ├── web/               # Web layer tests
│   └── config/            # Configuration tests
├── integration/           # Integration tests
│   ├── test_application.py
│   ├── test_service_interactions.py
│   └── test_command_system.py
├── mocks/                 # Mock implementations
│   ├── service_mocks.py
│   └── repository_mocks.py
└── fixtures/              # Test data and fixtures
```

### 2. Testing with Dependency Injection

**New Test Patterns:**
```python
import pytest
from src.core.container import DIContainer

@pytest.fixture
def container_with_mocks():
    container = DIContainer()
    container.register_instance(MediaService, MockMediaService())
    container.register_instance(FileService, MockFileService())
    return container

def test_cache_operation(container_with_mocks):
    service = container_with_mocks.resolve(CacheOperationService)
    result = service.cache_file("/test/file.mkv")
    assert result.success
```

### 3. Integration Testing

**New Integration Test Approach:**
```python
from src.application import create_test_application

def test_full_application_workflow():
    with create_test_application().application_scope() as app:
        # Test complete workflows through the application
        cache_service = app.get_service(CacheService)
        result = cache_service.cache_file("/test/movie.mkv")
        assert result.success
```

## Deployment Changes

### 1. Docker Configuration

**Updated Docker Startup:**
The existing Docker configuration continues to work, but now uses the new application bootstrap internally.

**Environment Variables:**
```dockerfile
ENV PLEXCACHE_ENVIRONMENT=docker
ENV PYTHONPATH=/app/src
```

### 2. Health Checks

**Enhanced Health Endpoints:**
```
GET /health          # Basic health check
GET /health/detailed # Detailed component status
GET /health/ready    # Readiness probe
```

### 3. Configuration Management

**New Configuration Approach:**
- Automatic environment detection
- Path resolution based on deployment environment
- Configuration validation on startup
- Migration support for configuration changes

## Common Migration Issues

### 1. Import Errors

**Problem:** Module import errors after restructuring
```python
# This will fail
from src.main import SomeFunction
```

**Solution:** Update imports to new module structure
```python
# Use new module structure
from src.core.interfaces import MediaService
from src.application import create_application
```

### 2. Service Access Patterns

**Problem:** Direct service instantiation
```python
# This pattern won't work with DI
service = MediaService()
```

**Solution:** Use dependency injection
```python
# Resolve through container
service = container.resolve(MediaService)

# Or in class constructors
class MyService:
    def __init__(self, media_service: MediaService):
        self.media_service = media_service
```

### 3. Configuration Path Issues

**Problem:** Hard-coded paths not working in different environments
```python
# This won't work across environments
cache_path = "/cache/movie.mkv"
```

**Solution:** Use configuration system
```python
config = container.resolve(Config)
cache_path = config.get_cache_path("movie.mkv")
```

### 4. Testing Issues

**Problem:** Tests failing due to missing dependencies
```python
# This will fail without proper setup
def test_service():
    service = CacheService()  # Missing dependencies
```

**Solution:** Use dependency injection in tests
```python
def test_service(configured_container):
    service = configured_container.resolve(CacheService)
    # Test with proper dependencies
```

## Backward Compatibility

### 1. API Compatibility

The REST API endpoints remain backward compatible. All existing endpoints continue to function with the same request/response formats.

### 2. Configuration Files

Existing configuration files are automatically migrated to the new format on first startup. The migration process:

1. Detects old configuration format
2. Creates backup of existing configuration
3. Migrates settings to new structure
4. Validates migrated configuration
5. Saves new configuration format

### 3. Data Files

Existing data files (cache metadata, etc.) are automatically migrated to the new repository format:

- Cache data is preserved and enhanced with new metadata
- Statistics and metrics are recalculated
- File integrity is validated during migration

### 4. Docker Compatibility

All existing Docker configurations continue to work without changes:
- Same environment variables supported
- Same volume mounts work
- Same port configurations
- Health checks enhanced but backward compatible

## Migration Checklist

### For Developers

- [ ] Update development environment with new dependencies
- [ ] Update import statements for new module structure
- [ ] Convert direct service access to dependency injection
- [ ] Update test files to use new testing patterns
- [ ] Review and update any custom extensions or integrations
- [ ] Test application startup and shutdown processes
- [ ] Validate configuration loading in your environment

### For Operations/Deployment

- [ ] Review and update deployment scripts if needed
- [ ] Validate health check endpoints work as expected
- [ ] Test configuration migration process
- [ ] Verify logging outputs and formats
- [ ] Test backup and restore procedures
- [ ] Validate monitoring and alerting integration

### For Testing

- [ ] Run full test suite to validate changes
- [ ] Test integration points with external systems
- [ ] Validate performance characteristics
- [ ] Test error handling and recovery scenarios
- [ ] Verify data migration and integrity

## Getting Help

If you encounter issues during migration:

1. **Check the logs**: New structured logging provides detailed information
2. **Review test examples**: Tests demonstrate proper usage patterns
3. **Consult documentation**: Architecture documentation explains design decisions
4. **Use debug mode**: Enable debug logging for detailed troubleshooting

The new architecture provides significant improvements in maintainability, testability, and scalability while maintaining full backward compatibility for production deployments.