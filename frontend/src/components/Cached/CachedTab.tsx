import React, { useState, useEffect } from 'react'
import { 
  Search, 
  Filter, 
  RefreshCw, 
  Download,
  Trash2,
  Users,
  BarChart3,
  FileText,
  Clock,
  HardDrive,
  Activity,
  TestTube
} from 'lucide-react'
import { CachedFilesFilter, ResultsFilter } from '../../types/api'
import { useCachedFilesRealTime, useCachedFilesOperations, useOperationResults, useOperationDetails, useTestResults } from '../../hooks/useApi'
import { useAppContext } from '../../store/AppContext'
import { LoadingSpinner, FullPageLoader } from '../common/LoadingSpinner'
import { classNames } from '../../utils/format'
import webSocketService from '../../services/websocket'

// Import child components (will be created)
import CachedFilesView from './CachedFilesView'
import CacheStatistics from './CacheStatistics'
import CacheActionsPanel from './CacheActionsPanel'
import FileDetailsModal from './FileDetailsModal'
import OperationsView from './OperationsView'
import { TestResults } from '../TestResults'

/**
 * Main Cached Tab Component
 * 
 * Features:
 * - Real-time cached files monitoring
 * - Operations tracking and history
 * - Advanced filtering and search capabilities
 * - Cache statistics dashboard
 * - File management operations
 * - Multi-user attribution tracking
 * - Export functionality
 * - Responsive design with mobile support
 * - WebSocket integration for live updates
 */

interface CachedTabProps {
  className?: string
}

