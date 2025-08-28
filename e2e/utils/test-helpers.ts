import { Page, expect } from '@playwright/test';
import testData from '../fixtures/test-data.json';

/**
 * Test utilities and helper functions for Playwright tests
 * Provides common functionality used across multiple test files
 */

/**
 * Wait for a specified amount of time
 */
export const wait = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Generate random test data
 */
export class TestDataGenerator {
  /**
   * Generate a random string of specified length
   */
  static randomString(length: number = 10): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  /**
   * Generate a random number between min and max
   */
  static randomNumber(min: number = 0, max: number = 100): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  /**
   * Generate a random date within a range
   */
  static randomDate(start: Date = new Date(2020, 0, 1), end: Date = new Date()): Date {
    return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
  }

  /**
   * Generate a random file size in bytes
   */
  static randomFileSize(minSize: number = 1024, maxSize: number = 1073741824): number {
    return Math.floor(Math.random() * (maxSize - minSize + 1)) + minSize;
  }

  /**
   * Generate a random IP address
   */
  static randomIP(): string {
    return `${this.randomNumber(1, 255)}.${this.randomNumber(0, 255)}.${this.randomNumber(0, 255)}.${this.randomNumber(1, 255)}`;
  }

  /**
   * Generate a random MAC address
   */
  static randomMAC(): string {
    const hexDigits = '0123456789ABCDEF';
    let mac = '';
    for (let i = 0; i < 6; i++) {
      if (i > 0) mac += ':';
      mac += hexDigits.charAt(Math.floor(Math.random() * 16));
      mac += hexDigits.charAt(Math.floor(Math.random() * 16));
    }
    return mac;
  }
}

/**
 * Custom assertions for common test scenarios
 */
export class CustomAssertions {
  /**
   * Assert that an element is visible and contains expected text
   */
  static async assertElementVisibleWithText(page: Page, selector: string, expectedText: string) {
    const element = page.locator(selector);
    await expect(element).toBeVisible();
    await expect(element).toContainText(expectedText);
  }

  /**
   * Assert that an element is hidden
   */
  static async assertElementHidden(page: Page, selector: string) {
    const element = page.locator(selector);
    await expect(element).toBeHidden();
  }

  /**
   * Assert that a page has no console errors
   */
  static async assertNoConsoleErrors(page: Page) {
    const errors: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Wait a bit for any console messages
    await wait(1000);
    
    expect(errors).toHaveLength(0);
  }

  /**
   * Assert that a page has no network errors
   */
  static async assertNoNetworkErrors(page: Page) {
    const errors: string[] = [];
    
    page.on('response', response => {
      if (response.status() >= 400) {
        errors.push(`${response.status()}: ${response.url()}`);
      }
    });

    // Wait a bit for any network requests
    await wait(1000);
    
    expect(errors).toHaveLength(0);
  }

  /**
   * Assert that a page loads within specified time
   */
  static async assertPageLoadsWithin(page: Page, maxLoadTime: number = 5000) {
    const startTime = Date.now();
    
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(maxLoadTime);
  }

  /**
   * Assert that an element has proper focus management
   */
  static async assertFocusManagement(page: Page, selector: string) {
    const element = page.locator(selector);
    
    // Focus the element
    await element.focus();
    
    // Check if it's focused
    await expect(element).toBeFocused();
    
    // Check if it has visible focus indicator
    const focusStyles = await element.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        boxShadow: styles.boxShadow,
        border: styles.border
      };
    });
    
    expect(
      focusStyles.outline !== 'none' || 
      focusStyles.boxShadow !== 'none' || 
      focusStyles.border !== 'none'
    ).toBeTruthy();
  }
}

/**
 * Test environment utilities
 */
export class TestEnvironment {
  /**
   * Check if running in CI environment
   */
  static isCI(): boolean {
    return process.env.CI === 'true' || process.env.GITHUB_ACTIONS === 'true';
  }

  /**
   * Check if running in Docker
   */
  static isDocker(): boolean {
    return process.env.DOCKER === 'true' || process.env.PLAYWRIGHT_DOCKER === 'true';
  }

  /**
   * Get test timeout based on environment
   */
  static getTestTimeout(): number {
    if (this.isCI()) {
      return 30000; // 30 seconds in CI
    }
    if (this.isDocker()) {
      return 20000; // 20 seconds in Docker
    }
    return 15000; // 15 seconds locally
  }

  /**
   * Get viewport size based on test type
   */
  static getViewportSize(type: 'mobile' | 'tablet' | 'desktop' = 'desktop') {
    const sizes = {
      mobile: { width: 375, height: 667 },
      tablet: { width: 768, height: 1024 },
      desktop: { width: 1280, height: 720 }
    };
    return sizes[type];
  }
}

/**
 * API testing utilities
 */
