# 🤖 CACHERR REFACTORING - AGENT EXECUTION GUIDE

## 📋 OVERVIEW

This document provides **step-by-step instructions** for each specific task in the Cacherr refactoring project. Each task is designed to be **completely independent** and can be handed to a fresh agent with no prior context.

**CRITICAL RULES**: ⚠️ 
1. **CHECK MASTER PLAN FIRST**: Always reference CACHERR_REFACTORING_MASTER_PLAN.md for complete task list and dependencies
2. Only execute the task assigned to you. Check dependencies before starting.
3. **Update Master Plan**: Mark your task as "in_progress" when you start and "completed" when finished
4. **Use Pydantic v2.5**: All Python code must use Pydantic v2.5 type hints and validation patterns
5. **Reference Context7**: Use Context7 documentation for best practices and modern patterns
6. **Extensive Code Comments**: Leave detailed comments explaining what every function, class, and complex logic does
7. **Self-Documenting Code**: Someone unfamiliar with the project should understand your code from comments alone
8. **ENSURE SETTINGS PERSISTENCE**: Test that settings survive page navigation and Docker restarts

---

# 🎯 TASK COMPLEXITY & AGENT MATCHING GUIDE

**⚠️ IMPORTANT NOTE**: This guide contains detailed instructions for the most critical phases. For complete task coverage including all 33 tasks, refer to the **CACHERR_REFACTORING_MASTER_PLAN.md** file which contains the authoritative task list, dependencies, and execution order. Additional task instructions may be documented separately for newer tasks.

## **🟢 SIMPLE TASKS** (Basic agents can handle - mostly find/replace operations)
- **TASK 0A**: Pre-Execution Environment Validation (`general-purpose`)
- **TASK 0B**: Create Rollback Documentation and Backup Strategy (`general-purpose`)
- **TASK 1C**: Replace Critical Project Name References (`general-purpose`)
- **TASK 2B**: Replace Remaining Project Name References (`general-purpose`)
- **TASK 2B1**: Environment Variable Migration Documentation (`general-purpose`)
- **TASK 3C**: Optimize Test Suite Structure (`general-purpose`)
- **TASK 4A**: Update All Documentation (`general-purpose`)

## **🟡 INTERMEDIATE TASKS** (Agents with domain knowledge)
- **TASK 1A1**: Verify and Create Missing Settings API Routes (`python-pro`)
- **TASK 1B**: Fix Docker Production Configuration (`deployment-engineer`)
- **TASK 2C**: Test Core Functionality Integration (`production-code-auditor`)
- **TASK 3A0**: Audit and Fix Configuration Import Structure (`python-pro`)
- **TASK 3A1**: Create Configuration Migration Script (`python-pro`)
- **TASK 3A3**: Update Core Services for New Configuration (`python-pro`)
- **TASK 3B**: Simplify WebSocket Implementation (`general-purpose`)
- **TASK 5A**: Legacy Configuration System Removal (`python-pro`)
- **TASK 5B**: Remove Deprecated Components and Files (`general-purpose`)
- **TASK 5C**: Clean Frontend Legacy Code (`react-ui-builder`)
- **TASK 6D**: Unraid Deployment Validation (`deployment-engineer`)

## **🔴 COMPLEX TASKS** (Expert agents required)
- **TASK 1A**: Fix Dashboard Backend Functionality (`python-pro`)
- **TASK 2A**: Create Settings Page TypeScript Interfaces and API Service (`react-ui-builder`)
- **TASK 2A2**: Implement Plex Settings Component (`react-ui-builder`)
- **TASK 2A3**: Implement Media Settings Component (`react-ui-builder`)
- **TASK 2A4**: Implement Performance & Advanced Settings Components (`react-ui-builder`)
- **TASK 2A5**: Implement Main Settings Page and Integration (`react-ui-builder`)
- **TASK 3A**: Update Configuration Imports to New System (`python-pro`)
- **TASK 3A2**: Ensure Pydantic v2.5 Compliance (`python-pro`)
- **TASK 4B**: Final Security & Quality Audit (`production-code-auditor`)
- **TASK 5A**: Legacy Configuration System Removal (`python-pro`)
- **TASK 5B**: Remove Deprecated Components and Files (`general-purpose`)
- **TASK 5C**: Clean Frontend Legacy Code (`react-ui-builder`)
- **TASK 6A**: Setup Backend Testing Framework (`python-pro`)
- **TASK 6A2**: Create Backend Unit Tests (`python-pro`)
- **TASK 6A3**: Create Backend API Integration Tests (`python-pro`)
- **TASK 6B**: Setup Playwright Testing Framework (`react-ui-builder`)
- **TASK 6B2**: Create Dashboard Playwright Tests (`react-ui-builder`)
- **TASK 6B3**: Create Settings Page Playwright Tests (`react-ui-builder`)
- **TASK 6B4**: Create Responsive Design & Error Handling Tests (`react-ui-builder`)
- **TASK 6C**: End-to-End Integration Testing & Production Validation (`production-code-auditor`)

---

## ✅ TASK 0A: PRE-EXECUTION ENVIRONMENT VALIDATION (CRITICAL FIRST STEP)

### Agent Type: `general-purpose`
### Complexity: 🟢 **SIMPLE** (environment checking and validation)
### Dependencies: NONE - must run first before any other tasks
### Can Run Parallel With: NONE - sequential only

### Context
Before any refactoring work begins, the environment must be validated to ensure all required dependencies, tools, and files are available. This prevents agent failures due to missing components.

### Pre-Execution Checklist
- [ ] You have access to basic system commands (ls, find, grep, etc.)
- [ ] You can read files in the Cacherr project directory
- [ ] You understand what constitutes a validation failure

### Step-by-Step Instructions

#### Step 1: Validate Project Structure
1. Verify the main project directory exists:
   ```bash
   ls -la /mnt/user/Cursor/Cacherr/
   ```
2. Check that critical directories are present:
   - `src/` (backend source code)
   - `frontend/` (React frontend)
   - `tests/` or `e2e/` (testing files)

#### Step 2: Validate Python Environment
1. Check Python version and availability:
   ```bash
   python3 --version
   python --version
   ```
2. Verify key Python files exist:
   - `/mnt/user/Cursor/Cacherr/main.py`
   - `/mnt/user/Cursor/Cacherr/src/web/app.py`
   - `/mnt/user/Cursor/Cacherr/requirements.txt`

#### Step 3: Validate Node.js Environment
1. Check Node.js and npm availability:
   ```bash
   node --version
   npm --version
   ```
2. Verify frontend structure:
   - `/mnt/user/Cursor/Cacherr/frontend/package.json`
   - `/mnt/user/Cursor/Cacherr/frontend/src/`

#### Step 4: Validate Docker Environment
1. Check Docker availability:
   ```bash
   docker --version
   docker-compose --version
   ```
2. Verify Docker-related files:
   - `/mnt/user/Cursor/Cacherr/Dockerfile` (current, needs fixing)
   - `/mnt/user/Cursor/Cacherr/docker-compose.yml`

#### Step 5: Create Environment Validation Report
Create a comprehensive validation report documenting:
- All available tools and versions
- Missing dependencies or tools
- Critical files that exist or are missing
- Any environment issues that need addressing

### Success Criteria
- [ ] All critical project directories confirmed to exist
- [ ] Python 3.x environment available and working
- [ ] Node.js and npm environment available
- [ ] Docker and docker-compose available
- [ ] All critical source files confirmed to exist
- [ ] Validation report created with findings

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 0A status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 0A status to "completed"

### Files Created
- Environment validation report (as output/log)

### Files Modified
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## 📋 TASK 0B: CREATE ROLLBACK DOCUMENTATION AND BACKUP STRATEGY (CRITICAL SAFETY)

### Agent Type: `general-purpose`
### Complexity: 🟢 **SIMPLE** (documentation and backup procedures)
### Dependencies: TASK 0A must be complete (environment validated)
### Can Run Parallel With: NONE - sequential only

### Context
Before making any changes to the codebase, create comprehensive rollback documentation and backup procedures to ensure recovery is possible if critical failures occur during refactoring.

### Pre-Execution Checklist
- [ ] Verify TASK 0A completed successfully (environment validated)
- [ ] You can create new files and directories
- [ ] You understand git operations and file backup strategies

### Step-by-Step Instructions

#### Step 1: Create Rollback Documentation
**File**: `/mnt/user/Cursor/Cacherr/ROLLBACK_PROCEDURES.md`

```markdown
# 🔄 CACHERR REFACTORING ROLLBACK PROCEDURES

## Critical File Backups
Before each phase, create backups of these critical files:

### Phase 1 Backups (Backend Fixes)
- `src/web/routes/api.py` → `src/web/routes/api.py.phase1.bak`
- `src/web/app.py` → `src/web/app.py.phase1.bak`
- `Dockerfile` → `Dockerfile.phase1.bak`
- `docker-compose.yml` → `docker-compose.yml.phase1.bak`

### Phase 2 Backups (Settings Implementation)
- `frontend/src/App.tsx` → `frontend/src/App.tsx.phase2.bak`
- `frontend/package.json` → `frontend/package.json.phase2.bak`

### Phase 3 Backups (Configuration Changes)
- `src/config/` → `src/config.phase3.backup/`
- All Python files importing configuration

## Rollback Commands by Phase

### If Phase 1 Fails:
```bash
# Restore backend files
cp src/web/routes/api.py.phase1.bak src/web/routes/api.py
cp src/web/app.py.phase1.bak src/web/app.py
cp Dockerfile.phase1.bak Dockerfile
cp docker-compose.yml.phase1.bak docker-compose.yml

# Restart services
docker-compose down
docker-compose up --build
```

### If Phase 2 Fails:
```bash
# Restore frontend files
cp frontend/src/App.tsx.phase2.bak frontend/src/App.tsx
cp frontend/package.json.phase2.bak frontend/package.json

# Rebuild frontend
cd frontend && npm install && npm run build
```

### If Phase 3 Configuration Fails:
```bash
# Restore entire config directory
rm -rf src/config/
cp -r src/config.phase3.backup/ src/config/

# Restart application
docker-compose restart
```

## Emergency Recovery Commands
If the application becomes completely unresponsive:

1. Stop all containers: `docker-compose down`
2. Remove any corrupted images: `docker system prune -f`
3. Restore from git: `git stash && git checkout HEAD~1`
4. Rebuild: `docker-compose up --build`

## Validation After Rollback
After any rollback:
1. Test dashboard access: http://localhost:5445
2. Verify all tabs load (Dashboard, Cached, Logs)
3. Check for console errors in browser
4. Ensure API health endpoints respond: `/api/health`
```

#### Step 2: Create Backup Script
**File**: `/mnt/user/Cursor/Cacherr/create_backup.sh`

```bash
#!/bin/bash
# Automated backup script for Cacherr refactoring

PHASE=$1
BACKUP_DIR="./backups/phase_${PHASE}"

if [ -z "$PHASE" ]; then
    echo "Usage: ./create_backup.sh <phase_number>"
    exit 1
fi

echo "Creating backup for Phase $PHASE..."
mkdir -p "$BACKUP_DIR"

# Phase-specific backups
case $PHASE in
    1)
        cp src/web/routes/api.py "$BACKUP_DIR/api.py.bak"
        cp src/web/app.py "$BACKUP_DIR/app.py.bak"
        cp Dockerfile "$BACKUP_DIR/Dockerfile.bak"
        cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.bak"
        ;;
    2)
        cp frontend/src/App.tsx "$BACKUP_DIR/App.tsx.bak"
        cp frontend/package.json "$BACKUP_DIR/package.json.bak"
        ;;
    3)
        cp -r src/config/ "$BACKUP_DIR/config.backup/"
        ;;
    *)
        echo "Unknown phase: $PHASE"
        exit 1
        ;;
esac

echo "Backup created in $BACKUP_DIR"
chmod +x ./create_backup.sh
```

#### Step 3: Document Recovery Testing
Add to ROLLBACK_PROCEDURES.md:

```markdown
## Testing Rollback Procedures

Before starting refactoring, test these procedures:

### Test 1: File Restoration
1. Create a test backup: `./create_backup.sh test`
2. Modify a backed-up file
3. Restore from backup
4. Verify restoration worked

### Test 2: Service Recovery
1. Stop application: `docker-compose down`
2. Start application: `docker-compose up`
3. Verify dashboard loads correctly
4. Test all major functionality

## Contact Information
If rollback procedures fail:
- Check Git commit history: `git log --oneline`
- Consider reverting to last known good commit
- Document any issues encountered for future agents
```

### Success Criteria
- [ ] Comprehensive rollback procedures documented
- [ ] Backup script created and tested
- [ ] Recovery commands verified for each phase
- [ ] Emergency recovery procedures documented
- [ ] Files are executable and properly formatted

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 0B status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 0B status to "completed"

### Files Created
- `/mnt/user/Cursor/Cacherr/ROLLBACK_PROCEDURES.md`
- `/mnt/user/Cursor/Cacherr/create_backup.sh`

### Files Modified
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## 🚨 TASK 1A: FIX DASHBOARD BACKEND FUNCTIONALITY (URGENT)

### Agent Type: `python-pro`
### Complexity: 🔴 **COMPLEX** (requires Python/Flask/Pydantic expertise)
### Dependencies: NONE - can start immediately  
### Can Run Parallel With: TASK 1B, TASK 1C

### Context
The Cacherr dashboard is completely broken due to backend service failures. Users cannot access any functionality because API calls return 500 errors. This must be fixed first before any other work can proceed.

### Pre-Execution Checklist
- [ ] Verify you can access the Cacherr project at `/mnt/user/Cursor/Cacherr/`
- [ ] Confirm backend is Python Flask with Pydantic models
- [ ] Check that you have tools to edit Python files and test API endpoints

### Step-by-Step Instructions

#### Step 1: Fix Missing Function References
**File**: `/mnt/user/Cursor/Cacherr/src/web/routes/api.py`
**Issue**: Function `get_engine()` doesn't exist, only `get_cache_engine()` exists

1. Open `/mnt/user/Cursor/Cacherr/src/web/routes/api.py`
2. Search for all instances of `get_engine()` (should be 5 instances)
3. Replace each `get_engine()` with `get_cache_engine()`
4. **Lines to fix**: 429, 868, 911, 955, 1020

**Before**:
```python
engine = get_engine()
```

**After**:
```python
engine = get_cache_engine()
```

#### Step 2: Add Null Checks for Engine
After each `get_cache_engine()` call, add null checking:

```python
engine = get_cache_engine()
if not engine:
    return jsonify({
        'status': 'error',
        'message': 'Cache engine not available',
        'data': None
    }), 503
```

#### Step 3: Fix Service Injection Issues
**File**: `/mnt/user/Cursor/Cacherr/src/web/app.py`

1. Locate the `_setup_dependency_injection()` method
2. Verify that all services are properly resolved and injected into Flask's `g` object
3. Add error handling for service resolution failures

