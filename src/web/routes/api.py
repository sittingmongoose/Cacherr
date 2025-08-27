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
from ...core.plex_watcher import PlexWatcher
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
    Update configuration settings using modern Pydantic v2 validation.
    
    Accepts JSON payload with settings to update. Uses Pydantic validation
    to ensure all updates are type-safe and within valid ranges.
    
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
        
        # Filter out restricted settings (environment-only configurations)
        filtered_data = {}
        for key, value in data.items():
            if key == 'paths':
                # Only allow user-configurable path settings
                filtered_paths = {}
                if 'plex_source' in value:
                    filtered_paths['plex_source'] = value['plex_source']
                if 'cache_destination' in value:
                    filtered_paths['cache_destination'] = value['cache_destination']
                # additional_sources are environment-only for security
                if filtered_paths:
                    filtered_data['paths'] = filtered_paths
            elif key not in ['logging']:  # logging is system-managed
                filtered_data[key] = value
        
        # Remove empty values to preserve existing settings
        def clean_empty_values(obj):
            if isinstance(obj, dict):
                return {k: clean_empty_values(v) for k, v in obj.items() 
                       if v != '' and v is not None}
            return obj
        
        filtered_data = clean_empty_values(filtered_data)
        
        if not filtered_data:
            response = APIResponse(
                success=True,
                message="No valid settings to update"
            )
            return jsonify(response.dict())
        
        # Use new Pydantic-based save_updates method
        config.save_updates(filtered_data)
        
        # Log successful update
        logger.info(f"Configuration updated successfully: {list(filtered_data.keys())}")
        
        # Reinitialize engine if Plex settings were updated
        if 'plex' in filtered_data and (filtered_data['plex'].get('url') or filtered_data['plex'].get('token')):
            try:
                # This would require access to the global engine instance
                # For now, we'll log that reinitialization is needed
                logger.info("Plex settings updated - engine reinitialization may be required")
            except Exception as e:
                logger.warning(f"Failed to reinitialize engine with new Plex credentials: {e}")
        
        # Reload watchers if real-time watching or Trakt settings were updated
        if 'real_time_watch' in filtered_data or 'trakt' in filtered_data:
            try:
                engine = get_engine()
                if engine:
                    engine.reload_watchers()
                    logger.info("Watchers reloaded due to configuration changes")
            except Exception as e:
                logger.warning(f"Failed to reload watchers: {e}")
        
        response = APIResponse(
            success=True,
            message="Settings updated successfully",
            data={
                "updated_sections": list(filtered_data.keys()),
                "validation_summary": config.get_summary()
            }
        )
        return jsonify(response.dict())
        
    except ValueError as e:
        # Pydantic validation error
        logger.error(f"Settings validation failed: {e}")
        response = APIResponse(
            success=False,
            error=f"Invalid settings: {str(e)}"
        )
        return jsonify(response.dict()), 400
        
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
    Validate configuration settings using Pydantic v2 validation.
    
    Performs comprehensive validation including:
    - Type checking and constraint validation
    - Cross-field validation (e.g., path matching)
    - Business logic validation
    - Range and format validation
    
    Returns:
        JSON response with detailed validation results
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
            # Validate current configuration
            validation_results = config.validate_all()
        else:
            # Validate provided settings without saving
            try:
                config._validate_updates(data)
                validation_results = {
                    'valid': True,
                    'errors': [],
                    'warnings': [],
                    'sections': {},
                    'message': 'All provided settings are valid'
                }
            except ValueError as e:
                validation_results = {
                    'valid': False,
                    'errors': [str(e)],
                    'warnings': [],
                    'sections': {},
                    'message': f'Validation failed: {str(e)}'
                }
        
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
    Reset configuration to default values using Pydantic v2 defaults.
    
    Resets all configurable settings to their Pydantic model defaults.
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
        # Reset to Pydantic model defaults
        default_settings = {
            'media': {
                'copy_to_cache': True,  # New default
                'delete_from_cache_when_done': True,
                'watched_move': True,
                'users_toggle': True,
                'watchlist_toggle': True,
                'exit_if_active_session': False,
                'days_to_monitor': 99,
                'number_episodes': 5,
                'watchlist_episodes': 1,
                'watchlist_cache_expiry': 6,
                'watched_cache_expiry': 48
            },
            'performance': {
                'max_concurrent_moves_cache': 3,  # Updated defaults
                'max_concurrent_moves_array': 1,
                'max_concurrent_local_transfers': 3,
                'max_concurrent_network_transfers': 1
            },
            'test_mode': {
                'enabled': False,
                'show_file_sizes': True,
                'show_total_size': True
            },
            'real_time_watch': {
                'enabled': False,
                'check_interval': 30,
                'auto_cache_on_watch': True,
                'cache_on_complete': True,
                'respect_existing_rules': True,
                'max_concurrent_watches': 5,
                'remove_from_cache_after_hours': 24,
                'respect_other_users_watchlists': True,
                'exclude_inactive_users_days': 30
            },
            'trakt': {
                'enabled': False,
                'trending_movies_count': 10,
                'check_interval': 3600
            }
        }
        
        # Apply default settings using the new configuration system
        config.save_updates(default_settings)
        
        # Reload configuration to ensure all changes are applied
        config.reload()
        
        response = APIResponse(
            success=True,
            message="Configuration reset to default values",
            data={
                "reset_sections": list(default_settings.keys()),
                "validation_summary": config.get_summary()
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


# Plex Validation
@api_bp.route('/validate-plex', methods=['POST'])
@handle_api_error
def api_validate_plex():
    """
    Validate Plex server connection and token.
    
    Tests connectivity to the specified Plex server using provided
    credentials. Verifies both server availability and token validity.
    
    Returns:
        JSON response with validation results
    """
    try:
        data = request.get_json()
        if not data:
            response = APIResponse(
                success=False,
                error="No validation data provided"
            )
            return jsonify(response.dict()), 400
        
        plex_url = data.get('url', '').strip()
        plex_token = data.get('token', '').strip()
        use_stored_token = data.get('use_stored_token', False)
        
        if not plex_url:
            response = APIResponse(
                success=False,
                error="Plex URL is required"
            )
            return jsonify(response.dict()), 400
        
        # Handle token - either provided or use stored one
        if use_stored_token:
            # Get stored token from configuration
            config = get_config()
            if not config:
                response = APIResponse(
                    success=False,
                    error="Configuration not available"
                )
                return jsonify(response.dict()), 500
            
            plex_token = config.plex.token
            if not plex_token:
                response = APIResponse(
                    success=False,
                    error="No stored Plex token found"
                )
                return jsonify(response.dict()), 400
        elif not plex_token:
            response = APIResponse(
                success=False,
                error="Plex token is required"
            )
            return jsonify(response.dict()), 400
        
        # Import PlexAPI for validation
        from plexapi.server import PlexServer
        import requests
        
        # Clean up URL format
        if not plex_url.startswith(('http://', 'https://')):
            plex_url = f'http://{plex_url}'
        
        # Test connection with timeout
        try:
            plex = PlexServer(plex_url, plex_token, timeout=10)
            # Try to get server info to verify connection
            server_name = plex.friendlyName
            version = plex.version
            
            response = APIResponse(
                success=True,
                message=f"Connected to {server_name} (v{version})"
            )
            return jsonify(response.dict()), 200
            
        except Exception as plex_error:
            error_msg = str(plex_error)
            if "401" in error_msg or "Unauthorized" in error_msg:
                error_msg = "Invalid token - check your Plex token"
            elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                error_msg = "Connection timeout - check URL and network"
            elif "resolve" in error_msg.lower() or "name" in error_msg.lower():
                error_msg = "Cannot resolve hostname - check Plex URL"
            else:
                error_msg = f"Connection failed: {error_msg}"
                
            response = APIResponse(
                success=False,
                error=error_msg
            )
            return jsonify(response.dict()), 400
            
    except ImportError:
        response = APIResponse(
            success=False,
            error="PlexAPI library not available"
        )
        return jsonify(response.dict()), 500
        
    except Exception as e:
        logger.error(f"Plex validation error: {str(e)}")
        response = APIResponse(
            success=False,
            error=f"Validation failed: {str(e)}"
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


# Real-time Watcher Endpoints
@api_bp.route('/watcher/start', methods=['POST'])
@handle_api_error
def api_watcher_start():
    """Start real-time Plex watching."""
    try:
        engine = get_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Engine not initialized"
            )
            return jsonify(response.dict()), 500
        
        if not engine.config.real_time_watch.enabled:
            response = APIResponse(
                success=False,
                error="Real-time watching is disabled in configuration. Please enable it in settings first."
            )
            return jsonify(response.dict()), 400
        
        success = engine.start_real_time_watching()
        if success:
            response = APIResponse(
                success=True,
                message="Real-time Plex watching started successfully"
            )
            return jsonify(response.dict())
        else:
            response = APIResponse(
                success=False,
                error="Failed to start real-time watching"
            )
            return jsonify(response.dict()), 500
    
    except Exception as e:
        logger.error(f"Error starting real-time watcher: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to start real-time watching: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/watcher/stop', methods=['POST'])
@handle_api_error
def api_watcher_stop():
    """Stop real-time Plex watching."""
    try:
        engine = get_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Engine not initialized"
            )
            return jsonify(response.dict()), 500
        
        success = engine.stop_real_time_watching()
        if success:
            response = APIResponse(
                success=True,
                message="Real-time Plex watching stopped successfully"
            )
            return jsonify(response.dict())
        else:
            response = APIResponse(
                success=False,
                error="Failed to stop real-time watching"
            )
            return jsonify(response.dict()), 500
    
    except Exception as e:
        logger.error(f"Error stopping real-time watcher: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to stop real-time watching: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/watcher/status')
@handle_api_error
def api_watcher_status():
    """
    Get real-time watcher status with atomic operation details.
    
    Returns comprehensive status including:
    - Current watching state
    - Atomic cache operation statistics  
    - Configuration details
    - Safety information about non-interrupting operations
    """
    try:
        engine = get_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Engine not initialized"
            )
            return jsonify(response.dict()), 500
        
        # Get type-safe status from Pydantic model
        if engine.plex_watcher:
            watcher_status = engine.plex_watcher.get_status()
            watch_history = engine.plex_watcher.get_watch_history()
        else:
            # Fallback when watcher not initialized
            from ..core.plex_watcher import RealTimeWatchingStatus
            watcher_status = RealTimeWatchingStatus()
            watch_history = {}
        
        response = APIResponse(
            success=True,
            data={
                "status": watcher_status.model_dump(),
                "enabled": engine.config.real_time_watch.enabled,
                "watch_history": watch_history,
                "atomic_operations": {
                    "description": "Real-time caching uses atomic operations that never interrupt Plex playback",
                    "process": [
                        "1. Copy file to cache (never move during playback)",
                        "2. Create temporary symlink in same directory", 
                        "3. Atomically replace original with symlink to cache",
                        "4. Plex seamlessly switches to reading from fast cache"
                    ],
                    "safety_guarantees": [
                        "No playback interruption",
                        "Atomic file operations (POSIX compliant)",
                        "Preserves file permissions and metadata",
                        "Transparent to Plex server"
                    ]
                },
                "config": {
                    "check_interval": engine.config.real_time_watch.check_interval,
                    "auto_cache_on_watch": engine.config.real_time_watch.auto_cache_on_watch,
                    "cache_on_complete": engine.config.real_time_watch.cache_on_complete,
                    "remove_from_cache_after_hours": engine.config.real_time_watch.remove_from_cache_after_hours,
                    "respect_other_users_watchlists": engine.config.real_time_watch.respect_other_users_watchlists,
                    "exclude_inactive_users_days": engine.config.real_time_watch.exclude_inactive_users_days
                }
            }
        )
        return jsonify(response.dict())
    
    except Exception as e:
        logger.error(f"Error getting watcher status: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get watcher status: {str(e)}"
        )
        return jsonify(response.dict()), 500


@api_bp.route('/watcher/clear-history', methods=['POST'])
@handle_api_error
def api_watcher_clear_history():
    """Clear real-time watcher history."""
    try:
        engine = get_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Engine not initialized"
            )
            return jsonify(response.dict()), 500
        
        if not engine.plex_watcher:
            response = APIResponse(
                success=False,
                error="Real-time watcher is not initialized"
            )
            return jsonify(response.dict()), 400
        
        engine.clear_watch_history()
        response = APIResponse(
            success=True,
            message="Watch history cleared successfully"
        )
        return jsonify(response.dict())
    
    except Exception as e:
        logger.error(f"Error clearing watch history: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to clear watch history: {str(e)}"
        )
        return jsonify(response.dict()), 500


# Results Management Endpoints
@api_bp.route('/results/operations', methods=['GET'])
@handle_api_error
def api_get_operations():
    """
    Get operation history with filtering and pagination.
    
    Query parameters:
    - limit: Number of operations to return (default: 50)
    - offset: Number of operations to skip (default: 0)
    - user_id: Filter by user ID
    - operation_type: Filter by operation type
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - active_only: Only return active operations (default: false)
    """
    try:
        # Get query parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        user_id = request.args.get('user_id')
        operation_type = request.args.get('operation_type')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        start_date = None
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date'))
        
        end_date = None
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date'))
        
        # Get results service (would come from DI container in real implementation)
        results_service = getattr(g, 'results_service', None)
        if not results_service:
            response = APIResponse(
                success=False,
                error="Results service not available"
            )
            return jsonify(response.dict()), 500
        
        if active_only:
            operations = results_service.get_active_operations(user_id)
            total_count = len(operations)
        else:
            operations, total_count = results_service.get_operation_history(
                limit=limit, offset=offset, user_id=user_id,
                operation_type=operation_type, start_date=start_date, end_date=end_date
            )
        
        # Convert to dict format
        operations_data = []
        for op in operations:
            op_dict = op.dict()
            # Convert datetime objects to ISO strings
            if op_dict.get('started_at'):
                op_dict['started_at'] = op.started_at.isoformat()
            if op_dict.get('completed_at'):
                op_dict['completed_at'] = op.completed_at.isoformat()
            operations_data.append(op_dict)
        
        response = APIResponse(
            success=True,
            data={
                'operations': operations_data,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'total_count': total_count,
                    'has_more': offset + len(operations) < total_count
                }
            }
        )
        return jsonify(response.dict())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid query parameter: {e}"
        )
        return jsonify(response.dict()), 400


