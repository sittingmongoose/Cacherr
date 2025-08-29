/**
 * Settings-specific TypeScript interfaces for the Cacherr Settings page.
 * 
 * These interfaces are specifically designed for the Settings UI components
 * and complement the broader API types defined in api.ts. They provide
 * clean, focused type definitions for settings management functionality.
 */

import { 
  ConfigurationSettings,
  ValidationResult,
  ConnectivityCheckResult,
  APIResponse
} from './api'

// Settings Page UI Types
export interface SettingsPageState {
  isLoading: boolean
  isSaving: boolean
  hasUnsavedChanges: boolean
  activeSection: SettingsSection
  validationErrors: Partial<SettingsValidationErrors>
  showAdvanced: boolean
}

export type SettingsSection = 'plex' | 'media' | 'performance' | 'advanced' | 'export-import'

export interface SettingsValidationErrors {
  plex: string[]
  media: string[]
  paths: string[]
  performance: string[]
  real_time_watch: string[]
  trakt: string[]
  web: string[]
  test_mode: string[]
  notifications: string[]
  logging: string[]
}

// Form-specific interfaces for Settings components
export interface PlexSettingsFormData {
  url: string
  token: string
  username?: string
  password?: string
}

export interface MediaSettingsFormData {
  copy_to_cache: boolean
  delete_from_cache_when_done: boolean
  watched_move: boolean
  users_toggle: boolean
  watchlist_toggle: boolean
  exit_if_active_session: boolean
  days_to_monitor: number
  number_episodes: number
  watchlist_episodes: number
  watchlist_cache_expiry: number
  watched_cache_expiry: number
}

export interface PathSettingsFormData {
  plex_source: string
  cache_destination: string
  additional_sources: string[]
  additional_plex_sources: string[]
}

export interface PerformanceSettingsFormData {
  max_concurrent_moves_cache: number
  max_concurrent_moves_array: number
  max_concurrent_local_transfers: number
  max_concurrent_network_transfers: number
  enable_monitoring: boolean
}

export interface RealTimeWatchFormData {
  enabled: boolean
  check_interval: number
  auto_cache_on_watch: boolean
  cache_on_complete: boolean
  respect_existing_rules: boolean
  max_concurrent_watches: number
  remove_from_cache_after_hours: number
  respect_other_users_watchlists: boolean
  exclude_inactive_users_days: number
}

export interface TraktSettingsFormData {
  enabled: boolean
  client_id: string
  client_secret: string
  trending_movies_count: number
  check_interval: number
}

export interface LoggingSettingsFormData {
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  max_files: number
  max_size_mb: number
}

export interface NotificationSettingsFormData {
  type: 'webhook' | 'email' | 'discord' | 'slack' | 'none'
  webhook_url?: string
  discord_webhook_url?: string
  slack_webhook_url?: string
}

// Settings API Response Types
export interface SettingsApiResponse extends APIResponse<ConfigurationSettings> {}

export interface SettingsUpdateResponse extends APIResponse<{
  updated_sections: string[]
  total_updates: number
  validation_result: ValidationResult
}> {}

export interface SettingsValidationResponse extends APIResponse<ValidationResult> {}

export interface SettingsTestPlexResponse extends APIResponse<ConnectivityCheckResult> {}

export interface SettingsExportResponse extends APIResponse<{
  configuration: ConfigurationSettings
  export_metadata: {
    exported_at: string
    version: string
    sections: string[]
  }
}> {}

export interface SettingsImportResponse extends APIResponse<{
  imported_sections: string[]
  skipped_sections: string[]
  validation_result: ValidationResult
}> {}

export interface SettingsSchemaResponse extends APIResponse<{
  schema: Record<string, SettingsFieldSchema>
  sections: Record<string, string[]>
  validation_rules: Record<string, any>
}> {}

