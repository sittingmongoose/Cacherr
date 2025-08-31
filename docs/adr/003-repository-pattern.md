# ADR-003: Repository Pattern for Data Access

## Status
Accepted

## Context

The original Cacherr system had scattered data access logic with several critical issues:

1. **Direct file operations**: Data access was spread throughout the codebase
2. **No data consistency**: Concurrent access could lead to data corruption
3. **Poor error handling**: File I/O errors were handled inconsistently
4. **No transaction support**: Multi-step data operations could leave inconsistent state
5. **Difficult testing**: Data access was tightly coupled to file system
6. **No data validation**: Data integrity was not guaranteed
7. **Limited query capabilities**: Complex data queries required custom code
8. **No backup/recovery**: Data loss risk from file corruption or accidental deletion

The system needed a clean abstraction layer over data access that would provide consistency, validation, and robust error handling while remaining testable.

## Decision

We decided to implement the Repository Pattern with file-based persistence:

### Core Repository Pattern Implementation
- **Repository interfaces**: Clean contracts for data access operations
- **File-based storage**: JSON files for data persistence with atomic operations
- **Thread-safe operations**: File locking and atomic writes for consistency
- **Base repository class**: Common functionality shared across all repositories

### Data Models and Validation
- **Pydantic models**: Strong typing and validation for all data
- **Schema versioning**: Support for data format migration
- **Data integrity checks**: Validation and corruption detection
- **Backup and recovery**: Automatic backup creation and recovery mechanisms

### Repository Implementations
- **CacheRepository**: Manages cached file metadata and statistics
- **ConfigRepository**: Handles configuration persistence and history
- **MetricsRepository**: Stores operational metrics and analytics
- **Factory pattern**: Centralized repository creation and configuration

### Integration Features
- **DI container integration**: Repositories registered as services
- **Error handling**: Comprehensive exception hierarchy
- **Performance optimization**: Efficient querying and indexing
- **Testing support**: In-memory and mock repository implementations

## Consequences

### Positive Consequences

1. **Data Consistency**
   - Atomic file operations prevent partial writes
   - File locking prevents concurrent access issues
   - Transaction-like behavior for multi-step operations

2. **Improved Testability**
   - Repository interfaces enable easy mocking
   - In-memory implementations for unit tests
   - Isolated testing of business logic

3. **Better Error Handling**
   - Comprehensive exception hierarchy with context
   - Graceful handling of file system errors
   - Automatic recovery from corruption when possible

4. **Data Integrity**
   - Pydantic validation ensures data quality
   - Schema versioning supports data evolution
   - Backup mechanisms prevent data loss

5. **Clean Architecture**
   - Clear separation between business logic and data access
   - Repository interfaces define clean contracts
   - Easy to swap storage implementations

6. **Enhanced Querying**
   - Repository methods provide optimized queries
   - Indexing for common query patterns
   - Filtering and sorting capabilities

### Negative Consequences

1. **Increased Complexity**
   - Additional abstraction layer to understand
   - More classes and interfaces to maintain
   - Repository pattern learning curve

2. **File-based Limitations**
   - No native ACID transaction support
   - Limited concurrent access compared to databases
   - Query performance limitations for large datasets

3. **Serialization Overhead**
   - JSON serialization/deserialization cost
   - Larger memory footprint for data models
   - Type conversion overhead

4. **Backup Storage Requirements**
   - Additional disk space for backup files
   - Backup management complexity
   - Cleanup and rotation policies needed

### Performance Considerations

1. **File I/O Optimization**
   - Minimize file reads/writes through caching
   - Batch operations where possible
   - Efficient JSON parsing and generation

2. **Memory Management**
   - Lazy loading for large datasets
   - Configurable cache sizes
   - Proper disposal of resources

## Alternatives Considered

### 1. Direct File Operations (Status Quo)
- **Pros**: Simple, no abstraction overhead
- **Cons**: Scattered logic, poor error handling, difficult testing
- **Why rejected**: Existing problems were significant impediments

### 2. SQLite Database
- **Pros**: ACID transactions, SQL querying, mature ecosystem
- **Cons**: Additional dependency, complexity for simple data, file format lock-in
- **Why rejected**: Overkill for current data volumes and complexity

### 3. NoSQL Database (MongoDB, etc.)
- **Pros**: JSON-native, flexible schema, powerful querying
- **Cons**: External dependency, deployment complexity, resource requirements
- **Why rejected**: Adds deployment complexity without sufficient benefits

