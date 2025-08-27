/**
 * Custom hooks for API operations
 * 
 * Provides reactive API calls with loading states, error handling,
 * and automatic retries. Integrates with the global state management.
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import APIService, { APIError } from '@/services/api'
import { useAppContext } from '@/store/AppContext'
import {
  SystemStatus,
  HealthStatus,
  LogsResponse,
  TestResults,
  ConfigurationSettings,
  RunOperationRequest,
  CachedFileInfo,
  CacheStatistics,
  UserCacheStatistics,
  CachedFilesFilter,
  CachedFilesResponse,
  CachedFileSearchResponse,
  CacheCleanupRequest,
  CacheCleanupResponse,
  RemoveCachedFileRequest,
} from '@/types/api'

// Generic API hook return type
interface APIHookResult<T> {
  data: T | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  lastFetched: Date | null
}

// Generic API hook with auto-refresh
interface UseAPIOptions {
  autoRefresh?: boolean
  refreshInterval?: number
  immediate?: boolean
  onSuccess?: (data: unknown) => void
  onError?: (error: APIError) => void
}

/**
 * Generic API hook
 */
function useAPI<T>(
  apiCall: () => Promise<T>,
  options: UseAPIOptions = {}
): APIHookResult<T> {
  const {
    autoRefresh = false,
    refreshInterval = 5000,
    immediate = true,
    onSuccess,
    onError,
  } = options

  const [data, setData] = useState<T | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastFetched, setLastFetched] = useState<Date | null>(null)
  
  const intervalRef = useRef<NodeJS.Timeout>()
  const mountedRef = useRef(true)

  const fetchData = useCallback(async () => {
    if (!mountedRef.current) return

    setIsLoading(true)
    setError(null)

    try {
      const result = await apiCall()
      
      if (!mountedRef.current) return

      setData(result)
      setLastFetched(new Date())
      
      if (onSuccess) {
        onSuccess(result)
      }

    } catch (err) {
      if (!mountedRef.current) return

      const apiError = err as APIError
      const errorMessage = apiError.message || 'An unexpected error occurred'
      
      setError(errorMessage)
      console.error('API call failed:', apiError)
      
      if (onError) {
        onError(apiError)
      }

    } finally {
      if (mountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [apiCall]) // Remove onSuccess and onError from dependencies to stabilize

  // Initial fetch
  useEffect(() => {
    if (immediate) {
      fetchData()
    }
  }, [immediate, fetchData])

  // Auto-refresh with stable timer
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      const intervalId = setInterval(() => {
        fetchData()
      }, refreshInterval)
      
      intervalRef.current = intervalId
      
      return () => {
        clearInterval(intervalId)
      }
    } else {
      // Clear interval if autoRefresh is disabled
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = undefined
      }
    }
  }, [autoRefresh, refreshInterval]) // Remove fetchData from dependencies

  // Cleanup
  useEffect(() => {
    return () => {
      mountedRef.current = false
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
    lastFetched,
  }
}

/**
 * Hook for system status with integration to global state
 */
export function useSystemStatus(options: Omit<UseAPIOptions, 'onSuccess'> = {}) {
  const { dispatch } = useAppContext()

  return useAPI(
    () => APIService.getSystemStatus(),
    {
      ...options,
      onSuccess: (data) => {
        dispatch({ type: 'SET_SYSTEM_STATUS', payload: data as SystemStatus })
      },
      onError: (error) => {
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'systemStatus', value: error.message }
        })
      },
    }
  )
}

/**
 * Hook for health status
 */
export function useHealthStatus(options: Omit<UseAPIOptions, 'onSuccess'> = {}) {
  const { dispatch } = useAppContext()

  return useAPI(
    () => APIService.getHealthStatus(),
    {
      ...options,
      onSuccess: (data) => {
        dispatch({ type: 'SET_HEALTH_STATUS', payload: data as HealthStatus })
      },
      onError: (error) => {
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'healthStatus', value: error.message }
        })
      },
    }
  )
}

/**
 * Hook for logs
 */
export function useLogs(options: Omit<UseAPIOptions, 'onSuccess'> = {}) {
  const { dispatch } = useAppContext()

  return useAPI(
    () => APIService.getLogs(),
    {
      ...options,
      onSuccess: (data) => {
        const logsData = data as LogsResponse
        dispatch({ type: 'SET_LOGS', payload: logsData.logs })
      },
      onError: (error) => {
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'logs', value: error.message }
        })
      },
    }
  )
}

/**
 * Hook for test results
 */
export function useTestResults(options: UseAPIOptions = {}) {
  const { dispatch } = useAppContext()

  return useAPI(
    () => APIService.getTestResults(),
    {
      ...options,
      immediate: false, // Don't fetch immediately, only when requested
      onSuccess: (data) => {
        dispatch({ type: 'SET_TEST_RESULTS', payload: data as TestResults })
      },
      onError: (error) => {
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'testResults', value: error.message }
        })
      },
    }
  )
}

