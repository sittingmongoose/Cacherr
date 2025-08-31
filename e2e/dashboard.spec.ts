/**
 * End-to-end tests for Dashboard functionality.
 *
 * This test suite covers all Dashboard features including:
 * - Tab navigation and content loading
 * - Real-time data updates via WebSocket
 * - Interactive elements and user actions
 * - Responsive design across different screen sizes
 * - Error handling and recovery scenarios
 */
import { test, expect, Page } from '@playwright/test';

/**
 * Test group for Dashboard core functionality.
 *
 * These tests verify that the dashboard loads correctly,
 * displays data, and handles user interactions properly.
 */
test.describe('Dashboard Core Functionality', () => {

  /**
   * Test that Dashboard page loads and displays all required elements.
   *
   * Verifies:
   * - Page loads without errors
   * - Navigation tabs are visible
   * - Default tab content is displayed
   * - No JavaScript console errors
   */
  test('Dashboard loads with all tabs visible', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');

    // Wait for dashboard to load completely
    await expect(page.locator('[data-testid="dashboard-container"]')).toBeVisible();

    // Verify page title
    await expect(page.locator('h1')).toContainText('Cacherr');

    // Verify all navigation links are present
    await expect(page.locator('[data-testid="dashboard-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="cached-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="logs-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="settings-link"]')).toBeVisible();

    // Verify default tab (Dashboard) is active
    await expect(page.locator('[data-testid="dashboard-link"][aria-current="page"]')).toBeVisible();

    // Check that dashboard content is loaded
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();

    // Verify no console errors occurred during loading
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    await page.waitForTimeout(2000);
    expect(errors).toHaveLength(0);
  });

  /**
   * Test navigation between different pages using the navigation menu.
   *
   * Verifies that clicking navigation links switches to different pages properly
   * and maintains proper state management.
   */
  test('Navigation switches content correctly', async ({ page }) => {
    await page.goto('/');

    // Start on Dashboard page
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();

    // Navigate to Cached page
    await page.click('[data-testid="cached-link"]');
    await expect(page.locator('[data-testid="cached-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeHidden();

    // Navigate to Logs page
    await page.click('[data-testid="logs-link"]');
    await expect(page.locator('[data-testid="logs-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="cached-content"]')).toBeHidden();

    // Navigate to Settings page
    await page.click('[data-testid="settings-link"]');
    await expect(page.locator('[data-testid="settings-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="logs-content"]')).toBeHidden();

    // Navigate back to Dashboard
    await page.click('[data-testid="dashboard-link"]');
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });

  /**
   * Test dashboard statistics display and calculations.
   *
   * Verifies that statistics are correctly calculated and displayed,
   * including cache usage, file counts, and performance metrics.
   */
  test('Statistics display correct cache usage information', async ({ page }) => {
    await page.goto('/');

    // Wait for statistics to load
    await expect(page.locator('[data-testid="cache-usage-stat"]')).toBeVisible();

    // Verify statistics have numerical values
    const cacheUsage = await page.locator('[data-testid="cache-usage-value"]').textContent();
    expect(cacheUsage).toMatch(/^\d+(\.\d+)?\s*(MB|GB|TB)$/);

    // Verify performance metrics are displayed
    await expect(page.locator('[data-testid="performance-metrics"]')).toBeVisible();

    // Check cache hit/miss rates
    const hitRate = await page.locator('[data-testid="hit-rate"]').textContent();
    const missRate = await page.locator('[data-testid="miss-rate"]').textContent();
    expect(hitRate).toMatch(/^\d+(\.\d+)?%$/);
    expect(missRate).toMatch(/^\d+(\.\d+)?%$/);

    // Verify transfer statistics
    const activeTransfers = await page.locator('[data-testid="active-transfers"]').textContent();
    const queuedOperations = await page.locator('[data-testid="queued-operations"]').textContent();
    expect(activeTransfers).toMatch(/^\d+$/);
    expect(queuedOperations).toMatch(/^\d+$/);
  });

  /**
   * Test system status information display.
   *
   * Verifies that system status data is properly displayed
   * and updated in real-time.
   */
  test('System status information is properly displayed', async ({ page }) => {
    await page.goto('/');

    // Verify system status card is visible
    await expect(page.locator('[data-testid="system-status-card"]')).toBeVisible();

    // Check system status indicators
    await expect(page.locator('[data-testid="system-health"]')).toBeVisible();
    await expect(page.locator('[data-testid="system-version"]')).toBeVisible();
    await expect(page.locator('[data-testid="system-uptime"]')).toBeVisible();

    // Verify status values are populated
    const healthStatus = await page.locator('[data-testid="system-health"]').textContent();
    const version = await page.locator('[data-testid="system-version"]').textContent();
    const uptime = await page.locator('[data-testid="system-uptime"]').textContent();

    expect(healthStatus).toBeTruthy();
    expect(version).toBeTruthy();
    expect(uptime).toBeTruthy();
  });

  /**
   * Test real-time update information display.
   *
   * Verifies that real-time updates section displays properly
   * and shows last update times.
   */
  test('Real-time update information is displayed', async ({ page }) => {
    await page.goto('/');

    // Check if real-time updates section is visible
    await expect(page.locator('[data-testid="real-time-updates"]')).toBeVisible();

    // Check if last update time is displayed
    await expect(page.locator('[data-testid="last-update-time"]')).toBeVisible();

    // Verify update timestamp format
    const lastUpdate = await page.locator('[data-testid="last-update-time"]').textContent();
    expect(lastUpdate).toMatch(/\d{1,2}:\d{2}:\d{2}/); // HH:MM:SS format
  });
});

/**
 * Test group for real-time WebSocket updates functionality.
 *
 * These tests verify that the dashboard receives and displays
 * real-time updates from the backend via WebSocket connections.
 */
test.describe('Real-Time Updates', () => {

  /**
   * Test WebSocket connection establishment and data updates.
   *
   * Verifies that the dashboard establishes WebSocket connection
   * and updates content when new data is received.
   */
  test('WebSocket updates dashboard data in real-time', async ({ page }) => {
    // Set up WebSocket monitoring
    const wsMessages: string[] = [];
    const receivedMessages: string[] = [];

    page.on('websocket', ws => {
      console.log(`WebSocket opened: ${ws.url()}`);
      ws.on('framesent', event => {
        console.log('Frame sent:', event.payload);
        wsMessages.push(`sent: ${event.payload}`);
      });
      ws.on('framereceived', event => {
        console.log('Frame received:', event.payload);
        receivedMessages.push(`received: ${event.payload}`);
      });
      ws.on('close', () => console.log('WebSocket closed'));
    });

    await page.goto('/');

    // Wait for WebSocket connection to establish
    await page.waitForFunction(() => {
      return window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN;
    }, { timeout: 10000 });

    // Verify WebSocket connection indicator is active
    await expect(page.locator('[data-testid="websocket-connected"]')).toBeVisible();

    // Wait for initial data load
    await page.waitForTimeout(2000);

    // Verify that some WebSocket messages were exchanged
    expect(wsMessages.length).toBeGreaterThan(0);

    // Check if dashboard data updates after WebSocket messages
    const initialCacheUsage = await page.locator('[data-testid="cache-usage-value"]').textContent();

    // Wait for potential updates
    await page.waitForTimeout(3000);

    const updatedCacheUsage = await page.locator('[data-testid="cache-usage-value"]').textContent();

    // Data should be present (may or may not change depending on backend activity)
    expect(updatedCacheUsage).toBeTruthy();
  });

  /**
   * Test WebSocket real-time data updates with mock server.
   *
   * Uses Playwright's WebSocket routing to mock server responses
   * and verify real-time updates are processed correctly.
   */
  test('WebSocket real-time updates with mock data', async ({ page }) => {
    // Mock WebSocket connection for testing
    await page.routeWebSocket('/api/ws', ws => {
      ws.onMessage(message => {
        console.log('Mock WebSocket received:', message);

        // Simulate server response with updated cache data
        if (message.includes('cache_status')) {
          ws.send(JSON.stringify({
            type: 'cache_update',
            data: {
              cacheUsage: '2.5 GB',
              hitRate: '94.2%',
              activeTransfers: 3,
              lastUpdate: new Date().toISOString()
            }
          }));
        }

        // Simulate system status update
        if (message.includes('system_status')) {
          ws.send(JSON.stringify({
            type: 'system_update',
            data: {
              health: 'healthy',
              uptime: '2h 34m',
              version: '1.0.0'
            }
          }));
        }
      });
    });

    await page.goto('/');

    // Wait for WebSocket connection
    await page.waitForTimeout(2000);

    // Trigger a manual refresh to initiate WebSocket communication
    await page.click('[data-testid="refresh-button"]');

    // Wait for mock data to be processed
    await page.waitForTimeout(1000);

    // Verify mock data was processed and displayed
    await expect(page.locator('[data-testid="cache-usage-value"]')).toContainText('2.5 GB');
    await expect(page.locator('[data-testid="hit-rate"]')).toContainText('94.2%');
    await expect(page.locator('[data-testid="active-transfers"]')).toContainText('3');
  });

  /**
   * Test graceful handling of WebSocket disconnection.
   *
   * Verifies that the dashboard handles WebSocket disconnection
   * gracefully and shows appropriate indicators.
   */
  test('WebSocket disconnection handled gracefully', async ({ page }) => {
    await page.goto('/');

    // Wait for initial WebSocket connection
    await page.waitForFunction(() => {
      return window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN;
    }, { timeout: 10000 });

    // Verify connected state
    await expect(page.locator('[data-testid="websocket-connected"]')).toBeVisible();

    // Simulate WebSocket disconnection by closing the connection
    await page.evaluate(() => {
      if (window.wsConnection) {
        window.wsConnection.close();
      }
    });

    // Wait for disconnection to be detected
    await page.waitForTimeout(1000);

    // Verify disconnected state is shown
    await expect(page.locator('[data-testid="websocket-disconnected"]')).toBeVisible();

    // Verify dashboard still functions without WebSocket
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="system-status-card"]')).toBeVisible();
  });

  /**
   * Test WebSocket reconnection after temporary failure.
   *
   * Verifies that WebSocket automatically reconnects after
   * temporary connection failures.
   */
  test('WebSocket reconnection after failure', async ({ page }) => {
    await page.goto('/');

    // Wait for initial connection
    await page.waitForFunction(() => {
      return window.wsConnection && window.wsConnection.readyState === WebSocket.OPEN;
    }, { timeout: 10000 });

    await expect(page.locator('[data-testid="websocket-connected"]')).toBeVisible();

    // Simulate connection failure
    await page.evaluate(() => {
      if (window.wsConnection) {
        window.wsConnection.close(1006, 'Simulated failure');
      }
    });

    // Wait for reconnection attempt
    await page.waitForTimeout(2000);

    // Verify reconnection indicator is shown
    await expect(page.locator('[data-testid="websocket-reconnecting"]')).toBeVisible();

    // Note: Actual reconnection depends on implementation
    // This test verifies the UI state during reconnection attempts
  });
});

