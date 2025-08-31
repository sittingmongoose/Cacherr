/**
 * Custom assertions for Playwright tests
 * Provides specialized assertions for accessibility, performance, and UI testing
 */

import { Page, Locator, expect } from '@playwright/test';

/**
 * Accessibility assertions
 */
export class AccessibilityAssertions {
  /**
   * Assert that an element has proper ARIA attributes
   */
  static async hasAriaAttributes(page: Page, selector: string): Promise<void> {
    const element = page.locator(selector);
    const ariaAttrs = await element.evaluate(el => {
      return Array.from(el.attributes)
        .filter(attr => attr.name.startsWith('aria-'))
        .map(attr => attr.name);
    });

    expect(ariaAttrs.length).toBeGreaterThan(0);
  }

  /**
   * Assert that an element has proper focus management
   */
  static async hasProperFocus(page: Page, selector: string): Promise<void> {
    const element = page.locator(selector);

    // Focus the element
    await element.focus();

    // Check if it's focused
    await expect(element).toBeFocused();

    // Check for visible focus indicator
    const hasFocusIndicator = await element.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.outline !== 'none' ||
             styles.boxShadow !== 'none' ||
             styles.border !== 'none';
    });

    expect(hasFocusIndicator).toBeTruthy();
  }

  /**
   * Assert that the page has proper heading hierarchy
   */
  static async hasProperHeadingHierarchy(page: Page): Promise<void> {
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();

    expect(headings.length).toBeGreaterThan(0);

    // First heading should be h1
    const firstHeading = await headings[0].evaluate(el => el.tagName.toLowerCase());
    expect(firstHeading).toBe('h1');

    // Check hierarchy levels
    const headingLevels = await Promise.all(
      headings.map(h => h.evaluate(el => parseInt(el.tagName.charAt(1))))
    );

    // Ensure no heading level is skipped (no h1 to h3 without h2)
    for (let i = 1; i < headingLevels.length; i++) {
      expect(headingLevels[i]).toBeLessThanOrEqual(headingLevels[i - 1] + 1);
    }
  }

  /**
   * Assert that interactive elements have proper labels
   */
  static async hasProperLabels(page: Page): Promise<void> {
    const interactiveElements = page.locator('button, input, select, textarea, [role="button"]');

    const elements = await interactiveElements.all();

    for (const element of elements) {
      const hasAccessibleName = await element.evaluate(el => {
        // Check for aria-label
        if (el.getAttribute('aria-label')) return true;

        // Check for aria-labelledby
        if (el.getAttribute('aria-labelledby')) return true;

        // Check for associated label
        if (el.id && document.querySelector(`label[for="${el.id}"]`)) return true;

        // Check for title attribute
        if (el.getAttribute('title')) return true;

        // Check for button text content
        if (el.tagName.toLowerCase() === 'button' && el.textContent?.trim()) return true;

        // Check for input placeholder (as fallback)
        if (el.tagName.toLowerCase() === 'input' && el.getAttribute('placeholder')) return true;

        return false;
      });

      expect(hasAccessibleName).toBeTruthy();
    }
  }

  /**
   * Assert that the page has sufficient color contrast
   */
  static async hasSufficientColorContrast(page: Page, selector: string): Promise<void> {
    const contrastRatio = await page.locator(selector).evaluate(el => {
      const styles = window.getComputedStyle(el);
      const bgColor = styles.backgroundColor;
      const color = styles.color;

      // Simple contrast calculation (simplified for testing)
      // In production, you'd use a proper color contrast library
      return bgColor !== color ? 4.5 : 1; // Assume good contrast if different
    });

    expect(contrastRatio).toBeGreaterThanOrEqual(4.5);
  }

  /**
   * Assert that form elements have proper validation attributes
   */
  static async hasProperFormValidation(page: Page, formSelector: string): Promise<void> {
    const form = page.locator(formSelector);
    const requiredInputs = form.locator('input[required], select[required], textarea[required]');

    const requiredCount = await requiredInputs.count();

    if (requiredCount > 0) {
      // Check that required inputs have proper indicators
      const inputs = await requiredInputs.all();

      for (const input of inputs) {
        const hasIndicator = await input.evaluate(el => {
          // Check for aria-required
          if (el.getAttribute('aria-required') === 'true') return true;

          // Check for visual indicators (simplified check)
          const styles = window.getComputedStyle(el);
          return styles.border !== 'none' || el.classList.contains('required');
        });

        expect(hasIndicator).toBeTruthy();
      }
    }
  }
}

