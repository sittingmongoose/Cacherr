/**
 * API service for Cacherr frontend
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
  CachedFileInfo,
  CacheStatistics,
  UserCacheStatistics,
  CachedFilesFilter,
  CachedFilesResponse,
  CachedFileSearchResponse,
  CacheCleanupRequest,
  CacheCleanupResponse,
  RemoveCachedFileRequest,
  OperationsResponse,
  OperationDetails,
} from '@/types/api'

// API configuration
const API_BASE_URL = '' // Always use relative URLs to go through Vite proxy
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
          
          // Provide more specific error messages based on status code
          let errorMessage = errorData.error || `HTTP ${response.status}`
          
          switch (response.status) {
            case 500:
              errorMessage = errorData.error || 'Internal server error. The backend service may be experiencing issues.'
              break
            case 503:
              errorMessage = 'Service temporarily unavailable. The backend is starting up or restarting.'
              break
            case 502:
              errorMessage = 'Backend service is not responding. Please check if the server is running.'
              break
            case 404:
              errorMessage = 'API endpoint not found. The requested resource does not exist.'
              break
            case 400:
              errorMessage = errorData.error || 'Invalid request. Please check your input.'
              break
          }
          
          throw new APIError(
            errorMessage,
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


  // Cached Files endpoints
  static async getCachedFiles(filter: CachedFilesFilter = {}): Promise<CachedFilesResponse> {
    const params = new URLSearchParams()
    
    // Convert filter to query parameters
    Object.entries(filter).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value))
      }
    })

    const endpoint = `/api/cached/files${params.toString() ? `?${params.toString()}` : ''}`
    const response = await client.get<APIResponse<CachedFilesResponse>>(endpoint)
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get cached files', 500)
    }
    return response.data
  }

  static async getCachedFile(fileId: string): Promise<CachedFileInfo> {
    const response = await client.get<APIResponse<CachedFileInfo>>(`/api/cached/files/${fileId}`)
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get cached file', 500)
    }
    return response.data
  }

  static async removeCachedFile(fileId: string, request: RemoveCachedFileRequest): Promise<{
    file_id: string
    file_path: string
    reason: string
  }> {
    const response = await client.delete<APIResponse<{
      file_id: string
      file_path: string
      reason: string
    }>>(`/api/cached/files/${fileId}`, { 
      body: JSON.stringify(request)
    })
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to remove cached file', 500)
    }
    return response.data
  }

  static async getCacheStatistics(): Promise<CacheStatistics> {
    const response = await client.get<APIResponse<CacheStatistics>>('/api/cached/statistics')
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get cache statistics', 500)
    }
    return response.data
  }

  static async getUserCacheStatistics(userId: string, days: number = 30): Promise<UserCacheStatistics> {
    const response = await client.get<APIResponse<UserCacheStatistics>>(
      `/api/cached/users/${userId}/stats?days=${days}`
    )
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get user cache statistics', 500)
    }
    return response.data
  }

  static async cleanupCache(request: CacheCleanupRequest = {}): Promise<CacheCleanupResponse> {
    const response = await client.post<APIResponse<CacheCleanupResponse>>('/api/cached/cleanup', request)
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to cleanup cache', 500)
    }
    return response.data
  }

  static async searchCachedFiles(
    query: string, 
    searchType: string = 'all', 
    limit: number = 50,
    includeRemoved: boolean = false
  ): Promise<CachedFileSearchResponse> {
    const params = new URLSearchParams({
      q: query,
      type: searchType,
      limit: String(limit),
      include_removed: String(includeRemoved)
    })

    const response = await client.get<APIResponse<CachedFileSearchResponse>>(
      `/api/cached/files/search?${params.toString()}`
    )
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to search cached files', 500)
    }
    return response.data
  }

  static async getOperations(
    limit: number = 50,
    offset: number = 0,
    user_id?: string,
    operation_type?: string,
    start_date?: string,
    end_date?: string,
    active_only: boolean = false
  ): Promise<OperationsResponse> {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
      active_only: String(active_only)
    })

    if (user_id) params.append('user_id', user_id)
    if (operation_type) params.append('operation_type', operation_type)
    if (start_date) params.append('start_date', start_date)
    if (end_date) params.append('end_date', end_date)

    const response = await client.get<APIResponse<OperationsResponse>>(
      `/api/results/operations?${params.toString()}`
    )
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get operations', 500)
    }
    return response.data
  }

  static async getOperationDetails(operationId: string): Promise<OperationDetails> {
    const response = await client.get<APIResponse<OperationDetails>>(
      `/api/results/operations/${operationId}`
    )
    
    if (!response.success || !response.data) {
      throw new APIError(response.error || 'Failed to get operation details', 500)
    }
    return response.data
  }

  static async exportCachedFiles(
    format: 'csv' | 'json' | 'txt' = 'csv',
    filter: Partial<CachedFilesFilter> = {},
    includeMetadata: boolean = false
  ): Promise<Blob> {
    const params = new URLSearchParams({
      format,
      include_metadata: String(includeMetadata)
    })

    // Add filter parameters
    Object.entries(filter).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value))
      }
    })

    const response = await fetch(`${API_BASE_URL}/api/cached/export?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Accept': format === 'csv' ? 'text/csv' : format === 'json' ? 'application/json' : 'text/plain'
      }
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new APIError(
        errorData.error || `Export failed with status ${response.status}`,
        response.status
      )
    }

    return response.blob()
  }
}

// Export the API service as default
export default APIService