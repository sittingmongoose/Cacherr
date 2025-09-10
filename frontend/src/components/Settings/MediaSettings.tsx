/**
 * MediaSettings Component
 * 
 * Provides form interface for configuring media processing settings including
 * source paths, file extensions, size limits, caching options, and watchlist management.
 * 
 * Features:
 * - Multi-path input functionality for managing source and additional paths
 * - File extension management with common media type presets
 * - Size limit conversion with unit selection (KB, MB, GB, TB)
 * - Real-time form validation with user-friendly error messages
 * - Mobile-responsive design with proper accessibility support
 * - Comprehensive error handling with inline validation feedback
 * - Toggle controls for boolean settings with clear descriptions
 * 
 * @component
 * @example
 * <MediaSettings
 *   data={configData}
 *   errors={validationErrors}
 *   onChange={(section, updates) => handleConfigChange('media', updates)}
 *   onValidate={handleValidation}
 *   readonly={false}
 * />
 */

import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { 
  Film, 
  FolderPlus,
  FolderMinus,
  HardDrive, 
  FileText,
  Settings,
  Plus,
  X,
  Check,
  AlertTriangle,
  Info,
  FileVideo,
  Database,
  Clock,
  Users,
  Eye,
  Trash2
} from 'lucide-react'

import { LoadingSpinner, ButtonSpinner } from '../common/LoadingSpinner'
import { classNames, formatBytes } from '../../utils/format'

// Type imports
import type { 
  ConfigurationSettings,
  MediaSettings as MediaSettingsType,
  PathSettings as PathSettingsType,
  SettingsFormProps,
  MediaSettingsFormData,
  PathSettingsFormData
} from './types'

/**
 * Props interface for the MediaSettings component
 * Extends the standard SettingsFormProps with media-specific functionality
 */
interface MediaSettingsProps extends SettingsFormProps {
  /** Whether to show advanced path and caching options */
  showAdvanced?: boolean
  /** Whether the component should auto-save changes */
  autoSave?: boolean
  /** Debounce delay in ms for auto-save (default: 1000ms) */
  autoSaveDelay?: number
}

/**
 * Form validation state interface for media settings
 * Tracks validation status and error messages for each field group
 */
interface MediaValidationState {
  paths: {
    isValid: boolean
    messages: string[]
  }
  extensions: {
    isValid: boolean
    messages: string[]
  }
  sizes: {
    isValid: boolean
    messages: string[]
  }
  durations: {
    isValid: boolean
    messages: string[]
  }
}

/**
 * Size unit conversion interface
 * Provides conversion factors and display names for file size units
 */
interface SizeUnit {
  value: string
  label: string
  factor: number
}

/**
 * File extension preset interface
 * Common media file extensions grouped by category
 */
interface ExtensionPreset {
  name: string
  extensions: string[]
  description: string
}

/**
 * Default validation state - all sections start as valid
 */
const DEFAULT_VALIDATION_STATE: MediaValidationState = {
  paths: { isValid: true, messages: [] },
  extensions: { isValid: true, messages: [] },
  sizes: { isValid: true, messages: [] },
  durations: { isValid: true, messages: [] }
}

/**
 * Available size units for file size limits
 * Ordered from smallest to largest for logical progression
 */
const SIZE_UNITS: SizeUnit[] = [
  { value: 'KB', label: 'KB', factor: 1024 },
  { value: 'MB', label: 'MB', factor: 1024 * 1024 },
  { value: 'GB', label: 'GB', factor: 1024 * 1024 * 1024 },
  { value: 'TB', label: 'TB', factor: 1024 * 1024 * 1024 * 1024 }
]

/**
 * Common file extension presets for different media types
 * Helps users quickly configure supported file formats
 */
const EXTENSION_PRESETS: ExtensionPreset[] = [
  {
    name: 'Video Files',
    extensions: ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v', '.webm'],
    description: 'Common video file formats'
  },
  {
    name: 'Audio Files', 
    extensions: ['.mp3', '.flac', '.m4a', '.wav', '.aac', '.ogg', '.wma'],
    description: 'Common audio file formats'
  },
  {
    name: 'All Media',
    extensions: ['.mp4', '.mkv', '.avi', '.mov', '.mp3', '.flac', '.m4a'],
    description: 'Most common video and audio formats'
  }
]