export class APITestUtils {
  /**
   * Mock API response for testing
   */
  static async mockAPIResponse(page: Page, urlPattern: string, response: any) {
    await page.route(urlPattern, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  /**
   * Mock API error for testing error handling
   */
  static async mockAPIError(page: Page, urlPattern: string, status: number = 500, error: any = null) {
    await page.route(urlPattern, route => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(error || { error: 'Test error' })
      });
    });
  }

  /**
   * Wait for API request to complete
   */
  static async waitForAPIRequest(page: Page, urlPattern: string, timeout: number = 10000) {
    await page.waitForResponse(
      response => response.url().includes(urlPattern),
      { timeout }
    );
  }

  /**
   * Get API response data
   */
  static async getAPIResponse(page: Page, urlPattern: string): Promise<any> {
    const response = await page.waitForResponse(
      response => response.url().includes(urlPattern)
    );
    return response.json();
  }
}

/**
 * Performance testing utilities
 */
export class PerformanceUtils {
  /**
   * Measure page load performance
   */
  static async measurePageLoad(page: Page): Promise<number> {
    const startTime = Date.now();
    
    await page.waitForLoadState('networkidle');
    
    return Date.now() - startTime;
  }

  /**
   * Measure interaction performance
   */
  static async measureInteraction(page: Page, action: () => Promise<void>): Promise<number> {
    const startTime = Date.now();
    
    await action();
    
    return Date.now() - startTime;
  }

  /**
   * Get memory usage (if available)
   */
  static async getMemoryUsage(page: Page): Promise<any> {
    try {
      return await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory;
        }
        return null;
      });
    } catch {
      return null;
    }
  }

  /**
   * Get performance metrics
   */
  static async getPerformanceMetrics(page: Page): Promise<any> {
    try {
      return await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        return {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
          firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
        };
      });
    } catch {
      return null;
    }
  }
}

/**
 * Accessibility testing utilities
 */
export class AccessibilityUtils {
  /**
   * Check if element has proper ARIA attributes
   */
  static async hasProperARIA(page: Page, selector: string): Promise<boolean> {
    try {
      const element = page.locator(selector);
      const ariaAttributes = await element.evaluate(el => {
        const attrs = el.getAttributeNames();
        return attrs.filter(attr => attr.startsWith('aria-'));
      });
      
      return ariaAttributes.length > 0;
    } catch {
      return false;
    }
  }

  /**
   * Check if element has proper focus management
   */
  static async hasProperFocus(page: Page, selector: string): Promise<boolean> {
    try {
      const element = page.locator(selector);
      await element.focus();
      
      const isFocused = await element.evaluate(el => el === document.activeElement);
      return isFocused;
    } catch {
      return false;
    }
  }

  /**
   * Check if page has proper heading hierarchy
   */
  static async hasProperHeadingHierarchy(page: Page): Promise<boolean> {
    try {
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      
      if (headings.length === 0) return false;
      
      // Check if first heading is h1
      const firstHeading = await headings[0].evaluate(el => el.tagName.toLowerCase());
      return firstHeading === 'h1';
    } catch {
      return false;
    }
  }
}

/**
 * Test data utilities
 */
export class TestDataUtils {
  /**
   * Get test data by key
   */
  static getTestData(key: string): any {
    return (testData as any)[key];
  }

  /**
   * Get system status test data
   */
  static getSystemStatusData() {
    return this.getTestData('systemStatus');
  }

  /**
   * Get health status test data
   */
  static getHealthStatusData() {
    return this.getTestData('healthStatus');
  }

  /**
   * Get cached files test data
   */
  static getCachedFilesData() {
    return this.getTestData('cachedFiles');
  }

  /**
   * Get error response test data
   */
  static getErrorResponseData(type: string = 'apiError') {
    return this.getTestData('errorResponses')[type];
  }
}

/**
 * Common test setup functions
 */
export class TestSetup {
  /**
   * Setup test environment
   */
  static async setupTest(page: Page) {
    // Set viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    
    // Set timeout
    page.setDefaultTimeout(TestEnvironment.getTestTimeout());
    
    // Listen for console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`Console Error: ${msg.text()}`);
      }
    });
    
    // Listen for page errors
    page.on('pageerror', error => {
      console.error(`Page Error: ${error.message}`);
    });
  }

  /**
   * Cleanup test environment
   */
  static async cleanupTest(page: Page) {
    // Close any open dialogs or modals
    try {
      await page.keyboard.press('Escape');
    } catch {}
    
    // Clear any stored data
    try {
      await page.evaluate(() => {
        localStorage.clear();
        sessionStorage.clear();
      });
    } catch {}
  }
}

// Export commonly used utilities
export {
  wait,
  TestDataGenerator,
  CustomAssertions,
  TestEnvironment,
  APITestUtils,
  PerformanceUtils,
  AccessibilityUtils,
  TestDataUtils,
  TestSetup
};
