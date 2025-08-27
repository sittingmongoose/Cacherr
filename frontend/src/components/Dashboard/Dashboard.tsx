import React, { useEffect } from 'react'
import { Settings, RefreshCw, Moon, Sun, Monitor, Wifi, WifiOff } from 'lucide-react'
import { SystemStatus, HealthStatus, CacheStatistics } from '@/types/api'
import StatusCard from '@/components/StatusCard'
import StatsGrid from '@/components/StatsGrid'
import { LoadingSpinner, FullPageLoader } from '@/components/common/LoadingSpinner'
import { classNames } from '@/utils/format'
import { useAppContext, useSystemStatus, useUIState, useWebSocketStatus } from '@/store'
import { useRealTimeData, useOperations } from '@/hooks/useApi'
import webSocketService from '@/services/websocket'

/**
 * Main Dashboard component
 * 
 * Features:
 * - Real-time system monitoring
 * - Operation controls
 * - Statistics overview
 * - Theme switching
 * - Responsive layout
 * - Auto-refresh functionality
 * - Error handling
 */
interface DashboardProps {
  className?: string
}

type Theme = 'light' | 'dark' | 'auto'

export const Dashboard: React.FC<DashboardProps> = ({ className }) => {
  // Global state management
  const { state } = useAppContext()
  const { systemStatus, healthStatus, logs, refreshAll, isLoading } = useRealTimeData()
  const { ui, setTheme, setAutoRefresh } = useUIState()
  const { dispatch } = useAppContext()
  const { isRunning, runCacheOperation, startScheduler, stopScheduler } = useOperations()
  const wsStatus = useWebSocketStatus()

  // Extract data from global state and API hooks
  const currentSystemStatus = systemStatus.data || state.systemStatus
  const currentHealthStatus = healthStatus.data || state.healthStatus
  const error = state.errors.systemStatus || state.errors.healthStatus || state.errors.operations

  // Initialize WebSocket connection
  useEffect(() => {
    webSocketService.connect()
    
    return () => {
      webSocketService.disconnect()
    }
  }, [])

  // Event handlers
  const handleRunCache = async () => {
    try {
      await runCacheOperation({ test_mode: false })
    } catch (error) {
      // Error handling is done in the useOperations hook
    }
  }

  const handleRunTest = async () => {
    try {
      await runCacheOperation({ test_mode: true })
    } catch (error) {
      // Error handling is done in the useOperations hook
    }
  }

  const handleStartScheduler = async () => {
    try {
      await startScheduler()
    } catch (error) {
      // Error handling is done in the useOperations hook
    }
  }

  const handleStopScheduler = async () => {
    try {
      await stopScheduler()
    } catch (error) {
      // Error handling is done in the useOperations hook
    }
  }

  const toggleTheme = () => {
    const themes: Theme[] = ['light', 'dark', 'auto']
    const currentIndex = themes.indexOf(ui.theme)
    const nextIndex = (currentIndex + 1) % themes.length
    setTheme(themes[nextIndex])
  }

  const getThemeIcon = () => {
    switch (ui.theme) {
      case 'light': return <Sun className="w-4 h-4" />
      case 'dark': return <Moon className="w-4 h-4" />
      case 'auto': return <Monitor className="w-4 h-4" />
    }
  }

  const getWebSocketIcon = () => {
    if (wsStatus.connected) {
      return <Wifi className="w-4 h-4 text-green-500" />
    } else if (wsStatus.reconnecting) {
      return <WifiOff className="w-4 h-4 text-yellow-500 animate-pulse" />
    } else {
      return <WifiOff className="w-4 h-4 text-red-500" />
    }
  }

  if (isLoading && !currentSystemStatus) {
    return <FullPageLoader text="Loading PlexCacheUltra Dashboard..." />
  }

  return (
    <div className={classNames('min-h-screen bg-gray-50 dark:bg-gray-900', className)}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Title */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  🎬 PlexCacheUltra
                </h1>
              </div>
              <div className="hidden md:block ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Docker-optimized Plex media caching system
                </p>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center space-x-3">
              {/* WebSocket status indicator */}
              <div
                className="flex items-center space-x-1 text-sm text-gray-600 dark:text-gray-400"
                title={`WebSocket: ${wsStatus.connected ? 'Connected' : wsStatus.reconnecting ? 'Reconnecting...' : 'Disconnected'}`}
              >
                {getWebSocketIcon()}
                <span className="hidden sm:inline text-xs">
                  {wsStatus.connected ? 'Live' : wsStatus.reconnecting ? 'Connecting...' : 'Offline'}
                </span>
              </div>

              {/* Auto-refresh toggle */}
              <label className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <input
                  type="checkbox"
                  checked={ui.autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700"
                />
                <span className="hidden sm:inline">Auto-refresh</span>
              </label>

              {/* Manual refresh */}
              <button
                onClick={refreshAll}
                disabled={isLoading}
                className="btn btn-ghost p-2"
                aria-label="Refresh data"
              >
                <RefreshCw className={classNames(
                  'w-4 h-4',
                  isLoading && 'animate-spin'
                )} />
              </button>

              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className="btn btn-ghost p-2"
                aria-label={`Switch theme (current: ${ui.theme})`}
              >
                {getThemeIcon()}
              </button>

              {/* Settings */}
              <button
                className="btn btn-ghost p-2"
                aria-label="Settings"
              >
                <Settings className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Status and refresh info */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Dashboard
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Last updated: {systemStatus.lastFetched?.toLocaleTimeString() || 'Never'}
                {ui.autoRefresh && (
                  <span className="ml-2 text-xs">
                    (refreshes every {ui.refreshInterval / 1000}s)
                  </span>
                )}
                {wsStatus.connected && (
                  <span className="ml-2 text-xs text-green-600 dark:text-green-400">
                    • Live updates active
                  </span>
                )}
              </p>
            </div>
            
            {isLoading && (
              <LoadingSpinner size="sm" text="Refreshing..." />
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-error-50 border border-error-200 rounded-lg p-4 dark:bg-error-900/20 dark:border-error-800">
              <p className="text-error-700 dark:text-error-300">
                {error}
              </p>
              <button
                onClick={() => dispatch({ type: 'CLEAR_ERRORS' })}
                className="text-error-600 hover:text-error-800 text-sm underline mt-2 dark:text-error-400 dark:hover:text-error-200"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Dashboard Grid */}
          <div className="dashboard-grid">
            {/* Status Card - Left Column */}
            <div className="lg:col-span-1">
              <StatusCard
                status={currentSystemStatus}
                isLoading={isLoading}
                error={error}
                onRunCache={handleRunCache}
                onRunTest={handleRunTest}
                onStartScheduler={handleStartScheduler}
                onStopScheduler={handleStopScheduler}
                operationInProgress={isRunning}
              />
            </div>

            {/* Stats Grid - Right Columns */}
            <div className="lg:col-span-2">
              <StatsGrid
                status={currentSystemStatus}
                cacheStats={currentSystemStatus?.cache_statistics}
                healthStatus={currentHealthStatus}
                isLoading={isLoading}
                error={error}
              />
            </div>
          </div>

          {/* Additional sections will be added here */}
          {/* - LogViewer */}
          {/* - TestResults */}
          {/* - Settings Panel */}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
            <div>
              PlexCacheUltra v1.0.0 - Modern React Dashboard
            </div>
            <div>
              Theme: <span className="capitalize">{ui.theme}</span>
              {wsStatus.connected && (
                <span className="ml-4 text-green-600 dark:text-green-400">
                  • Connected
                </span>
              )}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Dashboard