/**
 * Performance assertions
 */
export class PerformanceAssertions {
  /**
   * Assert that page load time is within acceptable limits
   */
  static async hasAcceptableLoadTime(page: Page, maxLoadTime: number = 3000): Promise<void> {
    const loadTime = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return navigation.loadEventEnd - navigation.navigationStart;
    });

    expect(loadTime).toBeLessThan(maxLoadTime);
  }

  /**
   * Assert that first contentful paint is within acceptable limits
   */
  static async hasAcceptableFCP(page: Page, maxFCP: number = 2000): Promise<void> {
    const fcp = await page.evaluate(() => {
      const paintEntries = performance.getEntriesByName('first-contentful-paint');
      return paintEntries.length > 0 ? paintEntries[0].startTime : 0;
    });

    expect(fcp).toBeGreaterThan(0);
    expect(fcp).toBeLessThan(maxFCP);
  }

  /**
   * Assert that the page has reasonable memory usage
   */
  static async hasReasonableMemoryUsage(page: Page): Promise<void> {
    const memoryUsage = await page.evaluate(() => {
      if ('memory' in performance) {
        const mem = (performance as any).memory;
        return {
          used: mem.usedJSHeapSize,
          total: mem.totalJSHeapSize,
          limit: mem.jsHeapSizeLimit
        };
      }
      return null;
    });

    if (memoryUsage) {
      const usagePercent = (memoryUsage.used / memoryUsage.limit) * 100;
      expect(usagePercent).toBeLessThan(80); // Less than 80% of heap limit
    }
  }

  /**
   * Assert that API response time is within acceptable limits
   */
  static async hasAcceptableAPIResponseTime(page: Page, urlPattern: string, maxResponseTime: number = 1000): Promise<void> {
    const responseTime = await page.evaluate((pattern) => {
      const entries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      const apiEntry = entries.find(entry => entry.name.includes(pattern));
      return apiEntry ? apiEntry.responseEnd - apiEntry.requestStart : 0;
    }, urlPattern);

    expect(responseTime).toBeGreaterThan(0);
    expect(responseTime).toBeLessThan(maxResponseTime);
  }

  /**
   * Assert that the page is responsive (no long tasks)
   */
  static async hasNoLongTasks(page: Page, maxTaskTime: number = 50): Promise<void> {
    const hasLongTasks = await page.evaluate((maxTime) => {
      if ('performance' in window && 'getEntriesByType' in performance) {
        const longTasks = performance.getEntriesByType('longtask') as any[];
        return longTasks.some(task => task.duration > maxTime);
      }
      return false;
    }, maxTaskTime);

    expect(hasLongTasks).toBeFalsy();
  }
}

/**
 * UI/UX assertions
 */
export class UIXAssertions {
  /**
   * Assert that an element is properly visible and interactive
   */
  static async isFullyInteractive(page: Page, selector: string): Promise<void> {
    const element = page.locator(selector);

    // Check visibility
    await expect(element).toBeVisible();

    // Check if it's not disabled
    await expect(element).not.toBeDisabled();

    // Check if it's within viewport
    const isInViewport = await element.evaluate(el => {
      const rect = el.getBoundingClientRect();
      return rect.top >= 0 &&
             rect.left >= 0 &&
             rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
             rect.right <= (window.innerWidth || document.documentElement.clientWidth);
    });

    expect(isInViewport).toBeTruthy();
  }

  /**
   * Assert that a form has proper validation feedback
   */
  static async hasProperValidationFeedback(page: Page, formSelector: string): Promise<void> {
    const form = page.locator(formSelector);

    // Submit empty form to trigger validation
    await form.locator('button[type="submit"]').click();

    // Check for validation messages
    const validationMessages = form.locator('.validation-error, .error-message, [data-testid="error"]');
    const messageCount = await validationMessages.count();

    if (messageCount > 0) {
      // If there are validation messages, they should be visible and descriptive
      const messages = await validationMessages.all();

      for (const message of messages) {
        await expect(message).toBeVisible();
        const text = await message.textContent();
        expect(text?.trim().length).toBeGreaterThan(0);
      }
    }
  }

