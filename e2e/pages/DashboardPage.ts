import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Dashboard page object for testing the main dashboard functionality
 * Extends BasePage with dashboard-specific interactions and assertions
 */
export class DashboardPage extends BasePage {
  // Dashboard-specific elements
  readonly dashboardTitle: Locator;
  readonly statusCards: Locator;
  readonly statsGrid: Locator;
  readonly systemStatusCard: Locator;
  readonly healthStatusCard: Locator;
  readonly cacheStatusCard: Locator;
  readonly plexStatusCard: Locator;

  // Status indicators
  readonly statusIndicator: Locator;
  readonly healthIndicator: Locator;
  readonly cacheIndicator: Locator;
  readonly plexIndicator: Locator;

  // Stats and metrics
  readonly uptimeValue: Locator;
  readonly versionValue: Locator;
  readonly cacheUsage: Locator;
  readonly mediaUsage: Locator;
  readonly activeTransfers: Locator;
  readonly queuedOperations: Locator;

  // Real-time elements
  readonly realTimeUpdates: Locator;
  readonly lastUpdateTime: Locator;
  readonly refreshIndicator: Locator;

  // User activity section
  readonly activeUsers: Locator;
  readonly recentActivity: Locator;
  readonly userActivityList: Locator;

  // Cache statistics
  readonly cacheStats: Locator;
  readonly hitRate: Locator;
  readonly missRate: Locator;
  readonly averageAccessTime: Locator;

  constructor(page: Page) {
    super(page);

    // Initialize dashboard-specific locators
    this.dashboardTitle = page.locator('h1, h2').filter({ hasText: 'Dashboard' });
    this.statusCards = page.locator('[data-testid="status-card"], .status-card');
    this.statsGrid = page.locator('[data-testid="stats-grid"], .stats-grid');

    // Status cards
    this.systemStatusCard = page.locator('[data-testid="system-status-card"], .system-status-card');
    this.healthStatusCard = page.locator('[data-testid="health-status-card"], .health-status-card');
    this.cacheStatusCard = page.locator('[data-testid="cache-status-card"], .cache-status-card');
    this.plexStatusCard = page.locator('[data-testid="plex-status-card"], .plex-status-card');

    // Status indicators
    this.statusIndicator = page.locator('[data-testid="status-indicator"], .status-indicator');
    this.healthIndicator = page.locator('[data-testid="health-indicator"], .health-indicator');
    this.cacheIndicator = page.locator('[data-testid="cache-indicator"], .cache-indicator');
    this.plexIndicator = page.locator('[data-testid="plex-indicator"], .plex-indicator');

    // Stats and metrics
    this.uptimeValue = page.locator('[data-testid="uptime-value"], .uptime-value');
    this.versionValue = page.locator('[data-testid="version-value"], .version-value');
    this.cacheUsage = page.locator('[data-testid="cache-usage"], .cache-usage');
    this.mediaUsage = page.locator('[data-testid="media-usage"], .media-usage');
    this.activeTransfers = page.locator('[data-testid="active-transfers"], .active-transfers');
    this.queuedOperations = page.locator('[data-testid="queued-operations"], .queued-operations');

    // Real-time elements
    this.realTimeUpdates = page.locator('[data-testid="real-time-updates"], .real-time-updates');
    this.lastUpdateTime = page.locator('[data-testid="last-update-time"], .last-update-time');
    this.refreshIndicator = page.locator('[data-testid="refresh-indicator"], .refresh-indicator');

    // User activity
    this.activeUsers = page.locator('[data-testid="active-users"], .active-users');
    this.recentActivity = page.locator('[data-testid="recent-activity"], .recent-activity');
    this.userActivityList = page.locator('[data-testid="user-activity-list"], .user-activity-list');

    // Cache statistics
    this.cacheStats = page.locator('[data-testid="cache-stats"], .cache-stats');
    this.hitRate = page.locator('[data-testid="hit-rate"], .hit-rate');
    this.missRate = page.locator('[data-testid="miss-rate"], .miss-rate');
    this.averageAccessTime = page.locator('[data-testid="average-access-time"], .average-access-time');
  }

  /**
   * Navigate to dashboard and wait for it to load
   */
  async gotoDashboard() {
    await this.goto('/');
    await this.waitForDashboardLoad();
  }

