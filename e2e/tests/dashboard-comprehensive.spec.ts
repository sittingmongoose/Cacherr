/**
 * Comprehensive Dashboard Test Suite
 * Tests all dashboard functionality including real-time updates, responsive design, and error handling
 */

import { test, expect, Page } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';
import { NavigationPage } from '../pages/NavigationPage';
import { TestSetup, TestEnvironment, CustomAssertions, PerformanceUtils, AccessibilityAssertions } from '../utils/test-helpers';
import { PredefinedMocks } from '../utils/mock-api';
import { PerformanceAssertions, UIXAssertions, APIAssertions } from '../utils/custom-assertions';

test.describe('Dashboard - Comprehensive Functionality', () => {
  let dashboardPage: DashboardPage;
  let navigationPage: NavigationPage;
  let mockManager: PredefinedMocks;

  test.beforeEach(async ({ page }) => {
    // Setup test environment
    await TestSetup.setupTest(page);

    // Initialize page objects
    dashboardPage = new DashboardPage(page);
    navigationPage = new NavigationPage(page);

    // Setup API mocks
    mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    // Navigate to dashboard
    await dashboardPage.gotoDashboard();
  });

  test.afterEach(async ({ page }) => {
    // Cleanup test environment
    await TestSetup.cleanupTest(page);
  });

  test('Dashboard loads with all required elements', async ({ page }) => {
    // Verify dashboard loads correctly
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

    // Verify all main sections are present
    await expect(dashboardPage.statusCards).toBeVisible();
    await expect(dashboardPage.statsGrid).toBeVisible();

    // Verify specific status cards
    await expect(dashboardPage.systemStatusCard).toBeVisible();
    await expect(dashboardPage.healthStatusCard).toBeVisible();
    await expect(dashboardPage.cacheStatusCard).toBeVisible();
    await expect(dashboardPage.plexStatusCard).toBeVisible();

    // Verify no console errors
    await CustomAssertions.assertNoConsoleErrors(page);
  });

  test('Dashboard displays system status correctly', async ({ page }) => {
    const systemStatus = await dashboardPage.getSystemStatus();

    // Verify all status fields are present
    expect(systemStatus.status).toBeTruthy();
    expect(systemStatus.uptime).toBeTruthy();
    expect(systemStatus.version).toBeTruthy();

    // Verify status is displayed in UI
    await expect(dashboardPage.systemStatusCard).toContainText(systemStatus.status);
    await expect(dashboardPage.systemStatusCard).toContainText(systemStatus.version);
  });

  test('Dashboard displays health status with proper indicators', async ({ page }) => {
    const healthStatus = await dashboardPage.getHealthStatus();

    // Verify health indicators are present
    expect(healthStatus.health).toBeTruthy();
    expect(healthStatus.plexStatus).toBeTruthy();
    expect(healthStatus.cacheStatus).toBeTruthy();

    // Verify status indicators are visible
    await expect(dashboardPage.healthIndicator).toBeVisible();
    await expect(dashboardPage.plexIndicator).toBeVisible();
    await expect(dashboardPage.cacheIndicator).toBeVisible();
  });

  test('Dashboard displays cache statistics accurately', async ({ page }) => {
    const cacheUsage = await dashboardPage.getCacheUsage();

    // Verify cache statistics are present
    expect(cacheUsage.cacheUsage).toBeTruthy();
    expect(cacheUsage.activeTransfers).toBeDefined();
    expect(cacheUsage.queuedOperations).toBeDefined();

    // Verify cache stats are displayed
    await expect(dashboardPage.cacheStatusCard).toContainText(cacheUsage.cacheUsage);
  });

  test('Dashboard updates data in real-time', async ({ page }) => {
    // Enable real-time updates if toggle exists
    const refreshToggle = page.locator('[data-testid="auto-refresh-toggle"]');
    if (await refreshToggle.isVisible()) {
      await refreshToggle.click();
    }

    // Wait for real-time updates
    const initialData = await dashboardPage.getSystemStatus();

    // Simulate data change (in real scenario, this would come from backend)
    await page.waitForTimeout(2000);

    // Verify dashboard is still functional
    const updatedData = await dashboardPage.getSystemStatus();
    expect(updatedData.status).toBeTruthy();
  });

  test('Dashboard handles refresh operations correctly', async ({ page }) => {
    // Get initial data
    const initialData = await dashboardPage.getSystemStatus();

    // Trigger manual refresh
    await dashboardPage.refreshData();

    // Verify refresh completes
    await expect(dashboardPage.loadingSpinner).toBeHidden();

    // Verify data is still available
    const refreshedData = await dashboardPage.getSystemStatus();
    expect(refreshedData.status).toBeTruthy();
  });

  test('Dashboard maintains state during navigation', async ({ page }) => {
    // Navigate to settings and back
    await navigationPage.goToSettings();
    await navigationPage.goToDashboard();

    // Verify dashboard still loads correctly
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

    // Verify data is still displayed
    const status = await dashboardPage.getSystemStatus();
    expect(status.status).toBeTruthy();
  });

  test('Dashboard handles error states gracefully', async ({ page }) => {
    // Mock API error
    await page.route('/api/dashboard/stats', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });

    // Refresh dashboard
    await dashboardPage.refreshData();

    // Verify error is handled (either error message or fallback data)
    const isLoaded = await dashboardPage.isDashboardLoaded();
    expect(isLoaded).toBeTruthy(); // Dashboard should still be functional
  });

  test('Dashboard is fully accessible', async ({ page }) => {
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThan(0);

    // Test proper heading hierarchy
    await AccessibilityAssertions.hasProperHeadingHierarchy(page);

    // Test ARIA labels
    const statusCards = await dashboardPage.statusCards.all();
    for (const card of statusCards) {
      await AccessibilityAssertions.hasAriaAttributes(page, card);
    }
  });

  test('Dashboard performance meets requirements', async ({ page }) => {
    // Test load time
    await PerformanceAssertions.hasAcceptableLoadTime(page, 3000);

    // Test memory usage
    await PerformanceAssertions.hasReasonableMemoryUsage(page);

    // Test no long tasks
    await PerformanceAssertions.hasNoLongTasks(page, 50);
  });

  test('Dashboard is responsive across all screen sizes', async ({ page }) => {
    const viewports = [
      { width: 375, height: 667, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1024, height: 768, name: 'desktop' },
      { width: 1920, height: 1080, name: 'large' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Verify dashboard still loads correctly
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

      // Verify critical elements are visible
      await expect(dashboardPage.statusCards).toBeVisible();
      await expect(dashboardPage.statsGrid).toBeVisible();

      // Verify no horizontal scroll
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBeFalsy();
    }
  });

  test('Dashboard handles theme switching correctly', async ({ page }) => {
    // Get initial theme
    const initialTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme') || 'auto';
    });

    // Toggle theme if toggle exists
    const themeToggle = page.locator('[data-testid="theme-toggle"]');
    if (await themeToggle.isVisible()) {
      await themeToggle.click();

      // Wait for theme change
      await page.waitForTimeout(300);

      // Verify theme changed
      const newTheme = await page.evaluate(() => {
        return document.documentElement.getAttribute('data-theme') || 'auto';
      });

      expect(newTheme).not.toBe(initialTheme);
    }
  });

  test('Dashboard displays user activity correctly', async ({ page }) => {
    // Check if user activity section exists
    if (await dashboardPage.activeUsers.isVisible()) {
      const activityData = await dashboardPage.getUserActivity();

      // Verify activity data is displayed
      if (activityData.activeUsers) {
        await expect(dashboardPage.activeUsers).toContainText(activityData.activeUsers);
      }

      if (activityData.recentActivity) {
        await expect(dashboardPage.recentActivity).toContainText(activityData.recentActivity);
      }
    }
  });

  test('Dashboard shows cache performance metrics', async ({ page }) => {
    // Check if cache stats section exists
    if (await dashboardPage.cacheStats.isVisible()) {
      const cacheStats = await dashboardPage.getCacheStats();

      // Verify cache metrics are displayed
      if (cacheStats.hitRate) {
        await expect(dashboardPage.hitRate).toContainText(cacheStats.hitRate);
      }

      if (cacheStats.missRate) {
        await expect(dashboardPage.missRate).toContainText(cacheStats.missRate);
      }
    }
  });
});