export interface SettingsPersistenceResponse extends APIResponse<{
  persistence_working: boolean
  config_file_exists: boolean
  config_file_writable: boolean
  test_write_successful: boolean
  error_details?: string
}> {}

// Settings Field Schema for dynamic form generation
export interface SettingsFieldSchema {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  title: string
  description?: string
  default?: any
  minimum?: number
  maximum?: number
  enum?: any[]
  pattern?: string
  required: boolean
  format?: string
  items?: SettingsFieldSchema
  properties?: Record<string, SettingsFieldSchema>
}

// Settings Update Request Types
export interface SettingsUpdateRequest {
  sections: Partial<ConfigurationSettings>
  validate_before_save?: boolean
  create_backup?: boolean
}

export interface SettingsValidationRequest {
  sections: Partial<ConfigurationSettings>
  full_validation?: boolean
}

export interface PlexTestRequest {
  url: string
  token: string
  timeout?: number
}

export interface SettingsImportRequest {
  configuration: Partial<ConfigurationSettings>
  validate_before_import?: boolean
  overwrite_existing?: boolean
  sections_to_import?: string[]
}

// Settings Component Props
export interface SettingsFormProps {
  data: ConfigurationSettings
  errors: Partial<SettingsValidationErrors>
  onChange: (section: keyof ConfigurationSettings, updates: any) => void
  onValidate?: (section: keyof ConfigurationSettings) => Promise<void>
  readonly?: boolean
}

export interface SettingsSectionProps extends SettingsFormProps {
  title: string
  description?: string
  collapsible?: boolean
  defaultExpanded?: boolean
}

// Settings Navigation
export interface SettingsNavItem {
  id: SettingsSection
  label: string
  icon: string
  badge?: string
  disabled?: boolean
  description?: string
}

// Export/Import Types
export interface SettingsExportOptions {
  include_secrets?: boolean
  sections?: SettingsSection[]
  format?: 'json' | 'yaml'
  minify?: boolean
}

export interface SettingsImportOptions {
  validate_first?: boolean
  dry_run?: boolean
  merge_strategy?: 'overwrite' | 'merge' | 'skip_existing'
  sections?: SettingsSection[]
}

// Utility Types for Settings
export type SettingsFormErrors = Partial<Record<keyof ConfigurationSettings, string[]>>

export interface SettingsFormField {
  key: string
  label: string
  type: 'text' | 'number' | 'boolean' | 'select' | 'textarea' | 'password' | 'url' | 'file'
  placeholder?: string
  help?: string
  required?: boolean
  validation?: (value: any) => string | null
  options?: { value: any; label: string }[]
  min?: number
  max?: number
  step?: number
  rows?: number
  accept?: string
}

export interface SettingsFormSection {
  id: SettingsSection
  title: string
  description?: string
  icon: string
  fields: SettingsFormField[]
}

// Settings Actions
export interface SettingsAction {
  type: 'UPDATE_SECTION' | 'SET_LOADING' | 'SET_ERRORS' | 'RESET_SECTION' | 'SET_ACTIVE_SECTION'
  payload: any
}

// Default values and constants
export const DEFAULT_SETTINGS_STATE: SettingsPageState = {
  isLoading: false,
  isSaving: false,
  hasUnsavedChanges: false,
  activeSection: 'plex',
  validationErrors: {},
  showAdvanced: false
}

export const SETTINGS_SECTIONS: SettingsNavItem[] = [
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
    description: 'Advanced settings and real-time features'
  },
  {
    id: 'export-import',
    label: 'Export/Import',
    icon: 'upload',
    description: 'Backup and restore configuration'
  }
]

// Type guards
export const isSettingsSection = (value: string): value is SettingsSection => {
  return ['plex', 'media', 'performance', 'advanced', 'export-import'].includes(value)
}

export const isValidationResponse = (response: any): response is SettingsValidationResponse => {
  return response && typeof response === 'object' && 'success' in response && 'data' in response
}