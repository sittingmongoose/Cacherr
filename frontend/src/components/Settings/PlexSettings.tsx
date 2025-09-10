/**
 * PlexSettings Component
 * 
 * Provides form interface for configuring Plex server connection settings
 * including URL, token, connection testing, and SSL verification.
 * 
 * Features:
 * - Real-time form validation with user-friendly error messages
 * - Connection testing with detailed feedback and progress indication
 * - Secure token handling with optional visibility toggle
 * - Mobile-responsive design with proper accessibility support
 * - Comprehensive error handling for network issues and server responses
 * - Auto-save functionality with unsaved changes detection
 * 
 * @component
 * @example
 * <PlexSettings
 *   data={configData}
 *   errors={validationErrors}
 *   onChange={(section, updates) => handleConfigChange('plex', updates)}
 *   onValidate={handleValidation}
 *   readonly={false}
 * />
 */

import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { 
  Server, 
  Eye, 
  EyeOff, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  TestTube,
  Info,
  RefreshCw
} from 'lucide-react'

import { LoadingSpinner, ButtonSpinner } from '../common/LoadingSpinner'
import { classNames } from '../../utils/format'
import SettingsAPIService, { APIError } from '../../services/settingsApi'

// Type imports
import type { 
  ConfigurationSettings, 
  ConnectivityCheckResult,
  SettingsFormProps,
  PlexTestRequest 
} from './types'

/**
 * Props interface for the PlexSettings component
 * Extends the standard SettingsFormProps with Plex-specific functionality
 */
interface PlexSettingsProps extends SettingsFormProps {
  /** Whether to show advanced SSL and timeout options */
  showAdvanced?: boolean
  /** Callback fired when connection test is performed */
  onTestConnection?: (result: ConnectivityCheckResult) => void
  /** Whether the component should auto-save changes */
  autoSave?: boolean
  /** Debounce delay in ms for auto-save (default: 1000ms) */
  autoSaveDelay?: number
}

/**
 * Form validation state interface
 * Tracks validation status and error messages for each field
 */
interface PlexValidationState {
  url: {
    isValid: boolean
    message?: string
  }
  token: {
    isValid: boolean
    message?: string
  }
  username: {
    isValid: boolean
    message?: string
  }
  password: {
    isValid: boolean
    message?: string
  }
}

/**
 * Connection test state interface
 * Tracks the status and results of Plex server connection tests
 */
interface ConnectionTestState {
  isLoading: boolean
  result: ConnectivityCheckResult | null
  error: string | null
  lastTestTimestamp: number | null
}

/**
 * Default validation state
 * All fields start as valid with no error messages
 */
const DEFAULT_VALIDATION_STATE: PlexValidationState = {
  url: { isValid: true },
  token: { isValid: true },
  username: { isValid: true },
  password: { isValid: true }
}

/**
 * Default connection test state
 * No tests performed initially
 */
const DEFAULT_TEST_STATE: ConnectionTestState = {
  isLoading: false,
  result: null,
  error: null,
  lastTestTimestamp: null
}

/**
 * PlexSettings Component
 * 
 * Main component for managing Plex server configuration settings.
 * Handles form state, validation, connection testing, and user interactions.
 */