export const CachedTab: React.FC<CachedTabProps> = ({ className }) => {
  // State management
  const { state } = useAppContext()
  const [filter, setFilter] = useState<CachedFilesFilter>({ limit: 50, offset: 0 })
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [activeView, setActiveView] = useState<'files' | 'stats' | 'operations' | 'test-results'>('files')
  
  // Operations state
  const [operationsFilter, setOperationsFilter] = useState<ResultsFilter>({})
  const [expandedOperations, setExpandedOperations] = useState<Set<string>>(new Set())
  const [selectedOperation, setSelectedOperation] = useState<string | null>(null)
  const [isPollingEnabled, setIsPollingEnabled] = useState(true)

  // API hooks
  const { 
    cachedFiles, 
    cacheStatistics, 
    refreshAll, 
    isLoading 
  } = useCachedFilesRealTime(filter)
  
  const {
    isLoading: isOperationLoading,
    cleanupCache,
    exportCachedFiles,
    searchCachedFiles
  } = useCachedFilesOperations()

  // Operations API hooks
  const { data: operationsData, isLoading: operationsLoading, error: operationsError, refetch: fetchOperations } = useOperationResults({
    autoRefresh: isPollingEnabled && activeView === 'operations',
    refreshInterval: 5000
  })

  const { data: operationDetails, isLoading: detailsLoading, error: detailsError, refetch: fetchOperationDetails } = useOperationDetails(selectedOperation)

  // Test Results API hook
  const { data: testResults, isLoading: testResultsLoading, error: testResultsError, refetch: fetchTestResults } = useTestResults({
    autoRefresh: false // Only refresh on demand for test results
  })

  // Fetch test results when switching to test-results tab
  useEffect(() => {
    if (activeView === 'test-results' && !testResults && !testResultsLoading) {
      fetchTestResults()
    }
  }, [activeView, testResults, testResultsLoading, fetchTestResults])

  // WebSocket connection is now managed at AppProvider level
  // Listen for cache-related WebSocket events
  useEffect(() => {
    const handleCacheUpdate = () => {
      refreshAll()
    }

    // Listen for operations-related WebSocket events
    const handleOperationUpdate = () => {
      if (activeView === 'operations') {
        fetchOperations()
      }
    }

    const handleFileUpdate = () => {
      if (selectedOperation) {
        fetchOperationDetails()
      }
    }

    // Add event listeners for operations updates
    webSocketService.addEventListener('operation_progress', handleOperationUpdate)
    webSocketService.addEventListener('operation_file_update', handleFileUpdate)

    return () => {
      webSocketService.removeEventListener('operation_progress', handleOperationUpdate)
      webSocketService.removeEventListener('operation_file_update', handleFileUpdate)
    }
  }, [refreshAll, activeView, selectedOperation, fetchOperations, fetchOperationDetails])

  // Event handlers
  const handleSearch = async (term: string) => {
    setSearchTerm(term)
    if (term.trim()) {
      try {
        const results = await searchCachedFiles(term, 'all', 50)
        setFilter(prev => ({ ...prev, search: term, offset: 0 }))
      } catch (error) {
        // Error handled by hook
      }
    } else {
      setFilter(prev => ({ ...prev, search: undefined, offset: 0 }))
    }
  }

  const handleFilterChange = (newFilter: Partial<CachedFilesFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter, offset: 0 }))
  }

  const handlePageChange = (page: number) => {
    const offset = page * (filter.limit || 50)
    setFilter(prev => ({ ...prev, offset }))
  }

  const handleExport = async (format: 'csv' | 'json' | 'txt') => {
    try {
      await exportCachedFiles(format, filter, true)
    } catch (error) {
      // Error handled by hook
    }
  }

  const handleCleanup = async (removeOrphaned: boolean = false) => {
    try {
      await cleanupCache({ 
        remove_orphaned: removeOrphaned,
        user_id: 'system' // Could be made dynamic based on current user
      })
      // Refresh data after cleanup
      refreshAll()
    } catch (error) {
      // Error handled by hook
    }
  }

  const handleFileSelect = (fileId: string) => {
    setSelectedFileId(fileId)
  }

  const handleCloseModal = () => {
    setSelectedFileId(null)
  }

  // Operations event handlers
  const handleOperationToggle = (operationId: string) => {
    setExpandedOperations(prev => {
      const newSet = new Set(prev)
      if (newSet.has(operationId)) {
        newSet.delete(operationId)
        if (selectedOperation === operationId) {
          setSelectedOperation(null)
        }
      } else {
        newSet.add(operationId)
        setSelectedOperation(operationId)
        fetchOperationDetails()
      }
      return newSet
    })
  }

  const handleOperationExport = (operationId: string) => {
    window.open(`/api/results/export/${operationId}`, '_blank')
  }

  const handleOperationsFilterChange = (newFilter: Partial<ResultsFilter>) => {
    setOperationsFilter(prev => ({ ...prev, ...newFilter }))
  }

  // Get current data
  const files = cachedFiles.data?.files || []
  const pagination = cachedFiles.data?.pagination
  const statistics = cacheStatistics.data
  const error = cachedFiles.error || cacheStatistics.error
  
  // Operations data
  const operations = operationsData?.operations || []
  const hasActiveOperations = operations.some(op => op.status === 'running' || op.status === 'pending')

  // Show loading state on initial load
  if (isLoading && !files.length && !statistics && activeView !== 'operations') {
    return <FullPageLoader text="Loading cached files data..." />
  }

  return (
    <div className={classNames('min-h-screen bg-gray-50 dark:bg-gray-900', className)}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Title and Navigation */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <HardDrive className="w-6 h-6 text-primary-600 mr-2" />
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  Cached Files & Operations
                </h1>
              </div>

              {/* View Toggle */}
              <div className="hidden sm:flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setActiveView('files')}
                  className={classNames(
                    'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                    activeView === 'files'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  <FileText className="w-4 h-4 mr-1 inline" />
                  Files
                </button>
                <button
                  onClick={() => setActiveView('stats')}
                  className={classNames(
                    'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                    activeView === 'stats'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  <BarChart3 className="w-4 h-4 mr-1 inline" />
                  Statistics
                </button>
                <button
                  onClick={() => setActiveView('operations')}
                  className={classNames(
                    'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                    activeView === 'operations'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  <Activity className="w-4 h-4 mr-1 inline" />
                  Operations
                  {hasActiveOperations && (
                    <span className="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Active
                    </span>
                  )}
                </button>
                <button
                  onClick={() => setActiveView('test-results')}
                  className={classNames(
                    'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                    activeView === 'test-results'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                  )}
                >
                  <TestTube className="w-4 h-4 mr-1 inline" />
                  Test Results
                </button>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-3">
              {/* Quick Stats */}
              {activeView === 'files' && (
                <div className="hidden md:flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>{files.length} files</span>
                  {statistics && (
                    <span>{statistics.total_size_readable}</span>
                  )}
                </div>
              )}
              
              {activeView === 'operations' && (
                <div className="hidden md:flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <span>{operations.length} operations</span>
                  {hasActiveOperations && (
                    <span className="text-green-600 dark:text-green-400">Active</span>
                  )}
                </div>
              )}

              {/* Live updates toggle for operations */}
              {activeView === 'operations' && (
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={isPollingEnabled}
                    onChange={(e) => setIsPollingEnabled(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-gray-600 dark:text-gray-400">Live updates</span>
                </label>
              )}

              {/* Refresh button */}
              <button
                onClick={() => {
                  if (activeView === 'operations') {
                    fetchOperations()
                  } else if (activeView === 'test-results') {
                    fetchTestResults()
                  } else {
                    refreshAll()
                  }
                }}
                disabled={isLoading || operationsLoading || testResultsLoading}
                className="btn btn-ghost btn-sm"
                aria-label="Refresh data"
              >
                <RefreshCw className={classNames('w-4 h-4', (isLoading || operationsLoading || testResultsLoading) && 'animate-spin')} />
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="pb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search cached files..."
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              {searchTerm && (
                <button
                  onClick={() => handleSearch('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {activeView === 'files' && (
          <CachedFilesView
            files={files}
            pagination={pagination}
            filter={filter}
            isLoading={isLoading}
            showFilters={showFilters}
            onFilterChange={handleFilterChange}
            onPageChange={handlePageChange}
            onFileSelect={handleFileSelect}
          />
        )}

        {activeView === 'stats' && (
          <CacheStatistics
            statistics={statistics}
            isLoading={isLoading}
          />
        )}

        {activeView === 'operations' && (
          <OperationsView
            operations={operations}
            isLoading={operationsLoading}
            error={operationsError}
            filter={operationsFilter}
            expandedOperations={expandedOperations}
            operationDetails={operationDetails}
            detailsLoading={detailsLoading}
            onFilterChange={handleOperationsFilterChange}
            onOperationToggle={handleOperationToggle}
            onExport={handleOperationExport}
          />
        )}

        {activeView === 'test-results' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <TestResults
              testResults={testResults}
              isLoading={testResultsLoading}
              error={testResultsError}
              onRefresh={fetchTestResults}
              className="w-full"
            />
          </div>
        )}
      </main>

      {/* Actions Panel */}
      {activeView === 'files' && (
        <CacheActionsPanel
          onSearch={handleSearch}
          onFilterChange={handleFilterChange}
          onExport={handleExport}
          onCleanup={handleCleanup}
          isLoading={isOperationLoading}
          showFilters={showFilters}
          onToggleFilters={() => setShowFilters(!showFilters)}
        />
      )}

      {/* File Details Modal */}
      <FileDetailsModal
        fileId={selectedFileId}
        isOpen={!!selectedFileId}
        onClose={handleCloseModal}
      />
    </div>
  )
}

export default CachedTab