/**
 * Utility functions for formatting data in the UI.
 * Provides consistent formatting across the application.
 */

/**
 * Format bytes to human-readable format
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes'
  if (bytes < 0) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * Format duration in seconds to human-readable format
 */
export function formatDuration(seconds: number): string {
  if (seconds < 0) return '0s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.round(seconds % 60)
  
  if (hours < 24) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`
  }
  
  const days = Math.floor(hours / 24)
  const remainingHours = hours % 24
  return `${days}d ${remainingHours}h ${minutes}m`
}

/**
 * Format timestamp to relative time (e.g., "2 minutes ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date()
  const target = typeof date === 'string' ? new Date(date) : date
  
  // Check if the date is valid
  if (isNaN(target.getTime())) {
    return 'Invalid date'
  }
  
  const diffMs = now.getTime() - target.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)

  if (diffSeconds < 60) return 'just now'
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} minutes ago`
  if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hours ago`
  if (diffSeconds < 604800) return `${Math.floor(diffSeconds / 86400)} days ago`
  
  return target.toLocaleDateString()
}

/**
 * Format absolute timestamp for display
 */
export function formatTimestamp(date: string | Date, includeTime = true): string {
  const target = typeof date === 'string' ? new Date(date) : date
  
  if (!includeTime) {
    return target.toLocaleDateString()
  }
  
  return target.toLocaleString()
}

/**
 * Format number with thousand separators
 */
export function formatNumber(num: number, decimals = 0): string {
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)
}

/**
 * Format percentage
 */
export function formatPercentage(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * Format file path for display (truncate if too long)
 */
export function formatFilePath(path: string, maxLength = 50): string {
  if (path.length <= maxLength) return path
  
  const parts = path.split('/')
  if (parts.length <= 2) return path
  
  // Try to show beginning and end
  let result = parts[0]
  let endParts = []
  let remainingLength = maxLength - result.length - 3 // Account for "..."
  
  for (let i = parts.length - 1; i > 0 && remainingLength > 0; i--) {
    const part = parts[i]
    if (part.length + 1 <= remainingLength) {
      endParts.unshift(part)
      remainingLength -= part.length + 1
    } else {
      break
    }
  }
  
  return `${result}/.../${endParts.join('/')}`
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number, suffix = '...'): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - suffix.length) + suffix
}

/**
 * Format log level for display
 */
export function formatLogLevel(level: string): string {
  return level.toUpperCase()
}

/**
 * Get appropriate color class for log level
 */
export function getLogLevelColor(level: string): string {
  switch (level.toLowerCase()) {
    case 'error':
      return 'text-error-600'
    case 'warning':
    case 'warn':
      return 'text-warning-600'
    case 'info':
      return 'text-blue-600'
    case 'debug':
      return 'text-gray-500'
    default:
      return 'text-gray-600'
  }
}

/**
 * Get appropriate badge variant for status
 */
export function getStatusVariant(status: string): 'default' | 'success' | 'warning' | 'error' {
  switch (status.toLowerCase()) {
    case 'running':
    case 'running_test':
    case 'active':
    case 'healthy':
    case 'success':
    case 'completed':
      return 'success'
    case 'warning':
    case 'degraded':
    case 'pending':
      return 'warning'
    case 'error':
    case 'failed':
    case 'unhealthy':
      return 'error'
    default:
      return 'default'
  }
}

/**
 * Get health indicator class name
 */
export function getHealthIndicatorClass(status: string): string {
  switch (status.toLowerCase()) {
    case 'healthy':
      return 'health-healthy'
    case 'unhealthy':
      return 'health-unhealthy'
    case 'not_configured':
      return 'health-not-configured'
    default:
      return 'health-unknown'
  }
}

/**
 * Format API error for display
 */
export function formatApiError(error: unknown): string {
  if (typeof error === 'string') return error
  
  if (error && typeof error === 'object' && 'message' in error) {
    return (error as { message: string }).message
  }
  
  if (error instanceof Error) {
    return error.message
  }
  
  return 'An unknown error occurred'
}

/**
 * Format validation errors for display
 */
export function formatValidationErrors(errors: string[]): string {
  if (errors.length === 0) return ''
  if (errors.length === 1) return errors[0]
  
  return `${errors.length} validation errors: ${errors.join(', ')}`
}

/**
 * Generate CSS class names conditionally
 */
export function classNames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

/**
 * Format operation type for display
 */
export function formatOperationType(type: string): string {
  return type.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}