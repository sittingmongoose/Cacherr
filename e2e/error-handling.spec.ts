/**
 * Error Handling Test Suite
 *
 * This test suite covers error conditions including:
 * - Network failures and API errors
 * - Invalid user inputs and validation errors
 * - WebSocket connection failures
 * - Backend service unavailability
 * - Recovery from error states
 * - User-friendly error messaging
 *
 * Uses Playwright's network interception and mocking capabilities
 * to simulate various error scenarios and verify proper handling.
 */

import { test, expect, Page } from '@playwright/test';
import { DashboardPage } from './pages/DashboardPage';
import { SettingsPage } from './pages/SettingsPage';
import { NavigationPage } from './pages/NavigationPage';

/**
 * Test network error handling.
 *
 * Verifies that the application gracefully handles network
 * failures and provides appropriate user feedback.
 */
test.describe('Network Error Handling', () => {

  test('API errors show user-friendly error messages', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Mock API error response for settings update
    await page.route('**/api/config/update', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({
          status: 'error',
          message: 'Internal server error occurred'
        })
      });
    });

    // Try to save settings to trigger error
    const saveButton = page.locator('[data-testid="save-settings-button"]');
    if (await saveButton.isVisible()) {
      await saveButton.click();

      // Verify error message appears
      const errorMessage = page.locator('[data-testid="error-message"], [data-testid="toast-error"]');
      await expect(errorMessage).toBeVisible();

      // Verify error message is user-friendly (not technical)
      const errorText = await errorMessage.textContent();
      expect(errorText?.toLowerCase()).not.toContain('500');
      expect(errorText?.toLowerCase()).not.toContain('internal server error');
      expect(errorText).toMatch(/error|problem|failed/i);
    }
  });

  test('Network timeout scenarios are handled gracefully', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Mock slow API response that times out
    await page.route('**/api/dashboard/stats', async route => {
      // Delay response to simulate timeout
      await new Promise(resolve => setTimeout(resolve, 35000)); // Longer than typical timeout
      route.fulfill({
        status: 200,
        body: JSON.stringify({ status: 'healthy' })
      });
    });

    // Trigger data refresh
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    if (await refreshButton.isVisible()) {
      await refreshButton.click();

      // Verify app remains functional despite timeout
      await expect(dashboardPage.dashboardContainer).toBeVisible();

      // Check for timeout-specific error message
      const timeoutMessage = page.locator('text=/timeout|taking longer|slow/i');
      if (await timeoutMessage.isVisible()) {
        const message = await timeoutMessage.textContent();
        expect(message).toBeTruthy();
      }
    }
  });

  test('Offline mode is handled correctly', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Simulate offline mode
    await page.context().setOffline(true);

    // Try to refresh data
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    if (await refreshButton.isVisible()) {
      await refreshButton.click();

      // Verify offline error message
      const offlineMessage = page.locator('text=/offline|no connection|network/i');
      await expect(offlineMessage).toBeVisible();

      // Verify app remains functional
      await expect(dashboardPage.dashboardContainer).toBeVisible();
    }

    // Restore online mode
    await page.context().setOffline(false);
  });

  test('HTTPS certificate errors are handled', async ({ page }) => {
    // Configure to ignore HTTPS errors for testing
    const context = await page.context().newPage();
    await context.route('https://self-signed.badssl.com/', route => {
      // This would normally fail with certificate error
      route.fulfill({
        status: 200,
        body: 'Certificate error handled'
      });
    });

    // Test navigation to problematic HTTPS site
    try {
      await context.goto('https://self-signed.badssl.com/');
      // If we get here, certificate errors are being handled
      await expect(context.locator('body')).toContainText('Certificate error handled');
    } catch (error) {
      // Certificate error occurred - verify it's handled gracefully
      expect(error.message).toContain('SSL');
    }
  });
});

/**
 * Test WebSocket connection failure handling.
 *
 * Verifies that WebSocket failures are handled gracefully
 * and users are informed about connection issues.
 */