/**
 * Hook for configuration settings
 */
export function useSettings(options: UseAPIOptions = {}) {
  return useAPI(() => APIService.getSettings(), options)
}

/**
 * Hook for operations (cache, test, etc.)
 */
export function useOperations() {
  const { dispatch } = useAppContext()
  const [isRunning, setIsRunning] = useState(false)

  const runCacheOperation = useCallback(async (request: RunOperationRequest = {}) => {
    setIsRunning(true)
    dispatch({ type: 'SET_LOADING', payload: { key: 'operations', value: true } })
    dispatch({ type: 'SET_ERROR', payload: { key: 'operations', value: null } })

    try {
      const result = await APIService.runCacheOperation(request)
      
      // Show success toast
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'success',
          message: result.message,
          duration: 5000,
        }
      })

      return result

    } catch (error) {
      const apiError = error as APIError
      const errorMessage = apiError.message || 'Operation failed'
      
      dispatch({
        type: 'SET_ERROR',
        payload: { key: 'operations', value: errorMessage }
      })
      
      // Show error toast
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'error',
          message: errorMessage,
          duration: 8000,
        }
      })

      throw error

    } finally {
      setIsRunning(false)
      dispatch({ type: 'SET_LOADING', payload: { key: 'operations', value: false } })
    }
  }, [dispatch])

  const startScheduler = useCallback(async () => {
    try {
      const result = await APIService.startScheduler()
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'success',
          message: result.message,
          duration: 5000,
        }
      })

      return result

    } catch (error) {
      const apiError = error as APIError
      const errorMessage = apiError.message || 'Failed to start scheduler'
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'error',
          message: errorMessage,
          duration: 8000,
        }
      })

      throw error
    }
  }, [dispatch])

  const stopScheduler = useCallback(async () => {
    try {
      const result = await APIService.stopScheduler()
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'success',
          message: result.message,
          duration: 5000,
        }
      })

      return result

    } catch (error) {
      const apiError = error as APIError
      const errorMessage = apiError.message || 'Failed to stop scheduler'
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'error',
          message: errorMessage,
          duration: 8000,
        }
      })

      throw error
    }
  }, [dispatch])

  return {
    isRunning,
    runCacheOperation,
    startScheduler,
    stopScheduler,
  }
}

/**
 * Hook for real-time data integration
 */
export function useRealTimeData() {
  const { state } = useAppContext()
  
  // Auto-refresh based on UI settings
  const systemStatusApi = useSystemStatus({
    autoRefresh: state.ui.autoRefresh,
    refreshInterval: state.ui.refreshInterval,
  })

  const healthStatusApi = useHealthStatus({
    autoRefresh: state.ui.autoRefresh,
    refreshInterval: state.ui.refreshInterval * 2, // Less frequent for health checks
  })

  const logsApi = useLogs({
    autoRefresh: state.ui.autoRefresh,
    refreshInterval: state.ui.refreshInterval * 3, // Even less frequent for logs
  })

  const refreshAll = useCallback(async () => {
    await Promise.all([
      systemStatusApi.refetch(),
      healthStatusApi.refetch(),
      logsApi.refetch(),
    ])
  }, [systemStatusApi, healthStatusApi, logsApi])

  return {
    systemStatus: systemStatusApi,
    healthStatus: healthStatusApi,
    logs: logsApi,
    refreshAll,
    isLoading: systemStatusApi.isLoading || healthStatusApi.isLoading || logsApi.isLoading,
  }
}

/**
 * Hook for cached files data with filtering and search
 */
export function useCachedFiles(filter: CachedFilesFilter = {}, options: UseAPIOptions = {}) {
  const { dispatch } = useAppContext()

  return useAPI(
    () => APIService.getCachedFiles(filter),
    {
      ...options,
      onError: (error) => {
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'cachedFiles', value: error.message }
        })
        if (options.onError) options.onError(error)
      },
    }
  )
}

/**
 * Hook for cache statistics
 */
export function useCacheStatistics(options: UseAPIOptions = {}) {
  const { dispatch } = useAppContext()

  return useAPI(
    () => APIService.getCacheStatistics(),
    {
      ...options,
      onError: (error) => {
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'cacheStatistics', value: error.message }
        })
        if (options.onError) options.onError(error)
      },
    }
  )
}

/**
 * Hook for user-specific cache statistics
 */
export function useUserCacheStatistics(userId: string, days: number = 30, options: UseAPIOptions = {}) {
  const { dispatch } = useAppContext()

  return useAPI(
    () => APIService.getUserCacheStatistics(userId, days),
    {
      ...options,
      immediate: options.immediate !== false && !!userId, // Don't fetch if no userId
      onError: (error) => {
        dispatch({
          type: 'SET_ERROR',
          payload: { key: 'userCacheStats', value: error.message }
        })
        if (options.onError) options.onError(error)
      },
    }
  )
}