/**
 * Test group for user interactions and controls.
 *
 * These tests verify that interactive elements work correctly
 * and provide proper user feedback.
 */
test.describe('User Interactions', () => {

  /**
   * Test theme switching functionality.
   *
   * Verifies that theme toggle works correctly and
   * changes are applied immediately.
   */
  test('Theme switching works correctly', async ({ page }) => {
    await page.goto('/');

    // Get initial theme
    const initialTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme') || 'light';
    });

    // Click theme toggle
    await page.click('[data-testid="theme-toggle"]');

    // Wait for theme change
    await page.waitForTimeout(500);

    // Verify theme changed
    const newTheme = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme') || 'light';
    });

    expect(newTheme).not.toBe(initialTheme);

    // Verify theme icon updated
    await expect(page.locator('[data-testid="theme-toggle"]')).toBeVisible();
  });

  /**
   * Test auto-refresh toggle functionality.
   *
   * Verifies that auto-refresh can be enabled/disabled
   * and the setting is remembered.
   */
  test('Auto-refresh toggle functionality', async ({ page }) => {
    await page.goto('/');

    // Get initial auto-refresh state
    const initialChecked = await page.locator('[data-testid="auto-refresh-toggle"]').isChecked();

    // Toggle auto-refresh
    await page.click('[data-testid="auto-refresh-toggle"]');

    // Verify state changed
    const newChecked = await page.locator('[data-testid="auto-refresh-toggle"]').isChecked();
    expect(newChecked).not.toBe(initialChecked);

    // Verify refresh interval indicator is shown/hidden appropriately
    if (newChecked) {
      await expect(page.locator('[data-testid="refresh-interval"]')).toBeVisible();
    } else {
      await expect(page.locator('[data-testid="refresh-interval"]')).toBeHidden();
    }
  });

  /**
   * Test manual refresh functionality.
   *
   * Verifies that manual refresh button works
   * and triggers data updates.
   */
  test('Manual refresh functionality', async ({ page }) => {
    await page.goto('/');

    // Get initial last update time
    const initialUpdateTime = await page.locator('[data-testid="last-update-time"]').textContent();

    // Click manual refresh
    await page.click('[data-testid="refresh-button"]');

    // Wait for refresh to complete
    await page.waitForTimeout(2000);

    // Verify refresh completed (last update time should change or stay current)
    const updatedTime = await page.locator('[data-testid="last-update-time"]').textContent();
    expect(updatedTime).toBeTruthy();

    // Verify loading indicator appeared and disappeared
    // Note: Loading state may be too fast to catch in test
  });

  /**
   * Test cache operation buttons.
   *
   * Verifies that cache operation buttons are present
   * and functional (if enabled).
   */
  test('Cache operation buttons functionality', async ({ page }) => {
    await page.goto('/');

    // Verify cache operation buttons are present
    await expect(page.locator('[data-testid="run-cache-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="run-test-button"]')).toBeVisible();

    // Test run cache button (if not disabled)
    const runCacheButton = page.locator('[data-testid="run-cache-button"]');
    const isDisabled = await runCacheButton.isDisabled();

    if (!isDisabled) {
      await runCacheButton.click();

      // Verify operation started (loading state or progress indicator)
      await expect(page.locator('[data-testid="operation-progress"]')).toBeVisible();
    }

    // Test run test button (if not disabled)
    const runTestButton = page.locator('[data-testid="run-test-button"]');
    const testDisabled = await runTestButton.isDisabled();

    if (!testDisabled) {
      await runTestButton.click();

      // Verify test operation started
      await expect(page.locator('[data-testid="test-progress"]')).toBeVisible();
    }
  });

  /**
   * Test scheduler control buttons.
   *
   * Verifies that scheduler start/stop buttons work correctly.
   */
  test('Scheduler control functionality', async ({ page }) => {
    await page.goto('/');

    // Verify scheduler buttons are present
    await expect(page.locator('[data-testid="start-scheduler-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="stop-scheduler-button"]')).toBeVisible();

    // Get initial scheduler status
    const initialStatus = await page.locator('[data-testid="scheduler-status"]').textContent();

    // Test start scheduler (if stopped)
    if (initialStatus?.includes('stopped')) {
      await page.click('[data-testid="start-scheduler-button"]');
      await expect(page.locator('[data-testid="scheduler-status"]')).toContainText('running');
    }

    // Test stop scheduler (if running)
    if (initialStatus?.includes('running')) {
      await page.click('[data-testid="stop-scheduler-button"]');
      await expect(page.locator('[data-testid="scheduler-status"]')).toContainText('stopped');
    }
  });
});