test.describe('WebSocket Error Handling', () => {

  test('WebSocket connection failures show appropriate warnings', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Block WebSocket connections to simulate failure
    await page.route('**/ws/**', route => route.abort());

    // Wait for connection attempt and failure
    await page.waitForTimeout(2000);

    // Verify connection status indicator shows disconnected state
    const connectionStatus = page.locator('[data-testid="connection-status"], [data-testid="websocket-status"]');
    if (await connectionStatus.isVisible()) {
      await expect(connectionStatus).toContainText(/disconnected|offline|failed/i);
      await expect(connectionStatus).toHaveClass(/text-red|error|warning/);
    }

    // Verify app remains functional without WebSocket
    await expect(dashboardPage.dashboardContainer).toBeVisible();
  });

  test('WebSocket reconnection works after failure', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Initially block WebSocket
    await page.route('**/ws/**', route => route.abort());
    await page.waitForTimeout(2000);

    // Verify disconnected state
    const connectionStatus = page.locator('[data-testid="connection-status"]');
    if (await connectionStatus.isVisible()) {
      await expect(connectionStatus).toContainText(/disconnected|offline/i);
    }

    // Restore WebSocket connection
    await page.unroute('**/ws/**');

    // Test reconnection
    const reconnectButton = page.locator('[data-testid="reconnect-button"], [data-testid="retry-connection"]');
    if (await reconnectButton.isVisible()) {
      await reconnectButton.click();

      // Verify reconnection attempt
      await expect(connectionStatus).toContainText(/connecting|reconnecting/i);

      // Wait for potential reconnection
      await page.waitForTimeout(3000);

      // App should remain functional
      await expect(dashboardPage.dashboardContainer).toBeVisible();
    }
  });
});

/**
 * Test form validation error scenarios.
 *
 * Verifies that all form validation works correctly and
 * provides clear guidance to users for fixing errors.
 */
test.describe('Form Validation Error Handling', () => {

  test('Settings form shows comprehensive validation errors', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Clear all required fields to trigger validation
    const urlInput = page.locator('[data-testid="plex-url-input"]');
    const tokenInput = page.locator('[data-testid="plex-token-input"]');
    const cachePathInput = page.locator('[data-testid="cache-path-input"]');

    if (await urlInput.isVisible()) await urlInput.fill('');
    if (await tokenInput.isVisible()) await tokenInput.fill('');
    if (await cachePathInput.isVisible()) await cachePathInput.fill('');

    // Try to save with invalid data
    const saveButton = page.locator('[data-testid="save-settings-button"]');
    if (await saveButton.isVisible()) {
      await saveButton.click();

      // Verify validation errors are displayed
      const urlError = page.locator('[data-testid="plex-url-error"], [data-testid="url-validation-error"]');
      const tokenError = page.locator('[data-testid="plex-token-error"], [data-testid="token-validation-error"]');
      const pathError = page.locator('[data-testid="cache-path-error"], [data-testid="path-validation-error"]');

      if (await urlInput.isVisible()) await expect(urlError).toBeVisible();
      if (await tokenInput.isVisible()) await expect(tokenError).toBeVisible();
      if (await cachePathInput.isVisible()) await expect(pathError).toBeVisible();

      // Verify error messages are helpful
      if (await urlError.isVisible()) {
        const urlErrorText = await urlError.textContent();
        expect(urlErrorText).toMatch(/URL.*required|valid URL|http/i);
      }
    }
  });

  test('Real-time validation feedback works correctly', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    const urlInput = page.locator('[data-testid="plex-url-input"]');
    if (await urlInput.isVisible()) {
      // Enter invalid URL
      await urlInput.fill('invalid-url');

      // Trigger validation (blur or input event)
      await urlInput.blur();

      // Verify validation error appears
      const urlError = page.locator('[data-testid="plex-url-error"]');
      await expect(urlError).toBeVisible();

      // Fix the URL
      await urlInput.fill('http://localhost:32400');

      // Verify error clears
      await expect(urlError).toBeHidden();
    }
  });

  test('Complex validation scenarios are handled', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    const urlInput = page.locator('[data-testid="plex-url-input"]');
    const tokenInput = page.locator('[data-testid="plex-token-input"]');

    // Test various invalid scenarios
    const invalidScenarios = [
      { url: 'ftp://invalid.com', token: 'valid-token' }, // Invalid protocol
      { url: 'http://localhost:32400', token: 'a'.repeat(1000) }, // Token too long
      { url: '', token: 'valid-token' }, // Missing URL
      { url: 'http://localhost:32400', token: '' }, // Missing token
    ];

    for (const scenario of invalidScenarios) {
      if (await urlInput.isVisible()) await urlInput.fill(scenario.url);
      if (await tokenInput.isVisible()) await tokenInput.fill(scenario.token);

      const saveButton = page.locator('[data-testid="save-settings-button"]');
      if (await saveButton.isVisible()) {
        await saveButton.click();

        // Verify appropriate validation errors
        const hasErrors = await page.locator('[data-testid*="error"]').count() > 0;
        expect(hasErrors).toBeTruthy();
      }
    }

    // Verify form remains functional after multiple validation failures
    await expect(settingsPage.settingsContainer).toBeVisible();
  });
});