@api_bp.route('/results/operations/<operation_id>', methods=['GET'])
@handle_api_error
def api_get_operation_details(operation_id: str):
    """Get detailed information about a specific operation."""
    try:
        results_service = getattr(g, 'results_service', None)
        if not results_service:
            response = APIResponse(
                success=False,
                error="Results service not available"
            )
            return jsonify(response.dict()), 500
        
        batch_op, file_ops = results_service.get_operation_details(operation_id)
        
        # Convert to dict format
        batch_dict = batch_op.dict()
        if batch_dict.get('started_at'):
            batch_dict['started_at'] = batch_op.started_at.isoformat()
        if batch_dict.get('completed_at'):
            batch_dict['completed_at'] = batch_op.completed_at.isoformat()
        
        file_ops_data = []
        for file_op in file_ops:
            file_dict = file_op.dict()
            if file_dict.get('started_at'):
                file_dict['started_at'] = file_op.started_at.isoformat()
            if file_dict.get('completed_at'):
                file_dict['completed_at'] = file_op.completed_at.isoformat()
            file_ops_data.append(file_dict)
        
        response = APIResponse(
            success=True,
            data={
                'batch_operation': batch_dict,
                'file_operations': file_ops_data
            }
        )
        return jsonify(response.dict())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=str(e)
        )
        return jsonify(response.dict()), 404


