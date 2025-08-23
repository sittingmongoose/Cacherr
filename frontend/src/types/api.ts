/**
 * API response and data type definitions for PlexCacheUltra frontend.
 * 
 * These types match the Pydantic models and API responses from the Flask backend,
 * ensuring type safety between frontend and backend communication.
 */

// Base API Response structure
export interface APIResponse<T = unknown> {
  success: boolean
  message?: string
  data?: T
  error?: string
  timestamp: string
}

// System Status Types
export interface SystemStatus {
  status: 'running' | 'idle' | 'error'
  pending_operations: PendingOperations
  last_execution: LastExecution | null
  scheduler_running: boolean
  cache_statistics?: CacheStatistics
  test_results?: TestResults
}

export interface PendingOperations {
  files_to_cache: number
  files_to_array: number
}

export interface LastExecution {
  execution_time: string
  success: boolean
  error_message?: string
  operation_type?: 'cache' | 'test' | 'scheduled'
  duration_seconds?: number
}

export interface CacheStatistics {
  total_files: number
  total_size_bytes: number
  total_size_readable: string
  cache_hit_ratio?: number
  last_updated: string
}

// Test Results Types
export interface TestResults {
  [operation: string]: TestOperationResult
}

export interface TestOperationResult {
  file_count: number
  total_size_bytes: number
  total_size_readable: string
  file_details: FileDetail[]
}

export interface FileDetail {
  filename: string
  directory: string
  size_bytes: number
  size_readable: string
  operation_type: 'cache' | 'array' | 'cleanup'
  last_modified?: string
}

// Health Check Types
export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded'
  timestamp: string
  checks: HealthCheck[]
  services: Record<string, ServiceStatus>
  cache_statistics?: CacheStatistics
  uptime_seconds?: number
}

export interface HealthCheck {
  name: string
  status: 'healthy' | 'unhealthy' | 'unknown' | 'not_configured'
  message?: string
  response_time_ms?: number
  last_checked: string
}

export type ServiceStatus = 'healthy' | 'unhealthy' | 'unknown' | 'not_configured'

// Configuration Types
export interface ConfigurationSettings {
  general: GeneralSettings
  plex: PlexSettings
  paths: PathSettings
  cache: CacheSettings
  scheduler: SchedulerSettings
  notifications: NotificationSettings
  trakt?: TraktSettings
}

export interface GeneralSettings {
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  debug: boolean
  test_mode: boolean
  exit_if_active_session: boolean
}

export interface PlexSettings {
  url: string
  token: string
  timeout_seconds: number
  max_retries: number
}

export interface PathSettings {
  plex_source: string
  cache_destination?: string
  additional_sources: string[]
}

export interface CacheSettings {
  copy_to_cache: boolean
  delete_from_cache_when_done: boolean
  use_symlinks_for_cache: boolean
  move_with_symlinks: boolean
  max_concurrent_moves_cache: number
  max_concurrent_moves_array: number
  max_concurrent_local_transfers: number
  max_concurrent_network_transfers: number
}

export interface SchedulerSettings {
  enabled: boolean
  interval_hours: number
  run_on_startup: boolean
  max_concurrent_operations: number
}

export interface NotificationSettings {
  type: 'webhook' | 'email' | 'discord' | 'slack' | 'none'
  webhook_url?: string
  email_config?: EmailConfig
  discord_webhook_url?: string
  slack_webhook_url?: string
}

export interface EmailConfig {
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_password: string
  from_email: string
  to_emails: string[]
  use_tls: boolean
}

export interface TraktSettings {
  client_id: string
  client_secret: string
  username: string
  enabled: boolean
  sync_watched: boolean
  sync_watchlist: boolean
}

// Validation Types
export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  path_checks: Record<string, PathCheckResult>
  connectivity_checks: Record<string, ConnectivityCheckResult>
}

export interface PathCheckResult {
  exists: boolean
  readable?: boolean
  writable?: boolean
  path: string
}

export interface ConnectivityCheckResult {
  status: 'success' | 'failed' | 'error'
  url?: string
  response_time_ms?: number
  status_code?: number
  error?: string
}

// Log Entry Types
export interface LogEntry {
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  timestamp: string
  module?: string
  function?: string
  line_number?: number
}

export interface LogsResponse {
  logs: LogEntry[]
  total_entries: number
  has_more?: boolean
  next_cursor?: string
}

// Operation Request Types
export interface RunOperationRequest {
  test_mode?: boolean
  force?: boolean
  operation_type?: 'full' | 'cache_only' | 'array_only'
}

export interface SettingsUpdateRequest {
  settings: Partial<ConfigurationSettings>
}

export interface SettingsValidationRequest {
  settings: Partial<ConfigurationSettings>
}

// Scheduler Types
export interface SchedulerStatus {
  running: boolean
  next_run?: string
  last_run?: string
  active_jobs: SchedulerJob[]
  total_runs: number
  successful_runs: number
  failed_runs: number
}

export interface SchedulerJob {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  progress?: number
  error_message?: string
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'status_update' | 'log_entry' | 'operation_progress' | 'error'
  data: unknown
  timestamp: string
}

export interface StatusUpdateMessage extends WebSocketMessage {
  type: 'status_update'
  data: SystemStatus
}

export interface LogUpdateMessage extends WebSocketMessage {
  type: 'log_entry'
  data: LogEntry
}

export interface OperationProgressMessage extends WebSocketMessage {
  type: 'operation_progress'
  data: {
    operation_id: string
    progress: number
    current_file?: string
    files_processed: number
    total_files: number
    estimated_time_remaining?: number
  }
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error'
  data: {
    error: string
    error_code?: string
    details?: unknown
  }
}

// UI State Types
export interface UIState {
  theme: 'light' | 'dark' | 'auto'
  sidebarCollapsed: boolean
  refreshInterval: number
  autoRefresh: boolean
  notifications: boolean
}

// Toast notification types
export interface ToastOptions {
  id?: string
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number // 0 means no auto-dismiss
  persistent?: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

// Loading component props
export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg'
  color?: string
  text?: string
  className?: string
}

// Chart Data Types
export interface ChartDataPoint {
  timestamp: string
  value: number
  label?: string
}

export interface TimeSeriesData {
  label: string
  data: ChartDataPoint[]
  color?: string
}

// Filter and Search Types
export interface LogFilter {
  level?: LogEntry['level'][]
  search?: string
  startDate?: string
  endDate?: string
  module?: string
}

export interface FileFilter {
  search?: string
  size_min?: number
  size_max?: number
  operation_type?: FileDetail['operation_type'][]
  date_modified?: string
}

// Pagination Types
export interface PaginationParams {
  page: number
  limit: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    current_page: number
    total_pages: number
    total_items: number
    items_per_page: number
    has_next: boolean
    has_prev: boolean
  }
}

// Error Types
export interface APIError {
  message: string
  status_code: number
  error_code?: string
  details?: Record<string, unknown>
  timestamp: string
}

// Export all types for convenient importing
export type {
  // Re-export commonly used types
  APIResponse as BaseAPIResponse,
  SystemStatus as Status,
  ConfigurationSettings as Config,
  LogEntry as Log,
  TestResults as Tests,
  HealthStatus as Health,
}