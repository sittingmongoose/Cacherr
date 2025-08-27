# Real-Time Plex Watching Documentation

## Overview

Real-time Plex watching provides intelligent, atomic caching of media files as users actively watch them. This feature ensures optimal streaming performance by moving frequently accessed content to faster cache storage without interrupting playback.

## How It Works

### Atomic Operations for Zero Interruption

The real-time watching system uses **atomic operations** to ensure that Plex playback is never interrupted:

1. **Copy to Cache**: When a user starts watching content, the system copies (never moves) the file to fast cache storage
2. **Create Temporary Symlink**: A temporary symlink is created in the same directory as the original file
3. **Atomic Replacement**: The original file is atomically replaced with a symlink pointing to the cached version
4. **Seamless Transition**: Plex transparently switches to reading from the fast cache without any interruption

### Safety Guarantees

- ✅ **No Playback Interruption**: Active streams continue uninterrupted during caching
- ✅ **POSIX Compliance**: Uses atomic `rename()` operations for guaranteed consistency
- ✅ **Permission Preservation**: Original file permissions and metadata are maintained
- ✅ **Docker/Unraid Compatible**: Works seamlessly with container mount points
- ✅ **Transparent to Plex**: The Plex server never knows files have been moved

## Configuration

### Basic Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `Enable Real-Time Watching` | Master toggle for the feature | `false` |
| `Check Interval` | How often to check for active sessions (seconds) | `30` |
| `Auto-Cache on Watch Start` | Cache files immediately when playback begins | `false` |
| `Cache on Watch Complete` | Cache files when playback finishes | `true` |

### Advanced Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `Remove from Cache After (hours)` | Auto-cleanup cached files after specified time | `0` (disabled) |
| `Respect Other Users' Watchlists` | Keep files cached if in other users' watchlists | `false` |
| `Exclude Inactive Users (Days)` | Ignore users inactive for this many days | `0` (disabled) |

## API Endpoints

### Get Status
```http
GET /api/watcher/status
```

Returns comprehensive status including atomic operation statistics and safety information.

### Start/Stop Watching
```http
POST /api/watcher/start
POST /api/watcher/stop
```

Control the real-time watching service.

### Clear History
```http
POST /api/watcher/clear-history
```

Clear the watch history and statistics.

## Technical Implementation

### Pydantic Models

The system uses Pydantic v2 for type-safe configuration and status reporting:

```python
class RealTimeWatchingStatus(BaseModel):
    """Real-time watching status with validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    is_running: bool = Field(default=False)
    total_operations: int = Field(default=0, ge=0)
    active_sessions: int = Field(default=0, ge=0)
    last_operation_time: Optional[float] = Field(default=None)
    cached_media_count: int = Field(default=0, ge=0)
```

### Atomic File Operations

The core atomic operation is implemented in `_create_atomic_symlink()`:

```python
def _create_atomic_symlink(self, original_path: str, cache_path: str) -> bool:
    """
    Atomically replace original file with symlink to cache.
    
    Uses temporary file + rename pattern for POSIX compliance.
    """
    # Create temporary symlink in same directory
    with tempfile.NamedTemporaryFile(dir=original_path_obj.parent, delete=False) as temp_file:
        temp_symlink_path = temp_file.name
        
    os.unlink(temp_symlink_path)  # Remove temp file, keep name
    os.symlink(cache_path, temp_symlink_path)  # Create symlink
    
    # Atomic replacement - this is the critical operation
    os.rename(temp_symlink_path, original_path)
```

## Troubleshooting

### Common Issues

**Q: Real-time watching isn't triggering**
- Check that `Enable Real-Time Watching` is enabled in settings
- Verify Plex server connectivity in the Plex settings section
- Ensure the check interval isn't too high (try 30 seconds)

**Q: Files aren't being cached**
- Confirm cache destination is set and accessible
- Check logs for permission errors
- Verify Docker volume mounts include both source and cache paths

**Q: Playback stutters during caching**
- This should never happen with atomic operations
- Check logs for error messages during caching operations
- Verify filesystem supports atomic operations (most modern filesystems do)

### Log Messages

Important log messages to watch for:

- `Real-time caching triggered for 'Movie Title' - Reason: watching_started`
- `Atomic symlink created: /path/to/original -> /cache/path`
- `Successfully cached 1/1 files for 'Movie Title'`

### Error Conditions

The system gracefully handles errors:

- **File not accessible**: Skips caching, continues monitoring
- **Cache full**: Logs error, continues with other files
- **Permission denied**: Logs error, does not retry automatically

## Docker/Unraid Considerations

### Volume Mounts

Ensure both source and cache paths are properly mounted:

```yaml
volumes:
  - /mnt/user/Media:/media
  - /mnt/cache/cacherr:/cache
```

### Permissions

The container user must have:
- Read access to source media files
- Write access to cache directory
- Ability to create symlinks in source directories

### Atomic Operations Support

Most modern filesystems support atomic operations:
- ✅ ext4, ext3, xfs, btrfs
- ✅ NTFS (Windows shares)
- ✅ ZFS, UnRAID parity arrays
- ⚠️ Some network filesystems may have limitations

## Performance Benefits

### Cache Hit Scenarios

Real-time watching provides immediate benefits for:

1. **Rewatching**: Previously watched content loads instantly from cache
2. **Family Viewing**: Multiple users watching same content
3. **Episode Binging**: Subsequent episodes already cached
4. **Popular Content**: Trending movies/shows stay in fast storage

### Storage Optimization

The system intelligently manages cache space:

- Copies only actively watched content
- Automatic cleanup of old cached files
- Respects user watchlists for retention decisions
- Preserves popular content based on viewing patterns

## Security Considerations

### File System Access

Real-time watching requires:
- Read access to media directories
- Write access to cache directory
- Symlink creation privileges in source directories

### Data Integrity

Safety measures include:
- Copy-first strategy preserves originals during active playback
- Atomic operations prevent corruption
- Metadata preservation maintains file integrity
- Error handling prevents system instability

## Development Notes

### Code Organization

- `src/core/plex_watcher.py`: Main watcher implementation
- `src/web/routes/api.py`: REST API endpoints
- `dashboard.html`: Web interface
- `src/config/settings.py`: Configuration management

### Testing Considerations

- Test mode always uses copy operations (never moves)
- Dry run mode logs operations without executing them
- Unit tests cover atomic operation edge cases
- Integration tests verify Docker mount compatibility

### Future Enhancements

Planned improvements:
- Predictive caching based on viewing patterns
- Integration with Plex server watch statistics
- Advanced cache eviction policies
- Real-time bandwidth optimization
