"""
API routes for Cacherr web application.

This module provides RESTful API endpoints for interacting with the Cacherr
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
import time
import os
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

from flask import Blueprint, jsonify, request, g, Response
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
            return jsonify(response.model_dump()), 400
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            response = APIResponse(
                success=False,
                error=f"Internal server error: {str(e)}"
            )
            return jsonify(response.model_dump()), 500
    
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
        return jsonify(response.model_dump()), 500
    
    try:
        status_data = engine.get_status()
        
        response = APIResponse(
            success=True,
            data=status_data
        )
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get system status: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


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
        return jsonify(response.model_dump()), 500
    
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
        
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Cache operation failed: {e}")
        response = APIResponse(
            success=False,
            error=f"Operation failed: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


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
        return jsonify(response.model_dump()), 500
    
    try:
        test_results = engine.get_test_results()
        
        response = APIResponse(
            success=True,
            data=test_results
        )
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Failed to get test results: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get test results: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


# Configuration Management
@api_bp.route('/config/current', methods=['GET'])
@handle_api_error
def api_get_config_current():
    """
    Get current application configuration.

    Returns the current configuration settings in a structured format
    that can be consumed by the Settings page frontend.

    Returns:
        JSON response with current configuration
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.model_dump()), 500

    try:
        # Return configuration in the format expected by Settings page
        # Ensure all values are JSON-serializable (cast Pydantic Url/Enum types to str)
        config_data = {
            'plex': {
                'url': str(config.plex.url) if getattr(config.plex, 'url', None) else '',
                'token': '***MASKED***' if config.plex.token else '',
                'username': config.plex.username or '',
                'password': '***MASKED***' if config.plex.password else ''
            },
            'media': {
                'exit_if_active_session': config.media.exit_if_active_session,
                'watched_move': config.media.watched_move,
                'users_toggle': config.media.users_toggle,
                'watchlist_toggle': config.media.watchlist_toggle,
                'days_to_monitor': config.media.days_to_monitor,
                'number_episodes': config.media.number_episodes,
                'watchlist_episodes': config.media.watchlist_episodes,
                'copy_to_cache': config.media.copy_to_cache,
                'delete_from_cache_when_done': config.media.delete_from_cache_when_done
            },
            'performance': {
                'max_concurrent_operations': getattr(config.performance, 'max_concurrent_moves_cache', getattr(config.performance, 'max_concurrent_operations', 3)),
                'cache_check_interval': (config.real_time_watch.get('check_interval', 30)
                                         if isinstance(config.real_time_watch, dict)
                                         else 30),
                'max_concurrent_local_transfers': getattr(config.performance, 'max_concurrent_local_transfers', 1),
                'log_level': str(getattr(config.logging, 'level', 'INFO')) if not isinstance(getattr(config.logging, 'level', 'INFO'), str) else getattr(config.logging, 'level', 'INFO')
            }
        }

        response = APIResponse(
            success=True,
            data=config_data
        )
        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"Failed to get current configuration: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to retrieve configuration: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/config/update', methods=['POST'])