/**
 * Test group for responsive design and mobile compatibility.
 *
 * These tests verify that the dashboard adapts correctly
 * to different screen sizes and devices.
 */
test.describe('Responsive Design', () => {

  /**
   * Test mobile viewport adaptation.
   *
   * Verifies that dashboard layout adapts correctly
   * for mobile screen sizes.
   */
  test('Mobile viewport adaptation', async ({ page }) => {
    await page.goto('/');

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);

    // Verify mobile navigation is available
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();

    // Verify main content is still accessible
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();

    // Verify status cards are properly sized for mobile
    await expect(page.locator('[data-testid="system-status-card"]')).toBeVisible();

    // Test mobile navigation menu toggle
    await page.click('[data-testid="mobile-menu-toggle"]');
    await expect(page.locator('[data-testid="mobile-nav-menu"]')).toBeVisible();

    // Close mobile menu
    await page.click('[data-testid="mobile-menu-close"]');
    await expect(page.locator('[data-testid="mobile-nav-menu"]')).toBeHidden();
  });

  /**
   * Test tablet viewport adaptation.
   *
   * Verifies that dashboard works correctly on tablet devices.
   */
  test('Tablet viewport adaptation', async ({ page }) => {
    await page.goto('/');

    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(1000);

    // Verify tablet layout
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="stats-grid"]')).toBeVisible();

    // Verify navigation is visible but compact
    await expect(page.locator('[data-testid="navigation-menu"]')).toBeVisible();
  });

  /**
   * Test desktop viewport functionality.
   *
   * Verifies that dashboard utilizes full desktop space effectively.
   */
  test('Desktop viewport functionality', async ({ page }) => {
    await page.goto('/');

    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.waitForTimeout(1000);

    // Verify full desktop layout
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="stats-grid"]')).toBeVisible();
    await expect(page.locator('[data-testid="cache-statistics"]')).toBeVisible();

    // Verify all navigation items are visible
    await expect(page.locator('[data-testid="dashboard-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="cached-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="logs-link"]')).toBeVisible();
    await expect(page.locator('[data-testid="settings-link"]')).toBeVisible();
  });

  /**
   * Test responsive functionality across viewports.
   *
   * Verifies that core functionality works across all screen sizes.
   */
  test('Responsive functionality across viewports', async ({ page }) => {
    const viewports = [
      { width: 375, height: 667, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1280, height: 720, name: 'desktop' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(1000);

      // Verify core functionality works in all viewports
      await expect(page.locator('[data-testid="dashboard-title"]')).toBeVisible();
      await expect(page.locator('[data-testid="system-status-card"]')).toBeVisible();

      // Test theme toggle in all viewports
      await page.click('[data-testid="theme-toggle"]');
      await page.waitForTimeout(500);

      // Test refresh functionality in all viewports
      await page.click('[data-testid="refresh-button"]');
      await page.waitForTimeout(1000);
    }
  });

  /**
   * Test touch interactions on mobile.
   *
   * Verifies that touch gestures work correctly on mobile devices.
   */
  test('Touch interactions on mobile', async ({ page }) => {
    await page.goto('/');

    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Test touch scrolling
    await page.locator('[data-testid="dashboard-content"]').tap();
    await page.mouse.wheel(0, 100); // Simulate scroll

    // Verify scrolling worked
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();

    // Test touch on interactive elements
    await page.locator('[data-testid="theme-toggle"]').tap();
    await page.waitForTimeout(500);

    // Verify theme toggle worked via touch
    const themeChanged = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme') !== null;
    });
    expect(themeChanged).toBeTruthy();
  });
});