@api_bp.route('/results/users/<user_id>/stats', methods=['GET'])
@handle_api_error
def api_get_user_stats(user_id: str):
    """Get statistics for a specific user."""
    try:
        days = int(request.args.get('days', 30))
        
        results_service = getattr(g, 'results_service', None)
        if not results_service:
            response = APIResponse(
                success=False,
                error="Results service not available"
            )
            return jsonify(response.dict()), 500
        
        stats = results_service.get_user_statistics(user_id, days)
        
        response = APIResponse(
            success=True,
            data=stats
        )
        return jsonify(response.dict())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid days parameter: {e}"
        )
        return jsonify(response.dict()), 400


@api_bp.route('/results/cleanup', methods=['POST'])
@handle_api_error
def api_cleanup_results():
    """Clean up old operation results."""
    try:
        data = request.get_json() or {}
        days_to_keep = int(data.get('days_to_keep', 90))
        
        results_service = getattr(g, 'results_service', None)
        if not results_service:
            response = APIResponse(
                success=False,
                error="Results service not available"
            )
            return jsonify(response.dict()), 500
        
        cleaned_count = results_service.cleanup_old_results(days_to_keep)
        
        response = APIResponse(
            success=True,
            message=f"Cleaned up {cleaned_count} old operations",
            data={
                'operations_cleaned': cleaned_count,
                'days_kept': days_to_keep
            }
        )
        return jsonify(response.dict())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid days_to_keep parameter: {e}"
        )
        return jsonify(response.dict()), 400


