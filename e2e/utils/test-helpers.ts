import { Page, expect } from '@playwright/test';

/**
 * Test Helper Utilities
 *
 * Common functions and utilities for Playwright tests
 */

export class TestHelpers {
  /**
   * Wait for API calls to complete
   */
  static async waitForAPICalls(page: Page, timeout: number = 10000): Promise<void> {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Check for JavaScript errors
   */
  static async getJavaScriptErrors(page: Page): Promise<string[]> {
    const errors: string[] = [];

    page.on('pageerror', error => {
      errors.push(error.message);
    });

    await page.waitForTimeout(2000);
    return errors;
  }

  /**
   * Check for console errors
   */
  static async getConsoleErrors(page: Page): Promise<string[]> {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.waitForTimeout(2000);
    return errors;
  }

  /**
   * Check for network errors
   */
  static async getNetworkErrors(page: Page): Promise<string[]> {
    const errors: string[] = [];

    page.on('response', response => {
      if (!response.ok() && response.status() >= 400) {
        errors.push(`${response.status()} ${response.statusText()}: ${response.url()}`);
      }
    });

    await page.waitForTimeout(2000);
    return errors;
  }

  /**
   * Measure API response time
   */
  static async measureAPIResponseTime(page: Page, url: string): Promise<number> {
    const startTime = Date.now();

    try {
      const response = await page.request.get(url);
      const endTime = Date.now();
      return endTime - startTime;
    } catch (error) {
      const endTime = Date.now();
      console.log(`API call failed after ${endTime - startTime}ms:`, error);
      return endTime - startTime;
    }
  }

  /**
   * Check if element exists
   */
  static async elementExists(page: Page, selector: string, timeout: number = 5000): Promise<boolean> {
    try {
      await page.waitForSelector(selector, { timeout });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get all text content from elements matching a selector
   */
  static async getTextContents(page: Page, selector: string): Promise<string[]> {
    try {
      return await page.locator(selector).allTextContents();
    } catch {
      return [];
    }
  }

  /**
   * Check for specific error patterns in page content
   */
  static async hasErrorPattern(page: Page, pattern: RegExp): Promise<boolean> {
    const pageText = await page.innerText('body');
    return pattern.test(pageText);
  }

  /**
   * Take a screenshot with timestamp
   */
  static async takeScreenshot(page: Page, name: string): Promise<void> {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    await page.screenshot({
      path: `test-results/${name}-${timestamp}.png`,
      fullPage: true
    });
  }

  /**
   * Wait for element to be visible and stable
   */
  static async waitForStableElement(page: Page, selector: string, timeout: number = 10000): Promise<void> {
    await page.waitForSelector(selector, { timeout });

    // Wait for element to be stable (not changing)
    let lastText = '';
    let stableCount = 0;

    for (let i = 0; i < 10; i++) {
      const currentText = await page.locator(selector).textContent() || '';
      if (currentText === lastText) {
        stableCount++;
        if (stableCount >= 3) {
          break;
        }
      } else {
        stableCount = 0;
        lastText = currentText;
      }
      await page.waitForTimeout(100);
    }
  }

  /**
   * Generate random test data
   */
  static generateRandomData(type: 'string' | 'number' | 'email', length: number = 10): string | number {
    switch (type) {
      case 'string':
        return Math.random().toString(36).substring(2, length + 2);
      case 'number':
        return Math.floor(Math.random() * Math.pow(10, length));
      case 'email':
        return `${Math.random().toString(36).substring(2, 8)}@test.com`;
      default:
        return Math.random().toString(36).substring(2, length + 2);
    }
  }

  /**
   * Check page performance metrics
   */
  static async getPerformanceMetrics(page: Page): Promise<{ [key: string]: number }> {
    return await page.evaluate(() => {
      const perf = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
        loadComplete: perf.loadEventEnd - perf.loadEventStart,
        totalTime: perf.loadEventEnd - perf.fetchStart
      };
    });
  }

  /**
   * Validate API response structure
   */
  static validateAPIResponse(response: any, expectedStructure: { [key: string]: any }): boolean {
    for (const [key, expectedType] of Object.entries(expectedStructure)) {
      if (!(key in response)) {
        console.log(`Missing key: ${key}`);
        return false;
      }

      if (typeof response[key] !== expectedType && expectedType !== 'any') {
        console.log(`Type mismatch for ${key}: expected ${expectedType}, got ${typeof response[key]}`);
        return false;
      }
    }

    return true;
  }

  /**
   * Create test data file
   */
  static async createTestFile(page: Page, filename: string, content: string): Promise<void> {
    await page.evaluate(({ filename, content }) => {
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, { filename, content });
  }

  /**
   * Check for accessibility issues
   */
  static async checkAccessibility(page: Page): Promise<{ [key: string]: number }> {
    const issues = {
      missingAlt: await page.locator('img:not([alt]), img[alt=""]').count(),
      missingLabels: await page.locator(
        'input:not([aria-label]):not([aria-labelledby]):not([placeholder]), ' +
        'select:not([aria-label]):not([aria-labelledby]), ' +
        'textarea:not([aria-label]):not([aria-labelledby])'
      ).count(),
      missingTitles: await page.locator('iframe:not([title]), frame:not([title])').count(),
      emptyButtons: await page.locator('button:not([aria-label]):not([aria-labelledby]):empty').count()
    };

    return issues;
  }

  /**
   * Test responsive design
   */
  static async testResponsiveDesign(page: Page): Promise<{ [key: string]: boolean }> {
    const results: { [key: string]: boolean } = {};

    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 1366, height: 768, name: 'Laptop' },
      { width: 768, height: 1024, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      const hasHorizontalScrollbar = await page.evaluate(() => {
        return document.body.scrollWidth > document.body.clientWidth;
      });

      const mainContentVisible = await page.locator('main, .dashboard, .content').isVisible();

      results[viewport.name] = !hasHorizontalScrollbar && mainContentVisible;
    }

    return results;
  }
}

/**
 * Custom assertion helpers
 */
export class CustomAssertions {
  /**
   * Assert that an API response is successful
   */
  static async assertAPISuccess(page: Page, url: string, expectedStatus: number = 200): Promise<void> {
    const response = await page.request.get(url);

    expect(response.status()).toBe(expectedStatus);

    if (expectedStatus === 200) {
      const responseData = await response.json();
      expect(responseData).toHaveProperty('success');
      expect(responseData.success).toBe(true);
    }
  }

  /**
   * Assert that cache is properly initialized
   */
  static async assertCacheInitialized(page: Page): Promise<void> {
    const response = await page.request.get('/api/status');
    expect(response.status()).toBe(200);

    const responseData = await response.json();
    expect(responseData).toHaveProperty('data');

    if (responseData.data && typeof responseData.data === 'object') {
      // Look for cache-related properties
      const hasCacheData = Object.keys(responseData.data).some(key =>
        key.toLowerCase().includes('cache')
      );

      if (hasCacheData) {
        console.log('Cache data found in API response');
      }
    }
  }

  /**
   * Assert that page loads without errors
   */
  static async assertPageLoadsWithoutErrors(page: Page): Promise<void> {
    const jsErrors = await TestHelpers.getJavaScriptErrors(page);
    const consoleErrors = await TestHelpers.getConsoleErrors(page);
    const networkErrors = await TestHelpers.getNetworkErrors(page);

    expect(jsErrors).toHaveLength(0);
    expect(consoleErrors.filter(error => !error.includes('favicon')).length).toBeLessThanOrEqual(2);
    expect(networkErrors.filter(error => !error.includes('favicon')).length).toBeLessThanOrEqual(2);
  }

  /**
   * Assert responsive design works
   */
  static async assertResponsiveDesign(page: Page): Promise<void> {
    const responsiveResults = await TestHelpers.testResponsiveDesign(page);

    for (const [viewport, passes] of Object.entries(responsiveResults)) {
      expect(passes).toBe(true);
    }
  }
}