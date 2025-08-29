import { Page } from '@playwright/test';

/**
 * Base Page Object Model
 *
 * Provides common functionality for all pages in the application
 */
export class BasePage {
  protected page: Page;
  protected baseURL: string;

  constructor(page: Page, baseURL: string = 'http://192.168.50.223:5445') {
    this.page = page;
    this.baseURL = baseURL;
  }

  /**
   * Navigate to a specific path
   */
  async goto(path: string = '/') {
    await this.page.goto(`${this.baseURL}${path}`);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for the page to be fully loaded
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForTimeout(1000); // Additional wait for dynamic content
  }

  /**
   * Check if the page has any JavaScript errors
   */
  async getJavaScriptErrors(): Promise<string[]> {
    const errors: string[] = [];

    this.page.on('pageerror', error => {
      errors.push(error.message);
    });

    // Wait a moment to capture any errors
    await this.page.waitForTimeout(2000);

    return errors;
  }

  /**
   * Take a screenshot for debugging
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({
      path: `test-results/${name}.png`,
      fullPage: true
    });
  }

  /**
   * Check for console errors
   */
  async getConsoleErrors(): Promise<string[]> {
    const errors: string[] = [];

    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await this.page.waitForTimeout(2000);
    return errors;
  }

  /**
   * Wait for an element to be visible
   */
  async waitForElement(selector: string, timeout: number = 10000) {
    await this.page.waitForSelector(selector, { timeout });
  }

  /**
   * Check if an element exists
   */
  async elementExists(selector: string): Promise<boolean> {
    try {
      await this.page.waitForSelector(selector, { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get the page title
   */
  async getTitle(): Promise<string> {
    return await this.page.title();
  }

  /**
   * Check for network errors
   */
  async getNetworkErrors(): Promise<string[]> {
    const errors: string[] = [];

    this.page.on('response', response => {
      if (!response.ok() && response.status() >= 400) {
        errors.push(`${response.status()} ${response.statusText()}: ${response.url()}`);
      }
    });

    await this.page.waitForTimeout(2000);
    return errors;
  }

  /**
   * Wait for API calls to complete
   */
  async waitForAPICalls() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get all text content from the page
   */
  async getPageText(): Promise<string> {
    return await this.page.innerText('body');
  }

  /**
   * Check for specific error patterns
   */
  async hasErrorPattern(pattern: RegExp): Promise<boolean> {
    const pageText = await this.getPageText();
    return pattern.test(pageText);
  }

  /**
   * Get elements by text content
   */
  async getElementsByText(text: string | RegExp) {
    return await this.page.locator(`text=${text}`);
  }
}