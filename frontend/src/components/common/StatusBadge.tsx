import React from 'react'
import { classNames, getStatusVariant } from '@/utils/format'

/**
 * StatusBadge component for displaying status indicators
 * 
 * Features:
 * - Multiple variants (success, warning, error, default)
 * - Optional pulse animation for active states
 * - Accessible design with proper color contrast
 * - Support for custom icons
 */
interface StatusBadgeProps {
  status: string
  variant?: 'success' | 'warning' | 'error' | 'default'
  pulse?: boolean
  size?: 'sm' | 'md' | 'lg'
  icon?: React.ReactNode
  className?: string
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant,
  pulse = false,
  size = 'md',
  icon,
  className
}) => {
  const badgeVariant = variant || getStatusVariant(status)
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
  }

  const variantClasses = {
    success: 'bg-success-100 text-success-800 dark:bg-success-900/30 dark:text-success-300',
    warning: 'bg-warning-100 text-warning-800 dark:bg-warning-900/30 dark:text-warning-300',
    error: 'bg-error-100 text-error-800 dark:bg-error-900/30 dark:text-error-300',
    default: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  }

  const badgeClasses = classNames(
    'inline-flex items-center font-medium rounded-full',
    sizeClasses[size],
    variantClasses[badgeVariant],
    pulse && 'animate-pulse',
    className
  )

  return (
    <span className={badgeClasses} role="status" aria-label={`Status: ${status}`}>
      {icon && (
        <span className="mr-1.5" aria-hidden="true">
          {icon}
        </span>
      )}
      <span className="capitalize">
        {status.replace(/_/g, ' ')}
      </span>
    </span>
  )
}

/**
 * HealthIndicator component for service health status
 */
interface HealthIndicatorProps {
  status: 'healthy' | 'unhealthy' | 'unknown' | 'not_configured'
  label: string
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const HealthIndicator: React.FC<HealthIndicatorProps> = ({
  status,
  label,
  showLabel = true,
  size = 'md',
  className
}) => {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  }

  const statusClasses = {
    healthy: 'bg-success-500',
    unhealthy: 'bg-error-500',
    unknown: 'bg-gray-400',
    not_configured: 'bg-warning-500',
  }

  const statusLabels = {
    healthy: 'Healthy',
    unhealthy: 'Unhealthy',
    unknown: 'Unknown',
    not_configured: 'Not Configured',
  }

  return (
    <div className={classNames('flex items-center', className)}>
      <div
        className={classNames(
          'rounded-full flex-shrink-0',
          sizeClasses[size],
          statusClasses[status]
        )}
        role="status"
        aria-label={`${label}: ${statusLabels[status]}`}
      />
      {showLabel && (
        <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
          {label}: {statusLabels[status]}
        </span>
      )}
    </div>
  )
}

/**
 * OperationStatusBadge for specific operation states
 */
interface OperationStatusBadgeProps {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress?: number
  className?: string
}

export const OperationStatusBadge: React.FC<OperationStatusBadgeProps> = ({
  status,
  progress,
  className
}) => {
  const getIcon = () => {
    switch (status) {
      case 'pending':
        return '⏳'
      case 'running':
        return '🔄'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      case 'cancelled':
        return '⏹️'
      default:
        return null
    }
  }

  const variant = (() => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
      case 'cancelled':
        return 'error'
      case 'running':
        return 'warning'
      default:
        return 'default'
    }
  })()

  return (
    <div className="flex flex-col items-start space-y-1">
      <StatusBadge
        status={status}
        variant={variant}
        pulse={status === 'running'}
        icon={getIcon()}
        className={className}
      />
      {status === 'running' && progress !== undefined && (
        <div className="w-full bg-gray-200 rounded-full h-1.5 dark:bg-gray-700">
          <div
            className="bg-primary-600 h-1.5 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Operation progress: ${progress}%`}
          />
        </div>
      )}
    </div>
  )
}

export default StatusBadge