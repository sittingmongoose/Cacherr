/**
 * API mocking utilities for Playwright tests
 * Provides comprehensive mocking capabilities for backend API responses
 */

import { Page, Route, Request } from '@playwright/test';
import testData from '../fixtures/test-data.json';

/**
 * Mock API response configuration
 */
export interface MockAPIConfig {
  url: string | RegExp;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  status?: number;
  response?: any;
  delay?: number;
  headers?: Record<string, string>;
  once?: boolean; // Only respond once
}

/**
 * API Mock Manager class
 */
export class APIMockManager {
  private mocks: Map<string, MockAPIConfig[]> = new Map();
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Add a mock API response
   */
  addMock(config: MockAPIConfig): void {
    const key = this.getMockKey(config.url, config.method);
    const existing = this.mocks.get(key) || [];
    existing.push(config);
    this.mocks.set(key, existing);
  }

  /**
   * Remove a mock API response
   */
  removeMock(url: string | RegExp, method: string = 'GET'): void {
    const key = this.getMockKey(url, method);
    this.mocks.delete(key);
  }

  /**
   * Clear all mocks
   */
  clearMocks(): void {
    this.mocks.clear();
  }

  /**
   * Setup all mocks
   */
  async setupMocks(): Promise<void> {
    // Setup route handlers for all mocks
    for (const [key, configs] of this.mocks.entries()) {
      await this.setupRouteHandler(key, configs);
    }
  }

  /**
   * Setup route handler for mocks
   */
  private async setupRouteHandler(key: string, configs: MockAPIConfig[]): Promise<void> {
    const [url, method] = key.split('|');

    await this.page.route(url, async (route: Route) => {
      const request = route.request();

      // Find matching config
      const config = configs.find(c =>
        (!c.method || c.method === request.method()) &&
        this.matchesUrl(request.url(), c.url)
      );

      if (config) {
        // Apply delay if specified
        if (config.delay) {
          await this.page.waitForTimeout(config.delay);
        }

        // Fulfill the route
        await route.fulfill({
          status: config.status || 200,
          contentType: 'application/json',
          body: JSON.stringify(config.response || {}),
          headers: {
            'Content-Type': 'application/json',
            ...config.headers
          }
        });

        // Remove mock if it's a one-time mock
        if (config.once) {
          configs.splice(configs.indexOf(config), 1);
          if (configs.length === 0) {
            this.mocks.delete(key);
          }
        }
      } else {
        // Continue with original request if no mock matches
        await route.continue();
      }
    });
  }

  /**
   * Get mock key for storage
   */
  private getMockKey(url: string | RegExp, method: string = 'GET'): string {
    const urlString = url instanceof RegExp ? url.source : url;
    return `${urlString}|${method}`;
  }

  /**
   * Check if URL matches pattern
   */
  private matchesUrl(requestUrl: string, pattern: string | RegExp): boolean {
    if (pattern instanceof RegExp) {
      return pattern.test(requestUrl);
    }
    return requestUrl.includes(pattern);
  }
}

/**
 * Predefined API mocks for common endpoints
 */
export class PredefinedMocks {
  private mockManager: APIMockManager;

  constructor(page: Page) {
    this.mockManager = new APIMockManager(page);
  }

  /**
   * Setup all predefined mocks
   */
  async setupAllMocks(): Promise<void> {
    await this.setupHealthMocks();
    await this.setupDashboardMocks();
    await this.setupSettingsMocks();
    await this.setupCachedFilesMocks();
    await this.setupLogsMocks();
    await this.setupErrorMocks();
  }

