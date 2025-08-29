/**
 * Settings API service for Cacherr frontend
 * 
 * Provides type-safe API communication for settings/configuration management
 * with the Flask backend's /api/config/* endpoints. This service handles all
 * settings operations including CRUD operations, validation, testing, and 
 * import/export functionality.
 */

import {
  // Core API types
  APIResponse,
  ConfigurationSettings,
  ValidationResult,
  ConnectivityCheckResult,
} from '@/types/api'

import {
  // Settings-specific types
  SettingsApiResponse,
  SettingsUpdateResponse,
  SettingsValidationResponse,
  SettingsTestPlexResponse,
  SettingsExportResponse,
  SettingsImportResponse,
  SettingsSchemaResponse,
  SettingsPersistenceResponse,
  SettingsUpdateRequest,
  SettingsValidationRequest,
  SettingsImportRequest,
  PlexTestRequest,
  SettingsExportOptions,
  SettingsImportOptions,
} from '@/types/settings'

// Import HTTP client from existing API service
import { APIError } from './api'

// HTTP client configuration
const API_BASE_URL = '' // Use relative URLs for Vite proxy
const DEFAULT_TIMEOUT = 15000 // 15 seconds for settings operations
const EXTENDED_TIMEOUT = 30000 // 30 seconds for import/export operations

// Request options interface
interface RequestOptions extends RequestInit {
  timeout?: number
  retries?: number
  retryDelay?: number
}

// Settings-specific HTTP client class
class SettingsHTTPClient {
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
          
          // Provide specific error messages for settings operations
          let errorMessage = errorData.error || `HTTP ${response.status}`
          
