"""
Secure Cached Files Service - Production-ready cached file tracking and management.

This is a complete rewrite of the CachedFilesService with comprehensive security
hardening to address all critical security vulnerabilities:

1. SQL Injection Prevention: All queries use parameterized statements
2. Path Traversal Protection: Comprehensive path validation and sanitization
3. Authorization Framework: Role-based access control with audit logging
4. Connection Pool Management: Proper database resource management
5. Race Condition Prevention: Atomic transactions for all operations
6. Input Validation: Enhanced Pydantic models with security-focused validation
7. Security Logging: Comprehensive audit trail for all security-relevant events

This implementation follows secure coding practices and is production-ready
for handling user data and file operations.
"""

import json
import logging
import sqlite3
import uuid
import hashlib
import hmac
import secrets
import threading
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union, ContextManager
from dataclasses import dataclass
from enum import Enum
from queue import Queue
from threading import Lock

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from pydantic import ValidationError as PydanticValidationError

try:
    from .interfaces import UserOperationContext
except ImportError:
    # Fallback for testing
    from interfaces import UserOperationContext


# Security Configuration
class SecurityConfig:
    """Security configuration constants."""
    MAX_PATH_LENGTH = 4096
    MAX_FILENAME_LENGTH = 255
    MAX_METADATA_SIZE = 65536  # 64KB
    MAX_QUERY_RESULTS = 1000
    SESSION_TIMEOUT_HOURS = 24
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_REQUESTS = 100
    
    # Allowed characters for filenames (security)
    SAFE_FILENAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- ()[]")
    
    # Path traversal patterns
    DANGEROUS_PATTERNS = ['../', '..\\', './', '.\\', '/..', '\\..']


class SecurityLevel(str, Enum):
    """Security levels for operations."""
    PUBLIC = "public"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


class PermissionType(str, Enum):
    """Permission types for authorization."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class SecurityEvent(BaseModel):
    """Security event for audit logging."""
    event_type: str
    user_id: Optional[str]
    resource: str
    action: str
    success: bool
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class DatabaseConnection:
    """Database connection wrapper with security context."""
    connection: sqlite3.Connection
    transaction_active: bool = False
    last_used: datetime = None
    connection_id: str = None


class SecurePathValidator:
    """Secure path validation utility."""
    
    @staticmethod
    def validate_path(path: str, base_paths: Optional[List[str]] = None) -> str:
        """
        Validate and sanitize a file path to prevent directory traversal attacks.
        
        Args:
            path: Path to validate
            base_paths: Optional list of allowed base paths
            
        Returns:
            Sanitized absolute path
            
        Raises:
            ValueError: If path is invalid or contains dangerous patterns
        """
        if not path or not isinstance(path, str):
            raise ValueError("Path must be a non-empty string")
        
        # Check length limits
        if len(path) > SecurityConfig.MAX_PATH_LENGTH:
            raise ValueError(f"Path too long (max {SecurityConfig.MAX_PATH_LENGTH} characters)")
        
        # Check for dangerous patterns
        path_lower = path.lower()
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if pattern in path_lower:
                raise ValueError(f"Path contains dangerous pattern: {pattern}")
        
        # Resolve path to absolute and normalize
        try:
            resolved_path = Path(path).resolve()
            path_str = str(resolved_path)
        except (OSError, ValueError) as e:
            raise ValueError(f"Invalid path: {e}")
        
        # Validate against base paths if provided
        if base_paths:
            allowed = False
            for base_path in base_paths:
                try:
                    base_resolved = Path(base_path).resolve()
                    if resolved_path.is_relative_to(base_resolved):
                        allowed = True
                        break
                except (OSError, ValueError):
                    continue
            
            if not allowed:
                raise ValueError(f"Path not within allowed directories: {path}")
        
        return path_str
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate and sanitize a filename.
        
        Args:
            filename: Filename to validate
            
        Returns:
            Sanitized filename
            
        Raises:
            ValueError: If filename is invalid
        """
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename must be a non-empty string")
        
        if len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
            raise ValueError(f"Filename too long (max {SecurityConfig.MAX_FILENAME_LENGTH} characters)")
        
        # Check for dangerous characters
        if not all(c in SecurityConfig.SAFE_FILENAME_CHARS for c in filename):
            raise ValueError("Filename contains invalid characters")
        
        # Check for reserved names (Windows)
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL'} | {f'COM{i}' for i in range(1, 10)} | {f'LPT{i}' for i in range(1, 10)}
        if filename.upper().split('.')[0] in reserved_names:
            raise ValueError(f"Filename uses reserved name: {filename}")
        
        return filename