### 4. ORM Framework (SQLAlchemy, etc.)
- **Pros**: Mature patterns, extensive features, database portability
- **Cons**: Heavy dependency, learning curve, complexity for simple use cases
- **Why rejected**: Too much complexity for file-based storage needs

### 5. Simple Data Access Layer
- **Pros**: Lighter weight than full repository pattern
- **Cons**: Less structure, limited reusability, still tightly coupled
- **Why rejected**: Doesn't provide sufficient abstraction benefits

## Implementation Details

The repository pattern implementation includes:

### Repository Interface Hierarchy
```python
class BaseRepository(Generic[T]):
    def add(self, entity: T) -> None
    def get(self, key: str) -> Optional[T]
    def update(self, entity: T) -> None
    def delete(self, key: str) -> bool
    def list(self, filters: Dict[str, Any] = None) -> List[T]

class CacheRepository(BaseRepository[CacheEntry]):
    def get_entries_older_than(self, age: timedelta) -> List[CacheEntry]
    def get_entries_by_size(self, min_size: int, max_size: int) -> List[CacheEntry]
    def get_cache_statistics(self) -> Dict[str, Any]
```

### File-based Storage Implementation
```python
class BaseFileRepository(BaseRepository[T]):
    def __init__(self, data_file: Path, auto_backup: bool = True):
        self.data_file = data_file
        self.auto_backup = auto_backup
        self._file_lock = FileLock(f"{data_file}.lock")
    
    def _save_data(self) -> None:
        """Save data with atomic write operations"""
        with self._file_lock:
            # Atomic write with temporary file
            temp_file = self.data_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(self._serialize_data(), f, indent=2)
            temp_file.replace(self.data_file)
```

### Data Models with Validation
```python
class CacheEntry(BaseModel):
    file_path: str = Field(..., min_length=1)
    cache_path: str = Field(..., min_length=1)
    original_size: int = Field(..., ge=0)
    cached_at: datetime
    operation_type: str = Field(..., regex=r'^(move|copy)$')
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_accessed: Optional[datetime] = None
```

### Exception Hierarchy
```python
class RepositoryError(Exception): pass
class EntryNotFoundError(RepositoryError): pass
class DuplicateEntryError(RepositoryError): pass
class DataIntegrityError(RepositoryError): pass
class ValidationError(RepositoryError): pass
```

## Validation Criteria

The success of this decision is measured by:

1. **Data Consistency**: Zero data corruption incidents
2. **Error Reduction**: Significant reduction in data-related errors
3. **Test Coverage**: Improved unit test coverage for data operations
4. **Development Velocity**: Faster development of data-related features
5. **Data Recovery**: Successful recovery from backup in error scenarios

## Repository Implementations

### CacheRepository
- **Purpose**: Manage cached file metadata
- **Features**: Age-based queries, size filtering, statistics calculation
- **Storage**: `cache_data.json` with automatic backup

### ConfigRepository
- **Purpose**: Handle configuration persistence
- **Features**: Configuration history, validation, migration support
- **Storage**: `config_data.json` with versioning

### MetricsRepository
- **Purpose**: Store operational metrics
- **Features**: Time-series data, aggregation, performance metrics
- **Storage**: `metrics_data.json` with rotation

## Testing Strategy

### Unit Testing
```python
def test_cache_repository_add_entry(test_cache_repository):
    entry = CacheEntry(
        file_path="/test/movie.mkv",
        cache_path="/cache/movie.mkv",
        original_size=1000000,
        cached_at=datetime.now(),
        operation_type="move"
    )
    
    test_cache_repository.add_cache_entry(entry)
    retrieved = test_cache_repository.get_cache_entry("/test/movie.mkv")
    
    assert retrieved is not None
    assert retrieved.file_path == entry.file_path
```

### Integration Testing
```python
def test_repository_factory_integration(configured_container):
    factory = configured_container.resolve(RepositoryFactory)
    cache_repo = factory.create_cache_repository()
    
    assert isinstance(cache_repo, CacheFileRepository)
    assert cache_repo.data_file.exists()
```

## Future Considerations

1. **Database Migration Path**: Repository pattern enables future database adoption
2. **Distributed Storage**: Could support distributed file storage
3. **Advanced Querying**: Add more sophisticated query capabilities
4. **Data Analytics**: Enhanced metrics and analytics repositories
5. **Schema Evolution**: Improve data migration and versioning support

This ADR establishes a robust data access layer that provides consistency, validation, and abstraction while maintaining the simplicity of file-based storage for the current requirements.