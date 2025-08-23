/**
 * WebSocket service for real-time updates
 * 
 * Provides real-time communication with the backend for:
 * - System status updates
 * - Log streaming
 * - Operation progress
 * - Error notifications
 */

import {
  WebSocketMessage,
  StatusUpdateMessage,
  LogUpdateMessage,
  OperationProgressMessage,
  ErrorMessage,
} from '@/types/api'

export type WebSocketEventType = 'status_update' | 'log_entry' | 'operation_progress' | 'error'

export interface WebSocketEventHandler {
  (data: unknown): void
}

export interface WebSocketConnectionStatus {
  connected: boolean
  reconnecting: boolean
  lastConnectedAt: Date | null
  reconnectAttempts: number
  maxReconnectAttempts: number
}

/**
 * WebSocket service class
 */
export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectTimer: NodeJS.Timeout | null = null
  private pingTimer: NodeJS.Timeout | null = null
  private eventHandlers: Map<WebSocketEventType, Set<WebSocketEventHandler>> = new Map()
  private connectionHandlers: Set<(status: WebSocketConnectionStatus) => void> = new Set()
  
  private status: WebSocketConnectionStatus = {
    connected: false,
    reconnecting: false,
    lastConnectedAt: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 10,
  }

  // Configuration
  private readonly reconnectDelay = 1000 // Start with 1 second
  private readonly maxReconnectDelay = 30000 // Max 30 seconds
  private readonly pingInterval = 30000 // Ping every 30 seconds
  private readonly pongTimeout = 10000 // Wait 10 seconds for pong

  constructor(url?: string) {
    this.url = url || this.buildWebSocketURL()
    
    // Initialize event handler maps
    const eventTypes: WebSocketEventType[] = ['status_update', 'log_entry', 'operation_progress', 'error']
    eventTypes.forEach(type => {
      this.eventHandlers.set(type, new Set())
    })
  }

  /**
   * Build WebSocket URL from current location
   */
  private buildWebSocketURL(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    
    // In development, use the proxy configured in Vite
    if (import.meta.env.DEV) {
      return `${protocol}//${host}/ws`
    }
    
    // In production, assume WebSocket is on the same host
    return `${protocol}//${host}/ws`
  }

  /**
   * Connect to WebSocket
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return // Already connected
    }

    if (this.ws?.readyState === WebSocket.CONNECTING) {
      return // Connection in progress
    }

    try {
      console.log('Connecting to WebSocket:', this.url)
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = this.handleOpen.bind(this)
      this.ws.onmessage = this.handleMessage.bind(this)
      this.ws.onclose = this.handleClose.bind(this)
      this.ws.onerror = this.handleError.bind(this)

    } catch (error) {
      console.error('WebSocket connection failed:', error)
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.clearTimers()
    
    if (this.ws) {
      this.ws.onopen = null
      this.ws.onmessage = null
      this.ws.onclose = null
      this.ws.onerror = null
      
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(1000, 'Client disconnect')
      }
      
      this.ws = null
    }

    this.updateStatus({ connected: false, reconnecting: false })
  }

  /**
   * Send message to WebSocket
   */
  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected, cannot send message:', data)
    }
  }

  /**
   * Add event listener
   */
  addEventListener(type: WebSocketEventType, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(type)
    if (handlers) {
      handlers.add(handler)
    }
  }

  /**
   * Remove event listener
   */
  removeEventListener(type: WebSocketEventType, handler: WebSocketEventHandler): void {
    const handlers = this.eventHandlers.get(type)
    if (handlers) {
      handlers.delete(handler)
    }
  }

  /**
   * Add connection status listener
   */
  addConnectionListener(handler: (status: WebSocketConnectionStatus) => void): void {
    this.connectionHandlers.add(handler)
    // Immediately call with current status
    handler(this.status)
  }

  /**
   * Remove connection status listener
   */
  removeConnectionListener(handler: (status: WebSocketConnectionStatus) => void): void {
    this.connectionHandlers.delete(handler)
  }

  /**
   * Get current connection status
   */
  getStatus(): WebSocketConnectionStatus {
    return { ...this.status }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log('WebSocket connected')
    this.updateStatus({
      connected: true,
      reconnecting: false,
      lastConnectedAt: new Date(),
      reconnectAttempts: 0,
    })
    
    this.startPing()
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      // Ignore pong messages
      if (message.type === 'pong') {
        return
      }
      
      // Dispatch to appropriate handlers
      const handlers = this.eventHandlers.get(message.type as WebSocketEventType)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message.data)
          } catch (error) {
            console.error(`Error in WebSocket event handler for ${message.type}:`, error)
          }
        })
      } else {
        console.warn('No handlers for WebSocket message type:', message.type)
      }

    } catch (error) {
      console.error('Error parsing WebSocket message:', event.data, error)
    }
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket closed:', event.code, event.reason)
    this.clearTimers()
    this.updateStatus({ connected: false })
    
    // Don't reconnect if it was a normal closure
    if (event.code !== 1000) {
      this.scheduleReconnect()
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(error: Event): void {
    console.error('WebSocket error:', error)
    this.clearTimers()
    this.scheduleReconnect()
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.status.reconnectAttempts >= this.status.maxReconnectAttempts) {
      console.error('Max WebSocket reconnection attempts reached')
      this.updateStatus({ reconnecting: false })
      return
    }

    if (this.reconnectTimer) {
      return // Already scheduled
    }

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.status.reconnectAttempts),
      this.maxReconnectDelay
    )

    console.log(`Scheduling WebSocket reconnection in ${delay}ms (attempt ${this.status.reconnectAttempts + 1})`)
    
    this.updateStatus({ reconnecting: true })
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.status.reconnectAttempts++
      this.connect()
    }, delay)
  }

  /**
   * Update connection status and notify listeners
   */
  private updateStatus(updates: Partial<WebSocketConnectionStatus>): void {
    this.status = { ...this.status, ...updates }
    
    this.connectionHandlers.forEach(handler => {
      try {
        handler(this.status)
      } catch (error) {
        console.error('Error in WebSocket connection handler:', error)
      }
    })
  }

  /**
   * Start ping timer
   */
  private startPing(): void {
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' })
      }
    }, this.pingInterval)
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }
}

// Create singleton instance
const webSocketService = new WebSocketService()

// Convenience functions for typed event handling
export const useWebSocketStatus = (handler: (status: WebSocketConnectionStatus) => void): void => {
  webSocketService.addConnectionListener(handler)
}

export const useWebSocketStatusUpdates = (handler: (data: StatusUpdateMessage['data']) => void): void => {
  webSocketService.addEventListener('status_update', handler)
}

export const useWebSocketLogs = (handler: (data: LogUpdateMessage['data']) => void): void => {
  webSocketService.addEventListener('log_entry', handler)
}

export const useWebSocketProgress = (handler: (data: OperationProgressMessage['data']) => void): void => {
  webSocketService.addEventListener('operation_progress', handler)
}

export const useWebSocketErrors = (handler: (data: ErrorMessage['data']) => void): void => {
  webSocketService.addEventListener('error', handler)
}

export default webSocketService