          switch (response.status) {
            case 500:
              errorMessage = errorData.error || 'Settings operation failed. The backend service may be experiencing issues.'
              break
            case 503:
              errorMessage = 'Settings service temporarily unavailable. The backend is starting up or restarting.'
              break
            case 502:
              errorMessage = 'Settings service is not responding. Please check if the server is running.'
              break
            case 404:
              errorMessage = 'Settings endpoint not found. The requested configuration resource does not exist.'
              break
            case 400:
              errorMessage = errorData.error || 'Invalid settings request. Please check your configuration data.'
              break
            case 422:
              errorMessage = errorData.error || 'Settings validation failed. Please correct the configuration errors.'
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
          // Don't retry client errors (4xx) except 408 Request Timeout
          if (error.statusCode >= 400 && error.statusCode < 500 && error.statusCode !== 408) {
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
}

// Create Settings HTTP client instance
const settingsClient = new SettingsHTTPClient()

/**
 * Settings API Service
 * 
 * Provides comprehensive settings management functionality using the
 * correct /api/config/* endpoints. This service replaces the incorrect
 * settings methods in the main API service that used /api/settings.
 */
export class SettingsAPIService {
  
  /**
   * Get Current Configuration
   * Retrieves the current configuration settings from the backend.
   * 
   * @returns Promise<ConfigurationSettings> Current configuration settings
   * @throws APIError If the request fails or returns invalid data
   */
  static async getCurrentConfig(): Promise<ConfigurationSettings> {
    const response = await settingsClient.get<SettingsApiResponse>('/api/config/current')
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to get current configuration', 
        500,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Update Configuration
   * Updates configuration settings with validation and backup options.
   * 
   * @param request - Settings update request with sections to update
   * @returns Promise<SettingsUpdateResponse> Update result with validation details
   * @throws APIError If validation fails or update cannot be applied
   */
  static async updateConfig(request: SettingsUpdateRequest): Promise<SettingsUpdateResponse['data']> {
    const response = await settingsClient.post<SettingsUpdateResponse>(
      '/api/config/update', 
      request
    )
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to update configuration', 
        422,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Validate Configuration
   * Validates configuration sections without saving changes.
   * 
   * @param request - Configuration sections to validate
   * @returns Promise<ValidationResult> Validation result with errors and warnings
   * @throws APIError If validation request fails
   */
  static async validateConfig(request: SettingsValidationRequest): Promise<ValidationResult> {
    const response = await settingsClient.post<SettingsValidationResponse>(
      '/api/config/validate',
      request
    )
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to validate configuration',
        500,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Test Plex Connection
   * Tests connectivity to Plex server with provided credentials.
   * 
   * @param request - Plex server URL, token, and optional timeout
   * @returns Promise<ConnectivityCheckResult> Connection test results
   * @throws APIError If test request fails
   */
  static async testPlexConnection(request: PlexTestRequest): Promise<ConnectivityCheckResult> {
    const response = await settingsClient.post<SettingsTestPlexResponse>(
      '/api/config/test-plex',
      request,
      { timeout: request.timeout || 15000 }
    )
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to test Plex connection',
        500,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Export Configuration
   * Exports current configuration with metadata and optional sections.
   * 
   * @param options - Export options including secrets, sections, and format
   * @returns Promise<SettingsExportResponse['data']> Exported configuration and metadata
   * @throws APIError If export fails
   */
  static async exportConfig(options: SettingsExportOptions = {}): Promise<SettingsExportResponse['data']> {
    const params = new URLSearchParams()
    
    if (options.include_secrets !== undefined) {
      params.append('include_secrets', String(options.include_secrets))
    }
    if (options.sections && options.sections.length > 0) {
      params.append('sections', options.sections.join(','))
    }
    if (options.format) {
      params.append('format', options.format)
    }
    if (options.minify !== undefined) {
      params.append('minify', String(options.minify))
    }

    const endpoint = `/api/config/export${params.toString() ? `?${params.toString()}` : ''}`
    
    const response = await settingsClient.get<SettingsExportResponse>(
      endpoint,
      { timeout: EXTENDED_TIMEOUT }
    )
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to export configuration',
        500,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Import Configuration
   * Imports configuration from provided data with validation and merge options.
   * 
   * @param request - Configuration data and import options
   * @returns Promise<SettingsImportResponse['data']> Import result with validation details
   * @throws APIError If import fails or validation errors occur
   */
  static async importConfig(request: SettingsImportRequest): Promise<SettingsImportResponse['data']> {
    const response = await settingsClient.post<SettingsImportResponse>(
      '/api/config/import',
      request,
      { timeout: EXTENDED_TIMEOUT }
    )
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to import configuration',
        422,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Get Configuration Schema
   * Retrieves the configuration schema for dynamic form generation.
   * 
   * @returns Promise<SettingsSchemaResponse['data']> Configuration schema with field definitions
   * @throws APIError If schema retrieval fails
   */
  static async getConfigSchema(): Promise<SettingsSchemaResponse['data']> {
    const response = await settingsClient.get<SettingsSchemaResponse>('/api/config/schema')
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to get configuration schema',
        500,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Reset Configuration to Defaults
   * Resets all or specific sections of configuration to default values.
   * 
   * @param sections - Optional array of section names to reset (resets all if not provided)
   * @returns Promise<SettingsUpdateResponse['data']> Reset result with updated sections
   * @throws APIError If reset operation fails
   */
  static async resetConfig(sections?: string[]): Promise<SettingsUpdateResponse['data']> {
    const requestData = sections ? { sections } : {}
    
    const response = await settingsClient.post<SettingsUpdateResponse>(
      '/api/config/reset',
      requestData
    )
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to reset configuration',
        500,
        response.error,
        response
      )
    }
    
    return response.data
  }

  /**
   * Validate Persistence Configuration
   * Tests that configuration persistence is working correctly (file system access, etc.)
   * 
   * @returns Promise<SettingsPersistenceResponse['data']> Persistence test results
   * @throws APIError If persistence test fails
   */
  static async validatePersistence(): Promise<SettingsPersistenceResponse['data']> {
    const response = await settingsClient.get<SettingsPersistenceResponse>('/api/config/validate-persistence')
    
    if (!response.success || !response.data) {
      throw new APIError(
        response.error || 'Failed to validate persistence configuration',
        500,
        response.error,
        response
      )
    }
    
    return response.data
  }

  // Utility methods for specific configuration sections

  /**
   * Update Plex Configuration Section
   * Convenience method to update only Plex settings with validation.
   * 
   * @param plexSettings - Plex configuration section
   * @param validate - Whether to validate before saving (default: true)
   * @returns Promise<SettingsUpdateResponse['data']> Update result
   */
  static async updatePlexConfig(
    plexSettings: Partial<ConfigurationSettings['plex']>, 
    validate: boolean = true
  ): Promise<SettingsUpdateResponse['data']> {
    return this.updateConfig({
      sections: { plex: plexSettings as any },
      validate_before_save: validate,
      create_backup: true
    })
  }

  /**
   * Update Media Configuration Section
   * Convenience method to update only media processing settings.
   * 
   * @param mediaSettings - Media configuration section
   * @param validate - Whether to validate before saving (default: true)
   * @returns Promise<SettingsUpdateResponse['data']> Update result
   */
  static async updateMediaConfig(
    mediaSettings: Partial<ConfigurationSettings['media']>,
    validate: boolean = true
  ): Promise<SettingsUpdateResponse['data']> {
    return this.updateConfig({
      sections: { media: mediaSettings as any },
      validate_before_save: validate,
      create_backup: true
    })
  }

  /**
   * Update Performance Configuration Section
   * Convenience method to update only performance settings.
   * 
   * @param performanceSettings - Performance configuration section
   * @param validate - Whether to validate before saving (default: true)
   * @returns Promise<SettingsUpdateResponse['data']> Update result
   */
  static async updatePerformanceConfig(
    performanceSettings: Partial<ConfigurationSettings['performance']>,
    validate: boolean = true
  ): Promise<SettingsUpdateResponse['data']> {
    return this.updateConfig({
      sections: { performance: performanceSettings as any },
      validate_before_save: validate,
      create_backup: true
    })
  }

  /**
   * Validate Multiple Sections
   * Convenience method to validate multiple configuration sections at once.
   * 
   * @param sections - Configuration sections to validate
   * @param fullValidation - Whether to perform full validation (default: true)
   * @returns Promise<ValidationResult> Comprehensive validation result
   */
  static async validateMultipleSections(
    sections: Partial<ConfigurationSettings>,
    fullValidation: boolean = true
  ): Promise<ValidationResult> {
    return this.validateConfig({
      sections,
      full_validation: fullValidation
    })
  }

  /**
   * Quick Plex Test
   * Convenience method to quickly test Plex connection using current settings.
   * 
   * @param timeout - Connection timeout in milliseconds (default: 10000)
   * @returns Promise<ConnectivityCheckResult> Connection test result
   */
  static async quickPlexTest(timeout: number = 10000): Promise<ConnectivityCheckResult> {
    // Get current config first to extract Plex settings
    const currentConfig = await this.getCurrentConfig()
    
    return this.testPlexConnection({
      url: currentConfig.plex.url,
      token: currentConfig.plex.token,
      timeout
    })
  }

  /**
   * Export Configuration as Download
   * Exports configuration and returns a downloadable Blob.
   * 
   * @param options - Export options
   * @returns Promise<{ blob: Blob; filename: string }> Downloadable configuration file
   */
  static async exportConfigAsDownload(
    options: SettingsExportOptions = {}
  ): Promise<{ blob: Blob; filename: string }> {
    const exportData = await this.exportConfig(options)
    
    const format = options.format || 'json'
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `cacherr-config-${timestamp}.${format}`
    
    let content: string
    let mimeType: string
    
    if (format === 'yaml') {
      content = JSON.stringify(exportData.configuration, null, 2) // TODO: Convert to YAML when needed
      mimeType = 'application/x-yaml'
    } else {
      content = options.minify 
        ? JSON.stringify(exportData.configuration)
        : JSON.stringify(exportData.configuration, null, 2)
      mimeType = 'application/json'
    }
    
    const blob = new Blob([content], { type: mimeType })
    
    return { blob, filename }
  }
}

// Export the Settings API service as default
export default SettingsAPIService

// Export individual items for convenient importing
export {
  APIError,
  type SettingsUpdateRequest,
  type SettingsValidationRequest,
  type SettingsImportRequest,
  type PlexTestRequest,
  type SettingsExportOptions,
  type SettingsImportOptions,
}