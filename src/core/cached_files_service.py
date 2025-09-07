"""
Cached Files Service - Comprehensive cached file tracking and management.

Provides tracking for cached files, user attribution, and operation history
using Pydantic v2.5 models and SQLite storage integration.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass

from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic import ValidationError as PydanticValidationError

try:
    from .interfaces import UserOperationContext
except ImportError:
    # Fallback for testing
    from interfaces import UserOperationContext


logger = logging.getLogger(__name__)


class CachedFileInfo(BaseModel):
    """
    Information about a cached file using Pydantic v2.5.
    
    Tracks comprehensive details about files that have been cached,
    including user attribution and operation context.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        extra='forbid'
    )
    
    id: str = Field(..., description="Unique identifier for the cached file")
    file_path: str = Field(..., description="Original file path")
    filename: str = Field(..., description="File name extracted from path")
    original_path: str = Field(..., description="Original location before caching")
    cached_path: str = Field(..., description="Current cached location")
    cache_method: str = Field(..., description="Method used for caching (symlink, copy, etc.)")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    file_size_readable: str = Field(..., description="Human-readable file size")
    cached_at: datetime = Field(..., description="When the file was cached")
    last_accessed: Optional[datetime] = Field(None, description="Last access time")
    access_count: int = Field(0, ge=0, description="Number of times accessed")
    triggered_by_user: Optional[str] = Field(None, description="Primary user who triggered caching")
    triggered_by_operation: str = Field(..., description="Operation that triggered caching")
    status: str = Field(..., description="Current status of the cached file")
    users: List[str] = Field(default_factory=list, description="All users associated with this cache")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @field_validator('cache_method')
    @classmethod
    def validate_cache_method(cls, v: str) -> str:
        allowed_methods = {'symlink', 'hardlink', 'copy', 'atomic_symlink', 'atomic_copy'}
        if v not in allowed_methods:
            raise ValueError(f'cache_method must be one of: {allowed_methods}')
        return v

    @field_validator('status')
    @classmethod 
    def validate_status(cls, v: str) -> str:
        allowed_statuses = {'active', 'orphaned', 'pending_removal', 'removed'}
        if v not in allowed_statuses:
            raise ValueError(f'status must be one of: {allowed_statuses}')
        return v

    @field_validator('triggered_by_operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        allowed_operations = {'watchlist', 'ondeck', 'trakt', 'manual', 'continue_watching', 'real_time_watch', 'active_watching'}
        if v not in allowed_operations:
            raise ValueError(f'triggered_by_operation must be one of: {allowed_operations}')
        return v


class CacheStatistics(BaseModel):
    """Current cache statistics using Pydantic v2.5."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    total_files: int = Field(..., ge=0, description="Total number of cached files")
    total_size_bytes: int = Field(..., ge=0, description="Total size in bytes")
    total_size_readable: str = Field(..., description="Human-readable total size")
    active_files: int = Field(..., ge=0, description="Number of active cached files")
    orphaned_files: int = Field(0, ge=0, description="Number of orphaned files")
    users_count: int = Field(0, ge=0, description="Number of unique users")
    oldest_cached_at: Optional[datetime] = Field(None, description="Oldest cache timestamp")
    most_accessed_file: Optional[str] = Field(None, description="Most frequently accessed file")
    cache_hit_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Cache hit ratio")
    
    
class CacheOperationLog(BaseModel):
    """Log entry for cache operations using Pydantic v2.5."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        extra='forbid'
    )
    
    id: str = Field(..., description="Unique log entry ID")
    operation_type: str = Field(..., description="Type of cache operation")
    file_path: str = Field(..., description="File path affected")
    triggered_by: str = Field(..., description="What triggered the operation")
    triggered_by_user: Optional[str] = Field(None, description="User who triggered operation")
    reason: str = Field(..., description="Reason for the operation")
    success: bool = Field(..., description="Whether operation succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional operation metadata")
    timestamp: datetime = Field(..., description="When operation occurred")

    @field_validator('operation_type')
    @classmethod
    def validate_operation_type(cls, v: str) -> str:
        allowed_types = {'cache_add', 'cache_remove', 'cache_cleanup', 'cache_access', 'cache_verify'}
        if v not in allowed_types:
            raise ValueError(f'operation_type must be one of: {allowed_types}')
        return v


