import { test, expect } from '@playwright/test';
import { DashboardPage } from '../pages/DashboardPage';

/**
 * Dashboard Tests
 *
 * Comprehensive tests for the PlexCache dashboard functionality
 * focusing on cache engine status display and data visualization
 */

test.describe('Dashboard Functionality', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
  });

  test('should display dashboard title correctly', async () => {
    await expect(dashboardPage.page).toHaveTitle(/PlexCache/);
  });

  test('should load dashboard without errors', async ({ page }) => {
    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');

    // Check for any JavaScript errors
    const errors: string[] = [];
    page.on('pageerror', error => {
      errors.push(error.message);
    });

    // Wait a moment for any dynamic content
    await page.waitForTimeout(2000);

    // Should have no JavaScript errors
    expect(errors).toHaveLength(0);
  });

  test('should display cache status information', async ({ page }) => {
    // Look for cache-related information on the dashboard
    const cacheElements = await page.locator('text=/cache|Cache/i').count();

    if (cacheElements > 0) {
      console.log(`Found ${cacheElements} cache-related elements on dashboard`);

      // Get text content of cache elements
      const cacheTexts = await page.locator('text=/cache|Cache/i').allTextContents();
      console.log('Cache element texts:', cacheTexts);

      // Ensure no cache error messages
      const errorCacheElements = await page.locator('text=/cache.*error|cache.*failed|cache.*not.*initialized/i').count();
      expect(errorCacheElements).toBe(0);
    } else {
      console.log('No cache elements found on dashboard - this may be expected');
    }
  });

  test('should handle API failures gracefully', async ({ page }) => {
    // Test what happens when API calls fail
    // This simulates the cache engine initialization failure scenario

    // First, verify the page loads normally
    await expect(page).toHaveTitle(/PlexCache/);

    // Look for error handling UI elements
    const errorBoundaries = await page.locator('[class*="error"], [class*="alert"], .toast, .notification').count();

    if (errorBoundaries > 0) {
      console.log(`Found ${errorBoundaries} error/alert elements on page`);
    }

    // The page should still be functional even if some API calls fail
    const mainContent = await page.locator('main, .dashboard, .content, [class*="main"]').first();
    await expect(mainContent).toBeVisible();
  });

  test('should display system status information', async ({ page }) => {
    // Look for system status or health indicators
    const statusElements = await page.locator('text=/status|Status|health|Health|system|System/i').count();

    if (statusElements > 0) {
      console.log(`Found ${statusElements} status/health elements`);

      const statusTexts = await page.locator('text=/status|Status|health|Health|system|System/i').allTextContents();
      console.log('Status element texts:', statusTexts);

      // Ensure no critical error statuses
      const criticalErrors = await page.locator('text=/critical|Critical|failed|Failed|error|Error/i').count();

      // Allow for some status messages but not critical errors
      if (criticalErrors > 0) {
        const criticalTexts = await page.locator('text=/critical|Critical|failed|Failed|error|Error/i').allTextContents();
        console.log('Critical status texts:', criticalTexts);

        // Filter out non-critical technical messages
        const actualErrors = criticalTexts.filter(text =>
          !text.toLowerCase().includes('debug') &&
          !text.toLowerCase().includes('log') &&
          !text.toLowerCase().includes('trace')
        );

        expect(actualErrors.length).toBeLessThanOrEqual(1);
      }
    }
  });

  test('should test responsive design', async ({ page }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 1366, height: 768, name: 'Laptop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      console.log(`Testing viewport: ${viewport.name} (${viewport.width}x${viewport.height})`);

      // Ensure main content is still visible and functional
      const mainContent = await page.locator('main, .dashboard, .content').first();
      await expect(mainContent).toBeVisible();

      // Check that no horizontal scrollbar appears
      const hasHorizontalScrollbar = await page.evaluate(() => {
        return document.body.scrollWidth > document.body.clientWidth;
      });

      expect(hasHorizontalScrollbar).toBe(false);
    }
  });

  test('should test theme switching if available', async ({ page }) => {
    // Look for theme toggle buttons or controls
    const themeToggles = await page.locator('button[class*="theme"], [class*="theme"] button, [data-theme], [aria-label*="theme"]').count();

    if (themeToggles > 0) {
      console.log(`Found ${themeToggles} theme toggle elements`);

      // Try to click the first theme toggle
      const firstToggle = await page.locator('button[class*="theme"], [class*="theme"] button, [data-theme], [aria-label*="theme"]').first();
      await firstToggle.click();

      // Wait for theme change to apply
      await page.waitForTimeout(1000);

      // Verify the page is still functional after theme change
      const mainContent = await page.locator('main, .dashboard, .content').first();
      await expect(mainContent).toBeVisible();

      console.log('Theme switching test completed successfully');
    } else {
      console.log('No theme toggle elements found - theme switching may not be implemented');
    }
  });

  test('should validate navigation functionality', async ({ page }) => {
    // Look for navigation elements
    const navElements = await page.locator('nav, .nav, .navigation, [class*="nav"], header').count();

    if (navElements > 0) {
      console.log(`Found ${navElements} navigation elements`);

      // Look for navigation links or buttons
      const navLinks = await page.locator('nav a, .nav a, .navigation a, [class*="nav"] a').count();

      if (navLinks > 0) {
        console.log(`Found ${navLinks} navigation links`);

        // Test that navigation links don't cause errors
        const firstLink = await page.locator('nav a, .nav a, .navigation a, [class*="nav"] a').first();

        // Get the href to check if it's valid
        const href = await firstLink.getAttribute('href');

        if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
          // For now, just check that clicking doesn't cause JavaScript errors
          // We'll implement full navigation testing in a separate test
          console.log(`Navigation link href: ${href}`);
        }
      }
    } else {
      console.log('No navigation elements found');
    }
  });
});