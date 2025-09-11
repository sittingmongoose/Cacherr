/**
 * SettingsPage Component
 * 
 * Main settings page that orchestrates all configuration sections:
 * - Plex Server Configuration
 * - Media Processing Settings
 * - Performance & Concurrency Controls
 * - Advanced Features (Real-time Watch, Trakt, Notifications)
 * 
 * Features:
 * - Centralized configuration management with real-time validation
 * - Auto-save functionality with unsaved changes detection
 * - Export/import configuration with backup capabilities
 * - Mobile-responsive tabbed interface with navigation persistence
 * - Comprehensive error handling and user feedback
 * - Integration with all specialized settings components
 * 
 * @component
 * @example
 * <SettingsPage />
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react'
import { 
  Settings,
  Save,
  RefreshCw,
  Download,
  Upload,
  AlertTriangle,
  CheckCircle,
  Info,
  Loader,
  FileText,
  Database,
  Undo2,
  Shield
} from 'lucide-react'

import { LoadingSpinner, ButtonSpinner } from '../common/LoadingSpinner'
import { classNames } from '../../utils/format'
import SettingsAPIService, { APIError } from '../../services/settingsApi'

// Import all Settings components
import PlexSettings from './PlexSettings'
import MediaSettings from './MediaSettings'
import PerformanceSettings from './PerformanceSettings'
import AdvancedSettings from './AdvancedSettings'

// Type imports
import type { 
  ConfigurationSettings,
  SettingsPageState,
  SettingsSection,
  SettingsValidationErrors,
  SETTINGS_SECTIONS,
  SettingsNavItem
} from './types'

// Import API ValidationResult explicitly to avoid conflict with generic ValidationResult
import type { ValidationResult } from './types/api'

/**
 * Settings page state interface
 * Manages overall page state and navigation
 */
interface SettingsPageLocalState {
  isLoading: boolean
  isSaving: boolean
  isExporting: boolean
  isImporting: boolean
  hasUnsavedChanges: boolean
  activeSection: SettingsSection
  validationErrors: Partial<SettingsValidationErrors>
  showAdvanced: boolean
  lastSavedAt: Date | null
  saveStatus: 'idle' | 'saving' | 'saved' | 'error'
}

/**
 * Navigation items for settings sections
 */
const SETTINGS_NAV_ITEMS: SettingsNavItem[] = [
  {
    id: 'plex',
    label: 'Plex Server',
    icon: 'server',
    description: 'Configure Plex server connection'
  },
  {
    id: 'media',
    label: 'Media Processing',
    icon: 'film',
    description: 'Media caching and processing settings'
  },
  {
    id: 'performance',
    label: 'Performance',
    icon: 'zap',
    description: 'Performance and concurrency settings'
  },
  {
    id: 'advanced',
    label: 'Advanced',
    icon: 'settings',
    description: 'Advanced settings and integrations'
  }
]

/**
 * Default settings page state
 */
const DEFAULT_SETTINGS_STATE: SettingsPageLocalState = {
  isLoading: true,
  isSaving: false,
  isExporting: false,
  isImporting: false,
  hasUnsavedChanges: false,
  activeSection: 'plex',
  validationErrors: {},
  showAdvanced: false,
  lastSavedAt: null,
  saveStatus: 'idle'
}

/**
 * SettingsPage Component
 * 
 * Main settings management interface that coordinates all configuration sections.
 * Provides a unified interface for managing system configuration.
 */
