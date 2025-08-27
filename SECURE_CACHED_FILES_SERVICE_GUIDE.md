# SecureCachedFilesService - Security Implementation Guide

## Overview

The `SecureCachedFilesService` is a comprehensive rewrite of the original `CachedFilesService` with enterprise-grade security hardening. This implementation addresses all critical security vulnerabilities identified in the production audit and implements defense-in-depth security practices.

## 🛡️ Security Features

### 1. SQL Injection Prevention
- **Parameterized Queries**: All database operations use parameterized queries instead of string concatenation
- **Query Validation**: Input validation before query execution
- **Database Constraints**: Schema-level constraints for additional protection

**Example**:
```python
# OLD (Vulnerable):
cursor.execute(f"SELECT * FROM cached_files WHERE user_id = '{user_id}'")

# NEW (Secure):
cursor.execute("SELECT * FROM cached_files WHERE user_id = ?", (user_id,))
```

### 2. Path Traversal Protection
- **Path Validation**: Comprehensive validation against directory traversal patterns
- **Allowed Base Paths**: Whitelist of allowed directory structures
- **Path Sanitization**: Automatic path normalization and resolution

**Protected Patterns**:
- `../`, `..\\`, `/..`, `\\..`
- `.//`, `.\\`, `./`, `.\\`
- Null bytes and other dangerous characters

**Example**:
```python
# Validates and sanitizes paths
validated_path = SecurePathValidator.validate_path(user_path, allowed_base_paths)
```

### 3. Authorization Framework
- **Role-Based Access Control**: Admin, User, and Public security levels
- **Permission Types**: Read, Write, Delete, and Admin permissions
- **Resource-Level Security**: Per-operation authorization checks

**Security Levels**:
- `ADMIN`: Full system access including cleanup and user management
- `USER`: Read/write access to cached files
- `PUBLIC`: Read-only access to statistics and file listings

### 4. Database Connection Management
- **Connection Pooling**: Thread-safe connection pool with configurable limits
- **Resource Cleanup**: Automatic connection cleanup and timeout handling
- **Transaction Management**: Proper transaction isolation and rollback

**Features**:
- Maximum connection limits to prevent resource exhaustion
- Connection reuse for improved performance
- Automatic cleanup of stale connections

### 5. Race Condition Prevention
- **Atomic Transactions**: All operations use `BEGIN IMMEDIATE` transactions
- **Lock Management**: Thread-safe operations with proper locking
- **Isolation Levels**: Proper transaction isolation to prevent data corruption

### 6. Enhanced Input Validation
- **Pydantic v2.5**: Comprehensive field validation with security-focused constraints
- **Size Limits**: Maximum sizes for paths, filenames, and metadata
- **Character Validation**: Whitelist-based character validation
- **Data Sanitization**: Automatic sanitization of user inputs

**Validation Rules**:
- File paths: Max 4096 characters, no dangerous patterns
- Filenames: Max 255 characters, alphanumeric + safe characters only
- Metadata: Max 64KB serialized size
- User IDs: Alphanumeric + safe characters only

### 7. Security Logging and Audit
- **Comprehensive Audit Trail**: All security-relevant events logged
- **Structured Logging**: Machine-readable security event format
- **Event Classification**: Different event types for analysis
- **Retention**: Configurable log retention policies

**Logged Events**:
- Authentication attempts
- Authorization failures
- File operations
- System access
- Configuration changes
- Integrity violations

### 8. Rate Limiting
- **Per-User Limits**: Configurable rate limits per user
- **Time Windows**: Sliding window rate limiting
- **DDoS Protection**: Automatic blocking of excessive requests

**Default Limits**:
- 100 requests per 60-second window per user
- Automatic cleanup of expired tracking data

## 🔧 Implementation Details

### Database Schema Enhancements

The secure service uses an enhanced database schema with security constraints:

```sql
-- Enhanced cached_files table with constraints
CREATE TABLE cached_files (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    original_path TEXT NOT NULL,
    cached_path TEXT NOT NULL,
    cache_method TEXT NOT NULL CHECK(cache_method IN ('atomic_symlink', 'atomic_hardlink', 'atomic_copy', 'secure_copy')),
    file_size_bytes INTEGER NOT NULL CHECK(file_size_bytes >= 0 AND file_size_bytes <= 1000000000000),
    -- ... additional security constraints
);

-- Security events table for audit trail
CREATE TABLE security_events (
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
);
```

### Security Context

Every operation includes security context information:

```python
security_context = {
    'added_by': user_id or 'system',
    'ip_address': ip_address or 'unknown',
    'user_agent': user_agent or 'unknown',
    'timestamp': datetime.now(timezone.utc).isoformat()
}
```

### Integrity Verification