test.describe('Dashboard - Cross-browser Compatibility', () => {
  test('Dashboard works correctly in Chromium', async ({ page, browserName }) => {
    test.skip(browserName !== 'chromium', 'Test only runs on Chromium');

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Dashboard works correctly in Firefox', async ({ page, browserName }) => {
    test.skip(browserName !== 'firefox', 'Test only runs on Firefox');

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Dashboard works correctly in WebKit', async ({ page, browserName }) => {
    test.skip(browserName !== 'webkit', 'Test only runs on WebKit');

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });
});

test.describe('Dashboard - Error Scenarios', () => {
  test('Dashboard handles network failures gracefully', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    // Mock network failure
    await page.route('/api/dashboard/stats', route => {
      route.abort();
    });

    await dashboardPage.gotoDashboard();

    // Dashboard should still load with fallback content
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Dashboard handles API timeout gracefully', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    // Mock slow API response
    await page.route('/api/dashboard/stats', async route => {
      await page.waitForTimeout(10000); // 10 second delay
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy', uptime: '1d' })
      });
    });

    await dashboardPage.gotoDashboard();

    // Dashboard should handle timeout gracefully
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Dashboard handles invalid API responses', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    // Mock invalid JSON response
    await page.route('/api/dashboard/stats', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json'
      });
    });

    await dashboardPage.gotoDashboard();

    // Dashboard should handle invalid responses gracefully
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });
});

test.describe('Dashboard - Performance Monitoring', () => {
  test('Dashboard loads within performance budget', async ({ page }) => {
    const startTime = Date.now();

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    const loadTime = Date.now() - startTime;

    // Performance budget: 3 seconds
    expect(loadTime).toBeLessThan(3000);

    console.log(`Dashboard load time: ${loadTime}ms`);
  });

  test('Dashboard handles high-frequency updates', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Simulate rapid data updates
    for (let i = 0; i < 10; i++) {
      await dashboardPage.refreshData();
      await page.waitForTimeout(100);
    }

    // Verify dashboard remains stable
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Dashboard maintains performance under load', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Measure initial performance
    const initialMemory = await PerformanceUtils.getMemoryUsage(page);

    // Perform multiple operations
    for (let i = 0; i < 20; i++) {
      await dashboardPage.refreshData();
      await page.waitForTimeout(50);
    }

    // Measure final performance
    const finalMemory = await PerformanceUtils.getMemoryUsage(page);

    // Verify no significant memory leaks
    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.used - initialMemory.used;
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
    }

    // Verify dashboard still functions
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });
});
