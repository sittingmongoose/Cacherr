/**
 * Active Watching Cache Hook
 * 
 * Specialized hook for monitoring active Plex watching cache operations.
 * Handles real-time updates for files being cached while actively watched.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { CachedFileInfo, CacheUpdateMessage } from '@/types/api'
import webSocketService from '@/services/websocket'

export interface ActiveWatchingEvent {
  timestamp: Date
  file_path: string
  filename: string
  user_id?: string
  action: 'started' | 'completed' | 'failed'
  cache_method: 'atomic_copy'
  file_size_readable: string
  reason: string
  error?: string
}

export interface ActiveWatchingStats {
  total_active_operations: number
  completed_today: number
  failed_today: number
  total_size_cached_today: number
  total_size_cached_today_readable: string
  most_active_user?: string
  current_operations: ActiveWatchingEvent[]
}

/**
 * Hook for monitoring active watching cache operations
 */
export function useActiveWatchingCache() {
  const [recentEvents, setRecentEvents] = useState<ActiveWatchingEvent[]>([])
  const [stats, setStats] = useState<ActiveWatchingStats>({
    total_active_operations: 0,
    completed_today: 0,
    failed_today: 0,
    total_size_cached_today: 0,
    total_size_cached_today_readable: '0 B',
    current_operations: []
  })
  const [isConnected, setIsConnected] = useState(false)
  const mountedRef = useRef(true)

  // Handle cache file added events (active watching)
  const handleCacheFileAdded = useCallback((message: CacheUpdateMessage) => {
    if (!mountedRef.current) return

    const { data } = message
    
    // Only handle active watching operations
    if (data.reason !== 'active_watching' && data.reason !== 'real_time_watch') {
      return
    }

    const event: ActiveWatchingEvent = {
      timestamp: new Date(),
      file_path: data.file_path,
      filename: data.file_path.split('/').pop() || 'Unknown',
      user_id: data.user_id,
      action: 'completed',
      cache_method: 'atomic_copy',
      file_size_readable: data.file_info?.file_size_readable || '0 B',
      reason: data.reason
    }

    setRecentEvents(prev => [event, ...prev.slice(0, 49)]) // Keep last 50 events

    // Update stats
    setStats(prev => {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      
      const todayEvents = [...prev.current_operations].filter(
        e => e.timestamp >= today
      )

      const totalSizeBytes = todayEvents.reduce((sum, e) => {
        // Simple parsing of readable size to bytes (approximate)
        const sizeStr = e.file_size_readable
        const size = parseFloat(sizeStr)
        if (sizeStr.includes('GB')) return sum + (size * 1024 * 1024 * 1024)
        if (sizeStr.includes('MB')) return sum + (size * 1024 * 1024)
        if (sizeStr.includes('KB')) return sum + (size * 1024)
        return sum + size
      }, 0)

      return {
        ...prev,
        completed_today: prev.completed_today + 1,
        total_size_cached_today: totalSizeBytes,
        total_size_cached_today_readable: formatBytes(totalSizeBytes),
        current_operations: [event, ...prev.current_operations.slice(0, 99)]
      }
    })
  }, [])

  // Handle cache file removal events
  const handleCacheFileRemoved = useCallback((message: CacheUpdateMessage) => {
    if (!mountedRef.current) return

    const { data } = message
    
    // Only handle active watching operations
    if (data.reason !== 'active_watching' && data.reason !== 'real_time_watch') {
      return
    }

    const event: ActiveWatchingEvent = {
      timestamp: new Date(),
      file_path: data.file_path,
      filename: data.file_path.split('/').pop() || 'Unknown',
      user_id: data.user_id,
      action: 'failed',
      cache_method: 'atomic_copy',
      file_size_readable: '0 B',
      reason: data.reason,
      error: 'Cache operation removed/failed'
    }

    setRecentEvents(prev => [event, ...prev.slice(0, 49)])

    setStats(prev => ({
      ...prev,
      failed_today: prev.failed_today + 1,
      current_operations: [event, ...prev.current_operations.slice(0, 99)]
    }))
  }, [])

  // WebSocket connection status
  const handleConnectionStatus = useCallback(() => {
    setIsConnected(webSocketService.isConnected())
  }, [])

  // Setup WebSocket listeners
  useEffect(() => {
    webSocketService.addEventListener('cache_file_added', handleCacheFileAdded)
    webSocketService.addEventListener('cache_file_removed', handleCacheFileRemoved)
    webSocketService.addEventListener('connected', handleConnectionStatus)
    webSocketService.addEventListener('disconnected', handleConnectionStatus)

    // Initial connection status
    setIsConnected(webSocketService.isConnected())

    return () => {
      webSocketService.removeEventListener('cache_file_added', handleCacheFileAdded)
      webSocketService.removeEventListener('cache_file_removed', handleCacheFileRemoved)
      webSocketService.removeEventListener('connected', handleConnectionStatus)
      webSocketService.removeEventListener('disconnected', handleConnectionStatus)
    }
  }, [handleCacheFileAdded, handleCacheFileRemoved, handleConnectionStatus])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false
    }
  }, [])

  // Clear old events periodically
  useEffect(() => {
    const cleanup = setInterval(() => {
      const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000) // 24 hours ago
      
      setRecentEvents(prev => prev.filter(event => event.timestamp > cutoff))
      setStats(prev => ({
        ...prev,
        current_operations: prev.current_operations.filter(event => event.timestamp > cutoff)
      }))
    }, 60 * 60 * 1000) // Every hour

    return () => clearInterval(cleanup)
  }, [])

  // Get events for a specific user
  const getUserEvents = useCallback((userId: string) => {
    return recentEvents.filter(event => event.user_id === userId)
  }, [recentEvents])

  // Get events for a specific file
  const getFileEvents = useCallback((filePath: string) => {
    return recentEvents.filter(event => event.file_path === filePath)
  }, [recentEvents])

  // Clear all events
  const clearEvents = useCallback(() => {
    setRecentEvents([])
    setStats(prev => ({
      ...prev,
      current_operations: []
    }))
  }, [])

  return {
    recentEvents,
    stats,
    isConnected,
    getUserEvents,
    getFileEvents,
    clearEvents
  }
}

/**
 * Format bytes to human readable string
 */
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default useActiveWatchingCache