Files include HMAC checksums for integrity verification:

```python
def _generate_checksum(self, data: str) -> str:
    return hmac.new(
        self.security_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
```

## 📋 Migration Guide

### Prerequisites

1. **Backup**: Create backups of existing database and configuration
2. **Dependencies**: Ensure all required packages are installed
3. **Permissions**: Verify file system permissions for new security model
4. **Configuration**: Prepare security configuration (keys, allowed paths)

### Step 1: Prepare Environment

```bash
# Install additional dependencies for secure service
pip install cryptography

# Create backup
cp /path/to/current/cache.db /path/to/current/cache.db.backup
```

### Step 2: Run Migration Script

```bash
python src/core/migrate_to_secure_service.py \
    --source-db /path/to/current/cache.db \
    --target-db /path/to/secure/cache.db \
    --allowed-paths "/media" "/cache" "/plex" \
    --security-key "your-secure-key-here" \
    --output-report migration_report.json
```

### Step 3: Verify Migration

```python
from core.secure_cached_files_service import SecureCachedFilesService

# Initialize secure service
service = SecureCachedFilesService("/path/to/secure/cache.db")

# Verify integrity
admin_context = UserOperationContext(user_id="admin", trigger_source="verification")
verified, errors = service.verify_cache_integrity(admin_context)

print(f"Verified: {verified}, Errors: {errors}")
```

### Step 4: Update Application Code

Replace old service initialization:

```python
# OLD
from core.cached_files_service import CachedFilesService
service = CachedFilesService("/path/to/cache.db")

# NEW
from core.secure_cached_files_service import SecureCachedFilesService
service = SecureCachedFilesService(
    database_path="/path/to/secure/cache.db",
    allowed_base_paths=["/media", "/cache", "/plex"],
    security_key=os.environ.get("CACHE_SECURITY_KEY")
)

# Set up users
service.auth_manager.add_user("admin", SecurityLevel.ADMIN)
service.auth_manager.add_user("plex_user", SecurityLevel.USER)
```

## 🔐 Security Configuration

### Environment Variables

```bash
# Required security configuration
export CACHE_SECURITY_KEY="your-256-bit-secret-key"
export CACHE_ALLOWED_PATHS="/media:/cache:/plex"
export CACHE_MAX_CONNECTIONS="10"
export CACHE_RATE_LIMIT_REQUESTS="100"
export CACHE_RATE_LIMIT_WINDOW="60"
```

### User Management

```python
# Set up user permissions
admin_context = UserOperationContext(user_id="system", trigger_source="setup")

# Add admin user
service.add_user_permission("admin_user", SecurityLevel.ADMIN, None, admin_context)

# Add regular user with specific permissions
service.add_user_permission(
    "plex_user", 
    SecurityLevel.USER, 
    {PermissionType.READ, PermissionType.WRITE}, 
    admin_context
)

# Add read-only user
service.add_user_permission("readonly_user", SecurityLevel.PUBLIC, None, admin_context)
```

### Security Monitoring

```python
# Monitor security events
events = service.get_security_events(
    limit=100, 
    event_type="authorization_failure",
    user_context=admin_context
)

for event in events:
    if not event['success']:
        print(f"Security Alert: {event['event_type']} by {event['user_id']}")
```

## 🚨 Security Best Practices

### 1. Key Management
- **Unique Keys**: Generate unique HMAC keys for each environment
- **Key Rotation**: Implement regular key rotation procedures
- **Secure Storage**: Store keys in secure environment variables or key management systems

### 2. Path Configuration
- **Minimal Paths**: Configure only necessary allowed base paths
- **Regular Audits**: Regularly audit and update allowed paths
- **Sandbox Principle**: Use the most restrictive path configuration possible

### 3. User Management
- **Principle of Least Privilege**: Grant minimum required permissions
- **Regular Reviews**: Regularly review and audit user permissions
- **Account Lifecycle**: Implement proper account creation and deletion procedures

### 4. Monitoring
- **Security Events**: Monitor security events for suspicious activity
- **Performance Metrics**: Monitor for performance anomalies that might indicate attacks
- **Log Analysis**: Implement automated log analysis for security events

### 5. Database Security
- **Connection Limits**: Set appropriate connection pool limits
- **Backup Encryption**: Encrypt database backups
- **Access Control**: Restrict database file access at OS level

## 🧪 Testing Security

### Unit Tests

Run the comprehensive security test suite:

```bash
python -m pytest tests/test_secure_cached_files_service.py -v
```

### Security Test Categories

1. **Path Traversal Tests**: Verify protection against directory traversal
2. **SQL Injection Tests**: Confirm parameterized query protection
3. **Authorization Tests**: Validate access control enforcement
4. **Rate Limiting Tests**: Check rate limiting functionality
5. **Integrity Tests**: Verify data integrity checks
6. **Concurrent Access Tests**: Test thread safety and connection pooling

