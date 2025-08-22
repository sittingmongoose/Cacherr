# PlexCacheUltra Interface Architecture

This document describes the foundational interfaces created for PlexCacheUltra's modular architecture refactoring.

## Overview

The interface layer provides clean contracts for dependency injection, improved testability, and modular design. These interfaces separate implementation details from business logic while maintaining backward compatibility.

## Core Service Interfaces

### MediaService (`src/core/interfaces.py`)
```python
from src.core.interfaces import MediaService
```

**Purpose**: Abstracts Plex server operations for fetching media content.

**Key Methods**:
- `fetch_ondeck_media()` - Get onDeck content from Plex
- `fetch_watchlist_media()` - Get user watchlist content
- `fetch_watched_media()` - Get watched content for cleanup
- `get_plex_connection()` - Manage Plex server connection

**Usage Example**:
```python
class PlexMediaService(MediaService):
    def __init__(self, config: Config):
        self.config = config
        self.plex = None
    
    def fetch_ondeck_media(self) -> List[str]:
        # Implementation here
        return file_paths
```

### FileService (`src/core/interfaces.py`)
```python
from src.core.interfaces import FileService
```

**Purpose**: Abstracts file system operations including moves, copies, and path processing.

**Key Methods**:
- `process_file_paths()` - Convert Plex paths to system paths
- `move_files()` - Handle concurrent file operations
- `check_available_space()` - Validate disk space
- `analyze_files_for_test_mode()` - Dry-run analysis

**Features**:
- Concurrent operations with configurable limits
- Support for move, copy, symlink, and hybrid operations
- Network vs local path optimization
- Test mode support

### NotificationService (`src/core/interfaces.py`)
```python
from src.core.interfaces import NotificationService
```

**Purpose**: Abstracts notification delivery across multiple channels.

**Key Methods**:
- `send_notification()` - Generic notification with levels
- `send_error_notification()` - Error-specific notifications
- `send_cache_operation_notification()` - Structured operation updates
- `validate_webhook_config()` - Configuration validation

**Supported Channels**:
- Discord webhooks
- Slack webhooks
- Generic webhook endpoints
- System notifications (future)

### CacheService (`src/core/interfaces.py`)
```python
from src.core.interfaces import CacheService
```

**Purpose**: Abstracts cache management and lifecycle operations.

**Key Methods**:
- `execute_cache_operation()` - Perform cache operations
- `analyze_cache_impact()` - Test mode analysis
- `get_cache_statistics()` - Usage and performance metrics
- `cleanup_cache()` - Automated cache maintenance

## Repository Interfaces

### CacheRepository (`src/core/repositories.py`)
```python
from src.core.repositories import CacheRepository, CacheEntry
```

**Purpose**: Abstracts cache metadata persistence and querying.

**Key Methods**:
- `add_cache_entry()` - Track new cached files
- `get_cache_entry()` - Retrieve file metadata
- `find_entries_by_age()` - Query for cleanup
- `get_cache_statistics()` - Aggregated cache stats

**Data Model**: `CacheEntry` with file paths, timestamps, checksums, and operation types.

### ConfigRepository (`src/core/repositories.py`)
```python
from src.core.repositories import ConfigRepository, ConfigurationItem
```

**Purpose**: Abstracts configuration persistence with audit trails.

**Key Methods**:
- `get_configuration()` - Retrieve config values
- `set_configuration()` - Store config with history
- `export_configuration()` - Backup configs
- `get_configuration_history()` - Audit trail

### MetricsRepository (`src/core/repositories.py`)
```python
from src.core.repositories import MetricsRepository, MetricsData
```

**Purpose**: Abstracts performance and usage metrics collection.

**Key Methods**:
- `record_metric()` - Store operation metrics
- `get_aggregated_metrics()` - Time-window analysis
- `record_user_activity()` - User behavior tracking
- `get_system_health_metrics()` - System performance

## Configuration Interfaces

### ConfigProvider (`src/config/interfaces.py`)
```python
from src.config.interfaces import ConfigProvider
```

**Purpose**: Abstracts configuration source (env vars, files, remote).

**Key Methods**:
- `get_string()`, `get_int()`, `get_bool()` - Typed value retrieval
- `set_value()` - Runtime configuration updates
- `reload()` - Refresh from source

### EnvironmentConfig (`src/config/interfaces.py`)
```python
from src.config.interfaces import EnvironmentConfig
```

**Purpose**: Abstracts environment detection and platform-specific settings.

