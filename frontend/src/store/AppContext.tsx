import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react'
import { SystemStatus, HealthStatus, LogEntry, TestResults, UIState, ToastOptions } from '../types/api'
import webSocketService, { WebSocketConnectionStatus } from '../services/websocket'

/**
 * Application-wide state management using React Context API
 * 
 * Features:
 * - Centralized state management
 * - Type-safe state updates
 * - Real-time data synchronization
 * - Toast notifications
 * - Theme management
 * - Error handling
 */

// State interfaces
export interface AppState {
  // System data
  systemStatus: SystemStatus | null
  healthStatus: HealthStatus | null
  logs: LogEntry[]
  testResults: TestResults | null
  
  // UI state
  ui: UIState
  
  // Loading states
  loading: {
    systemStatus: boolean
    healthStatus: boolean
    logs: boolean
    testResults: boolean
    operations: boolean
    cachedFiles: boolean
    cacheStatistics: boolean
    userCacheStats: boolean
    cachedFilesOperations: boolean
  }
  
  // Error states
  errors: {
    systemStatus: string | null
    healthStatus: string | null
    logs: string | null
    testResults: string | null
    operations: string | null
    cachedFiles: string | null
    cacheStatistics: string | null
    userCacheStats: string | null
    cachedFilesOperations: string | null
  }
  
  // Toast notifications
  toasts: ToastOptions[]
  
  // WebSocket connection
  websocket: {
    connected: boolean
    reconnecting: boolean
    lastConnectedAt: Date | null
  }
}

// Action types
export type AppAction =
  // System data actions
  | { type: 'SET_SYSTEM_STATUS'; payload: SystemStatus }
  | { type: 'SET_HEALTH_STATUS'; payload: HealthStatus }
  | { type: 'SET_LOGS'; payload: LogEntry[] }
  | { type: 'ADD_LOG'; payload: LogEntry }
  | { type: 'SET_TEST_RESULTS'; payload: TestResults }
  | { type: 'CLEAR_TEST_RESULTS' }
  
  // Loading actions
  | { type: 'SET_LOADING'; payload: { key: keyof AppState['loading']; value: boolean } }
  
  // Error actions
  | { type: 'SET_ERROR'; payload: { key: keyof AppState['errors']; value: string | null } }
  | { type: 'CLEAR_ERRORS' }
  
  // UI actions
  | { type: 'SET_THEME'; payload: UIState['theme'] }
  | { type: 'SET_SIDEBAR_COLLAPSED'; payload: boolean }
  | { type: 'SET_REFRESH_INTERVAL'; payload: number }
  | { type: 'SET_AUTO_REFRESH'; payload: boolean }
  | { type: 'SET_NOTIFICATIONS'; payload: boolean }
  
  // Toast actions
  | { type: 'ADD_TOAST'; payload: ToastOptions }
  | { type: 'REMOVE_TOAST'; payload: string }
  | { type: 'CLEAR_TOASTS' }
  
  // WebSocket actions
  | { type: 'SET_WEBSOCKET_CONNECTED'; payload: boolean }
  | { type: 'SET_WEBSOCKET_RECONNECTING'; payload: boolean }
  | { type: 'SET_WEBSOCKET_LAST_CONNECTED'; payload: Date }

// Initial state
const initialState: AppState = {
  systemStatus: null,
  healthStatus: null,
  logs: [],
  testResults: null,
  
  ui: {
    theme: 'auto',
    sidebarCollapsed: false,
    refreshInterval: 60000, // 1 minute instead of 5 seconds
    autoRefresh: true, // Keep enabled for initial data loading
    notifications: true,
  },
  
  loading: {
    systemStatus: false,
    healthStatus: false,
    logs: false,
    testResults: false,
    operations: false,
    cachedFiles: false,
    cacheStatistics: false,
    userCacheStats: false,
    cachedFilesOperations: false,
  },
  
  errors: {
    systemStatus: null,
    healthStatus: null,
    logs: null,
    testResults: null,
    operations: null,
    cachedFiles: null,
    cacheStatistics: null,
    userCacheStats: null,
    cachedFilesOperations: null,
  },
  
  toasts: [],
  
  websocket: {
    connected: false,
    reconnecting: false,
    lastConnectedAt: null,
  },
}

// Load persisted UI state from localStorage
const loadPersistedUIState = (): Partial<UIState> => {
  try {
    const stored = localStorage.getItem('cacherr-ui-state')
    return stored ? JSON.parse(stored) : {}
  } catch {
    return {}
  }
}