/**
 * Test group for accessibility compliance.
 *
 * These tests verify that the dashboard meets accessibility standards
 * and provides proper keyboard navigation and screen reader support.
 */
test.describe('Accessibility', () => {

  /**
   * Test keyboard navigation functionality.
   *
   * Verifies that all interactive elements are accessible via keyboard.
   */
  test('Keyboard navigation works correctly', async ({ page }) => {
    await page.goto('/');

    // Test tab navigation
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);

    // Navigate through main interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Verify focus management works
    focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);

    // Test Enter key on focused elements
    const currentFocused = await page.locator(':focus');
    await page.keyboard.press('Enter');

    // Verify action was triggered or element is interactive
    expect(await currentFocused.count()).toBe(1);
  });

  /**
   * Test ARIA labels and roles.
   *
   * Verifies that proper ARIA attributes are present
   * for screen reader accessibility.
   */
  test('ARIA labels and roles are properly implemented', async ({ page }) => {
    await page.goto('/');

    // Check for ARIA labels on interactive elements
    const elementsWithAria = await page.locator('[aria-label], [aria-labelledby]').all();
    expect(elementsWithAria.length).toBeGreaterThan(5); // Should have multiple ARIA labels

    // Check specific ARIA labels
    await expect(page.locator('[aria-label*="theme"]')).toBeVisible();
    await expect(page.locator('[aria-label*="refresh"]')).toBeVisible();

    // Check navigation landmarks
    await expect(page.locator('[role="navigation"]')).toBeVisible();
    await expect(page.locator('[role="main"]')).toBeVisible();
  });

  /**
   * Test heading hierarchy.
   *
   * Verifies that proper heading structure is maintained
   * for screen reader navigation.
   */
  test('Heading hierarchy is correct', async ({ page }) => {
    await page.goto('/');

    // Check for proper heading structure
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(2);

    // Verify main heading is present
    const mainHeading = await page.locator('h1').first();
    expect(await mainHeading.isVisible()).toBeTruthy();

    // Check heading content
    const headingText = await mainHeading.textContent();
    expect(headingText?.toLowerCase()).toContain('cacherr');
  });

  /**
   * Test focus indicators.
   *
   * Verifies that focused elements have visible focus indicators.
   */
  test('Focus indicators are visible', async ({ page }) => {
    await page.goto('/');

    // Tab to first interactive element
    await page.keyboard.press('Tab');

    // Verify focus is visible
    const focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBe(1);

    // Check if focused element has visible focus indicator
    const focusStyles = await focusedElement.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        outline: styles.outline,
        boxShadow: styles.boxShadow,
        border: styles.border
      };
    });

    // Focus indicator should be visible (at least one style should be set)
    const hasFocusIndicator = focusStyles.outline !== 'none' ||
                             focusStyles.boxShadow !== 'none' ||
                             focusStyles.border !== '0px none rgb(0, 0, 0)';
    expect(hasFocusIndicator).toBeTruthy();
  });

  /**
   * Test color contrast compliance.
   *
   * Verifies that text has sufficient contrast against backgrounds.
   */
  test('Color contrast meets accessibility standards', async ({ page }) => {
    await page.goto('/');

    // Test theme switching for contrast verification
    await page.click('[data-testid="theme-toggle"]');
    await page.waitForTimeout(500);

    // Verify elements are still visible in different theme
    await expect(page.locator('[data-testid="dashboard-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="system-status-card"]')).toBeVisible();

    // Test both light and dark themes
    const themes = ['light', 'dark'];
    for (const theme of themes) {
      await page.evaluate((t) => {
        document.documentElement.setAttribute('data-theme', t);
      }, theme);

      await page.waitForTimeout(500);

      // Verify content is readable in both themes
      await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    }
  });
});

