/**
 * Settings page object for testing the settings interface
 * Extends BasePage with settings-specific interactions and assertions
 */
import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class SettingsPage extends BasePage {
  // Main settings sections
  readonly plexSettings: Locator;
  readonly mediaSettings: Locator;
  readonly performanceSettings: Locator;
  readonly advancedSettings: Locator;

  // Plex settings
  readonly plexUrl: Locator;
  readonly plexToken: Locator;
  readonly plexTestButton: Locator;
  readonly plexConnectionStatus: Locator;

  // Media settings
  readonly mediaPaths: Locator;
  readonly fileExtensions: Locator;
  readonly sizeLimit: Locator;
  readonly copyToCache: Locator;
  readonly autoClean: Locator;
  readonly watchedMove: Locator;

  // Performance settings
  readonly concurrencySliders: Locator;
  readonly cacheConcurrency: Locator;
  readonly arrayConcurrency: Locator;
  readonly networkConcurrency: Locator;

  // Advanced settings
  readonly monitoringInterval: Locator;
  readonly notificationSettings: Locator;
  readonly webhookUrl: Locator;
  readonly discordWebhook: Locator;
  readonly slackWebhook: Locator;
  readonly emailSettings: Locator;
  readonly logLevel: Locator;
  readonly logRotation: Locator;

  // Action buttons
  readonly saveButton: Locator;
  readonly resetButton: Locator;
  readonly exportButton: Locator;
  readonly importButton: Locator;
  readonly testConnectionButton: Locator;

  // Status and feedback
  readonly saveStatus: Locator;
  readonly validationErrors: Locator;
  readonly successMessage: Locator;

  constructor(page: Page) {
    super(page);

    // Main settings sections
    this.plexSettings = page.locator('[data-testid="plex-settings"], .plex-settings');
    this.mediaSettings = page.locator('[data-testid="media-settings"], .media-settings');
    this.performanceSettings = page.locator('[data-testid="performance-settings"], .performance-settings');
    this.advancedSettings = page.locator('[data-testid="advanced-settings"], .advanced-settings');

    // Plex settings
    this.plexUrl = page.locator('[data-testid="plex-url"], input[name="plexUrl"]');
    this.plexToken = page.locator('[data-testid="plex-token"], input[name="plexToken"]');
    this.plexTestButton = page.locator('[data-testid="test-plex-connection"], button');
    this.plexConnectionStatus = page.locator('[data-testid="plex-connection-status"], .connection-status');

    // Media settings
    this.mediaPaths = page.locator('[data-testid="media-paths"], .media-paths');
    this.fileExtensions = page.locator('[data-testid="file-extensions"], input[name="extensions"]');
    this.sizeLimit = page.locator('[data-testid="size-limit"], input[name="sizeLimit"]');
    this.copyToCache = page.locator('[data-testid="copy-to-cache"], input[type="checkbox"]');
    this.autoClean = page.locator('[data-testid="auto-clean"], input[type="checkbox"]');
    this.watchedMove = page.locator('[data-testid="watched-move"], input[type="checkbox"]');

    // Performance settings
    this.concurrencySliders = page.locator('[data-testid="concurrency-sliders"], .concurrency-sliders');
    this.cacheConcurrency = page.locator('[data-testid="cache-concurrency"], input[type="range"]');
    this.arrayConcurrency = page.locator('[data-testid="array-concurrency"], input[type="range"]');
    this.networkConcurrency = page.locator('[data-testid="network-concurrency"], input[type="range"]');

    // Advanced settings
    this.monitoringInterval = page.locator('[data-testid="monitoring-interval"], input[name="monitoringInterval"]');
    this.notificationSettings = page.locator('[data-testid="notification-settings"], .notification-settings');
    this.webhookUrl = page.locator('[data-testid="webhook-url"], input[name="webhookUrl"]');
    this.discordWebhook = page.locator('[data-testid="discord-webhook"], input[name="discordWebhook"]');
    this.slackWebhook = page.locator('[data-testid="slack-webhook"], input[name="slackWebhook"]');
    this.emailSettings = page.locator('[data-testid="email-settings"], .email-settings');
    this.logLevel = page.locator('[data-testid="log-level"], select[name="logLevel"]');
    this.logRotation = page.locator('[data-testid="log-rotation"], input[name="logRotation"]');

    // Action buttons
    this.saveButton = page.locator('[data-testid="save-settings"], button[type="submit"]');
    this.resetButton = page.locator('[data-testid="reset-settings"], button');
    this.exportButton = page.locator('[data-testid="export-settings"], button');
    this.importButton = page.locator('[data-testid="import-settings"], button');
    this.testConnectionButton = page.locator('[data-testid="test-connection"], button');

    // Status and feedback
    this.saveStatus = page.locator('[data-testid="save-status"], .save-status');
    this.validationErrors = page.locator('[data-testid="validation-errors"], .validation-errors');
    this.successMessage = page.locator('[data-testid="success-message"], .success-message');
  }

  /**
   * Navigate to settings page and wait for it to load
   */
  async gotoSettings() {
    await this.goto('/settings');
    await this.waitForSettingsLoad();
  }

  /**
   * Wait for settings page to fully load
   */
  async waitForSettingsLoad() {
    await this.waitForVisible(this.plexSettings);
    await this.waitForVisible(this.mediaSettings);
    await this.waitForVisible(this.performanceSettings);
    await this.waitForVisible(this.advancedSettings);
    await this.waitForLoadingComplete();
  }

  /**
   * Check if settings page is properly loaded
   */
  async isSettingsLoaded(): Promise<boolean> {
    try {
      await this.waitForSettingsLoad();
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Configure Plex settings
   */
  async configurePlex(url: string, token: string) {
    await this.waitForVisible(this.plexUrl);
    await this.plexUrl.fill(url);
    await this.plexToken.fill(token);

    // Wait for auto-save or trigger save
    await this.page.waitForTimeout(1000);
  }

  /**
   * Test Plex connection
   */
  async testPlexConnection() {
    await this.waitForVisible(this.plexTestButton);
    await this.plexTestButton.click();

    // Wait for connection test to complete
    await this.page.waitForTimeout(2000);
  }

  /**
   * Get Plex connection status
   */
  async getPlexConnectionStatus(): Promise<string> {
    await this.waitForVisible(this.plexConnectionStatus);
    return await this.getText(this.plexConnectionStatus);
  }

  /**
   * Configure media settings
   */
  async configureMediaSettings(options: {
    paths?: string[];
    extensions?: string;
    sizeLimit?: string;
    copyToCache?: boolean;
    autoClean?: boolean;
    watchedMove?: boolean;
  }) {
    if (options.paths) {
      // Add media paths (this might involve multiple inputs)
      for (const path of options.paths) {
        await this.addMediaPath(path);
      }
    }

    if (options.extensions) {
      await this.fileExtensions.fill(options.extensions);
    }

    if (options.sizeLimit) {
      await this.sizeLimit.fill(options.sizeLimit);
    }

    if (options.copyToCache !== undefined) {
      await this.setCheckbox(this.copyToCache, options.copyToCache);
    }

    if (options.autoClean !== undefined) {
      await this.setCheckbox(this.autoClean, options.autoClean);
    }

    if (options.watchedMove !== undefined) {
      await this.setCheckbox(this.watchedMove, options.watchedMove);
    }
  }

  /**
   * Add a media path
   */
  async addMediaPath(path: string) {
    const addButton = this.page.locator('[data-testid="add-media-path"], .add-path-button');
    await addButton.click();

    const pathInputs = this.page.locator('[data-testid="media-path-input"], input[type="text"]');
    const lastInput = pathInputs.last();
    await lastInput.fill(path);
  }

  /**
   * Configure performance settings
   */
  async configurePerformanceSettings(options: {
    cacheConcurrency?: number;
    arrayConcurrency?: number;
    networkConcurrency?: number;
  }) {
    if (options.cacheConcurrency !== undefined) {
      await this.cacheConcurrency.fill(options.cacheConcurrency.toString());
    }

    if (options.arrayConcurrency !== undefined) {
      await this.arrayConcurrency.fill(options.arrayConcurrency.toString());
    }

    if (options.networkConcurrency !== undefined) {
      await this.networkConcurrency.fill(options.networkConcurrency.toString());
    }
  }

  /**
   * Configure advanced settings
   */
  async configureAdvancedSettings(options: {
    monitoringInterval?: string;
    webhookUrl?: string;
    discordWebhook?: string;
    slackWebhook?: string;
    logLevel?: string;
    logRotation?: string;
  }) {
    if (options.monitoringInterval) {
      await this.monitoringInterval.fill(options.monitoringInterval);
    }

    if (options.webhookUrl) {
      await this.webhookUrl.fill(options.webhookUrl);
    }

    if (options.discordWebhook) {
      await this.discordWebhook.fill(options.discordWebhook);
    }

    if (options.slackWebhook) {
      await this.slackWebhook.fill(options.slackWebhook);
    }

    if (options.logLevel) {
      await this.logLevel.selectOption(options.logLevel);
    }

    if (options.logRotation) {
      await this.logRotation.fill(options.logRotation);
    }
  }

  /**
   * Save settings
   */
  async saveSettings() {
    await this.saveButton.click();
    await this.waitForSaveComplete();
  }

  /**
   * Wait for save operation to complete
   */
  async waitForSaveComplete() {
    // Wait for success message or status update
    try {
      await this.waitForVisible(this.successMessage, 10000);
    } catch {
      // Check for save status
      await this.waitForVisible(this.saveStatus, 5000);
    }
  }

  /**
   * Reset settings to defaults
   */
  async resetSettings() {
    await this.resetButton.click();

    // Handle confirmation dialog if present
    const confirmButton = this.page.locator('[data-testid="confirm-reset"], .confirm-button');
    try {
      await confirmButton.click();
    } catch {
      // Confirmation might not be required
    }

    await this.waitForSettingsLoad();
  }

  /**
   * Export settings
   */
  async exportSettings(): Promise<string> {
    const downloadPromise = this.page.waitForEvent('download');
    await this.exportButton.click();
    const download = await downloadPromise;
    return await download.path();
  }

  /**
   * Import settings
   */
  async importSettings(filePath: string) {
    const fileInput = this.page.locator('[data-testid="import-file"], input[type="file"]');
    await fileInput.setInputFiles(filePath);

    await this.importButton.click();
    await this.waitForSettingsLoad();
  }

  /**
   * Get validation errors
   */
  async getValidationErrors(): Promise<string[]> {
    const errors: string[] = [];
    const errorElements = await this.validationErrors.locator('.error-item, .validation-error').all();

    for (const error of errorElements) {
      const text = await error.textContent();
      if (text) {
        errors.push(text);
      }
    }

    return errors;
  }

  /**
   * Check if settings have validation errors
   */
  async hasValidationErrors(): Promise<boolean> {
    return await this.validationErrors.isVisible();
  }

  /**
   * Set checkbox value
   */
  private async setCheckbox(checkbox: Locator, checked: boolean) {
    const isChecked = await checkbox.isChecked();
    if (isChecked !== checked) {
      await checkbox.click();
    }
  }

  /**
   * Get current settings values
   */
  async getCurrentSettings() {
    return {
      plex: {
        url: await this.plexUrl.inputValue(),
        token: await this.plexToken.inputValue(),
        connectionStatus: await this.getPlexConnectionStatus(),
      },
      media: {
        extensions: await this.fileExtensions.inputValue(),
        sizeLimit: await this.sizeLimit.inputValue(),
        copyToCache: await this.copyToCache.isChecked(),
        autoClean: await this.autoClean.isChecked(),
        watchedMove: await this.watchedMove.isChecked(),
      },
      performance: {
        cacheConcurrency: await this.cacheConcurrency.inputValue(),
        arrayConcurrency: await this.arrayConcurrency.inputValue(),
        networkConcurrency: await this.networkConcurrency.inputValue(),
      },
      advanced: {
        monitoringInterval: await this.monitoringInterval.inputValue(),
        webhookUrl: await this.webhookUrl.inputValue(),
        logLevel: await this.logLevel.inputValue(),
        logRotation: await this.logRotation.inputValue(),
      },
    };
  }

  /**
   * Test settings form validation
   */
  async testFormValidation() {
    // Test invalid Plex URL
    await this.plexUrl.fill('invalid-url');
    await this.saveSettings();

    const hasErrors = await this.hasValidationErrors();
    expect(hasErrors).toBeTruthy();

    // Test invalid token
    await this.plexToken.fill('');
    await this.saveSettings();

    const errors = await this.getValidationErrors();
    expect(errors.length).toBeGreaterThan(0);

    return errors;
  }

  /**
   * Test responsive design
   */
  async testResponsiveDesign() {
    // Test mobile viewport
    await this.page.setViewportSize({ width: 375, height: 667 });
    await this.page.waitForTimeout(1000);

    // Verify mobile layout
    expect(await this.isVisible(this.plexSettings)).toBeTruthy();

    // Test tablet viewport
    await this.page.setViewportSize({ width: 768, height: 1024 });
    await this.page.waitForTimeout(1000);

    // Verify tablet layout
    expect(await this.isVisible(this.performanceSettings)).toBeTruthy();

    // Test desktop viewport
    await this.page.setViewportSize({ width: 1280, height: 720 });
    await this.page.waitForTimeout(1000);

    // Verify desktop layout
    expect(await this.isVisible(this.advancedSettings)).toBeTruthy();
  }

  /**
   * Test accessibility features
   */
  async testAccessibility() {
    // Check for proper labels
    const inputs = await this.page.locator('input, select, textarea').all();
    for (const input of inputs) {
      const hasLabel = await input.evaluate(el => {
        return el.hasAttribute('aria-label') ||
               el.hasAttribute('aria-labelledby') ||
               el.hasAttribute('name') ||
               el.getAttribute('id') &&
               document.querySelector(`label[for="${el.getAttribute('id')}"]`);
      });
      expect(hasLabel).toBeTruthy();
    }

    // Check keyboard navigation
    await this.page.keyboard.press('Tab');
    let focusedElement = await this.page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);

    // Navigate through form elements
    for (let i = 0; i < 10; i++) {
      await this.page.keyboard.press('Tab');
      await this.page.waitForTimeout(100);
    }

    focusedElement = await this.page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);
  }

  /**
   * Comprehensive settings test
   */
  async runFullSettingsTest() {
    // Navigate to settings
    await this.gotoSettings();

    // Verify page loads correctly
    expect(await this.isSettingsLoaded()).toBeTruthy();

    // Test form validation
    await this.testFormValidation();

    // Test responsive design
    await this.testResponsiveDesign();

    // Test accessibility
    await this.testAccessibility();

    // Test settings configuration
    await this.configurePlex('http://localhost:32400', 'test-token');
    await this.configureMediaSettings({
      extensions: 'mp4,mkv,avi',
      sizeLimit: '100',
      copyToCache: true,
      autoClean: false,
      watchedMove: true,
    });

    await this.configurePerformanceSettings({
      cacheConcurrency: 4,
      arrayConcurrency: 2,
      networkConcurrency: 8,
    });

    await this.configureAdvancedSettings({
      monitoringInterval: '30',
      logLevel: 'info',
      logRotation: '7',
    });

    // Test save functionality
    await this.saveSettings();

    // Verify settings were saved
    const currentSettings = await this.getCurrentSettings();
    expect(currentSettings.media.extensions).toBe('mp4,mkv,avi');
  }
}
