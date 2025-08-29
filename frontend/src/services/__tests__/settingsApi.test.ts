/**
 * Test file for Settings API Service
 * 
 * Tests the Settings API service functionality with mock backend responses.
 * This ensures all endpoints are properly configured and error handling works correctly.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import SettingsAPIService from '../settingsApi'
import { APIError } from '../api'
import type { 
  ConfigurationSettings, 
  ValidationResult, 
  ConnectivityCheckResult 
} from '@/types/api'

// Mock fetch globally
global.fetch = vi.fn()

// Mock configuration data
const mockConfig: ConfigurationSettings = {
  plex: {
    url: 'http://localhost:32400',
    token: 'test-token-12345',
    username: 'testuser',
    password: undefined
  },
  media: {
    copy_to_cache: true,
    delete_from_cache_when_done: false,
    watched_move: true,
    users_toggle: true,
    watchlist_toggle: true,
    exit_if_active_session: false,
    days_to_monitor: 7,
    number_episodes: 5,
    watchlist_episodes: 10,
    watchlist_cache_expiry: 24,
    watched_cache_expiry: 72,
    cache_mode_description: 'Smart caching enabled'
  },
  paths: {
    plex_source: '/mnt/plex',
    cache_destination: '/mnt/cache',
    additional_sources: [],
    additional_plex_sources: []
  },
  performance: {
    max_concurrent_moves_cache: 2,
    max_concurrent_moves_array: 4,
    max_concurrent_local_transfers: 3,
    max_concurrent_network_transfers: 2,
    enable_monitoring: true
  },
  real_time_watch: {
    enabled: true,
    check_interval: 30,
    auto_cache_on_watch: true,
    cache_on_complete: false,
    respect_existing_rules: true,
    max_concurrent_watches: 5,
    remove_from_cache_after_hours: 48,
    respect_other_users_watchlists: true,
    exclude_inactive_users_days: 30
  },
  trakt: {
    enabled: false,
    client_id: '',
    client_secret: '',
    trending_movies_count: 20,
    check_interval: 3600
  },
  web: {
    host: '0.0.0.0',
    port: 5000,
    debug: false,
    enable_scheduler: true
  },
  test_mode: {
    enabled: false,
    show_file_sizes: true,
    show_total_size: true,
    dry_run: false
  },
  notifications: {
    type: 'none'
  },
  logging: {
    level: 'INFO',
    max_files: 5,
    max_size_mb: 10
  },
  debug: false
}

const mockValidationResult: ValidationResult = {
  valid: true,
  errors: [],
  warnings: [],
  sections: {
    plex: {
      valid: true,
      errors: [],
      model_class: 'PlexSettings'
    },
    media: {
      valid: true,
      errors: [],
      model_class: 'MediaSettings'
    }
  },
  message: 'Configuration is valid'
}

const mockConnectivityResult: ConnectivityCheckResult = {
  status: 'success',
  url: 'http://localhost:32400',
  response_time_ms: 156,
  status_code: 200
}

// Helper to create mock successful response
const createMockResponse = (data: any, success = true): Partial<Response> => ({
  ok: true,
  status: 200,
  headers: new Headers(),
  redirected: false,
  statusText: 'OK',
  type: 'basic',
  url: '',
  json: vi.fn().mockResolvedValue({
    success,
    data,
    timestamp: new Date().toISOString()
  })
})

// Helper to create mock error response
const createMockErrorResponse = (status: number, error: string): Partial<Response> => ({
  ok: false,
  status,
  headers: new Headers(),
  redirected: false,
  statusText: status === 400 ? 'Bad Request' : status === 500 ? 'Internal Server Error' : 'Error',
  type: 'basic',
  url: '',
  json: vi.fn().mockResolvedValue({
    success: false,
    error,
    timestamp: new Date().toISOString()
  })
})

describe('SettingsAPIService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('getCurrentConfig', () => {
    it('should successfully fetch current configuration', async () => {
      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockConfig) as Response)

      const result = await SettingsAPIService.getCurrentConfig()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/current',
        expect.objectContaining({
          method: 'GET',
          headers: expect.any(Headers)
        })
      )
      expect(result).toEqual(mockConfig)
    })

    it('should throw APIError when request fails', async () => {
      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockErrorResponse(500, 'Server error') as Response)

      await expect(SettingsAPIService.getCurrentConfig()).rejects.toThrow(APIError)
    }, 10000)
  })

  describe('updateConfig', () => {
    it('should successfully update configuration', async () => {
      const mockUpdateResponse = {
        updated_sections: ['plex'],
        total_updates: 1,
        validation_result: mockValidationResult
      }
      
      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockUpdateResponse) as Response)

      const updateRequest = {
        sections: { plex: { url: 'http://newserver:32400', token: 'new-token' } },
        validate_before_save: true,
        create_backup: true
      }

      const result = await SettingsAPIService.updateConfig(updateRequest)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/update',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(updateRequest),
          headers: expect.any(Headers)
        })
      )
      expect(result).toEqual(mockUpdateResponse)
    })

    it('should throw APIError on validation failure', async () => {
      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockErrorResponse(422, 'Validation failed') as Response)

      const updateRequest = {
        sections: { plex: { url: 'invalid-url', token: 'test-token' } }
      }

      await expect(SettingsAPIService.updateConfig(updateRequest)).rejects.toThrow(APIError)
    })
  })

  describe('validateConfig', () => {
    it('should successfully validate configuration', async () => {
      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockValidationResult) as Response)

      const validationRequest = {
        sections: { plex: mockConfig.plex },
        full_validation: true
      }

      const result = await SettingsAPIService.validateConfig(validationRequest)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/validate',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(validationRequest)
        })
      )
      expect(result).toEqual(mockValidationResult)
    })
  })

  describe('testPlexConnection', () => {
    it('should successfully test Plex connection', async () => {
      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockConnectivityResult) as Response)

      const plexTestRequest = {
        url: 'http://localhost:32400',
        token: 'test-token',
        timeout: 10000
      }

      const result = await SettingsAPIService.testPlexConnection(plexTestRequest)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/test-plex',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(plexTestRequest)
        })
      )
      expect(result).toEqual(mockConnectivityResult)
    })

    it('should handle connection failure', async () => {
      const mockFailedResult = {
        status: 'failed',
        error: 'Connection refused'
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockFailedResult) as Response)

      const result = await SettingsAPIService.testPlexConnection({
        url: 'http://localhost:32400',
        token: 'invalid-token'
      })

      expect(result.status).toBe('failed')
      expect(result.error).toBe('Connection refused')
    })
  })

  describe('exportConfig', () => {
    it('should successfully export configuration', async () => {
      const mockExportData = {
        configuration: mockConfig,
        export_metadata: {
          exported_at: new Date().toISOString(),
          version: '1.0.0',
          sections: ['plex', 'media']
        }
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockExportData) as Response)

      const result = await SettingsAPIService.exportConfig({
        include_secrets: false,
        sections: ['plex', 'media'],
        format: 'json'
      })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/export?include_secrets=false&sections=plex%2Cmedia&format=json',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockExportData)
    })
  })

  describe('importConfig', () => {
    it('should successfully import configuration', async () => {
      const mockImportResponse = {
        imported_sections: ['plex'],
        skipped_sections: [],
        validation_result: mockValidationResult
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockImportResponse) as Response)

      const importRequest = {
        configuration: { plex: mockConfig.plex },
        validate_before_import: true,
        overwrite_existing: true
      }

      const result = await SettingsAPIService.importConfig(importRequest)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/import',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(importRequest)
        })
      )
      expect(result).toEqual(mockImportResponse)
    })
  })

  describe('getConfigSchema', () => {
    it('should successfully fetch configuration schema', async () => {
      const mockSchema = {
        schema: {
          'plex.url': {
            type: 'string',
            title: 'Plex Server URL',
            required: true,
            format: 'uri'
          },
          'plex.token': {
            type: 'string',
            title: 'Plex Token',
            required: true
          }
        },
        sections: {
          plex: ['url', 'token', 'username'],
          media: ['copy_to_cache', 'delete_from_cache_when_done']
        },
        validation_rules: {}
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockSchema) as Response)

      const result = await SettingsAPIService.getConfigSchema()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/schema',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockSchema)
    })
  })

  describe('resetConfig', () => {
    it('should successfully reset configuration', async () => {
      const mockResetResponse = {
        updated_sections: ['plex', 'media'],
        total_updates: 15,
        validation_result: mockValidationResult
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockResetResponse) as Response)

      const result = await SettingsAPIService.resetConfig(['plex', 'media'])

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/reset',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ sections: ['plex', 'media'] })
        })
      )
      expect(result).toEqual(mockResetResponse)
    })

    it('should reset all sections when no specific sections provided', async () => {
      const mockResetResponse = {
        updated_sections: Object.keys(mockConfig),
        total_updates: 50,
        validation_result: mockValidationResult
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockResetResponse) as Response)

      const result = await SettingsAPIService.resetConfig()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/reset',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({})
        })
      )
      expect(result).toEqual(mockResetResponse)
    })
  })

  describe('validatePersistence', () => {
    it('should successfully validate persistence', async () => {
      const mockPersistenceResult = {
        persistence_working: true,
        config_file_exists: true,
        config_file_writable: true,
        test_write_successful: true
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockPersistenceResult) as Response)

      const result = await SettingsAPIService.validatePersistence()

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/validate-persistence',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockPersistenceResult)
    })

    it('should handle persistence failures', async () => {
      const mockPersistenceResult = {
        persistence_working: false,
        config_file_exists: true,
        config_file_writable: false,
        test_write_successful: false,
        error_details: 'Permission denied: /config/settings.json'
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockPersistenceResult) as Response)

      const result = await SettingsAPIService.validatePersistence()

      expect(result.persistence_working).toBe(false)
      expect(result.error_details).toContain('Permission denied')
    })
  })

  describe('convenience methods', () => {
    it('should update Plex config with convenience method', async () => {
      const mockUpdateResponse = {
        updated_sections: ['plex'],
        total_updates: 1,
        validation_result: mockValidationResult
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockUpdateResponse) as Response)

      const plexUpdate = { url: 'http://newserver:32400', token: 'updated-token' }
      const result = await SettingsAPIService.updatePlexConfig(plexUpdate)

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/config/update',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            sections: { plex: plexUpdate },
            validate_before_save: true,
            create_backup: true
          })
        })
      )
      expect(result).toEqual(mockUpdateResponse)
    })

    it('should perform quick Plex test using current config', async () => {
      const mockFetch = vi.mocked(fetch)
      
      // First call to get current config
      mockFetch.mockResolvedValueOnce(createMockResponse(mockConfig) as Response)
      
      // Second call to test Plex connection
      mockFetch.mockResolvedValueOnce(createMockResponse(mockConnectivityResult) as Response)

      const result = await SettingsAPIService.quickPlexTest()

      expect(mockFetch).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockConnectivityResult)
    })
  })

  describe('error handling', () => {
    it('should retry failed requests up to 3 times', async () => {
      const mockFetch = vi.mocked(fetch)
      
      // Fail 3 times, then succeed
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(createMockResponse(mockConfig) as Response)

      const result = await SettingsAPIService.getCurrentConfig()
      
      expect(mockFetch).toHaveBeenCalledTimes(4)
      expect(result).toEqual(mockConfig)
    }, 15000)

    it('should not retry 4xx client errors', async () => {
      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockErrorResponse(400, 'Bad request') as Response)

      await expect(SettingsAPIService.getCurrentConfig()).rejects.toThrow(APIError)
      expect(mockFetch).toHaveBeenCalledTimes(1) // Should not retry
    })

    it('should provide specific error messages for different status codes', async () => {
      const testCases = [
        { status: 500, expectedMessage: 'Settings operation failed. The backend service may be experiencing issues.' },
        { status: 503, expectedMessage: 'Settings service temporarily unavailable. The backend is starting up or restarting.' },
        { status: 404, expectedMessage: 'Settings endpoint not found. The requested configuration resource does not exist.' },
        { status: 422, expectedMessage: 'Settings validation failed. Please correct the configuration errors.' }
      ]

      for (const testCase of testCases) {
        const mockFetch = vi.mocked(fetch)
        mockFetch.mockResolvedValue(createMockErrorResponse(testCase.status, '') as Response)

        try {
          await SettingsAPIService.getCurrentConfig()
          expect.fail('Should have thrown an error')
        } catch (error) {
          expect(error).toBeInstanceOf(APIError)
          expect((error as APIError).message).toBe(testCase.expectedMessage)
        }

        vi.clearAllMocks()
      }
    }, 15000)
  })

  describe('exportConfigAsDownload', () => {
    it('should export configuration as downloadable file', async () => {
      const mockExportData = {
        configuration: mockConfig,
        export_metadata: {
          exported_at: '2024-01-01T12:00:00Z',
          version: '1.0.0',
          sections: ['plex', 'media']
        }
      }

      const mockFetch = vi.mocked(fetch)
      mockFetch.mockResolvedValue(createMockResponse(mockExportData) as Response)

      const result = await SettingsAPIService.exportConfigAsDownload({
        format: 'json',
        minify: false
      })

      expect(result.blob).toBeInstanceOf(Blob)
      expect(result.filename).toMatch(/cacherr-config-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z\.json/)
      
      // Check blob content
      const blobText = await result.blob.text()
      const exportedConfig = JSON.parse(blobText)
      expect(exportedConfig).toEqual(mockConfig)
    })
  })
})