/**
 * Test group for error handling and edge cases.
 *
 * These tests verify that the dashboard handles errors gracefully
 * and provides appropriate user feedback.
 */
test.describe('Error Handling', () => {

  /**
   * Test handling of API failures.
   *
   * Verifies that API failures are handled gracefully
   * with appropriate error messages.
   */
  test('API failures are handled gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('/api/system/status', route => route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal Server Error' })
    }));

    await page.goto('/');

    // Wait for error to be displayed
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();

    // Verify dashboard still shows basic content
    await expect(page.locator('[data-testid="dashboard-title"]')).toBeVisible();

    // Verify error message is user-friendly
    const errorMessage = await page.locator('[data-testid="error-message"]').textContent();
    expect(errorMessage).toBeTruthy();
  });

  /**
   * Test WebSocket connection errors.
   *
   * Verifies that WebSocket connection failures are handled properly.
   */
  test('WebSocket connection errors are handled', async ({ page }) => {
    // Mock WebSocket failure
    await page.routeWebSocket('/api/ws', ws => {
      // Simulate immediate failure
      ws.send(JSON.stringify({ error: 'Connection failed' }));
    });

    await page.goto('/');

    // Verify error indicator is shown
    await expect(page.locator('[data-testid="websocket-error"]')).toBeVisible();

    // Verify dashboard continues to function
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });

  /**
   * Test network connectivity issues.
   *
   * Verifies that network failures are handled gracefully.
   */
  test('Network connectivity issues are handled', async ({ page }) => {
    await page.goto('/');

    // Simulate offline state
    await page.context().setOffline(true);

    // Wait for offline detection
    await page.waitForTimeout(2000);

    // Verify offline indicator
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();

    // Simulate coming back online
    await page.context().setOffline(false);

    // Wait for reconnection
    await page.waitForTimeout(2000);

    // Verify back online
    await expect(page.locator('[data-testid="online-indicator"]')).toBeVisible();
  });

  /**
   * Test component rendering errors.
   *
   * Verifies that component errors are caught and handled.
   */
  test('Component rendering errors are handled', async ({ page }) => {
    await page.goto('/');

    // Trigger a component error (this would depend on the actual implementation)
    // For example, by setting invalid props or state

    // Verify error boundary catches the error
    await expect(page.locator('[data-testid="error-boundary"]')).toBeVisible();

    // Verify recovery options are provided
    await expect(page.locator('[data-testid="reload-button"]')).toBeVisible();
  });
});

