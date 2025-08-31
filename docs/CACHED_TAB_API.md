# Cached Tab API Documentation

## Overview

The Cached Tab provides comprehensive tracking and management of cached files in Cacherr. This feature enables users to monitor what files are currently cached, understand why they were cached, track user attribution, and manage cache operations.

## Features

- **Real-time Cache Monitoring**: Live view of cached files with automatic updates
- **Multi-user Attribution**: Track which users triggered caching operations
- **Operation Context**: Understand why files were cached (watchlist, Trakt, continue watching, etc.)
- **Advanced Filtering**: Search and filter cached files by various criteria
- **Cache Statistics**: Comprehensive statistics about cache usage and efficiency
- **Export Capabilities**: Export cache data in multiple formats (CSV, JSON, TXT)
- **Cleanup Operations**: Automated cleanup of orphaned cache entries

## Backend Architecture

### Data Models (Pydantic v2.5)

#### CachedFileInfo
```python
class CachedFileInfo(BaseModel):
    id: str                                 # Unique identifier
    file_path: str                         # Original file path
    filename: str                          # File name
    original_path: str                     # Original location before caching  
    cached_path: str                       # Current cached location
    cache_method: str                      # Method used (symlink, copy, etc.)
    file_size_bytes: int                   # File size in bytes
    file_size_readable: str                # Human-readable size
    cached_at: datetime                    # When cached
    last_accessed: Optional[datetime]      # Last access time
    access_count: int                      # Access count
    triggered_by_user: Optional[str]       # Primary user who triggered
    triggered_by_operation: str            # Operation type
    status: str                           # Current status
    users: List[str]                      # All associated users
    metadata: Optional[Dict[str, Any]]     # Additional metadata
```

#### CacheStatistics
```python
class CacheStatistics(BaseModel):
    total_files: int                       # Total cached files
    total_size_bytes: int                  # Total cache size in bytes
    total_size_readable: str               # Human-readable total size
    active_files: int                      # Number of active files
    orphaned_files: int                    # Number of orphaned files
    users_count: int                       # Number of unique users
    oldest_cached_at: Optional[datetime]   # Oldest cache timestamp
    most_accessed_file: Optional[str]      # Most accessed file path
    cache_hit_ratio: float                 # Cache efficiency ratio
```

#### CachedFilesFilter
```python
class CachedFilesFilter(BaseModel):
    search: Optional[str]                  # Search term
    user_id: Optional[str]                 # Filter by user
    status: Optional[str]                  # Filter by status
    triggered_by_operation: Optional[str]  # Filter by operation
    size_min: Optional[int]                # Minimum file size
    size_max: Optional[int]                # Maximum file size
    cached_since: Optional[datetime]       # Date filter
    limit: int = 50                        # Result limit (1-500)
    offset: int = 0                        # Pagination offset
```

### Database Schema

