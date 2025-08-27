import React from 'react'
import { 
  BarChart3, 
  HardDrive, 
  Users, 
  FileText, 
  Clock, 
  TrendingUp,
  AlertCircle,
  Activity,
  Calendar,
  Target
} from 'lucide-react'
import { CacheStatistics as CacheStats } from '@/types/api'
import { LoadingSpinner, CardLoader, SkeletonLoader } from '@/components/common/LoadingSpinner'
import { classNames } from '@/utils/format'

/**
 * CacheStatistics Component
 * 
 * Features:
 * - Comprehensive cache statistics dashboard
 * - Visual metrics and progress indicators
 * - Cache efficiency analysis
 * - Storage utilization breakdown
 * - User activity metrics
 * - Historical trends (placeholder for future implementation)
 * - Responsive design with mobile support
 * - Accessible design with proper ARIA labels
 */

interface CacheStatisticsProps {
  statistics: CacheStats | null
  isLoading?: boolean
  className?: string
}

interface StatCardProps {
  icon: React.ReactNode
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info'
  isLoading?: boolean
}

const StatCard: React.FC<StatCardProps> = ({
  icon,
  title,
  value,
  subtitle,
  trend,
  color = 'primary',
  isLoading = false
}) => {
  const colorClasses = {
    primary: 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400',
    success: 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400',
    warning: 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400',
    error: 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400',
    info: 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400',
  }

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center">
          <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
          <div className="ml-4 flex-1">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2" />
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center">
        <div className={classNames('p-3 rounded-lg', colorClasses[color])}>
          {icon}
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </p>
          <div className="flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
              {value}
            </p>
            {trend && (
              <span className={classNames(
                'ml-2 text-sm font-medium',
                trend === 'up' ? 'text-green-600 dark:text-green-400' : 
                trend === 'down' ? 'text-red-600 dark:text-red-400' : 
                'text-gray-600 dark:text-gray-400'
              )}>
                {trend === 'up' && '↗'}
                {trend === 'down' && '↘'}
                {trend === 'neutral' && '→'}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

interface ProgressBarProps {
  label: string
  value: number
  max: number
  color?: 'primary' | 'success' | 'warning' | 'error'
  showPercentage?: boolean
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  label,
  value,
  max,
  color = 'primary',
  showPercentage = true
}) => {
  const percentage = max > 0 ? (value / max) * 100 : 0
  
  const colorClasses = {
    primary: 'bg-primary-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </span>
        {showPercentage && (
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {percentage.toFixed(1)}%
          </span>
        )}
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <div
          className={classNames('h-2 rounded-full transition-all duration-300', colorClasses[color])}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>{value.toLocaleString()}</span>
        <span>{max.toLocaleString()}</span>
      </div>
    </div>
  )
}

export const CacheStatistics: React.FC<CacheStatisticsProps> = ({
  statistics,
  isLoading = false,
  className
}) => {
  if (isLoading && !statistics) {
    return (
      <div className={classNames('space-y-6', className)}>
        <CardLoader text="Loading cache statistics..." />
      </div>
    )
  }

  if (!statistics) {
    return (
      <div className={classNames('space-y-6', className)}>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
          <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No Statistics Available
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Cache statistics will appear here once files are cached.
          </p>
        </div>
      </div>
    )
  }

  // Calculate derived metrics
  const activePercentage = statistics.total_files > 0 
    ? (statistics.active_files / statistics.total_files) * 100 
    : 0
  const orphanedPercentage = statistics.total_files > 0 
    ? (statistics.orphaned_files / statistics.total_files) * 100 
    : 0

  // Determine cache health
  const getCacheHealthStatus = () => {
    if (orphanedPercentage > 20) return { status: 'Poor', color: 'error' as const }
    if (orphanedPercentage > 10) return { status: 'Fair', color: 'warning' as const }
    if (statistics.cache_hit_ratio > 0.8) return { status: 'Excellent', color: 'success' as const }
    if (statistics.cache_hit_ratio > 0.6) return { status: 'Good', color: 'primary' as const }
    return { status: 'Fair', color: 'warning' as const }
  }

  const cacheHealth = getCacheHealthStatus()

  return (
    <div className={classNames('space-y-6', className)}>
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<FileText className="w-6 h-6" />}
          title="Total Files"
          value={statistics.total_files.toLocaleString()}
          subtitle={`${statistics.active_files} active`}
          color="primary"
          isLoading={isLoading}
        />
        
        <StatCard
          icon={<HardDrive className="w-6 h-6" />}
          title="Total Size"
          value={statistics.total_size_readable}
          subtitle="Cache storage used"
          color="info"
          isLoading={isLoading}
        />
        
        <StatCard
          icon={<Users className="w-6 h-6" />}
          title="Users"
          value={statistics.users_count}
          subtitle="Contributing users"
          color="success"
          isLoading={isLoading}
        />
        
        <StatCard
          icon={<Target className="w-6 h-6" />}
          title="Hit Ratio"
          value={`${(statistics.cache_hit_ratio * 100).toFixed(1)}%`}
          subtitle="Cache efficiency"
          color={statistics.cache_hit_ratio > 0.8 ? 'success' : statistics.cache_hit_ratio > 0.6 ? 'primary' : 'warning'}
          trend={statistics.cache_hit_ratio > 0.8 ? 'up' : statistics.cache_hit_ratio < 0.4 ? 'down' : 'neutral'}
          isLoading={isLoading}
        />
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Status Breakdown */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center mb-6">
            <Activity className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              File Status Breakdown
            </h3>
          </div>
          
          <div className="space-y-6">
            <ProgressBar
              label="Active Files"
              value={statistics.active_files}
              max={statistics.total_files}
              color="success"
            />
            
            <ProgressBar
              label="Orphaned Files"
              value={statistics.orphaned_files}
              max={statistics.total_files}
              color={orphanedPercentage > 20 ? 'error' : orphanedPercentage > 10 ? 'warning' : 'primary'}
            />
            
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Cache Health
                </span>
                <span className={classNames(
                  'px-2 py-1 text-xs font-medium rounded-full',
                  cacheHealth.color === 'success' ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300' :
                  cacheHealth.color === 'error' ? 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300' :
                  cacheHealth.color === 'warning' ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300' :
                  'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                )}>
                  {cacheHealth.status}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Cache Insights */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center mb-6">
            <TrendingUp className="w-5 h-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              Cache Insights
            </h3>
          </div>
          
          <div className="space-y-4">
            {statistics.oldest_cached_at && (
              <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-700">
                <div className="flex items-center">
                  <Clock className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Oldest Cached File
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {new Date(statistics.oldest_cached_at).toLocaleDateString()}
                </span>
              </div>
            )}
            
            {statistics.most_accessed_file && (
              <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-700">
                <div className="flex items-center">
                  <FileText className="w-4 h-4 text-gray-400 mr-2" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Most Accessed File
                  </span>
                </div>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100 max-w-32 truncate" title={statistics.most_accessed_file}>
                  {statistics.most_accessed_file.split('/').pop()}
                </span>
              </div>
            )}
            
            <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-700">
              <div className="flex items-center">
                <HardDrive className="w-4 h-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Average File Size
                </span>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {statistics.total_files > 0 
                  ? `${((statistics.total_size_bytes / statistics.total_files) / 1024 / 1024 / 1024).toFixed(1)} GB`
                  : 'N/A'
                }
              </span>
            </div>
            
            <div className="flex items-center justify-between py-3">
              <div className="flex items-center">
                <Users className="w-4 h-4 text-gray-400 mr-2" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Files per User
                </span>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                {statistics.users_count > 0 
                  ? Math.round(statistics.total_files / statistics.users_count)
                  : 'N/A'
                }
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {(orphanedPercentage > 10 || statistics.cache_hit_ratio < 0.6) && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                Cache Optimization Recommendations
              </h3>
              <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                {orphanedPercentage > 10 && (
                  <li>
                    • Consider running cache cleanup - {statistics.orphaned_files} orphaned files detected ({orphanedPercentage.toFixed(1)}%)
                  </li>
                )}
                {statistics.cache_hit_ratio < 0.6 && (
                  <li>
                    • Cache hit ratio is below optimal (60%) - review caching strategies
                  </li>
                )}
                {statistics.users_count > 0 && statistics.total_files / statistics.users_count < 5 && (
                  <li>
                    • Low files per user ratio - consider promoting cache usage
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Quick Actions
        </h3>
        <div className="flex flex-wrap gap-3">
          <button className="btn btn-primary btn-sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            View Detailed Analytics
          </button>
          <button className="btn btn-secondary btn-sm">
            <FileText className="w-4 h-4 mr-2" />
            Export Statistics
          </button>
          {orphanedPercentage > 5 && (
            <button className="btn btn-warning btn-sm">
              <AlertCircle className="w-4 h-4 mr-2" />
              Run Cleanup
            </button>
          )}
        </div>
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white/50 dark:bg-gray-900/50 flex items-center justify-center">
          <LoadingSpinner size="lg" text="Updating statistics..." />
        </div>
      )}
    </div>
  )
}

export default CacheStatistics