@handle_api_error
def api_update_config():
    """
    Update application configuration.

    Accepts partial configuration updates and validates them using
    Pydantic models before applying changes.

    Returns:
        JSON response with updated configuration
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.model_dump()), 500

    try:
        data = request.get_json()
        if not data:
            response = APIResponse(
                success=False,
                error="No configuration data provided"
            )
            return jsonify(response.model_dump()), 400

        # Accept both {settings: {...}} and direct section updates
        updates = data.get('settings', data) if isinstance(data, dict) else {}

        # Update configuration using the configuration system
        config.save_updates(updates)

        # Log successful update
        logger.info(f"Configuration updated successfully: {list(updates.keys())}")

        response = APIResponse(
            success=True,
            message="Configuration updated successfully",
            data={
                "updated_sections": list(updates.keys()),
                "validation_summary": config.get_summary()
            }
        )
        return jsonify(response.model_dump())

    except ValidationError as e:
        response = APIResponse(
            success=False,
            error="Configuration validation failed",
            data={"validation_errors": e.errors()}
        )
        return jsonify(response.model_dump()), 422

    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to update configuration: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/config/validate', methods=['POST'])
@handle_api_error
def api_validate_config():
    """
    Validate configuration settings.

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
        return jsonify(response.model_dump()), 500

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
        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        response = APIResponse(
            success=False,
            error=f"Validation failed: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/config/reset', methods=['POST'])
@handle_api_error
def api_reset_config():
    """
    Reset configuration to default values.

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
        return jsonify(response.model_dump()), 500

    try:
        # Reset to Pydantic model defaults
        default_settings = {
            'media': {
                'copy_to_cache': True,
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
                'max_concurrent_moves_cache': 3,
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
        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"Failed to reset configuration: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to reset configuration: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


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
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to start scheduler: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


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
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to stop scheduler: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


# Plex Validation
@api_bp.route('/config/test-plex', methods=['POST'])
@handle_api_error
def api_test_plex_connection():
    """
    Test Plex server connection with provided credentials.

    Returns:
        JSON response with connection test result
    """
    try:
        data = request.get_json()
        if not data:
            response = APIResponse(
                success=False,
                error="No test data provided"
            )
            return jsonify(response.model_dump()), 400

        plex_url = (data.get('url') or '').strip()
        plex_token = (data.get('token') or '').strip()

        # Resolve token: treat masked tokens as "use saved value"
        MASK = '***MASKED***'
        cfg = get_config()
        if (not plex_token) or (plex_token == MASK) or ('*' in plex_token.upper()) or (plex_token.lower() == 'masked'):
            if cfg and getattr(cfg.plex, 'token', None):
                # Handle SecretStr and plain str
                token_val = cfg.plex.token
                if hasattr(token_val, 'get_secret_value'):
                    token_val = token_val.get_secret_value()
                plex_token = token_val
            elif os.getenv('PLEX_TOKEN'):
                plex_token = os.getenv('PLEX_TOKEN')

        # Resolve URL: fall back to saved or environment value
        if not plex_url:
            if cfg and getattr(cfg.plex, 'url', None):
                plex_url = str(cfg.plex.url)
            elif os.getenv('PLEX_URL'):
                plex_url = os.getenv('PLEX_URL')

        if not plex_url or not plex_token:
            response = APIResponse(
                success=False,
                error="Both URL and token are required"
            )
            return jsonify(response.model_dump()), 400

        # Test Plex connection using existing service
        # This should use the actual Plex service from the container
        try:
            # Import PlexAPI for validation
            from plexapi.server import PlexServer

            # Clean up URL format
            if not plex_url.startswith(('http://', 'https://')):
                plex_url = f'http://{plex_url}'

            # Test connection with timeout and measure response time
            t0 = time.perf_counter()
            plex = PlexServer(plex_url, plex_token, timeout=10)
            # Touch a light attribute to ensure the session is valid
            server_name = plex.friendlyName
            version = plex.version
            response_time_ms = int((time.perf_counter() - t0) * 1000)

            # Attempt to gather optional details (platform, libraries)
            platform = None
            library_count = None
            library_names = []
            try:
                platform = getattr(plex, 'platform', None)
            except Exception:
                platform = None
            try:
                sections = plex.library.sections()
                library_count = len(sections)
                library_names = [getattr(s, 'title', None) for s in sections if hasattr(s, 'title')]
            except Exception:
                # Library probing is optional; do not fail the test if unavailable
                pass

            # Build connectivity payload compatible with frontend expectations
            connectivity = {
                'status': 'success',
                'success': True,  # legacy compatibility flag used by UI
                'url': plex_url,
                'server_info': {
                    'product': 'Plex Media Server',
                    'version': str(version),
                    'platform': platform,
                    'server_name': server_name,
                    'library_count': library_count,
                    'libraries': library_names
                },
                'response_time_ms': response_time_ms,
                # Convenience flags some UI variants look for
                'ok': True,
                'connected': True
            }

            response = APIResponse(
                success=True,
                message=f"Connected to {server_name} (v{version})",
                data=connectivity
            )
            # Also surface ok/connected at top-level for legacy clients
            payload = response.model_dump()
            payload['ok'] = True
            payload['connected'] = True
            return jsonify(payload)

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

            connectivity = {
                'status': 'failed',
                'success': False,
                'url': plex_url,
                'error': error_msg,
                'ok': False,
                'connected': False
            }
            response = APIResponse(
                success=False,
                error=error_msg,
                data=connectivity
            )
            payload = response.model_dump()
            payload['ok'] = False
            payload['connected'] = False
            return jsonify(payload), 400

    except ImportError:
        response = APIResponse(
            success=False,
            error="PlexAPI library not available"
        )
        return jsonify(response.model_dump()), 500

    except Exception as e:
        logger.error(f"Plex connection test failed: {str(e)}")
        response = APIResponse(
            success=False,
            error=f"Connection test failed: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/config/export', methods=['GET'])
@handle_api_error
def api_export_config():
    """
    Export current configuration as JSON.

    Returns the complete configuration in a downloadable JSON format
    that can be used for backup or migration purposes.

    Returns:
        JSON file download with current configuration
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.model_dump()), 500

    try:
        # Get current configuration
        config_dict = config.to_dict()

        # Mask sensitive data
        if 'plex' in config_dict and 'token' in config_dict['plex']:
            config_dict['plex']['token'] = '***MASKED***'

        # Convert to JSON string
        import json
        config_json = json.dumps(config_dict, indent=2)

        # Return as downloadable file
        from flask import Response
        response = Response(
            config_json,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename="cacherr_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            }
        )
        return response

    except Exception as e:
        logger.error(f"Failed to export configuration: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to export configuration: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/config/import', methods=['POST'])
@handle_api_error
def api_import_config():
    """
    Import configuration from JSON data.

    Accepts JSON configuration data and applies it to the system
    after validation. This will overwrite existing configuration.

    Request body (JSON):
        Configuration data in the same format as export

    Returns:
        JSON response with import results
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.model_dump()), 500

    try:
        data = request.get_json()
        if not data:
            response = APIResponse(
                success=False,
                error="No configuration data provided"
            )
            return jsonify(response.model_dump()), 400

        # Validate the imported configuration
        try:
            config._validate_updates(data)
        except ValueError as e:
            response = APIResponse(
                success=False,
                error=f"Invalid configuration data: {str(e)}"
            )
            return jsonify(response.model_dump()), 400

        # Apply the imported configuration
        config.save_updates(data)

        response = APIResponse(
            success=True,
            message="Configuration imported successfully",
            data={
                "imported_sections": list(data.keys()),
                "validation_summary": config.get_summary()
            }
        )
        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"Failed to import configuration: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to import configuration: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/config/schema', methods=['GET'])
@handle_api_error
def api_get_config_schema():
    """
    Get configuration schema information.

    Returns detailed schema information including field types,
    validation rules, default values, and descriptions for all
    configuration sections.

    Returns:
        JSON response with configuration schema
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.model_dump()), 500

    try:
        # Build schema from Pydantic models - using actual PlexConfig attributes
        schema = {
            'plex': {
                'url': {
                    'type': 'string',
                    'description': 'Plex server URL including protocol and port',
                    'example': 'http://192.168.1.100:32400',
                    'validation': 'Must be a valid HTTP/HTTPS URL'
                },
                'token': {
                    'type': 'string',
                    'description': 'Plex authentication token',
                    'sensitive': True,
                    'validation': 'Must be a valid Plex token'
                },
                'username': {
                    'type': 'string',
                    'description': 'Plex username (optional for token auth)',
                    'default': None,
                    'validation': 'Optional username for authentication'
                },
                'password': {
                    'type': 'string',
                    'description': 'Plex password (optional for token auth)',
                    'sensitive': True,
                    'default': None,
                    'validation': 'Optional password for authentication'
                }
            },
            'media': {
                'exit_if_active_session': {
                    'type': 'boolean',
                    'description': 'Exit if Plex sessions are active',
                    'default': False
                },
                'watched_move': {
                    'type': 'boolean',
                    'description': 'Move watched content to array',
                    'default': True
                },
                'users_toggle': {
                    'type': 'boolean',
                    'description': 'Enable per-user processing',
                    'default': True
                },
                'watchlist_toggle': {
                    'type': 'boolean',
                    'description': 'Enable watchlist processing',
                    'default': True
                },
                'days_to_monitor': {
                    'type': 'integer',
                    'description': 'Days to monitor content',
                    'default': 99,
                    'min': 1,
                    'max': 999
                },
                'number_episodes': {
                    'type': 'integer',
                    'description': 'Number of episodes to cache per series',
                    'default': 5,
                    'min': 1,
                    'max': 100
                },
                'watchlist_episodes': {
                    'type': 'integer',
                    'description': 'Episodes to cache from watchlists',
                    'default': 1,
                    'min': 1,
                    'max': 100
                },
                'copy_to_cache': {
                    'type': 'boolean',
                    'description': 'Use copy mode instead of move (preserves originals)',
                    'default': True
                },
                'delete_from_cache_when_done': {
                    'type': 'boolean',
                    'description': 'Delete from cache when done',
                    'default': True
                }
            },
            'performance': {
                'max_concurrent_operations': {
                    'type': 'integer',
                    'description': 'Maximum number of concurrent cache operations',
                    'default': 3,
                    'min': 1,
                    'max': 10
                },
                'cache_check_interval': {
                    'type': 'integer',
                    'description': 'Interval between cache checks in seconds',
                    'default': 30,
                    'min': 10,
                    'max': 3600
                },
                'cleanup_interval': {
                    'type': 'integer',
                    'description': 'Interval between cleanup operations in hours',
                    'default': 24,
                    'min': 1,
                    'max': 168
                },
                'log_level': {
                    'type': 'string',
                    'description': 'Logging level',
                    'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    'default': 'INFO'
                }
            }
        }

        response = APIResponse(
            success=True,
            data={
                'schema': schema,
                'version': '2.0',
                'last_updated': datetime.now().isoformat()
            }
        )
        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"Failed to get configuration schema: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get configuration schema: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/config/validate-persistence', methods=['GET'])