#### cached_files Table
```sql
CREATE TABLE cached_files (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    original_path TEXT NOT NULL,
    cached_path TEXT NOT NULL,
    cache_method TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_size_readable TEXT NOT NULL,
    cached_at TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    triggered_by_user TEXT,
    triggered_by_operation TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### cached_file_users Table (Junction)
```sql
CREATE TABLE cached_file_users (
    cached_file_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    attribution_reason TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(cached_file_id, user_id),
    FOREIGN KEY(cached_file_id) REFERENCES cached_files(id) ON DELETE CASCADE
);
```

#### cache_operations_log Table
```sql
CREATE TABLE cache_operations_log (
    id TEXT PRIMARY KEY,
    operation_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    triggered_by TEXT NOT NULL,
    triggered_by_user TEXT,
    reason TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    metadata TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### GET /api/cached/files

Get cached files with filtering and pagination.

**Query Parameters:**
- `search` (string): Search term for filename/path filtering
- `user_id` (string): Filter by user ID who triggered caching
- `status` (string): Filter by file status (active, orphaned, pending_removal, removed)
- `triggered_by_operation` (string): Filter by operation type
- `size_min` (integer): Minimum file size in bytes
- `size_max` (integer): Maximum file size in bytes
- `cached_since` (ISO datetime): Only files cached since this date
- `limit` (integer): Maximum results to return (1-500, default 50)
- `offset` (integer): Offset for pagination (default 0)

**Response:**
```json
{
    "success": true,
    "data": {
        "files": [
            {
                "id": "uuid",
                "file_path": "/path/to/file.mkv",
                "filename": "file.mkv",
                "original_path": "/media/file.mkv",
                "cached_path": "/cache/file.mkv",
                "cache_method": "atomic_symlink",
                "file_size_bytes": 1073741824,
                "file_size_readable": "1.0 GB",
                "cached_at": "2023-12-01T10:30:00Z",
                "last_accessed": "2023-12-01T15:45:00Z",
                "access_count": 5,
                "triggered_by_user": "user1",
                "triggered_by_operation": "watchlist",
                "status": "active",
                "users": ["user1", "user2"],
                "metadata": {}
            }
        ],
        "pagination": {
            "limit": 50,
            "offset": 0,
            "total_count": 100,
            "has_more": true
        },
        "filter_applied": {
            "user_id": "user1",
            "limit": 50,
            "offset": 0
        }
    }
}
```

### DELETE /api/cached/files/{file_id}

Remove a specific file from cache tracking.

**Request Body:**
```json
{
    "reason": "manual_cleanup",
    "user_id": "user1"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Cached file removed successfully: file.mkv",
    "data": {
        "file_id": "uuid",
        "file_path": "/path/to/file.mkv",
        "reason": "manual_cleanup"
    }
}
```

### GET /api/cached/statistics

Get comprehensive cache statistics.

**Response:**
```json
{
    "success": true,
    "data": {
        "total_files": 150,
        "total_size_bytes": 107374182400,
        "total_size_readable": "100.0 GB",
        "active_files": 145,
        "orphaned_files": 5,
        "users_count": 3,
        "oldest_cached_at": "2023-11-01T08:00:00Z",
        "most_accessed_file": "/cache/popular_movie.mkv",
        "cache_hit_ratio": 0.85
    }
}
```

### GET /api/cached/users/{user_id}/stats

Get cache statistics for a specific user.

**Query Parameters:**
- `days` (integer): Number of days to include in statistics (default: 30)

**Response:**
```json
{
    "success": true,
    "data": {
        "user_id": "user1",
        "period_days": 30,
        "total_files": 45,
        "active_files": 42,
        "total_size_bytes": 21474836480,
        "total_size_readable": "20.0 GB",
        "most_common_operation": "watchlist",
        "recent_files": [
            {
                "filename": "recent_movie.mkv",
                "cached_at": "2023-12-01T10:30:00Z",
                "file_size_readable": "2.5 GB",
                "operation": "watchlist"
            }
        ]
    }
}
```

### POST /api/cached/cleanup

Clean up orphaned cached files.

**Request Body:**
```json
{
    "remove_orphaned": false,
    "user_id": "admin"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Cache cleanup completed. 3 files marked as orphaned.",
    "data": {
        "orphaned_count": 3,
        "removed_count": 0,
        "remove_orphaned": false
    }
}
```

### GET /api/cached/files/search

Advanced search for cached files.

**Query Parameters:**
- `q` (string): Search query (required)
- `type` (string): Search type (filename, path, user, operation, all)
- `limit` (integer): Maximum results (default: 50)
- `include_removed` (boolean): Include removed files (default: false)

**Response:**
```json
{
    "success": true,
    "data": {
        "query": "movie",
        "search_type": "filename",
        "results": [...],
        "total_found": 25,
        "limited_to": 50
    }
}
```

### GET /api/cached/export

Export cached files data as downloadable file.

**Query Parameters:**
- `format` (string): Export format (csv, json, txt) - default: csv
- `user_id` (string): Filter by user ID (optional)
- `status` (string): Filter by status (optional)
- `include_metadata` (boolean): Include metadata (default: false)

**Response:** Downloadable file with cached files data

## WebSocket Events

### Real-time Updates

The Cached tab supports real-time updates through WebSocket events:

#### cache_file_added
```json
{
    "type": "cache_file_added",
    "data": {
        "file_path": "/path/to/file.mkv",
        "action": "added",
        "user_id": "user1",
        "reason": "watchlist",
        "file_info": { ... }
    },
    "timestamp": "2023-12-01T10:30:00Z"
}
```

#### cache_file_removed
```json
{
    "type": "cache_file_removed",
    "data": {
        "file_path": "/path/to/file.mkv",
        "action": "removed",
        "user_id": "user1",
        "reason": "manual_cleanup"
    },
    "timestamp": "2023-12-01T10:30:00Z"
}
```

#### cache_statistics_updated
```json
{
    "type": "cache_statistics_updated",
    "data": {
        "total_files": 150,
        "total_size_bytes": 107374182400,
        "total_size_readable": "100.0 GB",
        "active_files": 145,
        "orphaned_files": 5
    },
    "timestamp": "2023-12-01T10:30:00Z"
}
```

## Status Values

### File Status
- `active`: File is currently cached and accessible
- `orphaned`: Cached file no longer exists on disk
- `pending_removal`: File marked for removal
- `removed`: File has been removed from cache

### Operation Types
- `watchlist`: Cached due to user's watchlist
- `ondeck`: Cached from on deck/continue watching
- `trakt`: Cached from Trakt.tv integration
- `manual`: Manually cached by user
- `continue_watching`: Cached from continue watching
- `real_time_watch`: Cached during real-time watching
- `active_watching`: Cached while actively being watched by Plex (copy-only)

### Cache Methods
- `atomic_copy`: Atomic copy operation (DEFAULT for all operations)
- `atomic_symlink`: Atomic symbolic link replacement (AVAILABLE for move mode)
- `symlink`: Standard symbolic link (LEGACY - auto-upgraded to atomic_symlink)
- `copy`: Full file copy (LEGACY - auto-upgraded to atomic_copy)
- `hardlink`: Hard link to cached file (LEGACY - rarely used)

## Error Handling

All endpoints follow the standard Cacherr API response format:

**Success Response:**
```json
{
    "success": true,
    "message": "Operation completed successfully",
    "data": { ... },
    "timestamp": "2023-12-01T10:30:00Z"
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "Error message describing what went wrong",
    "timestamp": "2023-12-01T10:30:00Z"
}
```

## Integration Points

### Atomic Redirection Integration

The cached files service integrates with Cacherr's atomic redirection system, which prevents Plex playback interruption:

**Atomic Operations Process:**
1. **Copy to Cache**: File is copied to cache destination (preserves original during access)
2. **Create Temp Symlink**: Temporary symlink created in same directory as original
3. **Atomic Replace**: Original file atomically replaced with symlink to cache
4. **Zero Interruption**: Plex seamlessly switches to reading from fast cache

**Integration Point in File Operations:**
```python
# In file_operations.py - after successful atomic caching
if success and hasattr(self.config, 'cached_files_service'):
    try:
        # Default to atomic_copy (copy mode is default)
        cache_method = 'atomic_copy'
        
        # Use atomic_symlink only if move mode explicitly enabled for non-active operations
        if (not config.copy_mode and 
            operation_reason not in ('active_watching', 'real_time_watch')):
            cache_method = 'atomic_symlink'
            
        self.config.cached_files_service.add_cached_file(
            file_path=src_str,
            original_path=src_str,
            cached_path=dest_str,
            cache_method=cache_method,
            user_context=getattr(self, '_current_user_context', None),
            operation_reason=getattr(self, '_current_operation_reason', 'cache_operation')
        )
    except Exception as e:
        self.logger.warning(f"Failed to add cache tracking: {e}")
```

**Cache Method Determination:**
- **Copy mode (DEFAULT)**: `atomic_copy` for all operations (trakt, watchlist, continue watching)
- **Move mode (AVAILABLE)**: `atomic_symlink` for non-active files (trakt, watchlist, continue watching)  
- **Active watching files**: `atomic_copy` ONLY (cannot interrupt active Plex playback)
- **ALL operations use atomic redirection** - no legacy move/copy operations
- **Automatic atomic upgrade**: Legacy `copy`→`atomic_copy`, `symlink`→`atomic_symlink`

**Active Plex Watching Constraints:**
When files are actively being watched by Plex users:
1. **Copy-Only Operations**: Files cannot be moved as they're actively in use
2. **Zero Plex Awareness**: Plex must remain completely unaware of caching operations
3. **Atomic Copy Required**: `atomic_copy` ensures no interruption to active streams
4. **Background Operation**: Caching happens transparently while users continue watching
5. **No File Locks**: Operations must work around existing file handles and locks

**Operation Modes and Atomic Redirection:**

**Copy Mode (DEFAULT for all operations):**
- **Method**: `atomic_copy` - Creates cache copy while preserving original
- **Use Cases**: All operations (trakt, watchlist, continue watching, active watching)
- **Benefits**: Zero risk, original files remain untouched, works with active files
- **Process**: File copied to cache → atomic symlink replaces original → seamless redirection

**Move Mode (AVAILABLE for inactive files only):**
- **Method**: `atomic_symlink` - Moves file to cache with atomic replacement
- **Use Cases**: trakt, watchlist, continue watching (NOT active watching)
- **Benefits**: Space efficient, faster operation, no file duplication
- **Process**: File moved to cache → atomic symlink replaces original → seamless redirection

**Active Watching Constraints:**
- **Method**: `atomic_copy` ONLY (move would interrupt active streams)
- **Reason**: Cannot move files that are actively being read by Plex
- **Process**: Background copy to cache → future access redirected → zero interruption
- **File Handle Safety**: Original file remains untouched during active playback

### Dependency Injection

The cached files service is registered in the DI container:

```python
# In container configuration
container.register(
    'cached_files_service',
    CachedFilesService,
    database_path=config.database_path
)
```

## Performance Considerations

### Database Indexes
- `idx_cached_files_status`: Index on status column for filtering
- `idx_cached_files_user`: Index on triggered_by_user for user queries
- `idx_cached_files_cached_at`: Index on cached_at for date filtering
- `idx_cache_log_timestamp`: Index on timestamp for log queries

### Query Optimization
- Pagination limits prevent large result sets
- Filtering is performed at the database level
- Date range queries use indexes for efficiency

### Memory Management
- Results are streamed for large exports
- WebSocket events are batched to prevent flooding
- Database connections are properly managed with context managers

## Security Considerations

### Input Validation
- All input parameters validated with Pydantic v2.5
- SQL injection prevention through parameterized queries
- File path validation to prevent directory traversal

### Access Control
- User context tracking for audit trails
- Operation logging for security monitoring
- Export functionality includes appropriate headers

### Data Privacy
- Metadata fields can contain sensitive information - handle appropriately
- User attribution respects privacy settings
- Export functionality should be restricted to authorized users

## Future Enhancements

### Planned Features
- Cache analytics and trending reports
- Automated cache optimization recommendations
- Integration with Plex analytics for smarter caching
- Cache warming based on user patterns
- Predictive caching using machine learning

### Scalability Improvements
- Database partitioning for large cache datasets
- Redis caching for frequently accessed statistics
- Asynchronous processing for large cleanup operations
- Batch operations for bulk cache management

This documentation provides comprehensive coverage of the Cached Tab API implementation using Pydantic v2.5 and modern Flask patterns.