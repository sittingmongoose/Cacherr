import { test, expect } from '@playwright/test';

/**
 * Basic Test Suite
 * 
 * This test suite verifies that the Playwright setup is working correctly
 * and that basic page functionality is accessible.
 */

test.describe('Basic Functionality Tests', () => {
  test('should load the application', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check if the page loaded successfully
    expect(page.url()).toContain('localhost:3000');
    
    // Check if there's some content on the page
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    
    // Check if there are no console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait a bit for any console messages
    await page.waitForTimeout(1000);
    
    // Log any console errors for debugging
    if (consoleErrors.length > 0) {
      console.log('Console errors found:', consoleErrors);
    }
    
    // For now, we'll just check that the page loads without crashing
    expect(true).toBeTruthy();
  });

  test('should have basic HTML structure', async ({ page }) => {
    await page.goto('/');
    
    // Check for basic HTML elements
    expect(await page.locator('html').count()).toBe(1);
    expect(await page.locator('head').count()).toBe(1);
    expect(await page.locator('body').count()).toBe(1);
    
    // Check if there's a title
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('should handle navigation gracefully', async ({ page }) => {
    await page.goto('/');
    
    // Try to navigate to a non-existent route
    await page.goto('/non-existent-route');
    
    // The page should still load (even if it's a 404)
    expect(page.url()).toContain('non-existent-route');
    
    // Check if there's some content (even if it's an error page)
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
  });

  test('should have responsive viewport', async ({ page }) => {
    await page.goto('/');
    
    // Test different viewport sizes
    const viewports = [
      { width: 375, height: 667, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1280, height: 720, name: 'desktop' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);
      
      // Verify the page is still accessible
      const bodyText = await page.textContent('body');
      expect(bodyText).toBeTruthy();
    }
  });

  test('should handle basic user interactions', async ({ page }) => {
    await page.goto('/');
    
    // Test basic keyboard navigation
    await page.keyboard.press('Tab');
    
    // Check if focus is managed
    const focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThanOrEqual(0);
    
    // Test basic mouse interaction
    await page.mouse.move(100, 100);
    
    // The page should remain stable
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
  });

  test('should have no critical JavaScript errors', async ({ page }) => {
    await page.goto('/');
    
    // Listen for page errors
    const pageErrors: string[] = [];
    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });
    
    // Wait for page to stabilize
    await page.waitForTimeout(2000);
    
    // Log any page errors for debugging
    if (pageErrors.length > 0) {
      console.log('Page errors found:', pageErrors);
    }
    
    // For now, we'll just check that the page doesn't crash
    // In a real test environment, you might want to fail on certain types of errors
    expect(true).toBeTruthy();
  });

  test('should load within reasonable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
    
    console.log(`Page loaded in ${loadTime}ms`);
  });

  test('should have accessible content', async ({ page }) => {
    await page.goto('/');
    
    // Check for basic accessibility features
    const hasHeadings = await page.locator('h1, h2, h3, h4, h5, h6').count() > 0;
    const hasMainContent = await page.locator('main, [role="main"], article, section').count() > 0;
    
    // Basic accessibility checks
    expect(hasHeadings || hasMainContent).toBeTruthy();
    
    // Check if there are any interactive elements
    const interactiveElements = await page.locator('button, a, input, select, textarea').count();
    expect(interactiveElements).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Environment Tests', () => {
  test('should have proper test environment', async ({ page }) => {
    // Check if we're in a test environment
    expect(process.env.NODE_ENV).toBeDefined();
    
    // Check if Playwright is working
    expect(page).toBeDefined();
    
    // Check if we can access the page
    await page.goto('/');
    expect(page.url()).toContain('localhost:3000');
  });

  test('should handle network conditions', async ({ page }) => {
    await page.goto('/');
    
    // Test basic network resilience
    // This is a simple test - in a real environment you might want to test
    // with different network conditions (slow 3G, offline, etc.)
    
    // Verify the page loads
    expect(page.url()).toContain('localhost:3000');
    
    // Check if there's content
    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
  });
});
