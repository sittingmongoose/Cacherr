/**
 * AdvancedSettings Component
 * 
 * Provides form interface for configuring advanced system features including
 * real-time monitoring, Trakt integration, notifications, and logging settings.
 * 
 * Features:
 * - Real-time watch configuration with interval controls
 * - Trakt.tv API integration settings with validation
 * - Multi-platform notification system configuration
 * - Comprehensive logging level and rotation settings
 * - Mobile-responsive design with proper accessibility support
 * - Advanced validation with service-specific feedback
 * - Collapsible sections for organized configuration management
 * 
 * @component
 * @example
 * <AdvancedSettings
 *   data={configData}
 *   errors={validationErrors}
 *   onChange={(section, updates) => handleConfigChange(section, updates)}
 *   onValidate={handleValidation}
 *   readonly={false}
 * />
 */

import React, { useState, useCallback, useMemo } from 'react'
import { 
  Settings,
  Eye,
  Activity,
  Bell,
  FileText,
  Clock,
  Users,
  Film,
  Webhook,
  Mail,
  MessageSquare,
  Slack,
  AlertTriangle,
  Info,
  CheckCircle,
  ExternalLink,
  Key,
  Shield,
  Database,
  RotateCcw,
  Timer,
  Zap
} from 'lucide-react'

import { LoadingSpinner } from '../common/LoadingSpinner'
import { classNames } from '../../utils/format'

// Type imports
import type { 
  ConfigurationSettings,
  RealTimeWatchSettings,
  TraktSettings,
  NotificationSettings,
  LoggingSettings,
  SettingsFormProps,
  RealTimeWatchFormData,
  TraktSettingsFormData,
  LoggingSettingsFormData,
  NotificationSettingsFormData
} from './types'

/**
 * Props interface for the AdvancedSettings component
 * Extends the standard SettingsFormProps with advanced-specific functionality
 */
interface AdvancedSettingsProps extends SettingsFormProps {
  /** Whether to show experimental features */
  showExperimental?: boolean
  /** Whether the component should auto-save changes */
  autoSave?: boolean
  /** Debounce delay in ms for auto-save (default: 1000ms) */
  autoSaveDelay?: number
}

/**
 * Form validation state interface for advanced settings
 * Tracks validation status and error messages for each section
 */
interface AdvancedValidationState {
  realTimeWatch: {
    isValid: boolean
    messages: string[]
  }
  trakt: {
    isValid: boolean
    messages: string[]
  }
  notifications: {
    isValid: boolean
    messages: string[]
  }
  logging: {
    isValid: boolean
    messages: string[]
  }
}

/**
 * Default validation state - all sections start as valid
 */
const DEFAULT_VALIDATION_STATE: AdvancedValidationState = {
  realTimeWatch: { isValid: true, messages: [] },
  trakt: { isValid: true, messages: [] },
  notifications: { isValid: true, messages: [] },
  logging: { isValid: true, messages: [] }
}

/**
 * Notification type configuration interface
 */
interface NotificationTypeConfig {
  value: string
  label: string
  description: string
  icon: any
  color: string
  requiresUrl?: boolean
  urlField?: string
  requiresConfig?: boolean
}

/**
 * Notification type configurations with platform-specific details
 */
const NOTIFICATION_TYPES: NotificationTypeConfig[] = [
  { 
    value: 'none', 
    label: 'Disabled', 
    description: 'No notifications will be sent',
    icon: Bell,
    color: 'gray'
  },
  { 
    value: 'webhook', 
    label: 'Generic Webhook', 
    description: 'Send JSON payload to any webhook URL',
    icon: Webhook,
    color: 'blue',
    requiresUrl: true,
    urlField: 'webhook_url'
  },
  { 
    value: 'discord', 
    label: 'Discord', 
    description: 'Send notifications to Discord channel',
    icon: MessageSquare,
    color: 'indigo',
    requiresUrl: true,
    urlField: 'discord_webhook_url'
  },
  { 
    value: 'slack', 
    label: 'Slack', 
    description: 'Send notifications to Slack channel',
    icon: Slack,
    color: 'green',
    requiresUrl: true,
    urlField: 'slack_webhook_url'
  },
  { 
    value: 'email', 
    label: 'Email', 
    description: 'Send email notifications (requires SMTP configuration)',
    icon: Mail,
    color: 'red',
    requiresConfig: true
  }
]

/**
 * Logging levels with descriptions and color coding
 */
