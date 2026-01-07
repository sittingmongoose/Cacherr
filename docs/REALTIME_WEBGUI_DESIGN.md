# Real-Time WebGUI Design

## Overview

The WebGUI needs to show live updates of cache operations, progress bars, and system status. This document describes the WebSocket-based architecture for real-time communication.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  Browser                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         React Frontend                               │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │    │
│  │  │  Dashboard   │  │   Settings   │  │      Live Activity       │  │    │
│  │  │  (stats)     │  │   (config)   │  │  (progress, operations)  │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │    │
│  │                           │                        │               │    │
│  │                    useWebSocket()          useWebSocket()          │    │
│  │                           │                        │               │    │
│  └───────────────────────────┼────────────────────────┼───────────────┘    │
│                              │                        │                     │
│                              ▼                        ▼                     │
│                    ┌─────────────────────────────────────┐                  │
│                    │         WebSocket Connection        │                  │
│                    │     ws://host:5445/ws/events        │                  │
│                    └─────────────────────────────────────┘                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       │ WebSocket
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                              Cacherr Backend                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Flask + Flask-SocketIO                        │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │    │
│  │  │  REST API    │  │  WebSocket   │  │    Event Broadcaster     │  │    │
│  │  │  /api/*      │  │  Handler     │  │                          │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │    │
│  │                                                  ▲                  │    │
│  │                                                  │                  │    │
│  │  ┌───────────────────────────────────────────────┴──────────────┐  │    │
│  │  │                     Cache Manager                            │  │    │
│  │  │  - File operations emit events                               │  │    │
│  │  │  - Progress updates emit events                              │  │    │
│  │  │  - Status changes emit events                                │  │    │
│  │  └──────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Event Types

### 1. Status Events
```typescript
interface StatusEvent {
  type: 'status';
  timestamp: string;
  data: {
    running: boolean;
    health: 'healthy' | 'warning' | 'critical';
    active_operations: number;
    active_sessions: number;
  };
}
```

### 2. Cache Stats Events
```typescript
interface StatsEvent {
  type: 'stats';
  timestamp: string;
  data: {
    total_size_bytes: number;
    limit_bytes: number;
    used_percent: number;
    file_count: number;
    health: CacheHealth;
  };
}
```

### 3. Operation Progress Events
```typescript
interface OperationProgressEvent {
  type: 'operation_progress';
  timestamp: string;
  data: {
    operation_id: string;
    operation_type: 'cache' | 'restore' | 'evict';
    file_name: string;
    progress_percent: number;
    bytes_transferred: number;
    bytes_total: number;
    speed_bytes_per_sec: number;
    eta_seconds: number;
  };
}
```

### 4. Operation Complete Events
```typescript
interface OperationCompleteEvent {
  type: 'operation_complete';
  timestamp: string;
  data: {
    operation_id: string;
    operation_type: 'cache' | 'restore' | 'evict';
    file_path: string;
    success: boolean;
    error?: string;
    duration_seconds: number;
    bytes_transferred: number;
  };
}
```

### 5. Session Events
```typescript
interface SessionEvent {
  type: 'session_start' | 'session_update' | 'session_end';
  timestamp: string;
  data: {
    session_id: string;
    username: string;
    media_title: string;
    state: 'playing' | 'paused' | 'stopped';
    progress_percent: number;
    file_path: string;
  };
}
```

### 6. Log Events
```typescript
interface LogEvent {
  type: 'log';
  timestamp: string;
  data: {
    level: 'debug' | 'info' | 'warning' | 'error';
    message: string;
    source: string;
  };
}
```

### 7. Cycle Events
```typescript
interface CycleEvent {
  type: 'cycle_start' | 'cycle_progress' | 'cycle_complete';
  timestamp: string;
  data: {
    cycle_id: string;
    phase: 'ondeck' | 'watchlist' | 'lists' | 'retention' | 'eviction';
    items_processed: number;
    items_total: number;
    files_cached: number;
    files_restored: number;
  };
}
```

---

## Backend Implementation

### Flask-SocketIO Setup
```python
from flask import Flask
from flask_socketio import SocketIO, emit
import logging

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class EventBroadcaster:
    """Broadcasts events to all connected WebSocket clients."""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self._logger = logging.getLogger(__name__)
    
    def emit_status(self, status: dict):
        """Emit status update to all clients."""
        self.socketio.emit('status', {
            'type': 'status',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': status
        })
    
    def emit_stats(self, stats: dict):
        """Emit cache stats update."""
        self.socketio.emit('stats', {
            'type': 'stats',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': stats
        })
    
    def emit_operation_progress(self, operation_id: str, progress: dict):
        """Emit file operation progress."""
        self.socketio.emit('operation_progress', {
            'type': 'operation_progress',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'operation_id': operation_id,
                **progress
            }
        })
    
    def emit_operation_complete(self, operation_id: str, result: dict):
        """Emit file operation completion."""
        self.socketio.emit('operation_complete', {
            'type': 'operation_complete',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'operation_id': operation_id,
                **result
            }
        })
    
    def emit_session(self, event_type: str, session: dict):
        """Emit Plex session event."""
        self.socketio.emit(event_type, {
            'type': event_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': session
        })
    
    def emit_log(self, level: str, message: str, source: str = ""):
        """Emit log message to clients."""
        self.socketio.emit('log', {
            'type': 'log',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': {
                'level': level,
                'message': message,
                'source': source
            }
        })

# Global broadcaster instance
broadcaster = EventBroadcaster(socketio)

@socketio.on('connect')
def handle_connect():
    """Handle new WebSocket connection."""
    logging.info("WebSocket client connected")
    # Send current status immediately
    emit('status', {
        'type': 'status',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data': get_current_status()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    logging.info("WebSocket client disconnected")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription requests for specific event types."""
    event_types = data.get('events', ['all'])
    # Could implement per-client filtering here
    logging.debug(f"Client subscribed to: {event_types}")
```

### File Operation Progress Tracking
```python
import uuid
import time
import os
from typing import Callable

class ProgressTrackingFileCopy:
    """File copy with progress reporting via WebSocket."""
    
    def __init__(self, broadcaster: EventBroadcaster, chunk_size: int = 1024 * 1024):
        self.broadcaster = broadcaster
        self.chunk_size = chunk_size
    
    def copy_with_progress(self, src: str, dst: str, operation_type: str = 'cache') -> dict:
        """Copy file with real-time progress updates."""
        operation_id = str(uuid.uuid4())[:8]
        file_name = os.path.basename(src)
        total_size = os.path.getsize(src)
        
        start_time = time.time()
        copied = 0
        last_update = 0
        
        try:
            with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                while True:
                    chunk = fsrc.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    fdst.write(chunk)
                    copied += len(chunk)
                    
                    # Update progress every 500ms or 5%
                    now = time.time()
                    progress = (copied / total_size) * 100
                    
                    if now - last_update >= 0.5 or progress - last_update >= 5:
                        elapsed = now - start_time
                        speed = copied / elapsed if elapsed > 0 else 0
                        eta = (total_size - copied) / speed if speed > 0 else 0
                        
                        self.broadcaster.emit_operation_progress(operation_id, {
                            'operation_type': operation_type,
                            'file_name': file_name,
                            'progress_percent': round(progress, 1),
                            'bytes_transferred': copied,
                            'bytes_total': total_size,
                            'speed_bytes_per_sec': int(speed),
                            'eta_seconds': int(eta),
                        })
                        last_update = now
            
            duration = time.time() - start_time
            
            self.broadcaster.emit_operation_complete(operation_id, {
                'operation_type': operation_type,
                'file_path': dst,
                'success': True,
                'duration_seconds': round(duration, 2),
                'bytes_transferred': total_size,
            })
            
            return {'success': True, 'operation_id': operation_id}
            
        except Exception as e:
            self.broadcaster.emit_operation_complete(operation_id, {
                'operation_type': operation_type,
                'file_path': dst,
                'success': False,
                'error': str(e),
                'duration_seconds': time.time() - start_time,
                'bytes_transferred': copied,
            })
            
            return {'success': False, 'error': str(e), 'operation_id': operation_id}
```

---

## Frontend Implementation

### React WebSocket Hook
```typescript
import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketOptions {
  url: string;
  reconnectInterval?: number;
  maxReconnects?: number;
}

export function useWebSocket<T>(options: UseWebSocketOptions) {
  const { url, reconnectInterval = 3000, maxReconnects = 10 } = options;
  
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };
      
      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;
        
        // Attempt reconnect
        if (reconnectCountRef.current < maxReconnects) {
          reconnectCountRef.current++;
          console.log(`Reconnecting (${reconnectCountRef.current}/${maxReconnects})...`);
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        } else {
          setError('Connection lost. Please refresh the page.');
        }
      };
      
      wsRef.current = ws;
    } catch (e) {
      setError('Failed to connect');
    }
  }, [url, reconnectInterval, maxReconnects]);
  
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
  
  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);
  
  return { isConnected, lastMessage, error, send };
}
```

### Live Activity Component
```typescript
import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface Operation {
  operation_id: string;
  operation_type: 'cache' | 'restore' | 'evict';
  file_name: string;
  progress_percent: number;
  speed_bytes_per_sec: number;
  eta_seconds: number;
}

const LiveActivity: React.FC = () => {
  const [operations, setOperations] = useState<Map<string, Operation>>(new Map());
  const [recentLogs, setRecentLogs] = useState<string[]>([]);
  
  const { lastMessage, isConnected } = useWebSocket({
    url: `ws://${window.location.host}/ws/events`,
  });
  
  useEffect(() => {
    if (!lastMessage) return;
    
    switch (lastMessage.type) {
      case 'operation_progress':
        setOperations(prev => {
          const next = new Map(prev);
          next.set(lastMessage.data.operation_id, lastMessage.data);
          return next;
        });
        break;
      
      case 'operation_complete':
        setOperations(prev => {
          const next = new Map(prev);
          next.delete(lastMessage.data.operation_id);
          return next;
        });
        break;
      
      case 'log':
        setRecentLogs(prev => [
          `[${lastMessage.data.level}] ${lastMessage.data.message}`,
          ...prev.slice(0, 99)
        ]);
        break;
    }
  }, [lastMessage]);
  
  return (
    <div className="live-activity">
      <div className="connection-status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
      
      <h3>Active Operations ({operations.size})</h3>
      <div className="operations-list">
        {Array.from(operations.values()).map(op => (
          <div key={op.operation_id} className="operation">
            <div className="operation-header">
              <span className={`badge ${op.operation_type}`}>
                {op.operation_type.toUpperCase()}
              </span>
              <span className="file-name">{op.file_name}</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${op.progress_percent}%` }}
              />
            </div>
            <div className="operation-stats">
              <span>{op.progress_percent.toFixed(1)}%</span>
              <span>{formatSpeed(op.speed_bytes_per_sec)}</span>
              <span>ETA: {formatEta(op.eta_seconds)}</span>
            </div>
          </div>
        ))}
        {operations.size === 0 && (
          <div className="no-operations">No active operations</div>
        )}
      </div>
      
      <h3>Recent Activity</h3>
      <div className="logs-list">
        {recentLogs.slice(0, 10).map((log, i) => (
          <div key={i} className="log-entry">{log}</div>
        ))}
      </div>
    </div>
  );
};

function formatSpeed(bytesPerSec: number): string {
  if (bytesPerSec > 1024 * 1024) {
    return `${(bytesPerSec / 1024 / 1024).toFixed(1)} MB/s`;
  }
  return `${(bytesPerSec / 1024).toFixed(1)} KB/s`;
}

function formatEta(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

export default LiveActivity;
```

---

## Configurable Refresh Rate

For users who prefer polling over WebSocket (or as fallback):

```typescript
interface RefreshSettings {
  mode: 'realtime' | 'polling';
  pollingInterval: 5 | 10 | 15 | 30 | 60 | 300;  // seconds
}

const RefreshSettingsPanel: React.FC<{
  settings: RefreshSettings;
  onChange: (settings: RefreshSettings) => void;
}> = ({ settings, onChange }) => {
  return (
    <div className="refresh-settings">
      <label>
        <input
          type="radio"
          name="mode"
          value="realtime"
          checked={settings.mode === 'realtime'}
          onChange={() => onChange({ ...settings, mode: 'realtime' })}
        />
        Real-time (WebSocket)
      </label>
      
      <label>
        <input
          type="radio"
          name="mode"
          value="polling"
          checked={settings.mode === 'polling'}
          onChange={() => onChange({ ...settings, mode: 'polling' })}
        />
        Polling
      </label>
      
      {settings.mode === 'polling' && (
        <select
          value={settings.pollingInterval}
          onChange={(e) => onChange({
            ...settings,
            pollingInterval: parseInt(e.target.value) as any
          })}
        >
          <option value="5">5 seconds</option>
          <option value="10">10 seconds</option>
          <option value="15">15 seconds</option>
          <option value="30">30 seconds</option>
          <option value="60">1 minute</option>
          <option value="300">5 minutes</option>
        </select>
      )}
    </div>
  );
};
```

---

## Plex API Rate Limiting

To protect Plex from excessive API calls:

```python
class RateLimitedPlexClient:
    """Plex client with configurable rate limiting."""
    
    def __init__(
        self,
        url: str,
        token: str,
        min_request_interval_ms: int = 1000,
        max_requests_per_minute: int = 30,
    ):
        self.url = url
        self.token = token
        self.min_interval = min_request_interval_ms / 1000
        self.max_per_minute = max_requests_per_minute
        
        self._lock = threading.Lock()
        self._last_request = 0
        self._request_times = []
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        with self._lock:
            now = time.time()
            
            # Enforce minimum interval between requests
            elapsed = now - self._last_request
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            
            # Enforce max requests per minute
            cutoff = now - 60
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            if len(self._request_times) >= self.max_per_minute:
                wait_until = self._request_times[0] + 60
                sleep_time = wait_until - now
                if sleep_time > 0:
                    logging.debug(f"Rate limited, waiting {sleep_time:.1f}s")
                    time.sleep(sleep_time)
            
            self._last_request = time.time()
            self._request_times.append(self._last_request)
    
    def get_sessions(self):
        """Get active sessions with rate limiting."""
        self._wait_for_rate_limit()
        return self._server.sessions()
    
    def get_ondeck(self):
        """Get OnDeck with rate limiting."""
        self._wait_for_rate_limit()
        return self._server.library.onDeck()
```

### Configurable Rate Limits
```python
class PlexApiSettings(BaseModel):
    """Plex API rate limiting settings."""
    
    # Minimum milliseconds between any Plex API call
    min_request_interval_ms: int = Field(
        default=1000, ge=100, le=10000,
        description="Minimum ms between Plex API calls"
    )
    
    # Maximum requests per minute to Plex
    max_requests_per_minute: int = Field(
        default=30, ge=5, le=120,
        description="Maximum Plex API requests per minute"
    )
    
    # Session check interval
    session_check_interval_seconds: int = Field(
        default=30, ge=10, le=300,
        description="Seconds between active session checks"
    )
    
    # OnDeck/Watchlist refresh interval
    library_refresh_interval_seconds: int = Field(
        default=300, ge=60, le=3600,
        description="Seconds between OnDeck/Watchlist refreshes"
    )
    
    # Connection timeout
    timeout_seconds: int = Field(
        default=30, ge=5, le=120,
        description="API request timeout"
    )
    
    # Retry settings
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_delay_seconds: int = Field(default=5, ge=1, le=60)
```

---

## Summary

The real-time WebGUI architecture provides:

1. **WebSocket Events** - Real-time updates for operations, sessions, logs
2. **Progress Tracking** - File copy progress with speed and ETA
3. **Fallback Polling** - Configurable polling as alternative
4. **Rate Limiting** - Protect Plex server from excessive API calls
5. **Configurable** - User can adjust refresh rates and intervals
