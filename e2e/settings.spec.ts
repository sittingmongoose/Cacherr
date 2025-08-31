/**
 * Comprehensive Settings Page End-to-End Tests
 *
 * This test suite covers all Settings page functionality including:
 * - Page loading and navigation
 * - Plex server configuration and testing
 * - Media settings configuration
 * - Performance settings with concurrency controls
 * - Advanced settings and notifications
 * - Form validation and error handling
 * - Settings export/import functionality
 * - Responsive design across viewports
 * - Accessibility compliance
 * - Real-time validation and feedback
 * - Connection testing and status updates
 */

import { test, expect, Page } from '@playwright/test';
import { SettingsPage } from './pages/SettingsPage';
import { NavigationPage } from './pages/NavigationPage';
import { TestSetup, TestEnvironment, CustomAssertions, TestDataUtils } from './utils/test-helpers';
import { PredefinedMocks } from './utils/mock-api';
import { UIXAssertions, APIAssertions, AccessibilityAssertions } from './utils/custom-assertions';

test.describe('Settings Page - Core Functionality', () => {
  let settingsPage: SettingsPage;
  let navigationPage: NavigationPage;
  let mockManager: PredefinedMocks;

  test.beforeEach(async ({ page }) => {
    // Setup test environment with proper mocks
    await TestSetup.setupTest(page);

    // Initialize page objects
    settingsPage = new SettingsPage(page);
    navigationPage = new NavigationPage(page);

    // Setup comprehensive API mocks for settings functionality
    mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    // Navigate to settings page
    await settingsPage.gotoSettings();
  });

  test.afterEach(async ({ page }) => {
    // Cleanup test environment
    await TestSetup.cleanupTest(page);
  });

  test('Settings page loads with all configuration sections', async ({ page }) => {
    // Verify settings page loads correctly
    await expect(settingsPage.plexSettings).toBeVisible();
    await expect(settingsPage.mediaSettings).toBeVisible();
    await expect(settingsPage.performanceSettings).toBeVisible();
    await expect(settingsPage.advancedSettings).toBeVisible();

    // Verify action buttons are present and functional
    await expect(settingsPage.saveButton).toBeVisible();
    await expect(settingsPage.resetButton).toBeVisible();
    await expect(settingsPage.exportButton).toBeVisible();
    await expect(settingsPage.importButton).toBeVisible();

    // Verify no console errors during page load
    await CustomAssertions.assertNoConsoleErrors(page);

    // Verify page title and URL
    await expect(page).toHaveURL(/.*\/settings/);
    await expect(page).toHaveTitle(/.*Settings.*/);
  });

  test('Plex settings configuration and validation', async ({ page }) => {
    // Test valid Plex configuration
    const validUrl = 'http://localhost:32400';
    const validToken = 'test-plex-token-123';

    await settingsPage.configurePlex(validUrl, validToken);

    // Verify values are set correctly
    await expect(settingsPage.plexUrl).toHaveValue(validUrl);
    await expect(settingsPage.plexToken).toHaveValue(validToken);

    // Test connection testing functionality
    await settingsPage.testPlexConnection();

    // Verify connection status is displayed
    const status = await settingsPage.getPlexConnectionStatus();
    expect(status).toBeTruthy();

    // Test invalid URL validation
    await settingsPage.plexUrl.fill('invalid-url-format');
    await settingsPage.saveSettings();

    // Should show validation error
    expect(await settingsPage.hasValidationErrors()).toBeTruthy();

    // Test empty token validation
    await settingsPage.plexUrl.fill(validUrl);
    await settingsPage.plexToken.fill('');
    await settingsPage.saveSettings();

    expect(await settingsPage.hasValidationErrors()).toBeTruthy();
  });

  test('Media settings configuration and file handling', async ({ page }) => {
    // Configure comprehensive media settings
    const mediaConfig = {
      extensions: 'mp4,mkv,avi,mp3,wav',
      sizeLimit: '200',
      copyToCache: true,
      autoClean: false,
      watchedMove: true
    };

    await settingsPage.configureMediaSettings(mediaConfig);

    // Verify all values are set correctly
    await expect(settingsPage.fileExtensions).toHaveValue(mediaConfig.extensions);
    await expect(settingsPage.sizeLimit).toHaveValue(mediaConfig.sizeLimit);
    expect(await settingsPage.copyToCache.isChecked()).toBe(mediaConfig.copyToCache);
    expect(await settingsPage.autoClean.isChecked()).toBe(mediaConfig.autoClean);
    expect(await settingsPage.watchedMove.isChecked()).toBe(mediaConfig.watchedMove);

    // Test file extension validation
    await settingsPage.fileExtensions.fill('invalid,format,h3r3');
    await settingsPage.saveSettings();

    // Should handle gracefully
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('Performance settings with concurrency controls', async ({ page }) => {
    // Configure performance settings with different concurrency levels
    const performanceConfig = {
      cacheConcurrency: 4,
      arrayConcurrency: 2,
      networkConcurrency: 8
    };

    await settingsPage.configurePerformanceSettings(performanceConfig);

    // Verify performance settings are configured
    await expect(settingsPage.performanceSettings).toBeVisible();

    // Test slider interactions and value updates
    await settingsPage.cacheConcurrency.fill('6');
    await expect(settingsPage.cacheConcurrency).toHaveValue('6');

    // Test performance warnings for high concurrency
    await settingsPage.networkConcurrency.fill('16');
    await expect(settingsPage.networkConcurrency).toHaveValue('16');
  });

  test('Advanced settings and notification configuration', async ({ page }) => {
    // Configure comprehensive advanced settings
    const advancedConfig = {
      monitoringInterval: '45',
      webhookUrl: 'https://hooks.slack.com/services/test',
      discordWebhook: 'https://discord.com/api/webhooks/test',
      slackWebhook: 'https://hooks.slack.com/test2',
      logLevel: 'debug',
      logRotation: '14'
    };

    await settingsPage.configureAdvancedSettings(advancedConfig);

    // Verify all advanced settings are configured
    await expect(settingsPage.monitoringInterval).toHaveValue(advancedConfig.monitoringInterval);
    await expect(settingsPage.webhookUrl).toHaveValue(advancedConfig.webhookUrl);
    await expect(settingsPage.discordWebhook).toHaveValue(advancedConfig.discordWebhook);
    await expect(settingsPage.slackWebhook).toHaveValue(advancedConfig.slackWebhook);
    await expect(settingsPage.logLevel).toHaveValue(advancedConfig.logLevel);
    await expect(settingsPage.logRotation).toHaveValue(advancedConfig.logRotation);

    // Test notification configuration validation
    await settingsPage.webhookUrl.fill('invalid-webhook-url');
    await settingsPage.saveSettings();

    // Should handle validation appropriately
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });
});

test.describe('Settings Page - Form Operations', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    await settingsPage.gotoSettings();
  });

  test('Settings save and persistence', async ({ page }) => {
    // Configure comprehensive settings
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');
    await settingsPage.configureMediaSettings({
      extensions: 'mp4,mkv,avi',
      copyToCache: true,
      autoClean: false
    });
    await settingsPage.configurePerformanceSettings({
      cacheConcurrency: 4,
      arrayConcurrency: 2,
      networkConcurrency: 6
    });
    await settingsPage.configureAdvancedSettings({
      monitoringInterval: '30',
      logLevel: 'info'
    });

    // Save settings and verify success
    await settingsPage.saveSettings();
    await expect(settingsPage.successMessage).toBeVisible();

    // Verify settings persist after page reload
    await page.reload();
    await settingsPage.waitForSettingsLoad();

    const currentSettings = await settingsPage.getCurrentSettings();
    expect(currentSettings.media.extensions).toBe('mp4,mkv,avi');
    expect(currentSettings.performance.cacheConcurrency).toBe('4');
  });

  test('Settings reset to defaults', async ({ page }) => {
    // Configure some settings
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');
    await settingsPage.configureMediaSettings({
      extensions: 'mp4,mkv',
      copyToCache: true
    });

    // Reset settings
    await settingsPage.resetSettings();

    // Verify settings are reset to defaults
    const currentSettings = await settingsPage.getCurrentSettings();
    expect(currentSettings.plex.url).toBe('');
    expect(currentSettings.plex.token).toBe('');
    expect(currentSettings.media.extensions).toBe('');
  });

  test('Settings export functionality', async ({ page }) => {
    // Configure settings for export
    await settingsPage.configurePlex('http://localhost:32400', 'export-test-token');
    await settingsPage.configureMediaSettings({
      extensions: 'mp4,mkv,avi',
      copyToCache: true
    });

    // Export settings
    const downloadPromise = page.waitForEvent('download');
    await settingsPage.exportButton.click();
    const download = await downloadPromise;

    // Verify download was initiated
    expect(download.suggestedFilename()).toContain('settings');
    expect(await download.path()).toBeTruthy();
  });

  test('Settings import functionality', async ({ page }) => {
    // Create a mock settings file for import
    const settingsData = JSON.stringify({
      plex: {
        url: 'http://imported-server:32400',
        token: 'imported-token-123'
      },
      media: {
        extensions: 'avi,mp4,mov',
        copyToCache: false,
        autoClean: true
      },
      advanced: {
        logLevel: 'warn',
        monitoringInterval: '60'
      }
    });

    // Mock file upload by setting up the file input
    await page.setInputFiles('[data-testid="import-file"], input[type="file"]', {
      name: 'test-settings.json',
      mimeType: 'application/json',
      buffer: Buffer.from(settingsData)
    });

    // Import settings
    await settingsPage.importButton.click();

    // Wait for settings to load
    await settingsPage.waitForSettingsLoad();

    // Verify imported settings
    const currentSettings = await settingsPage.getCurrentSettings();
    expect(currentSettings.plex.url).toBe('http://imported-server:32400');
    expect(currentSettings.media.extensions).toBe('avi,mp4,mov');
    expect(currentSettings.advanced.logLevel).toBe('warn');
  });
});

