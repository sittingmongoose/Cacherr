/**
 * Performance Testing Suite
 * Tests application performance, memory usage, and Core Web Vitals
 */

import { test, expect, Page } from '@playwright/test';
import { TestSetup, PerformanceUtils } from '../utils/test-helpers';
import { PerformanceTester } from '../utils/accessibility-test';

test.describe('Performance - Core Web Vitals', () => {
  let performanceTester: PerformanceTester;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    performanceTester = new PerformanceTester(page);
  });

  test('Page loads within acceptable time limits', async ({ page }) => {
    const startTime = Date.now();

    // Navigate to dashboard
    await page.goto('/');

    const loadTime = Date.now() - startTime;

    // Performance budget: 3 seconds for initial load
    expect(loadTime).toBeLessThan(3000);

    console.log(`Initial page load: ${loadTime}ms`);
  });

  test('Core Web Vitals meet acceptable thresholds', async ({ page }) => {
    await page.goto('/');

    // Wait for page to stabilize
    await page.waitForLoadState('networkidle');

    const coreWebVitals = await performanceTester.measureCoreWebVitals();

    // Largest Contentful Paint (LCP) - should be < 2.5s for good UX
    expect(coreWebVitals.LCP).toBeLessThan(2500);

    // First Input Delay (FID) - should be < 100ms for good UX
    expect(coreWebVitals.FID).toBeLessThan(100);

    // Cumulative Layout Shift (CLS) - should be < 0.1 for good UX
    expect(coreWebVitals.CLS).toBeLessThan(0.1);

    // First Contentful Paint (FCP) - should be < 1.8s for good UX
    expect(coreWebVitals.FCP).toBeLessThan(1800);

    console.log('Core Web Vitals:');
    console.log(`  LCP: ${coreWebVitals.LCP.toFixed(2)}ms`);
    console.log(`  FID: ${coreWebVitals.FID.toFixed(2)}ms`);
    console.log(`  CLS: ${coreWebVitals.CLS.toFixed(4)}`);
    console.log(`  FCP: ${coreWebVitals.FCP.toFixed(2)}ms`);
  });

  test('Page load performance metrics are optimal', async ({ page }) => {
    await page.goto('/');

    const loadMetrics = await performanceTester.measurePageLoadPerformance();

    // DOM Content Loaded should be < 1.5s
    expect(loadMetrics.domContentLoaded).toBeLessThan(1500);

    // Load complete should be < 3s
    expect(loadMetrics.loadComplete).toBeLessThan(3000);

    // First Paint should be < 1.5s
    expect(loadMetrics.firstPaint).toBeLessThan(1500);

    // First Contentful Paint should be < 1.8s
    expect(loadMetrics.firstContentfulPaint).toBeLessThan(1800);

    console.log('Load Performance:');
    console.log(`  DOM Content Loaded: ${loadMetrics.domContentLoaded.toFixed(2)}ms`);
    console.log(`  Load Complete: ${loadMetrics.loadComplete.toFixed(2)}ms`);
    console.log(`  First Paint: ${loadMetrics.firstPaint.toFixed(2)}ms`);
    console.log(`  First Contentful Paint: ${loadMetrics.firstContentfulPaint.toFixed(2)}ms`);
    console.log(`  Total Requests: ${loadMetrics.totalRequests}`);
    console.log(`  Total Transfer Size: ${(loadMetrics.totalTransferSize / 1024).toFixed(2)} KB`);
  });

  test('Memory usage remains within acceptable limits', async ({ page }) => {
    await page.goto('/');

    // Perform some interactions to test memory usage
    await page.click('text=Dashboard');
    await page.waitForTimeout(500);
    await page.click('text=Settings');
    await page.waitForTimeout(500);
    await page.click('text=Dashboard');
    await page.waitForTimeout(500);

    const memoryUsage = await performanceTester.measureMemoryUsage();

    if (memoryUsage) {
      // Memory usage should be < 50MB for good performance
      const usedMB = memoryUsage.usedJSHeapSize / 1024 / 1024;
      expect(usedMB).toBeLessThan(50);

      // Heap usage percentage should be < 70%
      const usagePercent = (memoryUsage.usedJSHeapSize / memoryUsage.jsHeapSizeLimit) * 100;
      expect(usagePercent).toBeLessThan(70);

      console.log('Memory Usage:');
      console.log(`  Used: ${usedMB.toFixed(2)} MB`);
      console.log(`  Total: ${(memoryUsage.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Limit: ${(memoryUsage.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Usage: ${usagePercent.toFixed(2)}%`);
    } else {
      console.log('Memory monitoring not available in this browser');
    }
  });

  test('No long-running tasks block the main thread', async ({ page }) => {
    await page.goto('/');

    const longTasks = await performanceTester.detectLongTasks();

    // Should have no long tasks (> 50ms) for good responsiveness
    expect(longTasks.length).toBe(0);

    if (longTasks.length > 0) {
      console.log('Long tasks detected:');
      longTasks.forEach(task => {
        console.log(`  ${task.name}: ${task.duration.toFixed(2)}ms at ${task.startTime.toFixed(2)}ms`);
      });
    }
  });
});

