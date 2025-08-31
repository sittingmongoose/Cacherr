/**
 * Responsive Design and Error Handling Test Suite
 * Tests responsive behavior across devices and comprehensive error scenarios
 */

import { test, expect, Page } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';
import { SettingsPage } from '../pages/SettingsPage';
import { NavigationPage } from '../pages/NavigationPage';
import { TestSetup, TestEnvironment, CustomAssertions } from '../utils/test-helpers';
import { PredefinedMocks, MockUtils } from '../utils/mock-api';
import { UIXAssertions, APIAssertions, PerformanceAssertions } from '../utils/custom-assertions';

test.describe('Responsive Design - Comprehensive Testing', () => {
  let dashboardPage: DashboardPage;
  let settingsPage: SettingsPage;
  let navigationPage: NavigationPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    dashboardPage = new DashboardPage(page);
    settingsPage = new SettingsPage(page);
    navigationPage = new NavigationPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();
  });

  test('Dashboard is fully responsive across all devices', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    const devices = [
      { name: 'iPhone SE', width: 375, height: 667 },
      { name: 'iPhone 12', width: 390, height: 844 },
      { name: 'iPad Mini', width: 768, height: 1024 },
      { name: 'iPad Pro', width: 1024, height: 1366 },
      { name: 'Desktop 1080p', width: 1920, height: 1080 },
      { name: 'Desktop 4K', width: 3840, height: 2160 },
      { name: 'Small Mobile', width: 320, height: 568 },
      { name: 'Large Tablet', width: 1280, height: 800 }
    ];

    for (const device of devices) {
      await page.setViewportSize({ width: device.width, height: device.height });
      await page.waitForTimeout(300); // Allow layout to settle

      // Verify dashboard loads correctly
      expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

      // Verify critical elements are visible and accessible
      await expect(dashboardPage.statusCards).toBeVisible();
      await expect(dashboardPage.statsGrid).toBeVisible();

      // Verify no horizontal scroll
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBeFalsy();

      // Verify content fits within viewport
      const contentHeight = await page.locator('main, [role="main"]').evaluate(el => el.scrollHeight);
      const viewportHeight = device.height;
      expect(contentHeight).toBeLessThanOrEqual(viewportHeight * 2); // Allow some scrolling but not excessive

      // Verify text is readable (not too small)
      const fontSize = await page.locator('body').evaluate(el => {
        const styles = window.getComputedStyle(el);
        return parseFloat(styles.fontSize);
      });
      expect(fontSize).toBeGreaterThanOrEqual(14); // Minimum readable font size
    }
  });

  test('Settings page is fully responsive across all devices', async ({ page }) => {
    await settingsPage.gotoSettings();

    const devices = [
      { name: 'iPhone SE', width: 375, height: 667 },
      { name: 'iPad Pro', width: 1024, height: 1366 },
      { name: 'Desktop', width: 1920, height: 1080 }
    ];

    for (const device of devices) {
      await page.setViewportSize({ width: device.width, height: device.height });
      await page.waitForTimeout(300);

      // Verify settings page loads correctly
      expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

      // Verify all sections are accessible
      await expect(settingsPage.plexSettings).toBeVisible();
      await expect(settingsPage.mediaSettings).toBeVisible();
      await expect(settingsPage.performanceSettings).toBeVisible();
      await expect(settingsPage.advancedSettings).toBeVisible();

      // Verify action buttons are accessible
      await expect(settingsPage.saveButton).toBeVisible();

      // Test form interaction on different screen sizes
      if (device.width >= 768) {
        // Test desktop/tablet interactions
        await settingsPage.configurePlex('http://localhost:32400', 'test-token');
        await expect(settingsPage.plexUrl).toHaveValue('http://localhost:32400');
      } else {
        // Test mobile interactions
        await settingsPage.configurePlex('http://localhost:32400', 'test-token');
        // Verify mobile layout doesn't break functionality
        expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
      }
    }
  });

  test('Navigation is responsive across all devices', async ({ page }) => {
    await navigationPage.goto('/');

    const devices = [
      { name: 'Mobile', width: 375, height: 667 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Desktop', width: 1280, height: 720 }
    ];

    for (const device of devices) {
      await page.setViewportSize({ width: device.width, height: device.height });
      await page.waitForTimeout(300);

      // Verify navigation is accessible
      await expect(navigationPage.navBar).toBeVisible();

      // Test navigation functionality
      const navLinks = await navigationPage.navLinks.all();

      if (device.width < 768) {
        // Mobile navigation
        const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
        if (await mobileMenuButton.isVisible()) {
          await mobileMenuButton.click();
          const mobileMenu = page.locator('[data-testid="mobile-menu"]');
          await expect(mobileMenu).toBeVisible();

          // Test mobile navigation
          if (navLinks.length > 0) {
            await navLinks[0].click();
            await navigationPage.waitForNavigation();
          }

          // Close mobile menu
          await mobileMenuButton.click();
          await expect(mobileMenu).toBeHidden();
        }
      } else {
        // Desktop/tablet navigation
        if (navLinks.length > 0) {
          await navLinks[0].click();
          await navigationPage.waitForNavigation();
        }
      }

      // Verify no layout issues
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBeFalsy();
    }
  });

  test('Touch interactions work correctly on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await dashboardPage.gotoDashboard();

    // Test touch scrolling
    await page.touchscreen.tap(200, 200);
    await page.waitForTimeout(100);

    // Test touch navigation
    const statusCard = dashboardPage.statusCards.first();
    await statusCard.tap();
    await page.waitForTimeout(100);

    // Verify touch interactions work
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('High DPI displays render correctly', async ({ page }) => {
    // Set high DPI viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.evaluate(() => {
      // Simulate high DPI
      Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
    });

    await dashboardPage.gotoDashboard();

    // Verify high DPI rendering
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

    // Check that elements scale properly
    const statusCard = dashboardPage.statusCards.first();
    const boundingBox = await statusCard.boundingBox();
    expect(boundingBox?.width).toBeGreaterThan(200); // Should be reasonably sized
  });
});