class CachedFilesFilter(BaseModel):
    """Filter parameters for cached files queries using Pydantic v2.5."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    search: Optional[str] = Field(None, description="Search term for filename/path")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by status")
    triggered_by_operation: Optional[str] = Field(None, description="Filter by operation type")
    size_min: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    size_max: Optional[int] = Field(None, ge=0, description="Maximum file size in bytes")
    cached_since: Optional[datetime] = Field(None, description="Filter files cached since this date")
    limit: int = Field(50, ge=1, le=500, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class CachedFilesService:
    """
    Service for managing cached files using Pydantic v2.5 models.
    
    Provides comprehensive cached file tracking with user attribution,
    operation history, and real-time statistics.
    """
    
    def __init__(self, database_path: str):
        """Initialize the cached files service with SQLite database."""
        self.database_path = database_path
        self.logger = logger
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database with proper schema."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Cached files table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_files (
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
                )
                """)
                
                # User attribution junction table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_file_users (
                    cached_file_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    attribution_reason TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(cached_file_id, user_id),
                    FOREIGN KEY(cached_file_id) REFERENCES cached_files(id) ON DELETE CASCADE
                )
                """)
                
                # Cache operations log
                conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_operations_log (
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
                )
                """)
                
                # Create indexes for performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_status ON cached_files(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_user ON cached_files(triggered_by_user)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_cached_at ON cached_files(cached_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_log_timestamp ON cache_operations_log(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_log_user ON cache_operations_log(triggered_by_user)")
                
                conn.commit()
                self.logger.info("Cached files database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to initialize cached files database: {e}")
            raise

    def _ensure_tables_exist(self) -> None:
        """Ensure required tables and indexes exist and are usable.

        This method is referenced by the application bootstrap during
        database path probing. It verifies the presence of the schema and
        performs a lightweight sanity check. If any required table is
        missing, it (re)initializes the schema.
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")

                # Check existing tables
                rows = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                existing_tables = {r[0] for r in rows}

                required_tables = {
                    'cached_files',
                    'cached_file_users',
                    'cache_operations_log',
                }

                # Initialize schema if anything is missing
                if not required_tables.issubset(existing_tables):
                    self.logger.info("Database schema incomplete; initializing tables...")
                    self._init_database()

                # Lightweight sanity checks (will raise if tables are inaccessible)
                conn.execute("SELECT 1 FROM cached_files LIMIT 1")
                conn.execute("SELECT 1 FROM cache_operations_log LIMIT 1")

                # Ensure indexes exist (idempotent)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_status ON cached_files(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_user ON cached_files(triggered_by_user)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_cached_at ON cached_files(cached_at)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_log_timestamp ON cache_operations_log(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_log_user ON cache_operations_log(triggered_by_user)")

                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Schema verification failed: {e}")
            raise

    def add_cached_file(self, file_path: str, original_path: str, cached_path: str,
                       cache_method: str = 'atomic_symlink', user_context: Optional[UserOperationContext] = None,
                       operation_reason: str = 'manual', metadata: Optional[Dict] = None) -> CachedFileInfo:
        """Add a file to cached files tracking."""
        try:
            file_id = str(uuid.uuid4())
            filename = Path(file_path).name
            
            # Ensure atomic operations are used for all cache methods
            if cache_method == 'copy':
                cache_method = 'atomic_copy'
            elif cache_method == 'symlink':
                cache_method = 'atomic_symlink'
            
            # Force atomic_copy for active watching operations (cannot interrupt active files)
            if operation_reason in ('active_watching', 'real_time_watch'):
                cache_method = 'atomic_copy'
                self.logger.debug(f"Forced atomic_copy for active watching: {file_path}")
            
            # Get file size
            try:
                file_size_bytes = Path(cached_path).stat().st_size if Path(cached_path).exists() else 0
                file_size_readable = self._format_file_size(file_size_bytes)
            except OSError:
                file_size_bytes = 0
                file_size_readable = "0 B"
            
            cached_file = CachedFileInfo(
                id=file_id,
                file_path=file_path,
                filename=filename,
                original_path=original_path,
                cached_path=cached_path,
                cache_method=cache_method,
                file_size_bytes=file_size_bytes,
                file_size_readable=file_size_readable,
                cached_at=datetime.now(timezone.utc),
                triggered_by_user=user_context.user_id if user_context else None,
                triggered_by_operation=operation_reason,
                status='active',
                users=[user_context.user_id] if user_context and user_context.user_id else [],
                metadata=metadata
            )
            
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Insert cached file
                conn.execute("""
                    INSERT OR REPLACE INTO cached_files 
                    (id, file_path, filename, original_path, cached_path, cache_method, 
                     file_size_bytes, file_size_readable, cached_at, triggered_by_user, 
                     triggered_by_operation, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cached_file.id, cached_file.file_path, cached_file.filename,
                    cached_file.original_path, cached_file.cached_path, cached_file.cache_method,
                    cached_file.file_size_bytes, cached_file.file_size_readable,
                    cached_file.cached_at.isoformat(), cached_file.triggered_by_user,
                    cached_file.triggered_by_operation, cached_file.status,
                    json.dumps(metadata) if metadata else None
                ))
                
                # Add user attribution
                if user_context and user_context.user_id:
                    conn.execute("""
                        INSERT OR IGNORE INTO cached_file_users 
                        (cached_file_id, user_id, attribution_reason)
                        VALUES (?, ?, ?)
                    """, (file_id, user_context.user_id, operation_reason))
                
                conn.commit()
            
            # Log the operation
            self._log_operation('cache_add', file_path, 'file_service', 
                              user_context.user_id if user_context else None,
                              f'File cached via {operation_reason}', True, None, metadata)
            
            self.logger.info(f"Added cached file: {file_path}")
            return cached_file
            
        except Exception as e:
            self.logger.error(f"Failed to add cached file {file_path}: {e}")
            self._log_operation('cache_add', file_path, 'file_service',
                              user_context.user_id if user_context else None,
                              f'File caching failed: {operation_reason}', False, str(e), metadata)
            raise

    def get_cached_files(self, filter_params: Optional[CachedFilesFilter] = None) -> Tuple[List[CachedFileInfo], int]:
        """Get cached files with filtering and pagination."""
        if filter_params is None:
            filter_params = CachedFilesFilter()
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Build query
                where_clauses = []
                params = []
                
                if filter_params.search:
                    where_clauses.append("(filename LIKE ? OR file_path LIKE ?)")
                    search_term = f"%{filter_params.search}%"
                    params.extend([search_term, search_term])
                
                if filter_params.user_id:
                    where_clauses.append("triggered_by_user = ?")
                    params.append(filter_params.user_id)
                
                if filter_params.status:
                    where_clauses.append("status = ?")
                    params.append(filter_params.status)
                
                if filter_params.triggered_by_operation:
                    where_clauses.append("triggered_by_operation = ?")
                    params.append(filter_params.triggered_by_operation)
                
                if filter_params.size_min:
                    where_clauses.append("file_size_bytes >= ?")
                    params.append(filter_params.size_min)
                
                if filter_params.size_max:
                    where_clauses.append("file_size_bytes <= ?")
                    params.append(filter_params.size_max)
                
                if filter_params.cached_since:
                    where_clauses.append("cached_at >= ?")
                    params.append(filter_params.cached_since.isoformat())
                
                where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                # Count total
                count_query = f"SELECT COUNT(*) FROM cached_files {where_sql}"
                total_count = conn.execute(count_query, params).fetchone()[0]
                
                # Get paginated results
                query = f"""
                    SELECT * FROM cached_files 
                    {where_sql}
                    ORDER BY cached_at DESC 
                    LIMIT ? OFFSET ?
                """
                params.extend([filter_params.limit, filter_params.offset])
                
                rows = conn.execute(query, params).fetchall()
                
                # Convert to Pydantic models
                cached_files = []
                for row in rows:
                    # Get user attributions
                    user_rows = conn.execute("""
                        SELECT user_id FROM cached_file_users WHERE cached_file_id = ?
                    """, (row['id'],)).fetchall()
                    users = [user_row['user_id'] for user_row in user_rows]
                    
                    cached_file = CachedFileInfo(
                        id=row['id'],
                        file_path=row['file_path'],
                        filename=row['filename'],
                        original_path=row['original_path'],
                        cached_path=row['cached_path'],
                        cache_method=row['cache_method'],
                        file_size_bytes=row['file_size_bytes'],
                        file_size_readable=row['file_size_readable'],
                        cached_at=datetime.fromisoformat(row['cached_at']),
                        last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                        access_count=row['access_count'],
                        triggered_by_user=row['triggered_by_user'],
                        triggered_by_operation=row['triggered_by_operation'],
                        status=row['status'],
                        users=users,
                        metadata=json.loads(row['metadata']) if row['metadata'] else None
                    )
                    cached_files.append(cached_file)
                
                return cached_files, total_count
                
        except Exception as e:
            self.logger.error(f"Failed to get cached files: {e}")
            return [], 0

    def get_cache_statistics(self) -> CacheStatistics:
        """Get comprehensive cache statistics."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Basic statistics
                stats_row = conn.execute("""
                    SELECT 
                        COUNT(*) as total_files,
                        SUM(file_size_bytes) as total_size_bytes,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_files,
                        COUNT(CASE WHEN status = 'orphaned' THEN 1 END) as orphaned_files,
                        COUNT(DISTINCT triggered_by_user) as users_count,
                        MIN(cached_at) as oldest_cached_at
                    FROM cached_files
                """).fetchone()
                
                # Most accessed file
                most_accessed_row = conn.execute("""
                    SELECT file_path FROM cached_files 
                    WHERE access_count > 0
                    ORDER BY access_count DESC 
                    LIMIT 1
                """).fetchone()
                
                total_size_bytes = stats_row['total_size_bytes'] or 0
                
                return CacheStatistics(
                    total_files=stats_row['total_files'],
                    total_size_bytes=total_size_bytes,
                    total_size_readable=self._format_file_size(total_size_bytes),
                    active_files=stats_row['active_files'],
                    orphaned_files=stats_row['orphaned_files'],
                    users_count=stats_row['users_count'],
                    oldest_cached_at=datetime.fromisoformat(stats_row['oldest_cached_at']) if stats_row['oldest_cached_at'] else None,
                    most_accessed_file=most_accessed_row['file_path'] if most_accessed_row else None,
                    cache_hit_ratio=0.0  # TODO: Calculate from access logs
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get cache statistics: {e}")
            return CacheStatistics(
                total_files=0, total_size_bytes=0, total_size_readable="0 B",
                active_files=0, orphaned_files=0, users_count=0
            )

    def remove_cached_file(self, file_path: str, reason: str = 'manual', 
                          user_id: Optional[str] = None) -> bool:
        """Remove a file from cached files tracking."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Update status to removed
                cursor = conn.execute("""
                    UPDATE cached_files 
                    SET status = 'removed' 
                    WHERE file_path = ? AND status != 'removed'
                """, (file_path,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self._log_operation('cache_remove', file_path, 'user_request',
                                      user_id, f'File removed: {reason}', True)
                    self.logger.info(f"Removed cached file: {file_path}")
                    return True
                else:
                    self.logger.warning(f"Cached file not found for removal: {file_path}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to remove cached file {file_path}: {e}")
            self._log_operation('cache_remove', file_path, 'user_request',
                              user_id, f'File removal failed: {reason}', False, str(e))
            return False

    def cleanup_orphaned_files(self) -> int:
        """Clean up orphaned cache entries (files that no longer exist)."""
        try:
            cleaned_count = 0
            with sqlite3.connect(self.database_path) as conn:
                # Get active cached files
                rows = conn.execute("""
                    SELECT id, file_path, cached_path FROM cached_files 
                    WHERE status = 'active'
                """).fetchall()
                
                for row in rows:
                    file_id, file_path, cached_path = row
                    if not Path(cached_path).exists():
                        # Mark as orphaned
                        conn.execute("""
                            UPDATE cached_files 
                            SET status = 'orphaned' 
                            WHERE id = ?
                        """, (file_id,))
                        cleaned_count += 1
                        self.logger.debug(f"Marked orphaned: {file_path}")
                
                conn.commit()
                
            if cleaned_count > 0:
                self._log_operation('cache_cleanup', '', 'system',
                                  None, f'Cleaned {cleaned_count} orphaned files', True)
                self.logger.info(f"Cleaned up {cleaned_count} orphaned cached files")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup orphaned files: {e}")
            return 0

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and unit_index < len(size_units) - 1:
            size /= 1024.0
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {size_units[unit_index]}"
        else:
            return f"{size:.1f} {size_units[unit_index]}"

    def get_cached_file_by_id(self, file_id: str) -> Optional[CachedFileInfo]:
        """Get a specific cached file by ID."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                
                row = conn.execute("""
                    SELECT * FROM cached_files WHERE id = ?
                """, (file_id,)).fetchone()
                
                if not row:
                    return None
                
                # Get user attributions
                user_rows = conn.execute("""
                    SELECT user_id FROM cached_file_users WHERE cached_file_id = ?
                """, (file_id,)).fetchall()
                users = [user_row['user_id'] for user_row in user_rows]
                
                return CachedFileInfo(
                    id=row['id'],
                    file_path=row['file_path'],
                    filename=row['filename'],
                    original_path=row['original_path'],
                    cached_path=row['cached_path'],
                    cache_method=row['cache_method'],
                    file_size_bytes=row['file_size_bytes'],
                    file_size_readable=row['file_size_readable'],
                    cached_at=datetime.fromisoformat(row['cached_at']),
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                    access_count=row['access_count'],
                    triggered_by_user=row['triggered_by_user'],
                    triggered_by_operation=row['triggered_by_operation'],
                    status=row['status'],
                    users=users,
                    metadata=json.loads(row['metadata']) if row['metadata'] else None
                )
                
        except Exception as e:
            self.logger.error(f"Failed to get cached file by ID {file_id}: {e}")
            return None

    def update_file_access(self, file_path: str, user_id: Optional[str] = None) -> bool:
        """Update file access timestamp and count."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    UPDATE cached_files 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE file_path = ? AND status = 'active'
                """, (datetime.now(timezone.utc).isoformat(), file_path))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self._log_operation('cache_access', file_path, 'system',
                                      user_id, 'File accessed', True)
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update file access for {file_path}: {e}")
            return False

    def add_user_to_file(self, file_path: str, user_id: str, attribution_reason: str = 'manual') -> bool:
        """Add a user attribution to a cached file."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get the file ID first
                row = conn.execute("SELECT id FROM cached_files WHERE file_path = ?", (file_path,)).fetchone()
                if not row:
                    self.logger.warning(f"Cached file not found: {file_path}")
                    return False
                
                file_id = row[0]
                
                # Add user attribution
                conn.execute("""
                    INSERT OR IGNORE INTO cached_file_users 
                    (cached_file_id, user_id, attribution_reason)
                    VALUES (?, ?, ?)
                """, (file_id, user_id, attribution_reason))
                
                conn.commit()
                self.logger.debug(f"Added user {user_id} to cached file: {file_path}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add user {user_id} to cached file {file_path}: {e}")
            return False

    def remove_user_from_file(self, file_path: str, user_id: str) -> bool:
        """Remove a user attribution from a cached file."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Get the file ID first
                row = conn.execute("SELECT id FROM cached_files WHERE file_path = ?", (file_path,)).fetchone()
                if not row:
                    return False
                
                file_id = row[0]
                
                # Remove user attribution
                cursor = conn.execute("""
                    DELETE FROM cached_file_users 
                    WHERE cached_file_id = ? AND user_id = ?
                """, (file_id, user_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.debug(f"Removed user {user_id} from cached file: {file_path}")
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove user {user_id} from cached file {file_path}: {e}")
            return False

    def get_files_by_user(self, user_id: str, limit: int = 100) -> List[CachedFileInfo]:
        """Get all cached files associated with a specific user."""
        try:
            filter_params = CachedFilesFilter(user_id=user_id, limit=limit)
            cached_files, _ = self.get_cached_files(filter_params)
            return cached_files
        except Exception as e:
            self.logger.error(f"Failed to get files for user {user_id}: {e}")
            return []

    def cleanup_removed_files(self, days_to_keep: int = 7) -> int:
        """Permanently remove old files marked as 'removed'."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.database_path) as conn:
                # Delete old removed files
                cursor = conn.execute("""
                    DELETE FROM cached_files 
                    WHERE status = 'removed' AND cached_at < ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self._log_operation('cache_cleanup', '', 'system', None,
                                      f'Permanently removed {deleted_count} old files', True)
                    self.logger.info(f"Permanently removed {deleted_count} old cached file records")
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup removed files: {e}")
            return 0

    def verify_cache_integrity(self) -> Tuple[int, int]:
        """Verify cache integrity and return (verified_count, error_count)."""
        try:
            verified_count = 0
            error_count = 0
            
            with sqlite3.connect(self.database_path) as conn:
                # Get all active cached files
                rows = conn.execute("""
                    SELECT id, file_path, cached_path, original_path FROM cached_files 
                    WHERE status = 'active'
                """).fetchall()
                
                for row in rows:
                    file_id, file_path, cached_path, original_path = row
                    
                    # Check if cached file exists
                    if not Path(cached_path).exists():
                        # Mark as orphaned
                        conn.execute("""
                            UPDATE cached_files 
                            SET status = 'orphaned' 
                            WHERE id = ?
                        """, (file_id,))
                        error_count += 1
                        self.logger.warning(f"Cached file missing, marked as orphaned: {cached_path}")
                    else:
                        verified_count += 1
                
                conn.commit()
                
            self._log_operation('cache_verify', '', 'system', None,
                              f'Verified {verified_count} files, found {error_count} errors', True)
            self.logger.info(f"Cache integrity check: {verified_count} verified, {error_count} errors")
            
            return verified_count, error_count
            
        except Exception as e:
            self.logger.error(f"Failed to verify cache integrity: {e}")
            return 0, 0

    def get_user_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive statistics for a specific user."""
        try:
            since_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get user's cached files stats
                stats_row = conn.execute("""
                    SELECT 
                        COUNT(*) as total_files,
                        SUM(file_size_bytes) as total_size_bytes,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_files,
                        COUNT(CASE WHEN triggered_by_operation = 'watchlist' THEN 1 END) as watchlist_files,
                        COUNT(CASE WHEN triggered_by_operation = 'ondeck' THEN 1 END) as ondeck_files,
                        COUNT(CASE WHEN triggered_by_operation = 'real_time_watch' THEN 1 END) as realtime_files,
                        AVG(access_count) as avg_access_count,
                        MAX(access_count) as max_access_count
                    FROM cached_files 
                    WHERE (triggered_by_user = ? OR EXISTS (
                        SELECT 1 FROM cached_file_users cfu 
                        WHERE cfu.cached_file_id = cached_files.id AND cfu.user_id = ?
                    )) AND cached_at >= ?
                """, (user_id, user_id, since_date.isoformat())).fetchone()
                
                # Get most accessed file by this user
                most_accessed_row = conn.execute("""
                    SELECT file_path, filename, access_count 
                    FROM cached_files 
                    WHERE (triggered_by_user = ? OR EXISTS (
                        SELECT 1 FROM cached_file_users cfu 
                        WHERE cfu.cached_file_id = cached_files.id AND cfu.user_id = ?
                    )) AND access_count > 0
                    ORDER BY access_count DESC 
                    LIMIT 1
                """, (user_id, user_id)).fetchone()
                
                total_size_bytes = stats_row['total_size_bytes'] or 0
                
                return {
                    'user_id': user_id,
                    'period_days': days,
                    'total_files': stats_row['total_files'],
                    'active_files': stats_row['active_files'],
                    'total_size_bytes': total_size_bytes,
                    'total_size_readable': self._format_file_size(total_size_bytes),
                    'files_by_operation': {
                        'watchlist': stats_row['watchlist_files'],
                        'ondeck': stats_row['ondeck_files'],
                        'real_time_watch': stats_row['realtime_files']
                    },
                    'access_stats': {
                        'average_access_count': round(stats_row['avg_access_count'] or 0, 1),
                        'max_access_count': stats_row['max_access_count'] or 0
                    },
                    'most_accessed_file': {
                        'path': most_accessed_row['file_path'] if most_accessed_row else None,
                        'filename': most_accessed_row['filename'] if most_accessed_row else None,
                        'access_count': most_accessed_row['access_count'] if most_accessed_row else 0
                    } if most_accessed_row else None
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get user statistics for {user_id}: {e}")
            return {
                'user_id': user_id,
                'period_days': days,
                'total_files': 0,
                'active_files': 0,
                'total_size_bytes': 0,
                'total_size_readable': '0 B',
                'files_by_operation': {},
                'access_stats': {'average_access_count': 0, 'max_access_count': 0},
                'most_accessed_file': None
            }

    def get_operation_logs(self, limit: int = 100, user_id: Optional[str] = None,
                          operation_type: Optional[str] = None) -> List[CacheOperationLog]:
        """Get cache operation logs with filtering."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clauses = []
                params = []
                
                if user_id:
                    where_clauses.append("triggered_by_user = ?")
                    params.append(user_id)
                
                if operation_type:
                    where_clauses.append("operation_type = ?")
                    params.append(operation_type)
                
                where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                query = f"""
                    SELECT * FROM cache_operations_log 
                    {where_sql}
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                
                logs = []
                for row in rows:
                    logs.append(CacheOperationLog(
                        id=row['id'],
                        operation_type=row['operation_type'],
                        file_path=row['file_path'],
                        triggered_by=row['triggered_by'],
                        triggered_by_user=row['triggered_by_user'],
                        reason=row['reason'],
                        success=bool(row['success']),
                        error_message=row['error_message'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None,
                        timestamp=datetime.fromisoformat(row['timestamp'])
                    ))
                
                return logs
                
        except Exception as e:
            self.logger.error(f"Failed to get operation logs: {e}")
            return []

    def _log_operation(self, operation_type: str, file_path: str, triggered_by: str,
                      triggered_by_user: Optional[str], reason: str, success: bool,
                      error_message: Optional[str] = None, metadata: Optional[Dict] = None) -> None:
        """Log cache operation for audit trail."""
        try:
            log_entry = CacheOperationLog(
                id=str(uuid.uuid4()),
                operation_type=operation_type,
                file_path=file_path,
                triggered_by=triggered_by,
                triggered_by_user=triggered_by_user,
                reason=reason,
                success=success,
                error_message=error_message,
                metadata=metadata,
                timestamp=datetime.now(timezone.utc)
            )
            
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO cache_operations_log 
                    (id, operation_type, file_path, triggered_by, triggered_by_user, 
                     reason, success, error_message, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_entry.id, log_entry.operation_type, log_entry.file_path,
                    log_entry.triggered_by, log_entry.triggered_by_user,
                    log_entry.reason, log_entry.success, log_entry.error_message,
                    json.dumps(metadata) if metadata else None, log_entry.timestamp.isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log cache operation: {e}")

    def migrate_database(self) -> bool:
        """Migrate database schema to latest version."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Check current schema version
                try:
                    version_result = conn.execute("PRAGMA user_version").fetchone()
                    current_version = version_result[0] if version_result else 0
                except sqlite3.Error:
                    current_version = 0
                
                self.logger.info(f"Current database schema version: {current_version}")
                
                # Apply migrations based on version
                if current_version < 1:
                    # Migration 1: Add indexes for better performance
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_operation ON cached_files(triggered_by_operation)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_cached_files_size ON cached_files(file_size_bytes)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_log_type ON cache_operations_log(operation_type)")
                    conn.execute("PRAGMA user_version = 1")
                    self.logger.info("Applied migration 1: Added performance indexes")
                
                if current_version < 2:
                    # Migration 2: Add cache method validation
                    # This would be handled by the Pydantic validation in the application
                    conn.execute("PRAGMA user_version = 2")
                    self.logger.info("Applied migration 2: Cache method validation")
                
                conn.commit()
                self.logger.info("Database migration completed successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Database migration failed: {e}")
            return False
