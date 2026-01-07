"""
Cacherr REST API Routes.

Provides HTTP endpoints for:
- Cache statistics and health
- Manual cache operations
- Configuration management
- Session monitoring
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict
from functools import wraps

from flask import Flask, Blueprint, jsonify, request, g


logger = logging.getLogger(__name__)


# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api')


def get_cache_manager():
    """Get cache manager from Flask app context."""
    from flask import current_app
    return getattr(current_app, 'cache_manager', None)


def api_response(success: bool, data: Any = None, message: str = "", error: str = "") -> Dict:
    """Standard API response format."""
    return {
        'success': success,
        'data': data,
        'message': message,
        'error': error,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# Health & Status Endpoints
# ============================================================

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    manager = get_cache_manager()
    healthy = manager is not None and manager._running if manager else False
    
    return jsonify({
        'status': 'healthy' if healthy else 'unhealthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }), 200 if healthy else 503


@api.route('/status', methods=['GET'])
def get_status():
    """Get overall cache manager status."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    return jsonify(api_response(True, data=manager.get_status()))


# ============================================================
# Cache Statistics Endpoints
# ============================================================

@api.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics and health."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    stats = manager.get_cache_stats()
    return jsonify(api_response(True, data=stats.to_dict()))


@api.route('/cache/files', methods=['GET'])
def get_cached_files():
    """Get list of all cached files."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    entries = manager.timestamp_tracker.get_all_entries()
    
    files = []
    for path, entry in entries.items():
        files.append({
            'path': path,
            'source': entry.get('source', 'unknown'),
            'cached_at': entry.get('cached_at'),
            'size_bytes': entry.get('file_size_bytes', 0),
        })
    
    # Sort by cached_at descending
    files.sort(key=lambda x: x.get('cached_at', ''), reverse=True)
    
    return jsonify(api_response(True, data={
        'count': len(files),
        'files': files,
    }))


# ============================================================
# Cache Operations Endpoints
# ============================================================

@api.route('/cache/cycle', methods=['POST'])
def run_cache_cycle():
    """Trigger a cache cycle (OnDeck, Watchlist, etc)."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    try:
        result = manager.run_cache_cycle()
        return jsonify(api_response(True, data=result, message="Cache cycle completed"))
    except Exception as e:
        logger.error(f"Cache cycle error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


@api.route('/cache/reconcile', methods=['POST'])
def run_reconciliation():
    """Trigger cache reconciliation."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    try:
        result = manager.reconcile()
        return jsonify(api_response(True, data=result.to_dict(), message="Reconciliation completed"))
    except Exception as e:
        logger.error(f"Reconciliation error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


@api.route('/cache/evict', methods=['POST'])
def trigger_eviction():
    """Manually trigger cache eviction."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    try:
        data = request.get_json() or {}
        dry_run = data.get('dry_run', False)
        
        if dry_run:
            # Just calculate what would be evicted
            stats = manager.get_cache_stats()
            if manager._limit_bytes <= 0:
                return jsonify(api_response(True, data={'message': 'No cache limit set'}))
            
            # Calculate candidates
            threshold_bytes = manager._limit_bytes * manager.config.cache_limits.eviction_threshold_percent / 100
            if stats.total_size_bytes < threshold_bytes:
                return jsonify(api_response(True, data={
                    'needed': False,
                    'message': 'Cache is under threshold'
                }))
            
            from .core.trackers import CachePriorityScorer
            entries = manager.timestamp_tracker.get_all_entries()
            target_bytes = manager._limit_bytes * manager.config.cache_limits.eviction_target_percent / 100
            bytes_to_free = stats.total_size_bytes - target_bytes
            
            candidates = CachePriorityScorer.get_eviction_candidates(
                entries,
                target_bytes=int(bytes_to_free),
                min_priority=manager.config.cache_limits.eviction_min_priority,
            )
            
            return jsonify(api_response(True, data={
                'dry_run': True,
                'needed': True,
                'bytes_to_free': bytes_to_free,
                'candidates': [
                    {'path': p, 'priority': pri, 'size': s}
                    for p, pri, s in candidates
                ],
            }))
        
        # Actually evict
        active_files = manager.get_active_file_paths()
        result = manager._enforce_cache_limits(active_files)
        return jsonify(api_response(True, data=result.to_dict(), message="Eviction completed"))
        
    except Exception as e:
        logger.error(f"Eviction error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


@api.route('/cache/file/<path:file_path>', methods=['DELETE'])
def uncache_file(file_path: str):
    """Remove a specific file from cache."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    # Prepend / if not present
    if not file_path.startswith('/'):
        file_path = '/' + file_path
    
    try:
        result = manager.file_ops.restore_to_array(file_path)
        
        if result.success:
            manager.timestamp_tracker.remove_entry(file_path)
            return jsonify(api_response(True, message=f"File restored to array"))
        else:
            return jsonify(api_response(False, error=result.error)), 400
            
    except Exception as e:
        logger.error(f"Uncache error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


# ============================================================
# Session Monitoring Endpoints
# ============================================================

@api.route('/sessions', methods=['GET'])
def get_sessions():
    """Get active Plex sessions."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    try:
        sessions = manager.plex.get_active_sessions()
        
        return jsonify(api_response(True, data={
            'count': len(sessions),
            'sessions': [
                {
                    'username': s.username,
                    'title': s.media_title,
                    'type': s.media_type,
                    'state': s.state,
                    'progress': round(s.progress_percent, 1),
                    'file_path': s.file_path,
                }
                for s in sessions
            ],
        }))
    except Exception as e:
        logger.error(f"Sessions error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


# ============================================================
# Configuration Endpoints
# ============================================================

@api.route('/config', methods=['GET'])
def get_config():
    """Get current configuration (sensitive values masked)."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    config = manager.config
    
    # Mask sensitive values
    masked = {
        'plex': {
            'url': config.plex.url,
            'token': '****' if config.plex.token else '',
            'number_episodes': config.plex.number_episodes,
            'days_to_monitor': config.plex.days_to_monitor,
        },
        'watchlist': {
            'enabled': config.watchlist.enabled,
            'episodes_per_show': config.watchlist.episodes_per_show,
        },
        'cache_limits': {
            'cache_limit': config.cache_limits.cache_limit,
            'eviction_mode': config.cache_limits.eviction_mode,
            'eviction_threshold_percent': config.cache_limits.eviction_threshold_percent,
            'eviction_target_percent': config.cache_limits.eviction_target_percent,
        },
        'retention': {
            'min_retention_hours': config.retention.min_retention_hours,
            'watched_expiry_hours': config.retention.watched_expiry_hours,
            'watchlist_retention_days': config.retention.watchlist_retention_days,
            'ondeck_protected': config.retention.ondeck_protected,
        },
        'realtime': {
            'enabled': config.realtime.enabled,
            'check_interval_seconds': config.realtime.check_interval_seconds,
        },
    }
    
    return jsonify(api_response(True, data=masked))


@api.route('/config', methods=['PATCH'])
def update_config():
    """Update configuration settings."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    try:
        updates = request.get_json()
        if not updates:
            return jsonify(api_response(False, error="No updates provided")), 400
        
        # TODO: Implement config updates
        # This would require config validation and potentially restart of services
        
        return jsonify(api_response(False, error="Config updates not yet implemented")), 501
        
    except Exception as e:
        logger.error(f"Config update error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


# ============================================================
# Utility Endpoints
# ============================================================

@api.route('/ondeck', methods=['GET'])
def get_ondeck():
    """Get current OnDeck items."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    try:
        items = manager.plex.get_ondeck(
            number_episodes=manager.config.plex.number_episodes,
            days_to_monitor=manager.config.plex.days_to_monitor,
        )
        
        return jsonify(api_response(True, data={
            'count': len(items),
            'items': [i.to_dict() for i in items],
        }))
    except Exception as e:
        logger.error(f"OnDeck error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


@api.route('/watchlist', methods=['GET'])
def get_watchlist():
    """Get current Watchlist items."""
    manager = get_cache_manager()
    if not manager:
        return jsonify(api_response(False, error="Cache manager not initialized")), 500
    
    try:
        items = manager.plex.get_watchlist(
            episodes_per_show=manager.config.watchlist.episodes_per_show,
        )
        
        return jsonify(api_response(True, data={
            'count': len(items),
            'items': [i.to_dict() for i in items],
        }))
    except Exception as e:
        logger.error(f"Watchlist error: {e}")
        return jsonify(api_response(False, error=str(e))), 500


def create_app(cache_manager=None):
    """Create Flask application."""
    app = Flask(__name__)
    
    # Store cache manager reference
    app.cache_manager = cache_manager
    
    # Register API blueprint
    app.register_blueprint(api)
    
    # Add CORS headers
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    return app
