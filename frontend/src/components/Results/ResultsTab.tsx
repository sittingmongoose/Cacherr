/**
 * Results Tab Component for PlexCacheUltra
 * 
 * Comprehensive results tracking interface featuring:
 * - Real-time operation monitoring
 * - Historical operation data
 * - Multi-user support with attribution
 * - Advanced filtering and search
 * - Export functionality
 * - Live progress updates
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { 
  Activity, 
  Clock, 
  Users, 
  Filter, 
  Search, 
  Download, 
  RefreshCw,
  ChevronDown,
  ChevronRight,
  PlayCircle,
  PauseCircle,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  User,
  Calendar
} from 'lucide-react'

import {
  BatchOperation,
  FileOperation,
  OperationDetails,
  ResultsFilter,
  OperationsResponse,
  UserStatistics,
  OperationProgressUpdateMessage,
  FileOperationUpdateMessage
} from '@/types/api'

import { LoadingSpinner, CardLoader } from '@/components/common/LoadingSpinner'
import { StatusBadge } from '@/components/common/StatusBadge'
import { formatBytes, formatDuration, formatFilePath, classNames } from '@/utils/format'
import { useApi } from '@/hooks/useApi'
import webSocketService from '@/services/websocket'

/**
 * Main Results Tab Component
 */
interface ResultsTabProps {
  className?: string
}

