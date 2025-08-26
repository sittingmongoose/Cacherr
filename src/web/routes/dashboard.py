"""
Dashboard routes for PlexCacheUltra web interface.

This module provides the main dashboard and UI routes for the PlexCacheUltra
web interface. Includes the main dashboard page with embedded HTML template
and any additional UI-focused routes.

The dashboard provides:
- Real-time system status display
- Cache operation controls (run, test mode)
- Scheduler management (start/stop)
- Live statistics and metrics
- Recent logs display
- Test mode results visualization

Example:
    ```
    GET /
    Returns: HTML dashboard page with embedded JavaScript
    ```
"""

import logging
from pathlib import Path
from typing import Optional

from flask import Blueprint, render_template_string, current_app
from pydantic import BaseModel, Field


# Blueprint for dashboard routes
dashboard_bp = Blueprint('dashboard', __name__)

logger = logging.getLogger(__name__)


class DashboardConfig(BaseModel):
    """Configuration for dashboard rendering."""
    
    title: str = Field(default="Cacherr Dashboard", description="Dashboard page title")
    refresh_interval: int = Field(default=5000, description="Auto-refresh interval in milliseconds")
    show_debug_info: bool = Field(default=False, description="Show debug information")
    theme: str = Field(default="default", description="Dashboard theme")
    
    class Config:
        extra = "forbid"


