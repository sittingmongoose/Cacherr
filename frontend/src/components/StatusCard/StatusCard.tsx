import React from 'react'
import { Play, Pause, TestTube, Calendar, Activity, AlertTriangle } from 'lucide-react'
import { SystemStatus } from '../../types/api'
import { StatusBadge, HealthIndicator } from '../common/StatusBadge'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { formatRelativeTime, classNames } from '../../utils/format'

/**
 * StatusCard component displays the main system status and controls
 * 
 * Features:
 * - Real-time status updates
 * - Operation controls (Run Cache, Test Mode)
 * - Scheduler controls
 * - Health indicators
 * - Accessibility support
 * - Responsive design
 */
interface StatusCardProps {
  status?: SystemStatus
  isLoading?: boolean
  error?: string
  onRunCache: () => Promise<void>
  onRunTest: () => Promise<void>
  onStartScheduler: () => Promise<void>
  onStopScheduler: () => Promise<void>
  operationInProgress?: boolean
  className?: string
}

export const StatusCard: React.FC<StatusCardProps> = ({
  status,
  isLoading,
  error,
  onRunCache,
  onRunTest,
  onStartScheduler,
  onStopScheduler,
  operationInProgress = false,
  className
}) => {
  const isSystemRunning = status?.status === 'running'
  const isTestModeRunning = status?.status === 'running_test'
  const isAnyOperationRunning = isSystemRunning || isTestModeRunning
  const isSchedulerRunning = status?.scheduler_running ?? false

  const handleRunCache = async () => {
    if (operationInProgress || isAnyOperationRunning) return
    await onRunCache()
  }

  const handleRunTest = async () => {
    if (operationInProgress || isAnyOperationRunning) return
    await onRunTest()
  }

  const handleStartScheduler = async () => {
    if (isSchedulerRunning) return
    await onStartScheduler()
  }

  const handleStopScheduler = async () => {
    if (!isSchedulerRunning) return
    await onStopScheduler()
  }

  if (error) {
    return (
      <div className={classNames('card bg-error-50 border-error-200 dark:bg-error-900/20 dark:border-error-800', className)}>
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-error-500 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-medium text-error-900 dark:text-error-100">
              System Error
            </h3>
            <p className="text-error-700 dark:text-error-300 mt-1">
              {error}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading || !status) {
    return (
      <div className={classNames('card', className)}>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner size="md" text="Loading system status..." />
        </div>
      </div>
    )
  }

  return (
    <div className={classNames('card', className)}>
      {/* Header */}
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            System Status
          </h2>
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-gray-400" aria-hidden="true" />
            <StatusBadge
              status={status.status}
              pulse={isAnyOperationRunning}
            />
          </div>
        </div>
      </div>

      {/* Status Information */}
      <div className="space-y-6">
        {/* Current Status */}
        <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Current Status
            </p>
            <p className="text-lg text-gray-900 dark:text-gray-100">
              {isSystemRunning ? 'Running cache operation' : 
               isTestModeRunning ? 'Running test mode analysis' : 
               'System is idle'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Last Updated
            </p>
            <p className="text-sm font-mono text-gray-700 dark:text-gray-300">
              {formatRelativeTime(new Date())}
            </p>
          </div>
        </div>

        {/* Operation Statistics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {status.pending_operations.files_to_cache}
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Files to Cache
            </p>
          </div>
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {status.pending_operations.files_to_array}
            </p>
            <p className="text-sm text-green-700 dark:text-green-300">
              Files to Array
            </p>
          </div>
        </div>

        {/* Last Execution */}
        {status.last_execution && (
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Last Execution
            </h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {status.last_execution.execution_time ? formatRelativeTime(status.last_execution.execution_time) : 'Unknown time'}
                </p>
                {status.last_execution.duration_seconds && (
                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    Duration: {Math.round(status.last_execution.duration_seconds)}s
                  </p>
                )}
              </div>
              <StatusBadge
                status={status.last_execution.success ? 'completed' : 'failed'}
                size="sm"
              />
            </div>
            {status.last_execution.error_message && (
              <p className="text-sm text-error-600 dark:text-error-400 mt-2">
                {status.last_execution.error_message}
              </p>
            )}
          </div>
        )}

        {/* Controls */}
        <div className="space-y-4">
          {/* Operation Controls */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Cache Operations
            </h3>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleRunCache}
                disabled={operationInProgress || isAnyOperationRunning}
                className="btn btn-primary flex items-center"
                aria-label="Run cache operation"
              >
                {(operationInProgress || isSystemRunning) ? (
                  <LoadingSpinner size="sm" inline />
                ) : (
                  <Play className="w-4 h-4 mr-2" aria-hidden="true" />
                )}
                Run Cache
              </button>
              
              <button
                onClick={handleRunTest}
                disabled={operationInProgress || isAnyOperationRunning}
                className="btn btn-secondary flex items-center"
                aria-label="Run test mode analysis"
              >
                {(operationInProgress || isTestModeRunning) ? (
                  <LoadingSpinner size="sm" inline />
                ) : (
                  <TestTube className="w-4 h-4 mr-2" aria-hidden="true" />
                )}
                Test Mode
              </button>
            </div>
          </div>

          {/* Scheduler Controls */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Scheduler
              </h3>
              <StatusBadge
                status={isSchedulerRunning ? 'running' : 'stopped'}
                size="sm"
                pulse={isSchedulerRunning}
              />
            </div>
            <div className="flex gap-3">
              {!isSchedulerRunning ? (
                <button
                  onClick={handleStartScheduler}
                  className="btn btn-success flex items-center"
                  aria-label="Start scheduler"
                >
                  <Play className="w-4 h-4 mr-2" aria-hidden="true" />
                  Start Scheduler
                </button>
              ) : (
                <button
                  onClick={handleStopScheduler}
                  className="btn btn-danger flex items-center"
                  aria-label="Stop scheduler"
                >
                  <Pause className="w-4 h-4 mr-2" aria-hidden="true" />
                  Stop Scheduler
                </button>
              )}
              
              <button
                className="btn btn-ghost flex items-center"
                aria-label="View scheduler settings"
              >
                <Calendar className="w-4 h-4 mr-2" aria-hidden="true" />
                Settings
              </button>
            </div>
          </div>
        </div>

        {/* Health Indicators (if available) */}
        {status.cache_statistics && (
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              System Health
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <HealthIndicator
                status="healthy"
                label="Cache System"
              />
              <HealthIndicator
                status={isSchedulerRunning ? "healthy" : "unknown"}
                label="Scheduler"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StatusCard