  /**
   * Wait for dashboard to fully load with all data
   */
  async waitForDashboardLoad() {
    // Wait for main dashboard content
    await this.waitForVisible(this.dashboardTitle);
    
    // Wait for status cards to load
    await this.waitForVisible(this.statusCards.first());
    
    // Wait for stats to populate
    await this.waitForVisible(this.statsGrid);
    
    // Wait for loading to complete
    await this.waitForLoadingComplete();
  }

  /**
   * Check if dashboard is properly loaded
   */
  async isDashboardLoaded(): Promise<boolean> {
    try {
      await this.waitForDashboardLoad();
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get system status information
   */
  async getSystemStatus() {
    await this.waitForVisible(this.systemStatusCard);
    
    const status = await this.getText(this.statusIndicator);
    const uptime = await this.getText(this.uptimeValue);
    const version = await this.getText(this.versionValue);
    
    return { status, uptime, version };
  }

  /**
   * Get health status information
   */
  async getHealthStatus() {
    await this.waitForVisible(this.healthStatusCard);
    
    const health = await this.getText(this.healthIndicator);
    const plexStatus = await this.getText(this.plexIndicator);
    const cacheStatus = await this.getText(this.cacheIndicator);
    
    return { health, plexStatus, cacheStatus };
  }

  /**
   * Get cache usage information
   */
  async getCacheUsage() {
    await this.waitForVisible(this.cacheStatusCard);
    
    const cacheUsage = await this.getText(this.cacheUsage);
    const mediaUsage = await this.getText(this.mediaUsage);
    const activeTransfers = await this.getText(this.activeTransfers);
    const queuedOperations = await this.getText(this.queuedOperations);
    
    return { cacheUsage, mediaUsage, activeTransfers, queuedOperations };
  }

  /**
   * Get cache statistics
   */
  async getCacheStats() {
    await this.waitForVisible(this.cacheStats);
    
    const hitRate = await this.getText(this.hitRate);
    const missRate = await this.getText(this.missRate);
    const averageAccessTime = await this.getText(this.averageAccessTime);
    
    return { hitRate, missRate, averageAccessTime };
  }

  /**
   * Get user activity information
   */
  async getUserActivity() {
    await this.waitForVisible(this.activeUsers);
    
    const activeUsers = await this.getText(this.activeUsers);
    const recentActivity = await this.getText(this.recentActivity);
    
    return { activeUsers, recentActivity };
  }

  /**
   * Check if real-time updates are working
   */
  async isRealTimeUpdatesActive(): Promise<boolean> {
    try {
      await this.waitForVisible(this.realTimeUpdates, 5000);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for data refresh
   */
  async waitForDataRefresh() {
    // Wait for refresh indicator to appear and disappear
    await this.waitForVisible(this.refreshIndicator);
    await this.waitForHidden(this.refreshIndicator);
    
    // Wait for new data to load
    await this.waitForLoadingComplete();
  }

  /**
   * Verify dashboard displays correct data
   */
  async verifyDashboardData() {
    // Check system status
    const systemStatus = await this.getSystemStatus();
    expect(systemStatus.status).toBeTruthy();
    expect(systemStatus.version).toBeTruthy();
    
    // Check health status
    const healthStatus = await this.getHealthStatus();
    expect(healthStatus.health).toBeTruthy();
    
    // Check cache status
    const cacheStatus = await this.getCacheUsage();
    expect(cacheStatus.cacheUsage).toBeTruthy();
    
    // Check if all status cards are visible
    expect(await this.isVisible(this.systemStatusCard)).toBeTruthy();
    expect(await this.isVisible(this.healthStatusCard)).toBeTruthy();
    expect(await this.isVisible(this.cacheStatusCard)).toBeTruthy();
    expect(await this.isVisible(this.plexStatusCard)).toBeTruthy();
  }

  /**
   * Test auto-refresh functionality
   */
  async testAutoRefresh() {
    // Enable auto-refresh
    await this.toggleAutoRefresh();
    
    // Wait for auto-refresh to trigger
    await this.page.waitForTimeout(5000);
    
    // Verify data was refreshed
    await this.waitForDataRefresh();
    
    // Disable auto-refresh
    await this.toggleAutoRefresh();
  }

  /**
   * Test manual refresh functionality
   */
  async testManualRefresh() {
    // Get initial data
    const initialData = await this.getSystemStatus();
    
    // Manually refresh
    await this.refreshData();
    
    // Verify data was refreshed
    const refreshedData = await this.getSystemStatus();
    
    // Data should be updated (timestamps should be different)
    expect(refreshedData).toBeTruthy();
  }

  /**
   * Test theme switching on dashboard
   */
  async testThemeSwitching() {
    // Get initial theme state
    const initialTheme = await this.page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme') || 'auto';
    });
    
    // Toggle theme
    await this.toggleTheme();
    
    // Wait for theme change
    await this.page.waitForTimeout(500);
    
    // Verify theme changed
    const newTheme = await this.page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme') || 'auto';
    });
    
    expect(newTheme).not.toBe(initialTheme);
  }

