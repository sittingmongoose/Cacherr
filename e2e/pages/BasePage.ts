import { Page, Locator, expect } from '@playwright/test';

/**
 * Base page object that provides common functionality for all pages
 * Implements the Page Object Model pattern for maintainable tests
 */
export class BasePage {
  protected page: Page;

  // Common navigation elements
  readonly navigationMenu: Locator;
  readonly dashboardLink: Locator;
  readonly cachedLink: Locator;
  readonly settingsLink: Locator;
  readonly logsLink: Locator;

  // Common UI elements
  readonly header: Locator;
  readonly footer: Locator;
  readonly loadingSpinner: Locator;
  readonly errorMessage: Locator;
  readonly toastContainer: Locator;

  // Theme and settings
  readonly themeToggle: Locator;
  readonly autoRefreshToggle: Locator;
  readonly refreshButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Initialize common locators
    this.navigationMenu = page.locator('nav[role="navigation"]');
    this.dashboardLink = page.locator('a[href="/"], a[href="/dashboard"]');
    this.cachedLink = page.locator('a[href="/cached"]');
    this.settingsLink = page.locator('a[href="/settings"]');
    this.logsLink = page.locator('a[href="/logs"]');

    this.header = page.locator('header, [role="banner"]');
    this.footer = page.locator('footer, [role="contentinfo"]');
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"], .loading-spinner');
    this.errorMessage = page.locator('[data-testid="error-message"], .error-message');
    this.toastContainer = page.locator('[data-testid="toast-container"], .toast-container');

    this.themeToggle = page.locator('[data-testid="theme-toggle"], [aria-label*="theme"]');
    this.autoRefreshToggle = page.locator('[data-testid="auto-refresh"], input[type="checkbox"]');
    this.refreshButton = page.locator('[data-testid="refresh-button"], [aria-label*="refresh"]');
  }

  /**
   * Navigate to the page
   */
  async goto(path: string = '/') {
    await this.page.goto(path);
    await this.waitForPageLoad();
  }

  /**
   * Wait for the page to fully load
   */
  async waitForPageLoad() {
    // Wait for network idle
    await this.page.waitForLoadState('networkidle');
    
    // Wait for main content to be visible
    await this.page.waitForSelector('main, [role="main"]', { timeout: 10000 });
    
    // Wait for any loading states to complete
    await this.waitForLoadingComplete();
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoadingComplete() {
    // Wait for loading spinner to disappear
    await this.page.waitForSelector('[data-testid="loading-spinner"], .loading-spinner', { 
      state: 'hidden', 
      timeout: 10000 
    }).catch(() => {
      // Loading spinner might not exist, which is fine
    });
  }

  /**
   * Navigate to dashboard
   */
  async goToDashboard() {
    await this.dashboardLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to cached files page
   */
  async goToCached() {
    await this.cachedLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to settings page
   */
  async goToSettings() {
    await this.settingsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to logs page
   */
  async goToLogs() {
    await this.logsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Toggle theme between light, dark, and auto
   */
  async toggleTheme() {
    await this.themeToggle.click();
    // Wait for theme change animation
    await this.page.waitForTimeout(300);
  }

  /**
   * Toggle auto-refresh functionality
   */
  async toggleAutoRefresh() {
    await this.autoRefreshToggle.click();
  }

  /**
   * Manually refresh the page data
   */
  async refreshData() {
    await this.refreshButton.click();
    await this.waitForLoadingComplete();
  }

  /**
   * Check if element is visible
   */
  async isVisible(locator: Locator): Promise<boolean> {
    try {
      await locator.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if element is hidden
   */
  async isHidden(locator: Locator): Promise<boolean> {
    try {
      await locator.waitFor({ state: 'hidden', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for element to be visible with custom timeout
   */
  async waitForVisible(locator: Locator, timeout: number = 10000) {
    await locator.waitFor({ state: 'visible', timeout });
  }

  /**
   * Wait for element to be hidden with custom timeout
   */
  async waitForHidden(locator: Locator, timeout: number = 10000) {
    await locator.waitFor({ state: 'hidden', timeout });
  }

  /**
   * Get text content of element
   */
  async getText(locator: Locator): Promise<string> {
    return await locator.textContent() || '';
  }

  /**
   * Check if element contains text
   */
  async containsText(locator: Locator, text: string): Promise<boolean> {
    const content = await this.getText(locator);
    return content.includes(text);
  }

  /**
   * Take a screenshot for debugging
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  /**
   * Wait for toast notification
   */
  async waitForToast(message?: string, timeout: number = 5000) {
    if (message) {
      await this.page.waitForSelector(`text=${message}`, { timeout });
    } else {
      await this.page.waitForSelector('[data-testid="toast"], .toast', { timeout });
    }
  }

  /**
   * Check if toast notification is visible
   */
  async hasToast(message: string): Promise<boolean> {
    try {
      await this.page.waitForSelector(`text=${message}`, { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for API response (for testing API integration)
   */
  async waitForAPIResponse(urlPattern: string, timeout: number = 10000) {
    await this.page.waitForResponse(
      response => response.url().includes(urlPattern),
      { timeout }
    );
  }

  /**
   * Check if error message is displayed
   */
  async hasError(message?: string): Promise<boolean> {
    try {
      if (message) {
        await this.page.waitForSelector(`text=${message}`, { timeout: 5000 });
      } else {
        await this.page.waitForSelector('[data-testid="error-message"], .error-message', { timeout: 5000 });
      }
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get current URL
   */
  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }

  /**
   * Check if current page matches expected path
   */
  async isOnPage(expectedPath: string): Promise<boolean> {
    const currentUrl = await this.getCurrentUrl();
    return currentUrl.includes(expectedPath);
  }

  /**
   * Wait for navigation to complete
   */
  async waitForNavigation() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get page title
   */
  async getPageTitle(): Promise<string> {
    return await this.page.title();
  }

  /**
   * Check if page has specific title
   */
  async hasTitle(expectedTitle: string): Promise<boolean> {
    const title = await this.getPageTitle();
    return title.includes(expectedTitle);
  }

  /**
   * Reload the page
   */
  async reload() {
    await this.page.reload();
    await this.waitForPageLoad();
  }

  /**
   * Go back in browser history
   */
  async goBack() {
    await this.page.goBack();
    await this.waitForPageLoad();
  }

  /**
   * Go forward in browser history
   */
  async goForward() {
    await this.page.goForward();
    await this.waitForPageLoad();
  }

  /**
   * Get browser console logs
   */
  async getConsoleLogs(): Promise<string[]> {
    const logs: string[] = [];
    
    this.page.on('console', msg => {
      logs.push(`${msg.type()}: ${msg.text()}`);
    });

    return logs;
  }

  /**
   * Check if page has no console errors
   */
  async hasNoConsoleErrors(): Promise<boolean> {
    const logs = await this.getConsoleLogs();
    return !logs.some(log => log.includes('error'));
  }
}
