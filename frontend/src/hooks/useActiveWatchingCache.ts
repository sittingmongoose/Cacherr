/**
 * Active Watching Cache Hook
 * 
 * Specialized hook for monitoring active Plex watching cache operations.
 * Handles real-time updates for files being cached while actively watched.
 */

import { useState, useEffect, useCallback, useRef } from 'react'

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