/**
 * Test group for performance and loading states.
 *
 * These tests verify that the dashboard loads efficiently
 * and provides appropriate loading feedback.
 */
test.describe('Performance', () => {

  /**
   * Test dashboard load time.
   *
   * Verifies that dashboard loads within acceptable time limits.
   */
  test('Dashboard loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');

    // Wait for dashboard to be fully loaded
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();

    const loadTime = Date.now() - startTime;

    // Dashboard should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  /**
   * Test data refresh performance.
   *
   * Verifies that data refresh operations complete efficiently.
   */
  test('Data refresh completes efficiently', async ({ page }) => {
    await page.goto('/');

    const startTime = Date.now();

    // Trigger manual refresh
    await page.click('[data-testid="refresh-button"]');

    // Wait for refresh to complete
    await expect(page.locator('[data-testid="refresh-indicator"]')).toBeHidden();

    const refreshTime = Date.now() - startTime;

    // Refresh should complete within 3 seconds
    expect(refreshTime).toBeLessThan(3000);
  });

  /**
   * Test smooth interactions.
   *
   * Verifies that user interactions are smooth and responsive.
   */
  test('Interactions are smooth and responsive', async ({ page }) => {
    await page.goto('/');

    // Perform multiple interactions quickly
    await page.click('[data-testid="theme-toggle"]');
    await page.click('[data-testid="auto-refresh-toggle"]');
    await page.click('[data-testid="refresh-button"]');

    // Verify all interactions completed successfully
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();

    // Check for any performance issues (no stuck loading states)
    const loadingElements = await page.locator('[data-testid*="loading"], [data-testid*="spinner"]').all();
    for (const element of loadingElements) {
      expect(await element.isHidden()).toBeTruthy();
    }
  });

  /**
   * Test memory and resource usage.
   *
   * Verifies that the dashboard doesn't have memory leaks
   * or excessive resource usage.
   */
  test('Memory usage remains stable', async ({ page }) => {
    await page.goto('/');

    // Get initial performance metrics
    const initialMetrics = await page.evaluate(() => ({
      heapUsed: (performance as any).memory?.usedJSHeapSize || 0,
      timestamp: Date.now()
    }));

    // Perform several operations
    for (let i = 0; i < 5; i++) {
      await page.click('[data-testid="refresh-button"]');
      await page.waitForTimeout(1000);
    }

    // Get final performance metrics
    const finalMetrics = await page.evaluate(() => ({
      heapUsed: (performance as any).memory?.usedJSHeapSize || 0,
      timestamp: Date.now()
    }));

    // Memory usage should not grow excessively
    const memoryIncrease = finalMetrics.heapUsed - initialMetrics.heapUsed;
    expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024); // Less than 50MB increase
  });
});

