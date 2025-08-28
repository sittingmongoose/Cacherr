/**
 * OperationCard Component
 * 
 * Displays individual operation details with expandable file listings,
 * progress tracking, and user attribution information.
 */

import React, { useMemo } from 'react'
import {
  ChevronDown,
  ChevronRight,
  PlayCircle,
  PauseCircle,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  User,
  Clock,
  Download,
  Activity,
  HardDrive,
  Database,
  Trash2
} from 'lucide-react'

import {
  BatchOperation,
  type OperationDetails,
  FileOperation
} from '@/types/api'

import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { formatBytes, formatDuration, formatFilePath, classNames } from '@/utils/format'

interface OperationCardProps {
  operation: BatchOperation
  isExpanded: boolean
  details: OperationDetails | null
  detailsLoading: boolean
  onToggle: () => void
  onExport: () => void
  isLive: boolean
}

export const OperationCard: React.FC<OperationCardProps> = ({
  operation,
  isExpanded,
  details,
  detailsLoading,
  onToggle,
  onExport,
  isLive
}) => {
  // Compute progress and status
  const progress = useMemo(() => {
    if (operation.total_files === 0) return 0
    return (operation.files_processed / operation.total_files) * 100
  }, [operation.files_processed, operation.total_files])

  const isActive = operation.status === 'running' || operation.status === 'pending'
  const isCompleted = operation.status === 'completed' || operation.status === 'completed_with_errors'
  const hasErrors = operation.status === 'failed' || operation.status === 'completed_with_errors'

  // Get appropriate icon for operation type
  const getOperationIcon = () => {
    switch (operation.operation_type) {
      case 'cache_batch':
        return <HardDrive className="w-5 h-5" />
      case 'array_batch':
        return <Database className="w-5 h-5" />
      case 'cleanup_batch':
        return <Trash2 className="w-5 h-5" />
      default:
        return <Activity className="w-5 h-5" />
    }
  }

  // Get status icon and color
  const getStatusDisplay = () => {
    switch (operation.status) {
      case 'pending':
        return { icon: <PauseCircle className="w-5 h-5" />, color: 'text-yellow-500' }
      case 'running':
        return { icon: <PlayCircle className="w-5 h-5" />, color: 'text-blue-500' }
      case 'completed':
        return { icon: <CheckCircle className="w-5 h-5" />, color: 'text-green-500' }
      case 'failed':
        return { icon: <XCircle className="w-5 h-5" />, color: 'text-red-500' }
      case 'completed_with_errors':
        return { icon: <AlertCircle className="w-5 h-5" />, color: 'text-orange-500' }
      case 'cancelled':
        return { icon: <XCircle className="w-5 h-5" />, color: 'text-gray-500' }
      default:
        return { icon: <Activity className="w-5 h-5" />, color: 'text-gray-500' }
    }
  }

  const statusDisplay = getStatusDisplay()
  const duration = operation.started_at && operation.completed_at
    ? formatDuration(new Date(operation.completed_at).getTime() - new Date(operation.started_at).getTime())
    : operation.started_at
    ? formatDuration(Date.now() - new Date(operation.started_at).getTime())
    : null

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm overflow-hidden">
      {/* Operation Header */}
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 flex-1 min-w-0">
            {/* Operation Type Icon */}
            <div className="flex-shrink-0 text-primary-600 dark:text-primary-400">
              {getOperationIcon()}
            </div>

            {/* Operation Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-3">
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 truncate">
                  {operation.operation_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h3>
                
                <StatusBadge
                  status={operation.status}
                  variant={isActive ? 'warning' : isCompleted && !hasErrors ? 'success' : hasErrors ? 'error' : 'default'}
                />

                {operation.test_mode && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                    Test Mode
                  </span>
                )}

                {isLive && isActive && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 animate-pulse">
                    Live
                  </span>
                )}
              </div>

              {/* Progress Bar */}
              {isActive && operation.total_files > 0 && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
                    <span>Progress: {operation.files_processed} / {operation.total_files} files</span>
                    <span>{Math.round(progress)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Summary Stats */}
              <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center space-x-1">
                  <FileText className="w-4 h-4" />
                  <span>{operation.files_processed} / {operation.total_files} files</span>
                </span>

                {operation.files_failed > 0 && (
                  <span className="flex items-center space-x-1 text-red-600 dark:text-red-400">
                    <XCircle className="w-4 h-4" />
                    <span>{operation.files_failed} failed</span>
                  </span>
                )}

                <span>{formatBytes(operation.bytes_processed)} / {formatBytes(operation.total_size_bytes)}</span>

                {operation.triggered_by_user && (
                  <span className="flex items-center space-x-1">
                    <User className="w-4 h-4" />
                    <span>{operation.triggered_by_user}</span>
                  </span>
                )}

                {duration && (
                  <span className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{duration}</span>
                  </span>
                )}

                <span className="capitalize">{operation.reason.replace('_', ' ')}</span>
              </div>
            </div>
          </div>

          {/* Status and Controls */}
          <div className="flex items-center space-x-3">
            {/* Status Icon */}
            <div className={classNames('flex-shrink-0', statusDisplay.color)}>
              {statusDisplay.icon}
            </div>

            {/* Export Button */}
            {isCompleted && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onExport()
                }}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                title="Export operation details"
              >
                <Download className="w-4 h-4" />
              </button>
            )}

            {/* Expand/Collapse Icon */}
            <div className="text-gray-400">
              {isExpanded ? (
                <ChevronDown className="w-5 h-5" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </div>
          </div>
        </div>
      </button>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {detailsLoading ? (
            <div className="p-6">
              <div className="flex items-center justify-center">
                <LoadingSpinner text="Loading operation details..." />
              </div>
            </div>
          ) : details ? (
            <OperationDetails operation={details} />
          ) : (
            <div className="p-6">
              <div className="text-center text-gray-500 dark:text-gray-400">
                Failed to load operation details
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Operation Details Component
 */
interface OperationDetailsProps {
  operation: OperationDetails
}

const OperationDetails: React.FC<OperationDetailsProps> = ({ operation }) => {
  const { batch_operation: batch, file_operations: files } = operation

  // Group files by status for better organization
  const filesByStatus = useMemo(() => {
    const groups: Record<string, FileOperation[]> = {}
    files.forEach(file => {
      if (!groups[file.status]) {
        groups[file.status] = []
      }
      groups[file.status].push(file)
    })
    return groups
  }, [files])

  return (
    <div className="space-y-6">
      {/* Operation Summary */}
      <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Timing</h4>
            <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <div>Started: {new Date(batch.started_at).toLocaleString()}</div>
              {batch.completed_at && (
                <div>Completed: {new Date(batch.completed_at).toLocaleString()}</div>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Attribution</h4>
            <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <div>Triggered by: {batch.triggered_by}</div>
              {batch.triggered_by_user && (
                <div>User: {batch.triggered_by_user}</div>
              )}
              <div>Reason: {batch.reason.replace('_', ' ')}</div>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Results</h4>
            <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <div>Success: {batch.files_successful} files</div>
              <div>Failed: {batch.files_failed} files</div>
              <div>Processed: {formatBytes(batch.bytes_processed)}</div>
            </div>
          </div>
        </div>

        {batch.error_message && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg dark:bg-red-900/20 dark:border-red-800">
            <h4 className="text-sm font-medium text-red-800 dark:text-red-300 mb-1">Error</h4>
            <p className="text-sm text-red-700 dark:text-red-300">{batch.error_message}</p>
          </div>
        )}
      </div>

      {/* File Operations */}
      <div className="px-6 pb-6">
        <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          File Operations ({files.length})
        </h4>

        {Object.entries(filesByStatus).map(([status, statusFiles]) => (
          <div key={status} className="mb-6 last:mb-0">
            <div className="flex items-center space-x-2 mb-3">
              <StatusBadge status={status} size="sm" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {status.charAt(0).toUpperCase() + status.slice(1)} ({statusFiles.length})
              </span>
            </div>

            <div className="space-y-2">
              {statusFiles.map((file) => (
                <FileOperationRow key={file.id} file={file} />
              ))}
            </div>
          </div>
        ))}

        {files.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No file operations found
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * File Operation Row Component
 */
interface FileOperationRowProps {
  file: FileOperation
}

const FileOperationRow: React.FC<FileOperationRowProps> = ({ file }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400'
      case 'failed':
        return 'text-red-600 dark:text-red-400'
      case 'processing':
        return 'text-blue-600 dark:text-blue-400'
      case 'pending':
        return 'text-yellow-600 dark:text-yellow-400'
      case 'skipped':
        return 'text-gray-600 dark:text-gray-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
      <div className="flex-1 min-w-0">
        <div className="font-medium text-gray-900 dark:text-gray-100 truncate">
          {file.filename}
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400 font-mono truncate">
          {formatFilePath(file.source_path)}
        </div>
        {file.destination_path && (
          <div className="text-sm text-gray-500 dark:text-gray-500 font-mono truncate">
            → {formatFilePath(file.destination_path)}
          </div>
        )}
        {file.error_message && (
          <div className="text-sm text-red-600 dark:text-red-400 mt-1">
            Error: {file.error_message}
          </div>
        )}
      </div>

      <div className="flex items-center space-x-4 ml-4">
        <div className="text-right">
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {formatBytes(file.file_size_bytes)}
          </div>
          <div className={classNames('text-xs capitalize', getStatusColor(file.status))}>
            {file.status}
          </div>
        </div>
        
        <div className="text-xs text-gray-500 dark:text-gray-500 text-right">
          <div>{file.operation_type}</div>
          <div>{file.reason.replace('_', ' ')}</div>
        </div>
      </div>
    </div>
  )
}

export default OperationCard