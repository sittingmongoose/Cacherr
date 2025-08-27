/**
 * Error handling utilities for the frontend application
 * 
 * Provides consistent error handling patterns and utilities
 * to prevent common runtime errors that trigger error boundaries.
 */

import { APIError } from '@/services/api'

/**
 * Safe data access with fallback values
 */
export function safeGet<T>(obj: any, path: string, fallback: T): T {
  try {
    return path.split('.').reduce((current, key) => current?.[key], obj) ?? fallback
  } catch {
    return fallback
  }
}

/**
 * Safe date parsing with fallback
 */
export function safeParseDate(dateString: string | null | undefined, fallback: Date = new Date()): Date {
  if (!dateString) return fallback
  
  try {
    const parsed = new Date(dateString)
    return isNaN(parsed.getTime()) ? fallback : parsed
  } catch {
    return fallback
  }
}

/**
 * Safe number parsing with fallback
 */
export function safeParseNumber(value: any, fallback: number = 0): number {
  if (typeof value === 'number' && !isNaN(value)) return value
  
  const parsed = Number(value)
  return isNaN(parsed) ? fallback : parsed
}

/**
 * Convert API errors to user-friendly messages
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof APIError) {
    // Handle specific API error codes
    switch (error.errorCode) {
      case 'DATABASE_ERROR':
        return 'Database connection issue. The system is trying to reconnect...'
      case 'PLEX_CONNECTION_ERROR':
        return 'Cannot connect to Plex server. Please check your Plex settings.'
      case 'PERMISSION_ERROR':
        return 'Permission denied. Please check file system permissions.'
      case 'DISK_SPACE_ERROR':
        return 'Insufficient disk space. Please free up some space.'
      default:
        return error.message || 'An unexpected error occurred'
    }
  }
  
  if (error instanceof Error) {
    return error.message
  }
  
  if (typeof error === 'string') {
    return error
  }
  
  return 'An unexpected error occurred'
}

/**
 * Check if an error is recoverable (user can retry)
 */
export function isRecoverableError(error: unknown): boolean {
  if (error instanceof APIError) {
    // 4xx errors are typically not recoverable (client errors)
    if (error.statusCode >= 400 && error.statusCode < 500) {
      return false
    }
    
    // 5xx errors are typically recoverable (server errors)
    if (error.statusCode >= 500) {
      return true
    }
    
    // Specific error codes that are recoverable
    const recoverableErrors = [
      'DATABASE_ERROR',
      'NETWORK_ERROR',
      'TIMEOUT_ERROR',
      'PLEX_CONNECTION_ERROR'
    ]
    
    return recoverableErrors.includes(error.errorCode || '')
  }
  
  // Network errors, timeout errors are typically recoverable
  if (error instanceof Error) {
    const networkErrors = ['NetworkError', 'TimeoutError', 'AbortError']
    return networkErrors.some(type => error.name === type)
  }
  
  return true // Default to recoverable
}

/**
 * Retry function with exponential backoff
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: Error
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      
      if (attempt === maxRetries || !isRecoverableError(error)) {
        throw error
      }
      
      // Exponential backoff with jitter
      const delay = initialDelay * Math.pow(2, attempt) + Math.random() * 1000
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  throw lastError!
}

/**
 * Safe async function wrapper that catches errors
 */
export function safeAsync<T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  onError?: (error: Error) => void
) {
  return async (...args: T): Promise<R | null> => {
    try {
      return await fn(...args)
    } catch (error) {
      console.error('Safe async error:', error)
      if (onError) {
        onError(error as Error)
      }
      return null
    }
  }
}

/**
 * React error boundary error reporting
 */
export function reportError(error: Error, errorInfo?: any) {
  const errorReport = {
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    userAgent: navigator.userAgent,
    errorInfo,
  }
  
  // In development, log to console
  if (process.env.NODE_ENV === 'development') {
    console.group('🚨 Error Report')
    console.error('Error:', error)
    console.error('Full Report:', errorReport)
    console.groupEnd()
  }
  
  // In production, send to error reporting service
  // Example: sendToSentry(errorReport)
  
  return errorReport
}

/**
 * Validate API response structure
 */
export function isValidAPIResponse<T>(response: any): response is { success: boolean; data?: T; error?: string } {
  return (
    typeof response === 'object' &&
    response !== null &&
    typeof response.success === 'boolean'
  )
}

/**
 * Component error boundary hook for functional components
 */
export function useErrorHandler() {
  return (error: Error, errorInfo?: any) => {
    reportError(error, errorInfo)
    
    // You could also dispatch to global error state here
    // or trigger a toast notification
  }
}