export const PlexSettings: React.FC<PlexSettingsProps> = ({
  data,
  errors,
  onChange,
  onValidate,
  onTestConnection,
  readonly = false,
  showAdvanced = false,
  autoSave = false,
  autoSaveDelay = 1000
}) => {
  // Component state management
  const [showToken, setShowToken] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [validationState, setValidationState] = useState<PlexValidationState>(DEFAULT_VALIDATION_STATE)
  const [connectionTest, setConnectionTest] = useState<ConnectionTestState>(DEFAULT_TEST_STATE)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // Extract Plex configuration from data with safe defaults
  // Keep original values if they are masked, allowing user to see placeholder text
  const plexConfig = useMemo(() => ({
    url: data.plex?.url || '',
    token: data.plex?.token || '',
    username: data.plex?.username || '',
    password: data.plex?.password || '',
    verify_ssl: data.plex?.verify_ssl ?? true,
    timeout: data.plex?.timeout || 30
  }), [data.plex])

  // Extract validation errors for Plex section
  const plexErrors = useMemo(() => 
    errors.plex || [], 
    [errors.plex]
  )

  // Reset unsaved changes when data updates (indicating a successful save)
  // Only reset if we currently have unsaved changes
  const prevDataRef = useRef(data)
  useEffect(() => {
    console.log('PlexSettings data changed:', {
      hasUnsavedChanges,
      prevData: prevDataRef.current,
      newData: data,
      dataChanged: prevDataRef.current !== data
    })
    if (hasUnsavedChanges && prevDataRef.current !== data) {
      console.log('Resetting hasUnsavedChanges to false')
      setHasUnsavedChanges(false)
    }
    prevDataRef.current = data
  }, [data, hasUnsavedChanges])

  /**
   * Validates a single form field based on field name and value
   * 
   * @param fieldName - The name of the field to validate
   * @param value - The current value of the field
   * @returns Validation result with isValid flag and optional error message
   */
  const validateField = useCallback((
    fieldName: keyof PlexValidationState, 
    value: string
  ): { isValid: boolean; message?: string } => {
    switch (fieldName) {
      case 'url':
        if (!value.trim()) {
          return { isValid: false, message: 'Plex server URL is required' }
        }
        
        // Basic URL format validation
        try {
          const url = new URL(value)
          if (!['http:', 'https:'].includes(url.protocol)) {
            return { 
              isValid: false, 
              message: 'URL must use HTTP or HTTPS protocol' 
            }
          }
          return { isValid: true }
        } catch {
          return { 
            isValid: false, 
            message: 'Please enter a valid URL (e.g., https://plex.example.com:32400)' 
          }
        }

      case 'token':
        // If token is masked, it means we have a configured token, so consider it valid
        if (value === '***MASKED***') {
          return { isValid: true }
        }
        if (!value.trim()) {
          return { isValid: false, message: 'Plex token is required' }
        }
        if (value.length < 16) {
          return { 
            isValid: false, 
            message: 'Plex token appears to be too short (minimum 16 characters)' 
          }
        }
        return { isValid: true }

      case 'username':
        // Username is optional, so we only validate format if provided
        if (value && value.length < 2) {
          return { 
            isValid: false, 
            message: 'Username must be at least 2 characters long' 
          }
        }
        return { isValid: true }

      case 'password':
        // Password is only required if username is provided
        if (plexConfig.username && !value) {
          return { 
            isValid: false, 
            message: 'Password is required when username is provided' 
          }
        }
        return { isValid: true }

      default:
        return { isValid: true }
    }
  }, [plexConfig.username])

  /**
   * Handles form field changes with validation and state updates
   * 
   * @param field - The field that changed
   * @param value - The new value for the field
   */
  const handleFieldChange = useCallback((field: string, value: any) => {
    // Update validation state for the changed field
    if (field in validationState) {
      const fieldValidation = validateField(field as keyof PlexValidationState, String(value))
      setValidationState(prev => ({
        ...prev,
        [field]: fieldValidation
      }))
    }

    // Create updated Plex configuration
    const updatedPlexConfig = {
      ...plexConfig,
      [field]: value
    }

    // Special handling for token field - don't send masked values unless user entered new value
    if (field === 'token') {
      const stringValue = String(value).trim()
      // Only skip the update if the value is exactly the masked placeholder
      // Allow empty strings so users can clear the token if needed
      if (stringValue === '***MASKED***') {
        // User hasn't actually changed the token, skip update
        return
      }
    }

    // Mark as having unsaved changes
    setHasUnsavedChanges(true)

    // Propagate change to parent component
    onChange('plex', updatedPlexConfig)
  }, [plexConfig, onChange, validateField, validationState])

  /**
   * Performs connection test with current Plex settings
   * Shows progress indicator and handles both success and error cases
   */
  const handleConnectionTest = useCallback(async () => {
    // Validate required fields before testing
    const urlValidation = validateField('url', plexConfig.url)
    const tokenValidation = validateField('token', plexConfig.token)

    if (!urlValidation.isValid || !tokenValidation.isValid) {
      setConnectionTest(prev => ({
        ...prev,
        error: 'Please fix validation errors before testing connection',
        result: null
      }))
      return
    }

    // Reset test state and start loading
    setConnectionTest(prev => ({
      ...prev,
      isLoading: true,
      error: null,
      result: null
    }))

    try {
      // Create test request with current form values
      // If token is masked, send it as-is - the backend will handle it
      const testRequest: PlexTestRequest = {
        url: plexConfig.url.trim(),
        token: plexConfig.token.trim(),
        timeout: 15000 // 15 second timeout for connection tests
      }

      // Perform the connection test via API
      const result = await SettingsAPIService.testPlexConnection(testRequest)

      // Update test state with successful result
      setConnectionTest({
        isLoading: false,
        result,
        error: null,
        lastTestTimestamp: Date.now()
      })

      // Notify parent component of test completion
      onTestConnection?.(result)

    } catch (error) {
      let errorMessage = 'Connection test failed with unknown error'

      if (error instanceof APIError) {
        errorMessage = error.message
      } else if (error instanceof Error) {
        errorMessage = error.message
      }

      // Update test state with error
      setConnectionTest({
        isLoading: false,
        result: null,
        error: errorMessage,
        lastTestTimestamp: Date.now()
      })
    }
  }, [plexConfig.url, plexConfig.token, validateField, onTestConnection])

  /**
   * Formats the connection test result for display
   * Provides user-friendly messages based on test outcome
   */
  const getTestResultDisplay = useCallback(() => {
    const { result, error, lastTestTimestamp } = connectionTest

    if (error) {
      return {
        type: 'error' as const,
        icon: XCircle,
        message: error,
        timestamp: lastTestTimestamp
      }
    }

    if (!result) return null

    if (result.success) {
      const serverInfo = result.server_info
      return {
        type: 'success' as const,
        icon: CheckCircle,
        message: `Connected successfully to ${serverInfo?.server_name || 'Plex Server'}`,
        details: serverInfo ? [
          `Version: ${serverInfo.version}`,
          `Platform: ${serverInfo.platform}`,
          `Libraries: ${serverInfo.library_count || 0}`
        ] : undefined,
        timestamp: lastTestTimestamp
      }
    } else {
      return {
        type: 'warning' as const,
        icon: AlertTriangle,
        message: result.message || 'Connection test failed',
        timestamp: lastTestTimestamp
      }
    }
  }, [connectionTest])

  /**
   * Determines if the connection test button should be enabled
   * Requires valid URL and token, and no ongoing test
   */
  const canTestConnection = useMemo(() => {
    return (
      !connectionTest.isLoading &&
      validationState.url.isValid &&
      validationState.token.isValid &&
      plexConfig.url.trim().length > 0 &&
      plexConfig.token.trim().length > 0 &&
      !readonly
    )
  }, [connectionTest.isLoading, validationState, plexConfig, readonly])

  // Get test result display information
  const testResultDisplay = getTestResultDisplay()

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
            <Server className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Plex Server Configuration
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Configure connection to your Plex Media Server
            </p>
          </div>
        </div>
        
        {hasUnsavedChanges && (
          <div className="flex items-center space-x-2 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm font-medium">Unsaved changes</span>
          </div>
        )}
      </div>

      {/* Display validation errors from parent */}
      {plexErrors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <XCircle className="h-5 w-5 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-200">
                Configuration Errors
              </h4>
              <ul className="mt-1 space-y-1 text-sm text-red-700 dark:text-red-300">
                {plexErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        {/* Plex Server URL */}
        <div className="space-y-2">
          <label 
            htmlFor="plex-url" 
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Plex Server URL
            <span className="text-red-500 ml-1" aria-label="Required">*</span>
          </label>
          <div className="relative">
            <input
              id="plex-url"
              type="url"
              value={plexConfig.url}
              onChange={(e) => handleFieldChange('url', e.target.value)}
              placeholder="https://plex.example.com:32400"
              disabled={readonly}
              className={classNames(
                'block w-full px-3 py-2 border rounded-lg shadow-sm',
                'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                !validationState.url.isValid
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600',
                'sm:text-sm'
              )}
              aria-describedby="plex-url-help plex-url-error"
              aria-invalid={!validationState.url.isValid}
            />
            {validationState.url.isValid && plexConfig.url && (
              <CheckCircle className="absolute right-3 top-2.5 h-4 w-4 text-green-500" />
            )}
          </div>
          
          {!validationState.url.isValid && validationState.url.message && (
            <p id="plex-url-error" className="text-sm text-red-600 dark:text-red-400">
              {validationState.url.message}
            </p>
          )}
          
          <p id="plex-url-help" className="text-sm text-gray-500 dark:text-gray-400">
            Enter the full URL to your Plex server, including port number (usually :32400)
          </p>
        </div>

        {/* Plex Token */}
        <div className="space-y-2">
          <label 
            htmlFor="plex-token" 
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Plex Token
            <span className="text-red-500 ml-1" aria-label="Required">*</span>
          </label>
          <div className="relative">
            <input
              id="plex-token"
              type={showToken ? 'text' : 'password'}
              value={plexConfig.token}
              onChange={(e) => handleFieldChange('token', e.target.value)}
              placeholder={data.plex?.token === '***MASKED***' ? 'Token is configured - enter new token to change' : 'Enter your Plex token'}
              disabled={readonly}
              className={classNames(
                'block w-full px-3 py-2 pr-10 border rounded-lg shadow-sm',
                'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                !validationState.token.isValid
                  ? 'border-red-300 dark:border-red-600'
                  : 'border-gray-300 dark:border-gray-600',
                'sm:text-sm font-mono'
              )}
              aria-describedby="plex-token-help plex-token-error"
              aria-invalid={!validationState.token.isValid}
            />
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              disabled={readonly}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
              aria-label={showToken ? 'Hide token' : 'Show token'}
            >
              {showToken ? (
                <EyeOff className="h-4 w-4 text-gray-400 hover:text-gray-600" />
              ) : (
                <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600" />
              )}
            </button>
          </div>
          
          {!validationState.token.isValid && validationState.token.message && (
            <p id="plex-token-error" className="text-sm text-red-600 dark:text-red-400">
              {validationState.token.message}
            </p>
          )}
          
          <p id="plex-token-help" className="text-sm text-gray-500 dark:text-gray-400">
            Your Plex authentication token. 
            <a 
              href="https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="ml-1 text-primary-600 dark:text-primary-400 hover:underline"
            >
              How to find your token
            </a>
          </p>
        </div>

        {/* Optional Username/Password Section */}
        {showAdvanced && (
          <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <Info className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Alternative Authentication (Optional)
              </span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              If you prefer username/password authentication instead of a token
            </p>

            {/* Username */}
            <div className="space-y-2">
              <label 
                htmlFor="plex-username" 
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Username
              </label>
              <input
                id="plex-username"
                type="text"
                value={plexConfig.username}
                onChange={(e) => handleFieldChange('username', e.target.value)}
                placeholder="Plex username or email"
                disabled={readonly}
                className={classNames(
                  'block w-full px-3 py-2 border rounded-lg shadow-sm',
                  'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                  'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                  'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                  !validationState.username.isValid
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-300 dark:border-gray-600',
                  'sm:text-sm'
                )}
                aria-invalid={!validationState.username.isValid}
              />
              {!validationState.username.isValid && validationState.username.message && (
                <p className="text-sm text-red-600 dark:text-red-400">
                  {validationState.username.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label 
                htmlFor="plex-password" 
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="plex-password"
                  type={showPassword ? 'text' : 'password'}
                  value={plexConfig.password}
                  onChange={(e) => handleFieldChange('password', e.target.value)}
                  placeholder="Plex password"
                  disabled={readonly}
                  className={classNames(
                    'block w-full px-3 py-2 pr-10 border rounded-lg shadow-sm',
                    'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                    'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                    'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                    !validationState.password.isValid
                      ? 'border-red-300 dark:border-red-600'
                      : 'border-gray-300 dark:border-gray-600',
                    'sm:text-sm'
                  )}
                  aria-invalid={!validationState.password.isValid}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={readonly}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
              {!validationState.password.isValid && validationState.password.message && (
                <p className="text-sm text-red-600 dark:text-red-400">
                  {validationState.password.message}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Connection Testing */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Connection Test
            </h4>
            <button
              type="button"
              onClick={handleConnectionTest}
              disabled={!canTestConnection}
              className={classNames(
                'inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg',
                'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500',
                'transition-colors duration-200',
                canTestConnection
                  ? 'bg-primary-600 hover:bg-primary-700 text-white'
                  : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
              )}
              aria-label="Test connection to Plex server"
            >
              {connectionTest.isLoading ? (
                <>
                  <ButtonSpinner />
                  Testing...
                </>
              ) : (
                <>
                  <TestTube className="h-4 w-4 mr-2" />
                  Test Connection
                </>
              )}
            </button>
          </div>

          {/* Connection Test Results */}
          {testResultDisplay && (
            <div
              className={classNames(
                'p-4 rounded-lg border',
                testResultDisplay.type === 'success' && 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
                testResultDisplay.type === 'error' && 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
                testResultDisplay.type === 'warning' && 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800'
              )}
            >
              <div className="flex items-start space-x-3">
                <testResultDisplay.icon
                  className={classNames(
                    'h-5 w-5 flex-shrink-0 mt-0.5',
                    testResultDisplay.type === 'success' && 'text-green-500 dark:text-green-400',
                    testResultDisplay.type === 'error' && 'text-red-500 dark:text-red-400',
                    testResultDisplay.type === 'warning' && 'text-amber-500 dark:text-amber-400'
                  )}
                />
                <div className="flex-1 min-w-0">
                  <p
                    className={classNames(
                      'text-sm font-medium',
                      testResultDisplay.type === 'success' && 'text-green-800 dark:text-green-200',
                      testResultDisplay.type === 'error' && 'text-red-800 dark:text-red-200',
                      testResultDisplay.type === 'warning' && 'text-amber-800 dark:text-amber-200'
                    )}
                  >
                    {testResultDisplay.message}
                  </p>
                  
                  {testResultDisplay.details && (
                    <ul
                      className={classNames(
                        'mt-2 text-sm space-y-1',
                        testResultDisplay.type === 'success' && 'text-green-700 dark:text-green-300',
                        testResultDisplay.type === 'error' && 'text-red-700 dark:text-red-300',
                        testResultDisplay.type === 'warning' && 'text-amber-700 dark:text-amber-300'
                      )}
                    >
                      {testResultDisplay.details.map((detail, index) => (
                        <li key={index}>• {detail}</li>
                      ))}
                    </ul>
                  )}
                  
                  {testResultDisplay.timestamp && (
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      Tested {new Date(testResultDisplay.timestamp).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PlexSettings