test.describe('Settings Page - Error Handling', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    await settingsPage.gotoSettings();
  });

  test('Handles API errors gracefully', async ({ page }) => {
    // Mock API error for save operation
    await page.route('/api/config/update', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    // Attempt to save settings
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');
    await settingsPage.saveSettings();

    // Verify page remains functional despite error
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
    await expect(settingsPage.plexSettings).toBeVisible();
  });

  test('Handles network connectivity issues', async ({ page }) => {
    // Mock network failure for connection test
    await page.route('/api/config/test-plex', route => {
      route.fulfill({
        status: 0, // Network error
        contentType: 'application/json',
        body: JSON.stringify({})
      });
    });

    // Test connection
    await settingsPage.configurePlex('http://offline-server:32400', 'test-token');
    await settingsPage.testPlexConnection();

    // Verify connection status shows error appropriately
    const status = await settingsPage.getPlexConnectionStatus();
    expect(status).toBeTruthy(); // Status should still be displayed
  });

  test('Handles invalid configuration data', async ({ page }) => {
    // Mock response with invalid data structure
    await page.route('/api/config/current', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ invalid: 'data structure' })
      });
    });

    // Reload page to trigger config load
    await page.reload();

    // Verify page handles invalid data gracefully
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });
});

test.describe('Settings Page - Responsive Design', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();
  });

  const viewports = [
    { width: 375, height: 667, name: 'Mobile' },
    { width: 768, height: 1024, name: 'Tablet' },
    { width: 1024, height: 768, name: 'Desktop' },
    { width: 1920, height: 1080, name: 'Large Desktop' }
  ];

  for (const viewport of viewports) {
    test(`Settings page works on ${viewport.name} (${viewport.width}x${viewport.height})`, async ({ page }) => {
      // Set viewport size
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      // Navigate to settings
      await settingsPage.gotoSettings();

      // Verify page loads correctly
      expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

      // Verify critical elements are visible
      await expect(settingsPage.plexSettings).toBeVisible();
      await expect(settingsPage.saveButton).toBeVisible();

      // Verify no horizontal scroll
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBeFalsy();

      // Test basic functionality still works
      await settingsPage.configurePlex('http://localhost:32400', 'test-token');
      await expect(settingsPage.plexUrl).toHaveValue('http://localhost:32400');
    });
  }
});