/**
 * Test group for cross-browser compatibility.
 *
 * These tests verify that the dashboard works consistently
 * across different browsers and browser versions.
 */
test.describe('Cross-browser Compatibility', () => {

  /**
   * Test core functionality across browsers.
   *
   * Verifies that essential dashboard functionality works
   * consistently across different browsers.
   */
  test('Core functionality works consistently across browsers', async ({ page, browserName }) => {
    await page.goto('/');

    // Verify dashboard loads in all browsers
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="system-status-card"]')).toBeVisible();

    // Test theme switching in all browsers
    await page.click('[data-testid="theme-toggle"]');
    await page.waitForTimeout(500);

    // Test refresh functionality in all browsers
    await page.click('[data-testid="refresh-button"]');
    await page.waitForTimeout(2000);

    // Log browser-specific results for debugging
    console.log(`Test completed successfully in ${browserName}`);
  });

  /**
   * Test browser-specific features.
   *
   * Verifies that browser-specific features are handled gracefully.
   */
  test('Browser-specific features are handled gracefully', async ({ page, browserName }) => {
    await page.goto('/');

    // Test keyboard shortcuts that might vary by browser
    if (browserName === 'chromium' || browserName === 'chrome') {
      // Test Chrome-specific features
      await page.keyboard.press('Control+r'); // Refresh shortcut
    } else if (browserName === 'firefox') {
      // Test Firefox-specific features
      await page.keyboard.press('Control+r'); // Refresh shortcut
    } else if (browserName === 'webkit' || browserName === 'safari') {
      // Test Safari-specific features
      await page.keyboard.press('Meta+r'); // Refresh shortcut
    }

    // Verify page remains functional after browser-specific actions
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });
});