**Add this validation**:
```python
def _validate_services():
    """Validate that all required services are available"""
    required_services = [
        'cached_files_service',
        'media_service', 
        'file_service',
        'websocket_manager'
    ]
    
    missing_services = []
    for service_name in required_services:
        try:
            service = g.container.resolve(service_name)
            if service is None:
                missing_services.append(service_name)
        except Exception as e:
            missing_services.append(f"{service_name} ({str(e)})")
    
    if missing_services:
        app.logger.error(f"Missing services: {missing_services}")
        return False
    return True
```

#### Step 4: Test Dashboard Functionality
1. Start the backend server
2. Navigate to dashboard in browser
3. Check browser console for JavaScript errors
4. Test each tab (Dashboard, Cached, Logs)
5. Verify API endpoints return data instead of 500 errors

### Success Criteria
- [ ] Dashboard loads without 500 errors
- [ ] All three tabs (Dashboard, Cached, Logs) display content
- [ ] No JavaScript console errors
- [ ] Health endpoints return valid JSON responses
- [ ] Backend logs show successful service initialization

### Code Quality Requirements
- **Comments**: Add detailed comments explaining the service resolution logic
- **Pydantic v2.5**: Ensure all models use latest Pydantic patterns
- **Error Handling**: Include comprehensive error messages for debugging

### Context7 Reference
Use Context7 Pydantic documentation for best practices:
```python
# Example: Use Context7 patterns for service validation
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

class ServiceHealth(BaseModel):
    """
    Represents the health status of a backend service.
    
    This model validates service health checks and provides
    structured error reporting for debugging purposes.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    service_name: Annotated[str, Field(..., description="Name of the service being checked")]
    is_healthy: Annotated[bool, Field(..., description="Whether the service is operational")]
    error_message: Annotated[str | None, Field(None, description="Error details if service is unhealthy")]
```

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 1A status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 1A status to "completed"

### Troubleshooting
If dashboard still fails:
1. Check backend server logs for service initialization errors
2. Verify dependency injection container is properly configured
3. Test API endpoints directly with curl/Postman
4. Check that all required services are registered in the container

### Files Modified
- `/mnt/user/Cursor/Cacherr/src/web/routes/api.py` (function calls and null checks)
- `/mnt/user/Cursor/Cacherr/src/web/app.py` (service validation)
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## 🔧 TASK 1A1: VERIFY AND CREATE MISSING SETTINGS API ROUTES (CRITICAL)

### Agent Type: `python-pro`
### Complexity: 🟡 **INTERMEDIATE** (requires Flask API and route knowledge)
### Dependencies: TASK 1A must be complete (dashboard backend fixed)
### Can Run Parallel With: NONE - sequential only

### Context
After fixing the dashboard backend, ensure that all necessary API routes exist for the Settings page implementation. The Settings page requires specific API endpoints that may be missing or incomplete.

### Pre-Execution Checklist
- [ ] Verify TASK 1A completed successfully (dashboard working)
- [ ] You have Python/Flask API development knowledge
- [ ] Backend server can be started and tested

### Step-by-Step Instructions

#### Step 1: Audit Existing Configuration API Routes
**File to Check**: `/mnt/user/Cursor/Cacherr/src/web/routes/api.py`

Search for existing configuration-related routes:
1. Look for routes starting with `/api/config/`
2. Document what endpoints currently exist
3. Check if they return proper JSON responses

**Required API Endpoints for Settings Page**:
- `GET /api/config/current` - Get current configuration
- `POST /api/config/update` - Update configuration
- `POST /api/config/test-plex` - Test Plex connection
- `GET /api/config/export` - Export configuration
- `POST /api/config/import` - Import configuration  
- `POST /api/config/reset` - Reset to defaults
- `GET /api/config/schema` - Get configuration schema

#### Step 2: Create Missing API Routes
If any routes are missing, add them to `/mnt/user/Cursor/Cacherr/src/web/routes/api.py`:

```python
@api.route('/config/current', methods=['GET'])
def get_current_config():
    """
    Get current application configuration.
    
    Returns the current configuration settings in a structured format
    that can be consumed by the Settings page frontend.
    
    Returns:
        JSON: Current configuration with status and data
    """
    try:
        # Get current configuration from the configuration system
        from src.core.new_settings import Config
        config = Config()
        
        return jsonify({
            'status': 'success',
            'data': {
                'plex': {
                    'url': config.plex.url,
                    'token': '***MASKED***' if config.plex.token else '',
                    'timeout': config.plex.timeout,
                    'verify_ssl': config.plex.verify_ssl
                },
                'media': {
                    'source_paths': config.media.source_paths,
                    'cache_path': config.media.cache_path,
                    'file_extensions': config.media.file_extensions,
                    'min_file_size': config.media.min_file_size,
                    'max_file_size': config.media.max_file_size
                },
                'performance': {
                    'max_concurrent_operations': config.performance.max_concurrent_operations,
                    'cache_check_interval': config.performance.cache_check_interval,
                    'cleanup_interval': config.performance.cleanup_interval,
                    'log_level': config.performance.log_level
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get current configuration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve configuration: {str(e)}'
        }), 500

@api.route('/config/update', methods=['POST'])
def update_config():
    """
    Update application configuration.
    
    Accepts partial configuration updates and validates them using
    Pydantic models before applying changes.
    
    Returns:
        JSON: Updated configuration with status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No configuration data provided'
            }), 400
            
        # Update configuration using the configuration system
        from src.core.new_settings import Config
        config = Config()
        
        # Apply updates and validate
        updated_config = config.save_updates(data)
        
        return jsonify({
            'status': 'success',
            'message': 'Configuration updated successfully',
            'data': updated_config
        })
        
    except ValidationError as e:
        return jsonify({
            'status': 'error',
            'message': 'Configuration validation failed',
            'errors': e.errors()
        }), 422
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to update configuration: {str(e)}'
        }), 500

@api.route('/config/test-plex', methods=['POST'])
def test_plex_connection():
    """
    Test Plex server connection with provided credentials.
    
    Returns:
        JSON: Connection test result
    """
    try:
        data = request.get_json()
        plex_url = data.get('url')
        plex_token = data.get('token')
        
        if not plex_url or not plex_token:
            return jsonify({
                'status': 'error',
                'message': 'Both URL and token are required'
            }), 400
            
        # Test Plex connection using existing Plex service
        # This should use the actual Plex service from the container
        plex_service = g.container.resolve('plex_service')
        
        # Test the connection
        connection_result = plex_service.test_connection(plex_url, plex_token)
        
        if connection_result:
            return jsonify({
                'status': 'success',
                'message': 'Plex connection successful'
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Failed to connect to Plex server'
            }), 400
            
    except Exception as e:
        logger.error(f"Plex connection test failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Connection test failed: {str(e)}'
        }), 500
```

#### Step 3: Test API Endpoints
1. Start the backend server
2. Test each endpoint using curl or a REST client:
   ```bash
   # Test get current config
   curl -X GET http://localhost:5445/api/config/current
   
   # Test Plex connection (use real credentials for testing)
   curl -X POST http://localhost:5445/api/config/test-plex \
     -H "Content-Type: application/json" \
     -d '{"url":"http://localhost:32400","token":"test-token"}'
   ```
3. Verify responses are properly formatted JSON
4. Check error handling for invalid inputs

#### Step 4: Update Unraid Template and Docker Compose
**Important**: The user prefers the docker template XML to stay simple with most variables set in the web UI.

**File**: `/mnt/user/Cursor/Cacherr/my-cacherr.xml`
- Update project name references from PlexCacheUltra to Cacherr  
- Keep environment variables minimal (only essential ones)
- Ensure volume mappings are correct
- Remove any outdated or unused environment variables

**File**: `/mnt/user/Cursor/Cacherr/docker-compose.yml`  
- Update any references to old project names
- Ensure environment variables match the new configuration system
- Keep the compose file focused on essential runtime configuration
- Document that most settings should be configured via the web UI

### Context7 Reference
**REQUIRED**: Use Context7 Flask documentation for API route patterns and error handling best practices.

### Code Quality Requirements
- **API Documentation**: Every route needs comprehensive docstrings
- **Error Handling**: Include proper HTTP status codes and error messages
- **Validation**: Use Pydantic models for request/response validation
- **Security**: Mask sensitive data (tokens) in responses
- **Logging**: Add appropriate logging for debugging

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 1A1 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 1A1 status to "completed"

#### Step 5: Ensure Settings Persistence (CRITICAL)
**Important**: The user has experienced major problems with settings not persisting across page changes and Docker restarts.

1. **Test Settings Persistence Across Page Navigation**:
   - Change settings in the web UI
   - Navigate to different tabs/pages
   - Return to settings page
   - Verify all settings are still present

2. **Test Settings Persistence Across Docker Restarts**:
   - Change settings via web UI
   - Restart Docker container: `docker-compose restart`
   - Check that settings are retained after restart
   - Verify settings are loaded from persistent storage

3. **Configuration File Persistence**:
   - Ensure configuration files are saved to mounted volumes
   - Map `/app/config` to `./config` in docker-compose.yml
   - Verify settings are written to files immediately upon save
   - Test that configuration loads correctly on startup

4. **Add Persistence Validation to Settings API**:
   ```python
   @api.route('/config/validate-persistence', methods=['GET'])
   def validate_persistence():
       """Validate that settings persistence is working correctly."""
       try:
           # Check if configuration files exist and are accessible
           from pathlib import Path
           config_dir = Path('/app/config')
           
           return jsonify({
               'status': 'success',
               'persistence': {
                   'config_dir_exists': config_dir.exists(),
                   'config_dir_writable': os.access(config_dir, os.W_OK),
                   'config_files': list(config_dir.glob('*.json')) if config_dir.exists() else []
               }
           })
       except Exception as e:
           return jsonify({'status': 'error', 'message': str(e)}), 500
   ```

### Success Criteria
- [ ] All required Settings API endpoints exist and work
- [ ] API responses are properly formatted JSON
- [ ] Error handling returns appropriate HTTP status codes
- [ ] Plex connection testing works correctly
- [ ] Unraid XML template updated with new project name
- [ ] Docker compose file updated appropriately
- [ ] No sensitive data exposed in API responses
- [ ] **CRITICAL**: Settings persist across page navigation
- [ ] **CRITICAL**: Settings persist across Docker container restarts
- [ ] Settings persistence validation endpoint working

### Files Modified
- `/mnt/user/Cursor/Cacherr/src/web/routes/api.py` (API route additions)
- `/mnt/user/Cursor/Cacherr/my-cacherr.xml` (template updates)
- `/mnt/user/Cursor/Cacherr/docker-compose.yml` (compose updates)
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## 🐳 TASK 1B: FIX DOCKER PRODUCTION CONFIGURATION (URGENT)

### Agent Type: `deployment-engineer`
### Complexity: 🟡 **INTERMEDIATE** (Docker/containerization knowledge needed)
### Dependencies: NONE - can start immediately
### Can Run Parallel With: TASK 1A, TASK 1C

### Context
The current Docker setup is completely wrong. The main `Dockerfile` is actually for Playwright testing (3.75GB) instead of the application. This needs a production-ready Docker configuration.

### Pre-Execution Checklist
- [ ] Verify you can access the Cacherr project at `/mnt/user/Cursor/Cacherr/`
- [ ] Confirm you have tools to create/edit Dockerfiles and docker-compose.yml
- [ ] Check that you can build and test Docker images

### Step-by-Step Instructions

#### Step 1: Create Production Dockerfile
**File**: `/mnt/user/Cursor/Cacherr/Dockerfile` (replace existing)

Create a new production Dockerfile:

```dockerfile
# Multi-stage build - Production Dockerfile for Cacherr
FROM node:18-alpine AS frontend-builder

# Build React frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY frontend/ ./
RUN npm run build

# Python production stage
FROM python:3.11-slim AS production

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY __init__.py .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create necessary directories
RUN mkdir -p /app/data /app/config /app/logs

# Expose port
EXPOSE 5445

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5445/api/health || exit 1

# Default command
CMD ["python", "main.py", "--mode", "docker"]
```

#### Step 2: Create .dockerignore
**File**: `/mnt/user/Cursor/Cacherr/.dockerignore`

```
# Development files
.git/
.gitignore
.env
.env.*

# Documentation
*.md
docs/
CACHERR_REFACTORING_MASTER_PLAN.md
AGENT_EXECUTION_GUIDE.md

# Test files and artifacts
e2e/
tests/
tests-examples/
playwright-report/
test-results/
*.spec.js
*.test.js
*.test.ts
*.test.tsx

# Node artifacts
node_modules/.cache/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.pytest_cache/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Build artifacts
frontend/dist/
frontend/node_modules/

# Cache and temp
.npm/
.cache/
*.tmp
*.temp

# Log files
*.log
logs/

# Media test files
*.mp4
*.mkv
*.avi
*.mov
```

#### Step 3: Update docker-compose.yml
**File**: `/mnt/user/Cursor/Cacherr/docker-compose.yml`

```yaml
version: '3.8'

services:
  # Production application
  cacherr:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5445:5445"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
      # Bind mount for media files (Unraid specific)
      - /mnt/user/media:/media:rw
      - /mnt/cache:/cache:rw
    environment:
      - CACHERR_ENVIRONMENT=production
      - CACHERR_CONFIG_DIR=/app/config
      - CACHERR_DATA_DIR=/app/data
      - CACHERR_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5445/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Development service
  cacherr-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "5445:5445"
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
      - /app/frontend/node_modules
    environment:
      - CACHERR_ENVIRONMENT=development
      - CACHERR_DEBUG=true
    profiles: ["dev"]

  # Testing services (separate profile)
  playwright:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - ./e2e:/app/e2e
      - ./playwright.config.js:/app/playwright.config.js
      - ./playwright-report:/app/playwright-report
    environment:
      - CI=true
    profiles: ["testing"]
    command: npx playwright test

  playwright-ui:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - ./e2e:/app/e2e
      - ./playwright.config.js:/app/playwright.config.js
    environment:
      - CI=false
    ports:
      - "9323:9323"
    profiles: ["testing"]
    command: npx playwright test --ui --ui-host=0.0.0.0
```

#### Step 4: Create Test-Only Dockerfile
**File**: `/mnt/user/Cursor/Cacherr/Dockerfile.test`

```dockerfile
# Test-only Dockerfile (rename current Dockerfile to this)
FROM mcr.microsoft.com/playwright:v1.47.0-jammy

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY playwright.config.js ./

# Install dependencies
RUN npm ci

# Copy test files only
COPY e2e/ ./e2e/

# Install only Chromium to reduce size
RUN npx playwright install chromium --with-deps

# Default test command
CMD ["npx", "playwright", "test"]
```

#### Step 5: Test Docker Build
1. Build the production image:
   ```bash
   docker build -t cacherr:prod .
   ```

2. Check image size:
   ```bash
   docker images cacherr:prod
   ```