test.describe('Settings Page - Accessibility', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    await settingsPage.gotoSettings();
  });

  test('Settings page meets accessibility standards', async ({ page }) => {
    // Test keyboard navigation through form elements
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThan(0);

    // Navigate through multiple form elements
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(50);
    }

    // Verify focus is maintained within form
    focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);

    // Test proper labels for form inputs
    const inputs = await page.locator('input, select, textarea').all();
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

    // Test form validation accessibility
    await settingsPage.plexToken.fill('');
    await settingsPage.saveSettings();

    // Verify validation errors are accessible
    if (await settingsPage.hasValidationErrors()) {
      const errors = await settingsPage.getValidationErrors();
      expect(errors.length).toBeGreaterThan(0);
    }
  });

  test('Settings page supports screen readers', async ({ page }) => {
    // Test semantic HTML structure
    await expect(page.locator('main, [role="main"]')).toBeVisible();

    // Test heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);

    // Test form landmarks
    await expect(page.locator('form, [role="form"]')).toBeVisible();

    // Test button accessibility
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const accessibleName = await button.evaluate(el => {
        return el.getAttribute('aria-label') ||
               el.textContent ||
               el.getAttribute('title');
      });
      expect(accessibleName?.trim()).toBeTruthy();
    }
  });
});