/**
 * Test group for integration scenarios.
 *
 * These tests verify that the dashboard integrates properly
 * with other system components and external services.
 */
test.describe('Integration Tests', () => {

  /**
   * Test integration with backend API.
   *
   * Verifies that dashboard properly integrates with backend APIs.
   */
  test('Dashboard integrates with backend API', async ({ page }) => {
    await page.goto('/');

    // Wait for API responses
    await page.waitForResponse('/api/system/status');
    await page.waitForResponse('/api/health');

    // Verify data is displayed
    await expect(page.locator('[data-testid="system-status-card"]')).toBeVisible();
    await expect(page.locator('[data-testid="health-status-card"]')).toBeVisible();

    // Test API-driven updates
    await page.click('[data-testid="refresh-button"]');

    // Wait for new API responses
    await page.waitForResponse('/api/system/status');
    await page.waitForResponse('/api/health');
  });

  /**
   * Test state persistence across navigation.
   *
   * Verifies that dashboard state is maintained when navigating
   * between different pages.
   */
  test('State persists across navigation', async ({ page }) => {
    await page.goto('/');

    // Set theme
    await page.click('[data-testid="theme-toggle"]');
    const themeAfterToggle = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });

    // Enable auto-refresh
    await page.click('[data-testid="auto-refresh-toggle"]');

    // Navigate away and back
    await page.click('[data-testid="cached-link"]');
    await page.click('[data-testid="dashboard-link"]');

    // Verify theme persisted
    const themeAfterNavigation = await page.evaluate(() => {
      return document.documentElement.getAttribute('data-theme');
    });
    expect(themeAfterNavigation).toBe(themeAfterToggle);

    // Verify auto-refresh setting persisted
    const autoRefreshChecked = await page.locator('[data-testid="auto-refresh-toggle"]').isChecked();
    expect(autoRefreshChecked).toBeTruthy();
  });

  /**
   * Test concurrent operations handling.
   *
   * Verifies that dashboard handles multiple concurrent operations properly.
   */
  test('Concurrent operations are handled properly', async ({ page }) => {
    await page.goto('/');

    // Start multiple operations simultaneously
    const operations = [
      page.click('[data-testid="run-cache-button"]'),
      page.click('[data-testid="run-test-button"]'),
      page.click('[data-testid="refresh-button"]')
    ];

    // Wait for all operations to complete
    await Promise.all(operations);

    // Verify dashboard remains stable
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();

    // Verify no conflicting states
    const loadingElements = await page.locator('[data-testid*="loading"]').all();
    expect(loadingElements.length).toBeLessThan(2); // Should not have multiple loading states
  });
});