### Manual Security Testing

```python
# Test path traversal protection
try:
    service.add_cached_file("../../../etc/passwd", ...)
    assert False, "Should have failed"
except ValueError as e:
    assert "dangerous pattern" in str(e)

# Test authorization
readonly_context = UserOperationContext(user_id="readonly", trigger_source="test")
try:
    service.add_cached_file(..., user_context=readonly_context)
    assert False, "Should have failed"
except PermissionError:
    pass  # Expected

# Test rate limiting
for i in range(150):  # Exceed limit
    try:
        service.get_cached_files(user_context=user_context)
    except PermissionError as e:
        if "rate limit" in str(e):
            break
else:
    assert False, "Rate limiting should have triggered"
```

## 📊 Performance Considerations

### Connection Pooling
- **Pool Size**: Configure based on expected concurrent users
- **Timeout Settings**: Set appropriate connection timeouts
- **Monitoring**: Monitor pool utilization and performance

### Database Optimization
- **Indexes**: Comprehensive indexes for security and performance
- **Vacuum**: Regular database maintenance and optimization
- **WAL Mode**: Write-Ahead Logging for better concurrency

### Memory Management
- **Cache Sizes**: Configure appropriate SQLite cache sizes
- **Rate Limiter**: Automatic cleanup of expired rate limit data
- **Log Retention**: Implement log rotation and cleanup

## 🆘 Troubleshooting

### Common Issues

#### 1. Path Validation Failures
```
Error: "Path contains dangerous pattern"
Solution: Check for path traversal patterns in file paths
```

#### 2. Permission Denied Errors
```
Error: "Insufficient permissions"
Solution: Verify user has required permissions for the operation
```

#### 3. Rate Limit Exceeded
```
Error: "Rate limit exceeded"
Solution: Check rate limiting configuration or implement backoff
```

#### 4. Database Connection Issues
```
Error: Connection pool timeout
Solution: Increase max_connections or optimize database queries
```

### Debugging Security Issues

Enable detailed security logging:

```python
import logging
logging.getLogger('security').setLevel(logging.DEBUG)

# Monitor security events in real-time
service.security_logger.log_security_event(
    "debug_session", "admin", "system", "debug_start", True, 
    {"debug_info": "Starting security debug session"}
)
```

### Recovery Procedures

#### Rollback Migration
```bash
python rollback_migration.py  # Generated during migration
```

#### Reset User Permissions
```python
# Clear and reset user permissions
service.auth_manager = AuthorizationManager()
service._setup_default_users()
```

#### Database Corruption Recovery
```python
# Run integrity verification
verified, errors = service.verify_cache_integrity(admin_context)

# Check security events for corruption indicators
events = service.get_security_events(event_type="integrity_failure")
```

## 📚 API Reference

### Core Classes

#### `SecureCachedFilesService`
Main service class with all security features.

**Methods**:
- `add_cached_file()`: Add file with security validation
- `get_cached_files()`: Retrieve files with authorization
- `remove_cached_file()`: Remove file with audit logging
- `verify_cache_integrity()`: Check data integrity
- `cleanup_orphaned_files()`: Admin-only cleanup
- `get_security_events()`: Admin-only security audit

#### `SecurePathValidator`
Path validation and sanitization utilities.

**Methods**:
- `validate_path()`: Validate and sanitize file paths
- `validate_filename()`: Validate filenames

#### `AuthorizationManager`
User permission and role management.

**Methods**:
- `add_user()`: Add user with permissions
- `check_permission()`: Verify user permissions
- `get_user_role()`: Get user security level

### Security Models

#### `SecureCachedFileInfo`
Enhanced cached file information with security validation.

#### `SecurityEvent`
Security event for audit logging.

#### `UserOperationContext`
User context for all operations.

## 🎯 Next Steps

1. **Deploy in Staging**: Test the secure service in a staging environment
2. **Performance Testing**: Conduct load testing with security features enabled
3. **Security Audit**: Have the implementation reviewed by security experts
4. **Documentation Updates**: Update all application documentation
5. **Training**: Train team members on the new security features
6. **Monitoring Setup**: Implement security monitoring and alerting

## 📞 Support

For security-related issues or questions:

1. **Check Logs**: Review security event logs first
2. **Run Tests**: Execute the security test suite
3. **Documentation**: Refer to this guide and inline documentation
4. **Issue Reporting**: Report security issues through secure channels

---

**⚠️ Security Notice**: This implementation follows security best practices, but security is an ongoing process. Regularly review and update security configurations, monitor for new threats, and keep dependencies updated.