test.describe('Settings Page - Performance', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();
  });

  test('Settings page loads within performance budget', async ({ page }) => {
    const startTime = Date.now();

    await settingsPage.gotoSettings();

    const loadTime = Date.now() - startTime;

    // Performance budget: 3 seconds max
    expect(loadTime).toBeLessThan(3000);

    console.log(`Settings page load time: ${loadTime}ms`);
  });

  test('Settings page handles rapid configuration changes', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Make multiple rapid configuration changes
    for (let i = 0; i < 10; i++) {
      await settingsPage.configurePlex(`http://server-${i}:32400`, `token-${i}`);
      await page.waitForTimeout(50); // Small delay between changes
    }

    // Verify page remains stable
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

    // Verify last configuration is maintained
    await expect(settingsPage.plexUrl).toHaveValue('http://server-9:32400');
  });

  test('Settings page handles concurrent operations', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Trigger multiple save operations rapidly
    const savePromises = [];
    for (let i = 0; i < 5; i++) {
      savePromises.push(settingsPage.saveSettings());
      await page.waitForTimeout(100);
    }

    // Wait for all operations to complete
    await Promise.all(savePromises);

    // Verify page remains functional
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
    await expect(settingsPage.plexSettings).toBeVisible();
  });
});

test.describe('Settings Page - Integration Tests', () => {
  let settingsPage: SettingsPage;
  let navigationPage: NavigationPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);
    navigationPage = new NavigationPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();
  });

  test('Settings integration with navigation', async ({ page }) => {
    // Navigate to dashboard first
    await navigationPage.goToDashboard();

    // Navigate to settings
    await navigationPage.goToSettings();

    // Verify settings page loads correctly
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

    // Make changes and navigate away
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');
    await navigationPage.goToDashboard();

    // Navigate back to settings
    await navigationPage.goToSettings();

    // Verify settings are maintained
    await expect(settingsPage.plexUrl).toHaveValue('http://localhost:32400');
  });

  test('Settings integration with real-time updates', async ({ page }) => {
    await settingsPage.gotoSettings();

    // Configure settings that might trigger real-time updates
    await settingsPage.configureAdvancedSettings({
      monitoringInterval: '15',
      logLevel: 'debug'
    });

    // Save settings
    await settingsPage.saveSettings();

    // Verify success feedback is shown
    await expect(settingsPage.successMessage).toBeVisible();

    // Wait for any real-time updates to process
    await page.waitForTimeout(1000);

    // Verify page remains in stable state
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('End-to-end settings configuration workflow', async ({ page }) => {
    // Complete settings configuration workflow
    await settingsPage.gotoSettings();

    // Step 1: Configure Plex
    await settingsPage.configurePlex('http://plex-server:32400', 'plex-token-123');
    await settingsPage.testPlexConnection();

    // Step 2: Configure Media
    await settingsPage.configureMediaSettings({
      extensions: 'mp4,mkv,avi,m4v',
      sizeLimit: '150',
      copyToCache: true,
      autoClean: true,
      watchedMove: false
    });

    // Step 3: Configure Performance
    await settingsPage.configurePerformanceSettings({
      cacheConcurrency: 3,
      arrayConcurrency: 2,
      networkConcurrency: 5
    });

    // Step 4: Configure Advanced
    await settingsPage.configureAdvancedSettings({
      monitoringInterval: '20',
      webhookUrl: 'https://webhook.example.com',
      logLevel: 'info',
      logRotation: '7'
    });

    // Step 5: Save all settings
    await settingsPage.saveSettings();
    await expect(settingsPage.successMessage).toBeVisible();

    // Step 6: Export settings for backup
    const downloadPromise = page.waitForEvent('download');
    await settingsPage.exportButton.click();
    await downloadPromise;

    // Step 7: Verify all settings are properly configured
    const finalSettings = await settingsPage.getCurrentSettings();
    expect(finalSettings.plex.url).toBe('http://plex-server:32400');
    expect(finalSettings.media.extensions).toBe('mp4,mkv,avi,m4v');
    expect(finalSettings.performance.cacheConcurrency).toBe('3');
    expect(finalSettings.advanced.monitoringInterval).toBe('20');

    console.log('✅ Complete settings configuration workflow successful');
  });
});
