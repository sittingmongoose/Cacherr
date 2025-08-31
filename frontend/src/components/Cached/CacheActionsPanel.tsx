import React, { useState } from 'react'
import { 
  Trash2, 
  Download, 
  RefreshCw, 
  AlertTriangle, 
  Settings, 
  Filter,
  BarChart3,
  FileText,
  Users,
  HardDrive,
  CheckCircle,
  Clock,
  Info,
  Zap,
  Shield,
  Target
} from 'lucide-react'
import { CacheStatistics, CacheCleanupRequest, CachedFilesFilter } from '@/types/api'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { classNames } from '@/utils/format'

/**
 * CacheActionsPanel Component
 * 
 * Features:
 * - Cache management operations
 * - Cleanup operations with preview
 * - Export functionality with format options
 * - Quick statistics display
 * - Batch operation controls
 * - Safety confirmations
 * - Progress indicators
 * - Responsive design
 * - Accessible interactions
 */

interface CacheActionsPanelProps {
  statistics?: CacheStatistics | null
  onCleanup: (removeOrphaned?: boolean) => Promise<void>
  onExport: (format: 'csv' | 'json' | 'txt') => Promise<void>
  onSearch?: (term: string) => Promise<void>
  onFilterChange?: (newFilter: Partial<CachedFilesFilter>) => void
  showFilters?: boolean
  onToggleFilters?: () => void
  isLoading?: boolean
  className?: string
}

interface ActionCardProps {
  icon: React.ReactNode
  title: string
  description: string
  action: React.ReactNode
  variant?: 'default' | 'warning' | 'danger' | 'success' | 'info'
  disabled?: boolean
}

const ActionCard: React.FC<ActionCardProps> = ({
  icon,
  title,
  description,
  action,
  variant = 'default',
  disabled = false
}) => {
  const variantClasses = {
    default: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
    warning: 'border-yellow-200 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20',
    danger: 'border-red-200 dark:border-red-700 bg-red-50 dark:bg-red-900/20',
    success: 'border-green-200 dark:border-green-700 bg-green-50 dark:bg-green-900/20',
    info: 'border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20'
  }

  const iconColors = {
    default: 'text-gray-500',
    warning: 'text-yellow-600 dark:text-yellow-400',
    danger: 'text-red-600 dark:text-red-400',
    success: 'text-green-600 dark:text-green-400',
    info: 'text-blue-600 dark:text-blue-400'
  }

  return (
    <div className={classNames(
      'border rounded-lg p-4 transition-all duration-200',
      variantClasses[variant],
      disabled && 'opacity-50'
    )}>
      <div className="flex items-start justify-between">
        <div className="flex items-start">
          <div className={classNames('p-2 rounded-lg mr-3 flex-shrink-0', iconColors[variant])}>
            {icon}
          </div>
          <div className="min-w-0 flex-1">
            <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
              {title}
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {description}
            </p>
          </div>
        </div>
        <div className="ml-4 flex-shrink-0">
          {action}
        </div>
      </div>
    </div>
  )
}

interface CleanupModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (removeOrphaned: boolean) => void
  statistics: CacheStatistics | null
  isLoading: boolean
}

