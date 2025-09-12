/**
 * Toast notification system
 * 
 * Features:
 * - Multiple types (success, error, warning, info)
 * - Auto-dismiss with configurable duration
 * - Manual dismiss
 * - Action buttons
 * - Animations
 * - Accessibility support
 * - Stack management
 */

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'
import { ToastOptions } from '../../types/api'
import { classNames } from '../../utils/format'
import { useToasts } from '../../store'

// Toast icon mapping
const toastIcons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

// Toast color mapping
const toastColors = {
  success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200',
  error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-200',
  info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200',
}

const iconColors = {
  success: 'text-green-400 dark:text-green-300',
  error: 'text-red-400 dark:text-red-300',
  warning: 'text-yellow-400 dark:text-yellow-300',
  info: 'text-blue-400 dark:text-blue-300',
}

/**
 * Individual Toast component
 */
interface ToastProps {
  toast: ToastOptions & { id: string }
  onDismiss: (id: string) => void
}

const Toast: React.FC<ToastProps> = ({ toast, onDismiss }) => {
  const [isVisible, setIsVisible] = useState(true)
  const type = toast.type || 'info'
  const Icon = toastIcons[type]

  // Auto-dismiss timer
  useEffect(() => {
    if (toast.duration && toast.duration > 0 && !toast.persistent) {
      const timer = setTimeout(() => {
        setIsVisible(false)
        setTimeout(() => onDismiss(toast.id), 300) // Wait for animation
      }, toast.duration)

      return () => clearTimeout(timer)
    }
  }, [toast.duration, toast.persistent, toast.id, onDismiss])

  const handleDismiss = () => {
    setIsVisible(false)
    setTimeout(() => onDismiss(toast.id), 300)
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: 300, scale: 0.3 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 300, scale: 0.3 }}
          transition={{ duration: 0.3 }}
          className={classNames(
            'max-w-sm w-full border rounded-lg shadow-lg pointer-events-auto overflow-hidden',
            toastColors[type]
          )}
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
        >
          <div className="p-4">
            <div className="flex items-start">
              {/* Icon */}
              <div className="flex-shrink-0">
                <Icon className={classNames('w-5 h-5', iconColors[type])} aria-hidden="true" />
              </div>

              {/* Content */}
              <div className="ml-3 w-0 flex-1">
                {toast.title && (
                  <p className="text-sm font-semibold">
                    {toast.title}
                  </p>
                )}
                <p className={classNames(
                  'text-sm',
                  toast.title ? 'mt-1' : ''
                )}>
                  {toast.message}
                </p>

                {/* Action button */}
                {toast.action && (
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={toast.action.onClick}
                      className={classNames(
                        'text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2',
                        type === 'success' && 'text-green-600 hover:text-green-500 focus:ring-green-500 dark:text-green-400',
                        type === 'error' && 'text-red-600 hover:text-red-500 focus:ring-red-500 dark:text-red-400',
                        type === 'warning' && 'text-yellow-600 hover:text-yellow-500 focus:ring-yellow-500 dark:text-yellow-400',
                        type === 'info' && 'text-blue-600 hover:text-blue-500 focus:ring-blue-500 dark:text-blue-400'
                      )}
                    >
                      {toast.action.label}
                    </button>
                  </div>
                )}
              </div>

              {/* Dismiss button */}
              <div className="ml-4 flex-shrink-0 flex">
                <button
                  type="button"
                  onClick={handleDismiss}
                  className={classNames(
                    'inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2',
                    type === 'success' && 'text-green-400 hover:text-green-500 focus:ring-green-500',
                    type === 'error' && 'text-red-400 hover:text-red-500 focus:ring-red-500',
                    type === 'warning' && 'text-yellow-400 hover:text-yellow-500 focus:ring-yellow-500',
                    type === 'info' && 'text-blue-400 hover:text-blue-500 focus:ring-blue-500'
                  )}
                  aria-label="Dismiss notification"
                >
                  <X className="w-5 h-5" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>

          {/* Progress bar for auto-dismiss */}
          {toast.duration && toast.duration > 0 && !toast.persistent && (
            <motion.div
              className={classNames(
                'h-1',
                type === 'success' && 'bg-green-200 dark:bg-green-800',
                type === 'error' && 'bg-red-200 dark:bg-red-800',
                type === 'warning' && 'bg-yellow-200 dark:bg-yellow-800',
                type === 'info' && 'bg-blue-200 dark:bg-blue-800'
              )}
            >
              <motion.div
                className={classNames(
                  'h-full',
                  type === 'success' && 'bg-green-400 dark:bg-green-600',
                  type === 'error' && 'bg-red-400 dark:bg-red-600',
                  type === 'warning' && 'bg-yellow-400 dark:bg-yellow-600',
                  type === 'info' && 'bg-blue-400 dark:bg-blue-600'
                )}
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: toast.duration / 1000, ease: 'linear' }}
              />
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

/**
 * Toast Container component - manages the stack of toasts
 */
export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToasts()

  if (!toasts || toasts.length === 0) {
    return null
  }

  return (
    <div
      aria-live="assertive"
      className="fixed inset-0 flex items-end justify-center px-4 py-6 pointer-events-none sm:p-6 sm:items-start sm:justify-end z-50"
    >
      <div className="w-full flex flex-col items-center space-y-4 sm:items-end">
        <AnimatePresence>
          {toasts.map((toast) => (
            <Toast
              key={toast.id}
              toast={toast as ToastOptions & { id: string }}
              onDismiss={removeToast}
            />
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}

/**
 * Hook for showing toasts (convenience functions)
 */
export const useToastNotifications = () => {
  const { addToast } = useToasts()

  const showSuccess = (message: string, options?: Partial<ToastOptions>) => {
    addToast({
      type: 'success',
      message,
      duration: 5000,
      ...options,
    })
  }

  const showError = (message: string, options?: Partial<ToastOptions>) => {
    addToast({
      type: 'error',
      message,
      duration: 8000,
      ...options,
    })
  }

  const showWarning = (message: string, options?: Partial<ToastOptions>) => {
    addToast({
      type: 'warning',
      message,
      duration: 6000,
      ...options,
    })
  }

  const showInfo = (message: string, options?: Partial<ToastOptions>) => {
    addToast({
      type: 'info',
      message,
      duration: 5000,
      ...options,
    })
  }

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showToast: addToast,
  }
}

export default Toast