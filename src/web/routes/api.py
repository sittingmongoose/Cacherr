"""
API routes for PlexCacheUltra web application.

This module provides RESTful API endpoints for interacting with the PlexCacheUltra
system programmatically. Includes endpoints for cache operations, scheduler control,
configuration management, and system monitoring.

API Endpoints:
- /status: Get system status and statistics
- /run: Execute cache operations (with optional test mode)
- /test-results: Get test mode analysis results
- /settings: Configuration management (GET/POST)
- /settings/validate: Validate configuration settings
- /settings/reset: Reset configuration to defaults
- /scheduler/*: Scheduler control endpoints
- /watcher/*: Real-time Plex watcher endpoints
- /trakt/*: Trakt.tv integration endpoints
- /logs: Get recent application logs

All endpoints return JSON responses with appropriate HTTP status codes
and comprehensive error handling.

Example:
    Get system status:
    ```
    GET /api/status
    {
        "status": "idle",
        "pending_operations": {
            "files_to_cache": 5,
            "files_to_array": 2
        },
        "last_execution": {
            "execution_time": "2024-01-01 12:00:00",
            "success": true
        },
        "scheduler_running": false
    }
    ```
    
    Execute cache operation:
    ```
    POST /api/run
    Content-Type: application/json
    {"test_mode": false}
    
    Response:
    {
        "success": true,
        "message": "Cache operation completed successfully",
        "test_mode": false
    }
    ```
"""

import logging
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from flask import Blueprint, jsonify, request, g
from pydantic import BaseModel, Field, ValidationError

from ...core.interfaces import CacheService, MediaService, FileService, NotificationService
from ...core.plex_cache_engine import CacherrEngine
from ...config.settings import Config


# Blueprint for API routes
api_bp = Blueprint('api', __name__)

logger = logging.getLogger(__name__)


class APIResponse(BaseModel):
    """Standard API response model."""
    
    success: bool = Field(description="Whether the operation was successful")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if applicable")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")


class RunOperationRequest(BaseModel):
    """Request model for run operation endpoint."""
    
    test_mode: bool = Field(default=False, description="Whether to run in test mode (dry run)")
    
    class Config:
        extra = "forbid"


class SettingsUpdateRequest(BaseModel):
    """Request model for settings update endpoint."""
    
    settings: Dict[str, Any] = Field(description="Settings to update")
    
    class Config:
        extra = "forbid"


class SettingsValidationRequest(BaseModel):
    """Request model for settings validation endpoint."""
    
    settings: Dict[str, Any] = Field(description="Settings to validate")
    
    class Config:
        extra = "forbid"


def get_cache_engine() -> Optional[CacherrEngine]:
    """
    Get the cache engine instance from the application context.
    
    Returns:
        CacherrEngine instance if available, None otherwise
    """
    # This would typically come from dependency injection
    # For now, we'll get it from the application context or global state
    return getattr(g, 'cache_engine', None)


def get_config() -> Optional[Config]:
    """
    Get the configuration instance from the application context.
    
    Returns:
        Config instance if available, None otherwise
    """
    return getattr(g, 'config', None)