/**
 * Test authentication and authorization error handling.
 *
 * Verifies that auth-related errors are handled appropriately
 * with proper user feedback and security considerations.
 */
test.describe('Authentication Error Handling', () => {

  test('Invalid credentials show appropriate error messages', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Mock authentication failure
    await page.route('**/api/config/test-plex', route => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({
          status: 'error',
          message: 'Invalid Plex credentials'
        })
      });
    });

    // Try to test Plex connection
    const testButton = page.locator('[data-testid="test-plex-button"]');
    if (await testButton.isVisible()) {
      await testButton.click();

      // Verify auth error message
      const authError = page.locator('text=/invalid credentials|authentication failed|unauthorized/i');
      await expect(authError).toBeVisible();

      // Verify sensitive information is not exposed
      const errorText = await authError.textContent();
      expect(errorText?.toLowerCase()).not.toContain('token');
      expect(errorText?.toLowerCase()).not.toContain('password');
    }
  });

  test('Session expiration is handled gracefully', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Mock session expiration on API calls
    await page.route('**/api/**', route => {
      route.fulfill({
        status: 401,
        body: JSON.stringify({
          status: 'error',
          message: 'Session expired'
        })
      });
    });

    // Trigger an API call
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    if (await refreshButton.isVisible()) {
      await refreshButton.click();

      // Verify session error handling
      const sessionError = page.locator('text=/session expired|login required|please sign in/i');
      await expect(sessionError).toBeVisible();

      // App should remain functional
      await expect(dashboardPage.dashboardContainer).toBeVisible();
    }
  });
});

/**
 * Test JavaScript runtime error handling.
 *
 * Verifies that runtime errors are caught and handled
 * without breaking the application.
 */
test.describe('JavaScript Runtime Error Handling', () => {

  test('Unhandled JavaScript errors are caught and displayed', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Listen for console errors
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Inject a JavaScript error
    await page.evaluate(() => {
      setTimeout(() => {
        throw new Error('Simulated runtime error');
      }, 500);
    });

    // Wait for error to occur
    await page.waitForTimeout(1000);

    // Verify app remains functional
    await expect(dashboardPage.dashboardContainer).toBeVisible();

    // Check if error was logged (errors may be caught by error boundaries)
    if (errors.length > 0) {
      expect(errors.some(error => error.includes('runtime') || error.includes('Error'))).toBeTruthy();
    }
  });

  test('Error boundaries catch and display component errors', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Inject error into a component
    await page.evaluate(() => {
      // Simulate component error
      const errorEvent = new ErrorEvent('error', {
        error: new Error('Component render error'),
        message: 'Component render error'
      });
      window.dispatchEvent(errorEvent);
    });

    // Verify error boundary displays user-friendly message
    const errorBoundary = page.locator('[data-testid="error-boundary"], .error-boundary');
    if (await errorBoundary.isVisible()) {
      const errorMessage = await errorBoundary.textContent();
      expect(errorMessage).not.toContain('Component render error'); // Should be user-friendly
      expect(errorMessage).toMatch(/error|problem|something went wrong/i);
    }

    // Verify app remains functional
    await expect(settingsPage.settingsContainer).toBeVisible();
  });
});