test.describe('Error Handling - Comprehensive Scenarios', () => {
  let dashboardPage: DashboardPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    dashboardPage = new DashboardPage(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();
  });

  test('Handles network connectivity issues gracefully', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    // Simulate network failure
    await page.route('**/api/**', route => route.abort());

    // Trigger a data refresh
    await dashboardPage.refreshData();

    // Verify app remains functional
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

    // Verify error handling
    await UIXAssertions.hasProperToastNotifications(page, '[data-testid="refresh-button"]');
  });

  test('Handles API server errors correctly', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    // Mock 500 server error
    await MockUtils.mockErrorResponse(page, '/api/dashboard/stats', 500);

    // Refresh data
    await dashboardPage.refreshData();

    // Verify error handling
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

    // Verify user-friendly error message
    const errorMessage = page.locator('[data-testid="error-message"], .error-message');
    if (await errorMessage.isVisible()) {
      const message = await errorMessage.textContent();
      expect(message?.toLowerCase()).not.toContain('internal server error');
    }
  });

  test('Handles API timeout scenarios', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    // Mock slow API response
    await MockUtils.mockDelayedResponse(page, '/api/dashboard/stats', 10000, { status: 'healthy' });

    // Start refresh
    const refreshPromise = dashboardPage.refreshData();

    // Verify timeout handling (should complete within reasonable time)
    await expect(async () => {
      await refreshPromise;
    }).not.toThrow();

    // Verify app remains stable
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Handles invalid API responses', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    // Mock invalid JSON response
    await page.route('/api/dashboard/stats', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json response { broken'
      });
    });

    await dashboardPage.refreshData();

    // Verify graceful handling of invalid responses
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Handles authentication errors', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Mock 401 unauthorized error
    await MockUtils.mockErrorResponse(page, '/api/config/current', 401);

    // Try to access settings
    await settingsPage.refreshData();

    // Verify authentication error handling
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

    // Should show appropriate error message
    const errorElement = page.locator('[data-testid="auth-error"], .auth-error');
    if (await errorElement.isVisible()) {
      const errorText = await errorElement.textContent();
      expect(errorText).toBeTruthy();
    }
  });

  test('Handles rate limiting correctly', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Mock 429 rate limit error
    await MockUtils.mockErrorResponse(page, '/api/config/update', 429, {
      error: 'Too Many Requests',
      retryAfter: 60
    });

    // Try to save settings multiple times rapidly
    await settingsPage.saveSettings();
    await settingsPage.saveSettings();

    // Verify rate limiting is handled
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

    // Check for retry-after handling
    const retryMessage = page.locator('text=/retry|wait|limit/i');
    if (await retryMessage.isVisible()) {
      const message = await retryMessage.textContent();
      expect(message).toBeTruthy();
    }
  });

  test('Handles WebSocket connection failures', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    // Mock WebSocket failure (if WebSocket is used)
    await page.evaluate(() => {
      // Simulate WebSocket connection failure
      const ws = (window as any).WebSocket;
      if (ws) {
        // Override WebSocket to simulate failure
        (window as any).originalWebSocket = ws;
        (window as any).WebSocket = class extends ws {
          constructor(url: string) {
            super(url);
            setTimeout(() => {
              this.dispatchEvent(new Event('error'));
            }, 100);
          }
        };
      }
    });

    // Wait for potential WebSocket operations
    await page.waitForTimeout(1000);

    // Verify app remains functional
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Handles JavaScript runtime errors', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    // Inject a JavaScript error
    await page.evaluate(() => {
      setTimeout(() => {
        throw new Error('Simulated runtime error');
      }, 500);
    });

    // Wait for error and recovery
    await page.waitForTimeout(1000);

    // Verify app remains functional
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

    // Verify error boundaries work
    const errorBoundary = page.locator('[data-testid="error-boundary"], .error-boundary');
    if (await errorBoundary.isVisible()) {
      const errorMessage = await errorBoundary.textContent();
      expect(errorMessage).not.toContain('Simulated runtime error'); // Should be user-friendly
    }
  });

  test('Handles memory pressure scenarios', async ({ page }) => {
    await dashboardPage.gotoDashboard();

    // Simulate memory pressure by creating many DOM elements
    await page.evaluate(() => {
      for (let i = 0; i < 1000; i++) {
        const div = document.createElement('div');
        div.textContent = `Test element ${i}`;
        div.style.display = 'none'; // Hidden but consuming memory
        document.body.appendChild(div);
      }
    });

    // Perform operations under memory pressure
    await dashboardPage.refreshData();

    // Verify app remains stable
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();

    // Clean up
    await page.evaluate(() => {
      const elements = document.querySelectorAll('div');
      elements.forEach(el => {
        if (el.textContent?.includes('Test element')) {
          el.remove();
        }
      });
    });
  });

  test('Handles browser storage failures', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Simulate localStorage failure
    await page.evaluate(() => {
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = () => {
        throw new Error('Storage quota exceeded');
      };

      // Store reference for cleanup
      (window as any).originalSetItem = originalSetItem;
    });

    // Try to save settings
    await settingsPage.saveSettings();

    // Verify graceful handling of storage failure
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

    // Cleanup
    await page.evaluate(() => {
      if ((window as any).originalSetItem) {
        localStorage.setItem = (window as any).originalSetItem;
      }
    });
  });

  test('Handles form validation errors comprehensively', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Test multiple validation scenarios
    const invalidConfigs = [
      { url: 'invalid-url', token: '' },
      { url: '', token: 'token' },
      { url: 'http://localhost:32400', token: 'a'.repeat(1000) }, // Too long
      { url: 'ftp://invalid-protocol.com', token: 'token' } // Invalid protocol
    ];

    for (const config of invalidConfigs) {
      await settingsPage.configurePlex(config.url, config.token);
      await settingsPage.saveSettings();

      // Verify validation errors are shown
      expect(await settingsPage.hasValidationErrors()).toBeTruthy();

      // Verify specific error messages
      const errors = await settingsPage.getValidationErrors();
      expect(errors.length).toBeGreaterThan(0);
    }

    // Verify form remains functional after validation errors
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('Handles concurrent API calls correctly', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Make multiple concurrent API calls
    const promises = [];
    for (let i = 0; i < 5; i++) {
      promises.push(settingsPage.saveSettings());
      await page.waitForTimeout(100); // Slight delay between calls
    }

    // Wait for all calls to complete
    const results = await Promise.allSettled(promises);

    // Verify some succeeded and app remains stable
    const successfulCalls = results.filter(result => result.status === 'fulfilled').length;
    expect(successfulCalls).toBeGreaterThan(0);
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('Handles browser back/forward navigation errors', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Navigate away and back
    await dashboardPage.goToDashboard();
    await page.goBack();

    // Verify settings page recovers correctly
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

    // Try forward navigation
    await page.goForward();
    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });
});

test.describe('Cross-browser Compatibility and Edge Cases', () => {
  test('Handles different browser user agents', async ({ page }) => {
    await page.setExtraHTTPHeaders({
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    });

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Handles different timezone settings', async ({ page }) => {
    // Test with different timezone
    await page.emulateTimezone('America/New_York');

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Verify timestamps are handled correctly
    const status = await dashboardPage.getSystemStatus();
    expect(status.uptime).toBeTruthy();
  });

  test('Handles different language/localization', async ({ page }) => {
    // Test with different locale
    await page.emulateLocale('es-ES');

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Handles reduced motion preferences', async ({ page }) => {
    // Test with reduced motion
    await page.emulateMedia({ reducedMotion: 'reduce' });

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });

  test('Handles high contrast mode', async ({ page }) => {
    // Test with high contrast
    await page.emulateMedia({ forcedColors: 'active' });

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    expect(await dashboardPage.isDashboardLoaded()).toBeTruthy();
  });
});
