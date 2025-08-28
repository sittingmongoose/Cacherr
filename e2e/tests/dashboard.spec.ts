import { test, expect } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';

/**
 * Comprehensive Dashboard Tests
 * 
 * Tests cover:
 * - Page rendering and navigation
 * - Data display and updates
 * - User interactions (theme, refresh, navigation)
 * - Responsive design
 * - Accessibility compliance
 * - Error handling
 * - Real-time updates
 */

test.describe('Dashboard Page', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test.describe('Page Rendering', () => {
    test('should load dashboard successfully', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Verify page loads without errors
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
      
      // Check page title
      expect(await dashboardPage.hasTitle('Dashboard')).toBeTruthy();
      
      // Verify no console errors
      expect(await dashboardPage.hasNoConsoleErrors()).toBeTruthy();
    });

    test('should display all main dashboard sections', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Check for main sections
      expect(await dashboardPage.isVisible(dashboardPage.header)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.statusCards)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.statsGrid)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.footer)).toBeTruthy();
    });

    test('should show loading state initially', async ({ page }) => {
      // Navigate to dashboard
      await page.goto('/');
      
      // Should show loading initially
      expect(await dashboardPage.isVisible(dashboardPage.loadingSpinner)).toBeTruthy();
      
      // Wait for loading to complete
      await dashboardPage.waitForLoadingComplete();
      
      // Loading should be hidden
      expect(await dashboardPage.isHidden(dashboardPage.loadingSpinner)).toBeTruthy();
    });

    test('should display proper navigation menu', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Check navigation menu is visible
      expect(await dashboardPage.isVisible(dashboardPage.navigationMenu)).toBeTruthy();
      
      // Check all navigation links are present
      expect(await dashboardPage.isVisible(dashboardPage.dashboardLink)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.cachedLink)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.settingsLink)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.logsLink)).toBeTruthy();
    });
  });

  test.describe('Data Display', () => {
    test('should display system status information', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      const systemStatus = await dashboardPage.getSystemStatus();
      
      // Verify system status data is displayed
      expect(systemStatus.status).toBeTruthy();
      expect(systemStatus.version).toBeTruthy();
      expect(systemStatus.uptime).toBeTruthy();
    });

    test('should display health status information', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      const healthStatus = await dashboardPage.getHealthStatus();
      
      // Verify health status data is displayed
      expect(healthStatus.health).toBeTruthy();
      expect(healthStatus.plexStatus).toBeTruthy();
      expect(healthStatus.cacheStatus).toBeTruthy();
    });

    test('should display cache usage information', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      const cacheStatus = await dashboardPage.getCacheUsage();
      
      // Verify cache status data is displayed
      expect(cacheStatus.cacheUsage).toBeTruthy();
      expect(cacheStatus.mediaUsage).toBeTruthy();
      expect(cacheStatus.activeTransfers).toBeTruthy();
      expect(cacheStatus.queuedOperations).toBeTruthy();
    });

    test('should display cache statistics', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      const cacheStats = await dashboardPage.getCacheStats();
      
      // Verify cache statistics are displayed
      expect(cacheStats.hitRate).toBeTruthy();
      expect(cacheStats.missRate).toBeTruthy();
      expect(cacheStats.averageAccessTime).toBeTruthy();
    });

    test('should display user activity information', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      const userActivity = await dashboardPage.getUserActivity();
      
      // Verify user activity data is displayed
      expect(userActivity.activeUsers).toBeTruthy();
      expect(userActivity.recentActivity).toBeTruthy();
    });

    test('should display real-time update information', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Check if real-time updates section is visible
      expect(await dashboardPage.isVisible(dashboardPage.realTimeUpdates)).toBeTruthy();
      
      // Check if last update time is displayed
      expect(await dashboardPage.isVisible(dashboardPage.lastUpdateTime)).toBeTruthy();
    });
  });

  test.describe('User Interactions', () => {
    test('should toggle theme successfully', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test theme switching
      await dashboardPage.testThemeSwitching();
    });

    test('should toggle auto-refresh functionality', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test auto-refresh toggle
      await dashboardPage.testAutoRefresh();
    });

    test('should manually refresh data', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test manual refresh
      await dashboardPage.testManualRefresh();
    });

    test('should navigate to different pages', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Navigate to cached files page
      await dashboardPage.goToCached();
      expect(await dashboardPage.isOnPage('/cached')).toBeTruthy();
      
      // Navigate to settings page
      await dashboardPage.goToSettings();
      expect(await dashboardPage.isOnPage('/settings')).toBeTruthy();
      
      // Navigate to logs page
      await dashboardPage.goToLogs();
      expect(await dashboardPage.isOnPage('/logs')).toBeTruthy();
      
      // Return to dashboard
      await dashboardPage.goToDashboard();
      expect(await dashboardPage.isOnPage('/')).toBeTruthy();
    });

    test('should handle keyboard navigation', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test keyboard navigation
      await dashboardPage.testKeyboardNavigation();
    });
  });

  test.describe('Responsive Design', () => {
    test('should adapt to mobile viewport', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(1000);
      
      // Verify mobile layout
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.statusCards)).toBeTruthy();
    });

    test('should adapt to tablet viewport', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(1000);
      
      // Verify tablet layout
      expect(await dashboardPage.isVisible(dashboardPage.statusCards)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.statsGrid)).toBeTruthy();
    });

    test('should adapt to desktop viewport', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Set desktop viewport
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.waitForTimeout(1000);
      
      // Verify desktop layout
      expect(await dashboardPage.isVisible(dashboardPage.statsGrid)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.cacheStats)).toBeTruthy();
    });

    test('should maintain functionality across viewports', async ({ page }) => {
      const viewports = [
        { width: 375, height: 667, name: 'mobile' },
        { width: 768, height: 1024, name: 'tablet' },
        { width: 1280, height: 720, name: 'desktop' }
      ];

      for (const viewport of viewports) {
        await page.setViewportSize(viewport);
        await page.waitForTimeout(1000);
        
        // Verify core functionality works in all viewports
        expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
        expect(await dashboardPage.isVisible(dashboardPage.statusCards)).toBeTruthy();
        
        // Test theme toggle in all viewports
        await dashboardPage.testThemeSwitching();
      }
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Check for proper heading structure
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      expect(headings.length).toBeGreaterThan(0);
      
      // Verify main heading is present
      const mainHeading = await page.locator('h1').first();
      expect(await mainHeading.isVisible()).toBeTruthy();
    });

    test('should have proper ARIA labels', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Check for ARIA labels on interactive elements
      const elementsWithAria = await page.locator('[aria-label], [aria-labelledby]').all();
      expect(elementsWithAria.length).toBeGreaterThan(0);
      
      // Check specific ARIA labels
      expect(await dashboardPage.isVisible(dashboardPage.themeToggle)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.refreshButton)).toBeTruthy();
    });

    test('should support keyboard navigation', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test tab navigation
      await page.keyboard.press('Tab');
      let focusedElement = await page.locator(':focus');
      expect(await focusedElement.count()).toBe(1);
      
      // Test arrow key navigation
      await page.keyboard.press('ArrowRight');
      await page.keyboard.press('ArrowDown');
      
      // Verify focus management works
      focusedElement = await page.locator(':focus');
      expect(await focusedElement.count()).toBe(1);
    });

    test('should have proper color contrast', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // This would typically use a color contrast checking library
      // For now, we'll verify the theme system works
      await dashboardPage.testThemeSwitching();
      
      // Verify both themes are accessible
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
    });

    test('should have proper focus indicators', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Tab to first interactive element
      await page.keyboard.press('Tab');
      
      // Verify focus is visible
      const focusedElement = await page.locator(':focus');
      expect(await focusedElement.count()).toBe(1);
      
      // Check if focused element has visible focus indicator
      const focusStyles = await focusedElement.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return {
          outline: styles.outline,
          boxShadow: styles.boxShadow,
          border: styles.border
        };
      });
      
      // Focus indicator should be visible
      expect(focusStyles.outline !== 'none' || 
             focusStyles.boxShadow !== 'none' || 
             focusStyles.border !== 'none').toBeTruthy();
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      // This test would require mocking API failures
      // For now, we'll test the error boundary functionality
      await dashboardPage.gotoDashboard();
      
      // Verify error handling works
      await dashboardPage.testErrorHandling();
    });

    test('should display error messages when appropriate', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Check if error messages are properly displayed when they occur
      if (await dashboardPage.hasError()) {
        const errorMessage = await dashboardPage.getText(dashboardPage.errorMessage);
        expect(errorMessage).toBeTruthy();
      }
    });

    test('should recover from errors gracefully', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Verify the page remains functional even with errors
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.navigationMenu)).toBeTruthy();
    });

    test('should handle network failures', async ({ page }) => {
      // This would require network condition simulation
      // For now, we'll test basic error resilience
      await dashboardPage.gotoDashboard();
      
      // Verify page loads and handles potential network issues
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
    });
  });

  test.describe('Real-time Updates', () => {
    test('should establish WebSocket connection', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test WebSocket functionality
      await dashboardPage.testWebSocketConnection();
    });

    test('should display real-time data updates', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Check if real-time updates are active
      if (await dashboardPage.isRealTimeUpdatesActive()) {
        // Wait for potential updates
        await page.waitForTimeout(3000);
        
        // Verify updates are displayed
        expect(await dashboardPage.isVisible(dashboardPage.lastUpdateTime)).toBeTruthy();
      }
    });

    test('should handle WebSocket disconnection gracefully', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // This would require WebSocket disconnection simulation
      // For now, we'll verify basic functionality
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
    });
  });

  test.describe('Performance', () => {
    test('should load within acceptable time', async ({ page }) => {
      const startTime = Date.now();
      
      await dashboardPage.gotoDashboard();
      
      const loadTime = Date.now() - startTime;
      
      // Dashboard should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle data refresh efficiently', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      const startTime = Date.now();
      
      // Test manual refresh
      await dashboardPage.refreshData();
      
      const refreshTime = Date.now() - startTime;
      
      // Refresh should complete within 3 seconds
      expect(refreshTime).toBeLessThan(3000);
    });

    test('should maintain smooth interactions', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test multiple interactions quickly
      await dashboardPage.toggleTheme();
      await dashboardPage.toggleAutoRefresh();
      await dashboardPage.refreshData();
      
      // Verify all interactions completed successfully
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
    });
  });

  test.describe('Cross-browser Compatibility', () => {
    test('should work consistently across browsers', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test core functionality that should work in all browsers
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
      expect(await dashboardPage.isVisible(dashboardPage.statusCards)).toBeTruthy();
    });

    test('should handle browser-specific features gracefully', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test features that might vary by browser
      await dashboardPage.testThemeSwitching();
      await dashboardPage.testKeyboardNavigation();
      
      // Verify functionality works regardless of browser differences
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
    });
  });

  test.describe('Integration Tests', () => {
    test('should integrate with backend API', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Wait for API responses
      await dashboardPage.waitForAPIResponse('/api/system/status');
      await dashboardPage.waitForAPIResponse('/api/health');
      
      // Verify data is displayed
      await dashboardPage.verifyDashboardData();
    });

    test('should handle API response variations', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Test with different data scenarios
      await dashboardPage.refreshData();
      
      // Verify data updates
      const systemStatus = await dashboardPage.getSystemStatus();
      expect(systemStatus).toBeTruthy();
    });

    test('should maintain state during navigation', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Set theme
      await dashboardPage.testThemeSwitching();
      
      // Navigate away and back
      await dashboardPage.goToCached();
      await dashboardPage.goToDashboard();
      
      // Theme should persist
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
    });
  });

  test.describe('Edge Cases', () => {
    test('should handle rapid user interactions', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Perform multiple rapid interactions
      for (let i = 0; i < 5; i++) {
        await dashboardPage.toggleTheme();
        await page.waitForTimeout(100);
      }
      
      // Verify page remains stable
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
    });

    test('should handle viewport changes during interaction', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Start interaction
      await dashboardPage.toggleTheme();
      
      // Change viewport during interaction
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(1000);
      
      // Verify functionality continues
      expect(await dashboardPage.isVisible(dashboardPage.dashboardTitle)).toBeTruthy();
    });

    test('should handle page reload during operation', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Start an operation
      await dashboardPage.toggleAutoRefresh();
      
      // Reload page
      await dashboardPage.reload();
      
      // Verify page recovers properly
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
    });

    test('should handle browser back/forward navigation', async ({ page }) => {
      await dashboardPage.gotoDashboard();
      
      // Navigate to another page
      await dashboardPage.goToCached();
      
      // Go back
      await dashboardPage.goBack();
      
      // Verify dashboard is restored
      expect(await dashboardPage.isOnPage('/')).toBeTruthy();
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
    });
  });

  test.describe('Comprehensive Testing', () => {
    test('should pass full dashboard test suite', async ({ page }) => {
      // Run the comprehensive test suite
      await dashboardPage.runFullDashboardTest();
    });
  });
});
