/**
 * API service for PlexCacheUltra frontend
 * 
 * Provides type-safe API communication with the Flask backend,
 * including error handling, retry logic, and response transformation.
 */

import {
  APIResponse,
  SystemStatus,
  HealthStatus,
  LogsResponse,
  TestResults,
  ConfigurationSettings,
  ValidationResult,
  RunOperationRequest,
  SettingsUpdateRequest,
  SettingsValidationRequest,
} from '@/types/api'

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const DEFAULT_TIMEOUT = 10000 // 10 seconds

// Custom error class for API errors
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorCode?: string,
    public details?: unknown
  ) {
    super(message)
    this.name = 'APIError'
  }
}

// Request options interface
interface RequestOptions extends RequestInit {
  timeout?: number
  retries?: number
  retryDelay?: number
}

// HTTP client with error handling and retries
class HTTPClient {
  private baseURL: string
  private defaultTimeout: number

  constructor(baseURL: string = API_BASE_URL, timeout: number = DEFAULT_TIMEOUT) {
    this.baseURL = baseURL
    this.defaultTimeout = timeout
  }

  async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const {
      timeout = this.defaultTimeout,
      retries = 3,
      retryDelay = 1000,
      ...fetchOptions
    } = options

    const url = `${this.baseURL}${endpoint}`
    
    // Default headers
    const headers = new Headers({
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    })

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    let lastError: Error

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...fetchOptions,
          headers,
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new APIError(
            errorData.error || `HTTP ${response.status}`,
            response.status,
            errorData.error_code,
            errorData
          )
        }

        const data = await response.json()
        return data as T

      } catch (error) {
        lastError = error as Error
        
        if (error instanceof APIError) {
          // Don't retry client errors (4xx)
          if (error.statusCode >= 400 && error.statusCode < 500) {
            throw error
          }
        }

        if (attempt < retries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)))
          continue
        }
      }
    }

    clearTimeout(timeoutId)
    throw lastError!
  }

  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' })
  }

  async post<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(endpoint: string, data?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' })
  }
}

// Create HTTP client instance
const client = new HTTPClient()

// API service class
export class APIService {
  // System status endpoints
  static async getSystemStatus(): Promise<SystemStatus> {
    const response = await client.get<APIResponse<SystemStatus>>('/api/status')
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get system status', 500)
    }
    return response.data
  }

  // Health check endpoints
  static async getHealthStatus(): Promise<HealthStatus> {
    const response = await client.get<HealthStatus>('/health/detailed')
    return response
  }

  static async getBasicHealth(): Promise<{ status: string; timestamp: string }> {
    return client.get<{ status: string; timestamp: string }>('/health')
  }

  static async getDependenciesHealth(): Promise<{
    status: string
    dependencies: Record<string, string>
    timestamp: string
  }> {
    return client.get('/health/dependencies')
  }

  static async getReadinessStatus(): Promise<{
    status: string
    critical_services: Record<string, string>
    timestamp: string
  }> {
    return client.get('/ready')
  }

  // Operation endpoints
  static async runCacheOperation(request: RunOperationRequest = {}): Promise<{
    success: boolean
    message: string
    test_mode: boolean
  }> {
    const response = await client.post<APIResponse<{
      test_mode: boolean
      operation_completed: boolean
    }>>('/api/run', request)
    
    if (!response.success) {
      throw new APIError(response.error || 'Operation failed', 500)
    }

    return {
      success: response.success,
      message: response.message || 'Operation completed',
      test_mode: response.data?.test_mode || false,
    }
  }

  static async getTestResults(): Promise<TestResults> {
    const response = await client.get<APIResponse<TestResults>>('/api/test-results')
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get test results', 500)
    }
    return response.data
  }

  // Configuration endpoints
  static async getSettings(): Promise<ConfigurationSettings> {
    const response = await client.get<APIResponse<ConfigurationSettings>>('/api/settings')
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get settings', 500)
    }
    return response.data
  }

  static async updateSettings(request: SettingsUpdateRequest): Promise<{
    updated_variables: Record<string, unknown>
    total_updates: number
  }> {
    const response = await client.post<APIResponse<{
      updated_variables: Record<string, unknown>
      total_updates: number
    }>>('/api/settings', request)
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to update settings', 500)
    }
    return response.data
  }

  static async validateSettings(request: SettingsValidationRequest): Promise<ValidationResult> {
    const response = await client.post<APIResponse<ValidationResult>>('/api/settings/validate', request)
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to validate settings', 500)
    }
    return response.data
  }

  static async resetSettings(): Promise<{
    default_settings: Record<string, string>
    total_reset: number
  }> {
    const response = await client.post<APIResponse<{
      default_settings: Record<string, string>
      total_reset: number
    }>>('/api/settings/reset')
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to reset settings', 500)
    }
    return response.data
  }

  // Scheduler endpoints
  static async startScheduler(): Promise<{ message: string }> {
    const response = await client.post<APIResponse<void>>('/api/scheduler/start')
    if (!response.success) {
      throw new APIError(response.error || 'Failed to start scheduler', 500)
    }
    return { message: response.message || 'Scheduler started' }
  }

  static async stopScheduler(): Promise<{ message: string }> {
    const response = await client.post<APIResponse<void>>('/api/scheduler/stop')
    if (!response.success) {
      throw new APIError(response.error || 'Failed to stop scheduler', 500)
    }
    return { message: response.message || 'Scheduler stopped' }
  }

  // Log endpoints
  static async getLogs(): Promise<LogsResponse> {
    const response = await client.get<APIResponse<LogsResponse>>('/api/logs')
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get logs', 500)
    }
    return response.data
  }

  // Watcher endpoints (placeholder implementations)
  static async startWatcher(): Promise<{ message: string }> {
    const response = await client.post<APIResponse<void>>('/api/watcher/start')
    if (!response.success) {
      throw new APIError(response.error || 'Failed to start watcher', 500)
    }
    return { message: response.message || 'Watcher started' }
  }

  static async stopWatcher(): Promise<{ message: string }> {
    const response = await client.post<APIResponse<void>>('/api/watcher/stop')
    if (!response.success) {
      throw new APIError(response.error || 'Failed to stop watcher', 500)
    }
    return { message: response.message || 'Watcher stopped' }
  }

  static async getWatcherStatus(): Promise<{
    is_watching: boolean
    stats: Record<string, unknown>
  }> {
    const response = await client.get<APIResponse<{
      is_watching: boolean
      stats: Record<string, unknown>
    }>>('/api/watcher/status')
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get watcher status', 500)
    }
    return response.data
  }

  // Trakt endpoints (placeholder implementations)
  static async getTraktStatus(): Promise<{
    stats: Record<string, unknown>
    trending_movies: unknown[]
  }> {
    const response = await client.get<APIResponse<{
      stats: Record<string, unknown>
      trending_movies: unknown[]
    }>>('/api/trakt/status')
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get Trakt status', 500)
    }
    return response.data
  }

  static async startTraktWatcher(): Promise<{ message: string }> {
    const response = await client.post<APIResponse<void>>('/api/trakt/start')
    if (!response.success) {
      throw new APIError(response.error || 'Failed to start Trakt watcher', 500)
    }
    return { message: response.message || 'Trakt watcher started' }
  }

  static async stopTraktWatcher(): Promise<{ message: string }> {
    const response = await client.post<APIResponse<void>>('/api/trakt/stop')
    if (!response.success) {
      throw new APIError(response.error || 'Failed to stop Trakt watcher', 500)
    }
    return { message: response.message || 'Trakt watcher stopped' }
  }
}

// Export the API service as default
export default APIService