# Embedded HTML template for the dashboard
DASHBOARD_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ config.title }}</title>
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
        .btn:disabled { background: #6c757d; cursor: not-allowed; }
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
        .log-entry { margin: 5px 0; padding: 5px; border-radius: 3px; font-family: monospace; font-size: 0.9em; }
        .log-info { background: #d1ecf1; }
        .log-warning { background: #fff3cd; }
        .log-error { background: #f8d7da; }
        .log-debug { background: #d4edda; }
        .test-results { background: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 6px; padding: 15px; margin: 20px 0; }
        .file-detail { background: white; border: 1px solid #dee2e6; border-radius: 4px; padding: 10px; margin: 5px 0; }
        .file-path { font-family: monospace; font-size: 0.9em; color: #495057; }
        .file-size { font-weight: bold; color: #28a745; }
        .loading { color: #6c757d; font-style: italic; }
        .error-message { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success-message { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .health-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .health-healthy { background-color: #28a745; }
        .health-unhealthy { background-color: #dc3545; }
        .health-unknown { background-color: #6c757d; }
        .health-not-configured { background-color: #ffc107; }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .container { margin: 10px; padding: 15px; }
            .stats-grid { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }
            .btn { padding: 8px 16px; margin: 3px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 {{ config.title }}</h1>
            <p>Docker-optimized Plex media caching system with enhanced features</p>
            {% if config.show_debug_info %}
            <div class="debug-info" style="font-size: 0.9em; color: #6c757d;">
                Debug Mode Enabled | Refresh Interval: {{ config.refresh_interval }}ms
            </div>
            {% endif %}
        </div>
        
        <!-- System Status Card -->
        <div class="status-card" id="statusCard">
            <h3>System Status</h3>
            <p id="statusText" class="loading">Loading system status...</p>
            <div id="healthIndicators" style="margin: 10px 0;"></div>
            <div id="controlButtons">
                <button class="btn btn-success" onclick="runCache()" id="runCacheBtn">Run Cache Operation</button>
                <button class="btn btn-warning" onclick="runTestMode()" id="runTestBtn">Run Test Mode</button>
                <button class="btn btn-success" onclick="startScheduler()" id="startSchedulerBtn">Start Scheduler</button>
                <button class="btn btn-danger" onclick="stopScheduler()" id="stopSchedulerBtn">Stop Scheduler</button>
            </div>
        </div>
        
        <!-- Statistics Grid -->
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
            <div class="stat-card">
                <div class="stat-value" id="cacheSize">-</div>
                <div class="stat-label">Cache Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="systemHealth">-</div>
                <div class="stat-label">System Health</div>
            </div>
        </div>
        
        <!-- Test Results Section -->
        <div class="test-results" id="testResults" style="display: none;">
            <h3>Test Mode Results</h3>
            <div id="testResultsContent">No test results available</div>
        </div>
        
        <!-- Recent Logs Section -->
        <div class="status-card">
            <h3>Recent Logs</h3>
            <div class="log-container" id="logContainer">
                <div class="log-entry log-info loading">Loading recent logs...</div>
            </div>
        </div>
    </div>
    
    <script>
        // Global variables
        let isOperationRunning = false;
        let schedulerRunning = false;
        let lastUpdateTime = null;
        
        // Utility functions
        function showMessage(message, type = 'info') {
            const existingMessage = document.querySelector('.error-message, .success-message');
            if (existingMessage) {
                existingMessage.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
            messageDiv.textContent = message;
            
            const statusCard = document.getElementById('statusCard');
            statusCard.insertBefore(messageDiv, statusCard.querySelector('#controlButtons'));
            
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 5000);
        }
        
        function updateButtonStates() {
            const runCacheBtn = document.getElementById('runCacheBtn');
            const runTestBtn = document.getElementById('runTestBtn');
            const startSchedulerBtn = document.getElementById('startSchedulerBtn');
            const stopSchedulerBtn = document.getElementById('stopSchedulerBtn');
            
            runCacheBtn.disabled = isOperationRunning;
            runTestBtn.disabled = isOperationRunning;
            startSchedulerBtn.disabled = schedulerRunning;
            stopSchedulerBtn.disabled = !schedulerRunning;
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function getHealthIndicatorHTML(status, label) {
            const statusClass = `health-${status}`;
            return `<span class="health-indicator ${statusClass}"></span>${label}: ${status}`;
        }
        
        // API interaction functions
        async function fetchWithErrorHandling(url, options = {}) {
            try {
                const response = await fetch(url, options);
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || `HTTP ${response.status}`);
                }
                
                return data;
            } catch (error) {
                console.error(`Error fetching ${url}:`, error);
                throw error;
            }
        }
        
        async function updateStatus() {
            try {
                const [statusData, healthData] = await Promise.all([
                    fetchWithErrorHandling('/api/status'),
                    fetchWithErrorHandling('/health/detailed').catch(() => null)
                ]);
                
                // Update main status
                const statusCard = document.getElementById('statusCard');
                const statusText = document.getElementById('statusText');
                
                if (statusData.status === 'running') {
                    statusCard.className = 'status-card status-running';
                    statusText.textContent = 'System is currently running a cache operation';
                    isOperationRunning = true;
                } else {
                    statusCard.className = 'status-card status-idle';
                    statusText.textContent = 'System is idle and ready for operations';
                    isOperationRunning = false;
                }
                
                // Update statistics
                document.getElementById('filesToCache').textContent = 
                    statusData.pending_operations?.files_to_cache || '-';
                document.getElementById('filesToArray').textContent = 
                    statusData.pending_operations?.files_to_array || '-';
                document.getElementById('lastExecution').textContent = 
                    statusData.last_execution?.execution_time || 'Never';
                
                // Update scheduler status
                schedulerRunning = statusData.scheduler_running || false;
                document.getElementById('schedulerStatus').textContent = 
                    schedulerRunning ? 'Running' : 'Stopped';
                
                // Update health information if available
                if (healthData) {
                    const healthIndicators = document.getElementById('healthIndicators');
                    let healthHTML = '';
                    
                    if (healthData.services) {
                        Object.entries(healthData.services).forEach(([service, status]) => {
                            healthHTML += getHealthIndicatorHTML(status, service.replace('_', ' ')) + ' ';
                        });
                    }
                    
                    healthIndicators.innerHTML = healthHTML;
                    
                    // Update system health
                    document.getElementById('systemHealth').textContent = healthData.status || '-';
                    
                    // Update cache size if available
                    if (healthData.cache_statistics && healthData.cache_statistics.total_size_bytes) {
                        document.getElementById('cacheSize').textContent = 
                            formatBytes(healthData.cache_statistics.total_size_bytes);
                    }
                }
                
                // Update test results if available
                if (statusData.test_results && Object.keys(statusData.test_results).length > 0) {
                    updateTestResults(statusData.test_results);
                }
                
                // Update button states
                updateButtonStates();
                
                lastUpdateTime = new Date();
                
            } catch (error) {
                console.error('Error updating status:', error);
                document.getElementById('statusText').textContent = 
                    'Error loading system status: ' + error.message;
                showMessage('Failed to update system status: ' + error.message, 'error');
            }
        }
        
        function updateTestResults(testResults) {
            const testResultsDiv = document.getElementById('testResults');
            const testResultsContent = document.getElementById('testResultsContent');
            
            if (!testResults || Object.keys(testResults).length === 0) {
                testResultsDiv.style.display = 'none';
                return;
            }
            
            testResultsDiv.style.display = 'block';
            let html = '';
            
            Object.entries(testResults).forEach(([operation, data]) => {
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
            });
            
            testResultsContent.innerHTML = html || 'No test results to display';
        }
        
        async function updateLogs() {
            try {
                const logsData = await fetchWithErrorHandling('/api/logs');
                const logContainer = document.getElementById('logContainer');
                
                if (logsData.data && logsData.data.logs && logsData.data.logs.length > 0) {
                    let html = '';
                    logsData.data.logs.slice(-50).forEach(log => {
                        const levelClass = `log-${log.level}`;
                        html += `<div class="log-entry ${levelClass}">${log.message}</div>`;
                    });
                    logContainer.innerHTML = html;
                } else {
                    logContainer.innerHTML = '<div class="log-entry log-info">No recent logs available</div>';
                }
                
                // Auto-scroll to bottom
                logContainer.scrollTop = logContainer.scrollHeight;
                
            } catch (error) {
                console.error('Error updating logs:', error);
                document.getElementById('logContainer').innerHTML = 
                    `<div class="log-entry log-error">Error loading logs: ${error.message}</div>`;
            }
        }
        
        // Operation functions
        async function runCache() {
            if (isOperationRunning) {
                showMessage('An operation is already running', 'error');
                return;
            }
            
            try {
                isOperationRunning = true;
                updateButtonStates();
                showMessage('Starting cache operation...', 'info');
                
                const result = await fetchWithErrorHandling('/api/run', { method: 'POST' });
                showMessage(result.message || 'Cache operation completed', 'success');
                
                // Refresh status after a short delay
                setTimeout(updateStatus, 1000);
                
            } catch (error) {
                showMessage('Cache operation failed: ' + error.message, 'error');
            } finally {
                isOperationRunning = false;
                updateButtonStates();
            }
        }
        
        async function runTestMode() {
            if (isOperationRunning) {
                showMessage('An operation is already running', 'error');
                return;
            }
            
            try {
                isOperationRunning = true;
                updateButtonStates();
                showMessage('Starting test mode analysis...', 'info');
                
                const result = await fetchWithErrorHandling('/api/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ test_mode: true })
                });
                
                showMessage(result.message || 'Test mode completed', 'success');
                
                // Refresh status to get test results
                setTimeout(updateStatus, 1000);
                
            } catch (error) {
                showMessage('Test mode failed: ' + error.message, 'error');
            } finally {
                isOperationRunning = false;
                updateButtonStates();
            }
        }
        
        async function startScheduler() {
            try {
                const result = await fetchWithErrorHandling('/api/scheduler/start', { method: 'POST' });
                showMessage(result.message || 'Scheduler started', 'success');
                schedulerRunning = true;
                updateButtonStates();
                setTimeout(updateStatus, 1000);
            } catch (error) {
                showMessage('Failed to start scheduler: ' + error.message, 'error');
            }
        }
        
        async function stopScheduler() {
            try {
                const result = await fetchWithErrorHandling('/api/scheduler/stop', { method: 'POST' });
                showMessage(result.message || 'Scheduler stopped', 'success');
                schedulerRunning = false;
                updateButtonStates();
                setTimeout(updateStatus, 1000);
            } catch (error) {
                showMessage('Failed to stop scheduler: ' + error.message, 'error');
            }
        }
        
        // Initialize dashboard
        function initializeDashboard() {
            console.log('Initializing PlexCacheUltra Dashboard...');
            
            // Initial load
            updateStatus();
            updateLogs();
            
            // Set up periodic updates
            setInterval(updateStatus, {{ config.refresh_interval }});
            setInterval(updateLogs, {{ config.refresh_interval }} * 2); // Update logs less frequently
            
            console.log('Dashboard initialized successfully');
        }
        
        // Start dashboard when page loads
        document.addEventListener('DOMContentLoaded', initializeDashboard);
    </script>
</body>
</html>
"""


@dashboard_bp.route('/')
def index():
    """
    Main dashboard page route.
    
    Renders the main PlexCacheUltra dashboard with embedded HTML template
    and JavaScript for real-time status updates and control functionality.
    
    Returns:
        Rendered HTML dashboard page
    """
    try:
        # Check if external dashboard.html exists (legacy support)
        dashboard_file = Path('dashboard.html')
        if dashboard_file.exists():
            logger.info("Using external dashboard.html file")
            try:
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read external dashboard.html: {e}")
                # Fall through to embedded template
        
        # Use embedded template
        config = DashboardConfig(
            show_debug_info=current_app.config.get('DEBUG', False),
            refresh_interval=5000  # 5 seconds
        )
        
        logger.debug("Rendering embedded dashboard template")
        return render_template_string(DASHBOARD_HTML_TEMPLATE, config=config)
        
    except Exception as e:
        logger.error(f"Failed to render dashboard: {e}")
        return f"""
        <html>
        <head><title>Dashboard Error</title></head>
        <body>
        <h1>Dashboard Error</h1>
        <p>Failed to load dashboard: {e}</p>
        <p>Please check the application logs for more details.</p>
        </body>
        </html>
        """, 500


@dashboard_bp.route('/dashboard/config')
def dashboard_config():
    """
    Dashboard configuration endpoint.
    
    Returns configuration information that can be used by external
    dashboard implementations or for debugging purposes.
    
    Returns:
        JSON response with dashboard configuration
    """
    try:
        config = DashboardConfig(
            show_debug_info=current_app.config.get('DEBUG', False),
            refresh_interval=5000
        )
        
        return {
            "config": config.dict(),
            "flask_config": {
                "debug": current_app.config.get('DEBUG', False),
                "testing": current_app.config.get('TESTING', False)
            },
            "endpoints": {
                "status": "/api/status",
                "health": "/health",
                "logs": "/api/logs",
                "run": "/api/run",
                "scheduler_start": "/api/scheduler/start",
                "scheduler_stop": "/api/scheduler/stop"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard config: {e}")
        return {"error": str(e)}, 500