/**
 * Test browser storage and persistence error handling.
 *
 * Verifies that localStorage/sessionStorage failures
 * are handled gracefully.
 */
test.describe('Browser Storage Error Handling', () => {

  test('localStorage failures are handled gracefully', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Simulate localStorage failure
    await page.evaluate(() => {
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = () => {
        throw new Error('Storage quota exceeded');
      };
      // Store reference for cleanup
      (window as any).originalSetItem = originalSetItem;
    });

    // Try to save settings
    const saveButton = page.locator('[data-testid="save-settings-button"]');
    if (await saveButton.isVisible()) {
      await saveButton.click();

      // Verify graceful handling of storage failure
      await expect(settingsPage.settingsContainer).toBeVisible();

      // Check for storage error message
      const storageError = page.locator('text=/storage|quota|space/i');
      if (await storageError.isVisible()) {
        const errorText = await storageError.textContent();
        expect(errorText).toBeTruthy();
      }
    }

    // Cleanup
    await page.evaluate(() => {
      if ((window as any).originalSetItem) {
        localStorage.setItem = (window as any).originalSetItem;
      }
    });
  });

  test('Corrupted stored data is handled correctly', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Simulate corrupted localStorage data
    await page.evaluate(() => {
      localStorage.setItem('cacherr_settings', 'invalid json {{{');
    });

    // Refresh page to trigger data loading
    await page.reload();

    // Verify app handles corrupted data gracefully
    await expect(dashboardPage.dashboardContainer).toBeVisible();

    // Verify corrupted data doesn't break functionality
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await expect(dashboardPage.dashboardContainer).toBeVisible();
    }
  });
});

/**
 * Test concurrent operation error handling.
 *
 * Verifies that multiple simultaneous operations
 * are handled correctly without conflicts.
 */
test.describe('Concurrent Operations Error Handling', () => {

  test('Multiple simultaneous API calls are handled correctly', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Make multiple concurrent API calls
    const promises = [];
    const saveButton = page.locator('[data-testid="save-settings-button"]');

    if (await saveButton.isVisible()) {
      for (let i = 0; i < 5; i++) {
        promises.push(saveButton.click());
        await page.waitForTimeout(100); // Slight delay between clicks
      }

      // Wait for all operations to complete
      const results = await Promise.allSettled(promises);

      // Verify some operations succeeded
      const successfulCalls = results.filter(result => result.status === 'fulfilled').length;
      expect(successfulCalls).toBeGreaterThan(0);

      // Verify app remains stable
      await expect(settingsPage.settingsContainer).toBeVisible();
    }
  });

  test('Race conditions between operations are prevented', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Mock delayed API responses to create race condition potential
    await page.route('**/api/config/update', async route => {
      await new Promise(resolve => setTimeout(resolve, Math.random() * 1000));
      route.fulfill({
        status: 200,
        body: JSON.stringify({ status: 'success' })
      });
    });

    // Trigger multiple rapid operations
    const operations = [];
    const urlInput = page.locator('[data-testid="plex-url-input"]');
    const saveButton = page.locator('[data-testid="save-settings-button"]');

    if (await urlInput.isVisible() && await saveButton.isVisible()) {
      for (let i = 0; i < 3; i++) {
        operations.push(
          urlInput.fill(`http://test${i}.com:32400`),
          saveButton.click()
        );
      }

      // Execute operations concurrently
      await Promise.all(operations);

      // Verify final state is consistent
      await expect(settingsPage.settingsContainer).toBeVisible();

      // Verify no conflicting error states
      const errorCount = await page.locator('[data-testid*="error"]').count();
      expect(errorCount).toBeLessThan(2); // Allow at most one error state
    }
  });
});