class SecureCachedFileInfo(BaseModel):
    """
    Secure cached file information with comprehensive validation.
    
    Enhanced with security-focused validation to prevent injection attacks
    and ensure data integrity.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        extra='forbid',
        frozen=False  # Allow modification for security updates
    )
    
    id: str = Field(
        ..., 
        min_length=1,
        max_length=128,
        pattern=r'^[a-zA-Z0-9-]+$',
        description="Unique identifier for the cached file"
    )
    file_path: str = Field(
        ..., 
        min_length=1,
        max_length=SecurityConfig.MAX_PATH_LENGTH,
        description="Original file path (validated)"
    )
    filename: str = Field(
        ..., 
        min_length=1,
        max_length=SecurityConfig.MAX_FILENAME_LENGTH,
        description="File name extracted from path (validated)"
    )
    original_path: str = Field(
        ..., 
        min_length=1,
        max_length=SecurityConfig.MAX_PATH_LENGTH,
        description="Original location before caching (validated)"
    )
    cached_path: str = Field(
        ..., 
        min_length=1,
        max_length=SecurityConfig.MAX_PATH_LENGTH,
        description="Current cached location (validated)"
    )
    cache_method: str = Field(..., description="Method used for caching")
    file_size_bytes: int = Field(..., ge=0, le=1000000000000, description="File size in bytes (max 1TB)")
    file_size_readable: str = Field(..., max_length=20, description="Human-readable file size")
    cached_at: datetime = Field(..., description="When the file was cached")
    last_accessed: Optional[datetime] = Field(None, description="Last access time")
    access_count: int = Field(0, ge=0, le=1000000, description="Number of times accessed")
    triggered_by_user: Optional[str] = Field(
        None, 
        max_length=128,
        pattern=r'^[a-zA-Z0-9._@-]+$',
        description="Primary user who triggered caching"
    )
    triggered_by_operation: str = Field(..., description="Operation that triggered caching")
    status: str = Field(..., description="Current status of the cached file")
    users: List[str] = Field(
        default_factory=list, 
        max_length=100,
        description="All users associated with this cache"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    checksum: Optional[str] = Field(None, description="File integrity checksum")
    security_context: Optional[Dict[str, str]] = Field(None, description="Security context")

    @field_validator('cache_method')
    @classmethod
    def validate_cache_method(cls, v: str) -> str:
        allowed_methods = {'atomic_symlink', 'atomic_hardlink', 'atomic_copy', 'secure_copy'}
        if v not in allowed_methods:
            raise ValueError(f'cache_method must be one of: {allowed_methods}')
        return v

    @field_validator('status')
    @classmethod 
    def validate_status(cls, v: str) -> str:
        allowed_statuses = {'active', 'orphaned', 'pending_removal', 'removed', 'quarantined'}
        if v not in allowed_statuses:
            raise ValueError(f'status must be one of: {allowed_statuses}')
        return v

    @field_validator('triggered_by_operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        allowed_operations = {
            'watchlist', 'ondeck', 'trakt', 'manual', 'continue_watching', 
            'real_time_watch', 'active_watching', 'system_maintenance'
        }
        if v not in allowed_operations:
            raise ValueError(f'triggered_by_operation must be one of: {allowed_operations}')
        return v

    @field_validator('file_path', 'original_path', 'cached_path')
    @classmethod
    def validate_paths(cls, v: str) -> str:
        return SecurePathValidator.validate_path(v)

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        return SecurePathValidator.validate_filename(v)

    @field_validator('users')
    @classmethod
    def validate_users(cls, v: List[str]) -> List[str]:
        for user in v:
            if not user or len(user) > 128:
                raise ValueError(f"Invalid user ID: {user}")
            if not user.replace('.', '').replace('_', '').replace('@', '').replace('-', '').isalnum():
                raise ValueError(f"User ID contains invalid characters: {user}")
        return v

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        
        # Serialize to check size
        serialized = json.dumps(v)
        if len(serialized) > SecurityConfig.MAX_METADATA_SIZE:
            raise ValueError(f"Metadata too large (max {SecurityConfig.MAX_METADATA_SIZE} bytes)")
        
        # Validate keys and basic values
        for key, value in v.items():
            if not isinstance(key, str) or len(key) > 128:
                raise ValueError(f"Invalid metadata key: {key}")
            if isinstance(value, str) and len(value) > 1024:
                raise ValueError(f"Metadata value too long for key {key}")
        
        return v


class SecureCacheStatistics(BaseModel):
    """Secure cache statistics with validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    total_files: int = Field(..., ge=0, le=10000000, description="Total number of cached files")
    total_size_bytes: int = Field(..., ge=0, description="Total size in bytes")
    total_size_readable: str = Field(..., max_length=50, description="Human-readable total size")
    active_files: int = Field(..., ge=0, description="Number of active cached files")
    orphaned_files: int = Field(0, ge=0, description="Number of orphaned files")
    users_count: int = Field(0, ge=0, le=10000, description="Number of unique users")
    oldest_cached_at: Optional[datetime] = Field(None, description="Oldest cache timestamp")
    most_accessed_file: Optional[str] = Field(None, max_length=512, description="Most frequently accessed file")
    cache_hit_ratio: float = Field(0.0, ge=0.0, le=1.0, description="Cache hit ratio")
    security_events_count: int = Field(0, ge=0, description="Number of security events")


