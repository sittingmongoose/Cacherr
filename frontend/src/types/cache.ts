/**
 * Cacherr TypeScript Type Definitions
 */

// ============================================================
// Enums
// ============================================================

export enum CacheHealth {
  HEALTHY = 'healthy',
  MODERATE = 'moderate',
  WARNING = 'warning',
  CRITICAL = 'critical',
  UNLIMITED = 'unlimited',
}

export enum EvictionMode {
  NONE = 'none',
  FIFO = 'fifo',
  SMART = 'smart',
}

export enum CacheSource {
  ONDECK = 'ondeck',
  WATCHLIST = 'watchlist',
  TRAKT = 'trakt',
  MANUAL = 'manual',
  ACTIVE_WATCHING = 'active_watching',
  UNKNOWN = 'unknown',
}

export enum SessionState {
  PLAYING = 'playing',
  PAUSED = 'paused',
  BUFFERING = 'buffering',
}

// ============================================================
// API Response Types
// ============================================================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T | null;
  message: string;
  error: string;
  timestamp: string;
}

// ============================================================
// Cache Statistics
// ============================================================

export interface CacheBreakdown {
  ondeck: { count: number; bytes: number };
  watchlist: { count: number; bytes: number };
  trakt: { count: number; bytes: number };
}

export interface CacheStats {
  total_size_bytes: number;
  total_size_human: string;
  limit_bytes: number;
  limit_human: string;
  used_percent: number;
  file_count: number;
  health: CacheHealth;
  breakdown: CacheBreakdown;
}

// ============================================================
// Cached Files
// ============================================================

export interface CachedFile {
  path: string;
  source: CacheSource;
  cached_at: string;
  size_bytes: number;
  priority?: number;
  users?: string[];
}

export interface CachedFilesResponse {
  count: number;
  files: CachedFile[];
}

// ============================================================
// Sessions
// ============================================================

export interface ActiveSession {
  username: string;
  title: string;
  type: 'movie' | 'episode';
  state: SessionState;
  progress: number;
  file_path: string;
}

export interface SessionsResponse {
  count: number;
  sessions: ActiveSession[];
}

// ============================================================
// OnDeck & Watchlist
// ============================================================

export interface EpisodeInfo {
  show: string;
  season: number;
  episode: number;
  is_current_ondeck?: boolean;
}

export interface OnDeckItem {
  file_path: string;
  username: string;
  media_title: string;
  media_type: 'movie' | 'episode';
  is_current_ondeck: boolean;
  episode_info: EpisodeInfo | null;
}

export interface WatchlistItem {
  file_path: string;
  username: string;
  media_title: string;
  media_type: 'movie' | 'episode';
  added_at: string | null;
}

export interface OnDeckResponse {
  count: number;
  items: OnDeckItem[];
}

export interface WatchlistResponse {
  count: number;
  items: WatchlistItem[];
}

// ============================================================
// Cache Operations
// ============================================================

export interface CacheCycleResult {
  ondeck_items: number;
  watchlist_items: number;
  trakt_items: number;
  files_cached: number;
  bytes_cached: number;
  files_restored: number;
  bytes_restored: number;
  eviction: EvictionResult | null;
  errors: string[];
  duration_seconds: number;
  skipped?: string;
}

export interface EvictionCandidate {
  path: string;
  priority: number;
  size: number;
}

export interface EvictionResult {
  needed: boolean;
  performed: boolean;
  files_evicted: number;
  bytes_freed: number;
  bytes_freed_human: string;
  errors: string[];
}

export interface EvictionPreview {
  dry_run: boolean;
  needed: boolean;
  bytes_to_free?: number;
  candidates?: EvictionCandidate[];
  message?: string;
}

export interface ReconciliationResult {
  files_checked: number;
  orphaned_found: number;
  untracked_found: number;
  stale_removed: number;
  errors: string[];
}

// ============================================================
// Configuration
// ============================================================

export interface PlexConfig {
  url: string;
  token: string;
  number_episodes: number;
  days_to_monitor: number;
}

export interface WatchlistConfig {
  enabled: boolean;
  episodes_per_show: number;
}

export interface CacheLimitsConfig {
  cache_limit: string;
  eviction_mode: EvictionMode;
  eviction_threshold_percent: number;
  eviction_target_percent: number;
}

export interface RetentionConfig {
  min_retention_hours: number;
  watched_expiry_hours: number;
  watchlist_retention_days: number;
  ondeck_protected: boolean;
}

export interface RealtimeConfig {
  enabled: boolean;
  check_interval_seconds: number;
}

export interface CacherrConfig {
  plex: PlexConfig;
  watchlist: WatchlistConfig;
  cache_limits: CacheLimitsConfig;
  retention: RetentionConfig;
  realtime: RealtimeConfig;
}

// ============================================================
// Status
// ============================================================

export interface CacherrStatus {
  running: boolean;
  stats: CacheStats;
  active_sessions: number;
  tracked_files: number;
  ondeck_entries: number;
  watchlist_entries: number;
}

// ============================================================
// API Service Interface
// ============================================================

export interface CacherrApi {
  // Health & Status
  getHealth(): Promise<ApiResponse<{ status: string }>>;
  getStatus(): Promise<ApiResponse<CacherrStatus>>;
  
  // Cache Statistics
  getCacheStats(): Promise<ApiResponse<CacheStats>>;
  getCachedFiles(): Promise<ApiResponse<CachedFilesResponse>>;
  
  // Cache Operations
  runCacheCycle(): Promise<ApiResponse<CacheCycleResult>>;
  runReconciliation(): Promise<ApiResponse<ReconciliationResult>>;
  triggerEviction(dryRun?: boolean): Promise<ApiResponse<EvictionResult | EvictionPreview>>;
  uncacheFile(filePath: string): Promise<ApiResponse<void>>;
  
  // Sessions
  getSessions(): Promise<ApiResponse<SessionsResponse>>;
  
  // Media Lists
  getOnDeck(): Promise<ApiResponse<OnDeckResponse>>;
  getWatchlist(): Promise<ApiResponse<WatchlistResponse>>;
  
  // Configuration
  getConfig(): Promise<ApiResponse<CacherrConfig>>;
}

// ============================================================
// Utility Types
// ============================================================

export type Priority = 'high' | 'medium' | 'low';

export function getPriorityLevel(score: number): Priority {
  if (score >= 70) return 'high';
  if (score >= 40) return 'medium';
  return 'low';
}

export function getHealthColor(health: CacheHealth): string {
  switch (health) {
    case CacheHealth.HEALTHY:
      return '#22c55e'; // green
    case CacheHealth.MODERATE:
      return '#eab308'; // yellow
    case CacheHealth.WARNING:
      return '#f97316'; // orange
    case CacheHealth.CRITICAL:
      return '#ef4444'; // red
    case CacheHealth.UNLIMITED:
      return '#6b7280'; // gray
  }
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

export function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
