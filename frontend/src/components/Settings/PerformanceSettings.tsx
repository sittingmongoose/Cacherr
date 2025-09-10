/**
 * PerformanceSettings Component
 * 
 * Provides form interface for configuring performance and concurrency settings
 * including transfer limits, monitoring options, and system optimization controls.
 * 
 * Features:
 * - Concurrency control sliders for different operation types
 * - Real-time validation with user-friendly error messages
 * - Performance monitoring toggle with system impact warnings
 * - Mobile-responsive design with proper accessibility support
 * - Comprehensive error handling with inline validation feedback
 * - Advanced controls for fine-tuning system performance
 * 
 * @component
 * @example
 * <PerformanceSettings
 *   data={configData}
 *   errors={validationErrors}
 *   onChange={(section, updates) => handleConfigChange('performance', updates)}
 *   onValidate={handleValidation}
 *   readonly={false}
 * />
 */

import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { 
  Zap,
  Activity,
  Monitor,
  Settings,
  HardDrive,
  Network,
  AlertTriangle,
  Info,
  CheckCircle,
  TrendingUp,
  Cpu,
  BarChart3,
  Server
} from 'lucide-react'

import { LoadingSpinner } from '../common/LoadingSpinner'
import { classNames } from '../../utils/format'

// Type imports
import type { 
  ConfigurationSettings,
  PerformanceSettings as PerformanceSettingsType,
  SettingsFormProps,
  PerformanceSettingsFormData
} from './types'

/**
 * Props interface for the PerformanceSettings component
 * Extends the standard SettingsFormProps with performance-specific functionality
 */
interface PerformanceSettingsProps extends SettingsFormProps {
  /** Whether to show advanced performance tuning options */
  showAdvanced?: boolean
  /** Whether the component should auto-save changes */
  autoSave?: boolean
  /** Debounce delay in ms for auto-save (default: 1000ms) */
  autoSaveDelay?: number
}

/**
 * Form validation state interface for performance settings
 * Tracks validation status and error messages for each field group
 */
interface PerformanceValidationState {
  concurrency: {
    isValid: boolean
    messages: string[]
  }
  monitoring: {
    isValid: boolean
    messages: string[]
  }
}

/**
 * Performance setting limits and configurations
 * Provides safe ranges and default values for performance tuning
 */
interface PerformanceLimits {
  min: number
  max: number
  step: number
  default: number
  recommended: number
  warningThreshold: number
}

/**
 * Default validation state - all sections start as valid
 */
const DEFAULT_VALIDATION_STATE: PerformanceValidationState = {
  concurrency: { isValid: true, messages: [] },
  monitoring: { isValid: true, messages: [] }
}

/**
 * Performance limits for different concurrency settings
 * Prevents system overload while allowing performance tuning
 */
const PERFORMANCE_LIMITS: Record<string, PerformanceLimits> = {
  cache_moves: {
    min: 1,
    max: 20,
    step: 1,
    default: 3,
    recommended: 5,
    warningThreshold: 10
  },
  array_moves: {
    min: 1,
    max: 15,
    step: 1,
    default: 2,
    recommended: 3,
    warningThreshold: 8
  },
  local_transfers: {
    min: 1,
    max: 25,
    step: 1,
    default: 5,
    recommended: 8,
    warningThreshold: 15
  },
  network_transfers: {
    min: 1,
    max: 10,
    step: 1,
    default: 2,
    recommended: 3,
    warningThreshold: 6
  }
}

/**
 * PerformanceSettings Component
 * 
 * Main component for managing system performance and concurrency configuration.
 * Handles form state, validation, and user interactions for performance tuning.
 */