**Key Methods**:
- `detect_environment()` - Docker vs bare metal detection
- `get_default_paths()` - Environment-appropriate paths
- `validate_environment_requirements()` - Prereq checks
- `get_resource_limits()` - Platform-specific limits

### PathConfiguration (`src/config/interfaces.py`)
```python
from src.config.interfaces import PathConfiguration
```

**Purpose**: Abstracts path validation and filesystem operations.

**Key Methods**:
- `validate_path()` - Check path accessibility
- `normalize_path()` - Platform-specific normalization
- `is_network_path()` - Network share detection
- `get_available_space()` - Disk space queries

## Type Safety Models

### Pydantic Models for Type Safety
```python
from src.core.interfaces import MediaFileInfo, CacheOperationResult, TestModeAnalysis
from src.core.repositories import CacheEntry, WatchedItem, UserActivity
```

**MediaFileInfo**: File metadata with validation
**CacheOperationResult**: Operation results with success/error details
**TestModeAnalysis**: Dry-run analysis results
**CacheEntry**: Cache file tracking with metadata
**WatchedItem**: User watch history tracking
**UserActivity**: User behavior analytics

## Implementation Guidelines

### 1. Dependency Injection Pattern
```python
class CacherrEngine:
    def __init__(self, 
                 media_service: MediaService,
                 file_service: FileService,
                 notification_service: NotificationService,
                 cache_service: CacheService):
        self.media_service = media_service
        self.file_service = file_service
        # ... etc
```

### 2. Interface Implementation
```python
class PlexMediaService(MediaService):
    def __init__(self, config: Config, plex_ops: PlexOperations):
        self.config = config
        self.plex_ops = plex_ops
    
    def fetch_ondeck_media(self) -> List[str]:
        return self.plex_ops.fetch_ondeck_media()
```

### 3. Testing with Mocks
```python
class MockMediaService(MediaService):
    def __init__(self, test_data: List[str]):
        self.test_data = test_data
    
    def fetch_ondeck_media(self) -> List[str]:
        return self.test_data
```

## Benefits

1. **Type Safety**: Pydantic models ensure data validation
2. **Testability**: Easy mocking and dependency injection
3. **Modularity**: Clean separation of concerns
4. **Backward Compatibility**: Gradual migration path
5. **Extensibility**: Easy to add new implementations
6. **Documentation**: Self-documenting contracts

## Migration Strategy

### Phase 1: ✅ Extract Interfaces (Current)
- [x] Define core service interfaces
- [x] Define repository interfaces  
- [x] Define configuration interfaces
- [x] Add Pydantic models for type safety

### Phase 2: Implement Dependency Injection Container
- [ ] Create DI container for service registration
- [ ] Implement interface adapters for existing classes
- [ ] Update main engine to use DI

### Phase 3: Modular Service Implementations
- [ ] Create separate implementation modules
- [ ] Add factory patterns for service creation
- [ ] Implement configuration-driven service selection

### Phase 4: Advanced Features
- [ ] Add service decorators (caching, retry, metrics)
- [ ] Implement plugin architecture
- [ ] Add health checks and monitoring

## Usage Examples

### Basic Service Usage
```python
# Current (after Phase 2)
from src.core.interfaces import MediaService
from src.core.services import PlexMediaService

media_service: MediaService = PlexMediaService(config)
ondeck_files = media_service.fetch_ondeck_media()
```

### Repository Pattern
```python
from src.core.repositories import CacheRepository
from src.core.implementations import JsonCacheRepository

cache_repo: CacheRepository = JsonCacheRepository("/config/cache.json")
entry = cache_repo.get_cache_entry("/path/to/file.mkv")
```

### Configuration Management
```python
from src.config.interfaces import ConfigProvider
from src.config.implementations import EnvironmentConfigProvider

config: ConfigProvider = EnvironmentConfigProvider()
plex_url = config.get_string("PLEX_URL", section="plex")
```

## Error Handling

All interfaces define specific exception types for proper error handling:

```python
try:
    files = media_service.fetch_ondeck_media()
except ConnectionError:
    # Handle Plex connection issues
except MediaFetchError:
    # Handle media fetching problems
```

## Next Steps

1. **Phase 2**: Implement dependency injection container
2. **Create adapter classes** to wrap existing implementations
3. **Update tests** to use interface mocks
4. **Gradual migration** of existing code to use interfaces
5. **Add monitoring** and health checks through interfaces

The interfaces are now ready for implementation and provide a solid foundation for the modular architecture refactoring.