const CleanupModal: React.FC<CleanupModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  statistics,
  isLoading
}) => {
  const [removeOrphaned, setRemoveOrphaned] = useState(false)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
          {/* Header */}
          <div className="flex items-center p-6 border-b border-gray-200 dark:border-gray-700">
            <AlertTriangle className="w-6 h-6 text-yellow-500 mr-3" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Cache Cleanup
            </h3>
          </div>

          {/* Content */}
          <div className="p-6">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              This will scan for and identify orphaned cache entries - files that are tracked 
              in the cache database but no longer exist on disk.
            </p>

            {statistics && (
              <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Total Files:</span>
                    <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                      {statistics.total_files}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Active Files:</span>
                    <span className="ml-2 font-medium text-green-600 dark:text-green-400">
                      {statistics.active_files}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Orphaned:</span>
                    <span className="ml-2 font-medium text-yellow-600 dark:text-yellow-400">
                      {statistics.orphaned_files}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600 dark:text-gray-400">Total Size:</span>
                    <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                      {statistics.total_size_readable}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Options */}
            <div className="space-y-3">
              <label className="flex items-start">
                <input
                  type="checkbox"
                  checked={removeOrphaned}
                  onChange={(e) => setRemoveOrphaned(e.target.checked)}
                  className="mt-1 rounded border-gray-300 text-red-600 focus:ring-red-500 dark:border-gray-600 dark:bg-gray-700"
                />
                <div className="ml-3">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Remove orphaned entries
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    Permanently delete orphaned cache entries from the database. 
                    This cannot be undone.
                  </div>
                </div>
              </label>
            </div>

            {/* Warning */}
            {removeOrphaned && (
              <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <div className="flex items-start">
                  <AlertTriangle className="w-4 h-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-red-700 dark:text-red-300">
                    <strong>Warning:</strong> Removing orphaned entries is permanent and cannot be undone. 
                    Make sure you have backups if needed.
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="btn btn-ghost"
            >
              Cancel
            </button>
            <button
              onClick={() => onConfirm(removeOrphaned)}
              disabled={isLoading}
              className={classNames(
                'btn',
                removeOrphaned ? 'btn-error' : 'btn-warning'
              )}
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Processing...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  {removeOrphaned ? 'Remove Orphaned' : 'Scan Only'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export const CacheActionsPanel: React.FC<CacheActionsPanelProps> = ({
  statistics,
  onCleanup,
  onExport,
  isLoading = false,
  className
}) => {
  const [showCleanupModal, setShowCleanupModal] = useState(false)
  const [exportFormat, setExportFormat] = useState<'csv' | 'json' | 'txt'>('csv')
  const [isExporting, setIsExporting] = useState(false)

  const handleExport = async (format: 'csv' | 'json' | 'txt') => {
    setIsExporting(true)
    try {
      await onExport(format)
    } finally {
      setIsExporting(false)
    }
  }

  const handleCleanup = async (removeOrphaned: boolean) => {
    try {
      await onCleanup(removeOrphaned)
      setShowCleanupModal(false)
    } catch (error) {
      // Error handled by parent component
    }
  }

  // Calculate health metrics
  const cacheHealth = statistics ? {
    orphanedPercentage: statistics.total_files > 0 ? (statistics.orphaned_files / statistics.total_files) * 100 : 0,
    hitRatioGood: statistics.cache_hit_ratio > 0.8,
    needsCleanup: statistics.orphaned_files > 0
  } : null

  return (
    <div className={classNames('space-y-6', className)}>
      {/* Quick Stats Header */}
      {statistics && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Cache Actions
            </h3>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                {statistics.total_files}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-center">
                <FileText className="w-3 h-3 mr-1" />
                Total Files
              </div>
            </div>
            <div className="text-center">
              <div className="text-xl font-semibold text-green-600 dark:text-green-400">
                {statistics.active_files}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-center">
                <CheckCircle className="w-3 h-3 mr-1" />
                Active
              </div>
            </div>
            <div className="text-center">
              <div className={classNames(
                'text-xl font-semibold',
                statistics.orphaned_files > 0 ? 'text-yellow-600 dark:text-yellow-400' : 'text-gray-600 dark:text-gray-400'
              )}>
                {statistics.orphaned_files}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-center">
                <AlertTriangle className="w-3 h-3 mr-1" />
                Orphaned
              </div>
            </div>
            <div className="text-center">
              <div className={classNames(
                'text-xl font-semibold',
                statistics.cache_hit_ratio > 0.8 ? 'text-green-600 dark:text-green-400' : 
                statistics.cache_hit_ratio > 0.6 ? 'text-yellow-600 dark:text-yellow-400' : 
                'text-red-600 dark:text-red-400'
              )}>
                {(statistics.cache_hit_ratio * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-center">
                <Target className="w-3 h-3 mr-1" />
                Hit Ratio
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Cache Cleanup */}
        <ActionCard
          icon={<Trash2 className="w-5 h-5" />}
          title="Cache Cleanup"
          description={
            statistics && statistics.orphaned_files > 0
              ? `${statistics.orphaned_files} orphaned files detected. Clean up to improve performance.`
              : 'Scan for and remove orphaned cache entries that no longer exist on disk.'
          }
          variant={
            statistics && statistics.orphaned_files > 5 ? 'danger' :
            statistics && statistics.orphaned_files > 0 ? 'warning' : 'default'
          }
          action={
            <button
              onClick={() => setShowCleanupModal(true)}
              disabled={isLoading}
              className={classNames(
                'btn btn-sm',
                statistics && statistics.orphaned_files > 5 ? 'btn-error' :
                statistics && statistics.orphaned_files > 0 ? 'btn-warning' : 'btn-secondary'
              )}
            >
              {isLoading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-1" />
                  Cleanup
                </>
              )}
            </button>
          }
        />

        {/* Export Data */}
        <ActionCard
          icon={<Download className="w-5 h-5" />}
          title="Export Cache Data"
          description="Export cached files information in various formats for analysis or backup purposes."
          variant="info"
          action={
            <div className="flex items-center space-x-2">
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json' | 'txt')}
                className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700"
                disabled={isExporting}
              >
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
                <option value="txt">TXT</option>
              </select>
              <button
                onClick={() => handleExport(exportFormat)}
                disabled={isExporting}
                className="btn btn-sm btn-secondary"
              >
                {isExporting ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <>
                    <Download className="w-4 h-4 mr-1" />
                    Export
                  </>
                )}
              </button>
            </div>
          }
        />

        {/* Cache Health Check */}
        <ActionCard
          icon={<Shield className="w-5 h-5" />}
          title="Cache Health"
          description={
            cacheHealth ? (
              cacheHealth.hitRatioGood && !cacheHealth.needsCleanup
                ? "Cache is performing well with good hit ratio and no orphaned files."
                : `${!cacheHealth.hitRatioGood ? 'Low hit ratio detected. ' : ''}${cacheHealth.needsCleanup ? 'Cleanup recommended. ' : ''}`
            ) : "Analyze cache performance and identify optimization opportunities."
          }
          variant={
            cacheHealth ? (
              cacheHealth.hitRatioGood && !cacheHealth.needsCleanup ? 'success' :
              cacheHealth.orphanedPercentage > 20 || statistics!.cache_hit_ratio < 0.4 ? 'danger' : 'warning'
            ) : 'default'
          }
          action={
            <button className="btn btn-sm btn-primary">
              <BarChart3 className="w-4 h-4 mr-1" />
              Analyze
            </button>
          }
        />

        {/* Quick Refresh */}
        <ActionCard
          icon={<RefreshCw className="w-5 h-5" />}
          title="Refresh Cache Data"
          description="Refresh all cached file information and statistics to ensure data is up to date."
          variant="default"
          action={
            <button 
              className="btn btn-sm btn-secondary"
              disabled={isLoading}
            >
              {isLoading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Refresh
                </>
              )}
            </button>
          }
        />
      </div>

      {/* Health Recommendations */}
      {cacheHealth && (!cacheHealth.hitRatioGood || cacheHealth.needsCleanup) && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                Performance Recommendations
              </h4>
              <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1 list-disc list-inside">
                {!cacheHealth.hitRatioGood && (
                  <li>Consider reviewing caching strategies to improve hit ratio above 80%</li>
                )}
                {cacheHealth.needsCleanup && (
                  <li>Run cache cleanup to remove {statistics?.orphaned_files} orphaned files</li>
                )}
                {cacheHealth.orphanedPercentage > 15 && (
                  <li>High percentage of orphaned files may indicate storage issues</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Cleanup Modal */}
      <CleanupModal
        isOpen={showCleanupModal}
        onClose={() => setShowCleanupModal(false)}
        onConfirm={handleCleanup}
        statistics={statistics}
        isLoading={isLoading}
      />
    </div>
  )
}

export default CacheActionsPanel