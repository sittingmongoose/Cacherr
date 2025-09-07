/**
 * Operations View Component for Cached Tab
 * 
 * Displays operations tracking and history within the Cached tab,
 * providing real-time monitoring and historical data for cache operations.
 */

import React, { useState } from 'react'
import { 
  Activity, 
  Clock, 
  Users, 
  Filter, 
  Search, 
  Download, 
  ChevronDown,
  ChevronRight,
  PlayCircle,
  PauseCircle,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  User,
  Calendar,
  HardDrive,
  Database,
  Trash2
} from 'lucide-react'

import {
  BatchOperation,
  FileOperation,
  OperationDetails,
  ResultsFilter
} from './types/api'

import { LoadingSpinner, CardLoader } from '../common/LoadingSpinner'
import StatusBadge from '../common/StatusBadge'
import { formatBytes, formatDuration, formatFilePath, classNames } from '../../utils/format'
import OperationCard from './OperationCard'

interface OperationsViewProps {
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

export const OperationsView: React.FC<OperationsViewProps> = ({
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
  const [activeTab, setActiveTab] = useState<'live' | 'history'>('live')

  // Filter operations based on active tab
  const filteredOperations = operations.filter(operation => {
    if (activeTab === 'live') {
      return operation.status === 'running' || operation.status === 'pending'
    }
    return operation.status === 'completed' || operation.status === 'failed' || operation.status === 'cancelled' || operation.status === 'completed_with_errors'
  })

  const hasActiveOperations = operations.some(op => op.status === 'running' || op.status === 'pending')

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="space-y-8">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Operations
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  Track cache operations, view results, and monitor progress
                </p>
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
              operations={filteredOperations}
              isLoading={isLoading}
              error={error}
              expandedOperations={expandedOperations}
              operationDetails={operationDetails}
              detailsLoading={detailsLoading}
              onOperationToggle={onOperationToggle}
              onExport={onExport}
            />
          ) : (
            <HistoryView
              operations={filteredOperations}
              isLoading={isLoading}
              error={error}
              filter={filter}
              expandedOperations={expandedOperations}
              operationDetails={operationDetails}
              detailsLoading={detailsLoading}
              onFilterChange={onFilterChange}
              onOperationToggle={onOperationToggle}
              onExport={onExport}
            />
          )}
        </div>
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

export default OperationsView