test.describe('Performance - User Interaction Response Times', () => {
  test('Navigation between pages is fast', async ({ page }) => {
    await TestSetup.setupTest(page);
    await page.goto('/');

    // Test navigation to settings
    const settingsStartTime = Date.now();
    await page.click('text=Settings');
    await page.waitForLoadState('networkidle');
    const settingsLoadTime = Date.now() - settingsStartTime;

    // Navigation should be < 1 second
    expect(settingsLoadTime).toBeLessThan(1000);

    // Test navigation back to dashboard
    const dashboardStartTime = Date.now();
    await page.click('text=Dashboard');
    await page.waitForLoadState('networkidle');
    const dashboardLoadTime = Date.now() - dashboardStartTime;

    // Navigation should be < 1 second
    expect(dashboardLoadTime).toBeLessThan(1000);

    console.log(`Navigation Performance:`);
    console.log(`  Dashboard → Settings: ${settingsLoadTime}ms`);
    console.log(`  Settings → Dashboard: ${dashboardLoadTime}ms`);
  });

  test('Form interactions are responsive', async ({ page }) => {
    await TestSetup.setupTest(page);

    // Navigate to settings
    await page.goto('/settings');

    // Test input responsiveness
    const input = page.locator('input[name="plexUrl"]').first();
    if (await input.isVisible()) {
      const inputStartTime = Date.now();
      await input.fill('http://localhost:32400');
      const inputResponseTime = Date.now() - inputStartTime;

      // Input should respond within 100ms
      expect(inputResponseTime).toBeLessThan(100);

      console.log(`Input Response Time: ${inputResponseTime}ms`);
    }
  });

  test('Button clicks are responsive', async ({ page }) => {
    await TestSetup.setupTest(page);
    await page.goto('/settings');

    // Find a button to test
    const button = page.locator('button').first();
    if (await button.isVisible()) {
      const clickStartTime = Date.now();
      await button.click();
      const clickResponseTime = Date.now() - clickStartTime;

      // Button click should respond within 200ms
      expect(clickResponseTime).toBeLessThan(200);

      console.log(`Button Click Response Time: ${clickResponseTime}ms`);
    }
  });
});

