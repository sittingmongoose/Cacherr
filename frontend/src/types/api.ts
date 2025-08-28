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
  active_files?: number
  orphaned_files?: number
  users_count?: number
  oldest_cached_at?: string
  most_accessed_file?: string
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

// Configuration Types (Updated for Pydantic v2)
export interface ConfigurationSettings {
  plex: PlexSettings
  media: MediaSettings
  paths: PathSettings
  performance: PerformanceSettings
  real_time_watch: RealTimeWatchSettings
  trakt: TraktSettings
  web: WebSettings
  test_mode: TestModeSettings
  notifications: NotificationSettings
  logging: LoggingSettings
  debug: boolean
}

export interface PlexSettings {
  url: string
  token: string
  username?: string
  password?: string
}

export interface MediaSettings {
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
  cache_mode_description: string  // Computed field
}

export interface PathSettings {
  plex_source: string
  cache_destination: string
  additional_sources: string[]
  additional_plex_sources: string[]
}

export interface PerformanceSettings {
  max_concurrent_moves_cache: number
  max_concurrent_moves_array: number
  max_concurrent_local_transfers: number
  max_concurrent_network_transfers: number
  enable_monitoring: boolean
}

export interface RealTimeWatchSettings {
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

export interface WebSettings {
  host: string
  port: number
  debug: boolean
  enable_scheduler: boolean
}

export interface TestModeSettings {
  enabled: boolean
  show_file_sizes: boolean
  show_total_size: boolean
  dry_run: boolean
}

export interface LoggingSettings {
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  max_files: number
  max_size_mb: number
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
  enabled: boolean
  client_id: string
  client_secret: string
  trending_movies_count: number
  check_interval: number
}

// Validation Types (Pydantic v2)
export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  sections: Record<string, SectionValidationResult>
  message?: string
}

export interface SectionValidationResult {
  valid: boolean
  errors: string[]
  model_class: string
}

export interface ConfigurationSummary {
  valid: boolean
  error_count: number
  sections_count: number
  key_settings: Record<string, any>
  validation_details: Record<string, SectionValidationResult>
}

export interface PathCheckResult {
  exists: boolean
  readable?: boolean
  writable?: boolean
  path: string
}

// Cached Files Types
export interface CachedFileInfo {
  id: string
  file_path: string
  filename: string
  original_path: string
  cached_path: string
  cache_method: 'atomic_symlink' | 'atomic_copy' | 'symlink' | 'hardlink' | 'copy'
  file_size_bytes: number
  file_size_readable: string
  cached_at: string
  last_accessed?: string
  access_count: number
  triggered_by_user?: string
  triggered_by_operation: 'watchlist' | 'ondeck' | 'trakt' | 'manual' | 'continue_watching' | 'real_time_watch' | 'active_watching'
  status: 'active' | 'orphaned' | 'pending_removal' | 'removed'
  users: string[]
  metadata?: Record<string, unknown>
}

export interface CachedFilesFilter {
  search?: string
  user_id?: string
  status?: CachedFileInfo['status']
  triggered_by_operation?: CachedFileInfo['triggered_by_operation']
  size_min?: number
  size_max?: number
  cached_since?: string
  limit?: number
  offset?: number
}

export interface CachedFilesResponse {
  files: CachedFileInfo[]
  pagination: {
    limit: number
    offset: number
    total_count: number
    has_more: boolean
  }
  filter_applied: Partial<CachedFilesFilter>
}

export interface CacheUpdateMessage extends WebSocketMessage {
  type: 'cache_file_added' | 'cache_file_removed'
  data: {
    file_path: string
    action: 'added' | 'removed'
    user_id?: string
    reason: string
    file_info?: CachedFileInfo
    cache_method?: CachedFileInfo['cache_method']
  }
}

export interface CacheStatisticsMessage extends WebSocketMessage {
  type: 'cache_statistics_updated'
  data: CacheStatistics
}

export interface CacheCleanupRequest {
  remove_orphaned?: boolean
  user_id?: string
}

export interface CacheCleanupResponse {
  orphaned_count: number
  removed_count: number
  remove_orphaned: boolean
}