// Save UI state to localStorage
const saveUIState = (uiState: UIState) => {
  try {
    localStorage.setItem('cacherr-ui-state', JSON.stringify(uiState))
  } catch {
    // Ignore storage errors
  }
}

// Reducer function
const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    // System data
    case 'SET_SYSTEM_STATUS':
      return {
        ...state,
        systemStatus: action.payload,
        errors: { ...state.errors, systemStatus: null },
      }
    
    case 'SET_HEALTH_STATUS':
      return {
        ...state,
        healthStatus: action.payload,
        errors: { ...state.errors, healthStatus: null },
      }
    
    case 'SET_LOGS':
      return {
        ...state,
        logs: action.payload,
        errors: { ...state.errors, logs: null },
      }
    
    case 'ADD_LOG':
      return {
        ...state,
        logs: [action.payload, ...state.logs].slice(0, 1000), // Keep last 1000 logs
      }
    
    case 'SET_TEST_RESULTS':
      return {
        ...state,
        testResults: action.payload,
        errors: { ...state.errors, testResults: null },
      }
    
    case 'CLEAR_TEST_RESULTS':
      return {
        ...state,
        testResults: null,
      }
    
    // Loading states
    case 'SET_LOADING':
      return {
        ...state,
        loading: {
          ...state.loading,
          [action.payload.key]: action.payload.value,
        },
      }
    
    // Error states
    case 'SET_ERROR':
      return {
        ...state,
        errors: {
          ...state.errors,
          [action.payload.key]: action.payload.value,
        },
        loading: {
          ...state.loading,
          [action.payload.key]: false,
        },
      }
    
    case 'CLEAR_ERRORS':
      return {
        ...state,
        errors: {
          systemStatus: null,
          healthStatus: null,
          logs: null,
          testResults: null,
          operations: null,
          cachedFiles: null,
          cacheStatistics: null,
          userCacheStats: null,
          cachedFilesOperations: null,
        },
      }
    
    // UI actions
    case 'SET_THEME':
      const newUIState = { ...state.ui, theme: action.payload }
      saveUIState(newUIState)
      return {
        ...state,
        ui: newUIState,
      }
    
    case 'SET_SIDEBAR_COLLAPSED':
      const updatedUIState = { ...state.ui, sidebarCollapsed: action.payload }
      saveUIState(updatedUIState)
      return {
        ...state,
        ui: updatedUIState,
      }
    
    case 'SET_REFRESH_INTERVAL':
      const refreshUIState = { ...state.ui, refreshInterval: action.payload }
      saveUIState(refreshUIState)
      return {
        ...state,
        ui: refreshUIState,
      }
    
    case 'SET_AUTO_REFRESH':
      const autoRefreshUIState = { ...state.ui, autoRefresh: action.payload }
      saveUIState(autoRefreshUIState)
      return {
        ...state,
        ui: autoRefreshUIState,
      }
    
    case 'SET_NOTIFICATIONS':
      const notificationsUIState = { ...state.ui, notifications: action.payload }
      saveUIState(notificationsUIState)
      return {
        ...state,
        ui: notificationsUIState,
      }
    
    // Toast actions
    case 'ADD_TOAST':
      const toast = {
        ...action.payload,
        id: action.payload.id || Date.now().toString(),
      }
      return {
        ...state,
        toasts: [...state.toasts, toast],
      }
    
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter(toast => toast.id !== action.payload),
      }
    
    case 'CLEAR_TOASTS':
      return {
        ...state,
        toasts: [],
      }
    
    // WebSocket actions
    case 'SET_WEBSOCKET_CONNECTED':
      return {
        ...state,
        websocket: {
          ...state.websocket,
          connected: action.payload,
          reconnecting: false,
          lastConnectedAt: action.payload ? new Date() : state.websocket.lastConnectedAt,
        },
      }
    
    case 'SET_WEBSOCKET_RECONNECTING':
      return {
        ...state,
        websocket: {
          ...state.websocket,
          reconnecting: action.payload,
        },
      }
    
    case 'SET_WEBSOCKET_LAST_CONNECTED':
      return {
        ...state,
        websocket: {
          ...state.websocket,
          lastConnectedAt: action.payload,
        },
      }
    
    default:
      return state
  }
}

// Context creation
const AppContext = createContext<{
  state: AppState
  dispatch: React.Dispatch<AppAction>
} | null>(null)

