# Configuration API Endpoints

## Overview

The Cacherr configuration API provides comprehensive endpoints for managing application settings with **Pydantic v2** validation, real-time error checking, and type-safe configuration management.

## Key Features

- **🛡️ Real-time Validation**: All configuration updates validated using Pydantic v2 models
- **⚡ Type Safety**: Automatic type conversion and constraint validation
- **🔧 Detailed Error Reporting**: Specific field-level validation errors with helpful messages
- **📝 Self-Documenting**: API responses include validation summaries and configuration schemas
- **🔄 Atomic Updates**: Configuration changes applied atomically with rollback on validation failure

## Endpoints

### `GET /api/settings`

Retrieve the complete current configuration.

**Response Structure:**
```json
{
  "success": true,
  "data": {
    "plex": {
      "url": "https://plex.example.com:32400",
      "token": "***",
      "username": null,
      "password": null
    },
    "media": {
      "copy_to_cache": true,
      "delete_from_cache_when_done": true,
      "watched_move": true,
      "users_toggle": true,
      "watchlist_toggle": true,
      "exit_if_active_session": false,
      "days_to_monitor": 99,
      "number_episodes": 5,
      "watchlist_episodes": 1,
      "cache_mode_description": "Copy to cache (preserves originals)"
    },
    "paths": {
      "plex_source": "/media",
      "cache_destination": "/cache",
      "additional_sources": ["/nas1", "/nas2"],
      "additional_plex_sources": ["/nas1", "/nas2"]
    },
    "performance": {
      "max_concurrent_moves_cache": 3,
      "max_concurrent_moves_array": 1,
      "max_concurrent_local_transfers": 3,
      "max_concurrent_network_transfers": 1
    },
    "real_time_watch": {
      "enabled": false,
      "check_interval": 30,
      "auto_cache_on_watch": true,
      "cache_on_complete": true,
      "respect_existing_rules": true,
      "max_concurrent_watches": 5,
      "remove_from_cache_after_hours": 24,
      "respect_other_users_watchlists": true,
      "exclude_inactive_users_days": 30
    },
    "trakt": {
      "enabled": false,
      "client_id": "",
      "client_secret": "***",
      "trending_movies_count": 10,
      "check_interval": 3600
    },
    "web": {
      "host": "0.0.0.0",
      "port": 5445,
      "debug": false,
      "enable_scheduler": false
    },
    "test_mode": {
      "enabled": false,
      "show_file_sizes": true,
      "show_total_size": true,
      "dry_run": false
    },
    "notifications": {
      "webhook_url": null,
      "webhook_headers": {}
    },
    "logging": {
      "level": "INFO",
      "max_files": 3,
      "max_size_mb": 10
    }
  }
}
```

### `POST /api/settings`

Update configuration settings with comprehensive Pydantic v2 validation.

**Request Structure:**
```json
{
  "media": {
    "copy_to_cache": true,
    "delete_from_cache_when_done": true,
    "number_episodes": 5
  },
  "performance": {
    "max_concurrent_moves_cache": 3,
    "max_concurrent_network_transfers": 1
  },
  "plex": {
    "url": "https://plex.example.com:32400",
    "token": "your_plex_token_here"
  }
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Settings updated successfully",
  "data": {
    "updated_sections": ["media", "performance", "plex"],
    "validation_summary": {
      "valid": true,
      "error_count": 0,
      "sections_count": 3,
      "key_settings": {
        "copy_to_cache": true,
        "cache_mode": "Copy to cache (preserves originals)",
        "plex_url": "https://plex.example.com:32400",
        "cache_destination": "/cache",
        "max_concurrent_cache": 3,
        "log_level": "INFO",
        "debug_mode": false
      }
    }
  }
}
```

**Validation Error Response:**
```json
{
  "success": false,
  "error": "Invalid settings: Invalid performance configuration: [{'type': 'greater_than', 'loc': ('max_concurrent_moves_cache',), 'msg': 'Input should be greater than 0', 'input': -1}]"
}
```

### `POST /api/settings/validate`

Validate configuration settings without applying them.

**Request Structure:**
```json
{
  "media": {
    "copy_to_cache": "invalid_boolean",
    "number_episodes": -5
  },
  "plex": {
    "url": "not_a_valid_url"
  }
}
```

**Validation Response:**
```json
{
  "success": true,
  "data": {
    "valid": false,
    "errors": [
      "Invalid media configuration: Input should be a valid boolean, unable to interpret input",
      "Invalid media configuration: Input should be greater than 0",
      "Invalid plex configuration: Input should be a valid URL"
    ],
    "warnings": [],
    "sections": {
      "media": {
        "valid": false,
        "errors": [
          "Input should be a valid boolean, unable to interpret input",
          "Input should be greater than 0"
        ],
        "model_class": "MediaConfig"
      },
      "plex": {
        "valid": false,
        "errors": [
          "Input should be a valid URL"
        ],
        "model_class": "PlexConfig"
      }
    },
    "message": "Validation failed: Invalid media configuration: [{'type': 'bool_parsing', 'loc': ('copy_to_cache',), 'msg': 'Input should be a valid boolean, unable to interpret input', 'input': 'invalid_boolean'}]"
  }
}
```

