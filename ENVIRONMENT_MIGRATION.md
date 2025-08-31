# 🔄 ENVIRONMENT VARIABLE MIGRATION GUIDE

## Overview

With the project rename from PlexCacheUltra to Cacherr, environment variable names have changed to maintain consistency and follow the new naming convention. This guide provides comprehensive instructions for migrating your environment variables from the old patterns to the new CACHERR_* pattern.

## Migration Mapping

### Required Changes

| Old Variable | New Variable | Description | Required |
|--------------|--------------|-------------|----------|
| `PLEXCACHE_CONFIG_DIR` | `CACHERR_CONFIG_DIR` | Configuration directory | Optional |
| `PLEXCACHE_DATA_DIR` | `CACHERR_DATA_DIR` | Data directory | Optional |
| `PLEXCACHE_LOG_LEVEL` | `CACHERR_LOG_LEVEL` | Logging level | Optional |
| `PLEXCACHE_DEBUG` | `CACHERR_DEBUG` | Debug mode | Optional |
| `PLEXCACHE_ENVIRONMENT` | `CACHERR_ENVIRONMENT` | Runtime environment | Optional |
| `PLEX_URL` | `CACHERR_PLEX_URL` | Plex server URL | Optional* |
| `PLEX_TOKEN` | `CACHERR_PLEX_TOKEN` | Plex authentication token | Optional* |

*These variables are optional because most configuration should now be done via the web UI. Environment variables are provided for backward compatibility and advanced use cases.

### New Environment Variables

| New Variable | Description | Default Value | Required |
|--------------|-------------|---------------|----------|
| `CACHERR_ENVIRONMENT` | Runtime environment | `production` | Yes |
| `CACHERR_CONFIG_DIR` | Configuration directory | `./config` | No |
| `CACHERR_DATA_DIR` | Data directory | `./data` | No |
| `CACHERR_LOG_LEVEL` | Logging level | `INFO` | No |
| `CACHERR_DEBUG` | Enable debug mode | `false` | No |
| `CACHERR_PLEX_URL` | Plex server URL | None | No* |
| `CACHERR_PLEX_TOKEN` | Plex token | None | No* |

*Prefer configuring Plex settings via the web UI rather than environment variables.

## Migration Steps

### Step 1: Stop Your Current Container

Before making changes, stop your running Cacherr container:

```bash
docker-compose down
```

### Step 2: Update Environment Variables

#### For Docker Compose Users

**File**: `docker-compose.yml`

```yaml
# OLD - Remove these legacy variables
environment:
  - PLEX_URL=${PLEX_URL:-}
  - PLEX_TOKEN=${PLEX_TOKEN:-}
  # Remove any PLEXCACHE_* variables if present

# NEW - Use these instead (if needed)
environment:
  - CACHERR_ENVIRONMENT=production
  - CACHERR_CONFIG_DIR=${CACHERR_CONFIG_DIR:-./config}
  - CACHERR_LOG_LEVEL=${LOG_LEVEL:-INFO}
  # Only if you prefer env vars over web UI:
  - CACHERR_PLEX_URL=${PLEX_URL:-}
  - CACHERR_PLEX_TOKEN=${PLEX_TOKEN:-}
```

#### For .env File Users

**File**: `.env`

```bash
# OLD - Remove or rename these
PLEX_URL=http://192.168.1.100:32400
PLEX_TOKEN=your_plex_token_here

# NEW - Use these instead
CACHERR_ENVIRONMENT=production
CACHERR_PLEX_URL=http://192.168.1.100:32400
CACHERR_PLEX_TOKEN=your_plex_token_here
LOG_LEVEL=INFO
```

#### For Unraid Template Users

The Unraid template has been updated automatically. Most settings should now be configured via the web interface rather than environment variables. The template now uses minimal environment variables:

```xml
<!-- Minimal environment variables in Unraid template -->
<Config Name="CACHERR_ENVIRONMENT" Target="CACHERR_ENVIRONMENT" Default="production" Mode="" Description="Runtime environment (production/development)" Type="Variable" Display="always" Required="false" Mask="false"></Config>
<Config Name="LOG_LEVEL" Target="LOG_LEVEL" Default="INFO" Mode="" Description="Logging level" Type="Variable" Display="always" Required="false" Mask="false"></Config>
```

### Step 3: Update Service Configuration (Advanced)

If you're using advanced service configuration with environment variables:

