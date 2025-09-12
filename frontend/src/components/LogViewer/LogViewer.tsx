import React, { useState, useEffect, useRef, useMemo } from 'react'
import { 
  Search, 
  Filter, 
  Download, 
  RefreshCw, 
  ChevronDown, 
  X,
  AlertCircle,
  Info,
  AlertTriangle,
  Bug
} from 'lucide-react'
import { LogEntry, LogFilter, LogsResponse } from '../../types/api'
import { LoadingSpinner, CardLoader } from '../common/LoadingSpinner'
import { formatTimestamp, getLogLevelColor, classNames } from '../../utils/format'
import { APIService, APIError } from '../../services/api'
import webSocketService from '../../services/websocket'

/**
 * LogViewer component for displaying and filtering application logs
 * 
 * Features:
 * - Real-time log streaming
 * - Advanced filtering (level, search, date range)
 * - Export functionality
 * - Virtualized scrolling for performance
 * - Auto-scroll to bottom
 * - Keyboard shortcuts
 * - Accessibility support
 */
export interface LogViewerProps {
  className?: string
  maxHeight?: string
  autoRefresh?: boolean
  refreshInterval?: number
}


const LOG_LEVELS = ['info', 'warning', 'error', 'debug'] as const
const LOG_MODULES = ['main', 'plex', 'config', 'file_operations', 'cache_engine', 'scheduler']