3. Test container startup:
   ```bash
   docker run -p 5445:5445 cacherr:prod
   ```

4. Verify health endpoint:
   ```bash
   curl http://localhost:5445/api/health
   ```

### Success Criteria
- [ ] Production Docker image builds successfully
- [ ] Image size is under 500MB (target: <200MB)
- [ ] Application starts and responds to health checks
- [ ] Frontend serves correctly from built assets
- [ ] Tests run in separate container without affecting production

### Files Created/Modified
- `Dockerfile` (new production version)
- `.dockerignore` (comprehensive exclusions)
- `docker-compose.yml` (updated with profiles)
- `Dockerfile.test` (renamed from current Dockerfile)

---

## 🔄 TASK 1C: REPLACE CRITICAL PROJECT NAME REFERENCES (URGENT)

### Agent Type: `general-purpose`
### Complexity: 🟢 **SIMPLE** (mostly find/replace operations)
### Dependencies: NONE - can start immediately
### Can Run Parallel With: TASK 1A, TASK 1B

### Context
Throughout the codebase, there are 200+ references to the old project names "PlexCacheUltra", "plexcache", "plexcacheultea" that need to be updated. This task focuses on the most critical, user-facing references.

### Pre-Execution Checklist
- [ ] Verify you can access the Cacherr project at `/mnt/user/Cursor/Cacherr/`
- [ ] Confirm you have tools for global find/replace operations
- [ ] Test that the application is working before starting changes

### Step-by-Step Instructions

#### Step 1: Update Critical Files Only
**Focus on user-facing and critical system files only**

**File**: `/mnt/user/Cursor/Cacherr/frontend/package.json`
- Line 5: `"description": "Modern React frontend for PlexCacheUltra dashboard"` 
- **Change to**: `"description": "Modern React frontend for Cacherr dashboard"`

**File**: `/mnt/user/Cursor/Cacherr/__init__.py`
- Line 2: `PlexCacheUltra - Docker-optimized Plex media caching system`
- **Change to**: `Cacherr - Docker-optimized Plex media caching system`
- Line 6: `__author__ = "PlexCacheUltra Team"`
- **Change to**: `__author__ = "Cacherr Team"`

**File**: `/mnt/user/Cursor/Cacherr/main.py`
- Line 223: `description='PlexCacheUltra CLI Operations'`
- **Change to**: `description='Cacherr CLI Operations'`
- Line 299: `"Starting PlexCacheUltra in {run_mode} mode..."`
- **Change to**: `"Starting Cacherr in {run_mode} mode..."`
- Line 311: `"PlexCacheUltra started successfully!"`
- **Change to**: `"Cacherr started successfully!"`
- Line 327: `"Failed to start PlexCacheUltra: {e}"`
- **Change to**: `"Failed to start Cacherr: {e}"`

**File**: `/mnt/user/Cursor/Cacherr/my-cacherr.xml`
- Line 12: Update overview text from "PlexCacheUltra" to "Cacherr"

**File**: `/mnt/user/Cursor/Cacherr/frontend/src/components/Dashboard/Dashboard.test.tsx`
- Line 85: `expect(screen.getByText('PlexCacheUltra')).toBeInTheDocument()`
- **Change to**: `expect(screen.getByText('Cacherr')).toBeInTheDocument()`
- Line 100: `'Loading PlexCacheUltra Dashboard...'`
- **Change to**: `'Loading Cacherr Dashboard...'`

**File**: `/mnt/user/Cursor/Cacherr/frontend/public/offline.html`
- Line 6: `<title>Offline - PlexCacheUltra</title>`
- **Change to**: `<title>Offline - Cacherr</title>`

#### Step 2: Test Application After Changes
1. Start the backend server
2. Start the frontend  
3. Verify the application loads correctly
4. Check that all references in the UI show "Cacherr"
5. Test that functionality still works

### Success Criteria
- [ ] All critical user-facing references updated
- [ ] Application starts successfully after changes
- [ ] UI displays "Cacherr" instead of old project names
- [ ] No broken references or import errors

### Files Modified
- `frontend/package.json` (description)
- `__init__.py` (project info)
- `main.py` (CLI messages)
- `my-cacherr.xml` (Unraid template)
- `frontend/src/components/Dashboard/Dashboard.test.tsx` (tests)
- `frontend/public/offline.html` (title)

---

## ⚙️ TASK 2A: CREATE SETTINGS PAGE TYPESCRIPT INTERFACES AND API SERVICE (HIGH PRIORITY)

### Agent Type: `react-ui-builder`
### Complexity: 🟡 **INTERMEDIATE** (requires TypeScript/API knowledge)
### Dependencies: TASK 1A must be complete (dashboard working)
### Can Run Parallel With: TASK 2B

### Context
This is the first step in implementing the Settings page. You'll create the TypeScript interfaces and API service that all Settings components will use. The backend API is fully implemented and ready.

### Pre-Execution Checklist
- [ ] Verify Phase 1.1 (Dashboard Fix) is completed and working
- [ ] Confirm you have access to React/TypeScript development tools
- [ ] Check that the backend settings API is working (`/api/config` endpoints)

### Step-by-Step Instructions

#### Step 1: Analyze Backend Configuration API
First, understand what settings are available:

1. Check `/mnt/user/Cursor/Cacherr/src/core/new_settings.py` for Pydantic models
2. Test settings endpoints:
   ```bash
   curl http://localhost:5445/api/config/current
   curl http://localhost:5445/api/config/schema
   ```
3. Identify all configuration sections and fields

#### Step 2: Create TypeScript Interfaces
**File**: `/mnt/user/Cursor/Cacherr/frontend/src/types/settings.ts`

```typescript
// Based on Pydantic models in new_settings.py
export interface PlexSettings {
  url: string;
  token: string;
  timeout: number;
  verify_ssl: boolean;
}

export interface MediaSettings {
  source_paths: string[];
  cache_path: string;
  file_extensions: string[];
  min_file_size: number;
  max_file_size: number;
}

export interface PerformanceSettings {
  max_concurrent_operations: number;
  cache_check_interval: number;
  cleanup_interval: number;
  log_level: string;
}

export interface RealTimeSettings {
  enabled: boolean;
  check_interval: number;
  max_items: number;
}

export interface TraktSettings {
  enabled: boolean;
  api_key?: string;
  username?: string;
}

export interface CacherrConfiguration {
  plex: PlexSettings;
  media: MediaSettings;
  performance: PerformanceSettings;
  real_time: RealTimeSettings;
  trakt: TraktSettings;
}

export interface ConfigurationResponse {
  status: string;
  data: CacherrConfiguration;
  message?: string;
}
```

#### Step 3: Create Settings API Service
**File**: `/mnt/user/Cursor/Cacherr/frontend/src/services/settingsApi.ts`

