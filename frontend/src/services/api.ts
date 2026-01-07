/**
 * Cacherr API Service
 * 
 * Provides typed API calls to the Cacherr backend.
 */

import type {
  ApiResponse,
  CacheStats,
  CachedFilesResponse,
  CacheCycleResult,
  ReconciliationResult,
  EvictionResult,
  EvictionPreview,
  SessionsResponse,
  OnDeckResponse,
  WatchlistResponse,
  CacherrConfig,
  CacherrStatus,
} from '../types/cache';

const API_BASE = '/api';

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });
    
    const data = await response.json();
    return data as ApiResponse<T>;
    
  } catch (error) {
    return {
      success: false,
      data: null,
      message: '',
      error: error instanceof Error ? error.message : 'Network error',
      timestamp: new Date().toISOString(),
    };
  }
}

// ============================================================
// Health & Status
// ============================================================

export async function getHealth(): Promise<ApiResponse<{ status: string }>> {
  return fetchApi('/health');
}

export async function getStatus(): Promise<ApiResponse<CacherrStatus>> {
  return fetchApi('/status');
}

// ============================================================
// Cache Statistics
// ============================================================

export async function getCacheStats(): Promise<ApiResponse<CacheStats>> {
  return fetchApi('/cache/stats');
}

export async function getCachedFiles(): Promise<ApiResponse<CachedFilesResponse>> {
  return fetchApi('/cache/files');
}

// ============================================================
// Cache Operations
// ============================================================

export async function runCacheCycle(): Promise<ApiResponse<CacheCycleResult>> {
  return fetchApi('/cache/cycle', { method: 'POST' });
}

export async function runReconciliation(): Promise<ApiResponse<ReconciliationResult>> {
  return fetchApi('/cache/reconcile', { method: 'POST' });
}

export async function triggerEviction(
  dryRun: boolean = false
): Promise<ApiResponse<EvictionResult | EvictionPreview>> {
  return fetchApi('/cache/evict', {
    method: 'POST',
    body: JSON.stringify({ dry_run: dryRun }),
  });
}

export async function uncacheFile(filePath: string): Promise<ApiResponse<void>> {
  // Remove leading slash for URL path
  const encodedPath = encodeURIComponent(filePath.replace(/^\//, ''));
  return fetchApi(`/cache/file/${encodedPath}`, { method: 'DELETE' });
}

// ============================================================
// Sessions
// ============================================================

export async function getSessions(): Promise<ApiResponse<SessionsResponse>> {
  return fetchApi('/sessions');
}

// ============================================================
// Media Lists
// ============================================================

export async function getOnDeck(): Promise<ApiResponse<OnDeckResponse>> {
  return fetchApi('/ondeck');
}

export async function getWatchlist(): Promise<ApiResponse<WatchlistResponse>> {
  return fetchApi('/watchlist');
}

// ============================================================
// Configuration
// ============================================================

export async function getConfig(): Promise<ApiResponse<CacherrConfig>> {
  return fetchApi('/config');
}

// ============================================================
// Polling Utilities
// ============================================================

export function createPoller<T>(
  fetchFn: () => Promise<ApiResponse<T>>,
  intervalMs: number = 5000
) {
  let timer: ReturnType<typeof setInterval> | null = null;
  let subscribers: ((data: T | null, error: string | null) => void)[] = [];
  
  const poll = async () => {
    const response = await fetchFn();
    
    if (response.success && response.data) {
      subscribers.forEach(cb => cb(response.data, null));
    } else {
      subscribers.forEach(cb => cb(null, response.error));
    }
  };
  
  return {
    start() {
      if (timer) return;
      poll(); // Initial fetch
      timer = setInterval(poll, intervalMs);
    },
    
    stop() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
    },
    
    subscribe(callback: (data: T | null, error: string | null) => void) {
      subscribers.push(callback);
      return () => {
        subscribers = subscribers.filter(cb => cb !== callback);
      };
    },
    
    isRunning() {
      return timer !== null;
    },
  };
}

// Create pre-configured pollers
export const statusPoller = createPoller(getStatus, 5000);
export const statsPoller = createPoller(getCacheStats, 10000);
export const sessionsPoller = createPoller(getSessions, 5000);

// ============================================================
// Export all as single object
// ============================================================

export const api = {
  getHealth,
  getStatus,
  getCacheStats,
  getCachedFiles,
  runCacheCycle,
  runReconciliation,
  triggerEviction,
  uncacheFile,
  getSessions,
  getOnDeck,
  getWatchlist,
  getConfig,
};

export default api;
