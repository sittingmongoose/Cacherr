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
  }, [apiCall, onSuccess, onError])

  // Initial fetch
  useEffect(() => {
    if (immediate) {
      fetchData()
    }
  }, [immediate, fetchData])

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval)
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
        }
      }
    }
  }, [autoRefresh, refreshInterval, fetchData])

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

export default useAPI