export const SettingsPage: React.FC = () => {
  // Component state management
  const [state, setState] = useState<SettingsPageLocalState>(DEFAULT_SETTINGS_STATE)
  const [configData, setConfigData] = useState<ConfigurationSettings | null>(null)

  /**
   * Loads current configuration from the backend
   */
  const loadConfiguration = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }))
      
      const config = await SettingsAPIService.getCurrentConfig()
      setConfigData(config)
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        validationErrors: {},
        // Clear unsaved badge on fresh load to avoid stale UI state
        hasUnsavedChanges: false
      }))
    } catch (error) {
      console.error('Failed to load configuration:', error)
      
      let errorMessage = 'Failed to load configuration'
      if (error instanceof APIError) {
        errorMessage = error.message
      }
      
      setState(prev => ({
        ...prev,
        isLoading: false,
        validationErrors: {
          general: [errorMessage]
        }
      }))
    }
  }, [])

  /**
   * Saves current configuration to the backend
   */
  const saveConfiguration = useCallback(async () => {
    if (!configData) return

    try {
      setState(prev => ({ 
        ...prev, 
        isSaving: true, 
        saveStatus: 'saving' 
      }))

      // Debug: Log what we're sending to the backend
      console.log('Saving configuration data:', {
        sections: configData,
        validate_before_save: true,
        create_backup: true
      })

      const result = await SettingsAPIService.updateConfig({
        sections: configData,
        validate_before_save: true,
        create_backup: true
      })
      // Clear any persisted unsaved snapshot immediately to avoid reload race
      try {
        localStorage.removeItem('cacherr-unsaved-config')
      } catch {}

      // Refresh configuration from backend so children receive new data object.
      // This ensures local unsaved-change badges reset and masked secrets are re-applied.
      await loadConfiguration()

      setState(prev => ({
        ...prev,
        isSaving: false,
        hasUnsavedChanges: false,
        saveStatus: 'saved',
        lastSavedAt: new Date(),
        validationErrors: {}
      }))

      // Reset save status after 3 seconds
      setTimeout(() => {
        setState(prev => ({ ...prev, saveStatus: 'idle' }))
      }, 3000)

    } catch (error) {
      console.error('Failed to save configuration:', error)
      
      let errorMessage = 'Failed to save configuration'
      let validationErrors: Partial<SettingsValidationErrors> = {}
      
      if (error instanceof APIError) {
        errorMessage = error.message
        // Extract section-specific validation errors if available
        if (error.details && typeof error.details === 'object' && 'validation_result' in error.details) {
          const validation = error.details.validation_result as ValidationResult
          if (!validation.valid) {
            Object.entries(validation.sections).forEach(([section, result]) => {
              if (!result.valid) {
                validationErrors[section as keyof SettingsValidationErrors] = result.errors
              }
            })
          }
        }
      }

      setState(prev => ({
        ...prev,
        isSaving: false,
        saveStatus: 'error',
        validationErrors: Object.keys(validationErrors).length > 0 
          ? validationErrors 
          : { general: [errorMessage] }
      }))
    }
  }, [configData])

  /**
   * Handles configuration changes from child components
   * 
   * @param section - The configuration section being updated
   * @param updates - The updated configuration for that section
   */
  const handleConfigChange = useCallback((
    section: keyof ConfigurationSettings,
    updates: any
  ) => {
    setConfigData(prev => {
      if (!prev) return prev

      // Only mark unsaved when the section actually changes
      const prevSection = prev[section as keyof ConfigurationSettings]
      const changed = JSON.stringify(prevSection) !== JSON.stringify(updates)

      if (!changed) {
        return prev
      }

      // Update section with new data
      const next = {
        ...prev,
        [section]: updates
      } as ConfigurationSettings

      // Flip unsaved flag only on real change
      setState(s => ({ ...s, hasUnsavedChanges: true, saveStatus: 'idle' }))
      return next
    })
  }, [])

  /**
   * Validates a specific configuration section
   * 
   * @param section - The section to validate
   */
  const handleValidateSection = useCallback(async (section: keyof ConfigurationSettings) => {
    if (!configData) return

    try {
      const validation = await SettingsAPIService.validateMultipleSections({
        [section]: configData[section]
      })

      setState(prev => ({
        ...prev,
        validationErrors: {
          ...prev.validationErrors,
          [section]: validation.valid ? [] : validation.errors
        }
      }))
    } catch (error) {
      console.error(`Failed to validate ${section}:`, error)
    }
  }, [configData])

  /**
   * Handles section navigation
   * 
   * @param sectionId - The section to navigate to
   */
  const handleSectionChange = useCallback((sectionId: SettingsSection) => {
    setState(prev => ({ ...prev, activeSection: sectionId }))
  }, [])

  /**
   * Exports current configuration
   */
  const handleExportConfig = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isExporting: true }))
      
      const exportData = await SettingsAPIService.exportConfigAsDownload({
        include_secrets: false,
        format: 'json',
        minify: false
      })
      
      // Create download link
      const url = URL.createObjectURL(exportData.blob)
      const link = document.createElement('a')
      link.href = url
      link.download = exportData.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
    } catch (error) {
      console.error('Failed to export configuration:', error)
    } finally {
      setState(prev => ({ ...prev, isExporting: false }))
    }
  }, [])

  /**
   * Resets configuration to defaults
   */
  const handleResetConfig = useCallback(async () => {
    if (!confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
      return
    }

    try {
      setState(prev => ({ ...prev, isLoading: true }))
      
      await SettingsAPIService.resetConfig()
      await loadConfiguration()
      
    } catch (error) {
      console.error('Failed to reset configuration:', error)
      setState(prev => ({ ...prev, isLoading: false }))
    }
  }, [loadConfiguration])

  // Load configuration on component mount
  useEffect(() => {
    loadConfiguration()
  }, [loadConfiguration])

  // Persist configuration changes to localStorage
  useEffect(() => {
    if (configData && state.hasUnsavedChanges) {
      try {
        localStorage.setItem('cacherr-unsaved-config', JSON.stringify(configData))
      } catch (error) {
        console.warn('Failed to persist unsaved configuration:', error)
      }
    }
  }, [configData, state.hasUnsavedChanges])

  // Load unsaved changes from localStorage on mount
  useEffect(() => {
    try {
      const savedConfig = localStorage.getItem('cacherr-unsaved-config')
      if (savedConfig && !state.isLoading) {
        const parsedConfig = JSON.parse(savedConfig)
        setConfigData(parsedConfig)
        setState(prev => ({ ...prev, hasUnsavedChanges: true }))
        console.log('Loaded unsaved configuration from localStorage')
      }
    } catch (error) {
      console.warn('Failed to load unsaved configuration:', error)
    }
  }, [state.isLoading])

  // Clear unsaved changes from localStorage when saved
  useEffect(() => {
    if (state.saveStatus === 'saved') {
      try {
        localStorage.removeItem('cacherr-unsaved-config')
      } catch (error) {
        console.warn('Failed to clear unsaved configuration:', error)
      }
    }
  }, [state.saveStatus])

  // Render the active settings component
  const renderActiveSettingsComponent = useMemo(() => {
    if (!configData) return null

    const commonProps = {
      data: configData,
      errors: state.validationErrors,
      onChange: handleConfigChange,
      onValidate: handleValidateSection,
      readonly: state.isSaving
    }

    switch (state.activeSection) {
      case 'plex':
        return <PlexSettings {...commonProps} showAdvanced={state.showAdvanced} />
      case 'media':
        return <MediaSettings {...commonProps} showAdvanced={state.showAdvanced} />
      case 'performance':
        return <PerformanceSettings {...commonProps} showAdvanced={state.showAdvanced} />
      case 'advanced':
        return <AdvancedSettings {...commonProps} showExperimental={state.showAdvanced} />
      default:
        return null
    }
  }, [configData, state.activeSection, state.validationErrors, state.isSaving, state.showAdvanced, handleConfigChange, handleValidateSection])

  if (state.isLoading) {
    return <LoadingSpinner text="Loading configuration..." />
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-xl">
                <Settings className="h-8 w-8 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                  System Configuration
                </h1>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  Manage your Cacherr system settings and preferences
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3">
              {/* Save Status */}
              {state.saveStatus !== 'idle' && (
                <div className="flex items-center space-x-2">
                  {state.saveStatus === 'saving' && (
                    <>
                      <ButtonSpinner />
                      <span className="text-sm text-gray-600 dark:text-gray-400">Saving...</span>
                    </>
                  )}
                  {state.saveStatus === 'saved' && (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span className="text-sm text-green-600 dark:text-green-400">Saved</span>
                    </>
                  )}
                  {state.saveStatus === 'error' && (
                    <>
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <span className="text-sm text-red-600 dark:text-red-400">Error</span>
                    </>
                  )}
                </div>
              )}

              {/* Export Button */}
              <button
                onClick={handleExportConfig}
                disabled={state.isExporting || state.isSaving}
                className={classNames(
                  'inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600',
                  'rounded-lg shadow-sm text-sm font-medium transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                  state.isExporting || state.isSaving
                    ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 cursor-not-allowed'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                )}
              >
                {state.isExporting ? (
                  <ButtonSpinner />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Export
              </button>

              {/* Reset Button */}
              <button
                onClick={handleResetConfig}
                disabled={state.isSaving}
                className={classNames(
                  'inline-flex items-center px-4 py-2 border border-red-300 dark:border-red-600',
                  'rounded-lg shadow-sm text-sm font-medium transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500',
                  state.isSaving
                    ? 'bg-red-100 dark:bg-red-900 text-red-400 cursor-not-allowed'
                    : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/40'
                )}
              >
                <Undo2 className="h-4 w-4 mr-2" />
                Reset
              </button>

              {/* Save Button */}
              <button
                onClick={saveConfiguration}
                disabled={!state.hasUnsavedChanges || state.isSaving}
                className={classNames(
                  'inline-flex items-center px-6 py-2 border border-transparent',
                  'rounded-lg shadow-sm text-sm font-medium transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                  state.hasUnsavedChanges && !state.isSaving
                    ? 'bg-primary-600 hover:bg-primary-700 text-white'
                    : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                )}
              >
                {state.isSaving ? (
                  <>
                    <ButtonSpinner />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    {state.hasUnsavedChanges ? 'Save Changes' : 'No Changes'}
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Unsaved Changes Warning */}
          {state.hasUnsavedChanges && (
            <div className="mt-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <div className="flex items-center">
                <AlertTriangle className="h-5 w-5 text-amber-500 dark:text-amber-400 mr-3" />
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  You have unsaved changes. Don't forget to save your configuration.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Settings Navigation & Content */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="flex">
            {/* Sidebar Navigation */}
            <div className="w-80 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700">
              <div className="p-6">
                <nav className="space-y-2">
                  {SETTINGS_NAV_ITEMS.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleSectionChange(item.id)}
                      className={classNames(
                        'w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors',
                        'focus:outline-none focus:ring-2 focus:ring-primary-500',
                        state.activeSection === item.id
                          ? 'bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                      )}
                    >
                      <div className="flex-1">
                        <div className="font-medium">{item.label}</div>
                        {item.description && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {item.description}
                          </div>
                        )}
                      </div>
                      {state.validationErrors[item.id as keyof SettingsValidationErrors]?.length > 0 && (
                        <AlertTriangle className="h-4 w-4 text-red-500 ml-2" />
                      )}
                    </button>
                  ))}
                </nav>

                {/* Advanced Toggle */}
                <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <label 
                      htmlFor="show-advanced"
                      className="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Advanced Options
                    </label>
                    <input
                      id="show-advanced"
                      type="checkbox"
                      checked={state.showAdvanced}
                      onChange={(e) => setState(prev => ({ ...prev, showAdvanced: e.target.checked }))}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Show advanced configuration options
                  </p>
                </div>

                {/* Last Saved */}
                {state.lastSavedAt && (
                  <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Last saved: {state.lastSavedAt.toLocaleTimeString()}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Main Content */}
            <div className="flex-1">
              <div className="p-8">
                {renderActiveSettingsComponent}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
