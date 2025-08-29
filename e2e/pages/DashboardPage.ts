import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Dashboard Page Object Model
 *
 * Provides specific functionality for the PlexCache dashboard page
 */
export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to the dashboard
   */
  async goto() {
    await super.goto('/');
    await this.waitForDashboardLoad();
  }

  /**
   * Wait for the dashboard to fully load
   */
  async waitForDashboardLoad() {
    await this.waitForPageLoad();

    // Wait for dashboard-specific elements
    const dashboardSelectors = [
      '.dashboard',
      '[class*="dashboard"]',
      'main',
      '.content',
      '[class*="main"]'
    ];

    for (const selector of dashboardSelectors) {
      if (await this.elementExists(selector)) {
        await this.waitForElement(selector);
        break;
      }
    }
  }

  /**
   * Check if the dashboard displays cache status
   */
  async hasCacheStatus(): Promise<boolean> {
    const cacheSelectors = [
      'text=/cache|Cache/i',
      '[class*="cache"]',
      '[data-cache]',
      '.cache-status',
      '.cache-info'
    ];

    for (const selector of cacheSelectors) {
      if (await this.elementExists(selector)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get cache status information
   */
  async getCacheStatus(): Promise<string[]> {
    const cacheElements = await this.page.locator('text=/cache|Cache/i').allTextContents();
    return cacheElements;
  }

  /**
   * Check for cache errors
   */
  async hasCacheErrors(): Promise<boolean> {
    const errorSelectors = [
      'text=/cache.*error|cache.*failed|cache.*not.*initialized/i',
      '.cache-error',
      '.cache-failed',
      '[class*="cache-error"]'
    ];

    for (const selector of errorSelectors) {
      if (await this.elementExists(selector)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get system status information
   */
  async getSystemStatus(): Promise<{ [key: string]: any }> {
    const status: { [key: string]: any } = {};

    // Look for status indicators
    const statusElements = await this.page.locator('text=/status|Status|health|Health/i').allTextContents();
    status.statusTexts = statusElements;

    // Check for error indicators
    const errorCount = await this.page.locator('text=/error|Error|failed|Failed/i').count();
    status.errorCount = errorCount;

    // Check for success indicators
    const successCount = await this.page.locator('text=/success|Success|ok|OK/i').count();
    status.successCount = successCount;

    return status;
  }

  /**
   * Test theme switching functionality
   */
  async testThemeSwitching(): Promise<boolean> {
    const themeToggles = await this.page.locator(
      'button[class*="theme"], [class*="theme"] button, [data-theme], [aria-label*="theme"]'
    ).count();

    if (themeToggles === 0) {
      console.log('No theme toggle found');
      return false;
    }

    // Get initial theme (check body class or data attribute)
    const initialTheme = await this.page.getAttribute('body', 'data-theme') ||
                        await this.page.getAttribute('body', 'class') ||
                        'unknown';

    // Click theme toggle
    await this.page.locator('button[class*="theme"], [class*="theme"] button, [data-theme], [aria-label*="theme"]').first().click();

    // Wait for theme change
    await this.page.waitForTimeout(1000);

    // Check if theme changed
    const newTheme = await this.page.getAttribute('body', 'data-theme') ||
                    await this.page.getAttribute('body', 'class') ||
                    'unknown';

    const themeChanged = initialTheme !== newTheme;
    console.log(`Theme switching: ${initialTheme} -> ${newTheme} (changed: ${themeChanged})`);

    return themeChanged;
  }

  /**
   * Test responsive design
   */
  async testResponsiveDesign(): Promise<{ [key: string]: boolean }> {
    const results: { [key: string]: boolean } = {};

    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 1366, height: 768, name: 'Laptop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      await this.page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Check for horizontal scrollbar
      const hasHorizontalScrollbar = await this.page.evaluate(() => {
        return document.body.scrollWidth > document.body.clientWidth;
      });

      // Check if main content is visible
      const mainContentVisible = await this.page.locator('main, .dashboard, .content').isVisible();

      results[viewport.name] = !hasHorizontalScrollbar && mainContentVisible;

      console.log(`${viewport.name} (${viewport.width}x${viewport.height}): ${results[viewport.name] ? 'PASS' : 'FAIL'}`);
    }

    return results;
  }

  /**
   * Check navigation functionality
   */
  async getNavigationElements(): Promise<string[]> {
    const navLinks = await this.page.locator('nav a, .nav a, .navigation a, [class*="nav"] a').allTextContents();
    return navLinks;
  }

  /**
   * Take dashboard screenshot
   */
  async takeDashboardScreenshot() {
    await this.takeScreenshot('dashboard-full');
  }

  /**
   * Get dashboard performance metrics
   */
  async getPerformanceMetrics(): Promise<{ [key: string]: number }> {
    const metrics = await this.page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
        loadComplete: perf.loadEventEnd - perf.loadEventStart,
        totalTime: perf.loadEventEnd - perf.fetchStart
      };
    });

    console.log('Dashboard performance metrics:', metrics);
    return metrics;
  }

  /**
   * Check for accessibility issues
   */
  async checkAccessibility(): Promise<{ [key: string]: number }> {
    const issues = {
      missingAlt: await this.page.locator('img:not([alt]), img[alt=""]').count(),
      missingLabels: await this.page.locator('input:not([aria-label]):not([aria-labelledby]):not([placeholder]), select:not([aria-label]):not([aria-labelledby]), textarea:not([aria-label]):not([aria-labelledby])').count(),
      lowContrast: 0, // Would need more complex analysis
      missingTitles: await this.page.locator('iframe:not([title]), frame:not([title])').count()
    };

    console.log('Accessibility check results:', issues);
    return issues;
  }
}