@handle_api_error
def api_validate_persistence():
    """
    Validate that settings persistence is working correctly.

    Checks that configuration files exist, are accessible, and can be
    read/written. This is critical for ensuring settings survive
    container restarts.

    Returns:
        JSON response with persistence validation results
    """
    config = get_config()
    if not config:
        response = APIResponse(
            success=False,
            error="Configuration not initialized"
        )
        return jsonify(response.model_dump()), 500

    try:
        # Check configuration directory
        from pathlib import Path
        config_dir = Path(config.settings.config_dir)
        config_dir_exists = config_dir.exists()
        config_dir_writable = False
        config_files = []

        if config_dir_exists:
            config_dir_writable = os.access(config_dir, os.W_OK)
            config_files = list(config_dir.glob('*.json'))

        # Check if current configuration can be saved
        persistence_test = False
        try:
            # Test persistence by saving a temporary backup
            test_backup = config_dir / f"persistence_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}

            with open(test_backup, 'w') as f:
                import json
                json.dump(test_data, f)

            # Verify we can read it back
            with open(test_backup, 'r') as f:
                read_data = json.load(f)

            persistence_test = read_data.get('test') == True

            # Clean up test file
            test_backup.unlink(missing_ok=True)

        except Exception as e:
            logger.warning(f"Persistence test failed: {e}")

        response = APIResponse(
            success=True,
            data={
                'persistence': {
                    'config_dir_exists': config_dir_exists,
                    'config_dir_writable': config_dir_writable,
                    'config_files': [str(f) for f in config_files],
                    'config_dir_path': str(config_dir),
                    'persistence_test_passed': persistence_test
                },
                'config_file_path': str(config.config_file),
                'config_file_exists': config.config_file.exists(),
                'config_file_writable': config.config_file.exists() and os.access(config.config_file, os.W_OK),
                'last_modified': config.config_file.stat().st_mtime if config.config_file.exists() else None
            }
        )
        return jsonify(response.model_dump())

    except Exception as e:
        logger.error(f"Failed to validate persistence: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to validate persistence: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


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
            return jsonify(response.model_dump())
        
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
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get logs: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


# Real-time Watcher Endpoints
@api_bp.route('/watcher/start', methods=['POST'])
@handle_api_error
def api_watcher_start():
    """Start real-time Plex watching."""
    try:
        engine = get_cache_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Cache engine not available"
            )
            return jsonify(response.model_dump()), 503
        
        if not engine.config.real_time_watch.enabled:
            response = APIResponse(
                success=False,
                error="Real-time watching is disabled in configuration. Please enable it in settings first."
            )
            return jsonify(response.model_dump()), 400
        
        success = engine.start_real_time_watching()
        if success:
            response = APIResponse(
                success=True,
                message="Real-time Plex watching started successfully"
            )
            return jsonify(response.model_dump())
        else:
            response = APIResponse(
                success=False,
                error="Failed to start real-time watching"
            )
            return jsonify(response.model_dump()), 500
    
    except Exception as e:
        logger.error(f"Error starting real-time watcher: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to start real-time watching: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/watcher/stop', methods=['POST'])
@handle_api_error
def api_watcher_stop():
    """Stop real-time Plex watching."""
    try:
        engine = get_cache_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Cache engine not available"
            )
            return jsonify(response.model_dump()), 503
        
        success = engine.stop_real_time_watching()
        if success:
            response = APIResponse(
                success=True,
                message="Real-time Plex watching stopped successfully"
            )
            return jsonify(response.model_dump())
        else:
            response = APIResponse(
                success=False,
                error="Failed to stop real-time watching"
            )
            return jsonify(response.model_dump()), 500
    
    except Exception as e:
        logger.error(f"Error stopping real-time watcher: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to stop real-time watching: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


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
        engine = get_cache_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Cache engine not available"
            )
            return jsonify(response.model_dump()), 503
        
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
        return jsonify(response.model_dump())
    
    except Exception as e:
        logger.error(f"Error getting watcher status: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get watcher status: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/watcher/clear-history', methods=['POST'])
@handle_api_error
def api_watcher_clear_history():
    """Clear real-time watcher history."""
    try:
        engine = get_cache_engine()
        if not engine:
            response = APIResponse(
                success=False,
                error="Cache engine not available"
            )
            return jsonify(response.model_dump()), 503
        
        if not engine.plex_watcher:
            response = APIResponse(
                success=False,
                error="Real-time watcher is not initialized"
            )
            return jsonify(response.model_dump()), 400
        
        engine.clear_watch_history()
        response = APIResponse(
            success=True,
            message="Watch history cleared successfully"
        )
        return jsonify(response.model_dump())
    
    except Exception as e:
        logger.error(f"Error clearing watch history: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to clear watch history: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


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
            return jsonify(response.model_dump()), 500
        
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
            op_dict = op.model_dump()
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
        return jsonify(response.model_dump())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid query parameter: {e}"
        )
        return jsonify(response.model_dump()), 400


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
            return jsonify(response.model_dump()), 500
        
        batch_op, file_ops = results_service.get_operation_details(operation_id)
        
        # Convert to dict format
        batch_dict = batch_op.model_dump()
        if batch_dict.get('started_at'):
            batch_dict['started_at'] = batch_op.started_at.isoformat()
        if batch_dict.get('completed_at'):
            batch_dict['completed_at'] = batch_op.completed_at.isoformat()
        
        file_ops_data = []
        for file_op in file_ops:
            file_dict = file_op.model_dump()
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
        return jsonify(response.model_dump())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=str(e)
        )
        return jsonify(response.model_dump()), 404


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
            return jsonify(response.model_dump()), 500
        
        stats = results_service.get_user_statistics(user_id, days)
        
        response = APIResponse(
            success=True,
            data=stats
        )
        return jsonify(response.model_dump())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid days parameter: {e}"
        )
        return jsonify(response.model_dump()), 400


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
            return jsonify(response.model_dump()), 500
        
        cleaned_count = results_service.cleanup_old_results(days_to_keep)
        
        response = APIResponse(
            success=True,
            message=f"Cleaned up {cleaned_count} old operations",
            data={
                'operations_cleaned': cleaned_count,
                'days_kept': days_to_keep
            }
        )
        return jsonify(response.model_dump())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid days_to_keep parameter: {e}"
        )
        return jsonify(response.model_dump()), 400


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
            return jsonify(response.model_dump()), 500
        
        batch_op, file_ops = results_service.get_operation_details(operation_id)
        
        # Generate export data
        export_data = f"Cacherr Operation Export\n"
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
        return jsonify(response.model_dump()), 404


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
    return jsonify(response.model_dump())