export const ResultsTab: React.FC<ResultsTabProps> = ({ className }) => {
  // State management
  const [filter, setFilter] = useState<ResultsFilter>({})
  const [activeTab, setActiveTab] = useState<'live' | 'history'>('live')
  const [expandedOperations, setExpandedOperations] = useState<Set<string>>(new Set())
  const [selectedOperation, setSelectedOperation] = useState<string | null>(null)
  const [isPollingEnabled, setIsPollingEnabled] = useState(true)

  // API hooks
  const { 
    data: operationsData,
    isLoading: operationsLoading,
    error: operationsError,
    execute: fetchOperations
  } = useApi<OperationsResponse>()

  const {
    data: operationDetails,
    isLoading: detailsLoading,
    error: detailsError,
    execute: fetchOperationDetails
  } = useApi<OperationDetails>()

  // Real-time updates
  useEffect(() => {
    const handleOperationUpdate = (data: OperationProgressUpdateMessage['data']) => {
      // Update operations list with real-time data
      fetchOperations()
    }

    const handleFileUpdate = (data: FileOperationUpdateMessage['data']) => {
      // Refresh details if we're viewing this operation
      if (selectedOperation) {
        fetchOperationDetails()
      }
    }

    webSocketService.addEventListener('operation_progress', handleOperationUpdate)
    webSocketService.addEventListener('operation_file_update', handleFileUpdate)

    return () => {
      webSocketService.removeEventListener('operation_progress', handleOperationUpdate)
      webSocketService.removeEventListener('operation_file_update', handleFileUpdate)
    }
  }, [selectedOperation, fetchOperations, fetchOperationDetails])

  // Polling for live updates
  useEffect(() => {
    if (!isPollingEnabled || activeTab !== 'live') return

    const interval = setInterval(() => {
      fetchOperations(`/api/results/operations?active_only=true&limit=20`)
    }, 5000)

    return () => clearInterval(interval)
  }, [isPollingEnabled, activeTab, fetchOperations])

  // Load initial data
  useEffect(() => {
    if (activeTab === 'live') {
      fetchOperations('/api/results/operations?active_only=true&limit=20')
    } else {
      loadHistoricalData()
    }
  }, [activeTab])

  const loadHistoricalData = useCallback(() => {
    const params = new URLSearchParams()
    params.set('limit', '50')
    params.set('offset', '0')
    
    if (filter.user_id) params.set('user_id', filter.user_id)
    if (filter.operation_type) params.set('operation_type', filter.operation_type)
    if (filter.start_date) params.set('start_date', filter.start_date)
    if (filter.end_date) params.set('end_date', filter.end_date)

    fetchOperations(`/api/results/operations?${params}`)
  }, [filter, fetchOperations])

  // Handle filter changes
  useEffect(() => {
    if (activeTab === 'history') {
      loadHistoricalData()
    }
  }, [filter, activeTab, loadHistoricalData])

  // Event handlers
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
        fetchOperationDetails(`/api/results/operations/${operationId}`)
      }
      return newSet
    })
  }

  const handleExport = (operationId: string) => {
    window.open(`/api/results/export/${operationId}`, '_blank')
  }

  const handleFilterChange = (newFilter: Partial<ResultsFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter }))
  }

  // Computed values
  const operations = operationsData?.operations || []
  const hasActiveOperations = operations.some(op => op.status === 'running' || op.status === 'pending')

  return (
    <div className={classNames('results-tab', className)}>
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Operation Results
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Track cache operations, view results, and monitor progress
              </p>
            </div>

            <div className="flex items-center space-x-3">
              {/* Live updates toggle */}
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={isPollingEnabled}
                  onChange={(e) => setIsPollingEnabled(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-gray-600 dark:text-gray-400">Live updates</span>
              </label>

              {/* Refresh button */}
              <button
                onClick={activeTab === 'live' ? () => fetchOperations('/api/results/operations?active_only=true&limit=20') : loadHistoricalData}
                disabled={operationsLoading}
                className="btn btn-ghost btn-sm"
                aria-label="Refresh data"
              >
                <RefreshCw className={classNames('w-4 h-4', operationsLoading && 'animate-spin')} />
              </button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="mt-6">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('live')}
                className={classNames(
                  'py-2 px-1 border-b-2 font-medium text-sm',
                  activeTab === 'live'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4" />
                  <span>Live Operations</span>
                  {hasActiveOperations && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Active
                    </span>
                  )}
                </div>
              </button>
              
              <button
                onClick={() => setActiveTab('history')}
                className={classNames(
                  'py-2 px-1 border-b-2 font-medium text-sm',
                  activeTab === 'history'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4" />
                  <span>Operation History</span>
                </div>
              </button>
            </nav>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'live' ? (
          <LiveOperationsView
            operations={operations}
            isLoading={operationsLoading}
            error={operationsError}
            expandedOperations={expandedOperations}
            operationDetails={operationDetails}
            detailsLoading={detailsLoading}
            onOperationToggle={handleOperationToggle}
            onExport={handleExport}
          />
        ) : (
          <HistoryView
            operations={operations}
            isLoading={operationsLoading}
            error={operationsError}
            filter={filter}
            expandedOperations={expandedOperations}
            operationDetails={operationDetails}
            detailsLoading={detailsLoading}
            onFilterChange={handleFilterChange}
            onOperationToggle={handleOperationToggle}
            onExport={handleExport}
          />
        )}
      </div>
    </div>
  )
}

/**
 * Live Operations View Component
 */
interface LiveOperationsViewProps {
  operations: BatchOperation[]
  isLoading: boolean
  error: string | null
  expandedOperations: Set<string>
  operationDetails: OperationDetails | null
  detailsLoading: boolean
  onOperationToggle: (operationId: string) => void
  onExport: (operationId: string) => void
}

const LiveOperationsView: React.FC<LiveOperationsViewProps> = ({
  operations,
  isLoading,
  error,
  expandedOperations,
  operationDetails,
  detailsLoading,
  onOperationToggle,
  onExport
}) => {
  if (isLoading && operations.length === 0) {
    return (
      <div className="p-6">
        <CardLoader text="Loading live operations..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-error-50 border border-error-200 rounded-lg p-4 dark:bg-error-900/20 dark:border-error-800">
          <p className="text-error-700 dark:text-error-300">{error}</p>
        </div>
      </div>
    )
  }

  if (operations.length === 0) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No Active Operations
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            All operations are currently idle. Start a cache operation to see live progress here.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4">
      {operations.map((operation) => (
        <OperationCard
          key={operation.id}
          operation={operation}
          isExpanded={expandedOperations.has(operation.id)}
          details={operationDetails?.batch_operation.id === operation.id ? operationDetails : null}
          detailsLoading={detailsLoading}
          onToggle={() => onOperationToggle(operation.id)}
          onExport={() => onExport(operation.id)}
          isLive={true}
        />
      ))}
    </div>
  )
}

/**
 * History View Component
 */
interface HistoryViewProps {
  operations: BatchOperation[]
  isLoading: boolean
  error: string | null
  filter: ResultsFilter
  expandedOperations: Set<string>
  operationDetails: OperationDetails | null
  detailsLoading: boolean
  onFilterChange: (filter: Partial<ResultsFilter>) => void
  onOperationToggle: (operationId: string) => void
  onExport: (operationId: string) => void
}

const HistoryView: React.FC<HistoryViewProps> = ({
  operations,
  isLoading,
  error,
  filter,
  expandedOperations,
  operationDetails,
  detailsLoading,
  onFilterChange,
  onOperationToggle,
  onExport
}) => {
  return (
    <div className="flex flex-col h-full">
      {/* Filters */}
      <div className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search operations..."
              value={filter.search || ''}
              onChange={(e) => onFilterChange({ search: e.target.value })}
              className="pl-10 w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700"
            />
          </div>

          {/* Operation Type */}
          <select
            value={filter.operation_type || ''}
            onChange={(e) => onFilterChange({ operation_type: e.target.value || undefined })}
            className="rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700"
          >
            <option value="">All Operation Types</option>
            <option value="cache_batch">Cache Operations</option>
            <option value="array_batch">Array Operations</option>
            <option value="cleanup_batch">Cleanup Operations</option>
          </select>

          {/* User Filter */}
          <input
            type="text"
            placeholder="Filter by user..."
            value={filter.user_id || ''}
            onChange={(e) => onFilterChange({ user_id: e.target.value || undefined })}
            className="rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700"
          />

          {/* Date Range */}
          <input
            type="date"
            value={filter.start_date || ''}
            onChange={(e) => onFilterChange({ start_date: e.target.value || undefined })}
            className="rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700"
          />
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <CardLoader text="Loading operation history..." />
        ) : error ? (
          <div className="bg-error-50 border border-error-200 rounded-lg p-4 dark:bg-error-900/20 dark:border-error-800">
            <p className="text-error-700 dark:text-error-300">{error}</p>
          </div>
        ) : operations.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              No Operations Found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              No operations match your current filters. Try adjusting your search criteria.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {operations.map((operation) => (
              <OperationCard
                key={operation.id}
                operation={operation}
                isExpanded={expandedOperations.has(operation.id)}
                details={operationDetails?.batch_operation.id === operation.id ? operationDetails : null}
                detailsLoading={detailsLoading}
                onToggle={() => onOperationToggle(operation.id)}
                onExport={() => onExport(operation.id)}
                isLive={false}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ResultsTab