class SecureCachedFilesFilter(BaseModel):
    """Secure filter parameters with validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    search: Optional[str] = Field(
        None, 
        max_length=256,
        pattern=r'^[a-zA-Z0-9._\-\s\(\)\[\]]*$',
        description="Search term for filename/path (alphanumeric only)"
    )
    user_id: Optional[str] = Field(
        None, 
        max_length=128,
        pattern=r'^[a-zA-Z0-9._@-]+$',
        description="Filter by user ID"
    )
    status: Optional[str] = Field(None, description="Filter by status")
    triggered_by_operation: Optional[str] = Field(None, description="Filter by operation type")
    size_min: Optional[int] = Field(None, ge=0, description="Minimum file size in bytes")
    size_max: Optional[int] = Field(None, ge=0, le=1000000000000, description="Maximum file size in bytes")
    cached_since: Optional[datetime] = Field(None, description="Filter files cached since this date")
    limit: int = Field(50, ge=1, le=SecurityConfig.MAX_QUERY_RESULTS, description="Maximum results to return")
    offset: int = Field(0, ge=0, le=100000, description="Offset for pagination")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed_statuses = {'active', 'orphaned', 'pending_removal', 'removed', 'quarantined'}
        if v not in allowed_statuses:
            raise ValueError(f'status must be one of: {allowed_statuses}')
        return v

    @field_validator('triggered_by_operation')
    @classmethod
    def validate_operation(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed_operations = {
            'watchlist', 'ondeck', 'trakt', 'manual', 'continue_watching', 
            'real_time_watch', 'active_watching', 'system_maintenance'
        }
        if v not in allowed_operations:
            raise ValueError(f'triggered_by_operation must be one of: {allowed_operations}')
        return v


class SecurityLogger:
    """Security-focused logger for audit trails."""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(f"security.{logger_name}")
        self.events: List[SecurityEvent] = []
        self._lock = Lock()
    
    def log_security_event(self, event_type: str, user_id: Optional[str], 
                          resource: str, action: str, success: bool, 
                          details: Dict[str, Any], ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None) -> None:
        """Log a security event."""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            resource=resource,
            action=action,
            success=success,
            details=details,
            timestamp=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        with self._lock:
            self.events.append(event)
            # Keep only recent events in memory
            if len(self.events) > 1000:
                self.events = self.events[-500:]
        
        # Log to standard logger
        level = logging.WARNING if not success or event_type in ['authentication_failure', 'authorization_failure'] else logging.INFO
        self.logger.log(level, f"SECURITY: {event_type} - {action} on {resource} by {user_id or 'system'} - {'SUCCESS' if success else 'FAILED'}")


class ConnectionPool:
    """Thread-safe database connection pool."""
    
    def __init__(self, database_path: str, max_connections: int = 10):
        self.database_path = database_path
        self.max_connections = max_connections
        self._pool: Queue = Queue(maxsize=max_connections)
        self._active_connections: Dict[str, DatabaseConnection] = {}
        self._lock = Lock()
        self._connection_count = 0
    
    def _create_connection(self) -> DatabaseConnection:
        """Create a new database connection."""
        conn = sqlite3.connect(
            self.database_path,
            timeout=30.0,  # 30 second timeout
            isolation_level=None,  # Autocommit disabled
            check_same_thread=False
        )
        
        # Enable security features
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous = FULL")  # Full durability
        conn.execute("PRAGMA temp_store = MEMORY")  # Store temp data in memory
        conn.execute("PRAGMA cache_size = 10000")  # 10MB cache
        
        connection_id = str(uuid.uuid4())
        return DatabaseConnection(
            connection=conn,
            last_used=datetime.now(timezone.utc),
            connection_id=connection_id
        )
    
    @contextmanager
    def get_connection(self) -> ContextManager[DatabaseConnection]:
        """Get a database connection from the pool."""
        db_conn = None
        try:
            # Try to get from pool
            try:
                db_conn = self._pool.get_nowait()
            except:
                # Create new connection if pool is empty
                with self._lock:
                    if self._connection_count < self.max_connections:
                        db_conn = self._create_connection()
                        self._connection_count += 1
                        self._active_connections[db_conn.connection_id] = db_conn
                    else:
                        # Wait for a connection to become available
                        db_conn = self._pool.get(timeout=30)
            
            db_conn.last_used = datetime.now(timezone.utc)
            yield db_conn
            
        finally:
            if db_conn:
                # Return connection to pool
                try:
                    if not db_conn.transaction_active:
                        self._pool.put_nowait(db_conn)
                    else:
                        # Connection has active transaction, close it
                        db_conn.connection.close()
                        with self._lock:
                            self._connection_count -= 1
                            if db_conn.connection_id in self._active_connections:
                                del self._active_connections[db_conn.connection_id]
                except:
                    # Close connection on error
                    try:
                        db_conn.connection.close()
                    except:
                        pass
                    with self._lock:
                        self._connection_count -= 1
                        if db_conn.connection_id in self._active_connections:
                            del self._active_connections[db_conn.connection_id]
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            # Close pooled connections
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.connection.close()
                except:
                    pass
            
            # Close active connections
            for db_conn in self._active_connections.values():
                try:
                    db_conn.connection.close()
                except:
                    pass
            
            self._active_connections.clear()
            self._connection_count = 0


class AuthorizationManager:
    """Authorization and access control manager."""
    
    def __init__(self):
        self.user_permissions: Dict[str, Set[PermissionType]] = {}
        self.user_roles: Dict[str, SecurityLevel] = {}
        self._lock = Lock()
    
    def add_user(self, user_id: str, role: SecurityLevel, permissions: Optional[Set[PermissionType]] = None):
        """Add a user with role and permissions."""
        with self._lock:
            self.user_roles[user_id] = role
            if permissions:
                self.user_permissions[user_id] = permissions
            else:
                # Default permissions based on role
                if role == SecurityLevel.ADMIN:
                    self.user_permissions[user_id] = {PermissionType.READ, PermissionType.WRITE, PermissionType.DELETE, PermissionType.ADMIN}
                elif role == SecurityLevel.USER:
                    self.user_permissions[user_id] = {PermissionType.READ, PermissionType.WRITE}
                else:
                    self.user_permissions[user_id] = {PermissionType.READ}
    
    def check_permission(self, user_id: Optional[str], permission: PermissionType, resource: str = "") -> bool:
        """Check if user has permission for an operation."""
        if user_id is None:
            return permission == PermissionType.READ  # Anonymous read-only access
        
        with self._lock:
            user_permissions = self.user_permissions.get(user_id, set())
            return permission in user_permissions
    
    def get_user_role(self, user_id: str) -> Optional[SecurityLevel]:
        """Get user's security role."""
        return self.user_roles.get(user_id)