/**
 * Hook for cached files operations (remove, cleanup, search)
 */
export function useCachedFilesOperations() {
  const { dispatch } = useAppContext()
  const [isLoading, setIsLoading] = useState(false)

  const removeCachedFile = useCallback(async (fileId: string, request: RemoveCachedFileRequest) => {
    setIsLoading(true)
    dispatch({ type: 'SET_ERROR', payload: { key: 'cachedFilesOperations', value: null } })

    try {
      const result = await APIService.removeCachedFile(fileId, request)
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'success',
          message: `Successfully removed cached file: ${result.file_path}`,
          duration: 5000,
        }
      })

      return result

    } catch (error) {
      const apiError = error as APIError
      const errorMessage = apiError.message || 'Failed to remove cached file'
      
      dispatch({
        type: 'SET_ERROR',
        payload: { key: 'cachedFilesOperations', value: errorMessage }
      })
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'error',
          message: errorMessage,
          duration: 8000,
        }
      })

      throw error

    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  const cleanupCache = useCallback(async (request: CacheCleanupRequest = {}) => {
    setIsLoading(true)
    dispatch({ type: 'SET_ERROR', payload: { key: 'cachedFilesOperations', value: null } })

    try {
      const result = await APIService.cleanupCache(request)
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'success',
          message: `Cache cleanup completed. ${result.orphaned_count} files marked as orphaned${result.removed_count > 0 ? `, ${result.removed_count} files removed` : ''}`,
          duration: 5000,
        }
      })

      return result

    } catch (error) {
      const apiError = error as APIError
      const errorMessage = apiError.message || 'Failed to cleanup cache'
      
      dispatch({
        type: 'SET_ERROR',
        payload: { key: 'cachedFilesOperations', value: errorMessage }
      })
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'error',
          message: errorMessage,
          duration: 8000,
        }
      })

      throw error

    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  const searchCachedFiles = useCallback(async (
    query: string, 
    searchType: string = 'all', 
    limit: number = 50,
    includeRemoved: boolean = false
  ) => {
    setIsLoading(true)
    dispatch({ type: 'SET_ERROR', payload: { key: 'cachedFilesOperations', value: null } })

    try {
      const result = await APIService.searchCachedFiles(query, searchType, limit, includeRemoved)
      return result

    } catch (error) {
      const apiError = error as APIError
      const errorMessage = apiError.message || 'Search failed'
      
      dispatch({
        type: 'SET_ERROR',
        payload: { key: 'cachedFilesOperations', value: errorMessage }
      })

      throw error

    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  const exportCachedFiles = useCallback(async (
    format: 'csv' | 'json' | 'txt' = 'csv',
    filter: Partial<CachedFilesFilter> = {},
    includeMetadata: boolean = false
  ) => {
    setIsLoading(true)
    dispatch({ type: 'SET_ERROR', payload: { key: 'cachedFilesOperations', value: null } })

    try {
      const blob = await APIService.exportCachedFiles(format, filter, includeMetadata)
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `cached-files-${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'success',
          message: `Export completed successfully (${format.toUpperCase()})`,
          duration: 5000,
        }
      })

    } catch (error) {
      const apiError = error as APIError
      const errorMessage = apiError.message || 'Export failed'
      
      dispatch({
        type: 'SET_ERROR',
        payload: { key: 'cachedFilesOperations', value: errorMessage }
      })
      
      dispatch({
        type: 'ADD_TOAST',
        payload: {
          type: 'error',
          message: errorMessage,
          duration: 8000,
        }
      })

      throw error

    } finally {
      setIsLoading(false)
    }
  }, [dispatch])

  return {
    isLoading,
    removeCachedFile,
    cleanupCache,
    searchCachedFiles,
    exportCachedFiles,
  }
}

/**
 * Hook for real-time cached files data with auto-refresh
 */
export function useCachedFilesRealTime(filter: CachedFilesFilter = {}) {
  const { state } = useAppContext()
  
  const cachedFilesApi = useCachedFiles(filter, {
    autoRefresh: state.ui.autoRefresh,
    refreshInterval: state.ui.refreshInterval * 2, // Less frequent than main dashboard
  })

  const cacheStatsApi = useCacheStatistics({
    autoRefresh: state.ui.autoRefresh,
    refreshInterval: state.ui.refreshInterval * 3, // Even less frequent for stats
  })

  const refreshAll = useCallback(async () => {
    await Promise.all([
      cachedFilesApi.refetch(),
      cacheStatsApi.refetch(),
    ])
  }, [cachedFilesApi, cacheStatsApi])

  return {
    cachedFiles: cachedFilesApi,
    cacheStatistics: cacheStatsApi,
    refreshAll,
    isLoading: cachedFilesApi.isLoading || cacheStatsApi.isLoading,
  }
}

export { useAPI }
export default useAPI