/**
 * MediaSettings Component
 * 
 * Main component for managing media processing and path configuration settings.
 * Handles form state, multi-path management, validation, and user interactions.
 */
export const MediaSettings: React.FC<MediaSettingsProps> = ({
  data,
  errors,
  onChange,
  onValidate,
  readonly = false,
  showAdvanced = false,
  autoSave = false,
  autoSaveDelay = 1000
}) => {
  // Component state management
  const [validationState, setValidationState] = useState<MediaValidationState>(DEFAULT_VALIDATION_STATE)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['basic']))

  // Extract media and path configuration from data with safe defaults
  const mediaConfig = useMemo<MediaSettingsFormData>(() => ({
    copy_to_cache: data.media?.copy_to_cache ?? true,
    delete_from_cache_when_done: data.media?.delete_from_cache_when_done ?? false,
    watched_move: data.media?.watched_move ?? true,
    users_toggle: data.media?.users_toggle ?? true,
    watchlist_toggle: data.media?.watchlist_toggle ?? true,
    exit_if_active_session: data.media?.exit_if_active_session ?? true,
    days_to_monitor: data.media?.days_to_monitor ?? 7,
    number_episodes: data.media?.number_episodes ?? 5,
    watchlist_episodes: data.media?.watchlist_episodes ?? 10,
    watchlist_cache_expiry: data.media?.watchlist_cache_expiry ?? 24,
    watched_cache_expiry: data.media?.watched_cache_expiry ?? 48
  }), [data.media])

  const pathConfig = useMemo<PathSettingsFormData>(() => ({
    plex_source: data.paths?.plex_source || '',
    cache_destination: data.paths?.cache_destination || '',
    additional_sources: data.paths?.additional_sources || [],
    additional_plex_sources: data.paths?.additional_plex_sources || []
  }), [data.paths])

  // Extract validation errors for media and paths sections
  const mediaErrors = useMemo(() => [...(errors.media || []), ...(errors.paths || [])], [errors.media, errors.paths])

  // Reset unsaved changes when data updates (indicating a successful save/refresh)
  const prevDataRef = useRef(data)
  useEffect(() => {
    if (hasUnsavedChanges && prevDataRef.current !== data) {
      setHasUnsavedChanges(false)
    }
    prevDataRef.current = data
  }, [data, hasUnsavedChanges])

  /**
   * Validates path input ensuring they exist and are properly formatted
   * 
   * @param path - The file system path to validate
   * @returns Validation result with validity flag and optional error message
   */
  const validatePath = useCallback((path: string): { isValid: boolean; message?: string } => {
    if (!path.trim()) {
      return { isValid: false, message: 'Path cannot be empty' }
    }

    // Basic path format validation
    const isAbsolutePath = path.startsWith('/') || /^[A-Za-z]:[\\\/]/.test(path)
    if (!isAbsolutePath) {
      return { 
        isValid: false, 
        message: 'Path must be absolute (start with / on Unix or C:\\ on Windows)' 
      }
    }

    // Check for invalid characters
    const invalidChars = /[<>:"|?*]/.test(path.replace(/^[A-Za-z]:/, ''))
    if (invalidChars) {
      return { 
        isValid: false, 
        message: 'Path contains invalid characters' 
      }
    }

    return { isValid: true }
  }, [])

  /**
   * Validates numeric input values with min/max constraints
   * 
   * @param value - The numeric value to validate
   * @param field - The field name for context-specific validation
   * @returns Validation result with validity and error message
   */
  const validateNumericField = useCallback((
    value: number, 
    field: keyof MediaSettingsFormData
  ): { isValid: boolean; message?: string } => {
    if (isNaN(value) || value < 0) {
      return { isValid: false, message: `${field} must be a positive number` }
    }

    // Field-specific validation rules
    switch (field) {
      case 'days_to_monitor':
        if (value > 365) {
          return { isValid: false, message: 'Days to monitor cannot exceed 365' }
        }
        if (value < 1) {
          return { isValid: false, message: 'Days to monitor must be at least 1' }
        }
        break
      
      case 'number_episodes':
      case 'watchlist_episodes':
        if (value > 100) {
          return { isValid: false, message: 'Episode count cannot exceed 100' }
        }
        break

      case 'watchlist_cache_expiry':
      case 'watched_cache_expiry':
        if (value > 8760) { // 1 year in hours
          return { isValid: false, message: 'Cache expiry cannot exceed 8760 hours (1 year)' }
        }
        if (value < 1) {
          return { isValid: false, message: 'Cache expiry must be at least 1 hour' }
        }
        break
    }

    return { isValid: true }
  }, [])

  /**
   * Handles form field changes for media settings with validation
   * 
   * @param section - The configuration section being updated ('media' or 'paths')
   * @param field - The specific field within the section
   * @param value - The new value for the field
   */
  const handleFieldChange = useCallback((
    section: 'media' | 'paths', 
    field: string, 
    value: any
  ) => {
    // Validate the field if it's a path or numeric value
    if (section === 'paths' && typeof value === 'string' && value.trim()) {
      const pathValidation = validatePath(value)
      setValidationState(prev => ({
        ...prev,
        paths: {
          isValid: pathValidation.isValid,
          messages: pathValidation.isValid ? [] : [pathValidation.message!]
        }
      }))
    }

    if (section === 'media' && typeof value === 'number') {
      const numericValidation = validateNumericField(value, field as keyof MediaSettingsFormData)
      setValidationState(prev => ({
        ...prev,
        durations: {
          isValid: numericValidation.isValid,
          messages: numericValidation.isValid ? [] : [numericValidation.message!]
        }
      }))
    }

    // Create updated configuration object
    const updatedConfig = section === 'media' ? 
      { ...mediaConfig, [field]: value } :
      { ...pathConfig, [field]: value }

    // Mark as having unsaved changes
    setHasUnsavedChanges(true)

    // Propagate change to parent component
    onChange(section, updatedConfig)
  }, [mediaConfig, pathConfig, onChange, validatePath, validateNumericField])

  /**
   * Adds a new path to the additional sources or plex sources array
   * Validates the path before adding to prevent empty or invalid entries
   * 
   * @param field - The array field to add to ('additional_sources' or 'additional_plex_sources')
   * @param newPath - The path to add to the array
   */
  const handleAddPath = useCallback((
    field: 'additional_sources' | 'additional_plex_sources', 
    newPath: string
  ) => {
    const trimmedPath = newPath.trim()
    if (!trimmedPath) return

    const pathValidation = validatePath(trimmedPath)
    if (!pathValidation.isValid) {
      setValidationState(prev => ({
        ...prev,
        paths: {
          isValid: false,
          messages: [pathValidation.message!]
        }
      }))
      return
    }

    const currentPaths = pathConfig[field]
    if (currentPaths.includes(trimmedPath)) {
      setValidationState(prev => ({
        ...prev,
        paths: {
          isValid: false,
          messages: ['Path already exists in the list']
        }
      }))
      return
    }

    const updatedPaths = [...currentPaths, trimmedPath]
    handleFieldChange('paths', field, updatedPaths)
  }, [pathConfig, validatePath, handleFieldChange])

  /**
   * Removes a path from the additional sources or plex sources array
   * 
   * @param field - The array field to remove from
   * @param index - The index of the path to remove
   */
  const handleRemovePath = useCallback((
    field: 'additional_sources' | 'additional_plex_sources',
    index: number
  ) => {
    const currentPaths = pathConfig[field]
    const updatedPaths = currentPaths.filter((_, i) => i !== index)
    handleFieldChange('paths', field, updatedPaths)
  }, [pathConfig, handleFieldChange])

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
   * Converts size value between units for display and input
   * 
   * @param bytes - Size in bytes to convert
   * @param targetUnit - Target unit to convert to
   * @returns Converted value in the target unit
   */
  const convertSize = useCallback((bytes: number, targetUnit: string): number => {
    const unit = SIZE_UNITS.find(u => u.value === targetUnit)
    return unit ? Math.round((bytes / unit.factor) * 100) / 100 : bytes
  }, [])

  /**
   * Multi-path input component for managing arrays of file system paths
   * 
   * @param field - The field name in pathConfig
   * @param label - Display label for the input group
   * @param description - Help text describing the purpose
   * @param placeholder - Placeholder text for new path input
   */
  const PathInputGroup: React.FC<{
    field: 'additional_sources' | 'additional_plex_sources'
    label: string
    description: string
    placeholder: string
  }> = ({ field, label, description, placeholder }) => {
    const [newPath, setNewPath] = useState('')
    const currentPaths = pathConfig[field]

    const handleKeyPress = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        if (newPath.trim()) {
          handleAddPath(field, newPath)
          setNewPath('')
        }
      }
    }

    return (
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
          </label>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {description}
          </p>
        </div>

        {/* Existing paths list */}
        {currentPaths.length > 0 && (
          <div className="space-y-2">
            {currentPaths.map((path, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <span className="text-sm font-mono text-gray-900 dark:text-gray-100 truncate flex-1">
                  {path}
                </span>
                <button
                  type="button"
                  onClick={() => handleRemovePath(field, index)}
                  disabled={readonly}
                  className="ml-3 p-1 text-red-500 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label={`Remove path ${path}`}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Add new path input */}
        <div className="flex space-x-2">
          <div className="flex-1">
            <input
              type="text"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={placeholder}
              disabled={readonly}
              className={classNames(
                'block w-full px-3 py-2 border rounded-lg shadow-sm',
                'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                'border-gray-300 dark:border-gray-600 sm:text-sm font-mono'
              )}
            />
          </div>
          <button
            type="button"
            onClick={() => {
              if (newPath.trim()) {
                handleAddPath(field, newPath)
                setNewPath('')
              }
            }}
            disabled={readonly || !newPath.trim()}
            className={classNames(
              'inline-flex items-center px-3 py-2 border border-transparent',
              'text-sm font-medium rounded-lg focus:outline-none focus:ring-2',
              'focus:ring-offset-2 focus:ring-primary-500 transition-colors duration-200',
              newPath.trim() && !readonly
                ? 'bg-primary-600 hover:bg-primary-700 text-white'
                : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
            )}
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Section Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
            <Film className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Media Processing Configuration
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Configure media file processing, paths, and caching behavior
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
      {mediaErrors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-200">
                Configuration Errors
              </h4>
              <ul className="mt-1 space-y-1 text-sm text-red-700 dark:text-red-300">
                {mediaErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Basic Media Settings Section */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('basic')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <Settings className="h-5 w-5 text-gray-500" />
            <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
              Basic Media Settings
            </h4>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('basic') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('basic') && (
          <div className="px-6 pb-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Copy to Cache Toggle */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label 
                    htmlFor="copy-to-cache"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Copy Files to Cache
                  </label>
                  <div className="relative">
                    <input
                      id="copy-to-cache"
                      type="checkbox"
                      checked={mediaConfig.copy_to_cache}
                      onChange={(e) => handleFieldChange('media', 'copy_to_cache', e.target.checked)}
                      disabled={readonly}
                      className="sr-only"
                    />
                    <div 
                      className={classNames(
                        'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                        mediaConfig.copy_to_cache 
                          ? 'bg-primary-600' 
                          : 'bg-gray-300 dark:bg-gray-600',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !readonly && handleFieldChange('media', 'copy_to_cache', !mediaConfig.copy_to_cache)}
                    >
                      <div 
                        className={classNames(
                          'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                          mediaConfig.copy_to_cache ? 'transform translate-x-6' : ''
                        )}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Copy media files to cache location when processing
                </p>
              </div>

              {/* Delete from Cache Toggle */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label 
                    htmlFor="delete-from-cache"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Auto-Clean Cache
                  </label>
                  <div className="relative">
                    <input
                      id="delete-from-cache"
                      type="checkbox"
                      checked={mediaConfig.delete_from_cache_when_done}
                      onChange={(e) => handleFieldChange('media', 'delete_from_cache_when_done', e.target.checked)}
                      disabled={readonly}
                      className="sr-only"
                    />
                    <div 
                      className={classNames(
                        'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                        mediaConfig.delete_from_cache_when_done 
                          ? 'bg-primary-600' 
                          : 'bg-gray-300 dark:bg-gray-600',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !readonly && handleFieldChange('media', 'delete_from_cache_when_done', !mediaConfig.delete_from_cache_when_done)}
                    >
                      <div 
                        className={classNames(
                          'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                          mediaConfig.delete_from_cache_when_done ? 'transform translate-x-6' : ''
                        )}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Automatically remove cached files after processing
                </p>
              </div>

              {/* Watched Move Toggle */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label 
                    htmlFor="watched-move"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Move Watched Files
                  </label>
                  <div className="relative">
                    <input
                      id="watched-move"
                      type="checkbox"
                      checked={mediaConfig.watched_move}
                      onChange={(e) => handleFieldChange('media', 'watched_move', e.target.checked)}
                      disabled={readonly}
                      className="sr-only"
                    />
                    <div 
                      className={classNames(
                        'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                        mediaConfig.watched_move 
                          ? 'bg-primary-600' 
                          : 'bg-gray-300 dark:bg-gray-600',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !readonly && handleFieldChange('media', 'watched_move', !mediaConfig.watched_move)}
                    >
                      <div 
                        className={classNames(
                          'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                          mediaConfig.watched_move ? 'transform translate-x-6' : ''
                        )}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Move files to array after they have been watched
                </p>
              </div>

              {/* Exit if Active Session Toggle */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label 
                    htmlFor="exit-active-session"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Respect Active Sessions
                  </label>
                  <div className="relative">
                    <input
                      id="exit-active-session"
                      type="checkbox"
                      checked={mediaConfig.exit_if_active_session}
                      onChange={(e) => handleFieldChange('media', 'exit_if_active_session', e.target.checked)}
                      disabled={readonly}
                      className="sr-only"
                    />
                    <div 
                      className={classNames(
                        'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                        mediaConfig.exit_if_active_session 
                          ? 'bg-primary-600' 
                          : 'bg-gray-300 dark:bg-gray-600',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !readonly && handleFieldChange('media', 'exit_if_active_session', !mediaConfig.exit_if_active_session)}
                    >
                      <div 
                        className={classNames(
                          'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                          mediaConfig.exit_if_active_session ? 'transform translate-x-6' : ''
                        )}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Skip processing if media is currently being watched
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Path Configuration Section */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('paths')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <HardDrive className="h-5 w-5 text-gray-500" />
            <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
              Path Configuration
            </h4>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('paths') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('paths') && (
          <div className="px-6 pb-6 space-y-6">
            {/* Plex Source Path */}
            <div className="space-y-2">
              <label 
                htmlFor="plex-source"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Plex Source Path
                <span className="text-red-500 ml-1" aria-label="Required">*</span>
              </label>
              <input
                id="plex-source"
                type="text"
                value={pathConfig.plex_source}
                onChange={(e) => handleFieldChange('paths', 'plex_source', e.target.value)}
                placeholder="/mnt/plex/media"
                disabled={readonly}
                className={classNames(
                  'block w-full px-3 py-2 border rounded-lg shadow-sm',
                  'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                  'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                  'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                  'border-gray-300 dark:border-gray-600 sm:text-sm font-mono'
                )}
              />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Primary path where Plex media files are stored
              </p>
            </div>

            {/* Cache Destination Path */}
            <div className="space-y-2">
              <label 
                htmlFor="cache-destination"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Cache Destination Path
                <span className="text-red-500 ml-1" aria-label="Required">*</span>
              </label>
              <input
                id="cache-destination"
                type="text"
                value={pathConfig.cache_destination}
                onChange={(e) => handleFieldChange('paths', 'cache_destination', e.target.value)}
                placeholder="/mnt/cache"
                disabled={readonly}
                className={classNames(
                  'block w-full px-3 py-2 border rounded-lg shadow-sm',
                  'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                  'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                  'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                  'border-gray-300 dark:border-gray-600 sm:text-sm font-mono'
                )}
              />
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Path where cached media files will be stored
              </p>
            </div>

            {/* Additional Source Paths */}
            <PathInputGroup
              field="additional_sources"
              label="Additional Source Paths"
              description="Additional paths to monitor for media files beyond the main Plex source"
              placeholder="/mnt/additional/media"
            />

            {/* Additional Plex Source Paths */}
            <PathInputGroup
              field="additional_plex_sources"
              label="Additional Plex Library Paths"
              description="Additional Plex library paths for comprehensive media discovery"
              placeholder="/mnt/plex/movies"
            />

            {/* Path validation errors */}
            {!validationState.paths.isValid && validationState.paths.messages.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-700 dark:text-red-300">
                    {validationState.paths.messages.map((message, index) => (
                      <p key={index}>{message}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Monitoring & Limits Section */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('monitoring')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <Eye className="h-5 w-5 text-gray-500" />
            <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
              Monitoring & Limits
            </h4>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('monitoring') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('monitoring') && (
          <div className="px-6 pb-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Days to Monitor */}
              <div className="space-y-2">
                <label 
                  htmlFor="days-to-monitor"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Days to Monitor
                </label>
                <div className="relative">
                  <input
                    id="days-to-monitor"
                    type="number"
                    min="1"
                    max="365"
                    value={mediaConfig.days_to_monitor}
                    onChange={(e) => handleFieldChange('media', 'days_to_monitor', parseInt(e.target.value) || 1)}
                    disabled={readonly}
                    className={classNames(
                      'block w-full px-3 py-2 pr-12 border rounded-lg shadow-sm',
                      'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                      'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                      'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                      'border-gray-300 dark:border-gray-600 sm:text-sm'
                    )}
                  />
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <span className="text-gray-500 dark:text-gray-400 text-sm">days</span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  How many days back to look for recently added media
                </p>
              </div>

              {/* Number of Episodes */}
              <div className="space-y-2">
                <label 
                  htmlFor="number-episodes"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Episodes Limit
                </label>
                <input
                  id="number-episodes"
                  type="number"
                  min="1"
                  max="100"
                  value={mediaConfig.number_episodes}
                  onChange={(e) => handleFieldChange('media', 'number_episodes', parseInt(e.target.value) || 1)}
                  disabled={readonly}
                  className={classNames(
                    'block w-full px-3 py-2 border rounded-lg shadow-sm',
                    'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                    'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                    'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                    'border-gray-300 dark:border-gray-600 sm:text-sm'
                  )}
                />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Maximum episodes to process per TV show
                </p>
              </div>

              {/* Watchlist Episodes */}
              <div className="space-y-2">
                <label 
                  htmlFor="watchlist-episodes"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Watchlist Episodes
                </label>
                <input
                  id="watchlist-episodes"
                  type="number"
                  min="1"
                  max="100"
                  value={mediaConfig.watchlist_episodes}
                  onChange={(e) => handleFieldChange('media', 'watchlist_episodes', parseInt(e.target.value) || 1)}
                  disabled={readonly}
                  className={classNames(
                    'block w-full px-3 py-2 border rounded-lg shadow-sm',
                    'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                    'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                    'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                    'border-gray-300 dark:border-gray-600 sm:text-sm'
                  )}
                />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Episodes to cache from watchlist items
                </p>
              </div>

              {/* Watchlist Cache Expiry */}
              <div className="space-y-2">
                <label 
                  htmlFor="watchlist-expiry"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Watchlist Expiry
                </label>
                <div className="relative">
                  <input
                    id="watchlist-expiry"
                    type="number"
                    min="1"
                    max="8760"
                    value={mediaConfig.watchlist_cache_expiry}
                    onChange={(e) => handleFieldChange('media', 'watchlist_cache_expiry', parseInt(e.target.value) || 1)}
                    disabled={readonly}
                    className={classNames(
                      'block w-full px-3 py-2 pr-16 border rounded-lg shadow-sm',
                      'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                      'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                      'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                      'border-gray-300 dark:border-gray-600 sm:text-sm'
                    )}
                  />
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <span className="text-gray-500 dark:text-gray-400 text-sm">hours</span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  How long to keep watchlist items cached
                </p>
              </div>

              {/* Watched Cache Expiry */}
              <div className="space-y-2">
                <label 
                  htmlFor="watched-expiry"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Watched Expiry
                </label>
                <div className="relative">
                  <input
                    id="watched-expiry"
                    type="number"
                    min="1"
                    max="8760"
                    value={mediaConfig.watched_cache_expiry}
                    onChange={(e) => handleFieldChange('media', 'watched_cache_expiry', parseInt(e.target.value) || 1)}
                    disabled={readonly}
                    className={classNames(
                      'block w-full px-3 py-2 pr-16 border rounded-lg shadow-sm',
                      'focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                      'dark:bg-gray-800 dark:border-gray-600 dark:text-gray-100',
                      'disabled:bg-gray-50 dark:disabled:bg-gray-900 disabled:cursor-not-allowed',
                      'border-gray-300 dark:border-gray-600 sm:text-sm'
                    )}
                  />
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <span className="text-gray-500 dark:text-gray-400 text-sm">hours</span>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  How long to keep watched items in cache
                </p>
              </div>
            </div>

            {/* Duration validation errors */}
            {!validationState.durations.isValid && validationState.durations.messages.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-700 dark:text-red-300">
                    {validationState.durations.messages.map((message, index) => (
                      <p key={index}>{message}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* User & Watchlist Management Section */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('users')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <Users className="h-5 w-5 text-gray-500" />
            <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
              User & Watchlist Management
            </h4>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('users') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('users') && (
          <div className="px-6 pb-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Users Toggle */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label 
                    htmlFor="users-toggle"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Enable User Management
                  </label>
                  <div className="relative">
                    <input
                      id="users-toggle"
                      type="checkbox"
                      checked={mediaConfig.users_toggle}
                      onChange={(e) => handleFieldChange('media', 'users_toggle', e.target.checked)}
                      disabled={readonly}
                      className="sr-only"
                    />
                    <div 
                      className={classNames(
                        'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                        mediaConfig.users_toggle 
                          ? 'bg-primary-600' 
                          : 'bg-gray-300 dark:bg-gray-600',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !readonly && handleFieldChange('media', 'users_toggle', !mediaConfig.users_toggle)}
                    >
                      <div 
                        className={classNames(
                          'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                          mediaConfig.users_toggle ? 'transform translate-x-6' : ''
                        )}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Track and manage user-specific media preferences
                </p>
              </div>

              {/* Watchlist Toggle */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label 
                    htmlFor="watchlist-toggle"
                    className="text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Enable Watchlist Processing
                  </label>
                  <div className="relative">
                    <input
                      id="watchlist-toggle"
                      type="checkbox"
                      checked={mediaConfig.watchlist_toggle}
                      onChange={(e) => handleFieldChange('media', 'watchlist_toggle', e.target.checked)}
                      disabled={readonly}
                      className="sr-only"
                    />
                    <div 
                      className={classNames(
                        'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                        mediaConfig.watchlist_toggle 
                          ? 'bg-primary-600' 
                          : 'bg-gray-300 dark:bg-gray-600',
                        readonly && 'opacity-50 cursor-not-allowed'
                      )}
                      onClick={() => !readonly && handleFieldChange('media', 'watchlist_toggle', !mediaConfig.watchlist_toggle)}
                    >
                      <div 
                        className={classNames(
                          'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                          mediaConfig.watchlist_toggle ? 'transform translate-x-6' : ''
                        )}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Process user watchlists for automatic caching
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default MediaSettings
