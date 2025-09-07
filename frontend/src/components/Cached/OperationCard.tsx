/**
 * OperationCard Component
 * 
 * Displays individual operation details with expandable file listings,
 * progress tracking, and user attribution information.
 */

import React from 'react'
import { 
  ChevronDown, 
  ChevronRight, 
  Download, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Play,
  Pause,
  FileText,
  HardDrive,
  User
} from 'lucide-react'
import { StatusBadge } from '../common/StatusBadge'
import { formatBytes, formatDuration, formatFilePath, classNames } from '../../utils/format'
import { BatchOperation, OperationDetails } from './types/api'

interface OperationCardProps {
  operation: BatchOperation
  isExpanded: boolean
  details: OperationDetails | null
  detailsLoading: boolean
  onToggle: () => void
  onExport: () => void
  isLive?: boolean
}

const OperationCard: React.FC<OperationCardProps> = ({
  operation,
  isExpanded,
  details,
  detailsLoading,
  onToggle,
  onExport,
  isLive = false
}) => {
  const getStatusIcon = (status: BatchOperation['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />
      case 'running':
        return <Play className="w-5 h-5 text-blue-500 animate-pulse" />
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />
      case 'cancelled':
        return <Pause className="w-5 h-5 text-gray-500" />
      case 'completed_with_errors':
        return <AlertCircle className="w-5 h-5 text-orange-500" />
      default:
        return <Clock className="w-5 h-5 text-gray-500" />
    }
  }

  const getProgressPercentage = () => {
    if (operation.total_files === 0) return 0
    return Math.round((operation.files_processed / operation.total_files) * 100)
  }

  const formatOperationType = (type: string) => {
    switch (type) {
      case 'cache_batch':
        return 'Cache Operation'
      case 'array_batch':
        return 'Array Operation'
      case 'cleanup_batch':
        return 'Cleanup Operation'
      default:
        return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(operation.status)}
            <div>
              <h3 className="font-medium text-gray-900 dark:text-gray-100">
                {formatOperationType(operation.operation_type)}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                ID: {operation.id}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <StatusBadge status={operation.status} />
            <button
              onClick={onToggle}
              className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
            <span>Progress: {operation.files_processed} / {operation.total_files} files</span>
            <span>{getProgressPercentage()}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgressPercentage()}%` }}
            />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600 dark:text-gray-400">
              {operation.files_successful} successful
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <XCircle className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600 dark:text-gray-400">
              {operation.files_failed} failed
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <HardDrive className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600 dark:text-gray-400">
              {formatBytes(operation.bytes_processed)}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <User className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600 dark:text-gray-400">
              {operation.triggered_by_user || operation.triggered_by}
            </span>
          </div>
        </div>

        {/* Timestamps */}
        <div className="mt-3 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Started: {new Date(operation.started_at).toLocaleString()}</span>
          {operation.completed_at && (
            <span>Completed: {new Date(operation.completed_at).toLocaleString()}</span>
          )}
        </div>

        {/* Test Mode Indicator */}
        {operation.test_mode && (
          <div className="mt-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
            Test Mode
          </div>
        )}

        {/* Live Updates Indicator */}
        {isLive && (
          <div className="mt-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
            Live Updates
          </div>
        )}
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800/50">
          {detailsLoading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Loading details...</p>
            </div>
          ) : details ? (
            <div className="space-y-4">
              {/* File Operations */}
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                  File Operations ({details.file_operations.length})
                </h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {details.file_operations.map((fileOp) => (
                    <div
                      key={fileOp.id}
                      className="flex items-center justify-between p-2 bg-white dark:bg-gray-700 rounded border"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {fileOp.filename}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {formatFilePath(fileOp.file_path)}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2 ml-2">
                        <StatusBadge status={fileOp.status} />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {formatBytes(fileOp.file_size_bytes)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Export Button */}
              <div className="flex justify-end">
                <button
                  onClick={onExport}
                  className="btn btn-outline btn-sm"
                  disabled={operation.status !== 'completed'}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export Results
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
              No detailed information available
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default OperationCard