```typescript
import { CacherrConfiguration, ConfigurationResponse } from '@/types/settings';

const API_BASE = '/api/config';

export class SettingsApiService {
  static async getCurrentConfig(): Promise<CacherrConfiguration> {
    const response = await fetch(`${API_BASE}/current`);
    if (!response.ok) {
      throw new Error(`Failed to fetch configuration: ${response.statusText}`);
    }
    const result: ConfigurationResponse = await response.json();
    return result.data;
  }

  static async updateConfig(config: Partial<CacherrConfiguration>): Promise<CacherrConfiguration> {
    const response = await fetch(`${API_BASE}/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    
    if (!response.ok) {
      throw new Error(`Failed to update configuration: ${response.statusText}`);
    }
    
    const result: ConfigurationResponse = await response.json();
    return result.data;
  }

  static async testPlexConnection(url: string, token: string): Promise<boolean> {
    const response = await fetch(`${API_BASE}/test-plex`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url, token }),
    });
    
    if (!response.ok) {
      return false;
    }
    
    const result = await response.json();
    return result.status === 'success';
  }

  static async exportConfig(): Promise<string> {
    const response = await fetch(`${API_BASE}/export`);
    if (!response.ok) {
      throw new Error(`Failed to export configuration: ${response.statusText}`);
    }
    return response.text();
  }

  static async importConfig(configData: string): Promise<CacherrConfiguration> {
    const response = await fetch(`${API_BASE}/import`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: configData,
    });
    
    if (!response.ok) {
      throw new Error(`Failed to import configuration: ${response.statusText}`);
    }
    
    const result: ConfigurationResponse = await response.json();
    return result.data;
  }

  static async resetToDefaults(): Promise<CacherrConfiguration> {
    const response = await fetch(`${API_BASE}/reset`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to reset configuration: ${response.statusText}`);
    }
    
    const result: ConfigurationResponse = await response.json();
    return result.data;
  }
}
```

#### Step 4: Create Settings Components

**File**: `/mnt/user/Cursor/Cacherr/frontend/src/components/Settings/PlexSettings.tsx`

```tsx
import React from 'react';
import { PlexSettings as PlexSettingsType } from '@/types/settings';
import { SettingsApiService } from '@/services/settingsApi';

interface PlexSettingsProps {
  settings: PlexSettingsType;
  onChange: (settings: PlexSettingsType) => void;
}

export const PlexSettings: React.FC<PlexSettingsProps> = ({ settings, onChange }) => {
  const [testing, setTesting] = React.useState(false);
  const [testResult, setTestResult] = React.useState<'success' | 'error' | null>(null);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    
    try {
      const success = await SettingsApiService.testPlexConnection(settings.url, settings.token);
      setTestResult(success ? 'success' : 'error');
    } catch (error) {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-white">Plex Server Settings</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Plex Server URL
          </label>
          <input
            type="url"
            value={settings.url}
            onChange={(e) => onChange({ ...settings, url: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="http://192.168.1.100:32400"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Plex Token
          </label>
          <input
            type="password"
            value={settings.token}
            onChange={(e) => onChange({ ...settings, token: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Your Plex authentication token"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Connection Timeout (seconds)
          </label>
          <input
            type="number"
            value={settings.timeout}
            onChange={(e) => onChange({ ...settings, timeout: parseInt(e.target.value) })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="5"
            max="300"
          />
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="verify-ssl"
            checked={settings.verify_ssl}
            onChange={(e) => onChange({ ...settings, verify_ssl: e.target.checked })}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="verify-ssl" className="text-sm font-medium text-gray-300">
            Verify SSL Certificate
          </label>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={handleTestConnection}
            disabled={testing || !settings.url || !settings.token}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>

          {testResult && (
            <span className={`text-sm ${testResult === 'success' ? 'text-green-400' : 'text-red-400'}`}>
              {testResult === 'success' ? '✅ Connection successful' : '❌ Connection failed'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
```

**File**: `/mnt/user/Cursor/Cacherr/frontend/src/components/Settings/MediaSettings.tsx`

```tsx
import React from 'react';
import { MediaSettings as MediaSettingsType } from '@/types/settings';

interface MediaSettingsProps {
  settings: MediaSettingsType;
  onChange: (settings: MediaSettingsType) => void;
}

export const MediaSettings: React.FC<MediaSettingsProps> = ({ settings, onChange }) => {
  const handleSourcePathsChange = (paths: string) => {
    const pathArray = paths.split('\n').filter(path => path.trim() !== '');
    onChange({ ...settings, source_paths: pathArray });
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-white">Media Settings</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Source Media Paths (one per line)
          </label>
          <textarea
            value={settings.source_paths.join('\n')}
            onChange={(e) => handleSourcePathsChange(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={4}
            placeholder="/mnt/user/media/Movies&#10;/mnt/user/media/TV Shows"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Cache Destination Path
          </label>
          <input
            type="text"
            value={settings.cache_path}
            onChange={(e) => onChange({ ...settings, cache_path: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="/mnt/cache/cacherr"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            File Extensions (comma-separated)
          </label>
          <input
            type="text"
            value={settings.file_extensions.join(', ')}
            onChange={(e) => onChange({ 
              ...settings, 
              file_extensions: e.target.value.split(',').map(ext => ext.trim()) 
            })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="mp4, mkv, avi, mov"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Minimum File Size (MB)
            </label>
            <input
              type="number"
              value={settings.min_file_size}
              onChange={(e) => onChange({ ...settings, min_file_size: parseInt(e.target.value) })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="0"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Maximum File Size (GB, 0 = unlimited)
            </label>
            <input
              type="number"
              value={Math.round(settings.max_file_size / 1024)}
              onChange={(e) => onChange({ ...settings, max_file_size: parseInt(e.target.value) * 1024 })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              min="0"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
```

#### Step 5: Create Main Settings Page
**File**: `/mnt/user/Cursor/Cacherr/frontend/src/pages/SettingsPage.tsx`

```tsx
import React from 'react';
import { CacherrConfiguration } from '@/types/settings';
import { SettingsApiService } from '@/services/settingsApi';
import { PlexSettings } from '@/components/Settings/PlexSettings';
import { MediaSettings } from '@/components/Settings/MediaSettings';
import { Loader2, Save, Download, Upload, RotateCcw } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = React.useState<CacherrConfiguration | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState(false);

  React.useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      setError(null);
      const currentConfig = await SettingsApiService.getCurrentConfig();
      setConfig(currentConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveConfiguration = async () => {
    if (!config) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      
      await SettingsApiService.updateConfig(config);
      setSuccess(true);
      
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const exportConfiguration = async () => {
    try {
      const configData = await SettingsApiService.exportConfig();
      const blob = new Blob([configData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cacherr-config-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export configuration');
    }
  };

  const resetToDefaults = async () => {
    if (!confirm('Are you sure you want to reset all settings to default values? This cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);
      const defaultConfig = await SettingsApiService.resetToDefaults();
      setConfig(defaultConfig);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset configuration');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !config) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center space-x-2 text-gray-400">
          <Loader2 className="animate-spin h-5 w-5" />
          <span>Loading settings...</span>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="p-6">
        <div className="bg-red-600 text-white p-4 rounded-md">
          <h3 className="font-semibold">Error Loading Settings</h3>
          <p>{error || 'Failed to load configuration'}</p>
          <button 
            onClick={loadConfiguration}
            className="mt-2 px-4 py-2 bg-red-700 hover:bg-red-800 rounded-md"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={exportConfiguration}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              <Download size={16} />
              <span>Export</span>
            </button>
            
            <button
              onClick={resetToDefaults}
              className="flex items-center space-x-2 px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
            >
              <RotateCcw size={16} />
              <span>Reset to Defaults</span>
            </button>
            
            <button
              onClick={saveConfiguration}
              disabled={saving}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? <Loader2 className="animate-spin h-4 w-4" /> : <Save size={16} />}
              <span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-600 text-white p-4 rounded-md">
            <h3 className="font-semibold">Error</h3>
            <p>{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 bg-green-600 text-white p-4 rounded-md">
            <h3 className="font-semibold">Success</h3>
            <p>Configuration saved successfully!</p>
          </div>
        )}

        <div className="space-y-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <PlexSettings 
              settings={config.plex} 
              onChange={(plex) => setConfig({ ...config, plex })} 
            />
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <MediaSettings 
              settings={config.media} 
              onChange={(media) => setConfig({ ...config, media })} 
            />
          </div>

          {/* Add more settings sections as needed */}
        </div>
      </div>
    </div>
  );
};
```

#### Step 6: Update App Routing
**File**: `/mnt/user/Cursor/Cacherr/frontend/src/App.tsx`

Replace the placeholder settings route:

```tsx
// Replace the existing settings route
<Route path="/settings" element={<SettingsPage />} />
```

#### Step 7: Test Settings Functionality
1. Navigate to `/settings` in the application
2. Verify all form fields load with current values
3. Test form validation and updates
4. Test Plex connection testing
5. Test save functionality
6. Verify mobile responsiveness

### Success Criteria
- [ ] Settings page displays without errors
- [ ] All configuration sections are visible and editable
- [ ] Form validation works correctly
- [ ] Plex connection test works
- [ ] Settings save and persist correctly
- [ ] Export/import functionality works
- [ ] Reset to defaults works
- [ ] Mobile responsive design
- [ ] Consistent with existing UI design

### Files Created
- `frontend/src/types/settings.ts` (TypeScript interfaces)
- `frontend/src/services/settingsApi.ts` (API service)
- `frontend/src/components/Settings/PlexSettings.tsx`
- `frontend/src/components/Settings/MediaSettings.tsx`
- `frontend/src/pages/SettingsPage.tsx` (main page)

### Files Modified
- `frontend/src/App.tsx` (routing update)

---

## 📋 PHASE 2.1B: ENVIRONMENT VARIABLE MIGRATION DOCUMENTATION (HIGH PRIORITY)

### Agent Assignment: `general-purpose`

### Context
After updating project name references, create comprehensive documentation for users to migrate their environment variables from the old PLEXCACHE_* pattern to the new CACHERR_* pattern.

### Pre-Execution Checklist
- [ ] Verify Phase 2.2 completed (remaining name references updated)
- [ ] You understand environment variable patterns and Docker usage
- [ ] You can create clear documentation for end users

### Step-by-Step Instructions

#### Step 1: Create Environment Variable Migration Guide
**File**: `/mnt/user/Cursor/Cacherr/ENVIRONMENT_MIGRATION.md`

```markdown
# 🔄 ENVIRONMENT VARIABLE MIGRATION GUIDE

## Overview
With the project rename from PlexCacheUltra to Cacherr, environment variable names have changed to maintain consistency.

## Migration Mapping

### Required Changes
| Old Variable | New Variable | Description |
|--------------|--------------|-------------|
| `PLEXCACHE_CONFIG_DIR` | `CACHERR_CONFIG_DIR` | Configuration directory |
| `PLEXCACHE_DATA_DIR` | `CACHERR_DATA_DIR` | Data directory |
| `PLEXCACHE_LOG_LEVEL` | `CACHERR_LOG_LEVEL` | Logging level |
| `PLEXCACHE_DEBUG` | `CACHERR_DEBUG` | Debug mode |

### Docker Compose Update
```yaml
# OLD - Remove these
environment:
  - PLEXCACHE_CONFIG_DIR=/app/config
  - PLEXCACHE_DATA_DIR=/app/data

# NEW - Use these instead  
environment:
  - CACHERR_CONFIG_DIR=/app/config
  - CACHERR_DATA_DIR=/app/data
```

### Unraid Template Update
The Unraid template has been updated automatically. Most settings should now be configured via the web interface rather than environment variables.

## Migration Steps
1. Stop your current Cacherr container
2. Update environment variables in your docker-compose.yml or Unraid template
3. Start the container with new variables
4. Verify settings are loaded correctly via the web interface

## Backward Compatibility
The application will continue to recognize old PLEXCACHE_* variables temporarily, but they will be deprecated in future versions.
```

#### Step 2: Update Docker Compose with Migration Notes
**File**: `/mnt/user/Cursor/Cacherr/docker-compose.yml`

Add comments documenting the migration:
```yaml
services:
  cacherr:
    environment:
      # New environment variable format (post-migration)
      # Most settings should now be configured via web UI
      - CACHERR_ENVIRONMENT=production
      - CACHERR_CONFIG_DIR=/app/config
      - CACHERR_DATA_DIR=/app/data
      - CACHERR_LOG_LEVEL=INFO
      
      # Legacy variables (DEPRECATED - will be removed)
      # - PLEXCACHE_CONFIG_DIR=/app/config  # Use CACHERR_CONFIG_DIR instead
      # - PLEXCACHE_DATA_DIR=/app/data      # Use CACHERR_DATA_DIR instead
```

### Context7 Reference
**REQUIRED**: Use Context7 documentation patterns for clear user guides and migration documentation.

### Success Criteria
- [ ] Comprehensive migration guide created
- [ ] All old → new variable mappings documented
- [ ] Docker compose file updated with migration notes
- [ ] User-friendly migration steps provided
- [ ] Backward compatibility notes included

### Files Created
- `/mnt/user/Cursor/Cacherr/ENVIRONMENT_MIGRATION.md`

### Files Modified
- `/mnt/user/Cursor/Cacherr/docker-compose.yml` (migration comments)

---

## 🔄 PHASE 2.2: PROJECT NAME GLOBAL REPLACEMENT (HIGH PRIORITY)

### Agent Assignment: `general-purpose`

### Context
Throughout the codebase, there are 200+ references to the old project names "PlexCacheUltra", "plexcache", "plexcacheultea" that need to be updated to "Cacherr" or "cacherr". This cleanup is essential for professional appearance and consistency.

### Pre-Execution Checklist
- [ ] Verify Phases 1.1, 1.2, and 2.1 are completed successfully
- [ ] Confirm you have tools for global find/replace operations
- [ ] Test that the application is working before starting changes

### Step-by-Step Instructions

#### Step 1: Critical File Updates (Phase 2A)
Update the most critical files first:

**File**: `/mnt/user/Cursor/Cacherr/frontend/package.json`
- Line 5: `"description": "Modern React frontend for PlexCacheUltra dashboard"` 
- **Change to**: `"description": "Modern React frontend for Cacherr dashboard"`

**File**: `/mnt/user/Cursor/Cacherr/__init__.py`
- Line 2: `PlexCacheUltra - Docker-optimized Plex media caching system`
- **Change to**: `Cacherr - Docker-optimized Plex media caching system`
- Line 6: `__author__ = "PlexCacheUltra Team"`
- **Change to**: `__author__ = "Cacherr Team"`

**File**: `/mnt/user/Cursor/Cacherr/main.py`
- Line 223: `description='PlexCacheUltra CLI Operations'`
- **Change to**: `description='Cacherr CLI Operations'`
- Line 299: `"Starting PlexCacheUltra in {run_mode} mode..."`
- **Change to**: `"Starting Cacherr in {run_mode} mode..."`
- Line 311: `"PlexCacheUltra started successfully!"`
- **Change to**: `"Cacherr started successfully!"`
- Line 327: `"Failed to start PlexCacheUltra: {e}"`
- **Change to**: `"Failed to start Cacherr: {e}"`

**File**: `/mnt/user/Cursor/Cacherr/my-cacherr.xml`
- Line 12: Update overview text from "PlexCacheUltra" to "Cacherr"

#### Step 2: Frontend Test Files
**File**: `/mnt/user/Cursor/Cacherr/frontend/src/components/Dashboard/Dashboard.test.tsx`
- Line 85: `expect(screen.getByText('PlexCacheUltra')).toBeInTheDocument()`
- **Change to**: `expect(screen.getByText('Cacherr')).toBeInTheDocument()`
- Line 100: `'Loading PlexCacheUltra Dashboard...'`
- **Change to**: `'Loading Cacherr Dashboard...'`

**File**: `/mnt/user/Cursor/Cacherr/frontend/public/offline.html`
- Line 6: `<title>Offline - PlexCacheUltra</title>`
- **Change to**: `<title>Offline - Cacherr</title>`

#### Step 3: Environment Variables Update (Phase 2B)
Search for and replace environment variable patterns:

**Pattern**: `PLEXCACHE_*` → `CACHERR_*`
**Pattern**: `PLEXCACHEULTRA_*` → `CACHERR_*`

**Files to check**:
- `/mnt/user/Cursor/Cacherr/docs/migration/architecture-migration.md`
- `/mnt/user/Cursor/Cacherr/src/core/service_configuration.py`
- `/mnt/user/Cursor/Cacherr/src/core/DI_SYSTEM_README.md`

#### Step 4: Application Code Updates
**File**: `/mnt/user/Cursor/Cacherr/src/application.py`
- Line 210: `"Starting PlexCacheUltra application..."`
- **Change to**: `"Starting Cacherr application..."`
- Line 283: `"Shutting down PlexCacheUltra application..."`
- **Change to**: `"Shutting down Cacherr application..."`

**File**: `/mnt/user/Cursor/Cacherr/src/core/di_example.py`
- Line 464: `"PlexCacheUltra Dependency Injection System Examples"`
- **Change to**: `"Cacherr Dependency Injection System Examples"`

**File**: `/mnt/user/Cursor/Cacherr/src/core/command_example.py`
- Line 246: `"Starting PlexCacheUltra Command System Demo"`
- **Change to**: `"Starting Cacherr Command System Demo"`

#### Step 5: API Export/Output Updates
**File**: `/mnt/user/Cursor/Cacherr/src/web/routes/api.py`
- Line 1265: `export_data = f"PlexCacheUltra Operation Export\n"`
- **Change to**: `export_data = f"Cacherr Operation Export\n"`
- Line 1965: `"PlexCacheUltra Cached Files Export"`
- **Change to**: `"Cacherr Cached Files Export"`

#### Step 6: Test and Mock Updates
**File**: `/mnt/user/Cursor/Cacherr/tests/mocks/service_mocks.py`
- Line 501: `title: str = "PlexCacheUltra"`
- **Change to**: `title: str = "Cacherr"`
- Line 532: `"This is a test notification from PlexCacheUltra"`
- **Change to**: `"This is a test notification from Cacherr"`

**Files**: `/mnt/user/Cursor/Cacherr/tests/test_secure_cached_files_service.py`
- Lines 676, 687: `user_agent="PlexCacheUltra/1.0"`
- **Change to**: `user_agent="Cacherr/1.0"`

#### Step 7: Cleanup Patterns
**File**: `/mnt/user/Cursor/Cacherr/src/scheduler/tasks/cleanup_tasks.py`
- Line 600: `app_patterns = ["plexcache*", "cacherr*"]`
- **Change to**: `app_patterns = ["cacherr*"]`

#### Step 8: Git Configuration (if needed)
**File**: `/mnt/user/Cursor/Cacherr/.git/config`
- If line 20 contains old repository URL, update to correct repository

#### Step 9: Test Application After Changes
1. Start the backend server
2. Start the frontend
3. Verify the application loads correctly
4. Check that all references in the UI show "Cacherr"
5. Test that functionality still works

### Verification Script
Create and run this verification script to check for remaining references:

```bash
#!/bin/bash
echo "Searching for remaining old project name references..."
echo "=== PlexCacheUltra references ==="
grep -r -i "plexcacheultra" /mnt/user/Cursor/Cacherr/ --exclude-dir=node_modules --exclude-dir=.git --exclude="*.log" || echo "None found"

echo "=== PlexCache references ==="
grep -r -i "plexcache" /mnt/user/Cursor/Cacherr/ --exclude-dir=node_modules --exclude-dir=.git --exclude="*.log" | grep -v "cacherr" || echo "None found"

echo "=== Environment variable patterns ==="
grep -r "PLEXCACHE" /mnt/user/Cursor/Cacherr/ --exclude-dir=node_modules --exclude-dir=.git || echo "None found"
```

### Success Criteria
- [ ] All critical references updated (package.json, main.py, __init__.py)
- [ ] UI displays "Cacherr" instead of old project names
- [ ] Environment variables follow CACHERR_* pattern
- [ ] Application starts and runs correctly after changes
- [ ] No broken references or import errors
- [ ] Verification script shows minimal remaining references

### Files Modified (Complete List)
- `frontend/package.json` (description)
- `__init__.py` (project info)
- `main.py` (CLI messages)
- `my-cacherr.xml` (Unraid template)
- `frontend/src/components/Dashboard/Dashboard.test.tsx` (tests)
- `frontend/public/offline.html` (title)
- `src/application.py` (log messages)
- `src/core/di_example.py` (demo messages)
- `src/core/command_example.py` (demo messages)
- `src/web/routes/api.py` (export messages)
- `tests/mocks/service_mocks.py` (mock data)
- `tests/test_secure_cached_files_service.py` (test data)
- `src/scheduler/tasks/cleanup_tasks.py` (cleanup patterns)
- Various environment variable references

---

## 📝 AGENT HANDOFF PROTOCOL

### For Each Phase Completion

When completing your assigned phase, provide this handoff report:

```markdown
## PHASE [X.X] COMPLETION REPORT

### Agent: [agent-type]
### Date: [date]
### Status: ✅ COMPLETED / ❌ FAILED / ⚠️ PARTIAL

### Tasks Completed:
- [ ] Task 1 description
- [ ] Task 2 description
- [ ] etc.

### Files Modified:
- `file1.py` - Description of changes
- `file2.tsx` - Description of changes

### Files Created:
- `newfile.ts` - Purpose and contents

### Testing Results:
- [ ] Application starts successfully
- [ ] Core functionality tested
- [ ] No critical errors in logs

### Issues Encountered:
(Describe any issues and how they were resolved)

### Notes for Next Agent:
(Any important context for the next phase)

### Verification Commands:
```bash
# Commands to verify this phase worked
```

### READY FOR NEXT PHASE: ✅ YES / ❌ NO
```

### Critical Rules for All Agents

1. **Complete ALL tasks** in your assigned phase before marking as complete
2. **Test functionality** after making changes
3. **Document all changes** in the handoff report
4. **Verify no breaking changes** were introduced
5. **Do not proceed to next phase** - wait for explicit assignment

### Emergency Rollback

If critical errors are introduced:
1. Document the exact error and circumstances
2. Attempt to fix the immediate issue
3. If unable to fix, note the specific changes that need reversal
4. Mark phase as FAILED with detailed error report

---

---

## 🗑️ TASK 5A: LEGACY CONFIGURATION SYSTEM REMOVAL (CLEANUP)

### Agent Type: `python-pro`
### Complexity: 🟡 **INTERMEDIATE** (requires understanding imports and dependencies)
### Dependencies: TASK 3A must be complete (configuration consolidated)
### Can Run Parallel With: TASK 5B, TASK 5C

### Context
After consolidating to the new Pydantic v2.5 configuration system, the old configuration files and their references need to be completely removed to prevent confusion and maintenance issues.

### Pre-Execution Checklist
- [ ] Verify TASK 3A is completed (configuration system consolidated)
- [ ] Confirm you have Python code analysis tools
- [ ] Backup current state before removal

### Step-by-Step Instructions

#### Step 1: Remove Legacy Configuration Files
**Files to Delete Completely**:
- `/mnt/user/Cursor/Cacherr/src/config/old_settings.py`
- Any other files referencing the old configuration classes

#### Step 2: Find and Remove Import References
Search for and remove all imports of old configuration:
```bash
# Search for remaining references
grep -r "from.*old_settings" /mnt/user/Cursor/Cacherr/src/
grep -r "import.*old_settings" /mnt/user/Cursor/Cacherr/src/
```

#### Step 3: Update Any Remaining Code References
- Replace any remaining references to old configuration classes
- Update any instantiation of old config objects
- Remove unused import statements

#### Step 4: Test Configuration Loading
- Start the application to ensure configuration loads properly
- Verify no import errors occur
- Test that settings page still works correctly

### Success Criteria
- [ ] All old configuration files completely removed
- [ ] No import references to old configuration remain
- [ ] Application starts successfully
- [ ] Settings functionality unaffected
- [ ] No Python import errors

### Files Modified/Removed
- Removed: `src/config/old_settings.py`
- Modified: Any files with old configuration imports

---

## 🧹 TASK 5B: REMOVE DEPRECATED COMPONENTS AND FILES (CLEANUP)

### Agent Type: `general-purpose`
### Complexity: 🟡 **INTERMEDIATE** (requires careful analysis of unused code)
### Dependencies: TASK 4B must be complete (functionality verified)
### Can Run Parallel With: TASK 5A, TASK 5C

### Context
Throughout the migration and refactoring process, deprecated components, unused files, and legacy code artifacts have accumulated. These need systematic identification and removal.

### Pre-Execution Checklist
- [ ] Verify TASK 4B is completed (functionality audit passed)
- [ ] Have tools for code analysis and file search
- [ ] Create backup of current state

### Step-by-Step Instructions

#### Step 1: Identify and Remove Duplicate Test Files
**Files to Remove**:
```bash
/mnt/user/Cursor/Cacherr/tests/example.spec.js (duplicate)
/mnt/user/Cursor/Cacherr/tests-examples/ (entire directory)
/mnt/user/Cursor/Cacherr/.npm/ (cached artifacts)
```

#### Step 2: Remove Unused Frontend Components
Search for and analyze:
- Empty or unused React components
- Unused utility files
- Orphaned CSS/style files
- Unused API service methods

**Specific targets**:
- `/mnt/user/Cursor/Cacherr/frontend/src/components/Results/` (empty directory)
- Any placeholder components no longer needed

#### Step 3: Clean Backend Deprecated Code
Look for and remove:
- Unused Python modules
- Deprecated API endpoints
- Old route handlers not in use
- Unused utility functions
- Legacy service implementations

#### Step 4: Remove Build Artifacts and Cache
```bash
# Remove build artifacts
rm -rf /mnt/user/Cursor/Cacherr/frontend/node_modules/.cache/
rm -rf /mnt/user/Cursor/Cacherr/playwright-report/
rm -rf /mnt/user/Cursor/Cacherr/test-results/
```

#### Step 5: Update Import Statements
- Remove imports for deleted files
- Clean up unused imports
- Update any path references

#### Step 6: Test Application After Cleanup
- Build frontend successfully
- Start backend without errors
- Verify all functionality still works
- Check that no broken imports exist

### Success Criteria
- [ ] All identified deprecated files removed
- [ ] No unused components remain
- [ ] Build artifacts cleaned up
- [ ] Application builds and runs successfully
- [ ] No broken imports or references
- [ ] Reduced codebase size and complexity

### Files Removed
- `tests/example.spec.js`
- `tests-examples/` directory
- `.npm/` cached artifacts
- `frontend/src/components/Results/` (empty directory)
- Any other identified deprecated files

---

## 🎨 TASK 5C: CLEAN FRONTEND LEGACY CODE (CLEANUP)

### Agent Type: `react-ui-builder`
### Complexity: 🟡 **INTERMEDIATE** (requires React/TypeScript analysis)
### Dependencies: TASK 2A must be complete (Settings page implemented)
### Can Run Parallel With: TASK 5A, TASK 5B

### Context
With the Settings page now implemented and React migration complete, there may be placeholder code, unused components, or legacy React patterns that need cleanup.

### Pre-Execution Checklist
- [ ] Verify TASK 2A is completed (Settings page working)
- [ ] Have React/TypeScript analysis tools
- [ ] Test that frontend works before cleanup

### Step-by-Step Instructions

#### Step 1: Remove Placeholder Components
- Remove any "coming soon" or placeholder components
- Clean up temporary UI elements
- Remove unused route placeholders

#### Step 2: Clean Up Unused Hooks and Contexts
- Identify unused custom hooks
- Remove unused Context providers
- Clean up unused state management

#### Step 3: Optimize Component Structure
- Remove unused props from components
- Clean up unused component methods
- Remove commented-out code

#### Step 4: Update TypeScript Interfaces
- Remove unused type definitions
- Clean up unused interface properties
- Optimize type imports

#### Step 5: Clean CSS and Styling
- Remove unused CSS classes
- Clean up unused Tailwind utilities
- Remove redundant styling

#### Step 6: Test Frontend After Cleanup
- All pages load correctly
- All interactions work properly
- No TypeScript errors
- No console warnings
- Mobile responsive still works

### Success Criteria
- [ ] No placeholder or "coming soon" components remain
- [ ] Unused React code removed
- [ ] TypeScript interfaces optimized
- [ ] CSS/styling cleaned up
- [ ] Frontend builds without warnings
- [ ] All functionality preserved

### Files Modified
- React components with unused code
- TypeScript interface files
- CSS/styling files
- Route configuration

---

## 🧪 TASK 6A: COMPREHENSIVE BACKEND TESTING SUITE (TESTING)

### Agent Type: `python-pro`
### Complexity: 🔴 **COMPLEX** (requires extensive Python testing knowledge)
### Dependencies: TASK 5A must be complete (legacy cleanup done)
### Can Run Parallel With: NONE - sequential only

### Context
Create a comprehensive testing suite for all backend functionality, including unit tests, integration tests, and API endpoint testing. This ensures reliability and catches regressions.

### Pre-Execution Checklist
- [ ] Verify TASK 5A completed (no legacy config issues)
- [ ] Have Python testing frameworks available (pytest, etc.)
- [ ] Backend application running successfully

### Step-by-Step Instructions

#### Step 1: Set Up Testing Framework
- Configure pytest with proper test discovery
- Set up test configuration and fixtures
- Create test database/mock setups

#### Step 2: Unit Tests for Core Services
**Test Coverage Required**:
- Configuration system (Pydantic models)
- Media file services
- Cache management services
- Plex API integration
- Trakt API integration (if enabled)
- WebSocket manager
- File operations (atomic redirects)

#### Step 3: API Endpoint Testing
**Test All Endpoints**:
```python
# Test health endpoints
/api/health
/api/status

# Test configuration endpoints
/api/config/current
/api/config/update
/api/config/test-plex

# Test media endpoints
/api/media/cached
/api/media/operations
/api/media/status

# Test authentication/security
```

#### Step 4: Integration Testing
- Test service-to-service communication
- Test database interactions
- Test file system operations
- Test external API integrations (Plex/Trakt)

#### Step 5: Error Handling Testing
- Test error conditions and edge cases
- Test network failures
- Test invalid configurations
- Test permission issues

#### Step 6: Performance Testing
- Test concurrent operations
- Test large file handling
- Test API response times
- Test memory usage patterns

#### Step 7: Create Test Reports
- Generate coverage reports (target: >80% coverage)
- Document test results
- Create performance benchmarks

### Success Criteria
- [ ] Comprehensive unit test suite (>80% coverage)
- [ ] All API endpoints tested
- [ ] Integration tests passing
- [ ] Error handling tests complete
- [ ] Performance benchmarks established
- [ ] Test suite runs in <5 minutes
- [ ] All tests pass consistently

### Files Created
- `tests/unit/` (comprehensive unit tests)
- `tests/integration/` (integration tests)
- `tests/api/` (API endpoint tests)
- `tests/conftest.py` (test configuration)
- `pytest.ini` (pytest configuration)

---

## 🎭 TASK 6B: COMPLETE PLAYWRIGHT FRONTEND TESTING (TESTING)

### Agent Type: `react-ui-builder`
### Complexity: 🔴 **COMPLEX** (requires Playwright and React testing expertise)
### Dependencies: TASK 6A must be complete (backend tests passing)
### Can Run Parallel With: NONE - sequential only

### Context
Create comprehensive end-to-end tests using Playwright to ensure all frontend functionality works correctly, including user interactions, responsive design, and error handling.

### Pre-Execution Checklist
- [ ] Verify TASK 6A completed (backend tests passing)
- [ ] Backend and frontend running successfully
- [ ] Playwright test environment configured

### Step-by-Step Instructions

#### Step 1: Expand Playwright Test Suite
**Test Coverage Required**:
- Dashboard functionality (all tabs)
- Settings page (complete flow)
- Navigation and routing
- User interactions (forms, buttons, etc.)
- Real-time updates (WebSocket)
- Error handling and edge cases
- Mobile responsive behavior

#### Step 2: Dashboard Testing
```typescript
// Test all dashboard tabs
test('Dashboard - All tabs load and display data', async ({ page }) => {
  // Test Dashboard tab
  // Test Cached tab  
  // Test Logs tab
  // Verify data loads correctly
  // Test tab switching
});

// Test real-time updates
test('Dashboard - WebSocket updates work correctly', async ({ page }) => {
  // Test connection status
  // Test real-time data updates
  // Test error handling when WebSocket fails
});
```

#### Step 3: Settings Page Testing
```typescript
test('Settings - Complete configuration flow', async ({ page }) => {
  // Test all form sections
  // Test form validation
  // Test Plex connection testing
  // Test save functionality
  // Test export/import
  // Test reset to defaults
});
```

#### Step 4: Responsive Design Testing
- Test mobile layouts (320px, 768px, 1024px, 1920px)
- Test tablet interactions
- Test touch vs mouse interactions
- Test navigation on small screens

#### Step 5: Error Handling Testing
- Test network failures
- Test API error responses
- Test invalid form inputs
- Test browser compatibility

#### Step 6: Performance Testing
- Test page load times
- Test large data sets
- Test memory usage
- Test CPU usage patterns

#### Step 7: Cross-Browser Testing
- Test Chrome (primary)
- Test Firefox
- Test Safari (if available)
- Test Edge

#### Step 8: Create Separate Test Docker
**Create `/mnt/user/Cursor/Cacherr/Dockerfile.playwright`**:
```dockerfile
FROM mcr.microsoft.com/playwright:v1.47.0-jammy

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY playwright.config.js ./

# Install dependencies  
RUN npm ci

# Copy test files only
COPY e2e/ ./e2e/

# Install only Chromium for main tests
RUN npx playwright install chromium --with-deps

# Command for running tests
CMD ["npx", "playwright", "test"]
```

### Success Criteria
- [ ] All user flows tested end-to-end
- [ ] Dashboard functionality fully tested
- [ ] Settings page completely tested  
- [ ] Responsive design verified
- [ ] Error handling tested
- [ ] Performance benchmarks established
- [ ] Cross-browser compatibility verified
- [ ] Test Docker separate from production
- [ ] Tests run in <10 minutes
- [ ] All tests pass consistently

### Files Created/Modified
- Enhanced `e2e/` test suite
- `Dockerfile.playwright` (separate test container)
- Updated `playwright.config.js`
- Test documentation and reports

---

## 🔍 TASK 6C: END-TO-END INTEGRATION TESTING & PRODUCTION VALIDATION (TESTING)

### Agent Type: `production-code-auditor`
### Complexity: 🔴 **COMPLEX** (requires full-stack testing and validation)
### Dependencies: TASK 6B must be complete (frontend tests passing)
### Can Run Parallel With: NONE - sequential only

### Context
Perform final comprehensive testing of the entire system, including production-like scenarios, security validation, performance testing, and deployment verification.

### Pre-Execution Checklist
- [ ] Verify TASK 6B completed (frontend tests passing)
- [ ] All previous tasks completed successfully
- [ ] Production Docker image available
- [ ] Test environment configured

### Step-by-Step Instructions

#### Step 1: Production Docker Testing
- Build production Docker image
- Test container startup and health checks
- Verify image size (<500MB target)
- Test container resource usage
- Test container restart behavior

#### Step 2: End-to-End Workflow Testing
**Test Complete User Workflows**:
- Initial setup and configuration
- Plex server connection and authentication
- Media file discovery and caching
- Real-time monitoring and updates
- Settings changes and persistence
- System restart and recovery

#### Step 3: Security Validation
- Test authentication and authorization
- Validate input sanitization
- Test for common vulnerabilities (OWASP Top 10)
- Verify sensitive data handling
- Test API security headers
- Validate configuration security

#### Step 4: Performance Validation
- Test concurrent user scenarios
- Test large media file operations
- Test system under load
- Validate memory usage patterns
- Test database performance
- Measure API response times

#### Step 5: Integration Testing
- Test Plex server integration
- Test Trakt integration (if enabled)
- Test file system operations
- Test atomic redirects functionality
- Test WebSocket communication
- Test error recovery scenarios

#### Step 6: Deployment Testing
- Test Docker deployment process
- Test Unraid integration
- Test configuration persistence
- Test logging and monitoring
- Test backup and recovery

#### Step 7: Regression Testing
- Re-run all critical user flows
- Verify no functionality lost during refactoring
- Test backward compatibility where relevant
- Verify performance hasn't degraded

#### Step 8: Create Production Readiness Report
**Comprehensive Report Including**:
- All test results and coverage
- Performance benchmarks
- Security assessment results
- Deployment validation
- Known issues and limitations
- Recommended monitoring and maintenance

### Success Criteria
- [ ] Production Docker image builds and runs correctly
- [ ] All end-to-end workflows tested and working
- [ ] Security validation passed
- [ ] Performance meets requirements
- [ ] All integrations working properly
- [ ] Deployment process validated
- [ ] No regressions identified
- [ ] Production readiness report complete
- [ ] Zero critical or high-severity issues
- [ ] System ready for production deployment

### Deliverables
- Production readiness report
- Complete test results documentation
- Performance benchmark report
- Security assessment report
- Deployment guide validation
- Monitoring and maintenance recommendations

---

---

## 🔧 TASK 2A2: IMPLEMENT PLEX SETTINGS COMPONENT (HIGH PRIORITY)

### Agent Type: `react-ui-builder`
### Complexity: 🟡 **INTERMEDIATE** (requires React forms and validation)
### Dependencies: TASK 2A must be complete (interfaces created)
### Can Run Parallel With: TASK 2A3, TASK 2A4

### Context
Create the Plex Settings component that handles Plex server configuration, including URL, token, connection testing, and SSL verification. This component will be integrated into the main Settings page.

### Pre-Execution Checklist
- [ ] Verify TASK 2A is completed (TypeScript interfaces ready)
- [ ] Confirm you have React form handling knowledge
- [ ] Test that backend Plex API endpoints work

### Step-by-Step Instructions

#### Step 1: Create Plex Settings Component
Create `/mnt/user/Cursor/Cacherr/frontend/src/components/Settings/PlexSettings.tsx` with comprehensive documentation and comments explaining every function.

#### Step 2: Implement Connection Testing
- Add "Test Connection" functionality with loading states
- Provide clear success/error feedback
- Handle network timeouts gracefully

#### Step 3: Add Form Validation  
- Client-side validation for URL format and token
- Range validation for timeout settings
- Real-time validation feedback

### Context7 Reference
Use Context7 React documentation for form handling best practices.

### Code Quality Requirements
- **Extensive Comments**: Every function, component, and complex logic must have detailed comments
- **JSDoc Documentation**: Full component and prop documentation
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Self-Documenting**: Code should be understandable by someone unfamiliar with the project

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A2 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A2 status to "completed"

### Success Criteria
- [ ] Component renders and functions correctly
- [ ] Connection testing works
- [ ] Form validation provides clear feedback
- [ ] Mobile responsive design
- [ ] Comprehensive comments and documentation

### Files Created
- `frontend/src/components/Settings/PlexSettings.tsx`

### Files Modified
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## 📁 TASK 2A3: IMPLEMENT MEDIA SETTINGS COMPONENT (HIGH PRIORITY)

### Agent Type: `react-ui-builder`
### Complexity: 🟡 **INTERMEDIATE** (requires React forms)
### Dependencies: TASK 2A must be complete (interfaces created)
### Can Run Parallel With: TASK 2A2, TASK 2A4

### Context
Create the Media Settings component for configuring media processing options including source paths, file extensions, size limits, and cache destinations.

### Pre-Execution Checklist
- [ ] Verify TASK 2A is completed (TypeScript interfaces ready)
- [ ] Understand media file processing requirements
- [ ] Review existing media configuration patterns

### Step-by-Step Instructions

#### Step 1: Create Media Settings Component
Create `/mnt/user/Cursor/Cacherr/frontend/src/components/Settings/MediaSettings.tsx` with extensive comments explaining multi-path handling and validation logic.

#### Step 2: Implement Advanced Form Controls
- Multi-line textarea for source paths with validation
- Dynamic file extension management
- Size limit inputs with unit conversion (MB/GB)

#### Step 3: Add Path Validation
- Validate path formats and check for duplicates
- Provide suggestions for common media directories
- Warn about potential permission issues

### Context7 Reference
Use Context7 React patterns for complex form controls.

### Code Quality Requirements
- **Path Handling Documentation**: Explain how multi-path input processing works
- **Validation Comments**: Clear explanation of validation rules and edge cases
- **Unit Conversion Logic**: Document size unit conversion implementation

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A3 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A3 status to "completed"

### Success Criteria
- [ ] Media Settings component renders correctly
- [ ] Multi-path input functionality works
- [ ] File extension management functional
- [ ] Size limit conversion accurate
- [ ] Form validation clear and helpful

### Files Created
- `frontend/src/components/Settings/MediaSettings.tsx`

### Files Modified
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## ⚡ TASK 2A4: IMPLEMENT PERFORMANCE & ADVANCED SETTINGS COMPONENTS (HIGH PRIORITY)

### Agent Type: `react-ui-builder`
### Complexity: 🟡 **INTERMEDIATE** (requires React forms)
### Dependencies: TASK 2A must be complete (interfaces created)
### Can Run Parallel With: TASK 2A2, TASK 2A3

### Context
Create components for performance tuning and advanced settings including concurrency limits, intervals, Trakt integration, and real-time monitoring configuration.

### Pre-Execution Checklist
- [ ] Verify TASK 2A is completed (TypeScript interfaces ready)
- [ ] Understand performance implications of settings
- [ ] Review Trakt API integration requirements

### Step-by-Step Instructions

#### Step 1: Create Performance Settings Component
Create `/mnt/user/Cursor/Cacherr/frontend/src/components/Settings/PerformanceSettings.tsx` with detailed comments on how each setting affects system performance.

#### Step 2: Create Advanced Settings Component  
Create `/mnt/user/Cursor/Cacherr/frontend/src/components/Settings/AdvancedSettings.tsx` for Trakt integration and advanced features.

#### Step 3: Add Validation and Helpers
- Range controls with recommended values
- Performance impact warnings for extreme values
- Trakt API key validation

### Context7 Reference
Use Context7 React patterns for complex form controls and validation.

### Code Quality Requirements
- **Performance Impact Documentation**: Explain how each setting affects system behavior
- **Integration Comments**: Clear documentation of external service integration logic
- **Validation Rules**: Document acceptable ranges and their rationales

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A4 status to "in_progress"  
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A4 status to "completed"

### Success Criteria
- [ ] Performance Settings component functional
- [ ] Advanced Settings component functional
- [ ] All validation working correctly
- [ ] Performance warnings implemented
- [ ] Trakt integration settings complete

### Files Created
- `frontend/src/components/Settings/PerformanceSettings.tsx`
- `frontend/src/components/Settings/AdvancedSettings.tsx`

### Files Modified
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## 🔗 TASK 2A5: IMPLEMENT MAIN SETTINGS PAGE AND INTEGRATION (HIGH PRIORITY)

### Agent Type: `react-ui-builder`
### Complexity: 🟡 **INTERMEDIATE** (requires React state management)
### Dependencies: TASK 2A2, 2A3, 2A4 must be complete (all components ready)
### Can Run Parallel With: NONE - sequential only

### Context
Create the main Settings page that integrates all individual settings components, handles global state management, save/load operations, and provides a cohesive user experience.

### Pre-Execution Checklist
- [ ] Verify TASK 2A2, 2A3, 2A4 are completed (all components ready)
- [ ] Test individual components work correctly
- [ ] Confirm backend settings API is functional

### Step-by-Step Instructions

#### Step 1: Create Main Settings Page
Create `/mnt/user/Cursor/Cacherr/frontend/src/pages/SettingsPage.tsx` with comprehensive documentation on state management and component coordination.

#### Step 2: Implement Global State Management
- Load configuration on mount with error handling
- Track changes across all child components
- Implement save/export/import/reset functionality

#### Step 3: Add Settings Organization
- Organize into logical sections with navigation
- Implement mobile-friendly collapsible sections
- Add search/filter functionality

### Context7 Reference
Use Context7 React state management patterns for complex application state.

### Code Quality Requirements
- **State Flow Documentation**: Explain how state flows between components
- **Integration Logic**: Document component communication patterns
- **Error Recovery**: Comprehensive error handling with user guidance

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A5 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 2A5 status to "completed"

### Success Criteria
- [ ] Main Settings page integrates all components
- [ ] Save/load operations work end-to-end
- [ ] Export/import functionality complete
- [ ] Reset to defaults functional
- [ ] Mobile responsive design
- [ ] Comprehensive error handling

### Files Created
- `frontend/src/pages/SettingsPage.tsx`

### Files Modified
- `frontend/src/App.tsx` (routing update)
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

## 🐍 TASK 3A2: ENSURE PYDANTIC V2.5 COMPLIANCE (OPTIMIZATION)

### Agent Type: `python-pro`
### Complexity: 🟡 **INTERMEDIATE** (requires Pydantic v2.5 knowledge)
### Dependencies: TASK 3A must be complete (imports updated)
### Can Run Parallel With: NONE - sequential only

### Context
Ensure all Python code uses the latest Pydantic v2.5 patterns, type hints, and validation features. This includes updating models, validators, and configuration patterns.

### Pre-Execution Checklist
- [ ] Verify TASK 3A is completed (configuration imports updated)
- [ ] Have Context7 Pydantic documentation available
- [ ] Test current Pydantic functionality

### Step-by-Step Instructions

#### Step 1: Update Pydantic Model Patterns
Review all Pydantic models and update to v2.5 patterns:

```python
# Example of Pydantic v2.5 compliance with extensive comments
from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

class CacherrConfiguration(BaseModel):
    """
    Main configuration model for the Cacherr application.
    
    This model defines the complete configuration schema using Pydantic v2.5
    patterns including proper type annotations, field validation, and
    configuration settings optimized for performance and clarity.
    
    Attributes:
        model_config: Pydantic v2.5 configuration settings
        plex_url: Plex server URL with validation for proper format
        cache_path: Filesystem path where cached files are stored
        max_file_size: Maximum file size for caching in bytes
        created_at: Timestamp of configuration creation
    """
    model_config = ConfigDict(
        # Enable strict mode for better type checking
        strict=True,
        # Validate assignments to catch errors early
        validate_assignment=True,
        # Strip whitespace from string fields
        str_strip_whitespace=True,
        # Use enum values instead of names for serialization
        use_enum_values=True,
        # Validate default values
        validate_default=True
    )
    
    plex_url: Annotated[
        str, 
        Field(
            ..., 
            description="Plex server URL including protocol and port",
            examples=["http://192.168.1.100:32400", "https://plex.example.com"],
            pattern=r"^https?://[a-zA-Z0-9.-]+(?::[0-9]+)?$"
        )
    ]
    
    cache_path: Annotated[
        str,
        Field(
            ...,
            description="Absolute filesystem path for cached media files",
            examples=["/mnt/cache/cacherr", "/cache/media"],
            min_length=1
        )
    ]
    
    @field_validator('cache_path')
    @classmethod
    def validate_cache_path(cls, v: str) -> str:
        """
        Validate that cache_path is an absolute path.
        
        Args:
            v: The cache path string to validate
            
        Returns:
            The validated cache path
            
        Raises:
            ValueError: If path is not absolute or not accessible
        """
        from pathlib import Path
        
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("Cache path must be absolute")
        
        return v
```

#### Step 2: Update All Configuration Models
- Apply Pydantic v2.5 patterns to all models in `new_settings.py`
- Add comprehensive field documentation
- Implement custom validators with detailed comments
- Add model configuration optimizations

#### Step 3: Test Pydantic Compliance
1. Verify all models validate correctly
2. Test serialization/deserialization
3. Validate error messages are user-friendly
4. Confirm performance optimizations work

### Context7 Reference
**REQUIRED**: Use Context7 Pydantic documentation extensively for v2.5 best practices, validation patterns, and performance optimization.

### Code Quality Requirements
- **Model Documentation**: Every model needs comprehensive docstrings
- **Field Comments**: Each field must have clear descriptions and examples
- **Validator Comments**: All validators need detailed explanations
- **Type Hints**: Use Annotated types with rich metadata
- **Configuration Comments**: Explain each ConfigDict setting

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 3A2 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 3A2 status to "completed"

### Success Criteria
- [ ] All models use Pydantic v2.5 patterns
- [ ] Comprehensive model documentation added
- [ ] Custom validators properly implemented
- [ ] Configuration optimization applied
- [ ] All tests pass with new patterns
- [ ] Performance improvements verified

### Files Modified
- `/mnt/user/Cursor/Cacherr/src/core/new_settings.py` (Pydantic v2.5 compliance)
- Any other files with Pydantic models
- `/mnt/user/Cursor/Cacherr/CACHERR_REFACTORING_MASTER_PLAN.md` (task status updates)

---

---

## 🧪 TASK 6A2: CREATE BACKEND UNIT TESTS (TESTING)

### Agent Type: `python-pro`
### Complexity: 🔴 **COMPLEX** (requires comprehensive Python testing)
### Dependencies: TASK 6A must be complete (testing framework setup)
### Can Run Parallel With: NONE - sequential only

### Context
Create comprehensive unit tests for all backend services, models, and utilities. Focus on testing individual components in isolation with proper mocking and edge case coverage.

### Pre-Execution Checklist
- [ ] Verify TASK 6A completed (testing framework configured)
- [ ] Have pytest and testing libraries available
- [ ] Backend services are identifiable and testable

### Step-by-Step Instructions

#### Step 1: Create Service Unit Tests
Create comprehensive unit tests for core services:

**File**: `/mnt/user/Cursor/Cacherr/tests/unit/test_media_service.py`
```python
"""
Unit tests for MediaService class.

This module tests all MediaService functionality in isolation,
including file operations, cache management, and error handling.
Tests use mocking to avoid filesystem dependencies and ensure
fast, reliable test execution.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.services.media_service import MediaService
from src.core.new_settings import MediaSettings

class TestMediaService:
    """
    Test suite for MediaService class.
    
    Tests cover all major functionality including file discovery,
    cache operations, validation, and error conditions. Each test
    is isolated using mocks to prevent filesystem side effects.
    """
    
    @pytest.fixture
    def media_settings(self):
        """Create mock media settings for testing."""
        return MediaSettings(
            source_paths=["/test/media", "/test/movies"],
            cache_path="/test/cache",
            file_extensions=["mp4", "mkv"],
            min_file_size=100,
            max_file_size=5000
        )
    
    @pytest.fixture
    def media_service(self, media_settings):
        """Create MediaService instance with mocked dependencies."""
        return MediaService(media_settings)
    
    def test_discover_media_files_success(self, media_service):
        """
        Test successful media file discovery.
        
        Verifies that the service correctly identifies valid media files
        from configured source paths and applies size/extension filtering.
        """
        # Test implementation with detailed assertions
        pass
    
    def test_cache_file_atomic_operation(self, media_service):
        """
        Test atomic file caching operation.
        
        Ensures that file caching operations are atomic (all-or-nothing)
        and don't leave partial files in the cache directory during failures.
        """
        # Test atomic operation implementation
        pass
```

#### Step 2: Create Pydantic Model Tests
**File**: `/mnt/user/Cursor/Cacherr/tests/unit/test_configuration_models.py`
```python
"""
Unit tests for Pydantic configuration models.

Tests all validation rules, serialization/deserialization,
and edge cases for configuration models. Ensures Pydantic v2.5
compliance and proper error handling.
"""
import pytest
from pydantic import ValidationError
from src.core.new_settings import CacherrConfiguration, PlexSettings

class TestPydanticModels:
    """Test Pydantic v2.5 model validation and serialization."""
    
    def test_plex_settings_url_validation(self):
        """
        Test URL validation in PlexSettings model.
        
        Ensures that Plex URLs are properly validated for format,
        protocol, and common edge cases like missing ports or
        invalid characters.
        """
        # Valid URL formats
        valid_urls = [
            "http://192.168.1.100:32400",
            "https://plex.example.com:32400",
            "http://localhost:32400"
        ]
        
        # Invalid URL formats that should raise ValidationError
        invalid_urls = [
            "not-a-url",
            "ftp://invalid-protocol.com",
            "http://",
            ""
        ]
        
        # Test implementations with clear assertions
        pass
```

#### Step 3: Create Utility Function Tests
Test all utility functions with comprehensive edge case coverage:

**File**: `/mnt/user/Cursor/Cacherr/tests/unit/test_file_utils.py`
```python
"""
Unit tests for file utility functions.

Tests file operation utilities including path validation,
atomic operations, permission checking, and error handling.
All tests use temporary directories and mocking to avoid
affecting the actual filesystem.
"""
# Comprehensive utility testing implementation
```

### Context7 Reference
**REQUIRED**: Use Context7 pytest documentation for advanced testing patterns, fixtures, and mocking strategies.

### Code Quality Requirements
- **Test Documentation**: Every test method needs clear docstrings explaining what is tested
- **Fixture Comments**: Explain the purpose and setup of each pytest fixture
- **Assertion Messages**: Use descriptive assertion messages for debugging
- **Edge Case Coverage**: Test boundary conditions, error cases, and invalid inputs
- **Mock Explanations**: Comment why mocks are used and what they represent

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6A2 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6A2 status to "completed"

### Success Criteria
- [ ] All service classes have comprehensive unit tests
- [ ] Pydantic models thoroughly tested
- [ ] Utility functions covered with edge cases
- [ ] >80% code coverage for tested components
- [ ] All tests run in <2 minutes
- [ ] Zero test failures or flaky tests

### Files Created
- `tests/unit/test_media_service.py`
- `tests/unit/test_configuration_models.py`
- `tests/unit/test_file_utils.py`
- `tests/unit/test_plex_service.py`
- Additional unit test files as needed

---

## 🔗 TASK 6A3: CREATE BACKEND API INTEGRATION TESTS (TESTING)

### Agent Type: `python-pro` 
### Complexity: 🔴 **COMPLEX** (requires API testing expertise)
### Dependencies: TASK 6A2 must be complete (unit tests passing)
### Can Run Parallel With: NONE - sequential only

### Context
Create comprehensive API integration tests that verify all backend endpoints, request/response handling, authentication, error conditions, and data flow between services.

### Pre-Execution Checklist
- [ ] Verify TASK 6A2 completed (unit tests passing)
- [ ] Backend API endpoints are functional
- [ ] Have API testing libraries (requests, httpx, etc.)

### Step-by-Step Instructions

#### Step 1: Create API Test Framework
**File**: `/mnt/user/Cursor/Cacherr/tests/integration/conftest.py`
```python
"""
Pytest configuration and fixtures for API integration tests.

Provides reusable fixtures for API testing including test client setup,
authentication handling, database cleanup, and common test data.
All fixtures are designed to be isolated and not affect production data.
"""
import pytest
from fastapi.testclient import TestClient
from src.web.app import create_app

@pytest.fixture
def api_client():
    """
    Create a test client for API integration testing.
    
    This fixture provides a FastAPI test client configured for testing
    with isolated database connections and mocked external dependencies.
    The client automatically handles request/response serialization.
    
    Returns:
        TestClient: Configured test client for API requests
    """
    app = create_app(testing=True)
    return TestClient(app)

@pytest.fixture
def sample_config():
    """Create sample configuration data for testing."""
    return {
        "plex": {
            "url": "http://test-plex:32400",
            "token": "test-token",
            "timeout": 30,
            "verify_ssl": False
        },
        "media": {
            "source_paths": ["/test/media"],
            "cache_path": "/test/cache", 
            "file_extensions": ["mp4", "mkv"],
            "min_file_size": 100,
            "max_file_size": 5000
        }
    }
```

#### Step 2: Test Configuration Endpoints
**File**: `/mnt/user/Cursor/Cacherr/tests/integration/test_config_api.py`
```python
"""
Integration tests for configuration API endpoints.

Tests the complete configuration management flow including
getting current config, updating settings, validation,
and error handling. Verifies proper HTTP status codes
and response formats.
"""
import pytest
from fastapi import status

class TestConfigurationAPI:
    """Test suite for /api/config endpoints."""
    
    def test_get_current_config_success(self, api_client):
        """
        Test successful retrieval of current configuration.
        
        Verifies that the /api/config/current endpoint returns
        valid configuration data with proper structure and
        HTTP 200 status code.
        """
        response = api_client.get("/api/config/current")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert data["status"] == "success"
        
        # Verify configuration structure
        config = data["data"]
        assert "plex" in config
        assert "media" in config
        assert "performance" in config
        
        # Test implementation continues...
        
    def test_update_config_validation_error(self, api_client):
        """
        Test configuration update with validation errors.
        
        Ensures that invalid configuration data is rejected
        with appropriate error messages and HTTP 422 status.
        """
        invalid_config = {
            "plex": {
                "url": "not-a-valid-url",  # Invalid URL format
                "token": "",  # Empty token
                "timeout": -1  # Invalid timeout
            }
        }
        
        response = api_client.post("/api/config/update", json=invalid_config)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Verify error response structure
        error_data = response.json()
        assert "detail" in error_data
        # Test continues with detailed validation...
```

#### Step 3: Test Media API Endpoints  
**File**: `/mnt/user/Cursor/Cacherr/tests/integration/test_media_api.py`
```python
"""
Integration tests for media management API endpoints.

Tests media file operations including listing cached files,
triggering cache operations, monitoring progress, and
handling various media file scenarios.
"""
# Comprehensive media API testing implementation
```

#### Step 4: Test WebSocket Integration
**File**: `/mnt/user/Cursor/Cacherr/tests/integration/test_websocket_api.py`
```python
"""
Integration tests for WebSocket functionality.

Tests real-time communication including connection establishment,
message broadcasting, client disconnection handling, and
error recovery scenarios.
"""
# WebSocket testing implementation with proper async handling
```

### Context7 Reference
**REQUIRED**: Use Context7 FastAPI testing documentation for API testing best practices, async testing, and WebSocket testing patterns.

### Code Quality Requirements
- **API Test Documentation**: Clear explanation of what each endpoint test verifies
- **Request/Response Comments**: Document expected request formats and response structures  
- **Error Scenario Testing**: Comprehensive coverage of error conditions and status codes
- **Authentication Testing**: Document security testing approach and edge cases
- **Data Flow Comments**: Explain how data flows through the API layers

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6A3 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6A3 status to "completed"

### Success Criteria
- [ ] All API endpoints thoroughly tested
- [ ] Request/response validation comprehensive
- [ ] Authentication and security tested
- [ ] WebSocket functionality verified
- [ ] Error handling scenarios covered
- [ ] Integration tests run in <3 minutes
- [ ] Zero flaky or unreliable tests

### Files Created
- `tests/integration/conftest.py` (test configuration)
- `tests/integration/test_config_api.py`
- `tests/integration/test_media_api.py`
- `tests/integration/test_websocket_api.py`
- `tests/integration/test_health_api.py`

---

## 🎭 TASK 6B2: CREATE DASHBOARD PLAYWRIGHT TESTS (TESTING)

### Agent Type: `react-ui-builder`
### Complexity: 🔴 **COMPLEX** (requires Playwright expertise)
### Dependencies: TASK 6B must be complete (Playwright framework setup)
### Can Run Parallel With: NONE - sequential only

### Context
Create comprehensive end-to-end tests for the Dashboard functionality using Playwright. Test all dashboard tabs, real-time updates, user interactions, and responsive behavior.

### Pre-Execution Checklist
- [ ] Verify TASK 6B completed (Playwright framework configured)
- [ ] Dashboard is fully functional
- [ ] Backend API is providing test data

### Step-by-Step Instructions

#### Step 1: Create Dashboard Test Base
**File**: `/mnt/user/Cursor/Cacherr/e2e/dashboard.spec.ts`
```typescript
/**
 * End-to-end tests for Dashboard functionality.
 * 
 * This test suite covers all Dashboard features including:
 * - Tab navigation and content loading
 * - Real-time data updates via WebSocket
 * - Interactive elements and user actions
 * - Responsive design across different screen sizes
 * - Error handling and recovery scenarios
 */
import { test, expect, Page } from '@playwright/test';

/**
 * Test group for Dashboard core functionality.
 * 
 * These tests verify that the dashboard loads correctly,
 * displays data, and handles user interactions properly.
 */
test.describe('Dashboard Core Functionality', () => {
  
  /**
   * Test that Dashboard page loads and displays all required elements.
   * 
   * Verifies:
   * - Page loads without errors
   * - Navigation tabs are visible
   * - Default tab content is displayed
   * - No JavaScript console errors
   */
  test('Dashboard loads with all tabs visible', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
    
    // Wait for dashboard to load completely
    await expect(page.locator('[data-testid="dashboard-container"]')).toBeVisible();
    
    // Verify all tab buttons are present
    await expect(page.locator('[data-testid="dashboard-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="cached-tab"]')).toBeVisible();
    await expect(page.locator('[data-testid="logs-tab"]')).toBeVisible();
    
    // Verify default tab (Dashboard) is active
    await expect(page.locator('[data-testid="dashboard-tab"][aria-selected="true"]')).toBeVisible();
    
    // Check that dashboard content is loaded
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
  });
  
  /**
   * Test tab navigation functionality.
   * 
   * Verifies that clicking tabs switches content properly
   * and maintains proper state management.
   */
  test('Tab navigation switches content correctly', async ({ page }) => {
    await page.goto('/');
    
    // Start on Dashboard tab
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    
    // Switch to Cached tab
    await page.click('[data-testid="cached-tab"]');
    await expect(page.locator('[data-testid="cached-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeHidden();
    
    // Switch to Logs tab
    await page.click('[data-testid="logs-tab"]');
    await expect(page.locator('[data-testid="logs-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="cached-content"]')).toBeHidden();
    
    // Switch back to Dashboard
    await page.click('[data-testid="dashboard-tab"]');
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });
});
```

#### Step 2: Test Real-Time Updates
```typescript
/**
 * Test WebSocket real-time updates functionality.
 * 
 * These tests verify that the dashboard receives and displays
 * real-time updates from the backend via WebSocket connections.
 */
test.describe('Real-Time Updates', () => {
  
  /**
   * Test WebSocket connection and data updates.
   * 
   * Verifies that the dashboard establishes WebSocket connection
   * and updates content when new data is received.
   */
  test('WebSocket updates dashboard data in real-time', async ({ page }) => {
    // Set up WebSocket monitoring
    const wsMessages: string[] = [];
    
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        wsMessages.push(event.payload);
      });
    });
    
    await page.goto('/');
    
    // Wait for WebSocket connection
    await page.waitForFunction(() => {
      return window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN;
    });
    
    // Trigger backend operation that sends WebSocket update
    // (This would involve calling a backend API that triggers updates)
    
    // Verify that dashboard content updates
    // Implementation continues with specific assertions...
  });
});
```

#### Step 3: Test Dashboard Statistics
```typescript
/**
 * Test dashboard statistics display and calculations.
 * 
 * Verifies that statistics are correctly calculated and displayed,
 * including cache usage, file counts, and performance metrics.
 */
test.describe('Dashboard Statistics', () => {
  
  test('Statistics display correct cache usage information', async ({ page }) => {
    await page.goto('/');
    
    // Wait for statistics to load
    await expect(page.locator('[data-testid="cache-usage-stat"]')).toBeVisible();
    
    // Verify statistics have numerical values
    const cacheUsage = await page.locator('[data-testid="cache-usage-value"]').textContent();
    expect(cacheUsage).toMatch(/^\d+(\.\d+)?\s*(MB|GB|TB)$/);
    
    // Test continues with more specific validations...
  });
});
```

### Context7 Reference
**REQUIRED**: Use Context7 Playwright documentation for advanced testing patterns, WebSocket testing, and responsive design testing.

### Code Quality Requirements
- **Test Documentation**: Every test function needs comprehensive JSDoc comments
- **Selector Strategy**: Use data-testid attributes for reliable element selection
- **Wait Strategies**: Document why specific waits are used and their timeout expectations
- **WebSocket Testing**: Clear explanation of real-time testing approach
- **Assertion Messages**: Descriptive expect messages for debugging failures

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6B2 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6B2 status to "completed"

### Success Criteria
- [ ] All dashboard tabs tested end-to-end
- [ ] WebSocket real-time updates verified
- [ ] Statistics calculations validated
- [ ] Tab navigation thoroughly tested
- [ ] Tests run reliably in <5 minutes
- [ ] Zero flaky test failures

### Files Created
- `e2e/dashboard.spec.ts` (comprehensive dashboard tests)

---

## ⚙️ TASK 6B3: CREATE SETTINGS PAGE PLAYWRIGHT TESTS (TESTING)

### Agent Type: `react-ui-builder`
### Complexity: 🔴 **COMPLEX** (requires form testing expertise)
### Dependencies: TASK 6B2 must be complete (dashboard tests passing)
### Can Run Parallel With: NONE - sequential only

### Context
Create comprehensive end-to-end tests for the Settings page functionality. Test all settings sections, form validation, save/load operations, and advanced features like export/import.

### Pre-Execution Checklist
- [ ] Verify TASK 6B2 completed (dashboard tests passing)
- [ ] Settings page is fully functional
- [ ] Backend settings API is working

### Step-by-Step Instructions

#### Step 1: Create Settings Test Base
**File**: `/mnt/user/Cursor/Cacherr/e2e/settings.spec.ts`
```typescript
/**
 * End-to-end tests for Settings page functionality.
 * 
 * This comprehensive test suite covers all settings features including:
 * - Form validation and input handling
 * - Settings sections (Plex, Media, Performance, Advanced)
 * - Save/load configuration operations
 * - Export/import functionality
 * - Connection testing and validation
 * - Error handling and recovery
 * - Mobile responsive behavior
 */
import { test, expect, Page } from '@playwright/test';

/**
 * Test group for Settings page core functionality.
 * 
 * These tests verify basic settings page operation including
 * loading, navigation, and form display.
 */
test.describe('Settings Page Core', () => {
  
  /**
   * Test Settings page loads with all sections visible.
   * 
   * Verifies that the settings page loads correctly and displays
   * all configuration sections with proper form controls.
   */
  test('Settings page loads with all configuration sections', async ({ page }) => {
    await page.goto('/settings');
    
    // Wait for settings page to load
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
    
    // Verify page title
    await expect(page.locator('h1')).toContainText('Settings');
    
    // Verify all settings sections are present
    await expect(page.locator('[data-testid="plex-settings-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="media-settings-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="performance-settings-section"]')).toBeVisible();
    await expect(page.locator('[data-testid="advanced-settings-section"]')).toBeVisible();
    
    // Verify action buttons are present
    await expect(page.locator('[data-testid="save-settings-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="export-settings-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="reset-settings-button"]')).toBeVisible();
  });
});
```

#### Step 2: Test Plex Settings Section
```typescript
/**
 * Test Plex configuration settings functionality.
 * 
 * Covers Plex server configuration including URL validation,
 * token handling, connection testing, and SSL settings.
 */
test.describe('Plex Settings', () => {
  
  /**
   * Test Plex connection testing functionality.
   * 
   * Verifies that the "Test Connection" button works correctly
   * and provides appropriate feedback for success/failure scenarios.
   */
  test('Plex connection testing provides proper feedback', async ({ page }) => {
    await page.goto('/settings');
    
    // Fill in Plex settings
    await page.fill('[data-testid="plex-url-input"]', 'http://localhost:32400');
    await page.fill('[data-testid="plex-token-input"]', 'test-token-123');
    
    // Mock successful connection test
    await page.route('**/api/config/test-plex', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ status: 'success' })
      });
    });
    
    // Click test connection button
    await page.click('[data-testid="test-plex-connection-button"]');
    
    // Verify loading state
    await expect(page.locator('[data-testid="test-plex-connection-button"]')).toContainText('Testing...');
    
    // Verify success feedback
    await expect(page.locator('[data-testid="plex-connection-result"]')).toContainText('Connection successful');
    await expect(page.locator('[data-testid="plex-connection-result"]')).toHaveClass(/text-green/);
  });
  
  /**
   * Test Plex URL validation.
   * 
   * Verifies that URL input validation works correctly and
   * provides helpful error messages for invalid URLs.
   */
  test('Plex URL validation shows appropriate errors', async ({ page }) => {
    await page.goto('/settings');
    
    // Test invalid URL formats
    const invalidUrls = [
      'not-a-url',
      'ftp://invalid-protocol.com',
      'http://',
      ''
    ];
    
    for (const invalidUrl of invalidUrls) {
      await page.fill('[data-testid="plex-url-input"]', invalidUrl);
      await page.blur('[data-testid="plex-url-input"]');
      
      // Verify validation error appears
      await expect(page.locator('[data-testid="plex-url-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="plex-url-error"]')).toContainText('valid URL');
    }
  });
});
```

#### Step 3: Test Settings Save/Load Operations
```typescript
/**
 * Test settings persistence functionality.
 * 
 * Verifies that settings can be saved, loaded, and persist
 * across page reloads correctly.
 */
test.describe('Settings Persistence', () => {
  
  /**
   * Test complete settings save and reload workflow.
   * 
   * Verifies that settings changes are saved to backend
   * and properly restored when page is reloaded.
   */
  test('Settings save and persist across page reload', async ({ page }) => {
    await page.goto('/settings');
    
    // Modify settings in each section
    await page.fill('[data-testid="plex-url-input"]', 'http://test-plex:32400');
    await page.fill('[data-testid="cache-path-input"]', '/test/cache/path');
    await page.fill('[data-testid="max-concurrent-input"]', '5');
    
    // Save settings
    await page.click('[data-testid="save-settings-button"]');
    
    // Wait for save confirmation
    await expect(page.locator('[data-testid="save-success-message"]')).toBeVisible();
    
    // Reload page
    await page.reload();
    
    // Verify settings were persisted
    await expect(page.locator('[data-testid="plex-url-input"]')).toHaveValue('http://test-plex:32400');
    await expect(page.locator('[data-testid="cache-path-input"]')).toHaveValue('/test/cache/path');
    await expect(page.locator('[data-testid="max-concurrent-input"]')).toHaveValue('5');
  });
});
```

#### Step 4: Test Export/Import Functionality
```typescript
/**
 * Test settings export and import functionality.
 * 
 * Verifies that settings can be exported to JSON and
 * imported back correctly, including error handling.
 */
test.describe('Settings Export/Import', () => {
  
  test('Export downloads configuration file correctly', async ({ page }) => {
    await page.goto('/settings');
    
    // Set up download handler
    const downloadPromise = page.waitForEvent('download');
    
    // Click export button
    await page.click('[data-testid="export-settings-button"]');
    
    // Wait for download
    const download = await downloadPromise;
    
    // Verify download filename
    expect(download.suggestedFilename()).toMatch(/cacherr-config-\d{4}-\d{2}-\d{2}\.json/);
    
    // Verify file content (if needed)
    // Implementation continues...
  });
});
```

### Context7 Reference
**REQUIRED**: Use Context7 Playwright documentation for form testing, file downloads, and complex user interactions.

### Code Quality Requirements
- **Form Testing Documentation**: Clear explanation of form validation testing approach
- **Input Validation**: Document all validation scenarios and expected behaviors
- **Save/Load Comments**: Explain the persistence testing strategy
- **Export/Import Logic**: Document file handling and validation testing
- **Error Scenario Coverage**: Comprehensive error condition testing

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6B3 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6B3 status to "completed"

### Success Criteria
- [ ] All settings sections tested comprehensively
- [ ] Form validation thoroughly verified
- [ ] Save/load operations tested end-to-end
- [ ] Export/import functionality validated
- [ ] Connection testing verified
- [ ] Tests run reliably in <7 minutes
- [ ] Zero false positives or flaky failures

### Files Created
- `e2e/settings.spec.ts` (comprehensive settings tests)

---

## 📱 TASK 6B4: CREATE RESPONSIVE DESIGN & ERROR HANDLING TESTS (TESTING)

### Agent Type: `react-ui-builder`
### Complexity: 🔴 **COMPLEX** (requires responsive and error testing expertise)
### Dependencies: TASK 6B3 must be complete (settings tests passing)
### Can Run Parallel With: NONE - sequential only

### Context
Create comprehensive tests for responsive design behavior across different screen sizes and comprehensive error handling scenarios. Ensure the application works correctly on mobile, tablet, and desktop devices.

### Pre-Execution Checklist
- [ ] Verify TASK 6B3 completed (settings tests passing)
- [ ] Application is responsive across different screen sizes
- [ ] Error scenarios are testable

### Step-by-Step Instructions

#### Step 1: Create Responsive Design Tests
**File**: `/mnt/user/Cursor/Cacherr/e2e/responsive.spec.ts`
```typescript
/**
 * End-to-end tests for responsive design behavior.
 * 
 * This test suite verifies that the application works correctly
 * across different screen sizes and device types including:
 * - Mobile devices (320px - 768px)
 * - Tablet devices (768px - 1024px)  
 * - Desktop devices (1024px+)
 * - Navigation behavior on small screens
 * - Touch vs mouse interactions
 * - Layout adaptations and content reflow
 */
import { test, expect, devices } from '@playwright/test';

/**
 * Test responsive behavior on mobile devices.
 * 
 * These tests verify that the application interface adapts
 * correctly to mobile screen sizes and touch interactions.
 */
test.describe('Mobile Responsive Design', () => {
  
  // Use iPhone 12 viewport for mobile tests
  test.use({ ...devices['iPhone 12'] });
  
  /**
   * Test mobile navigation functionality.
   * 
   * Verifies that navigation works correctly on mobile devices,
   * including hamburger menu behavior and touch interactions.
   */
  test('Mobile navigation works correctly', async ({ page }) => {
    await page.goto('/');
    
    // Verify mobile navigation is present
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    
    // Test hamburger menu opening
    await page.tap('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-navigation-menu"]')).toBeVisible();
    
    // Test navigation links work
    await page.tap('[data-testid="mobile-settings-link"]');
    await expect(page).toHaveURL(/.*\/settings/);
    
    // Verify settings page is mobile-friendly
    await expect(page.locator('[data-testid="settings-page"]')).toBeVisible();
    
    // Test form inputs are touch-friendly on mobile
    const urlInput = page.locator('[data-testid="plex-url-input"]');
    await expect(urlInput).toHaveCSS('min-height', /44px|48px/); // iOS touch target size
  });
  
  /**
   * Test dashboard layout on mobile.
   * 
   * Verifies that dashboard content adapts correctly to mobile
   * layout with proper spacing and readability.
   */
  test('Dashboard layout adapts to mobile screen', async ({ page }) => {
    await page.goto('/');
    
    // Verify dashboard container uses full width on mobile
    const dashboard = page.locator('[data-testid="dashboard-container"]');
    await expect(dashboard).toHaveCSS('width', /100%|calc\(/);
    
    // Test tab navigation on mobile
    await expect(page.locator('[data-testid="tab-navigation"]')).toBeVisible();
    
    // Verify tabs are scrollable if needed
    const tabContainer = page.locator('[data-testid="tab-container"]');
    const isScrollable = await tabContainer.evaluate(el => 
      el.scrollWidth > el.clientWidth
    );
    
    if (isScrollable) {
      // Test horizontal scrolling works
      await tabContainer.evaluate(el => el.scrollLeft = 100);
      const scrollPos = await tabContainer.evaluate(el => el.scrollLeft);
      expect(scrollPos).toBeGreaterThan(0);
    }
  });
});
```

#### Step 2: Test Tablet and Desktop Layouts
```typescript
/**
 * Test responsive behavior on tablet devices.
 * 
 * Verifies intermediate screen size behavior and layout adaptations
 * for tablet-sized screens.
 */
test.describe('Tablet Responsive Design', () => {
  
  // Use iPad viewport for tablet tests
  test.use({ ...devices['iPad'] });
  
  test('Tablet layout shows appropriate sidebar navigation', async ({ page }) => {
    await page.goto('/');
    
    // Verify tablet navigation layout
    await expect(page.locator('[data-testid="tablet-navigation"]')).toBeVisible();
    
    // Test that both mobile and desktop elements are hidden
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeHidden();
    await expect(page.locator('[data-testid="desktop-sidebar"]')).toBeHidden();
    
    // Test settings page tablet layout
    await page.goto('/settings');
    
    // Verify settings sections layout for tablet
    const settingsSections = page.locator('[data-testid="settings-section"]');
    const sectionsCount = await settingsSections.count();
    
    // On tablet, sections might be in 2-column layout
    // Implementation continues with tablet-specific validations...
  });
});
```

#### Step 3: Create Error Handling Tests  
**File**: `/mnt/user/Cursor/Cacherr/e2e/error-handling.spec.ts`
```typescript
/**
 * End-to-end tests for error handling and recovery scenarios.
 * 
 * This test suite covers error conditions including:
 * - Network failures and API errors
 * - Invalid user inputs and validation errors
 * - WebSocket connection failures
 * - Backend service unavailability
 * - Recovery from error states
 * - User-friendly error messaging
 */
import { test, expect, Page } from '@playwright/test';

/**
 * Test network error handling.
 * 
 * Verifies that the application gracefully handles network
 * failures and provides appropriate user feedback.
 */
test.describe('Network Error Handling', () => {
  
  /**
   * Test API error response handling.
   * 
   * Verifies that API errors are properly caught and displayed
   * to users with helpful error messages.
   */
  test('API errors show user-friendly error messages', async ({ page }) => {
    await page.goto('/settings');
    
    // Mock API error response
    await page.route('**/api/config/update', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({
          status: 'error',
          message: 'Internal server error occurred'
        })
      });
    });
    
    // Try to save settings to trigger error
    await page.click('[data-testid="save-settings-button"]');
    
    // Verify error message appears
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('server error');
    
    // Verify error message is user-friendly (not technical)
    const errorText = await page.locator('[data-testid="error-message"]').textContent();
    expect(errorText).not.toContain('500');
    expect(errorText).not.toContain('stack trace');
  });
  
  /**
   * Test WebSocket connection failure handling.
   * 
   * Verifies that WebSocket failures are handled gracefully
   * and users are informed about connection issues.
   */
  test('WebSocket connection failures show appropriate warnings', async ({ page }) => {
    // Block WebSocket connections
    await page.route('**/ws/**', route => route.abort());
    
    await page.goto('/');
    
    // Wait for connection attempt and failure
    await page.waitForTimeout(2000);
    
    // Verify connection status indicator
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Disconnected');
    await expect(page.locator('[data-testid="connection-status"]')).toHaveClass(/text-red/);
    
    // Verify retry mechanism works
    await page.click('[data-testid="reconnect-button"]');
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connecting...');
  });
});
```

#### Step 4: Test Form Validation Error Handling
```typescript
/**
 * Test comprehensive form validation error scenarios.
 * 
 * Verifies that all form validation works correctly and
 * provides clear guidance to users for fixing errors.
 */
test.describe('Form Validation Error Handling', () => {
  
  test('Settings form shows comprehensive validation errors', async ({ page }) => {
    await page.goto('/settings');
    
    // Clear all required fields to trigger validation
    await page.fill('[data-testid="plex-url-input"]', '');
    await page.fill('[data-testid="plex-token-input"]', '');
    await page.fill('[data-testid="cache-path-input"]', '');
    
    // Try to save with invalid data
    await page.click('[data-testid="save-settings-button"]');
    
    // Verify validation errors are displayed
    await expect(page.locator('[data-testid="plex-url-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="plex-token-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="cache-path-error"]')).toBeVisible();
    
    // Verify error messages are helpful
    const urlError = await page.locator('[data-testid="plex-url-error"]').textContent();
    expect(urlError).toMatch(/URL.*required|valid URL/i);
    
    // Test error clearing when fields are fixed
    await page.fill('[data-testid="plex-url-input"]', 'http://valid-url.com:32400');
    await expect(page.locator('[data-testid="plex-url-error"]')).toBeHidden();
  });
});
```

### Context7 Reference
**REQUIRED**: Use Context7 Playwright documentation for responsive testing, device emulation, and error scenario testing.

### Code Quality Requirements
- **Responsive Testing Documentation**: Explain testing strategy for different screen sizes
- **Device Emulation Comments**: Document why specific devices are chosen for testing
- **Error Scenario Coverage**: Comprehensive documentation of error conditions tested
- **Recovery Testing**: Explain how error recovery mechanisms are verified
- **User Experience Focus**: Document how error messages are validated for user-friendliness

### Update Master Plan
When you start: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6B4 status to "in_progress"
When you finish: Update CACHERR_REFACTORING_MASTER_PLAN.md TASK 6B4 status to "completed"

### Success Criteria
- [ ] Responsive design tested across all target screen sizes
- [ ] Mobile navigation and touch interactions verified
- [ ] Tablet layout adaptations tested
- [ ] Comprehensive error handling scenarios covered
- [ ] Network failure recovery tested
- [ ] Form validation errors thoroughly tested
- [ ] User-friendly error messages validated
- [ ] Tests run reliably across all device emulations

### Files Created
- `e2e/responsive.spec.ts` (responsive design tests)
- `e2e/error-handling.spec.ts` (error scenario tests)

---

This execution guide ensures each agent has complete, self-contained instructions for their specific task while maintaining project consistency and quality throughout the refactoring process. The comprehensive testing and cleanup phases ensure a production-ready system with no legacy code artifacts.

**CRITICAL REMINDERS FOR ALL AGENTS:**
1. **Always reference CACHERR_REFACTORING_MASTER_PLAN.md** for complete task list and dependencies
2. **Always reference Context7** for best practices in your technology domain  
3. **Add extensive comments** - someone unfamiliar with the project should understand your code
4. **Use Pydantic v2.5** patterns for all Python code
5. **Update the master plan** when you start and complete tasks
6. **Test your changes** thoroughly before marking complete
7. **ENSURE SETTINGS PERSISTENCE** - Test that settings survive page navigation and Docker restarts
8. **Keep Unraid template simple** - Most settings should be configured via web UI, not environment variables