@api_bp.route('/trakt/start', methods=['POST'])
@handle_api_error
def api_trakt_start():
    """Start Trakt.tv watcher (placeholder)."""
    # TODO: Implement Trakt start logic
    response = APIResponse(
        success=True,
        message="Trakt watcher start requested (implementation pending)"
    )
    return jsonify(response.model_dump())


@api_bp.route('/trakt/stop', methods=['POST'])
@handle_api_error
def api_trakt_stop():
    """Stop Trakt.tv watcher (placeholder)."""
    # TODO: Implement Trakt stop logic
    response = APIResponse(
        success=True,
        message="Trakt watcher stop requested (implementation pending)"
    )
    return jsonify(response.model_dump())


# Cached Files Management Endpoints
@api_bp.route('/cached/files', methods=['GET'])
@handle_api_error
def api_get_cached_files():
    """
    Get cached files with filtering and pagination.
    
    Query parameters:
    - search: Search term for filename/path filtering
    - user_id: Filter by user ID who triggered caching
    - status: Filter by file status (active, orphaned, pending_removal, removed)
    - triggered_by_operation: Filter by operation type (watchlist, ondeck, trakt, manual, etc.)
    - size_min: Minimum file size in bytes
    - size_max: Maximum file size in bytes  
    - cached_since: ISO date string - only files cached since this date
    - limit: Maximum results to return (1-500, default 50)
    - offset: Offset for pagination (default 0)
    
    Returns:
        JSON response with cached files list and pagination info
    """
    try:
        # Parse query parameters with Pydantic validation
        from ...core.cached_files_service import CachedFilesFilter
        
        filter_params = {}
        
        # String parameters
        if request.args.get('search'):
            filter_params['search'] = request.args.get('search').strip()
        
        if request.args.get('user_id'):
            filter_params['user_id'] = request.args.get('user_id').strip()
            
        if request.args.get('status'):
            filter_params['status'] = request.args.get('status').strip()
            
        if request.args.get('triggered_by_operation'):
            filter_params['triggered_by_operation'] = request.args.get('triggered_by_operation').strip()
        
        # Integer parameters
        if request.args.get('size_min'):
            filter_params['size_min'] = int(request.args.get('size_min'))
            
        if request.args.get('size_max'):
            filter_params['size_max'] = int(request.args.get('size_max'))
            
        if request.args.get('limit'):
            filter_params['limit'] = min(int(request.args.get('limit')), 500)
            
        if request.args.get('offset'):
            filter_params['offset'] = max(int(request.args.get('offset')), 0)
        
        # Date parameter
        if request.args.get('cached_since'):
            filter_params['cached_since'] = datetime.fromisoformat(request.args.get('cached_since'))
        
        # Validate with Pydantic
        filter_obj = CachedFilesFilter(**filter_params)
        
        # Get cached files service from dependency injection
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        cached_files, total_count = cached_files_service.get_cached_files(filter_obj)
        
        # Convert to dict format for JSON response
        files_data = []
        for file_info in cached_files:
            file_dict = file_info.model_dump()
            # Convert datetime objects to ISO strings
            if file_dict.get('cached_at'):
                file_dict['cached_at'] = file_info.cached_at.isoformat()
            if file_dict.get('last_accessed'):
                file_dict['last_accessed'] = file_info.last_accessed.isoformat()
            files_data.append(file_dict)
        
        response = APIResponse(
            success=True,
            data={
                'files': files_data,
                'pagination': {
                    'limit': filter_obj.limit,
                    'offset': filter_obj.offset,
                    'total_count': total_count,
                    'has_more': filter_obj.offset + len(cached_files) < total_count
                },
                'filter_applied': filter_obj.model_dump(exclude_unset=True)
            }
        )
        return jsonify(response.model_dump())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid query parameter: {e}"
        )
        return jsonify(response.model_dump()), 400