export interface UserCacheStatistics {
  user_id: string
  period_days: number
  total_files: number
  active_files: number
  total_size_bytes: number
  total_size_readable: string
  most_common_operation?: string
  recent_files: {
    filename: string
    cached_at: string
    file_size_readable: string
    operation: string
  }[]
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
  type: 'status_update' | 'log_entry' | 'operation_progress' | 'error' | 'cache_file_added' | 'cache_file_removed' | 'cache_statistics_updated' | 'operation_file_update' | 'pong'
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

// Results and Operations Types
export interface BatchOperation {
  id: string
  operation_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'completed_with_errors'
  test_mode: boolean
  triggered_by: string
  triggered_by_user?: string
  reason: string
  started_at: string
  completed_at?: string
  total_files: number
  files_processed: number
  files_successful: number
  files_failed: number
  total_size_bytes: number
  bytes_processed: number
  error_message?: string
  metadata?: Record<string, unknown>
}

export interface FileOperation {
  id: string
  operation_id: string
  file_path: string
  filename: string
  source_path: string
  destination_path?: string
  operation_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'
  reason: string
  triggered_by_user?: string
  file_size_bytes: number
  started_at?: string
  completed_at?: string
  error_message?: string
  parent_operation_id: string
}

export interface OperationDetails {
  batch_operation: BatchOperation
  file_operations: FileOperation[]
}

export interface UserStatistics {
  user_id: string
  total_operations: number
  total_files_successful: number
  total_files_failed: number
  total_bytes_processed: number
  successful_operations: number
  failed_operations: number
  period_days: number
  start_date: string
}

export interface OperationsResponse {
  operations: BatchOperation[]
  pagination: {
    limit: number
    offset: number
    total_count: number
    has_more: boolean
  }
}

// Results Tab Filter Types
export interface ResultsFilter {
  user_id?: string
  operation_type?: string
  status?: BatchOperation['status'][]
  start_date?: string
  end_date?: string
  search?: string
  active_only?: boolean
}

// Results WebSocket Message Types
export interface OperationProgressUpdateMessage extends WebSocketMessage {
  type: 'operation_progress'
  data: {
    operation_id: string
    operation_type: string
    status: BatchOperation['status']
    test_mode: boolean
    progress: number
    files_processed: number
    files_successful: number
    files_failed: number
    total_files: number
    bytes_processed: number
    total_bytes: number
    started_at?: string
    completed_at?: string
    triggered_by: string
    triggered_by_user?: string
    reason: string
    error_message?: string
  }
}

export interface FileOperationUpdateMessage extends WebSocketMessage {
  type: 'operation_file_update'
  data: {
    operation_id: string
    status: FileOperation['status']
    error_message?: string
    completed_at?: string
  }
}

// Cached Files Types (for new Cached tab)
export interface CachedFileInfo {
  id: string
  file_path: string
  filename: string
  original_path: string
  cached_path: string
  cache_method: 'atomic_symlink' | 'atomic_copy' | 'symlink' | 'hardlink' | 'copy'
  file_size_bytes: number
  file_size_readable: string
  cached_at: string
  last_accessed?: string
  access_count: number
  triggered_by_user?: string
  triggered_by_operation: 'watchlist' | 'ondeck' | 'trakt' | 'manual' | 'continue_watching' | 'real_time_watch' | 'active_watching'
  status: 'active' | 'orphaned' | 'pending_removal' | 'removed'
  users: string[]
  metadata?: Record<string, unknown>
}

export interface UserCacheStatistics {
  user_id: string
  period_days: number
  total_files: number
  active_files: number
  total_size_bytes: number
  total_size_readable: string
  most_common_operation?: string
  recent_files: Array<{
    filename: string
    cached_at: string
    file_size_readable: string
    operation: string
  }>
}

export interface CachedFilesFilter {
  search?: string
  user_id?: string
  status?: CachedFileInfo['status']
  triggered_by_operation?: 'watchlist' | 'ondeck' | 'trakt' | 'manual' | 'continue_watching' | 'real_time_watch' | 'active_watching'
  size_min?: number
  size_max?: number
  cached_since?: string
  limit?: number
  offset?: number
}

export interface CachedFilesResponse {
  files: CachedFileInfo[]
  pagination: {
    limit: number
    offset: number
    total_count: number
    has_more: boolean
  }
  filter_applied: CachedFilesFilter
}

export interface CachedFileSearchResponse {
  query: string
  search_type: string
  results: CachedFileInfo[]
  total_found: number
  limited_to: number
}

export interface CacheCleanupRequest {
  remove_orphaned?: boolean
  user_id?: string
}

export interface CacheCleanupResponse {
  orphaned_count: number
  removed_count: number
  remove_orphaned: boolean
}

export interface RemoveCachedFileRequest {
  reason: string
  user_id?: string
}

// Cached Files WebSocket Message Types
export interface CacheFileAddedMessage extends WebSocketMessage {
  type: 'cache_file_added'
  data: {
    file_path: string
    action: 'added'
    user_id?: string
    reason: string
    file_info: CachedFileInfo
  }
}

export interface CacheFileRemovedMessage extends WebSocketMessage {
  type: 'cache_file_removed'
  data: {
    file_path: string
    action: 'removed'
    user_id?: string
    reason: string
    file_id: string
  }
}

export interface CacheStatisticsUpdatedMessage extends WebSocketMessage {
  type: 'cache_statistics_updated'
  data: CacheStatistics
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
  BatchOperation as Operation,
  FileOperation as FileOp,
}