**Old Pattern**:
```bash
CACHERR_SERVICE_MEDIA_SERVICE_IMPLEMENTATION=DefaultMediaService
CACHERR_SERVICE_MEDIA_SERVICE_LIFETIME=transient
```

**New Pattern** (already current):
```bash
CACHERR_SERVICE_MEDIA_SERVICE_IMPLEMENTATION=DefaultMediaService
CACHERR_SERVICE_MEDIA_SERVICE_LIFETIME=transient
```

### Step 4: Start Container with New Variables

```bash
docker-compose up -d
```

### Step 5: Verify Migration Success

1. Check container logs for any environment variable warnings:
```bash
docker-compose logs cacherr
```

2. Verify the web interface loads correctly:
   - Open http://localhost:5445
   - Navigate to Settings page
   - Confirm Plex settings are loaded (if configured via env vars)

3. Test functionality:
   - Try Plex connection testing
   - Verify settings persistence
   - Check that all features work as expected

## Recommended Migration Strategy

### Option A: Minimal Migration (Recommended)

1. Remove old PLEX_* environment variables
2. Keep CACHERR_* variables minimal
3. Configure everything via web UI
4. Benefits: Simpler, more maintainable, no env var conflicts

```yaml
# Minimal environment variables - configure via web UI
environment:
  - CACHERR_ENVIRONMENT=production
  - CACHERR_LOG_LEVEL=INFO
```

### Option B: Full Environment Variable Migration

1. Replace all old variables with new CACHERR_* equivalents
2. Keep advanced configuration in environment variables
3. Benefits: Scriptable deployment, infrastructure-as-code friendly

```yaml
# Full environment variable configuration
environment:
  - CACHERR_ENVIRONMENT=production
  - CACHERR_CONFIG_DIR=./config
  - CACHERR_LOG_LEVEL=INFO
  - CACHERR_PLEX_URL=http://plex-server:32400
  - CACHERR_PLEX_TOKEN=your_token_here
```

## Backward Compatibility

The application currently maintains backward compatibility with old PLEX_* environment variables, but this support will be removed in future versions. You'll see deprecation warnings in the logs when using old variables.

### Temporary Compatibility Mode

```yaml
# This will work but show deprecation warnings
environment:
  - PLEX_URL=http://plex-server:32400
  - PLEX_TOKEN=your_token_here

# Recommended approach
environment:
  - CACHERR_PLEX_URL=http://plex-server:32400
  - CACHERR_PLEX_TOKEN=your_token_here
```

## Troubleshooting

### Common Issues

#### 1. Container Won't Start
```bash
# Check logs for environment variable errors
docker-compose logs cacherr

# Common issue: Incorrect variable names
# Solution: Verify variable names match exactly
```

#### 2. Settings Not Loading
```bash
# Check if configuration files exist
ls -la config/

# Verify environment variables are passed correctly
docker-compose exec cacherr env | grep CACHERR
```

#### 3. Plex Connection Issues
```bash
# Test connection via web UI
# Check that CACHERR_PLEX_* variables are correct
# Verify Plex server is accessible from container
```

#### 4. Deprecation Warnings
```bash
# If you see warnings about old variables:
# 1. Note which variables are being used
# 2. Update them to CACHERR_* equivalents
# 3. Restart container
docker-compose restart
```

### Getting Help

If you encounter issues during migration:

1. Check the container logs for specific error messages
2. Verify your docker-compose.yml syntax
3. Ensure environment variables are properly formatted
4. Test with minimal configuration first
5. Document any issues for the development team

## Verification Checklist

- [ ] Container starts without errors
- [ ] Web interface loads correctly
- [ ] Settings page displays properly
- [ ] Plex connection works (if configured)
- [ ] No deprecation warnings in logs
- [ ] Configuration persists across restarts
- [ ] All functionality works as expected

## Future Considerations

### Environment Variable Deprecation Timeline

- **Current**: PLEX_* variables supported with warnings
- **Future Release**: PLEX_* variables deprecated
- **v2.0.0**: PLEX_* variables removed entirely

### Best Practices Moving Forward

1. **Prefer Web UI**: Configure most settings via the web interface
2. **Use Environment Variables for**:
   - Infrastructure-specific settings (ports, directories)
   - Secrets that shouldn't be in config files
   - Deployment automation
3. **Document Your Configuration**: Keep track of your environment variables for future migrations

---

*This migration guide was created as part of the Cacherr project refactoring to ensure smooth transition from PlexCacheUltra to the new Cacherr naming convention.*
