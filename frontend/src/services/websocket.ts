/**
 * Socket.IO service for real-time updates
 * 
 * Provides real-time communication with the backend for:
 * - System status updates
 * - Log streaming
 * - Operation progress
 * - Error notifications
 * - Cache file updates
 * - Statistics updates
 */

import { io, Socket, SocketOptions } from 'socket.io-client'
import {
  WebSocketMessage,
  OperationProgressMessage,
  FileOperationUpdateMessage,
} from './types/api'

export type WebSocketEventType =
  | 'operation_progress'
  | 'operation_file_update'

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
 * Socket.IO service class
 */
export class WebSocketService {
  private socket: Socket | null = null
  private url: string
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

  constructor(url?: string) {
    this.url = url || this.buildWebSocketURL()
    
    // Initialize event handler maps
    const eventTypes: WebSocketEventType[] = [
      'operation_progress',
      'operation_file_update'
    ]
    eventTypes.forEach(type => {
      this.eventHandlers.set(type, new Set())
    })
  }

  /**
   * Build WebSocket URL from current location
   */
  private buildWebSocketURL(): string {
    // Use the same host as the current page, but with Socket.IO protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = window.location.port || (protocol === 'wss:' ? '443' : '80')
    
    // For development, use the backend port directly
    if (process.env.NODE_ENV === 'development') {
      return `http://${host}:5445`
    }
    
    return `${protocol}//${host}:${port}`
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.socket?.connected) {
      console.log('Already connected to WebSocket server')
      return
    }

    console.log('Connecting to WebSocket server:', this.url)

    try {
      // Socket.IO configuration
      const options: SocketOptions = {}

      // Create Socket.IO connection
      this.socket = io(this.url, options)

      // Set up event listeners
      this._setupSocketEventListeners()

      // Connect to the server
      this.socket.connect()

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.updateStatus({ connected: false, reconnecting: false })
    }
  }

  /**
   * Set up Socket.IO event listeners
   */
  private _setupSocketEventListeners(): void {
    if (!this.socket) return

    // Connection events
    this.socket.on('connect', () => {
      console.log('Connected to WebSocket server')
      this.updateStatus({
        connected: true,
        reconnecting: false,
        lastConnectedAt: new Date(),
        reconnectAttempts: 0,
      })
      
      // Start ping interval
      this.startPing()
      
      // WebSocket connected successfully
      console.log('WebSocket connected and ready')
    })

    this.socket.on('disconnect', (reason: string) => {
      console.log('Disconnected from WebSocket server:', reason)
      this.updateStatus({ connected: false })
      
      // WebSocket disconnected
      console.log('WebSocket disconnected:', reason)
      
      // Clear ping timer
      this.clearTimers()
    })

    this.socket.on('connect_error', (error: Error) => {
      console.error('WebSocket connection error:', error)
      this.updateStatus({ connected: false, reconnecting: true })
    })

    this.socket.on('reconnect', (attemptNumber: number) => {
      console.log(`Reconnected to WebSocket server (attempt ${attemptNumber})`)
      this.updateStatus({
        connected: true,
        reconnecting: false,
        lastConnectedAt: new Date(),
        reconnectAttempts: attemptNumber,
      })
    })

    this.socket.on('reconnect_error', (error: Error) => {
      console.error('WebSocket reconnection error:', error)
      this.updateStatus({ reconnecting: true })
    })

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed')
      this.updateStatus({ reconnecting: false })
    })

    // Application-specific events
    this.socket.on('operation_progress', (data: OperationProgressMessage['data']) => {
      this._emitEvent('operation_progress', data)
    })

    this.socket.on('operation_file_update', (data: FileOperationUpdateMessage['data']) => {
      this._emitEvent('operation_file_update', data)
    })
  }

  /**
   * Emit event to registered handlers
   */
  private _emitEvent(type: WebSocketEventType, data: unknown): void {
    const handlers = this.eventHandlers.get(type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${type}:`, error)
        }
      })
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.clearTimers()
    
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }

    this.updateStatus({ connected: false, reconnecting: false })
  }

  /**
   * Send message to WebSocket server
   */
  send(data: unknown): void {
    if (this.socket?.connected) {
      this.socket.emit('message', data)
    } else {
      console.warn('WebSocket not connected, cannot send message:', data)
    }
  }

  /**
   * Join a room for targeted messaging
   */
  joinRoom(room: string): void {
    if (this.socket?.connected) {
      this.socket.emit('join', { room })
    } else {
      console.warn('WebSocket not connected, cannot join room:', room)
    }
  }

  /**
   * Leave a room
   */
  leaveRoom(room: string): void {
    if (this.socket?.connected) {
      this.socket.emit('leave', { room })
    } else {
      console.warn('WebSocket not connected, cannot leave room:', room)
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
   * Check if currently connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false
  }

  /**
   * Start ping timer
   */
  private startPing(): void {
    this.clearTimers()
    
    // Send ping every 30 seconds to keep connection alive
    this.pingTimer = setInterval(() => {
      if (this.socket?.connected) {
        this.socket.emit('ping')
      }
    }, this.pingInterval)
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
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

  // Private properties
  private pingTimer: NodeJS.Timeout | null = null
}

// Create singleton instance
const webSocketService = new WebSocketService()

// Convenience functions for typed event handling
export const useWebSocketProgress = (handler: (data: OperationProgressMessage['data']) => void): void => {
  webSocketService.addEventListener('operation_progress', handler)
}

export const useWebSocketFileUpdates = (handler: (data: FileOperationUpdateMessage['data']) => void): void => {
  webSocketService.addEventListener('operation_file_update', handler)
}

export default webSocketService