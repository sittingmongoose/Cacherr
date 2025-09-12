import React from 'react'
import { 
  HardDrive, 
  Files, 
  Clock, 
  Activity, 
  TrendingUp, 
  Database,
  Zap,
  CheckCircle 
} from 'lucide-react'
import { SystemStatus, CacheStatistics } from '../../types/api'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { formatBytes, formatNumber, formatRelativeTime, classNames } from '../../utils/format'

/**
 * StatsGrid component displays key system metrics in a grid layout
 * 
 * Features:
 * - Responsive grid layout
 * - Loading and error states
 * - Real-time data updates
 * - Accessible design
 * - Visual progress indicators
 */
interface StatsGridProps {
  status?: SystemStatus
  cacheStats?: CacheStatistics
  healthStatus?: any // Add healthStatus prop to match Dashboard usage
  isLoading?: boolean
  error?: string
  className?: string
}

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'red' | 'gray'
  isLoading?: boolean
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = 'blue',
  isLoading = false
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
    green: 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400',
    orange: 'bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400',
    purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400',
    red: 'bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400',
    gray: 'bg-gray-50 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400',
  }

  const trendIcons = {
    up: <TrendingUp className="w-3 h-3 text-green-500" />,
    down: <TrendingUp className="w-3 h-3 text-red-500 transform rotate-180" />,
    neutral: <div className="w-3 h-3" />,
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6 transition-all duration-200 hover:shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <div className={classNames('p-2 rounded-lg', colorClasses[color])}>
              {icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 truncate">
                {title}
              </p>
              <div className="flex items-baseline space-x-2">
                {isLoading ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                    {typeof value === 'number' ? formatNumber(value) : (value || 'N/A')}
                  </p>
                )}
                {trend && trendValue && !isLoading && (
                  <div className="flex items-center space-x-1">
                    {trendIcons[trend]}
                    <span className={classNames(
                      'text-xs font-medium',
                      trend === 'up' ? 'text-green-600' : 
                      trend === 'down' ? 'text-red-600' : 
                      'text-gray-500'
                    )}>
                      {trendValue}
                    </span>
                  </div>
                )}
              </div>
              {subtitle && (
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export const StatsGrid: React.FC<StatsGridProps> = ({
  status,
  cacheStats,
  isLoading = false,
  error,
  className
}) => {
  if (error) {
    return (
      <div className={classNames('bg-error-50 border border-error-200 rounded-xl p-6 dark:bg-error-900/20 dark:border-error-800', className)}>
        <p className="text-error-700 dark:text-error-300 text-center">
          Failed to load statistics: {error}
        </p>
      </div>
    )
  }

  const stats = [
    {
      title: 'Files to Cache',
      value: status?.pending_operations.files_to_cache ?? 0,
      subtitle: 'Pending cache operations',
      icon: <Files className="w-5 h-5" />,
      color: 'blue' as const,
    },
    {
      title: 'Files to Array',
      value: status?.pending_operations.files_to_array ?? 0,
      subtitle: 'Pending array operations',
      icon: <Database className="w-5 h-5" />,
      color: 'green' as const,
    },
    {
      title: 'Cache Size',
      value: cacheStats?.total_size_readable ?? formatBytes(cacheStats?.total_size_bytes ?? 0),
      subtitle: `${formatNumber(cacheStats?.total_files ?? 0)} files`,
      icon: <HardDrive className="w-5 h-5" />,
      color: 'purple' as const,
    },
    {
      title: 'System Status',
      value: status?.status === 'running' ? 'Running' : 'Idle',
      subtitle: status?.scheduler_running ? 'Scheduler active' : 'Scheduler inactive',
      icon: <Activity className="w-5 h-5" />,
      color: (status?.status === 'running' ? 'orange' : 'gray') as 'orange' | 'gray',
    },
    {
      title: 'Last Execution',
      value: status?.last_execution ? 
        (status.last_execution.success ? 'Success' : 'Failed') : 
        'Never',
      subtitle: status?.last_execution?.execution_time ? 
        formatRelativeTime(status.last_execution.execution_time) : 
        'No recent executions',
      icon: status?.last_execution?.success ? 
        <CheckCircle className="w-5 h-5" /> : 
        <Clock className="w-5 h-5" />,
      color: (status?.last_execution?.success ? 'green' : 
             status?.last_execution ? 'red' : 'gray') as 'green' | 'red' | 'gray',
    },
    {
      title: 'Cache Hit Ratio',
      value: cacheStats?.cache_hit_ratio ? 
        `${Math.round(cacheStats.cache_hit_ratio * 100)}%` : 
        'N/A',
      subtitle: 'Cache efficiency',
      icon: <Zap className="w-5 h-5" />,
      color: 'orange' as const,
      trend: (cacheStats?.cache_hit_ratio && cacheStats.cache_hit_ratio > 0.8 ? 'up' : 
             cacheStats?.cache_hit_ratio && cacheStats.cache_hit_ratio < 0.5 ? 'down' : 
             'neutral') as 'up' | 'down' | 'neutral',
      trendValue: cacheStats?.cache_hit_ratio ? 
        (cacheStats.cache_hit_ratio > 0.8 ? 'Excellent' : 
         cacheStats.cache_hit_ratio > 0.6 ? 'Good' : 'Poor') : 
        undefined,
    },
  ]

  return (
    <div className={className}>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          System Overview
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Real-time statistics and performance metrics
        </p>
      </div>
      
      <div className="stats-grid">
        {stats.map((stat, index) => (
          <StatCard
            key={stat.title}
            title={stat.title}
            value={stat.value}
            subtitle={stat.subtitle}
            icon={stat.icon}
            color={stat.color}
            trend={stat.trend}
            trendValue={stat.trendValue}
            isLoading={isLoading}
          />
        ))}
      </div>

      {/* Additional Statistics Section */}
      {(cacheStats || status?.last_execution) && !isLoading && (
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Summary */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
              Performance Summary
            </h3>
            <div className="space-y-3">
              {status?.last_execution?.duration_seconds && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Last Operation Duration</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {Math.round(status.last_execution.duration_seconds)}s
                  </span>
                </div>
              )}
              {cacheStats?.last_updated && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Stats Last Updated</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {formatRelativeTime(cacheStats.last_updated)}
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total Pending Files</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {formatNumber(
                    (status?.pending_operations.files_to_cache ?? 0) + 
                    (status?.pending_operations.files_to_array ?? 0)
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* System Health */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-soft border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
              System Health
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Cache System</span>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-green-600 dark:text-green-400">
                    Healthy
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Scheduler</span>
                <div className="flex items-center space-x-2">
                  <div className={classNames(
                    'w-2 h-2 rounded-full',
                    status?.scheduler_running ? 'bg-green-500' : 'bg-gray-400'
                  )}></div>
                  <span className={classNames(
                    'text-sm font-medium',
                    status?.scheduler_running ? 
                      'text-green-600 dark:text-green-400' : 
                      'text-gray-500 dark:text-gray-400'
                  )}>
                    {status?.scheduler_running ? 'Running' : 'Stopped'}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Overall Status</span>
                <div className="flex items-center space-x-2">
                  <div className={classNames(
                    'w-2 h-2 rounded-full',
                    status?.status === 'running' ? 'bg-blue-500' :
                    status?.status === 'error' ? 'bg-red-500' :
                    'bg-gray-400'
                  )}></div>
                  <span className={classNames(
                    'text-sm font-medium capitalize',
                    status?.status === 'running' ? 'text-blue-600 dark:text-blue-400' :
                    status?.status === 'error' ? 'text-red-600 dark:text-red-400' :
                    'text-gray-500 dark:text-gray-400'
                  )}>
                    {status?.status ?? 'Unknown'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StatsGrid