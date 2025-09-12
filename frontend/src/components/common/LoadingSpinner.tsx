import React from 'react'
import { LoadingProps } from '../../types'
import { classNames } from '../../utils/format'

/**
 * LoadingSpinner component with accessibility support
 * 
 * Features:
 * - Multiple sizes (sm, md, lg)
 * - Customizable color
 * - Optional text display
 * - Screen reader support
 * - Smooth animations
 */
interface LoadingSpinnerProps extends LoadingProps {
  inline?: boolean
  center?: boolean
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color,
  text,
  inline = false,
  center = true,
  className,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }

  const containerClasses = classNames(
    'flex items-center',
    center && !inline && 'justify-center',
    inline ? 'inline-flex' : 'flex',
    text && 'space-x-2',
    className
  )

  const spinnerClasses = classNames(
    'animate-spin border-2 border-current border-t-transparent rounded-full',
    sizeClasses[size],
    color ? `text-${color}` : 'text-primary-600'
  )

  return (
    <div className={containerClasses} role="status" aria-live="polite">
      <div 
        className={spinnerClasses}
        aria-hidden="true"
      />
      {text && (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {text}
        </span>
      )}
      <span className="sr-only">
        {text || 'Loading...'}
      </span>
    </div>
  )
}

/**
 * FullPageLoader for page-level loading states
 */
export const FullPageLoader: React.FC<{ text?: string }> = ({ text = 'Loading...' }) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <div className="text-center">
      <LoadingSpinner size="lg" text={text} className="mb-4" />
    </div>
  </div>
)

/**
 * CardLoader for card-level loading states
 */
export const CardLoader: React.FC<{ text?: string; className?: string }> = ({ 
  text = 'Loading...', 
  className 
}) => (
  <div className={classNames('flex items-center justify-center p-8', className)}>
    <LoadingSpinner size="md" text={text} />
  </div>
)

/**
 * Skeleton loader for content placeholders
 */
export const SkeletonLoader: React.FC<{
  lines?: number
  className?: string
  animate?: boolean
}> = ({ 
  lines = 3, 
  className,
  animate = true
}) => (
  <div className={classNames('space-y-3', className)} aria-label="Loading content">
    {Array.from({ length: lines }).map((_, index) => (
      <div
        key={index}
        className={classNames(
          'h-4 bg-gray-200 rounded dark:bg-gray-700',
          animate && 'animate-pulse',
          index === lines - 1 && 'w-3/4' // Last line is shorter
        )}
      />
    ))}
  </div>
)

/**
 * Button loading state
 */
export const ButtonSpinner: React.FC = () => (
  <LoadingSpinner size="sm" inline className="mr-2" />
)