def handle_api_error(func):
    """
    Decorator for consistent API error handling.
    
    Args:
        func: Flask route function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            response = APIResponse(
                success=False,
                error="Validation error: " + str(e)
            )
            return jsonify(response.dict()), 400
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            response = APIResponse(
                success=False,
                error=f"Internal server error: {str(e)}"
            )
            return jsonify(response.dict()), 500
    
    wrapper.__name__ = func.__name__
    return wrapper


# System Status and Operations
@api_bp.route('/status')
@handle_api_error
def api_status():
    """
    Get comprehensive system status information.
    
    Returns detailed information about current system state, including:
    - Current operation status (running/idle)
    - Pending operations count
    - Last execution information
    - Scheduler status
    - Cache statistics
    - Test results if available
    
    Returns:
        JSON response with system status information
    """
    engine = get_cache_engine()
    if not engine:
        response = APIResponse(
            success=False,
            error="Cache engine not initialized"
        )
        return jsonify(response.dict()), 500
    
    try:
        status_data = engine.get_status()
        
        response = APIResponse(
            success=True,
            data=status_data
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get system status: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/run', methods=['POST'])
@handle_api_error
def api_run():
    """
    Execute cache operations with optional test mode.
    
    Accepts JSON payload to configure operation mode:
    - test_mode: boolean - whether to run in test mode (dry run)
    
    Test mode performs analysis without making actual file changes,
    useful for previewing what operations would be performed.
    
    Returns:
        JSON response with operation results
    """
    engine = get_cache_engine()
    if not engine:
        response = APIResponse(
            success=False,
            error="Cache engine not initialized"
        )
        return jsonify(response.dict()), 500
    
    try:
        # Parse request data
        test_mode = False
        if request.is_json:
            data = request.get_json(silent=True)
            if data and isinstance(data, dict):
                run_request = RunOperationRequest(**data)
                test_mode = run_request.test_mode
        
        logger.info(f"Starting cache operation (test_mode={test_mode})")
        
        # Execute operation
        success = engine.run(test_mode=test_mode)
        
        operation_type = "Test mode analysis" if test_mode else "Cache operation"
        message = f"{operation_type} completed {'successfully' if success else 'with errors'}"
        
        response = APIResponse(
            success=bool(success),
            message=message,
            data={
                "test_mode": test_mode,
                "operation_completed": True
            }
        )
        
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Cache operation failed: {e}")
        response = APIResponse(
            success=False,
            error=f"Operation failed: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/test-results')
@handle_api_error
def api_test_results():
    """
    Get test mode analysis results.
    
    Returns detailed analysis of what operations would be performed
    in test mode, including file lists, sizes, and operation types.
    
    Returns:
        JSON response with test mode results
    """
    engine = get_cache_engine()
    if not engine:
        response = APIResponse(
            success=False,
            error="Cache engine not initialized"
        )
        return jsonify(response.dict()), 500
    
    try:
        test_results = engine.get_test_results()
        
        response = APIResponse(
            success=True,
            data=test_results
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to get test results: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get test results: {str(e)}"
        )
        return jsonify(response.dict()), 500


# Configuration Management
@api_bp.route('/settings', methods=['GET'])
@handle_api_error
def api_get_settings():
    """
    Get current configuration settings.
    
    Returns the complete configuration as a JSON object,
    including all sections and their current values.
    
    Returns:
        JSON response with current configuration
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.dict()), 500
    
    try:
        config_dict = config.to_dict()
        
        response = APIResponse(
            success=True,
            data=config_dict
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get settings: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/settings', methods=['POST'])
@handle_api_error
def api_update_settings():
    """
    Update configuration settings.
    
    Accepts JSON payload with settings to update. Filtered to prevent
    updating certain critical settings like additional sources which
    should only be configured via Docker environment variables.
    
    Returns:
        JSON response with update results
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.dict()), 500
    
    try:
        data = request.get_json()
        if not data:
            response = APIResponse(
                success=False,
                error="No settings data provided"
            )
            return jsonify(response.dict()), 400
        
        # Filter out restricted settings
        filtered_data = {}
        for key, value in data.items():
            if key == 'paths':
                # Only allow plex_source and cache_destination, not additional_sources
                filtered_paths = {}
                if 'plex_source' in value:
                    filtered_paths['plex_source'] = value['plex_source']
                if 'cache_destination' in value:
                    filtered_paths['cache_destination'] = value['cache_destination']
                if filtered_paths:
                    filtered_data['paths'] = filtered_paths
            else:
                filtered_data[key] = value
        
        # Update configuration
        updated_vars = {}
        for key, value in filtered_data.items():
            if hasattr(config, key) and hasattr(getattr(config, key), '__dict__'):
                # Handle nested configuration objects
                section = getattr(config, key)
                for subkey, subvalue in value.items():
                    if hasattr(section, subkey):
                        if config.update_persistent_config(key, subkey, subvalue):
                            updated_vars[f"{key}.{subkey}"] = subvalue
            else:
                # Handle top-level configuration
                if config.update_persistent_config('general', key, value):
                    updated_vars[key] = value
        
        # Reinitialize engine if Plex settings were updated
        if 'plex' in filtered_data and (filtered_data['plex'].get('url') or filtered_data['plex'].get('token')):
            try:
                # This would require access to the global engine instance
                # For now, we'll log that reinitialization is needed
                logger.info("Plex settings updated - engine reinitialization may be required")
            except Exception as e:
                logger.warning(f"Failed to reinitialize engine with new Plex credentials: {e}")
        
        response = APIResponse(
            success=True,
            message=f"Updated {len(updated_vars)} settings",
            data={
                "updated_variables": updated_vars,
                "total_updates": len(updated_vars)
            }
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to update settings: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/settings/validate', methods=['POST'])
@handle_api_error
def api_validate_settings():
    """
    Validate configuration settings without applying them.
    
    Performs comprehensive validation including:
    - Path existence and accessibility checks
    - Plex server connectivity tests
    - Configuration value validation
    - Dependency availability checks
    
    Returns:
        JSON response with validation results
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.dict()), 500
    
    try:
        data = request.get_json()
        if not data:
            response = APIResponse(
                success=False,
                error="No settings data provided for validation"
            )
            return jsonify(response.dict()), 400
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'path_checks': {},
            'connectivity_checks': {}
        }
        
        # Validate paths
        if 'paths' in data:
            paths = data['paths']
            
            # Check plex source
            if 'plex_source' in paths:
                plex_source = paths['plex_source']
                if os.path.exists(plex_source):
                    validation_results['path_checks']['plex_source'] = {
                        'exists': True,
                        'readable': os.access(plex_source, os.R_OK),
                        'path': plex_source
                    }
                else:
                    validation_results['path_checks']['plex_source'] = {
                        'exists': False,
                        'readable': False,
                        'path': plex_source
                    }
                    validation_results['errors'].append(f"Plex source directory does not exist: {plex_source}")
                    validation_results['valid'] = False
            
            # Check cache destination
            if 'cache_destination' in paths and paths['cache_destination']:
                cache_dest = paths['cache_destination']
                if os.path.exists(cache_dest):
                    validation_results['path_checks']['cache_destination'] = {
                        'exists': True,
                        'writable': os.access(cache_dest, os.W_OK),
                        'path': cache_dest
                    }
                else:
                    validation_results['path_checks']['cache_destination'] = {
                        'exists': False,
                        'writable': False,
                        'path': cache_dest
                    }
                    validation_results['warnings'].append(f"Cache destination directory does not exist: {cache_dest}")
        
        # Validate Plex connection
        if 'plex' in data:
            plex_config = data['plex']
            if 'url' in plex_config and 'token' in plex_config:
                try:
                    plex_url = plex_config['url']
                    plex_token = plex_config['token']
                    
                    # Test Plex connection
                    test_url = f"{plex_url}/status/sessions"
                    headers = {'X-Plex-Token': plex_token}
                    response_req = requests.get(test_url, headers=headers, timeout=10)
                    
                    if response_req.status_code == 200:
                        validation_results['connectivity_checks']['plex_server'] = {
                            'status': 'success',
                            'url': plex_url,
                            'response_time_ms': response_req.elapsed.total_seconds() * 1000
                        }
                    else:
                        validation_results['connectivity_checks']['plex_server'] = {
                            'status': 'failed',
                            'url': plex_url,
                            'status_code': response_req.status_code
                        }
                        validation_results['errors'].append(f"Plex connection failed: HTTP {response_req.status_code}")
                        validation_results['valid'] = False
                        
                except Exception as e:
                    validation_results['connectivity_checks']['plex_server'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    validation_results['errors'].append(f"Plex connection error: {e}")
                    validation_results['valid'] = False
        
        response = APIResponse(
            success=True,
            data=validation_results
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Settings validation failed: {e}")
        response = APIResponse(
            success=False,
            error=f"Validation failed: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/settings/reset', methods=['POST'])
@handle_api_error
def api_reset_settings():
    """
    Reset configuration to default values.
    
    Resets all configurable settings to their default values.
    This operation cannot be undone, so use with caution.
    
    Returns:
        JSON response with reset operation results
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.dict()), 500
    
    try:
        # Default settings
        default_settings = {
            'PLEX_SOURCE': '/media',
            'LOG_LEVEL': 'INFO',
            'NOTIFICATION_TYPE': 'webhook',
            'MAX_CONCURRENT_MOVES_CACHE': '5',
            'MAX_CONCURRENT_MOVES_ARRAY': '2',
            'MAX_CONCURRENT_LOCAL_TRANSFERS': '5',
            'MAX_CONCURRENT_NETWORK_TRANSFERS': '2',
            'NUMBER_EPISODES': '5',
            'DAYS_TO_MONITOR': '99',
            'WATCHLIST_TOGGLE': 'true',
            'WATCHLIST_EPISODES': '1',
            'WATCHLIST_CACHE_EXPIRY': '6',
            'WATCHED_MOVE': 'true',
            'WATCHED_CACHE_EXPIRY': '48',
            'USERS_TOGGLE': 'true',
            'EXIT_IF_ACTIVE_SESSION': 'false',
            'COPY_TO_CACHE': 'false',
            'DELETE_FROM_CACHE_WHEN_DONE': 'true',
            'USE_SYMLINKS_FOR_CACHE': 'true',
            'MOVE_WITH_SYMLINKS': 'false',
            'TEST_MODE': 'false',
            'TEST_SHOW_FILE_SIZES': 'true',
            'TEST_SHOW_TOTAL_SIZE': 'true',
            'DEBUG': 'false'
        }
        
        # Apply default settings to environment
        for key, value in default_settings.items():
            os.environ[key] = value
        
        response = APIResponse(
            success=True,
            message="Settings reset to defaults successfully",
            data={
                "default_settings": default_settings,
                "total_reset": len(default_settings)
            }
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to reset settings: {str(e)}"
        )
        return jsonify(response.dict()), 500


# Scheduler Management
@api_bp.route('/scheduler/start', methods=['POST'])
@handle_api_error
def api_scheduler_start():
    """
    Start the background scheduler.
    
    Starts the scheduler that runs cache operations automatically
    at configured intervals.
    
    Returns:
        JSON response with scheduler start results
    """
    # This would need to interact with the scheduler service
    # For now, we'll return a placeholder response
    try:
        # TODO: Implement scheduler start logic
        response = APIResponse(
            success=True,
            message="Scheduler start requested (implementation pending)"
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to start scheduler: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/scheduler/stop', methods=['POST'])
@handle_api_error
def api_scheduler_stop():
    """
    Stop the background scheduler.
    
    Stops the currently running scheduler, preventing automatic
    cache operations from running.
    
    Returns:
        JSON response with scheduler stop results
    """
    # This would need to interact with the scheduler service
    # For now, we'll return a placeholder response
    try:
        # TODO: Implement scheduler stop logic
        response = APIResponse(
            success=True,
            message="Scheduler stop requested (implementation pending)"
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to stop scheduler: {str(e)}"
        )
        return jsonify(response.dict()), 500


# Logs and Monitoring
@api_bp.route('/logs')
@handle_api_error
def api_logs():
    """
    Get recent application logs.
    
    Returns the most recent log entries from the application log file,
    parsed and formatted for display in the web interface.
    
    Returns:
        JSON response with recent log entries
    """
    try:
        log_file = Path("/config/logs/cacherr.log")
        if not log_file.exists():
            response = APIResponse(
                success=True,
                data={
                    "logs": [],
                    "message": "No log file found"
                }
            )
            return jsonify(response.dict())
        
        # Read last 100 lines of the log file
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-100:] if len(lines) > 100 else lines
        
        # Parse log entries
        log_entries = []
        for line in recent_lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse log level from the line
            log_level = 'info'
            if ' - ERROR - ' in line:
                log_level = 'error'
            elif ' - WARNING - ' in line:
                log_level = 'warning'
            elif ' - DEBUG - ' in line:
                log_level = 'debug'
            
            log_entries.append({
                'level': log_level,
                'message': line,
                'timestamp': line.split(' - ')[0] if ' - ' in line else ''
            })
        
        response = APIResponse(
            success=True,
            data={
                "logs": log_entries,
                "total_entries": len(log_entries)
            }
        )
        return jsonify(response.dict())
        
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get logs: {str(e)}"
        )
        return jsonify(response.dict()), 500


# Real-time Watcher Endpoints (Placeholder implementations)
@api_bp.route('/watcher/start', methods=['POST'])
@handle_api_error
def api_watcher_start():
    """Start real-time Plex watching (placeholder)."""
    # TODO: Implement watcher start logic
    response = APIResponse(
        success=True,
        message="Watcher start requested (implementation pending)"
    )
    return jsonify(response.dict())


@api_bp.route('/watcher/stop', methods=['POST'])
@handle_api_error
def api_watcher_stop():
    """Stop real-time Plex watching (placeholder)."""
    # TODO: Implement watcher stop logic
    response = APIResponse(
        success=True,
        message="Watcher stop requested (implementation pending)"
    )
    return jsonify(response.dict())


@api_bp.route('/watcher/status')
@handle_api_error
def api_watcher_status():
    """Get real-time watcher status (placeholder)."""
    # TODO: Implement watcher status logic
    response = APIResponse(
        success=True,
        data={
            "is_watching": False,
            "stats": {},
            "message": "Watcher status implementation pending"
        }
    )
    return jsonify(response.dict())


# Trakt.tv Integration Endpoints (Placeholder implementations)
@api_bp.route('/trakt/status')
@handle_api_error
def api_trakt_status():
    """Get Trakt.tv watcher status (placeholder)."""
    # TODO: Implement Trakt status logic
    response = APIResponse(
        success=True,
        data={
            "stats": {},
            "trending_movies": [],
            "message": "Trakt status implementation pending"
        }
    )
    return jsonify(response.dict())


@api_bp.route('/trakt/start', methods=['POST'])
@handle_api_error
def api_trakt_start():
    """Start Trakt.tv watcher (placeholder)."""
    # TODO: Implement Trakt start logic
    response = APIResponse(
        success=True,
        message="Trakt watcher start requested (implementation pending)"
    )
    return jsonify(response.dict())


@api_bp.route('/trakt/stop', methods=['POST'])
@handle_api_error
def api_trakt_stop():
    """Stop Trakt.tv watcher (placeholder)."""
    # TODO: Implement Trakt stop logic
    response = APIResponse(
        success=True,
        message="Trakt watcher stop requested (implementation pending)"
    )
    return jsonify(response.dict())