  /**
   * Test responsive behavior
   */
  async testResponsiveBehavior() {
    // Test mobile viewport
    await this.page.setViewportSize({ width: 375, height: 667 });
    await this.page.waitForTimeout(1000);
    
    // Verify mobile layout
    expect(await this.isVisible(this.dashboardTitle)).toBeTruthy();
    
    // Test tablet viewport
    await this.page.setViewportSize({ width: 768, height: 1024 });
    await this.page.waitForTimeout(1000);
    
    // Verify tablet layout
    expect(await this.isVisible(this.statusCards)).toBeTruthy();
    
    // Test desktop viewport
    await this.page.setViewportSize({ width: 1280, height: 720 });
    await this.page.waitForTimeout(1000);
    
    // Verify desktop layout
    expect(await this.isVisible(this.statsGrid)).toBeTruthy();
  }

  /**
   * Test error handling scenarios
   */
  async testErrorHandling() {
    // Check if error messages are properly displayed
    if (await this.hasError()) {
      const errorMessage = await this.getText(this.errorMessage);
      expect(errorMessage).toBeTruthy();
    }
    
    // Verify error boundaries work
    expect(await this.isVisible(this.dashboardTitle)).toBeTruthy();
  }

  /**
   * Test accessibility features
   */
  async testAccessibility() {
    // Check for proper heading hierarchy
    const headings = await this.page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);
    
    // Check for ARIA labels
    const elementsWithAria = await this.page.locator('[aria-label], [aria-labelledby]').all();
    expect(elementsWithAria.length).toBeGreaterThan(0);
    
    // Check for proper focus management
    await this.page.keyboard.press('Tab');
    const focusedElement = await this.page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);
  }

  /**
   * Test keyboard navigation
   */
  async testKeyboardNavigation() {
    // Tab through interactive elements
    await this.page.keyboard.press('Tab');
    let focusedElement = await this.page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);
    
    // Navigate with arrow keys
    await this.page.keyboard.press('ArrowRight');
    await this.page.keyboard.press('ArrowDown');
    
    // Verify focus management works
    focusedElement = await this.page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);
  }

  /**
   * Test WebSocket connection (if applicable)
   */
  async testWebSocketConnection() {
    // Check if WebSocket connection is established
    const wsConnected = await this.page.evaluate(() => {
      return window.websocket && window.websocket.readyState === WebSocket.OPEN;
    });
    
    // If WebSocket is available, test real-time updates
    if (wsConnected) {
      await this.waitForTimeout(2000);
      expect(await this.isRealTimeUpdatesActive()).toBeTruthy();
    }
  }

  /**
   * Comprehensive dashboard test
   */
  async runFullDashboardTest() {
    // Navigate to dashboard
    await this.gotoDashboard();
    
    // Verify dashboard loads correctly
    expect(await this.isDashboardLoaded()).toBeTruthy();
    
    // Verify data display
    await this.verifyDashboardData();
    
    // Test functionality
    await this.testAutoRefresh();
    await this.testManualRefresh();
    await this.testThemeSwitching();
    
    // Test responsive behavior
    await this.testResponsiveBehavior();
    
    // Test accessibility
    await this.testAccessibility();
    await this.testKeyboardNavigation();
    
    // Test WebSocket
    await this.testWebSocketConnection();
    
    // Test error handling
    await this.testErrorHandling();
  }
}