// Provider component
export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, {
    ...initialState,
    ui: { ...initialState.ui, ...loadPersistedUIState() },
  })

  // Apply theme to document
  useEffect(() => {
    const root = window.document.documentElement
    
    if (state.ui.theme === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      root.classList.toggle('dark', mediaQuery.matches)
      
      const handler = (e: MediaQueryListEvent) => {
        root.classList.toggle('dark', e.matches)
      }
      
      mediaQuery.addEventListener('change', handler)
      return () => mediaQuery.removeEventListener('change', handler)
    } else {
      root.classList.toggle('dark', state.ui.theme === 'dark')
    }
  }, [state.ui.theme])

  // Auto-remove toasts
  useEffect(() => {
    state.toasts.forEach(toast => {
      if (!toast.persistent && toast.duration !== 0) {
        const timeout = setTimeout(() => {
          dispatch({ type: 'REMOVE_TOAST', payload: toast.id! })
        }, toast.duration || 5000)
        
        return () => clearTimeout(timeout)
      }
    })
  }, [state.toasts])

  // WebSocket event handling
  useEffect(() => {
    // Connection status handler
    const handleConnectionStatus = (status: WebSocketConnectionStatus) => {
      dispatch({ type: 'SET_WEBSOCKET_CONNECTED', payload: status.connected })
      dispatch({ type: 'SET_WEBSOCKET_RECONNECTING', payload: status.reconnecting })
      if (status.lastConnectedAt) {
        dispatch({ type: 'SET_WEBSOCKET_LAST_CONNECTED', payload: status.lastConnectedAt })
      }
    }

    // Register event handlers
    webSocketService.addConnectionListener(handleConnectionStatus)

    // Connect to WebSocket once at app level
    if (!webSocketService.isConnected()) {
      console.log('AppProvider: Initializing WebSocket connection...')
      webSocketService.connect()
    }

    // Cleanup
    return () => {
      webSocketService.removeConnectionListener(handleConnectionStatus)
      console.log('AppProvider: Cleaning up WebSocket connection...')
      webSocketService.disconnect()
    }
  }, [dispatch])

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

// Hook for accessing context
export const useAppContext = () => {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider')
  }
  return context
}

// Convenience hooks for specific state slices
export const useSystemStatus = () => {
  const { state } = useAppContext()
  return {
    systemStatus: state.systemStatus,
    isLoading: state.loading.systemStatus,
    error: state.errors.systemStatus,
  }
}

export const useHealthStatus = () => {
  const { state } = useAppContext()
  return {
    healthStatus: state.healthStatus,
    isLoading: state.loading.healthStatus,
    error: state.errors.healthStatus,
  }
}

export const useLogs = () => {
  const { state } = useAppContext()
  return {
    logs: state.logs,
    isLoading: state.loading.logs,
    error: state.errors.logs,
  }
}

export const useTestResults = () => {
  const { state } = useAppContext()
  return {
    testResults: state.testResults,
    isLoading: state.loading.testResults,
    error: state.errors.testResults,
  }
}

export const useUIState = () => {
  const { state, dispatch } = useAppContext()
  return {
    ui: state.ui,
    setTheme: (theme: UIState['theme']) => dispatch({ type: 'SET_THEME', payload: theme }),
    setSidebarCollapsed: (collapsed: boolean) => dispatch({ type: 'SET_SIDEBAR_COLLAPSED', payload: collapsed }),
    setRefreshInterval: (interval: number) => dispatch({ type: 'SET_REFRESH_INTERVAL', payload: interval }),
    setAutoRefresh: (enabled: boolean) => dispatch({ type: 'SET_AUTO_REFRESH', payload: enabled }),
    setNotifications: (enabled: boolean) => dispatch({ type: 'SET_NOTIFICATIONS', payload: enabled }),
  }
}

export const useToasts = () => {
  const { state, dispatch } = useAppContext()
  return {
    toasts: state.toasts,
    addToast: (toast: Omit<ToastOptions, 'id'>) => dispatch({ type: 'ADD_TOAST', payload: toast }),
    removeToast: (id: string) => dispatch({ type: 'REMOVE_TOAST', payload: id }),
    clearToasts: () => dispatch({ type: 'CLEAR_TOASTS' }),
  }
}

export const useWebSocketStatus = () => {
  const { state } = useAppContext()
  return state.websocket
}