@api_bp.route('/cached/files/<file_id>', methods=['GET'])
@handle_api_error
def api_get_cached_file(file_id: str):
    """
    Get details for a specific cached file.
    
    Args:
        file_id: The ID of the cached file to retrieve
        
    Returns:
        JSON response with cached file details
    """
    try:
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        # Get the file info by ID
        cached_file = cached_files_service.get_cached_file_by_id(file_id)
        
        if not cached_file:
            response = APIResponse(
                success=False,
                error=f"Cached file with ID {file_id} not found"
            )
            return jsonify(response.model_dump()), 404
        
        # Convert to dict format for JSON response
        file_dict = cached_file.model_dump()
        if file_dict.get('cached_at'):
            file_dict['cached_at'] = cached_file.cached_at.isoformat()
        if file_dict.get('last_accessed'):
            file_dict['last_accessed'] = cached_file.last_accessed.isoformat()
        
        response = APIResponse(
            success=True,
            data=file_dict
        )
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Error retrieving cached file {file_id}: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to retrieve cached file: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/cached/files/<file_id>', methods=['DELETE'])
@handle_api_error
def api_remove_cached_file(file_id: str):
    """
    Remove a specific file from cache tracking.
    
    Args:
        file_id: The ID of the cached file to remove
        
    Request body (JSON):
    - reason: Reason for removal (optional, default: "manual")
    - user_id: User ID triggering the removal (optional)
    
    Returns:
        JSON response confirming removal
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'manual')
        user_id = data.get('user_id')
        
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        # Get the file info by ID
        cached_file = cached_files_service.get_cached_file_by_id(file_id)
        
        if not cached_file:
            response = APIResponse(
                success=False,
                error=f"Cached file with ID {file_id} not found"
            )
            return jsonify(response.model_dump()), 404
        success = cached_files_service.remove_cached_file(
            cached_file.file_path, reason, user_id
        )
        
        if success:
            response = APIResponse(
                success=True,
                message=f"Cached file removed successfully: {cached_file.filename}",
                data={
                    'file_id': file_id,
                    'file_path': cached_file.file_path,
                    'reason': reason
                }
            )
            return jsonify(response.model_dump())
        else:
            response = APIResponse(
                success=False,
                error="Failed to remove cached file"
            )
            return jsonify(response.model_dump()), 500
            
    except Exception as e:
        logger.error(f"Error removing cached file {file_id}: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to remove cached file: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/cached/statistics', methods=['GET'])
@handle_api_error
def api_get_cache_statistics():
    """
    Get comprehensive cache statistics.
    
    Returns detailed statistics about cached files including:
    - Total files and size
    - Active vs orphaned files
    - User count and access patterns
    - Cache efficiency metrics
    
    Returns:
        JSON response with cache statistics
    """
    try:
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        statistics = cached_files_service.get_cache_statistics()
        stats_dict = statistics.model_dump()
        
        # Convert datetime objects to ISO strings
        if stats_dict.get('oldest_cached_at'):
            stats_dict['oldest_cached_at'] = statistics.oldest_cached_at.isoformat()
        
        response = APIResponse(
            success=True,
            data=stats_dict
        )
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get cache statistics: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/cached/users/<user_id>/stats', methods=['GET'])
@handle_api_error
def api_get_user_cache_stats(user_id: str):
    """
    Get cache statistics for a specific user.
    
    Query parameters:
    - days: Number of days to include in statistics (default: 30)
    
    Args:
        user_id: The user ID to get statistics for
    
    Returns:
        JSON response with user-specific cache statistics
    """
    try:
        days = int(request.args.get('days', 30))
        if days <= 0:
            raise ValueError("Days must be positive")
        
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        # Get user's cached files stats using the service method
        user_stats = cached_files_service.get_user_statistics(user_id, days)
        
        response = APIResponse(
            success=True,
            data=user_stats
        )
        return jsonify(response.model_dump())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid parameter: {e}"
        )
        return jsonify(response.model_dump()), 400
        
    except Exception as e:
        logger.error(f"Error getting user cache stats for {user_id}: {e}")
        response = APIResponse(
            success=False,
            error=f"Failed to get user statistics: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/cached/cleanup', methods=['POST'])
@handle_api_error
def api_cleanup_cached_files():
    """
    Clean up orphaned cached files.
    
    Scans cached files and marks those that no longer exist on disk as orphaned.
    Optionally removes orphaned entries completely.
    
    Request body (JSON):
    - remove_orphaned: Whether to completely remove orphaned entries (default: false)
    - user_id: User ID triggering the cleanup (optional)
    
    Returns:
        JSON response with cleanup results
    """
    try:
        data = request.get_json() or {}
        remove_orphaned = data.get('remove_orphaned', False)
        user_id = data.get('user_id')
        
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        orphaned_count = cached_files_service.cleanup_orphaned_files()
        
        # If requested, remove orphaned entries completely
        removed_count = 0
        if remove_orphaned and orphaned_count > 0:
            # This would require additional method in service
            pass  # TODO: Implement complete removal of orphaned entries
        
        response = APIResponse(
            success=True,
            message=f"Cache cleanup completed. {orphaned_count} files marked as orphaned.",
            data={
                'orphaned_count': orphaned_count,
                'removed_count': removed_count,
                'remove_orphaned': remove_orphaned
            }
        )
        return jsonify(response.model_dump())
        
    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")
        response = APIResponse(
            success=False,
            error=f"Cache cleanup failed: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/cached/files/search', methods=['GET'])
@handle_api_error
def api_search_cached_files():
    """
    Advanced search for cached files.
    
    Query parameters:
    - q: Search query (searches filename, path, and user fields)
    - type: Search type ('filename', 'path', 'user', 'operation', 'all')
    - limit: Maximum results (default: 50)
    - include_removed: Include removed files in results (default: false)
    
    Returns:
        JSON response with search results
    """
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')
        limit = min(int(request.args.get('limit', 50)), 500)
        include_removed = request.args.get('include_removed', 'false').lower() == 'true'
        
        if not query:
            response = APIResponse(
                success=False,
                error="Search query parameter 'q' is required"
            )
            return jsonify(response.model_dump()), 400
        
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        # Build search filter based on type
        from ...core.cached_files_service import CachedFilesFilter
        search_filter = CachedFilesFilter(limit=limit)
        
        if search_type in ('filename', 'path', 'all'):
            search_filter.search = query
            
        if search_type == 'user':
            search_filter.user_id = query
            
        if search_type == 'operation':
            search_filter.triggered_by_operation = query
            
        if not include_removed:
            # Exclude removed files
            if not search_filter.status:
                search_filter.status = 'active'
        
        cached_files, total_count = cached_files_service.get_cached_files(search_filter)
        
        # Convert to dict format
        files_data = []
        for file_info in cached_files:
            file_dict = file_info.model_dump()
            if file_dict.get('cached_at'):
                file_dict['cached_at'] = file_info.cached_at.isoformat()
            if file_dict.get('last_accessed'):
                file_dict['last_accessed'] = file_info.last_accessed.isoformat()
            files_data.append(file_dict)
        
        response = APIResponse(
            success=True,
            data={
                'query': query,
                'search_type': search_type,
                'results': files_data,
                'total_found': total_count,
                'limited_to': limit
            }
        )
        return jsonify(response.model_dump())
        
    except ValueError as e:
        response = APIResponse(
            success=False,
            error=f"Invalid parameter: {e}"
        )
        return jsonify(response.model_dump()), 400
        
    except Exception as e:
        logger.error(f"Error in cached files search: {e}")
        response = APIResponse(
            success=False,
            error=f"Search failed: {str(e)}"
        )
        return jsonify(response.model_dump()), 500


@api_bp.route('/cached/export', methods=['GET'])
@handle_api_error
def api_export_cached_files():
    """
    Export cached files data as downloadable file.
    
    Query parameters:
    - format: Export format ('csv', 'json', 'txt') - default: 'csv'
    - user_id: Filter by user ID (optional)
    - status: Filter by status (optional)
    - include_metadata: Include metadata in export (default: false)
    
    Returns:
        Downloadable file with cached files data
    """
    try:
        export_format = request.args.get('format', 'csv').lower()
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        include_metadata = request.args.get('include_metadata', 'false').lower() == 'true'
        
        if export_format not in ('csv', 'json', 'txt'):
            response = APIResponse(
                success=False,
                error="Format must be 'csv', 'json', or 'txt'"
            )
            return jsonify(response.model_dump()), 400
        
        from ...core.cached_files_service import CachedFilesService
        try:
            cached_files_service = g.container.resolve(CachedFilesService)
        except Exception as e:
            logger.error(f"Failed to resolve CachedFilesService: {e}")
            response = APIResponse(
                success=False,
                error="Cached files service not available"
            )
            return jsonify(response.model_dump()), 500
        
        # Get filtered cached files
        from ...core.cached_files_service import CachedFilesFilter
        filter_params = CachedFilesFilter(limit=10000)  # Large limit for export
        if user_id:
            filter_params.user_id = user_id
        if status:
            filter_params.status = status
            
        cached_files, _ = cached_files_service.get_cached_files(filter_params)
        
        if export_format == 'json':
            # JSON export
            files_data = []
            for file_info in cached_files:
                file_dict = file_info.model_dump()
                if file_dict.get('cached_at'):
                    file_dict['cached_at'] = file_info.cached_at.isoformat()
                if file_dict.get('last_accessed'):
                    file_dict['last_accessed'] = file_info.last_accessed.isoformat()
                if not include_metadata:
                    file_dict.pop('metadata', None)
                files_data.append(file_dict)
            
            export_data = {
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_files': len(files_data),
                'filters_applied': filter_params.model_dump(exclude_unset=True),
                'cached_files': files_data
            }
            
            response = jsonify(export_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename="cached_files_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            return response
            
        elif export_format == 'csv':
            # CSV export
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header row
            headers = ['filename', 'file_path', 'cached_path', 'cache_method', 'file_size_readable', 
                      'cached_at', 'triggered_by_user', 'triggered_by_operation', 'status', 'users']
            if include_metadata:
                headers.append('metadata')
            writer.writerow(headers)
            
            # Data rows
            for file_info in cached_files:
                row = [
                    file_info.filename,
                    file_info.file_path,
                    file_info.cached_path,
                    file_info.cache_method,
                    file_info.file_size_readable,
                    file_info.cached_at.isoformat(),
                    file_info.triggered_by_user or '',
                    file_info.triggered_by_operation,
                    file_info.status,
                    ','.join(file_info.users)
                ]
                if include_metadata:
                    row.append(str(file_info.metadata) if file_info.metadata else '')
                writer.writerow(row)
            
            output.seek(0)
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename="cached_files_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'}
            )
            return response
            
        else:  # txt format
            # Text export
            export_lines = []
            export_lines.append("Cacherr Cached Files Export")
            export_lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
            export_lines.append(f"Total Files: {len(cached_files)}")
            export_lines.append("")
            
            for file_info in cached_files:
                export_lines.append(f"File: {file_info.filename}")
                export_lines.append(f"  Path: {file_info.file_path}")
                export_lines.append(f"  Cached: {file_info.cached_at.isoformat()}")
                export_lines.append(f"  Size: {file_info.file_size_readable}")
                export_lines.append(f"  User: {file_info.triggered_by_user or 'N/A'}")
                export_lines.append(f"  Operation: {file_info.triggered_by_operation}")
                export_lines.append(f"  Status: {file_info.status}")
                if file_info.users:
                    export_lines.append(f"  All Users: {', '.join(file_info.users)}")
                export_lines.append("")
            
            response = Response(
                '\n'.join(export_lines),
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename="cached_files_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"'}
            )
            return response
            
    except Exception as e:
        logger.error(f"Error exporting cached files: {e}")
        response = APIResponse(
            success=False,
            error=f"Export failed: {str(e)}"
        )
        return jsonify(response.model_dump()), 500