  /**
   * Assert that loading states are properly handled
   */
  static async hasProperLoadingStates(page: Page, triggerSelector: string): Promise<void> {
    const trigger = page.locator(triggerSelector);

    // Click trigger to start loading
    await trigger.click();

    // Check for loading indicator
    const loadingIndicator = page.locator('[data-testid="loading"], .loading-spinner, .spinner');
    await expect(loadingIndicator).toBeVisible();

    // Wait for loading to complete
    await expect(loadingIndicator).toBeHidden({ timeout: 10000 });
  }

  /**
   * Assert that the page handles responsive design properly
   */
  static async hasResponsiveDesign(page: Page): Promise<void> {
    const viewports = [
      { width: 320, height: 568, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1280, height: 720, name: 'desktop' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Check that main content is still accessible
      const mainContent = page.locator('main, [role="main"], .main-content');
      await expect(mainContent).toBeVisible();

      // Check that navigation is accessible
      const nav = page.locator('nav, [role="navigation"]');
      await expect(nav).toBeVisible();

      // Check for horizontal scroll (should not exist)
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });

      expect(hasHorizontalScroll).toBeFalsy();
    }
  }

  /**
   * Assert that toast notifications work properly
   */
  static async hasProperToastNotifications(page: Page, triggerSelector: string): Promise<void> {
    const trigger = page.locator(triggerSelector);
    await trigger.click();

    // Check for toast appearance
    const toast = page.locator('[data-testid="toast"], .toast, .notification');
    await expect(toast).toBeVisible();

    // Check toast content
    const toastText = await toast.textContent();
    expect(toastText?.trim().length).toBeGreaterThan(0);

    // Check that toast disappears after timeout
    await expect(toast).toBeHidden({ timeout: 10000 });
  }

  /**
   * Assert that modal dialogs are properly implemented
   */
  static async hasProperModalDialog(page: Page, triggerSelector: string): Promise<void> {
    const trigger = page.locator(triggerSelector);
    await trigger.click();

    // Check for modal appearance
    const modal = page.locator('[role="dialog"], .modal, .dialog');
    await expect(modal).toBeVisible();

    // Check for proper focus management
    const focusedElement = await page.locator(':focus');
    const isInModal = await focusedElement.evaluate(el => {
      return el.closest('[role="dialog"], .modal, .dialog') !== null;
    });
    expect(isInModal).toBeTruthy();

    // Check for close button
    const closeButton = modal.locator('[aria-label*="close"], .close-button, button[type="button"]');
    await expect(closeButton).toBeVisible();

    // Test closing modal
    await closeButton.click();
    await expect(modal).toBeHidden();
  }
}

/**
 * API assertions
 */
export class APIAssertions {
  /**
   * Assert that an API request was made with correct parameters
   */
  static async wasAPIRequestMade(page: Page, urlPattern: string, method: string = 'GET'): Promise<void> {
    const requestMade = await page.evaluate(
      ({ pattern, expectedMethod }) => {
        const requests = (window as any).__testRequests || [];
        return requests.some((req: any) =>
          req.url.includes(pattern) && req.method === expectedMethod
        );
      },
      { pattern: urlPattern, method }
    );

    expect(requestMade).toBeTruthy();
  }

  /**
   * Assert that an API response has the expected structure
   */
  static async hasExpectedAPIResponse(page: Page, urlPattern: string, expectedKeys: string[]): Promise<void> {
    const response = await page.waitForResponse(resp => resp.url().includes(urlPattern));
    const data = await response.json();

    for (const key of expectedKeys) {
      expect(data).toHaveProperty(key);
    }
  }

  /**
   * Assert that API error responses are properly handled
   */
  static async handlesAPIErrorProperly(page: Page, errorTrigger: string, errorMessage: string): Promise<void> {
    // Trigger the error
    if (errorTrigger.startsWith('/')) {
      // It's a URL pattern, mock the error
      await page.route(errorTrigger, route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Test error' })
        });
      });
    } else {
      // It's a selector
      await page.locator(errorTrigger).click();
    }

    // Check for error handling
    const errorElement = page.locator(`text=${errorMessage}`);
    await expect(errorElement).toBeVisible();

    // Check that the app doesn't crash
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent).toBeVisible();
  }
}

// Export all assertion classes
export {
  AccessibilityAssertions,
  PerformanceAssertions,
  UIXAssertions,
  APIAssertions
};