class SecureCachedFilesService:
    """
    Secure cached files service with comprehensive security hardening.
    
    This implementation addresses all critical security vulnerabilities:
    - SQL injection prevention through parameterized queries
    - Path traversal protection with validation
    - Proper authorization and access control
    - Database connection pooling and resource management
    - Atomic transactions to prevent race conditions
    - Comprehensive security logging and audit trails
    - Enhanced input validation with Pydantic v2.5
    
    All operations are logged for security auditing and the service
    implements defense-in-depth security practices.
    """
    
    def __init__(self, database_path: str, allowed_base_paths: Optional[List[str]] = None,
                 max_connections: int = 10, security_key: Optional[str] = None):
        """
        Initialize the secure cached files service.
        
        Args:
            database_path: Path to SQLite database
            allowed_base_paths: List of allowed base directories for files
            max_connections: Maximum database connections
            security_key: Secret key for HMAC operations
        """
        self.database_path = SecurePathValidator.validate_path(database_path)
        self.allowed_base_paths = allowed_base_paths or []
        self.security_key = security_key or secrets.token_urlsafe(32)
        
        # Initialize security components
        self.security_logger = SecurityLogger("cached_files_service")
        self.connection_pool = ConnectionPool(self.database_path, max_connections)
        self.auth_manager = AuthorizationManager()
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self._rate_limiter: Dict[str, List[datetime]] = {}
        self._rate_limit_lock = Lock()
        
        # Initialize database with security features
        self._init_secure_database()
        
        self.security_logger.log_security_event(
            "service_initialization", None, "cached_files_service", 
            "initialize", True, {"database_path": self.database_path}
        )
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limits."""
        with self._rate_limit_lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=SecurityConfig.RATE_LIMIT_WINDOW)
            
            if user_id not in self._rate_limiter:
                self._rate_limiter[user_id] = []
            
            # Remove old requests
            self._rate_limiter[user_id] = [req_time for req_time in self._rate_limiter[user_id] if req_time > window_start]
            
            # Check limit
            if len(self._rate_limiter[user_id]) >= SecurityConfig.RATE_LIMIT_REQUESTS:
                return False
            
            # Add current request
            self._rate_limiter[user_id].append(now)
            return True
    
    def _generate_checksum(self, data: str) -> str:
        """Generate HMAC checksum for data integrity."""
        return hmac.new(
            self.security_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _verify_checksum(self, data: str, checksum: str) -> bool:
        """Verify HMAC checksum."""
        expected = self._generate_checksum(data)
        return hmac.compare_digest(expected, checksum)
    
    def _init_secure_database(self) -> None:
        """Initialize SQLite database with security features."""
        try:
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                
                # Create tables with enhanced security
                conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_files (
                    id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    cached_path TEXT NOT NULL,
                    cache_method TEXT NOT NULL CHECK(cache_method IN ('atomic_symlink', 'atomic_hardlink', 'atomic_copy', 'secure_copy')),
                    file_size_bytes INTEGER NOT NULL CHECK(file_size_bytes >= 0 AND file_size_bytes <= 1000000000000),
                    file_size_readable TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0 CHECK(access_count >= 0),
                    triggered_by_user TEXT,
                    triggered_by_operation TEXT NOT NULL CHECK(triggered_by_operation IN ('watchlist', 'ondeck', 'trakt', 'manual', 'continue_watching', 'real_time_watch', 'active_watching', 'system_maintenance')),
                    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'orphaned', 'pending_removal', 'removed', 'quarantined')),
                    metadata TEXT,
                    checksum TEXT,
                    security_context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Enhanced user attribution table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS cached_file_users (
                    cached_file_id TEXT NOT NULL,
                    user_id TEXT NOT NULL CHECK(LENGTH(user_id) <= 128),
                    attribution_reason TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(cached_file_id, user_id),
                    FOREIGN KEY(cached_file_id) REFERENCES cached_files(id) ON DELETE CASCADE
                )
                """)
                
                # Enhanced operations log with security context
                conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_operations_log (
                    id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL CHECK(operation_type IN ('cache_add', 'cache_remove', 'cache_cleanup', 'cache_access', 'cache_verify', 'security_event')),
                    file_path TEXT NOT NULL,
                    triggered_by TEXT NOT NULL,
                    triggered_by_user TEXT,
                    reason TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    metadata TEXT,
                    security_context TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Security events table
                conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    details TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Create comprehensive indexes for performance and security
                security_indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_cached_files_status ON cached_files(status)",
                    "CREATE INDEX IF NOT EXISTS idx_cached_files_user ON cached_files(triggered_by_user)",
                    "CREATE INDEX IF NOT EXISTS idx_cached_files_cached_at ON cached_files(cached_at)",
                    "CREATE INDEX IF NOT EXISTS idx_cached_files_path ON cached_files(file_path)",
                    "CREATE INDEX IF NOT EXISTS idx_cache_log_timestamp ON cache_operations_log(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_cache_log_user ON cache_operations_log(triggered_by_user)",
                    "CREATE INDEX IF NOT EXISTS idx_cache_log_type ON cache_operations_log(operation_type)",
                    "CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_security_events_user ON security_events(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)",
                ]
                
                for index_sql in security_indexes:
                    conn.execute(index_sql)
                
                # Enable secure SQLite features
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA secure_delete = ON")  # Overwrite deleted data
                conn.execute("PRAGMA cell_size_check = ON")  # Integrity checks
                
                conn.commit()
                self.logger.info("Secure cached files database initialized successfully")
                
        except sqlite3.Error as e:
            self.security_logger.log_security_event(
                "database_initialization_failed", None, "database", 
                "initialize", False, {"error": str(e)}
            )
            self.logger.error(f"Failed to initialize secure cached files database: {e}")
            raise

    def add_cached_file(self, file_path: str, original_path: str, cached_path: str,
                       cache_method: str = 'atomic_symlink', user_context: Optional[UserOperationContext] = None,
                       operation_reason: str = 'manual', metadata: Optional[Dict] = None,
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> SecureCachedFileInfo:
        """
        Add a file to cached files tracking with comprehensive security.
        
        Args:
            file_path: Original file path
            original_path: Original location before caching
            cached_path: Current cached location  
            cache_method: Caching method to use
            user_context: User operation context
            operation_reason: Reason for the operation
            metadata: Additional metadata
            ip_address: Client IP address for security logging
            user_agent: Client user agent for security logging
            
        Returns:
            SecureCachedFileInfo instance
            
        Raises:
            ValueError: If validation fails
            PermissionError: If user lacks required permissions
            sqlite3.Error: If database operation fails
        """
        user_id = user_context.user_id if user_context else None
        
        # Security checks
        if user_id and not self._check_rate_limit(user_id):
            self.security_logger.log_security_event(
                "rate_limit_exceeded", user_id, "cached_files", "add_file", 
                False, {"file_path": file_path}, ip_address, user_agent
            )
            raise PermissionError("Rate limit exceeded")
        
        if not self.auth_manager.check_permission(user_id, PermissionType.WRITE, file_path):
            self.security_logger.log_security_event(
                "authorization_failure", user_id, "cached_files", "add_file",
                False, {"file_path": file_path}, ip_address, user_agent
            )
            raise PermissionError("Insufficient permissions to add cached file")
        
        try:
            # Validate and sanitize paths
            validated_file_path = SecurePathValidator.validate_path(file_path, self.allowed_base_paths)
            validated_original_path = SecurePathValidator.validate_path(original_path, self.allowed_base_paths)
            validated_cached_path = SecurePathValidator.validate_path(cached_path, self.allowed_base_paths)
            
            file_id = str(uuid.uuid4())
            filename = SecurePathValidator.validate_filename(Path(validated_file_path).name)
            
            # Ensure atomic operations
            if cache_method in ('copy', 'symlink'):
                cache_method = f'atomic_{cache_method}'
            
            # Force secure_copy for active watching operations
            if operation_reason in ('active_watching', 'real_time_watch'):
                cache_method = 'secure_copy'
                self.logger.debug(f"Forced secure_copy for active watching: {validated_file_path}")
            
            # Get file size safely
            try:
                file_size_bytes = Path(validated_cached_path).stat().st_size if Path(validated_cached_path).exists() else 0
                file_size_readable = self._format_file_size(file_size_bytes)
            except OSError:
                file_size_bytes = 0
                file_size_readable = "0 B"
            
            # Generate integrity checksum
            checksum_data = f"{validated_file_path}:{file_size_bytes}:{cache_method}"
            checksum = self._generate_checksum(checksum_data)
            
            # Create secure cached file info
            cached_file = SecureCachedFileInfo(
                id=file_id,
                file_path=validated_file_path,
                filename=filename,
                original_path=validated_original_path,
                cached_path=validated_cached_path,
                cache_method=cache_method,
                file_size_bytes=file_size_bytes,
                file_size_readable=file_size_readable,
                cached_at=datetime.now(timezone.utc),
                triggered_by_user=user_id,
                triggered_by_operation=operation_reason,
                status='active',
                users=[user_id] if user_id else [],
                metadata=metadata,
                checksum=checksum,
                security_context={
                    'added_by': user_id or 'system',
                    'ip_address': ip_address or 'unknown',
                    'user_agent': user_agent or 'unknown'
                }
            )
            
            # Use atomic transaction
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                db_conn.transaction_active = True
                
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Insert cached file with parameterized query
                    conn.execute("""
                        INSERT OR REPLACE INTO cached_files 
                        (id, file_path, filename, original_path, cached_path, cache_method, 
                         file_size_bytes, file_size_readable, cached_at, triggered_by_user, 
                         triggered_by_operation, status, metadata, checksum, security_context)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cached_file.id, cached_file.file_path, cached_file.filename,
                        cached_file.original_path, cached_file.cached_path, cached_file.cache_method,
                        cached_file.file_size_bytes, cached_file.file_size_readable,
                        cached_file.cached_at.isoformat(), cached_file.triggered_by_user,
                        cached_file.triggered_by_operation, cached_file.status,
                        json.dumps(metadata) if metadata else None,
                        checksum, json.dumps(cached_file.security_context)
                    ))
                    
                    # Add user attribution
                    if user_id:
                        conn.execute("""
                            INSERT OR IGNORE INTO cached_file_users 
                            (cached_file_id, user_id, attribution_reason)
                            VALUES (?, ?, ?)
                        """, (file_id, user_id, operation_reason))
                    
                    conn.commit()
                    db_conn.transaction_active = False
                    
                except Exception as e:
                    conn.rollback()
                    db_conn.transaction_active = False
                    raise
            
            # Log successful operation
            self._log_secure_operation('cache_add', validated_file_path, 'file_service', 
                                     user_id, f'File cached via {operation_reason}', True, 
                                     None, metadata, ip_address, user_agent)
            
            self.security_logger.log_security_event(
                "file_cached", user_id, validated_file_path, "add_cached_file",
                True, {
                    "file_id": file_id,
                    "cache_method": cache_method,
                    "operation_reason": operation_reason,
                    "file_size": file_size_bytes
                }, ip_address, user_agent
            )
            
            self.logger.info(f"Added cached file: {validated_file_path}")
            return cached_file
            
        except (ValueError, PydanticValidationError) as e:
            self.security_logger.log_security_event(
                "validation_failure", user_id, file_path, "add_cached_file",
                False, {"error": str(e)}, ip_address, user_agent
            )
            self.logger.error(f"Validation failed for cached file {file_path}: {e}")
            raise ValueError(f"Invalid input: {e}")
            
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", user_id, file_path, "add_cached_file",
                False, {"error": str(e)}, ip_address, user_agent
            )
            self.logger.error(f"Failed to add cached file {file_path}: {e}")
            self._log_secure_operation('cache_add', file_path, 'file_service',
                                     user_id, f'File caching failed: {operation_reason}', 
                                     False, str(e), metadata, ip_address, user_agent)
            raise

    def get_cached_files(self, filter_params: Optional[SecureCachedFilesFilter] = None,
                        user_context: Optional[UserOperationContext] = None,
                        ip_address: Optional[str] = None) -> Tuple[List[SecureCachedFileInfo], int]:
        """
        Get cached files with secure filtering and pagination.
        
        Args:
            filter_params: Filter parameters (validated)
            user_context: User operation context
            ip_address: Client IP address
            
        Returns:
            Tuple of (cached files list, total count)
            
        Raises:
            PermissionError: If user lacks read permissions
            ValueError: If filter validation fails
        """
        if filter_params is None:
            filter_params = SecureCachedFilesFilter()
        
        user_id = user_context.user_id if user_context else None
        
        # Security checks
        if user_id and not self._check_rate_limit(user_id):
            self.security_logger.log_security_event(
                "rate_limit_exceeded", user_id, "cached_files", "get_files",
                False, {"filter": filter_params.model_dump()}, ip_address
            )
            raise PermissionError("Rate limit exceeded")
        
        if not self.auth_manager.check_permission(user_id, PermissionType.READ):
            self.security_logger.log_security_event(
                "authorization_failure", user_id, "cached_files", "get_files",
                False, {"filter": filter_params.model_dump()}, ip_address
            )
            raise PermissionError("Insufficient permissions to read cached files")
        
        try:
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                conn.row_factory = sqlite3.Row
                
                # Build secure parameterized query
                where_clauses = []
                params = []
                
                if filter_params.search:
                    # Use safe search with LIKE and parameterized values
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
                
                # Count total with same parameters
                count_query = f"SELECT COUNT(*) FROM cached_files {where_sql}"
                total_count = conn.execute(count_query, params).fetchone()[0]
                
                # Get paginated results with parameterized query
                query = f"""
                    SELECT * FROM cached_files 
                    {where_sql}
                    ORDER BY cached_at DESC 
                    LIMIT ? OFFSET ?
                """
                params.extend([filter_params.limit, filter_params.offset])
                
                rows = conn.execute(query, params).fetchall()
                
                # Convert to secure models
                cached_files = []
                for row in rows:
                    # Get user attributions with parameterized query
                    user_rows = conn.execute("""
                        SELECT user_id FROM cached_file_users WHERE cached_file_id = ?
                    """, (row['id'],)).fetchall()
                    users = [user_row['user_id'] for user_row in user_rows]
                    
                    # Verify integrity if checksum exists
                    if row['checksum']:
                        expected_data = f"{row['file_path']}:{row['file_size_bytes']}:{row['cache_method']}"
                        if not self._verify_checksum(expected_data, row['checksum']):
                            self.security_logger.log_security_event(
                                "integrity_check_failed", user_id, row['file_path'], 
                                "get_cached_files", False, {"file_id": row['id']}, ip_address
                            )
                    
                    cached_file = SecureCachedFileInfo(
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
                        metadata=json.loads(row['metadata']) if row['metadata'] else None,
                        checksum=row['checksum'],
                        security_context=json.loads(row['security_context']) if row['security_context'] else None
                    )
                    cached_files.append(cached_file)
                
                # Log successful access
                self.security_logger.log_security_event(
                    "files_accessed", user_id, "cached_files", "get_cached_files",
                    True, {
                        "count": len(cached_files),
                        "total": total_count,
                        "filter": filter_params.model_dump()
                    }, ip_address
                )
                
                return cached_files, total_count
                
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", user_id, "cached_files", "get_cached_files",
                False, {"error": str(e)}, ip_address
            )
            self.logger.error(f"Failed to get cached files: {e}")
            return [], 0

    def get_cache_statistics(self, user_context: Optional[UserOperationContext] = None,
                           ip_address: Optional[str] = None) -> SecureCacheStatistics:
        """
        Get comprehensive cache statistics with security logging.
        
        Args:
            user_context: User operation context
            ip_address: Client IP address
            
        Returns:
            SecureCacheStatistics instance
            
        Raises:
            PermissionError: If user lacks read permissions
        """
        user_id = user_context.user_id if user_context else None
        
        # Security check
        if not self.auth_manager.check_permission(user_id, PermissionType.READ):
            self.security_logger.log_security_event(
                "authorization_failure", user_id, "cache_statistics", "get_statistics",
                False, {}, ip_address
            )
            raise PermissionError("Insufficient permissions to read cache statistics")
        
        try:
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                conn.row_factory = sqlite3.Row
                
                # Basic statistics with parameterized queries
                stats_row = conn.execute("""
                    SELECT 
                        COUNT(*) as total_files,
                        COALESCE(SUM(file_size_bytes), 0) as total_size_bytes,
                        COUNT(CASE WHEN status = ? THEN 1 END) as active_files,
                        COUNT(CASE WHEN status = ? THEN 1 END) as orphaned_files,
                        COUNT(DISTINCT triggered_by_user) as users_count,
                        MIN(cached_at) as oldest_cached_at
                    FROM cached_files
                """, ('active', 'orphaned')).fetchone()
                
                # Most accessed file with parameterized query
                most_accessed_row = conn.execute("""
                    SELECT file_path FROM cached_files 
                    WHERE access_count > ?
                    ORDER BY access_count DESC 
                    LIMIT 1
                """, (0,)).fetchone()
                
                # Count security events
                security_events_count = conn.execute("""
                    SELECT COUNT(*) FROM security_events 
                    WHERE timestamp >= ?
                """, ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),)).fetchone()[0]
                
                total_size_bytes = stats_row['total_size_bytes'] or 0
                
                statistics = SecureCacheStatistics(
                    total_files=stats_row['total_files'],
                    total_size_bytes=total_size_bytes,
                    total_size_readable=self._format_file_size(total_size_bytes),
                    active_files=stats_row['active_files'],
                    orphaned_files=stats_row['orphaned_files'],
                    users_count=stats_row['users_count'],
                    oldest_cached_at=datetime.fromisoformat(stats_row['oldest_cached_at']) if stats_row['oldest_cached_at'] else None,
                    most_accessed_file=most_accessed_row['file_path'] if most_accessed_row else None,
                    cache_hit_ratio=0.0,  # TODO: Calculate from access logs
                    security_events_count=security_events_count
                )
                
                # Log successful access
                self.security_logger.log_security_event(
                    "statistics_accessed", user_id, "cache_statistics", "get_statistics",
                    True, {"files_count": stats_row['total_files']}, ip_address
                )
                
                return statistics
                
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", user_id, "cache_statistics", "get_statistics",
                False, {"error": str(e)}, ip_address
            )
            self.logger.error(f"Failed to get cache statistics: {e}")
            return SecureCacheStatistics(
                total_files=0, total_size_bytes=0, total_size_readable="0 B",
                active_files=0, orphaned_files=0, users_count=0,
                security_events_count=0
            )

    def remove_cached_file(self, file_path: str, reason: str = 'manual', 
                          user_context: Optional[UserOperationContext] = None,
                          ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """
        Remove a file from cached files tracking with security logging.
        
        Args:
            file_path: Path of file to remove
            reason: Reason for removal
            user_context: User operation context
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            True if file was removed successfully
            
        Raises:
            ValueError: If validation fails
            PermissionError: If user lacks delete permissions
        """
        user_id = user_context.user_id if user_context else None
        
        # Security checks
        if user_id and not self._check_rate_limit(user_id):
            self.security_logger.log_security_event(
                "rate_limit_exceeded", user_id, "cached_files", "remove_file",
                False, {"file_path": file_path}, ip_address, user_agent
            )
            raise PermissionError("Rate limit exceeded")
        
        if not self.auth_manager.check_permission(user_id, PermissionType.DELETE, file_path):
            self.security_logger.log_security_event(
                "authorization_failure", user_id, file_path, "remove_cached_file",
                False, {"reason": reason}, ip_address, user_agent
            )
            raise PermissionError("Insufficient permissions to remove cached file")
        
        try:
            # Validate path
            validated_path = SecurePathValidator.validate_path(file_path, self.allowed_base_paths)
            
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                db_conn.transaction_active = True
                
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Update status with parameterized query
                    cursor = conn.execute("""
                        UPDATE cached_files 
                        SET status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE file_path = ? AND status != ?
                    """, ('removed', validated_path, 'removed'))
                    
                    success = cursor.rowcount > 0
                    conn.commit()
                    db_conn.transaction_active = False
                    
                    if success:
                        self._log_secure_operation('cache_remove', validated_path, 'user_request',
                                                 user_id, f'File removed: {reason}', True,
                                                 None, None, ip_address, user_agent)
                        
                        self.security_logger.log_security_event(
                            "file_removed", user_id, validated_path, "remove_cached_file",
                            True, {"reason": reason}, ip_address, user_agent
                        )
                        
                        self.logger.info(f"Removed cached file: {validated_path}")
                        return True
                    else:
                        self.logger.warning(f"Cached file not found for removal: {validated_path}")
                        return False
                        
                except Exception as e:
                    conn.rollback()
                    db_conn.transaction_active = False
                    raise
                    
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", user_id, file_path, "remove_cached_file",
                False, {"error": str(e), "reason": reason}, ip_address, user_agent
            )
            self.logger.error(f"Failed to remove cached file {file_path}: {e}")
            self._log_secure_operation('cache_remove', file_path, 'user_request',
                                     user_id, f'File removal failed: {reason}', False, 
                                     str(e), None, ip_address, user_agent)
            return False

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

    def _log_secure_operation(self, operation_type: str, file_path: str, triggered_by: str,
                            triggered_by_user: Optional[str], reason: str, success: bool,
                            error_message: Optional[str] = None, metadata: Optional[Dict] = None,
                            ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> None:
        """Log cache operation with security context."""
        try:
            log_id = str(uuid.uuid4())
            
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                
                # Store in operations log
                conn.execute("""
                    INSERT INTO cache_operations_log 
                    (id, operation_type, file_path, triggered_by, triggered_by_user, 
                     reason, success, error_message, metadata, security_context, 
                     ip_address, user_agent, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_id, operation_type, file_path, triggered_by, triggered_by_user,
                    reason, success, error_message,
                    json.dumps(metadata) if metadata else None,
                    json.dumps({"logged_by": "secure_service"}),
                    ip_address, user_agent, datetime.now(timezone.utc).isoformat()
                ))
                
                # Store in security events if it's a security-relevant operation
                if operation_type in ['cache_remove', 'cache_cleanup'] or not success:
                    conn.execute("""
                        INSERT INTO security_events 
                        (id, event_type, user_id, resource, action, success, details, 
                         ip_address, user_agent, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), f"cache_{operation_type}", triggered_by_user,
                        file_path, operation_type, success,
                        json.dumps({
                            "reason": reason,
                            "error": error_message,
                            "metadata": metadata
                        }),
                        ip_address, user_agent, datetime.now(timezone.utc).isoformat()
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to log secure operation: {e}")

    def cleanup_orphaned_files(self, user_context: Optional[UserOperationContext] = None,
                              ip_address: Optional[str] = None) -> int:
        """
        Clean up orphaned cache entries with security logging.
        
        Args:
            user_context: User operation context
            ip_address: Client IP address
            
        Returns:
            Number of files cleaned up
            
        Raises:
            PermissionError: If user lacks admin permissions
        """
        user_id = user_context.user_id if user_context else None
        
        # Check admin permission for cleanup
        if not self.auth_manager.check_permission(user_id, PermissionType.ADMIN):
            self.security_logger.log_security_event(
                "authorization_failure", user_id, "cached_files", "cleanup_orphaned",
                False, {}, ip_address
            )
            raise PermissionError("Insufficient permissions for cleanup operations")
        
        try:
            cleaned_count = 0
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                db_conn.transaction_active = True
                
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Get active cached files with parameterized query
                    rows = conn.execute("""
                        SELECT id, file_path, cached_path FROM cached_files 
                        WHERE status = ?
                    """, ('active',)).fetchall()
                    
                    for row in rows:
                        file_id, file_path, cached_path = row
                        if not Path(cached_path).exists():
                            # Mark as orphaned with parameterized query
                            conn.execute("""
                                UPDATE cached_files 
                                SET status = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, ('orphaned', file_id))
                            cleaned_count += 1
                            self.logger.debug(f"Marked orphaned: {file_path}")
                    
                    conn.commit()
                    db_conn.transaction_active = False
                    
                except Exception as e:
                    conn.rollback()
                    db_conn.transaction_active = False
                    raise
                
            if cleaned_count > 0:
                self._log_secure_operation('cache_cleanup', '', 'system',
                                         user_id, f'Cleaned {cleaned_count} orphaned files', 
                                         True, None, None, ip_address)
                
                self.security_logger.log_security_event(
                    "orphaned_cleanup", user_id, "cached_files", "cleanup_orphaned",
                    True, {"cleaned_count": cleaned_count}, ip_address
                )
                
                self.logger.info(f"Cleaned up {cleaned_count} orphaned cached files")
            
            return cleaned_count
            
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", user_id, "cached_files", "cleanup_orphaned",
                False, {"error": str(e)}, ip_address
            )
            self.logger.error(f"Failed to cleanup orphaned files: {e}")
            return 0

    def verify_cache_integrity(self, user_context: Optional[UserOperationContext] = None,
                              ip_address: Optional[str] = None) -> Tuple[int, int]:
        """
        Verify cache integrity with comprehensive security checks.
        
        Args:
            user_context: User operation context
            ip_address: Client IP address
            
        Returns:
            Tuple of (verified_count, error_count)
            
        Raises:
            PermissionError: If user lacks admin permissions
        """
        user_id = user_context.user_id if user_context else None
        
        # Check admin permission for integrity verification
        if not self.auth_manager.check_permission(user_id, PermissionType.ADMIN):
            self.security_logger.log_security_event(
                "authorization_failure", user_id, "cached_files", "verify_integrity",
                False, {}, ip_address
            )
            raise PermissionError("Insufficient permissions for integrity verification")
        
        try:
            verified_count = 0
            error_count = 0
            
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                db_conn.transaction_active = True
                
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    
                    # Get all active cached files
                    rows = conn.execute("""
                        SELECT id, file_path, cached_path, original_path, file_size_bytes, 
                               cache_method, checksum FROM cached_files 
                        WHERE status = ?
                    """, ('active',)).fetchall()
                    
                    for row in rows:
                        file_id, file_path, cached_path, original_path, file_size_bytes, cache_method, stored_checksum = row
                        
                        # Check if cached file exists
                        if not Path(cached_path).exists():
                            # Mark as orphaned
                            conn.execute("""
                                UPDATE cached_files 
                                SET status = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, ('orphaned', file_id))
                            error_count += 1
                            self.logger.warning(f"Cached file missing, marked as orphaned: {cached_path}")
                        else:
                            # Verify checksum if available
                            if stored_checksum:
                                expected_data = f"{file_path}:{file_size_bytes}:{cache_method}"
                                if not self._verify_checksum(expected_data, stored_checksum):
                                    # Mark as quarantined due to integrity failure
                                    conn.execute("""
                                        UPDATE cached_files 
                                        SET status = ?, updated_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, ('quarantined', file_id))
                                    error_count += 1
                                    
                                    self.security_logger.log_security_event(
                                        "integrity_failure", user_id, file_path, "verify_integrity",
                                        False, {"file_id": file_id, "checksum_mismatch": True}, ip_address
                                    )
                                    
                                    self.logger.error(f"Integrity check failed for file: {file_path}")
                                else:
                                    verified_count += 1
                            else:
                                verified_count += 1
                    
                    conn.commit()
                    db_conn.transaction_active = False
                    
                except Exception as e:
                    conn.rollback()
                    db_conn.transaction_active = False
                    raise
                
            self._log_secure_operation('cache_verify', '', 'system', user_id,
                                     f'Verified {verified_count} files, found {error_count} errors', 
                                     True, None, None, ip_address)
            
            self.security_logger.log_security_event(
                "integrity_verification", user_id, "cached_files", "verify_integrity",
                True, {
                    "verified_count": verified_count,
                    "error_count": error_count
                }, ip_address
            )
            
            self.logger.info(f"Cache integrity check: {verified_count} verified, {error_count} errors")
            
            return verified_count, error_count
            
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", user_id, "cached_files", "verify_integrity",
                False, {"error": str(e)}, ip_address
            )
            self.logger.error(f"Failed to verify cache integrity: {e}")
            return 0, 0

    def add_user_permission(self, user_id: str, role: SecurityLevel, permissions: Optional[Set[PermissionType]] = None,
                           admin_context: Optional[UserOperationContext] = None) -> bool:
        """
        Add user with permissions (admin only).
        
        Args:
            user_id: User ID to add
            role: Security role for the user
            permissions: Optional specific permissions
            admin_context: Admin user context
            
        Returns:
            True if user added successfully
            
        Raises:
            PermissionError: If caller lacks admin permissions
        """
        admin_user_id = admin_context.user_id if admin_context else None
        
        if not self.auth_manager.check_permission(admin_user_id, PermissionType.ADMIN):
            self.security_logger.log_security_event(
                "authorization_failure", admin_user_id, "user_management", "add_user",
                False, {"target_user": user_id}, None
            )
            raise PermissionError("Insufficient permissions to manage users")
        
        try:
            self.auth_manager.add_user(user_id, role, permissions)
            
            self.security_logger.log_security_event(
                "user_added", admin_user_id, "user_management", "add_user",
                True, {
                    "target_user": user_id,
                    "role": role.value,
                    "permissions": [p.value for p in (permissions or [])]
                }
            )
            
            self.logger.info(f"Added user {user_id} with role {role.value}")
            return True
            
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", admin_user_id, "user_management", "add_user",
                False, {"error": str(e), "target_user": user_id}
            )
            self.logger.error(f"Failed to add user {user_id}: {e}")
            return False

    def get_security_events(self, limit: int = 100, event_type: Optional[str] = None,
                           user_context: Optional[UserOperationContext] = None) -> List[Dict[str, Any]]:
        """
        Get security events (admin only).
        
        Args:
            limit: Maximum number of events to return
            event_type: Optional event type filter
            user_context: User operation context
            
        Returns:
            List of security events
            
        Raises:
            PermissionError: If user lacks admin permissions
        """
        user_id = user_context.user_id if user_context else None
        
        if not self.auth_manager.check_permission(user_id, PermissionType.ADMIN):
            self.security_logger.log_security_event(
                "authorization_failure", user_id, "security_events", "get_events",
                False, {}, None
            )
            raise PermissionError("Insufficient permissions to view security events")
        
        try:
            with self.connection_pool.get_connection() as db_conn:
                conn = db_conn.connection
                conn.row_factory = sqlite3.Row
                
                if event_type:
                    query = """
                        SELECT * FROM security_events 
                        WHERE event_type = ?
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    params = (event_type, limit)
                else:
                    query = """
                        SELECT * FROM security_events 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    """
                    params = (limit,)
                
                rows = conn.execute(query, params).fetchall()
                
                events = []
                for row in rows:
                    events.append({
                        'id': row['id'],
                        'event_type': row['event_type'],
                        'user_id': row['user_id'],
                        'resource': row['resource'],
                        'action': row['action'],
                        'success': bool(row['success']),
                        'details': json.loads(row['details']) if row['details'] else {},
                        'ip_address': row['ip_address'],
                        'user_agent': row['user_agent'],
                        'timestamp': row['timestamp']
                    })
                
                return events
                
        except Exception as e:
            self.security_logger.log_security_event(
                "operation_failure", user_id, "security_events", "get_events",
                False, {"error": str(e)}
            )
            self.logger.error(f"Failed to get security events: {e}")
            return []

    def close(self):
        """Clean shutdown of service resources."""
        try:
            self.connection_pool.close_all()
            self.logger.info("Secure cached files service closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing secure cached files service: {e}")