const LOGGING_LEVELS = [
  { value: 'DEBUG', label: 'Debug', description: 'Detailed diagnostic information', color: 'gray' },
  { value: 'INFO', label: 'Info', description: 'General information messages', color: 'blue' },
  { value: 'WARNING', label: 'Warning', description: 'Warning messages for potential issues', color: 'amber' },
  { value: 'ERROR', label: 'Error', description: 'Error messages for failed operations', color: 'red' },
  { value: 'CRITICAL', label: 'Critical', description: 'Critical errors that may stop the application', color: 'red' }
] as const

/**
 * AdvancedSettings Component
 * 
 * Main component for managing advanced system configuration settings.
 * Handles multiple complex configuration sections with validation.
 */
export const AdvancedSettings: React.FC<AdvancedSettingsProps> = ({
  data,
  errors,
  onChange,
  onValidate,
  readonly = false,
  showExperimental = false,
  autoSave = false,
  autoSaveDelay = 1000
}) => {
  // Component state management
  const [validationState, setValidationState] = useState<AdvancedValidationState>(DEFAULT_VALIDATION_STATE)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['realTimeWatch']))

  // Extract configuration sections from data with safe defaults
  const realTimeWatchConfig = useMemo<RealTimeWatchFormData>(() => ({
    enabled: data.real_time_watch?.enabled ?? false,
    check_interval: data.real_time_watch?.check_interval ?? 300,
    auto_cache_on_watch: data.real_time_watch?.auto_cache_on_watch ?? true,
    cache_on_complete: data.real_time_watch?.cache_on_complete ?? false,
    respect_existing_rules: data.real_time_watch?.respect_existing_rules ?? true,
    max_concurrent_watches: data.real_time_watch?.max_concurrent_watches ?? 3,
    remove_from_cache_after_hours: data.real_time_watch?.remove_from_cache_after_hours ?? 24,
    respect_other_users_watchlists: data.real_time_watch?.respect_other_users_watchlists ?? true,
    exclude_inactive_users_days: data.real_time_watch?.exclude_inactive_users_days ?? 30
  }), [data.real_time_watch])

  const traktConfig = useMemo<TraktSettingsFormData>(() => ({
    enabled: data.trakt?.enabled ?? false,
    client_id: data.trakt?.client_id || '',
    client_secret: data.trakt?.client_secret || '',
    trending_movies_count: data.trakt?.trending_movies_count ?? 20,
    check_interval: data.trakt?.check_interval ?? 3600
  }), [data.trakt])

  const notificationConfig = useMemo<NotificationSettingsFormData>(() => ({
    type: data.notifications?.type ?? 'none',
    webhook_url: data.notifications?.webhook_url || '',
    discord_webhook_url: data.notifications?.discord_webhook_url || '',
    slack_webhook_url: data.notifications?.slack_webhook_url || ''
  }), [data.notifications])

  const loggingConfig = useMemo<LoggingSettingsFormData>(() => ({
    level: data.logging?.level ?? 'INFO',
    max_files: data.logging?.max_files ?? 5,
    max_size_mb: data.logging?.max_size_mb ?? 10
  }), [data.logging])

  // Extract validation errors for advanced sections
  const advancedErrors = useMemo(() => [
    ...(errors.real_time_watch || []),
    ...(errors.trakt || []),
    ...(errors.notifications || []),
    ...(errors.logging || [])
  ], [errors])

  /**
   * Validates URL fields for notification configurations
   * 
   * @param url - URL string to validate
   * @returns Validation result with validity and error message
   */
  const validateUrl = useCallback((url: string): { isValid: boolean; message?: string } => {
    if (!url.trim()) {
      return { isValid: false, message: 'URL is required for this notification type' }
    }

    try {
      const urlObj = new URL(url)
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        return { isValid: false, message: 'URL must use HTTP or HTTPS protocol' }
      }
      return { isValid: true }
    } catch {
      return { isValid: false, message: 'Please enter a valid URL' }
    }
  }, [])

  /**
   * Validates numeric fields with range checking
   * 
   * @param value - Numeric value to validate
   * @param field - Field name for context
   * @param min - Minimum allowed value
   * @param max - Maximum allowed value
   * @returns Validation result
   */
  const validateNumericField = useCallback((
    value: number, 
    field: string,
    min: number = 0,
    max: number = Infinity
  ): { isValid: boolean; message?: string } => {
    if (isNaN(value) || value < min) {
      return { isValid: false, message: `${field} must be at least ${min}` }
    }
    if (value > max) {
      return { isValid: false, message: `${field} cannot exceed ${max}` }
    }
    return { isValid: true }
  }, [])

  /**
   * Handles form field changes with section-specific validation
   * 
   * @param section - The configuration section being updated
   * @param field - The specific field within the section
   * @param value - The new value for the field
   */
  const handleFieldChange = useCallback((
    section: 'real_time_watch' | 'trakt' | 'notifications' | 'logging', 
    field: string, 
    value: any
  ) => {
    let updatedConfig: any
    let validationKey: keyof AdvancedValidationState

    // Handle section-specific updates and validation
    switch (section) {
      case 'real_time_watch':
        updatedConfig = { ...realTimeWatchConfig, [field]: value }
        validationKey = 'realTimeWatch'
        break
      case 'trakt':
        updatedConfig = { ...traktConfig, [field]: value }
        validationKey = 'trakt'
        // Validate Trakt API fields
        if (field === 'client_id' && typeof value === 'string' && value && value.length < 10) {
          setValidationState(prev => ({
            ...prev,
            [validationKey]: {
              isValid: false,
              messages: ['Trakt Client ID appears to be too short']
            }
          }))
        }
        break
      case 'notifications':
        updatedConfig = { ...notificationConfig, [field]: value }
        validationKey = 'notifications'
        // Validate notification URLs
        if (field.includes('url') && typeof value === 'string' && value) {
          const urlValidation = validateUrl(value)
          setValidationState(prev => ({
            ...prev,
            [validationKey]: {
              isValid: urlValidation.isValid,
              messages: urlValidation.isValid ? [] : [urlValidation.message!]
            }
          }))
        }
        break
      case 'logging':
        updatedConfig = { ...loggingConfig, [field]: value }
        validationKey = 'logging'
        // Validate logging numeric fields
        if (typeof value === 'number') {
          const validation = validateNumericField(
            value,
            field,
            field === 'max_files' ? 1 : 1,
            field === 'max_files' ? 100 : 1000
          )
          setValidationState(prev => ({
            ...prev,
            [validationKey]: {
              isValid: validation.isValid,
              messages: validation.isValid ? [] : [validation.message!]
            }
          }))
        }
        break
    }

    // Mark as having unsaved changes
    setHasUnsavedChanges(true)

    // Propagate change to parent component
    onChange(section, updatedConfig)
  }, [realTimeWatchConfig, traktConfig, notificationConfig, loggingConfig, onChange, validateUrl, validateNumericField])

  /**
   * Toggles expanded state for collapsible sections
   * 
   * @param sectionId - The ID of the section to toggle
   */
  const toggleSection = useCallback((sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId)
      } else {
        newSet.add(sectionId)
      }
      return newSet
    })
  }, [])

  /**
   * Gets the current notification type configuration
   */
  const currentNotificationType = useMemo(() => {
    return NOTIFICATION_TYPES.find(type => type.value === notificationConfig.type) || NOTIFICATION_TYPES[0]
  }, [notificationConfig.type])

  return (
    <div className="space-y-8">
      {/* Section Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
            <Settings className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Advanced System Configuration
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Configure real-time monitoring, integrations, and system services
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
      {advancedErrors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-200">
                Configuration Errors
              </h4>
              <ul className="mt-1 space-y-1 text-sm text-red-700 dark:text-red-300">
                {advancedErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Real-Time Watch Settings */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('realTimeWatch')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <Eye className="h-5 w-5 text-gray-500" />
            <div>
              <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
                Real-Time Watch Monitoring
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {realTimeWatchConfig.enabled ? 'Active' : 'Disabled'}
              </p>
            </div>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('realTimeWatch') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('realTimeWatch') && (
          <div className="px-6 pb-6 space-y-6">
            {/* Enable Real-Time Watch */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label 
                    htmlFor="realtime-enabled"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Enable Real-Time Watch Monitoring
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Automatically monitor and cache media based on user watching activity
                  </p>
                </div>
                <div className="relative">
                  <input
                    id="realtime-enabled"
                    type="checkbox"
                    checked={realTimeWatchConfig.enabled}
                    onChange={(e) => handleFieldChange('real_time_watch', 'enabled', e.target.checked)}
                    disabled={readonly}
                    className="sr-only"
                  />
                  <div 
                    className={classNames(
                      'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                      realTimeWatchConfig.enabled 
                        ? 'bg-primary-600' 
                        : 'bg-gray-300 dark:bg-gray-600',
                      readonly && 'opacity-50 cursor-not-allowed'
                    )}
                    onClick={() => !readonly && handleFieldChange('real_time_watch', 'enabled', !realTimeWatchConfig.enabled)}
                  >
                    <div 
                      className={classNames(
                        'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                        realTimeWatchConfig.enabled ? 'transform translate-x-6' : ''
                      )}
                    />
                  </div>
                </div>
              </div>

              {/* Real-time watch configuration */}
              {realTimeWatchConfig.enabled && (
                <div className="space-y-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Check Interval */}
                    <div className="space-y-2">
                      <label 
                        htmlFor="realtime-check-interval"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                      >
                        Check Interval (seconds)
                      </label>
                      <input
                        id="realtime-check-interval"
                        type="number"
                        min="60"
                        max="3600"
                        value={realTimeWatchConfig.check_interval}
                        onChange={(e) => handleFieldChange('real_time_watch', 'check_interval', parseInt(e.target.value) || 300)}
                        disabled={readonly}
                        className={classNames(
                          'block w-full px-3 py-2 border rounded-lg shadow-sm',
                          'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                          'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                          'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                          'border-gray-300 dark:border-gray-600 sm:text-sm'
                        )}
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        How often to check for new watching activity (60-3600 seconds)
                      </p>
                    </div>

                    {/* Max Concurrent Watches */}
                    <div className="space-y-2">
                      <label 
                        htmlFor="realtime-max-concurrent"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                      >
                        Max Concurrent Watches
                      </label>
                      <input
                        id="realtime-max-concurrent"
                        type="number"
                        min="1"
                        max="10"
                        value={realTimeWatchConfig.max_concurrent_watches}
                        onChange={(e) => handleFieldChange('real_time_watch', 'max_concurrent_watches', parseInt(e.target.value) || 3)}
                        disabled={readonly}
                        className={classNames(
                          'block w-full px-3 py-2 border rounded-lg shadow-sm',
                          'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                          'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                          'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                          'border-gray-300 dark:border-gray-600 sm:text-sm'
                        )}
                      />
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Maximum simultaneous media items to monitor
                      </p>
                    </div>
                  </div>

                  {/* Boolean Settings */}
                  <div className="space-y-4">
                    {[
                      { field: 'auto_cache_on_watch', label: 'Auto-cache on Watch', description: 'Automatically cache media when user starts watching' },
                      { field: 'cache_on_complete', label: 'Cache on Complete', description: 'Cache media when user completes watching' },
                      { field: 'respect_existing_rules', label: 'Respect Existing Rules', description: 'Follow existing media processing rules' },
                      { field: 'respect_other_users_watchlists', label: 'Respect Other Users', description: 'Consider other users\' watchlists when caching' }
                    ].map(({ field, label, description }) => (
                      <div key={field} className="flex items-center justify-between">
                        <div>
                          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {label}
                          </label>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {description}
                          </p>
                        </div>
                        <div className="relative">
                          <input
                            type="checkbox"
                            checked={realTimeWatchConfig[field as keyof RealTimeWatchFormData] as boolean}
                            onChange={(e) => handleFieldChange('real_time_watch', field, e.target.checked)}
                            disabled={readonly}
                            className="sr-only"
                          />
                          <div 
                            className={classNames(
                              'block w-10 h-5 rounded-full cursor-pointer transition-colors',
                              realTimeWatchConfig[field as keyof RealTimeWatchFormData]
                                ? 'bg-primary-600' 
                                : 'bg-gray-300 dark:bg-gray-600',
                              readonly && 'opacity-50 cursor-not-allowed'
                            )}
                            onClick={() => !readonly && handleFieldChange('real_time_watch', field, !realTimeWatchConfig[field as keyof RealTimeWatchFormData])}
                          >
                            <div 
                              className={classNames(
                                'absolute left-0.5 top-0.5 bg-white w-4 h-4 rounded-full transition-transform',
                                realTimeWatchConfig[field as keyof RealTimeWatchFormData] ? 'transform translate-x-5' : ''
                              )}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Trakt Integration Settings */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('trakt')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <Film className="h-5 w-5 text-gray-500" />
            <div>
              <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
                Trakt.tv Integration
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {traktConfig.enabled ? 'Connected' : 'Disabled'}
              </p>
            </div>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('trakt') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('trakt') && (
          <div className="px-6 pb-6 space-y-6">
            {/* Enable Trakt */}
            <div className="flex items-center justify-between">
              <div>
                <label 
                  htmlFor="trakt-enabled"
                  className="text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Enable Trakt.tv Integration
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Track watching history and sync with Trakt.tv
                </p>
              </div>
              <div className="relative">
                <input
                  id="trakt-enabled"
                  type="checkbox"
                  checked={traktConfig.enabled}
                  onChange={(e) => handleFieldChange('trakt', 'enabled', e.target.checked)}
                  disabled={readonly}
                  className="sr-only"
                />
                <div 
                  className={classNames(
                    'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                    traktConfig.enabled 
                      ? 'bg-primary-600' 
                      : 'bg-gray-300 dark:bg-gray-600',
                    readonly && 'opacity-50 cursor-not-allowed'
                  )}
                  onClick={() => !readonly && handleFieldChange('trakt', 'enabled', !traktConfig.enabled)}
                >
                  <div 
                    className={classNames(
                      'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                      traktConfig.enabled ? 'transform translate-x-6' : ''
                    )}
                  />
                </div>
              </div>
            </div>

            {/* Trakt Configuration */}
            {traktConfig.enabled && (
              <div className="space-y-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <Info className="h-5 w-5 text-blue-500 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800 dark:text-blue-200">
                      <p className="font-medium mb-1">API Configuration Required</p>
                      <p>
                        You need to create a Trakt.tv API application to get your Client ID and Secret.
                        <a 
                          href="https://trakt.tv/oauth/applications/new" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="ml-1 text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center"
                        >
                          Create App <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-6">
                  {/* Client ID */}
                  <div className="space-y-2">
                    <label 
                      htmlFor="trakt-client-id"
                      className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Client ID
                      <span className="text-red-500 ml-1" aria-label="Required">*</span>
                    </label>
                    <div className="relative">
                      <input
                        id="trakt-client-id"
                        type="text"
                        value={traktConfig.client_id}
                        onChange={(e) => handleFieldChange('trakt', 'client_id', e.target.value)}
                        placeholder="Enter your Trakt API Client ID"
                        disabled={readonly}
                        className={classNames(
                          'block w-full px-3 py-2 pr-10 border rounded-lg shadow-sm',
                          'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                          'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                          'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                          'border-gray-300 dark:border-gray-600 sm:text-sm font-mono'
                        )}
                      />
                      <Key className="absolute right-3 top-2.5 h-4 w-4 text-gray-400" />
                    </div>
                  </div>

                  {/* Client Secret */}
                  <div className="space-y-2">
                    <label 
                      htmlFor="trakt-client-secret"
                      className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Client Secret
                      <span className="text-red-500 ml-1" aria-label="Required">*</span>
                    </label>
                    <div className="relative">
                      <input
                        id="trakt-client-secret"
                        type="password"
                        value={traktConfig.client_secret}
                        onChange={(e) => handleFieldChange('trakt', 'client_secret', e.target.value)}
                        placeholder="Enter your Trakt API Client Secret"
                        disabled={readonly}
                        className={classNames(
                          'block w-full px-3 py-2 pr-10 border rounded-lg shadow-sm',
                          'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                          'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                          'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                          'border-gray-300 dark:border-gray-600 sm:text-sm font-mono'
                        )}
                      />
                      <Shield className="absolute right-3 top-2.5 h-4 w-4 text-gray-400" />
                    </div>
                  </div>
                </div>

                {/* Validation feedback for Trakt */}
                {!validationState.trakt.isValid && validationState.trakt.messages.length > 0 && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="h-4 w-4 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-red-700 dark:text-red-300">
                        {validationState.trakt.messages.map((message, index) => (
                          <p key={index}>{message}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Notification Settings */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('notifications')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <Bell className="h-5 w-5 text-gray-500" />
            <div>
              <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
                Notification Settings
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {currentNotificationType.label}
              </p>
            </div>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('notifications') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('notifications') && (
          <div className="px-6 pb-6 space-y-6">
            {/* Notification Type Selection */}
            <div className="space-y-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Notification Type
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {NOTIFICATION_TYPES.map((type) => {
                  const Icon = type.icon
                  const isSelected = notificationConfig.type === type.value
                  
                  return (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => !readonly && handleFieldChange('notifications', 'type', type.value)}
                      disabled={readonly}
                      className={classNames(
                        'p-4 rounded-lg border-2 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500',
                        isSelected
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                    >
                      <div className="flex items-start space-x-3">
                        <Icon className={classNames(
                          'h-5 w-5 flex-shrink-0 mt-0.5',
                          isSelected ? 'text-primary-600 dark:text-primary-400' : 'text-gray-500'
                        )} />
                        <div>
                          <h5 className={classNames(
                            'text-sm font-medium',
                            isSelected 
                              ? 'text-primary-900 dark:text-primary-100' 
                              : 'text-gray-900 dark:text-gray-100'
                          )}>
                            {type.label}
                          </h5>
                          <p className={classNames(
                            'text-xs mt-1',
                            isSelected 
                              ? 'text-primary-700 dark:text-primary-300' 
                              : 'text-gray-500 dark:text-gray-400'
                          )}>
                            {type.description}
                          </p>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* URL Configuration for webhook-based notifications */}
            {currentNotificationType.requiresUrl && (
              <div className="space-y-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                <label 
                  htmlFor={`notification-url-${currentNotificationType.value}`}
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  {currentNotificationType.label} Webhook URL
                  <span className="text-red-500 ml-1" aria-label="Required">*</span>
                </label>
                <input
                  id={`notification-url-${currentNotificationType.value}`}
                  type="url"
                  value={notificationConfig[currentNotificationType.urlField! as keyof NotificationSettingsFormData] as string}
                  onChange={(e) => handleFieldChange('notifications', currentNotificationType.urlField!, e.target.value)}
                  placeholder={`Enter your ${currentNotificationType.label} webhook URL`}
                  disabled={readonly}
                  className={classNames(
                    'block w-full px-3 py-2 border rounded-lg shadow-sm',
                    'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                    'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                    'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                    !validationState.notifications.isValid
                      ? 'border-red-300 dark:border-red-600'
                      : 'border-gray-300 dark:border-gray-600',
                    'sm:text-sm'
                  )}
                />
                
                {/* URL validation feedback */}
                {!validationState.notifications.isValid && validationState.notifications.messages.length > 0 && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="h-4 w-4 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-red-700 dark:text-red-300">
                        {validationState.notifications.messages.map((message, index) => (
                          <p key={index}>{message}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Logging Settings */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('logging')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <FileText className="h-5 w-5 text-gray-500" />
            <div>
              <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
                Logging Configuration
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Level: {loggingConfig.level}
              </p>
            </div>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('logging') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('logging') && (
          <div className="px-6 pb-6 space-y-6">
            {/* Logging Level */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Logging Level
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
                {LOGGING_LEVELS.map((level) => {
                  const isSelected = loggingConfig.level === level.value
                  
                  return (
                    <button
                      key={level.value}
                      type="button"
                      onClick={() => !readonly && handleFieldChange('logging', 'level', level.value)}
                      disabled={readonly}
                      className={classNames(
                        'p-3 rounded-lg border text-center transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500',
                        isSelected
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-900 dark:text-primary-100'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-700 dark:text-gray-300',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                    >
                      <div className="font-medium text-sm">{level.label}</div>
                      <div className="text-xs opacity-75 mt-1">{level.description}</div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Log Rotation Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              {/* Max Files */}
              <div className="space-y-2">
                <label 
                  htmlFor="logging-max-files"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Max Log Files
                </label>
                <input
                  id="logging-max-files"
                  type="number"
                  min="1"
                  max="100"
                  value={loggingConfig.max_files}
                  onChange={(e) => handleFieldChange('logging', 'max_files', parseInt(e.target.value) || 5)}
                  disabled={readonly}
                  className={classNames(
                    'block w-full px-3 py-2 border rounded-lg shadow-sm',
                    'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                    'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                    'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                    'border-gray-300 dark:border-gray-600 sm:text-sm'
                  )}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Number of log files to retain (1-100)
                </p>
              </div>

              {/* Max Size */}
              <div className="space-y-2">
                <label 
                  htmlFor="logging-max-size"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Max File Size (MB)
                </label>
                <input
                  id="logging-max-size"
                  type="number"
                  min="1"
                  max="1000"
                  value={loggingConfig.max_size_mb}
                  onChange={(e) => handleFieldChange('logging', 'max_size_mb', parseInt(e.target.value) || 10)}
                  disabled={readonly}
                  className={classNames(
                    'block w-full px-3 py-2 border rounded-lg shadow-sm',
                    'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                    'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                    'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                    'border-gray-300 dark:border-gray-600 sm:text-sm'
                  )}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Maximum size per log file (1-1000 MB)
                </p>
              </div>
            </div>

            {/* Logging validation feedback */}
            {!validationState.logging.isValid && validationState.logging.messages.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-700 dark:text-red-300">
                    {validationState.logging.messages.map((message, index) => (
                      <p key={index}>{message}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default AdvancedSettings