  /**
   * Setup health endpoint mocks
   */
  async setupHealthMocks(): Promise<void> {
    // Health endpoint
    this.mockManager.addMock({
      url: '/api/health',
      method: 'GET',
      response: {
        status: 'healthy',
        uptime: '1d 2h 30m',
        version: '1.0.0',
        timestamp: new Date().toISOString()
      }
    });

    // Health check with different states
    this.mockManager.addMock({
      url: '/api/health?state=degraded',
      method: 'GET',
      response: {
        status: 'degraded',
        uptime: '1d 2h 30m',
        version: '1.0.0',
        issues: ['Database connection slow'],
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Setup dashboard endpoint mocks
   */
  async setupDashboardMocks(): Promise<void> {
    // Dashboard stats
    this.mockManager.addMock({
      url: '/api/dashboard/stats',
      method: 'GET',
      response: {
        system: {
          uptime: '1d 2h 30m',
          version: '1.0.0',
          cpu: 45,
          memory: 67
        },
        cache: {
          totalSize: '2.5 GB',
          fileCount: 1250,
          hitRate: '94.2%',
          efficiency: '87.5%'
        },
        activity: {
          activeTransfers: 3,
          queuedOperations: 12,
          recentActivity: [
            { action: 'cached', file: 'movie.mp4', timestamp: '2024-01-15T10:30:00Z' },
            { action: 'copied', file: 'series.mkv', timestamp: '2024-01-15T10:25:00Z' }
          ]
        }
      }
    });

    // Real-time updates
    this.mockManager.addMock({
      url: '/api/dashboard/realtime',
      method: 'GET',
      response: {
        timestamp: new Date().toISOString(),
        updates: [
          { type: 'cache_hit', file: 'movie.mp4', size: '2.1 GB' },
          { type: 'transfer_complete', file: 'series.mkv', duration: '45s' }
        ]
      }
    });
  }

  /**
   * Setup settings endpoint mocks
   */
  async setupSettingsMocks(): Promise<void> {
    // Get current settings
    this.mockManager.addMock({
      url: '/api/config/current',
      method: 'GET',
      response: {
        plex: {
          url: 'http://localhost:32400',
          token: 'test-token-123',
          connectionStatus: 'connected'
        },
        media: {
          paths: ['/mnt/media', '/mnt/cache'],
          extensions: 'mp4,mkv,avi,mp3',
          sizeLimit: '50',
          copyToCache: true,
          autoClean: false,
          watchedMove: true
        },
        performance: {
          cacheConcurrency: 4,
          arrayConcurrency: 2,
          networkConcurrency: 8
        },
        advanced: {
          monitoringInterval: '30',
          logLevel: 'info',
          logRotation: '7'
        }
      }
    });

    // Update settings
    this.mockManager.addMock({
      url: '/api/config/update',
      method: 'POST',
      response: {
        success: true,
        message: 'Settings updated successfully',
        timestamp: new Date().toISOString()
      }
    });

    // Test Plex connection
    this.mockManager.addMock({
      url: '/api/config/test-plex',
      method: 'POST',
      response: {
        success: true,
        message: 'Plex connection successful',
        serverInfo: {
          name: 'Test Plex Server',
          version: '1.32.0',
          platform: 'Linux'
        }
      }
    });
  }

  /**
   * Setup cached files endpoint mocks
   */
  async setupCachedFilesMocks(): Promise<void> {
    // Get cached files list
    this.mockManager.addMock({
      url: '/api/cached-files',
      method: 'GET',
      response: {
        files: [
          {
            id: 'file-1',
            name: 'The Matrix (1999).mp4',
            path: '/mnt/cache/movies/The Matrix (1999).mp4',
            size: '2.1 GB',
            cachedDate: '2024-01-15T10:30:00Z',
            lastAccess: '2024-01-15T14:20:00Z',
            status: 'cached'
          },
          {
            id: 'file-2',
            name: 'Breaking Bad S01E01.mkv',
            path: '/mnt/cache/series/Breaking Bad S01E01.mkv',
            size: '850 MB',
            cachedDate: '2024-01-15T09:15:00Z',
            lastAccess: '2024-01-15T13:45:00Z',
            status: 'cached'
          }
        ],
        pagination: {
          page: 1,
          pageSize: 20,
          total: 2,
          totalPages: 1
        },
        summary: {
          totalFiles: 2,
          totalSize: '2.95 GB',
          averageSize: '1.475 GB'
        }
      }
    });

    // Delete cached file
    this.mockManager.addMock({
      url: '/api/cached-files/file-1',
      method: 'DELETE',
      response: {
        success: true,
        message: 'File deleted successfully'
      }
    });
  }

  /**
   * Setup logs endpoint mocks
   */
  async setupLogsMocks(): Promise<void> {
    // Get logs
    this.mockManager.addMock({
      url: '/api/logs',
      method: 'GET',
      response: {
        logs: [
          {
            timestamp: '2024-01-15T14:30:00Z',
            level: 'INFO',
            message: 'Cache operation completed successfully',
            source: 'CacheEngine'
          },
          {
            timestamp: '2024-01-15T14:25:00Z',
            level: 'WARN',
            message: 'File access timeout',
            source: 'FileOperations'
          },
          {
            timestamp: '2024-01-15T14:20:00Z',
            level: 'ERROR',
            message: 'Failed to connect to Plex server',
            source: 'PlexOperations'
          }
        ],
        pagination: {
          page: 1,
          pageSize: 50,
          total: 3,
          totalPages: 1
        }
      }
    });
  }

  /**
   * Setup error response mocks
   */
  async setupErrorMocks(): Promise<void> {
    // API error responses
    this.mockManager.addMock({
      url: '/api/error-test',
      method: 'GET',
      status: 500,
      response: {
        error: 'Internal Server Error',
        message: 'Something went wrong on the server',
        timestamp: new Date().toISOString()
      }
    });

    // Network timeout
    this.mockManager.addMock({
      url: '/api/timeout-test',
      method: 'GET',
      delay: 30000, // 30 second delay
      response: {
        success: true,
        message: 'This should timeout'
      }
    });

    // Unauthorized access
    this.mockManager.addMock({
      url: '/api/unauthorized',
      method: 'GET',
      status: 401,
      response: {
        error: 'Unauthorized',
        message: 'Authentication required',
        timestamp: new Date().toISOString()
      }
    });

    // Not found
    this.mockManager.addMock({
      url: '/api/not-found',
      method: 'GET',
      status: 404,
      response: {
        error: 'Not Found',
        message: 'Resource not found',
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Get the mock manager instance
   */
  getMockManager(): APIMockManager {
    return this.mockManager;
  }
}

/**
 * Mock data generators for dynamic responses
 */
export class MockDataGenerator {
  /**
   * Generate mock cached files
   */
  static generateCachedFiles(count: number = 10) {
    const files = [];
    const fileNames = [
      'The Matrix (1999).mp4',
      'Inception (2010).mkv',
      'Breaking Bad S01E01.mkv',
      'Stranger Things S01E01.mp4',
      'The Dark Knight.mp4',
      'Pulp Fiction.avi',
      'Fight Club.mp4',
      'Interstellar.mkv',
      'The Shawshank Redemption.mp4',
      'The Godfather.mp4'
    ];

    for (let i = 0; i < count; i++) {
      const fileName = fileNames[i % fileNames.length];
      const size = Math.floor(Math.random() * 5000) + 500; // 500MB to 5GB
      const daysAgo = Math.floor(Math.random() * 30);

      files.push({
        id: `file-${i + 1}`,
        name: fileName,
        path: `/mnt/cache/movies/${fileName}`,
        size: `${size} MB`,
        cachedDate: new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000).toISOString(),
        lastAccess: new Date(Date.now() - Math.floor(Math.random() * 7) * 24 * 60 * 60 * 1000).toISOString(),
        status: 'cached'
      });
    }

    return {
      files,
      pagination: {
        page: 1,
        pageSize: 20,
        total: count,
        totalPages: Math.ceil(count / 20)
      },
      summary: {
        totalFiles: count,
        totalSize: `${files.reduce((sum, file) => sum + parseInt(file.size), 0)} MB`,
        averageSize: `${Math.floor(files.reduce((sum, file) => sum + parseInt(file.size), 0) / count)} MB`
      }
    };
  }

  /**
   * Generate mock system stats
   */
  static generateSystemStats() {
    return {
      system: {
        uptime: `${Math.floor(Math.random() * 30)}d ${Math.floor(Math.random() * 24)}h ${Math.floor(Math.random() * 60)}m`,
        version: '1.0.0',
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100)
      },
      cache: {
        totalSize: `${(Math.random() * 10).toFixed(1)} GB`,
        fileCount: Math.floor(Math.random() * 2000) + 500,
        hitRate: `${(Math.random() * 20 + 80).toFixed(1)}%`,
        efficiency: `${(Math.random() * 20 + 75).toFixed(1)}%`
      },
      activity: {
        activeTransfers: Math.floor(Math.random() * 10),
        queuedOperations: Math.floor(Math.random() * 50),
        recentActivity: Array.from({ length: 5 }, (_, i) => ({
          action: ['cached', 'copied', 'accessed'][Math.floor(Math.random() * 3)],
          file: `file_${i + 1}.mp4`,
          timestamp: new Date(Date.now() - i * 60000).toISOString()
        }))
      }
    };
  }

  /**
   * Generate mock log entries
   */
  static generateLogEntries(count: number = 20) {
    const levels = ['INFO', 'WARN', 'ERROR', 'DEBUG'];
    const messages = [
      'Cache operation completed successfully',
      'File access timeout occurred',
      'Failed to connect to Plex server',
      'New file cached successfully',
      'Cache cleanup completed',
      'Plex server connection restored',
      'File transfer completed',
      'Cache performance optimized',
      'System health check passed',
      'Configuration updated'
    ];
    const sources = ['CacheEngine', 'FileOperations', 'PlexOperations', 'WebSocketManager', 'SettingsManager'];

    const logs = [];
    for (let i = 0; i < count; i++) {
      logs.push({
        timestamp: new Date(Date.now() - i * 300000).toISOString(), // 5 minutes apart
        level: levels[Math.floor(Math.random() * levels.length)],
        message: messages[Math.floor(Math.random() * messages.length)],
        source: sources[Math.floor(Math.random() * sources.length)]
      });
    }

    return {
      logs,
      pagination: {
        page: 1,
        pageSize: 50,
        total: count,
        totalPages: Math.ceil(count / 50)
      }
    };
  }
}

/**
 * Convenience functions for common mocking scenarios
 */
export class MockUtils {
  /**
   * Mock successful API response
   */
  static async mockSuccessResponse(page: Page, url: string, data: any): Promise<void> {
    const mockManager = new APIMockManager(page);
    mockManager.addMock({
      url,
      method: 'GET',
      response: data
    });
    await mockManager.setupMocks();
  }

  /**
   * Mock API error response
   */
  static async mockErrorResponse(page: Page, url: string, status: number = 500, error: any = null): Promise<void> {
    const mockManager = new APIMockManager(page);
    mockManager.addMock({
      url,
      method: 'GET',
      status,
      response: error || { error: 'Test error' }
    });
    await mockManager.setupMocks();
  }

  /**
   * Mock network delay
   */
  static async mockDelayedResponse(page: Page, url: string, delay: number, data: any): Promise<void> {
    const mockManager = new APIMockManager(page);
    mockManager.addMock({
      url,
      method: 'GET',
      delay,
      response: data
    });
    await mockManager.setupMocks();
  }

  /**
   * Mock one-time response (responds only once)
   */
  static async mockOneTimeResponse(page: Page, url: string, data: any): Promise<void> {
    const mockManager = new APIMockManager(page);
    mockManager.addMock({
      url,
      method: 'GET',
      once: true,
      response: data
    });
    await mockManager.setupMocks();
  }
}

// Export all utilities
export {
  MockAPIConfig,
  APIMockManager,
  PredefinedMocks,
  MockDataGenerator,
  MockUtils
};