test.describe('Performance - Resource Loading', () => {
  test('Critical resources load efficiently', async ({ page }) => {
    const resources: Array<{ url: string; type: string; duration: number }> = [];

    // Monitor resource loading
    page.on('response', response => {
      const url = response.url();
      const resourceType = response.request().resourceType();

      // Only track critical resources
      if (resourceType === 'document' ||
          resourceType === 'script' ||
          resourceType === 'stylesheet' ||
          url.includes('api/')) {

        const timing = response.request().timing;
        if (timing) {
          resources.push({
            url: url.split('/').pop() || url,
            type: resourceType,
            duration: timing.receiveHeadersEnd - timing.sendStart
          });
        }
      }
    });

    await page.goto('/');

    // Wait for all resources to load
    await page.waitForLoadState('networkidle');

    // Analyze critical resource loading times
    const criticalResources = resources.filter(r =>
      r.type === 'document' ||
      r.type === 'script' ||
      r.url.includes('main') ||
      r.url.includes('app')
    );

    console.log('Critical Resource Loading Times:');
    criticalResources.forEach(resource => {
      console.log(`  ${resource.type}: ${resource.url} - ${resource.duration}ms`);

      // Critical resources should load within 2 seconds
      expect(resource.duration).toBeLessThan(2000);
    });

    // Should have reasonable number of critical resources
    expect(criticalResources.length).toBeLessThan(10);
  });

  test('API calls are efficient', async ({ page }) => {
    const apiCalls: Array<{ url: string; duration: number; status: number }> = [];

    // Monitor API calls
    page.on('response', response => {
      const url = response.url();
      if (url.includes('/api/')) {
        const timing = response.request().timing;
        if (timing) {
          apiCalls.push({
            url: url.split('/api/')[1] || url,
            duration: timing.receiveHeadersEnd - timing.sendStart,
            status: response.status()
          });
        }
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    console.log('API Call Performance:');
    apiCalls.forEach(call => {
      console.log(`  ${call.url}: ${call.duration}ms (${call.status})`);

      // API calls should be < 1 second
      expect(call.duration).toBeLessThan(1000);

      // Should return successful status
      expect(call.status).toBeGreaterThanOrEqual(200);
      expect(call.status).toBeLessThan(300);
    });
  });
});

test.describe('Performance - Scalability Tests', () => {
  test('Application handles multiple rapid interactions', async ({ page }) => {
    await TestSetup.setupTest(page);
    await page.goto('/');

    const startTime = Date.now();
    const interactions = 20;

    // Perform multiple rapid interactions
    for (let i = 0; i < interactions; i++) {
      // Navigate between pages rapidly
      if (i % 2 === 0) {
        await page.click('text=Settings');
      } else {
        await page.click('text=Dashboard');
      }
      await page.waitForTimeout(100);
    }

    const totalTime = Date.now() - startTime;
    const averageInteractionTime = totalTime / interactions;

    // Average interaction should be < 500ms
    expect(averageInteractionTime).toBeLessThan(500);

    console.log(`Scalability Test Results:`);
    console.log(`  Total Interactions: ${interactions}`);
    console.log(`  Total Time: ${totalTime}ms`);
    console.log(`  Average Interaction: ${averageInteractionTime.toFixed(2)}ms`);
  });

  test('Memory usage remains stable under load', async ({ page }) => {
    await TestSetup.setupTest(page);
    const performanceTester = new PerformanceTester(page);

    await page.goto('/');

    const initialMemory = await performanceTester.measureMemoryUsage();

    // Perform memory-intensive operations
    for (let i = 0; i < 10; i++) {
      await page.click('text=Settings');
      await page.waitForTimeout(200);
      await page.click('text=Dashboard');
      await page.waitForTimeout(200);
    }

    const finalMemory = await performanceTester.measureMemoryUsage();

    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      const memoryIncreaseMB = memoryIncrease / 1024 / 1024;

      // Memory increase should be < 10MB after heavy usage
      expect(memoryIncreaseMB).toBeLessThan(10);

      console.log(`Memory Stability Test:`);
      console.log(`  Initial Memory: ${(initialMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Final Memory: ${(finalMemory.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Memory Increase: ${memoryIncreaseMB.toFixed(2)} MB`);
    }
  });
});

test.describe('Performance - Browser Comparison', () => {
  test('Performance is consistent across browsers', async ({ page, browserName }) => {
    await TestSetup.setupTest(page);
    const performanceTester = new PerformanceTester(page);

    await page.goto('/');

    const coreWebVitals = await performanceTester.measureCoreWebVitals();
    const loadMetrics = await performanceTester.measurePageLoadPerformance();

    // Log performance by browser for comparison
    console.log(`Browser: ${browserName}`);
    console.log(`  LCP: ${coreWebVitals.LCP.toFixed(2)}ms`);
    console.log(`  FID: ${coreWebVitals.FID.toFixed(2)}ms`);
    console.log(`  CLS: ${coreWebVitals.CLS.toFixed(4)}`);
    console.log(`  Load Time: ${loadMetrics.loadComplete.toFixed(2)}ms`);

    // Basic performance expectations for all browsers
    expect(coreWebVitals.LCP).toBeLessThan(4000); // Reasonable upper bound
    expect(loadMetrics.loadComplete).toBeLessThan(5000); // Reasonable upper bound
  });
});
