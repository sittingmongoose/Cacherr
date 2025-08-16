#!/usr/bin/env python3
"""
PlexCacheUltra - Docker-optimized Plex media caching system
Main application entry point with web interface and scheduled execution
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template_string
import schedule

from config.settings import Config
from core.plex_cache_engine import PlexCacheUltraEngine

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging(config: Config):
    """Setup logging configuration"""
    log_dir = Path("/config/logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set log level
    log_level = getattr(logging, config.logging.level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "plexcache_ultra.log")
        ]
    )

# Create Flask app
app = Flask(__name__)

# Global variables
config = None
engine = None
scheduler_thread = None
scheduler_running = False

@app.route('/')
def index():
    """Main dashboard page"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PlexCacheUltra Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .status-card { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 20px; margin-bottom: 20px; }
            .status-running { border-left: 4px solid #28a745; }
            .status-idle { border-left: 4px solid #6c757d; }
            .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #0056b3; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
            .btn-success { background: #28a745; }
            .btn-success:hover { background: #218838; }
            .btn-warning { background: #ffc107; color: #212529; }
            .btn-warning:hover { background: #e0a800; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: white; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; text-align: center; }
            .stat-value { font-size: 2em; font-weight: bold; color: #007bff; }
            .stat-label { color: #6c757d; margin-top: 5px; }
            .log-container { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 15px; max-height: 300px; overflow-y: auto; }
            .log-entry { margin: 5px 0; padding: 5px; border-radius: 3px; }
            .log-info { background: #d1ecf1; }
            .log-warning { background: #fff3cd; }
            .log-error { background: #f8d7da; }
            .test-results { background: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 6px; padding: 15px; margin: 20px 0; }
            .file-detail { background: white; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px; margin: 5px 0; }
            .file-path { font-family: monospace; font-size: 0.9em; color: #495057; }
            .file-size { font-weight: bold; color: #28a745; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 PlexCacheUltra Dashboard</h1>
                <p>Docker-optimized Plex media caching system with enhanced features</p>
            </div>
            
            <div class="status-card" id="statusCard">
                <h3>System Status</h3>
                <p id="statusText">Loading...</p>
                <div>
                    <button class="btn btn-success" onclick="runCache()">Run Cache Operation</button>
                    <button class="btn btn-warning" onclick="runTestMode()">Run Test Mode</button>
                    <button class="btn btn-success" onclick="startScheduler()">Start Scheduler</button>
                    <button class="btn btn-danger" onclick="stopScheduler()">Stop Scheduler</button>
                </div>
            </div>
            
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="stat-value" id="filesToCache">-</div>
                    <div class="stat-label">Files to Cache</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="filesToArray">-</div>
                    <div class="stat-label">Files to Array</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="lastExecution">-</div>
                    <div class="stat-label">Last Execution</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="schedulerStatus">-</div>
                    <div class="stat-label">Scheduler Status</div>
                </div>
            </div>
            
            <div class="test-results" id="testResults" style="display: none;">
                <h3>Test Mode Results</h3>
                <div id="testResultsContent"></div>
            </div>
            
            <div class="status-card">
                <h3>Recent Logs</h3>
                <div class="log-container" id="logContainer">
                    <div class="log-entry log-info">Loading logs...</div>
                </div>
            </div>
        </div>
        
        <script>
            function updateStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusCard = document.getElementById('statusCard');
                        const statusText = document.getElementById('statusText');
                        const filesToCache = document.getElementById('filesToCache');
                        const filesToArray = document.getElementById('filesToArray');
                        const lastExecution = document.getElementById('lastExecution');
                        const schedulerStatus = document.getElementById('schedulerStatus');
                        
                        // Update status
                        if (data.status === 'running') {
                            statusCard.className = 'status-card status-running';
                            statusText.textContent = 'System is currently running';
                        } else {
                            statusCard.className = 'status-card status-idle';
                            statusText.textContent = 'System is idle';
                        }
                        
                        // Update stats
                        filesToCache.textContent = data.pending_operations.files_to_cache;
                        filesToArray.textContent = data.pending_operations.files_to_array;
                        lastExecution.textContent = data.last_execution.execution_time || 'Never';
                        schedulerStatus.textContent = scheduler_running ? 'Running' : 'Stopped';
                        
                        // Update test results if available
                        if (data.test_results) {
                            updateTestResults(data.test_results);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching status:', error);
                    });
            }
            
            function updateTestResults(testResults) {
                const testResultsDiv = document.getElementById('testResults');
                const testResultsContent = document.getElementById('testResultsContent');
                
                if (Object.keys(testResults).length === 0) {
                    testResultsDiv.style.display = 'none';
                    return;
                }
                
                testResultsDiv.style.display = 'block';
                let html = '';
                
                for (const [operation, data] of Object.entries(testResults)) {
                    if (data.file_count > 0) {
                        html += `<h4>${operation.replace('_', ' ').toUpperCase()} Operation</h4>`;
                        html += `<p><strong>Files:</strong> ${data.file_count} | <strong>Total Size:</strong> ${data.total_size_readable}</p>`;
                        
                        if (data.file_details && data.file_details.length > 0) {
                            html += '<div class="file-details">';
                            data.file_details.forEach(file => {
                                html += `
                                    <div class="file-detail">
                                        <div class="file-path">${file.filename}</div>
                                        <div class="file-size">${file.size_readable}</div>
                                        <div class="file-path">${file.directory}</div>
                                    </div>
                                `;
                            });
                            html += '</div>';
                        }
                    }
                }
                
                testResultsContent.innerHTML = html;
            }
            
            function runCache() {
                fetch('/api/run', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        setTimeout(updateStatus, 1000);
                    })
                    .catch(error => {
                        console.error('Error running cache:', error);
                        alert('Error running cache operation');
                    });
            }
            
            function runTestMode() {
                fetch('/api/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ test_mode: true }) })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        setTimeout(updateStatus, 1000);
                    })
                    .catch(error => {
                        console.error('Error running test mode:', error);
                        alert('Error running test mode');
                    });
            }
            
            function startScheduler() {
                fetch('/api/scheduler/start', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        setTimeout(updateStatus, 1000);
                    })
                    .catch(error => {
                        console.error('Error starting scheduler:', error);
                        alert('Error starting scheduler');
                    });
            }
            
            function stopScheduler() {
                fetch('/api/scheduler/stop', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        setTimeout(updateStatus, 1000);
                    })
                    .catch(error => {
                        console.error('Error stopping scheduler:', error);
                        alert('Error stopping scheduler');
                    });
            }
            
            // Update status every 5 seconds
            setInterval(updateStatus, 5000);
            updateStatus();
        </script>
    </body>
    </html>
    """
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Dashboard file not found. Please ensure dashboard.html exists in the current directory.", 404

@app.route('/api/status')
def api_status():
    """Get system status"""
    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    try:
        status = engine.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/run', methods=['POST'])
def api_run():
    """Run cache operation or test mode"""
    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    try:
        # Check if test mode is requested
        test_mode = False
        if request.is_json:
            data = None
            try:
                data = request.get_json(silent=True)
            except Exception:
                data = None
            if data is None:
                return jsonify({'error': 'Invalid JSON'}), 400
            if isinstance(data, dict):
                test_mode = bool(data.get('test_mode', False))
        
        # Run the engine
        success = bool(engine.run(test_mode=test_mode))
        
        if test_mode:
            message = "Test mode completed successfully" if success else "Test mode failed"
        else:
            message = "Cache operation completed successfully" if success else "Cache operation failed"

        return jsonify({'success': success, 'message': message, 'test_mode': bool(test_mode)})
    except Exception as e:
        # If bad JSON was supplied, treat as client error
        try:
            from werkzeug.exceptions import BadRequest
            if isinstance(e, BadRequest):
                return jsonify({'error': 'Invalid JSON'}), 400
        except Exception:
            pass
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-results')
def api_test_results():
    """Get test mode results"""
    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    try:
        test_results = engine.get_test_results()
        return jsonify(test_results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """Get current configuration settings"""
    if not config:
        return jsonify({'error': 'Configuration not initialized'}), 500
    
    try:
        return jsonify(config.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """Update configuration settings"""
    if not config:
        return jsonify({'error': 'Configuration not initialized'}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update environment variables
        updated_vars = {}
        for key, value in data.items():
            if hasattr(config, key) and hasattr(getattr(config, key), '__dict__'):
                # Handle nested configuration objects
                section = getattr(config, key)
                for subkey, subvalue in value.items():
                    if hasattr(section, subkey):
                        env_key = f"{key.upper()}_{subkey.upper()}"
                        os.environ[env_key] = str(subvalue)
                        updated_vars[env_key] = subvalue
            else:
                # Handle top-level configuration
                os.environ[key.upper()] = str(value)
                updated_vars[key.upper()] = value
        
        # Reinitialize engine if Plex settings were updated
        global engine
        if 'plex' in data and (data['plex'].get('url') or data['plex'].get('token')):
            try:
                # Reload config to get new environment variables
                config.reload()
                # Try to reinitialize engine with new Plex credentials
                engine = PlexCacheUltraEngine(config)
                logging.info("Engine reinitialized with new Plex credentials")
            except Exception as e:
                logging.warning(f"Failed to reinitialize engine with new Plex credentials: {e}")
                # Keep old engine if reinitialization fails
                pass
        
        return jsonify({
            'success': True,
            'message': f'Updated {len(updated_vars)} settings',
            'updated_vars': updated_vars
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/validate', methods=['POST'])
def api_validate_settings():
    """Validate configuration settings"""
    if not config:
        return jsonify({'error': 'Configuration not initialized'}), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'path_checks': {}
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
            
            # Check additional sources
            if 'additional_sources' in paths and paths['additional_sources']:
                additional_sources = paths['additional_sources']
                validation_results['path_checks']['additional_sources'] = []
                
                for source in additional_sources:
                    if os.path.exists(source):
                        validation_results['path_checks']['additional_sources'].append({
                            'exists': True,
                            'readable': os.access(source, os.R_OK),
                            'path': source
                        })
                    else:
                        validation_results['path_checks']['additional_sources'].append({
                            'exists': False,
                            'readable': False,
                            'path': source
                        })
                        validation_results['warnings'].append(f"Additional source directory does not exist: {source}")
                
                # Check additional plex sources
                if 'additional_plex_sources' in paths and paths['additional_plex_sources']:
                    additional_plex_sources = paths['additional_plex_sources']
                    
                    # Validate count matching
                    if len(additional_sources) != len(additional_plex_sources):
                        validation_results['errors'].append(f"Additional sources count mismatch: {len(additional_sources)} real sources vs {len(additional_plex_sources)} plex sources")
                        validation_results['valid'] = False
                    
                    # Check for duplicate plex sources
                    if len(set(additional_plex_sources)) != len(additional_plex_sources):
                        validation_results['warnings'].append("Duplicate plex source paths detected in additional plex sources")
                    
                    validation_results['path_checks']['additional_plex_sources'] = []
                    for plex_source in additional_plex_sources:
                        validation_results['path_checks']['additional_plex_sources'].append({
                            'exists': True,  # Plex sources are internal paths, so they "exist" by definition
                            'readable': True,
                            'path': plex_source
                        })
                else:
                    if additional_sources:
                        validation_results['warnings'].append("Additional sources specified but no additional plex sources provided")
        
        # Validate Plex connection
        if 'plex' in data:
            plex_config = data['plex']
            if 'url' in plex_config and 'token' in plex_config:
                try:
                    import requests
                    plex_url = plex_config['url']
                    plex_token = plex_config['token']
                    
                    # Test Plex connection
                    test_url = f"{plex_url}/status/sessions"
                    headers = {'X-Plex-Token': plex_token}
                    response = requests.get(test_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        validation_results['plex_connection'] = {
                            'status': 'success',
                            'url': plex_url
                        }
                    else:
                        validation_results['plex_connection'] = {
                            'status': 'failed',
                            'url': plex_url,
                            'status_code': response.status_code
                        }
                        validation_results['errors'].append(f"Plex connection failed: HTTP {response.status_code}")
                        validation_results['valid'] = False
                        
                except Exception as e:
                    validation_results['plex_connection'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    validation_results['errors'].append(f"Plex connection error: {e}")
                    validation_results['valid'] = False
        
        return jsonify(validation_results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/reset', methods=['POST'])
def api_reset_settings():
    """Reset configuration to defaults"""
    if not config:
        return jsonify({'error': 'Configuration not initialized'}), 500
    
    try:
        # Reset to default values
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
            'TEST_DRY_RUN': 'true',
            'DEBUG': 'false'
        }
        
        for key, value in default_settings.items():
            os.environ[key] = value
        
        return jsonify({
            'success': True,
            'message': 'Settings reset to defaults',
            'defaults': default_settings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/start', methods=['POST'])
def api_scheduler_start():
    """Start the scheduler"""
    global scheduler_running
    if scheduler_running:
        return jsonify({'message': 'Scheduler is already running'})
    
    try:
        start_scheduler()
        return jsonify({'message': 'Scheduler started successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def api_scheduler_stop():
    """Stop the scheduler"""
    global scheduler_running
    if not scheduler_running:
        return jsonify({'message': 'Scheduler is not running'})
    
    try:
        stop_scheduler()
        return jsonify({'message': 'Scheduler stopped successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/start', methods=['POST'])
def api_watcher_start():
    """Start real-time Plex watching"""
    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    try:
        success = engine.start_real_time_watching()
        if success:
            return jsonify({'success': True, 'message': 'Real-time Plex watching started successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start real-time watching'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/stop', methods=['POST'])
def api_watcher_stop():
    """Stop real-time Plex watching"""
    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    try:
        success = engine.stop_real_time_watching()
        if success:
            return jsonify({'success': True, 'message': 'Real-time Plex watching stopped successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to stop real-time watching'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/status', methods=['GET'])
def api_watcher_status():
    """Get real-time watcher status and statistics"""
    try:
        is_watching = engine.is_real_time_watching() if hasattr(engine, 'is_real_time_watching') else False
        stats = engine.get_watcher_stats() if hasattr(engine, 'get_watcher_stats') else {}
        cache_removal_schedule = engine.get_cache_removal_schedule() if hasattr(engine, 'get_cache_removal_schedule') else {}
        user_activity_status = engine.get_user_activity_status() if hasattr(engine, 'get_user_activity_status') else {}
        watch_history = {}
        if hasattr(engine, 'get_watch_history'):
            try:
                wh = engine.get_watch_history()
                if isinstance(wh, (dict, list, str, int, float, bool)) or wh is None:
                    watch_history = wh
            except Exception:
                watch_history = {}

        status = {
            'is_watching': is_watching,
            'stats': stats,
            'watch_history': watch_history,
            'cache_removal_schedule': cache_removal_schedule,
            'user_activity_status': user_activity_status
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/cache-removal-schedule', methods=['GET'])
def api_cache_removal_schedule():
    """Get the current cache removal schedule"""
    try:
        schedule = engine.get_cache_removal_schedule()
        return jsonify(schedule)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watcher/user-activity', methods=['GET'])
def api_user_activity():
    """Get user activity status from real-time watcher"""
    try:
        user_activity = engine.get_user_activity_status()
        return jsonify({
            'success': True,
            'user_activity': user_activity
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Trakt.tv API endpoints
@app.route('/api/trakt/status', methods=['GET'])
def api_trakt_status():
    """Get Trakt.tv watcher status and statistics"""
    try:
        stats = engine.get_trakt_stats()
        trending_movies = engine.get_trakt_trending_movies()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'trending_movies': trending_movies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trakt/trending-movies', methods=['GET'])
def api_trakt_trending_movies():
    """Get current trending movies from Trakt.tv"""
    try:
        trending_movies = engine.get_trakt_trending_movies()
        return jsonify({
            'success': True,
            'trending_movies': trending_movies
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trakt/start', methods=['POST'])
def api_trakt_start():
    """Start Trakt.tv watcher"""
    try:
        success = engine.start_trakt_watcher()
        return jsonify({
            'success': success,
            'message': 'Trakt.tv watcher started' if success else 'Failed to start Trakt.tv watcher'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trakt/stop', methods=['POST'])
def api_trakt_stop():
    """Stop Trakt.tv watcher"""
    try:
        success = engine.stop_trakt_watcher()
        return jsonify({
            'success': success,
            'message': 'Trakt.tv watcher stopped' if success else 'Failed to stop Trakt.tv watcher'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trakt/clear-history', methods=['POST'])
def api_trakt_clear_history():
    """Clear Trakt.tv watcher history"""
    try:
        success = engine.clear_trakt_history()
        return jsonify({
            'success': success,
            'message': 'Trakt.tv history cleared' if success else 'Failed to clear Trakt.tv history'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/watcher/clear-history', methods=['POST'])
def api_watcher_clear_history():
    """Clear the watch history"""
    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500
    
    try:
        engine.clear_watch_history()
        return jsonify({'success': True, 'message': 'Watch history cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Get recent logs"""
    try:
        log_file = Path("/config/logs/plexcache_ultra.log")
        if not log_file.exists():
            return jsonify({'logs': [], 'message': 'No log file found'})
        
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
        
        return jsonify({'logs': log_entries})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Docker"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

def start_scheduler():
    """Start the background scheduler"""
    global scheduler_running, scheduler_thread
    
    if scheduler_running:
        return
    
    def run_scheduler():
        global scheduler_running
        scheduler_running = True
        
        # Schedule cache operation every 6 hours
        schedule.every(6).hours.do(lambda: engine.run() if engine else None)
        
        while scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("Scheduler started")

def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler_running
    scheduler_running = False
    if scheduler_thread:
        scheduler_thread.join(timeout=5)
    logging.info("Scheduler stopped")

def main():
    """Main application entry point"""
    global config, engine
    
    try:
        # Load configuration
        config = Config()
        
        # Setup logging
        setup_logging(config)
        
        # Validate configuration
        if not config.validate():
            logging.error("Configuration validation failed")
            sys.exit(1)
        
        logging.info("Configuration loaded successfully")
        logging.info(f"Configuration: {config.to_dict()}")
        
        # Initialize engine (Plex connection is optional for container startup)
        try:
            engine = PlexCacheUltraEngine(config)
            logging.info("PlexCacheUltra engine initialized")
        except Exception as e:
            logging.warning(f"PlexCacheUltra engine initialization failed (Plex connection issue): {e}")
            logging.info("Container will start but Plex operations will be limited until connection is established")
            engine = None
        
        # Start scheduler if configured
        if not config.test_mode.enabled and config.web.enable_scheduler:
            start_scheduler()
        
        # Start Flask app
        # Prefer WEB_PORT/PORT via config
        app.run(host=config.web.host, port=config.web.port, debug=config.web.debug)
        
    except Exception as e:
        logging.error(f"Failed to start PlexCacheUltra: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