export const PerformanceSettings: React.FC<PerformanceSettingsProps> = ({
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
  const [validationState, setValidationState] = useState<PerformanceValidationState>(DEFAULT_VALIDATION_STATE)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['concurrency']))

  // Extract performance configuration from data with safe defaults
  const performanceConfig = useMemo<PerformanceSettingsFormData>(() => ({
    max_concurrent_moves_cache: data.performance?.max_concurrent_moves_cache ?? PERFORMANCE_LIMITS.cache_moves.default,
    max_concurrent_moves_array: data.performance?.max_concurrent_moves_array ?? PERFORMANCE_LIMITS.array_moves.default,
    max_concurrent_local_transfers: data.performance?.max_concurrent_local_transfers ?? PERFORMANCE_LIMITS.local_transfers.default,
    max_concurrent_network_transfers: data.performance?.max_concurrent_network_transfers ?? PERFORMANCE_LIMITS.network_transfers.default,
    enable_monitoring: data.performance?.enable_monitoring ?? true
  }), [data.performance])

  // Extract validation errors for performance section
  const performanceErrors = useMemo(() => errors.performance || [], [errors.performance])

  // Reset unsaved changes when data updates (indicating a successful save/refresh)
  const prevDataRef = useRef(data)
  useEffect(() => {
    if (hasUnsavedChanges && prevDataRef.current !== data) {
      setHasUnsavedChanges(false)
    }
    prevDataRef.current = data
  }, [data, hasUnsavedChanges])

  /**
   * Validates numeric concurrency value against defined limits
   * 
   * @param value - The numeric value to validate
   * @param field - The field being validated for context-specific limits
   * @returns Validation result with validity and error message
   */
  const validateConcurrencyField = useCallback((
    value: number,
    field: keyof PerformanceSettingsFormData
  ): { isValid: boolean; message?: string; level?: 'warning' | 'error' } => {
    if (isNaN(value) || value < 1) {
      return { 
        isValid: false, 
        message: 'Concurrency value must be a positive number',
        level: 'error'
      }
    }

    // Get limits based on field type
    let limits: PerformanceLimits
    switch (field) {
      case 'max_concurrent_moves_cache':
        limits = PERFORMANCE_LIMITS.cache_moves
        break
      case 'max_concurrent_moves_array':
        limits = PERFORMANCE_LIMITS.array_moves
        break
      case 'max_concurrent_local_transfers':
        limits = PERFORMANCE_LIMITS.local_transfers
        break
      case 'max_concurrent_network_transfers':
        limits = PERFORMANCE_LIMITS.network_transfers
        break
      default:
        return { isValid: true }
    }

    if (value > limits.max) {
      return {
        isValid: false,
        message: `Value cannot exceed ${limits.max} (maximum safe limit)`,
        level: 'error'
      }
    }

    if (value < limits.min) {
      return {
        isValid: false,
        message: `Value must be at least ${limits.min}`,
        level: 'error'
      }
    }

    if (value > limits.warningThreshold) {
      return {
        isValid: true,
        message: `High concurrency may impact system performance. Recommended: ${limits.recommended}`,
        level: 'warning'
      }
    }

    return { isValid: true }
  }, [])

  /**
   * Handles form field changes with validation and state updates
   * 
   * @param field - The specific field being updated
   * @param value - The new value for the field
   */
  const handleFieldChange = useCallback((field: string, value: any) => {
    // Validate concurrency fields
    if (field !== 'enable_monitoring' && typeof value === 'number') {
      const fieldValidation = validateConcurrencyField(value, field as keyof PerformanceSettingsFormData)
      setValidationState(prev => ({
        ...prev,
        concurrency: {
          isValid: fieldValidation.isValid,
          messages: fieldValidation.isValid ? [] : [fieldValidation.message!]
        }
      }))
    }

    // Create updated configuration
    const updatedConfig = {
      ...performanceConfig,
      [field]: value
    }

    // Mark as having unsaved changes
    setHasUnsavedChanges(true)

    // Propagate change to parent component
    onChange('performance', updatedConfig)
  }, [performanceConfig, onChange, validateConcurrencyField])

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
   * Gets performance level indicator based on current settings
   * 
   * @param value - Current value to assess
   * @param limits - Performance limits for the setting
   * @returns Performance level assessment
   */
  const getPerformanceLevel = useCallback((value: number, limits: PerformanceLimits) => {
    if (value <= limits.recommended) {
      return { level: 'conservative', color: 'green', label: 'Conservative' }
    } else if (value <= limits.warningThreshold) {
      return { level: 'balanced', color: 'blue', label: 'Balanced' }
    } else {
      return { level: 'aggressive', color: 'amber', label: 'Aggressive' }
    }
  }, [])

  /**
   * Concurrency Slider Component
   * Reusable component for rendering concurrency control sliders
   */
  const ConcurrencySlider: React.FC<{
    field: keyof PerformanceSettingsFormData
    label: string
    description: string
    icon: React.ComponentType<{ className?: string }>
    limits: PerformanceLimits
  }> = ({ field, label, description, icon: Icon, limits }) => {
    const value = performanceConfig[field] as number
    const validation = validateConcurrencyField(value, field)
    const perfLevel = getPerformanceLevel(value, limits)

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Icon className="h-5 w-5 text-gray-500" />
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {label}
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {description}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-2">
              <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {value}
              </span>
              <span className={classNames(
                'px-2 py-1 text-xs font-medium rounded-full',
                perfLevel.color === 'green' && 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
                perfLevel.color === 'blue' && 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
                perfLevel.color === 'amber' && 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
              )}>
                {perfLevel.label}
              </span>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Recommended: {limits.recommended}
            </div>
          </div>
        </div>

        {/* Slider */}
        <div className="relative">
          <input
            type="range"
            min={limits.min}
            max={limits.max}
            step={limits.step}
            value={value}
            onChange={(e) => handleFieldChange(field, parseInt(e.target.value))}
            disabled={readonly}
            className={classNames(
              'w-full h-2 rounded-lg appearance-none cursor-pointer',
              'bg-gray-200 dark:bg-gray-700',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4',
              '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary-600',
              '[&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-lg',
              '[&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full',
              '[&::-moz-range-thumb]:bg-primary-600 [&::-moz-range-thumb]:cursor-pointer',
              '[&::-moz-range-thumb]:border-none [&::-moz-range-thumb]:shadow-lg'
            )}
            aria-label={`${label} concurrency setting`}
          />
          
          {/* Slider markers */}
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>{limits.min}</span>
            <span className="text-primary-600 dark:text-primary-400 font-medium">
              {limits.recommended}
            </span>
            <span>{limits.max}</span>
          </div>
        </div>

        {/* Validation feedback */}
        {validation.message && (
          <div className={classNames(
            'flex items-start space-x-2 p-3 rounded-lg',
            validation.level === 'warning' 
              ? 'bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800'
              : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
          )}>
            <AlertTriangle className={classNames(
              'h-4 w-4 flex-shrink-0 mt-0.5',
              validation.level === 'warning' 
                ? 'text-amber-500 dark:text-amber-400' 
                : 'text-red-500 dark:text-red-400'
            )} />
            <p className={classNames(
              'text-sm',
              validation.level === 'warning'
                ? 'text-amber-800 dark:text-amber-200'
                : 'text-red-800 dark:text-red-200'
            )}>
              {validation.message}
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Section Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
            <Zap className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Performance & Concurrency Settings
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Configure system performance limits and monitoring options
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
      {performanceErrors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-red-500 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-800 dark:text-red-200">
                Configuration Errors
              </h4>
              <ul className="mt-1 space-y-1 text-sm text-red-700 dark:text-red-300">
                {performanceErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Concurrency Controls Section */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('concurrency')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <TrendingUp className="h-5 w-5 text-gray-500" />
            <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
              Concurrency Controls
            </h4>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('concurrency') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('concurrency') && (
          <div className="px-6 pb-6 space-y-8">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Info className="h-5 w-5 text-blue-500 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800 dark:text-blue-200">
                  <p className="font-medium mb-1">Performance Guidelines</p>
                  <p>
                    Higher concurrency improves speed but increases system load. Start with recommended values
                    and adjust based on your hardware capabilities and system performance.
                  </p>
                </div>
              </div>
            </div>

            {/* Cache Operations Concurrency */}
            <ConcurrencySlider
              field="max_concurrent_moves_cache"
              label="Cache Operations"
              description="Concurrent file operations when moving to cache"
              icon={HardDrive}
              limits={PERFORMANCE_LIMITS.cache_moves}
            />

            {/* Array Operations Concurrency */}
            <ConcurrencySlider
              field="max_concurrent_moves_array"
              label="Array Operations"
              description="Concurrent file operations when moving to array storage"
              icon={Server}
              limits={PERFORMANCE_LIMITS.array_moves}
            />

            {/* Local Transfers Concurrency */}
            <ConcurrencySlider
              field="max_concurrent_local_transfers"
              label="Local Transfers"
              description="Concurrent local file system operations"
              icon={Cpu}
              limits={PERFORMANCE_LIMITS.local_transfers}
            />

            {/* Network Transfers Concurrency */}
            <ConcurrencySlider
              field="max_concurrent_network_transfers"
              label="Network Transfers"
              description="Concurrent network-based file operations"
              icon={Network}
              limits={PERFORMANCE_LIMITS.network_transfers}
            />
          </div>
        )}
      </div>

      {/* Monitoring & System Health Section */}
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
        <button
          type="button"
          onClick={() => toggleSection('monitoring')}
          className="w-full px-6 py-4 flex items-center justify-between text-left focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-inset"
        >
          <div className="flex items-center space-x-3">
            <Activity className="h-5 w-5 text-gray-500" />
            <h4 className="text-base font-medium text-gray-900 dark:text-gray-100">
              Monitoring & System Health
            </h4>
          </div>
          <div className="text-gray-400">
            {expandedSections.has('monitoring') ? '−' : '+'}
          </div>
        </button>
        
        {expandedSections.has('monitoring') && (
          <div className="px-6 pb-6 space-y-6">
            {/* Enable Performance Monitoring Toggle */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Monitor className="h-5 w-5 text-gray-500" />
                  <div>
                    <label 
                      htmlFor="enable-monitoring"
                      className="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                      Enable Performance Monitoring
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Monitor system performance and collect operation metrics
                    </p>
                  </div>
                </div>
                <div className="relative">
                  <input
                    id="enable-monitoring"
                    type="checkbox"
                    checked={performanceConfig.enable_monitoring}
                    onChange={(e) => handleFieldChange('enable_monitoring', e.target.checked)}
                    disabled={readonly}
                    className="sr-only"
                  />
                  <div 
                    className={classNames(
                      'block w-12 h-6 rounded-full cursor-pointer transition-colors',
                      performanceConfig.enable_monitoring 
                        ? 'bg-primary-600' 
                        : 'bg-gray-300 dark:bg-gray-600',
                      readonly && 'opacity-50 cursor-not-allowed'
                    )}
                    onClick={() => !readonly && handleFieldChange('enable_monitoring', !performanceConfig.enable_monitoring)}
                  >
                    <div 
                      className={classNames(
                        'absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform',
                        performanceConfig.enable_monitoring ? 'transform translate-x-6' : ''
                      )}
                    />
                  </div>
                </div>
              </div>

              {/* Monitoring Status Information */}
              <div className={classNames(
                'p-4 rounded-lg border',
                performanceConfig.enable_monitoring
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                  : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
              )}>
                <div className="flex items-start space-x-3">
                  {performanceConfig.enable_monitoring ? (
                    <CheckCircle className="h-5 w-5 text-green-500 dark:text-green-400 flex-shrink-0 mt-0.5" />
                  ) : (
                    <BarChart3 className="h-5 w-5 text-gray-500 dark:text-gray-400 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className={classNames(
                      'text-sm font-medium',
                      performanceConfig.enable_monitoring 
                        ? 'text-green-800 dark:text-green-200'
                        : 'text-gray-700 dark:text-gray-300'
                    )}>
                      {performanceConfig.enable_monitoring 
                        ? 'Performance monitoring is enabled' 
                        : 'Performance monitoring is disabled'
                      }
                    </p>
                    <p className={classNames(
                      'text-xs mt-1',
                      performanceConfig.enable_monitoring
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-gray-500 dark:text-gray-400'
                    )}>
                      {performanceConfig.enable_monitoring 
                        ? 'System metrics, transfer speeds, and operation timings are being collected and displayed in the dashboard.'
                        : 'Enable monitoring to track system performance, operation success rates, and identify potential bottlenecks.'
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PerformanceSettings