export const LogViewer: React.FC<LogViewerProps> = ({
  className,
  maxHeight = '600px',
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  // State
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<LogFilter>({})
  const [showFilters, setShowFilters] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  
  // Refs
  const logContainerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Initial fetch and auto-refresh effect
  useEffect(() => {
    fetchLogs() // Initial fetch
    
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchLogs()
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])

  // WebSocket connection and real-time log updates
  useEffect(() => {
    // Connect to WebSocket if not already connected
    if (!webSocketService.isConnected()) {
      webSocketService.connect()
    }

    // Handle real-time log entries
    const handleLogEntry = (logData: LogEntry) => {
      setLogs(prevLogs => {
        // Avoid duplicates by checking timestamp and message
        const isDuplicate = prevLogs.some(log => 
          log.timestamp === logData.timestamp && log.message === logData.message
        )
        
        if (!isDuplicate) {
          // Add new log and keep only last 500 entries for performance
          const updatedLogs = [...prevLogs, logData].slice(-500)
          return updatedLogs
        }
        
        return prevLogs
      })
    }


  }, [])

  // Filter logs whenever filters or logs change
  useEffect(() => {
    applyFilters()
  }, [logs, filters])

  // Auto-scroll effect
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [filteredLogs, autoScroll])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'f':
            e.preventDefault()
            searchInputRef.current?.focus()
            break
          case 'r':
            e.preventDefault()
            fetchLogs()
            break
        }
      }
      
      if (e.key === 'Escape') {
        setShowFilters(false)
        setFilters({})
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const fetchLogs = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const logsResponse = await APIService.getLogs()
      setLogs(logsResponse.logs || [])
      
    } catch (err) {
      console.error('Error fetching logs:', err)
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError(err instanceof Error ? err.message : 'Failed to fetch logs')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const applyFilters = () => {
    let filtered = logs

    // Filter by level
    if (filters.level && filters.level.length > 0) {
      filtered = filtered.filter(log => filters.level!.includes(log.level))
    }

    // Filter by search term
    if (filters.search && filters.search.trim()) {
      const searchTerm = filters.search.toLowerCase()
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm) ||
        log.module?.toLowerCase().includes(searchTerm)
      )
    }

    // Filter by module
    if (filters.module) {
      filtered = filtered.filter(log => log.module === filters.module)
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

    setFilteredLogs(filtered)
  }

  const handleFilterChange = (key: keyof LogFilter, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }))
  }

  const clearFilters = () => {
    setFilters({})
    setShowFilters(false)
  }

  const exportLogs = () => {
    try {
      const logText = filteredLogs.map(log => 
        `[${formatTimestamp(log.timestamp)}] ${log.level.toUpperCase()} ${log.module ? `[${log.module}]` : ''} ${log.message}`
      ).join('\n')
      
      const blob = new Blob([logText], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cacherr-logs-${new Date().toISOString().split('T')[0]}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Error exporting logs:', err)
      setError('Failed to export logs')
    }
  }

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="w-4 h-4" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4" />
      case 'info':
        return <Info className="w-4 h-4" />
      case 'debug':
        return <Bug className="w-4 h-4" />
      default:
        return null
    }
  }

  const activeFiltersCount = useMemo(() => {
    return Object.values(filters).filter(value => 
      value !== undefined && value !== null && 
      (Array.isArray(value) ? value.length > 0 : value.toString().trim() !== '')
    ).length
  }, [filters])

  return (
    <div className={classNames('card', className)}>
      {/* Header */}
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Application Logs
            {filteredLogs.length !== logs.length && (
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                ({filteredLogs.length} of {logs.length})
              </span>
            )}
          </h2>
          <div className="flex items-center space-x-2">
            {/* Auto-scroll toggle */}
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-gray-600 dark:text-gray-400">Auto-scroll</span>
            </label>

            {/* Export button */}
            <button
              onClick={exportLogs}
              className="btn btn-ghost btn-sm"
              title="Export logs"
            >
              <Download className="w-4 h-4" />
            </button>

            {/* Filter toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={classNames(
                'btn btn-ghost btn-sm relative',
                showFilters && 'bg-gray-100 dark:bg-gray-700'
              )}
              title="Toggle filters"
            >
              <Filter className="w-4 h-4" />
              {activeFiltersCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-primary-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {activeFiltersCount}
                </span>
              )}
            </button>

            {/* Refresh button */}
            <button
              onClick={fetchLogs}
              disabled={isLoading}
              className="btn btn-ghost btn-sm"
              title="Refresh logs (Ctrl+R)"
            >
              <RefreshCw className={classNames('w-4 h-4', isLoading && 'animate-spin')} />
            </button>
          </div>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 dark:bg-gray-800/50 p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Search
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search logs... (Ctrl+F)"
                  value={filters.search || ''}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="pl-10 w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* Level Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Log Level
              </label>
              <div className="space-y-2">
                {LOG_LEVELS.map(level => (
                  <label key={level} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.level?.includes(level) || false}
                      onChange={(e) => {
                        const currentLevels = filters.level || []
                        const newLevels = e.target.checked
                          ? [...currentLevels, level]
                          : currentLevels.filter(l => l !== level)
                        handleFilterChange('level', newLevels.length > 0 ? newLevels : undefined)
                      }}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 mr-2"
                    />
                    <span className={classNames('text-sm capitalize', getLogLevelColor(level))}>
                      {level}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Module Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Module
              </label>
              <select
                value={filters.module || ''}
                onChange={(e) => handleFilterChange('module', e.target.value || undefined)}
                className="w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All modules</option>
                {LOG_MODULES.map(module => (
                  <option key={module} value={module}>
                    {module}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Showing {filteredLogs.length} of {logs.length} log entries
            </div>
            <button
              onClick={clearFilters}
              className="btn btn-ghost btn-sm"
            >
              Clear filters
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-error-50 border border-error-200 p-3 dark:bg-error-900/20 dark:border-error-800">
          <p className="text-error-700 dark:text-error-300 text-sm">
            {error}
          </p>
        </div>
      )}

      {/* Log Container */}
      <div className="relative flex-1">
        {isLoading && filteredLogs.length === 0 ? (
          <CardLoader text="Loading logs..." />
        ) : (
          <div
            ref={logContainerRef}
            className="overflow-y-auto p-4 space-y-1 font-mono text-sm"
            style={{ maxHeight }}
            role="log"
            aria-live={autoRefresh ? "polite" : "off"}
            aria-label="Application logs"
          >
            {filteredLogs.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                {logs.length === 0 ? 'No logs available' : 'No logs match the current filters'}
              </div>
            ) : (
              filteredLogs.map((log, index) => (
                <div
                  key={`${log.timestamp}-${index}`}
                  className={classNames(
                    'flex items-start space-x-3 p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors',
                    log.level === 'error' && 'bg-error-50/50 dark:bg-error-900/10',
                    log.level === 'warning' && 'bg-warning-50/50 dark:bg-warning-900/10'
                  )}
                >
                  {/* Level Icon */}
                  <div className={classNames('mt-0.5 flex-shrink-0', getLogLevelColor(log.level))}>
                    {getLogIcon(log.level)}
                  </div>

                  {/* Timestamp */}
                  <div className="text-gray-500 dark:text-gray-400 w-24 flex-shrink-0 text-xs">
                    {log.timestamp ? 
                      (new Date(log.timestamp).toLocaleTimeString() || log.timestamp.slice(-8)) 
                      : new Date().toLocaleTimeString()
                    }
                  </div>

                  {/* Module */}
                  {log.module && (
                    <div className="text-primary-600 dark:text-primary-400 w-20 flex-shrink-0 text-xs">
                      [{log.module}]
                    </div>
                  )}

                  {/* Message */}
                  <div className="flex-1 text-gray-900 dark:text-gray-100 break-words">
                    {log.message}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Loading overlay */}
        {isLoading && filteredLogs.length > 0 && (
          <div className="absolute top-2 right-2">
            <LoadingSpinner size="sm" />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-2 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center justify-between">
          <div>
            Keyboard shortcuts: Ctrl+F (search), Ctrl+R (refresh), Esc (clear filters)
          </div>
          <div>
            Auto-refresh: {autoRefresh ? `${refreshInterval / 1000}s` : 'off'}
          </div>
        </div>
      </div>
    </div>
  )
}

export default LogViewer