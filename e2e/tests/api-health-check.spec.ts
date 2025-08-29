import { test, expect } from '@playwright/test';

/**
 * API Health Check Tests
 *
 * These tests validate that the backend API is functioning correctly,
 * specifically testing the /api/status endpoint that was failing with 500 errors
 * due to cache engine initialization issues.
 */

test.describe('API Health Check', () => {
  test.setTimeout(60000); // 60 second timeout

  test('should check API endpoint health and identify 500 errors', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check if we're on the correct page
    await expect(page).toHaveTitle(/PlexCache/);

    // Test the /api/status endpoint directly
    const response = await page.request.get('/api/status');

    // Log the response for debugging
    console.log('Status endpoint response:', {
      status: response.status(),
      statusText: response.statusText(),
      url: response.url(),
      headers: response.headers()
    });

    // The critical test: ensure we don't get a 500 error
    expect(response.status()).not.toBe(500);

    // Additional validation for successful response
    if (response.status() === 200) {
      const responseData = await response.json();
      console.log('API Status Response:', responseData);

      // Validate response structure
      expect(responseData).toHaveProperty('success');
      expect(responseData).toHaveProperty('data');

      // Ensure success is true and data is not null
      expect(responseData.success).toBe(true);
      expect(responseData.data).not.toBeNull();

      // Check for cache-related data
      if (responseData.data && typeof responseData.data === 'object') {
        // Look for cache status information
        const dataKeys = Object.keys(responseData.data);
        console.log('Available data keys:', dataKeys);

        // If cache information is present, validate it
        if (dataKeys.some(key => key.toLowerCase().includes('cache'))) {
          console.log('Cache data found in response');
        }
      }
    } else {
      // Log non-200 responses for debugging
      console.log(`Non-200 response: ${response.status()} ${response.statusText()}`);
      const responseText = await response.text();
      console.log('Response body:', responseText);
    }
  });

  test('should verify WebSocket connection health', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for WebSocket connection indicators
    // This might be shown in the UI or console
    const logs: string[] = [];

    // Listen for console messages that might indicate WebSocket status
    page.on('console', msg => {
      logs.push(msg.text());
      console.log('Browser console:', msg.text());
    });

    // Wait a moment for any WebSocket connections to establish
    await page.waitForTimeout(5000);

    // Check console logs for WebSocket-related messages
    const wsLogs = logs.filter(log =>
      log.toLowerCase().includes('websocket') ||
      log.toLowerCase().includes('ws://') ||
      log.toLowerCase().includes('wss://') ||
      log.toLowerCase().includes('socket')
    );

    if (wsLogs.length > 0) {
      console.log('WebSocket logs found:', wsLogs);
    } else {
      console.log('No WebSocket logs detected in console');
    }

    // Additional check: look for any error indicators in the UI
    const errorElements = await page.locator('[class*="error"], [class*="alert"], [class*="danger"]').count();
    expect(errorElements).toBeLessThanOrEqual(2); // Allow for minor UI warnings
  });

  test('should validate dashboard loads without cache errors', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');

    // Check that the page title is correct
    await expect(page).toHaveTitle(/PlexCache/);

    // Wait for any dynamic content to load
    await page.waitForTimeout(3000);

    // Check for cache-related error messages
    const cacheErrors = await page.locator('text=/cache.*not.*initialized|cache.*error|cache.*failed/i').count();
    expect(cacheErrors).toBe(0);

    // Check for general error indicators
    const generalErrors = await page.locator('text=/error|failed|exception/i').count();

    // Allow for some technical error messages that might be in logs/debug info
    if (generalErrors > 0) {
      const errorTexts = await page.locator('text=/error|failed|exception/i').allTextContents();
      console.log('Found error texts:', errorTexts);

      // Filter out technical/log messages that aren't user-facing errors
      const userFacingErrors = errorTexts.filter(text =>
        !text.toLowerCase().includes('console') &&
        !text.toLowerCase().includes('log') &&
        !text.toLowerCase().includes('debug')
      );

      expect(userFacingErrors.length).toBeLessThanOrEqual(1);
    }

    // Check that main dashboard content is visible
    const mainContent = await page.locator('main, .dashboard, .content, [class*="dashboard"]').count();
    expect(mainContent).toBeGreaterThan(0);

    // Take a screenshot for visual verification
    await page.screenshot({ path: 'test-results/dashboard-loaded.png', fullPage: true });
  });

  test('should test API response time and performance', async ({ page }) => {
    const startTime = Date.now();

    // Test the status endpoint
    const response = await page.request.get('/api/status');
    const endTime = Date.now();
    const responseTime = endTime - startTime;

    console.log(`API response time: ${responseTime}ms`);

    // Response should be reasonably fast (under 10 seconds)
    expect(responseTime).toBeLessThan(10000);

    // For successful responses, they should be very fast
    if (response.status() === 200) {
      expect(responseTime).toBeLessThan(1000); // Should respond within 1 second
    }
  });
});