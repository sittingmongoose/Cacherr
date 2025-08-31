# 🚀 Cacherr Configuration Migration Guide

## Overview

The Cacherr Configuration Migration Script (`src/config/migration_script.py`) provides comprehensive migration functionality for transitioning from legacy configuration systems to the modern Pydantic v2.5 configuration architecture.

## What It Does

The migration script handles:

### ✅ Environment Variable Migration
- Migrates old `PLEXCACHE_*` variables to new `CACHERR_*` variables
- Handles various legacy prefixes (`PLEXCACHEULTRA_*`, etc.)
- Preserves backward compatibility during transition

### ✅ Persistent Configuration Migration
- Detects legacy configuration files (`plexcache_config.json`, `old_settings.json`, etc.)
- Transforms legacy configuration formats to modern structure
- Validates migrated data against Pydantic v2.5 models
- Creates new unified configuration file

### ✅ Configuration Validation
- Validates migrated configuration against modern models
- Provides detailed error reporting for any issues
- Ensures configuration compatibility

### ✅ Legacy Cleanup
- Backs up legacy files before removal
- Cleans up deprecated configuration files
- Generates comprehensive migration reports

## Usage

### Basic Migration
```bash
# Run migration with default settings
python -m src.config.migration_script

# Run migration for specific config directory
python -m src.config.migration_script --config-dir /path/to/config
```

### Safe Migration (Recommended)
```bash
# Dry run to see what would be migrated
python -m src.config.migration_script --dry-run

# Verbose output for detailed information
python -m src.config.migration_script --dry-run --verbose
```

### Advanced Options
```bash
# Force migration even if validation fails
python -m src.config.migration_script --force

# Custom configuration directory
python -m src.config.migration_script --config-dir /custom/config/path
```

## Migration Examples

### Environment Variables
**Before:**
```bash
export PLEXCACHE_CONFIG_DIR=/config
export PLEXCACHE_DEBUG=true
export PLEXCACHE_WEB_HOST=localhost
```

**After Migration:**
```bash
export CACHERR_CONFIG_DIR=/config  # Migrated from PLEXCACHE_CONFIG_DIR
export CACHERR_DEBUG=true          # Migrated from PLEXCACHE_DEBUG
export CACHERR_WEB_HOST=localhost  # Migrated from PLEXCACHE_WEB_HOST
```

### Configuration Files
**Legacy File:** `plexcache_config.json`
```json
{
  "plex": {
    "url": "http://plex.example.com:32400",
    "token": "old-token-format"
  },
  "media": {
    "copy_to_cache": true
  }
}
```

**Migrated File:** `cacherr_config.json`
```json
{
  "plex": {
    "url": "http://plex.example.com:32400",
    "token": "old-token-format",
    "timeout": 30,
    "verify_ssl": true
  },
  "media": {
    "copy_to_cache": true,
    "delete_from_cache_when_done": true,
    "file_extensions": ["mp4", "mkv", "avi", "mov"]
  },
  "performance": {
    "max_concurrent_moves_cache": 3,
    "max_concurrent_moves_array": 1
  }
}
```

## Migration Report

After migration, the script generates a detailed report at `config/migration_report.json`:

```json
{
  "migration_timestamp": "1756668282.6802902",
  "success_rate": 100.0,
  "statistics": {
    "total_operations": 5,
    "successful_operations": 4,
    "failed_operations": 0,
    "skipped_operations": 1
  },
  "warnings": [],
  "errors": [],
  "dry_run": false,
  "migrated_environment_variables": [
    "PLEXCACHE_CONFIG_DIR -> CACHERR_CONFIG_DIR",
    "PLEXCACHE_DEBUG -> CACHERR_DEBUG"
  ],
  "configuration_status": "validated"
}
```

## Safety Features

### 🛡️ Backup Strategy
- All legacy files are backed up before modification
- Original files are preserved with `.backup` extension
- Easy rollback if migration issues occur

### 🛡️ Dry Run Mode
- Test migration without making actual changes
- Preview all operations that would be performed
- Safe way to verify migration plan

### 🛡️ Validation
- All migrated configuration is validated against modern models
- Detailed error reporting for any validation failures
- Migration stops if critical validation errors occur

### 🛡️ Rollback Support
- Migration logs provide clear rollback instructions
- Backup files enable easy restoration
- Comprehensive error reporting for troubleshooting

## Troubleshooting

### Common Issues

**Migration fails with validation errors:**
```bash
# Check validation errors in detail
python -m src.config.migration_script --dry-run --verbose

# Force migration (use with caution)
python -m src.config.migration_script --force
```

**Environment variables not migrating:**
```bash
# Check current environment
env | grep PLEX

# Manual migration if needed
export CACHERR_CONFIG_DIR=$PLEXCACHE_CONFIG_DIR
```

**Configuration files not found:**
```bash
# Check if files exist in expected location
ls -la /config/

# Specify custom config directory
python -m src.config.migration_script --config-dir /custom/path
```

### Rollback Procedure

If migration encounters issues:

1. **Check migration logs:**
   ```bash
   cat config_migration.log
   ```

2. **Check migration report:**
   ```bash
   cat config/migration_report.json
   ```

3. **Restore from backups:**
   ```bash
   # Restore backed up configuration files
   find /config -name "*.backup" -exec bash -c 'mv "$1" "${1%.backup}"' _ {} \;
   ```

4. **Restore environment variables:**
   ```bash
   # Revert to old variable names if needed
   export PLEXCACHE_CONFIG_DIR=$CACHERR_CONFIG_DIR
   ```

## Integration with Cacherr

The migration script is designed to work seamlessly with the modern Cacherr configuration system:

- **Pydantic v2.5 Compatible**: Uses the same models and validation as the main application
- **Environment Variable Support**: Handles the same environment variables as Cacherr
- **Configuration File Format**: Produces files compatible with Cacherr's config loading
- **Error Handling**: Uses the same error handling patterns as the main application

## Best Practices

1. **Always run dry-run first** to understand what will be migrated
2. **Backup important configuration** before running migration
3. **Test migrated configuration** after migration completes
4. **Review migration report** for any warnings or errors
5. **Keep migration logs** for troubleshooting and auditing

## Technical Details

### Architecture
- **Python-based**: Pure Python implementation, no external dependencies
- **Pydantic Integration**: Leverages the same Pydantic models as the main application
- **Modular Design**: Separate phases for different migration aspects
- **Comprehensive Logging**: Detailed logging for auditing and troubleshooting

### Performance
- **Lazy Loading**: Configuration is loaded only when needed
- **Efficient Processing**: Minimal memory usage for large configuration files
- **Fast Validation**: Optimized validation using Pydantic v2.5 features
- **Background Processing**: Non-blocking operations where possible

### Security
- **No Credential Exposure**: Sensitive data is handled securely
- **Permission Validation**: Checks file permissions before operations
- **Safe File Operations**: Atomic file operations to prevent corruption
- **Audit Trail**: Comprehensive logging of all operations

---

## Quick Start

```bash
# 1. Preview migration (recommended)
python -m src.config.migration_script --dry-run --verbose

# 2. Run actual migration
python -m src.config.migration_script

# 3. Verify results
cat config/migration_report.json

# 4. Test application
python main.py
```

The migration script ensures a smooth transition from legacy configuration systems to the modern, robust Cacherr configuration architecture.