@api_bp.route('/results/export/<operation_id>', methods=['GET'])
@handle_api_error
def api_export_operation(operation_id: str):
    """Export operation results as downloadable file."""
    try:
        results_service = getattr(g, 'results_service', None)
        if not results_service:
            response = APIResponse(
                success=False,
                error="Results service not available"
            )
            return jsonify(response.dict()), 500
        
        batch_op, file_ops = results_service.get_operation_details(operation_id)
        
        # Generate export data
        export_data = f"PlexCacheUltra Operation Export\n"
        export_data += f"Generated: {datetime.now().isoformat()}\n\n"
        export_data += f"Operation ID: {batch_op.id}\n"
        export_data += f"Type: {batch_op.operation_type}\n"
        export_data += f"Status: {batch_op.status}\n"
        export_data += f"Test Mode: {'Yes' if batch_op.test_mode else 'No'}\n"
        export_data += f"Triggered By: {batch_op.triggered_by}\n"
        if batch_op.triggered_by_user:
            export_data += f"User: {batch_op.triggered_by_user}\n"
        export_data += f"Reason: {batch_op.reason}\n"
        export_data += f"Started: {batch_op.started_at}\n"
        if batch_op.completed_at:
            export_data += f"Completed: {batch_op.completed_at}\n"
        export_data += f"Files: {batch_op.files_processed}/{batch_op.total_files}\n"
        export_data += f"Success/Failed: {batch_op.files_successful}/{batch_op.files_failed}\n"
        export_data += f"Size: {batch_op.bytes_processed}/{batch_op.total_size_bytes} bytes\n\n"
        
        export_data += "File Operations:\n"
        for file_op in file_ops:
            export_data += f"- {file_op.filename} ({file_op.status})\n"
            export_data += f"  Path: {file_op.file_path}\n"
            export_data += f"  Operation: {file_op.operation_type}\n"
            export_data += f"  Reason: {file_op.reason}\n"
            export_data += f"  Size: {file_op.file_size_bytes} bytes\n"
            if file_op.error_message:
                export_data += f"  Error: {file_op.error_message}\n"
            export_data += "\n"
        
        # Return as downloadable text file
        from flask import make_response
        response = make_response(export_data)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename="operation_{operation_id}.txt"'
        return response
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=str(e)
        )
        return jsonify(response.dict()), 404


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