### `POST /api/settings/reset`

Reset all configuration settings to Pydantic model defaults.

**Response:**
```json
{
  "success": true,
  "message": "Configuration reset to default values",
  "data": {
    "reset_sections": ["media", "performance", "test_mode", "real_time_watch", "trakt"],
    "validation_summary": {
      "valid": true,
      "error_count": 0,
      "sections_count": 9,
      "key_settings": {
        "copy_to_cache": true,
        "cache_mode": "Copy to cache (preserves originals)",
        "max_concurrent_cache": 3,
        "log_level": "INFO",
        "debug_mode": false
      }
    }
  }
}
```

## Validation Rules

### Media Configuration

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `copy_to_cache` | `bool` | - | `true` | Copy files to cache instead of moving |
| `delete_from_cache_when_done` | `bool` | - | `true` | Delete from cache when operation complete |
| `watched_move` | `bool` | - | `true` | Move watched content to array |
| `users_toggle` | `bool` | - | `true` | Enable multi-user support |
| `exit_if_active_session` | `bool` | - | `false` | Exit if active Plex sessions detected |
| `days_to_monitor` | `int` | `> 0` | `99` | Days to monitor for user activity |
| `number_episodes` | `int` | `> 0` | `5` | Number of episodes to cache |
| `watchlist_episodes` | `int` | `> 0` | `1` | Watchlist episodes to cache |

### Plex Configuration

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `url` | `HttpUrl` | Valid HTTP/HTTPS URL | Plex server URL |
| `token` | `str` | `min_length=20` | Plex authentication token |
| `username` | `str` (optional) | - | Plex username (alternative auth) |
| `password` | `str` (optional) | - | Plex password (alternative auth) |

### Performance Configuration

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| `max_concurrent_moves_cache` | `int` | `> 0, <= 10` | `3` | Max concurrent cache operations |
| `max_concurrent_moves_array` | `int` | `> 0, <= 5` | `1` | Max concurrent array operations |
| `max_concurrent_local_transfers` | `int` | `> 0, <= 10` | `3` | Max concurrent local transfers |
| `max_concurrent_network_transfers` | `int` | `> 0, <= 5` | `1` | Max concurrent network transfers |

### Paths Configuration

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `plex_source` | `str` | Valid directory path | Plex media source directory |
| `cache_destination` | `str` | Valid directory path | Cache destination directory |
| `additional_sources` | `List[str]` | Environment-only | Additional source directories |
| `additional_plex_sources` | `List[str]` | Environment-only | Additional Plex source directories |

## Error Handling

### Validation Error Types

1. **Type Validation**: Invalid data types (e.g., string for boolean)
2. **Constraint Validation**: Values outside valid ranges (e.g., negative integers)
3. **Format Validation**: Invalid formats (e.g., malformed URLs)
4. **Required Field**: Missing required fields
5. **Business Logic**: Cross-field validation failures

### Error Response Format

All validation errors include:
- **Field Location**: Exact field path that failed validation
- **Error Type**: Specific validation rule that failed
- **Error Message**: Human-readable description
- **Input Value**: The invalid value that was provided
- **Model Context**: Which Pydantic model performed the validation

## Configuration Persistence

### Persistent Storage
- **File Location**: `/config/cacherr_config.json`
- **Format**: JSON with nested configuration sections
- **Atomic Updates**: Configuration changes applied atomically
- **Backup Strategy**: Previous configuration backed up before updates

### Priority Hierarchy
1. **Web GUI Overrides** (persistent JSON file)
2. **Environment Variables** (Docker/system)
3. **`.env` File Values**
4. **Pydantic Model Defaults**

## Security Considerations

### Sensitive Data Handling
- Passwords and tokens are masked in API responses (`***`)
- Sensitive fields use Pydantic `SecretStr` type for secure handling
- API logs exclude sensitive configuration values

### Input Validation
- All input sanitized through Pydantic validation
- SQL injection prevention through type safety
- Path traversal protection via path validation
- URL validation prevents malicious endpoints

### Access Control
- Configuration endpoints require proper authentication
- Write operations restricted to authorized users
- Read operations may expose masked sensitive data

## Example Usage

### Update Cache Mode via API
```bash
curl -X POST http://localhost:5445/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "media": {
      "copy_to_cache": true,
      "delete_from_cache_when_done": true
    }
  }'
```

### Validate Performance Settings
```bash
curl -X POST http://localhost:5445/api/settings/validate \
  -H "Content-Type: application/json" \
  -d '{
    "performance": {
      "max_concurrent_moves_cache": 5,
      "max_concurrent_network_transfers": 2
    }
  }'
```

### Reset to Defaults
```bash
curl -X POST http://localhost:5445/api/settings/reset
```

This comprehensive API documentation ensures developers can effectively interact with the modern Pydantic v2 configuration system while understanding validation rules, error handling, and security considerations.
