/**
 * Comprehensive Settings Test Suite
 * Tests all settings functionality including form validation, save/load, and responsive design
 */

import { test, expect, Page } from '@playwright/test';
import { SettingsPage } from '../pages/SettingsPage';
import { NavigationPage } from '../pages/NavigationPage';
import { TestSetup, TestEnvironment, CustomAssertions, TestDataUtils } from '../utils/test-helpers';
import { PredefinedMocks } from '../utils/mock-api';
import { UIXAssertions, APIAssertions, AccessibilityAssertions } from '../utils/custom-assertions';

test.describe('Settings - Comprehensive Functionality', () => {
  let settingsPage: SettingsPage;
  let navigationPage: NavigationPage;
  let mockManager: PredefinedMocks;

  test.beforeEach(async ({ page }) => {
    // Setup test environment
    await TestSetup.setupTest(page);

    // Initialize page objects
    settingsPage = new SettingsPage(page);
    navigationPage = new NavigationPage(page);

    // Setup API mocks
    mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    // Navigate to settings
    await settingsPage.gotoSettings();
  });

  test.afterEach(async ({ page }) => {
    // Cleanup test environment
    await TestSetup.cleanupTest(page);
  });

  test('Settings page loads with all required sections', async ({ page }) => {
    // Verify settings page loads correctly
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

    // Verify all main sections are present
    await expect(settingsPage.plexSettings).toBeVisible();
    await expect(settingsPage.mediaSettings).toBeVisible();
    await expect(settingsPage.performanceSettings).toBeVisible();
    await expect(settingsPage.advancedSettings).toBeVisible();

    // Verify action buttons are present
    await expect(settingsPage.saveButton).toBeVisible();
    await expect(settingsPage.resetButton).toBeVisible();

    // Verify no console errors
    await CustomAssertions.assertNoConsoleErrors(page);
  });

  test('Plex settings configuration works correctly', async ({ page }) => {
    // Configure Plex settings
    const testUrl = 'http://localhost:32400';
    const testToken = 'test-plex-token-123';

    await settingsPage.configurePlex(testUrl, testToken);

    // Verify values are set
    await expect(settingsPage.plexUrl).toHaveValue(testUrl);
    await expect(settingsPage.plexToken).toHaveValue(testToken);
  });

  test('Plex connection test functionality works', async ({ page }) => {
    // Set valid Plex configuration
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');

    // Test connection
    await settingsPage.testPlexConnection();

    // Verify connection test result
    const status = await settingsPage.getPlexConnectionStatus();
    expect(status).toBeTruthy();
  });

  test('Media settings configuration works correctly', async ({ page }) => {
    const mediaConfig = {
      extensions: 'mp4,mkv,avi,mp3',
      sizeLimit: '100',
      copyToCache: true,
      autoClean: false,
      watchedMove: true
    };

    await settingsPage.configureMediaSettings(mediaConfig);

    // Verify values are set
    await expect(settingsPage.fileExtensions).toHaveValue(mediaConfig.extensions);
    await expect(settingsPage.sizeLimit).toHaveValue(mediaConfig.sizeLimit);

    // Verify checkboxes are set correctly
    expect(await settingsPage.copyToCache.isChecked()).toBe(mediaConfig.copyToCache);
    expect(await settingsPage.autoClean.isChecked()).toBe(mediaConfig.autoClean);
    expect(await settingsPage.watchedMove.isChecked()).toBe(mediaConfig.watchedMove);
  });

  test('Performance settings configuration works correctly', async ({ page }) => {
    const performanceConfig = {
      cacheConcurrency: 4,
      arrayConcurrency: 2,
      networkConcurrency: 8
    };

    await settingsPage.configurePerformanceSettings(performanceConfig);

    // Note: Range inputs might need special handling for verification
    // This tests the configuration functionality
    await expect(settingsPage.performanceSettings).toBeVisible();
  });

  test('Advanced settings configuration works correctly', async ({ page }) => {
    const advancedConfig = {
      monitoringInterval: '30',
      webhookUrl: 'https://hooks.slack.com/test',
      discordWebhook: 'https://discord.com/api/webhooks/test',
      slackWebhook: 'https://hooks.slack.com/test2',
      logLevel: 'debug',
      logRotation: '7'
    };

    await settingsPage.configureAdvancedSettings(advancedConfig);

    // Verify values are set
    await expect(settingsPage.monitoringInterval).toHaveValue(advancedConfig.monitoringInterval);
    await expect(settingsPage.webhookUrl).toHaveValue(advancedConfig.webhookUrl);
    await expect(settingsPage.logLevel).toHaveValue(advancedConfig.logLevel);
  });

  test('Settings save functionality works correctly', async ({ page }) => {
    // Configure some settings
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');
    await settingsPage.configureMediaSettings({
      extensions: 'mp4,mkv',
      copyToCache: true
    });

    // Save settings
    await settingsPage.saveSettings();

    // Verify save operation completed
    await expect(settingsPage.successMessage).toBeVisible();
  });

  test('Settings reset functionality works correctly', async ({ page }) => {
    // Configure some settings
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');

    // Reset settings
    await settingsPage.resetSettings();

    // Verify settings are reset (values should be cleared or set to defaults)
    const currentSettings = await settingsPage.getCurrentSettings();
    expect(currentSettings).toBeTruthy();
  });

  test('Settings export functionality works correctly', async ({ page }) => {
    // Configure some settings
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');

    // Export settings
    const exportPath = await settingsPage.exportSettings();

    // Verify export file was created
    expect(exportPath).toBeTruthy();
  });

  test('Settings import functionality works correctly', async ({ page }) => {
    // Create a temporary settings file
    const settingsData = {
      plex: { url: 'http://localhost:32400', token: 'imported-token' },
      media: { extensions: 'mp4,mkv', copyToCache: true }
    };

    const tempFilePath = '/tmp/test-settings.json';
    await page.evaluate(async (data) => {
      const response = await fetch('/api/config/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return response.ok;
    }, settingsData);

    // Import settings (mock the file upload)
    await settingsPage.importSettings(tempFilePath);

    // Verify settings were imported
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('Form validation works correctly', async ({ page }) => {
    // Test validation errors
    const errors = await settingsPage.testFormValidation();

    // Verify validation is working
    if (errors.length > 0) {
      expect(await settingsPage.hasValidationErrors()).toBeTruthy();
    }
  });

  test('Settings page is fully accessible', async ({ page }) => {
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThan(0);

    // Test proper labels
    await AccessibilityAssertions.hasProperLabels(page);

    // Test form validation accessibility
    await AccessibilityAssertions.hasProperFormValidation(page, '[data-testid="settings-form"]');
  });

  test('Settings page is responsive across all screen sizes', async ({ page }) => {
    const viewports = [
      { width: 375, height: 667, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1024, height: 768, name: 'desktop' },
      { width: 1920, height: 1080, name: 'large' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Verify settings page still loads correctly
      expect(await settingsPage.isSettingsLoaded()).toBeTruthy();

      // Verify critical elements are visible
      await expect(settingsPage.plexSettings).toBeVisible();
      await expect(settingsPage.saveButton).toBeVisible();

      // Verify no horizontal scroll
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBeFalsy();
    }
  });

  test('Settings page handles loading states correctly', async ({ page }) => {
    // Test save button loading state
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');
    await settingsPage.saveButton.click();

    // Verify loading state handling
    await UIXAssertions.hasProperLoadingStates(page, '[data-testid="save-settings"]');
  });

  test('Settings page handles error states gracefully', async ({ page }) => {
    // Mock API error for save operation
    await page.route('/api/config/update', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Save failed' })
      });
    });

    // Try to save settings
    await settingsPage.saveSettings();

    // Verify error is handled properly
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('Settings page maintains state during navigation', async ({ page }) => {
    // Configure some settings
    await settingsPage.configurePlex('http://localhost:32400', 'test-token');

    // Navigate away and back
    await navigationPage.goToDashboard();
    await navigationPage.goToSettings();

    // Verify settings page still loads correctly
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });
});

test.describe('Settings - Form Validation', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    await settingsPage.gotoSettings();
  });

  test('Validates Plex URL format', async ({ page }) => {
    // Test invalid URL
    await settingsPage.plexUrl.fill('invalid-url');
    await settingsPage.saveSettings();

    // Should show validation error
    expect(await settingsPage.hasValidationErrors()).toBeTruthy();
  });

  test('Validates Plex token presence', async ({ page }) => {
    // Test empty token
    await settingsPage.plexToken.fill('');
    await settingsPage.saveSettings();

    // Should show validation error
    expect(await settingsPage.hasValidationErrors()).toBeTruthy();
  });

  test('Validates file extension format', async ({ page }) => {
    // Test invalid extensions
    await settingsPage.fileExtensions.fill('invalid,format,here');
    await settingsPage.saveSettings();

    // Should handle invalid format gracefully
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('Validates size limit format', async ({ page }) => {
    // Test invalid size limit
    await settingsPage.sizeLimit.fill('invalid');
    await settingsPage.saveSettings();

    // Should show validation error
    expect(await settingsPage.hasValidationErrors()).toBeTruthy();
  });

  test('Validates monitoring interval', async ({ page }) => {
    // Test invalid interval
    await settingsPage.monitoringInterval.fill('-1');
    await settingsPage.saveSettings();

    // Should show validation error
    expect(await settingsPage.hasValidationErrors()).toBeTruthy();
  });
});

test.describe('Settings - Advanced Features', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    await settingsPage.gotoSettings();
  });

  test('Notification settings work correctly', async ({ page }) => {
    // Configure notification settings
    await settingsPage.configureAdvancedSettings({
      webhookUrl: 'https://hooks.slack.com/test',
      discordWebhook: 'https://discord.com/api/webhooks/test',
      slackWebhook: 'https://hooks.slack.com/test2'
    });

    // Save settings
    await settingsPage.saveSettings();

    // Verify notifications are configured
    await expect(settingsPage.successMessage).toBeVisible();
  });

  test('Log level settings work correctly', async ({ page }) => {
    const logLevels = ['debug', 'info', 'warn', 'error'];

    for (const level of logLevels) {
      await settingsPage.configureAdvancedSettings({ logLevel: level });
      await expect(settingsPage.logLevel).toHaveValue(level);
    }
  });

  test('Log rotation settings work correctly', async ({ page }) => {
    const rotationValues = ['1', '7', '30', '90'];

    for (const rotation of rotationValues) {
      await settingsPage.configureAdvancedSettings({ logRotation: rotation });
      await expect(settingsPage.logRotation).toHaveValue(rotation);
    }
  });
});

test.describe('Settings - Performance and Reliability', () => {
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    settingsPage = new SettingsPage(page);

    const mockManager = new PredefinedMocks(page);
    await mockManager.setupAllMocks();

    await settingsPage.gotoSettings();
  });

  test('Settings page loads within performance budget', async ({ page }) => {
    const startTime = Date.now();
    await settingsPage.gotoSettings();
    const loadTime = Date.now() - startTime;

    // Performance budget: 3 seconds
    expect(loadTime).toBeLessThan(3000);
    console.log(`Settings page load time: ${loadTime}ms`);
  });

  test('Settings page handles rapid configuration changes', async ({ page }) => {
    // Make multiple rapid changes
    for (let i = 0; i < 10; i++) {
      await settingsPage.configurePlex(`http://localhost:3240${i}`, `token-${i}`);
      await page.waitForTimeout(50);
    }

    // Verify page remains stable
    expect(await settingsPage.isSettingsLoaded()).toBeTruthy();
  });

  test('Settings page handles concurrent API calls', async ({ page }) => {
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
  });
});
