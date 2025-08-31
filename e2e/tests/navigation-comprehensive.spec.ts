/**
 * Comprehensive Navigation Test Suite
 * Tests all navigation functionality including responsive design, accessibility, and error handling
 */

import { test, expect, Page } from '@playwright/test';
import { NavigationPage } from '../pages/NavigationPage';
import { DashboardPage } from '../pages/DashboardPage';
import { SettingsPage } from '../pages/SettingsPage';
import { TestSetup, TestEnvironment, CustomAssertions } from '../utils/test-helpers';
import { AccessibilityAssertions, UIXAssertions, PerformanceAssertions } from '../utils/custom-assertions';

test.describe('Navigation - Comprehensive Functionality', () => {
  let navigationPage: NavigationPage;
  let dashboardPage: DashboardPage;
  let settingsPage: SettingsPage;

  test.beforeEach(async ({ page }) => {
    // Setup test environment
    await TestSetup.setupTest(page);

    // Initialize page objects
    navigationPage = new NavigationPage(page);
    dashboardPage = new DashboardPage(page);
    settingsPage = new SettingsPage(page);

    // Navigate to dashboard (starting point)
    await dashboardPage.gotoDashboard();
  });

  test.afterEach(async ({ page }) => {
    // Cleanup test environment
    await TestSetup.cleanupTest(page);
  });

  test('Navigation bar loads with all required elements', async ({ page }) => {
    // Verify navigation bar is visible
    await expect(navigationPage.navBar).toBeVisible();

    // Verify navigation links are present
    const navLinks = await navigationPage.getNavigationLinks();
    expect(navLinks.length).toBeGreaterThan(0);

    // Verify essential navigation elements
    expect(navLinks).toContain('Dashboard');
    expect(navLinks).toContain('Cached');
    expect(navLinks).toContain('Settings');
    expect(navLinks).toContain('Logs');
  });

  test('Navigation links work correctly', async ({ page }) => {
    const navLinks = await navigationPage.getNavigationLinks();

    for (const linkText of navLinks) {
      // Navigate by link text
      await navigationPage.navigateByText(linkText);

      // Verify navigation completed
      expect(await navigationPage.isOnPage(linkText.toLowerCase())).toBeTruthy();

      // Verify page title is appropriate
      const pageTitle = await navigationPage.getPageTitle();
      expect(pageTitle).toBeTruthy();

      // Verify active state is correct
      const activeHref = await navigationPage.activeNavLink.getAttribute('href');
      expect(activeHref).toContain(linkText.toLowerCase());
    }
  });

  test('Navigation maintains state correctly', async ({ page }) => {
    // Navigate through different pages
    await navigationPage.goToSettings();
    expect(await navigationPage.isOnPage('settings')).toBeTruthy();

    await navigationPage.goToDashboard();
    expect(await navigationPage.isOnPage('dashboard')).toBeTruthy();

    // Verify navigation state is maintained
    const navState = await navigationPage.getCurrentPageInfo();
    expect(navState.title).toBeTruthy();
    expect(navState.url).toContain('dashboard');
  });

  test('Navigation handles browser back/forward correctly', async ({ page }) => {
    // Navigate to settings
    await navigationPage.goToSettings();
    expect(await navigationPage.isOnPage('settings')).toBeTruthy();

    // Go back
    await navigationPage.goBack();
    expect(await navigationPage.isOnPage('dashboard')).toBeTruthy();

    // Go forward
    await navigationPage.goForward();
    expect(await navigationPage.isOnPage('settings')).toBeTruthy();
  });

  test('Navigation breadcrumb functionality works', async ({ page }) => {
    // Navigate to a page that might have breadcrumbs
    await navigationPage.goToSettings();

    // Check if breadcrumbs exist and work
    if (await navigationPage.breadcrumb.isVisible()) {
      await navigationPage.testBreadcrumbNavigation();
    }
  });

  test('Navigation keyboard accessibility works correctly', async ({ page }) => {
    // Test keyboard navigation
    await navigationPage.testKeyboardNavigation();

    // Verify focus management
    const focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThan(0);
  });

  test('Navigation is fully accessible', async ({ page }) => {
    // Test navigation role
    await AccessibilityAssertions.hasAriaAttributes(page, navigationPage.navBar);

    // Test proper focus management
    await AccessibilityAssertions.hasProperFocus(page, navigationPage.navBar);

    // Test keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThan(0);
  });

  test('Navigation loading states are handled correctly', async ({ page }) => {
    // Navigate and check for loading indicators
    await navigationPage.goToSettings();

    // Check if loading states are properly handled
    await expect(navigationPage.loadingIndicator).toBeHidden({ timeout: 5000 });
  });

  test('Navigation error handling works correctly', async ({ page }) => {
    // Test navigation to non-existent page
    await page.goto('/non-existent-page');

    // Verify error handling
    expect(await navigationPage.isOnPage('non-existent-page')).toBeTruthy();

    // Test navigation still works from error page
    await navigationPage.goToDashboard();
    expect(await navigationPage.isOnPage('dashboard')).toBeTruthy();
  });

  test('Navigation performance meets requirements', async ({ page }) => {
    // Test navigation performance
    const performanceResults = await navigationPage.testNavigationPerformance();

    // Verify reasonable performance
    performanceResults.forEach(result => {
      expect(result.loadTime).toBeLessThan(3000); // 3 second budget
    });
  });
});

test.describe('Navigation - Mobile and Responsive', () => {
  let navigationPage: NavigationPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    navigationPage = new NavigationPage(page);
    await navigationPage.goto('/');
  });

  test('Mobile navigation works correctly', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Test mobile navigation
    await navigationPage.testMobileNavigation();

    // Verify mobile menu functionality
    const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
    if (await mobileMenuButton.isVisible()) {
      await mobileMenuButton.click();

      const mobileMenu = page.locator('[data-testid="mobile-menu"]');
      await expect(mobileMenu).toBeVisible();

      // Test navigation from mobile menu
      const mobileLinks = mobileMenu.locator('a');
      if (await mobileLinks.count() > 0) {
        await mobileLinks.first().click();
        await expect(mobileMenu).toBeHidden();
      }
    }
  });

  test('Tablet navigation works correctly', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    // Test tablet navigation
    await expect(navigationPage.navBar).toBeVisible();

    // Verify navigation links are accessible
    const navLinks = await navigationPage.navLinks.all();
    expect(navLinks.length).toBeGreaterThan(0);

    // Test navigation functionality
    for (const link of navLinks.slice(0, 3)) { // Test first 3 links
      const href = await link.getAttribute('href');
      if (href && href !== '#') {
        await link.click();
        await navigationPage.waitForNavigation();
        expect(await page.url()).toContain(href);
      }
    }
  });

  test('Desktop navigation works correctly', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });

    // Test desktop navigation
    await navigationPage.testDesktopNavigation();

    // Verify all navigation elements are visible
    await expect(navigationPage.navBar).toBeVisible();
    await expect(navigationPage.navLinks.first()).toBeVisible();
  });

  test('Navigation adapts to different screen sizes', async ({ page }) => {
    const viewports = [
      { width: 320, height: 568, name: 'mobile-small' },
      { width: 375, height: 667, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1024, height: 768, name: 'desktop-small' },
      { width: 1280, height: 720, name: 'desktop' },
      { width: 1920, height: 1080, name: 'desktop-large' }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);

      // Verify navigation is always accessible
      await expect(navigationPage.navBar).toBeVisible();

      // Verify no horizontal scroll issues
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBeFalsy();

      // Verify navigation links are accessible
      const visibleLinks = await navigationPage.navLinks.all();
      expect(visibleLinks.length).toBeGreaterThan(0);
    }
  });
});

test.describe('Navigation - Accessibility Compliance', () => {
  let navigationPage: NavigationPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    navigationPage = new NavigationPage(page);
    await navigationPage.goto('/');
  });

  test('Navigation has proper ARIA attributes', async ({ page }) => {
    // Test navigation landmark
    const navRole = await navigationPage.navBar.getAttribute('role');
    expect(navRole).toBe('navigation');

    // Test ARIA labels
    const navLabel = await navigationPage.navBar.getAttribute('aria-label');
    expect(navLabel).toBeTruthy();

    // Test individual navigation links
    const navLinks = await navigationPage.navLinks.all();
    for (const link of navLinks) {
      const accessibleName = await link.evaluate(el => {
        return el.textContent ||
               el.getAttribute('aria-label') ||
               el.getAttribute('title');
      });
      expect(accessibleName?.trim()).toBeTruthy();
    }
  });

  test('Navigation supports keyboard navigation', async ({ page }) => {
    // Test Tab navigation
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus');
    expect(await focusedElement.count()).toBeGreaterThan(0);

    // Test navigation through all links
    const navLinks = await navigationPage.navLinks.all();
    for (let i = 0; i < Math.min(navLinks.length, 5); i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);
    }

    // Verify focus is still within navigation
    focusedElement = await page.locator(':focus');
    const isInNav = await focusedElement.evaluate(el => {
      return el.closest('nav') !== null;
    });
    expect(isInNav).toBeTruthy();
  });

  test('Navigation has proper focus management', async ({ page }) => {
    // Test focus indicators
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus');

    const hasFocusIndicator = await focusedElement.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.outline !== 'none' ||
             styles.boxShadow !== 'none' ||
             styles.border !== 'none';
    });
    expect(hasFocusIndicator).toBeTruthy();
  });

  test('Navigation works with screen readers', async ({ page }) => {
    // Test semantic structure
    const navElement = navigationPage.navBar;
    const tagName = await navElement.evaluate(el => el.tagName.toLowerCase());
    expect(['nav', 'div']).toContain(tagName);

    // Test navigation list structure
    const listElement = page.locator('nav ul, nav ol, [role="navigation"] ul, [role="navigation"] ol');
    if (await listElement.isVisible()) {
      const listItems = listElement.locator('li');
      expect(await listItems.count()).toBeGreaterThan(0);
    }
  });

  test('Navigation handles high contrast mode', async ({ page }) => {
    // Test with forced colors (simulating high contrast mode)
    await page.emulateMedia({ colorScheme: 'dark' });

    // Verify navigation is still visible and functional
    await expect(navigationPage.navBar).toBeVisible();

    // Test navigation links are still readable
    const navLinks = await navigationPage.navLinks.all();
    for (const link of navLinks) {
      const isVisible = await link.isVisible();
      expect(isVisible).toBeTruthy();
    }
  });
});

test.describe('Navigation - Error Handling and Edge Cases', () => {
  let navigationPage: NavigationPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    navigationPage = new NavigationPage(page);
    await navigationPage.goto('/');
  });

  test('Navigation handles network failures gracefully', async ({ page }) => {
    // Mock network failure for navigation
    await page.route('**/api/**', route => route.abort());

    // Try to navigate
    await navigationPage.goToSettings();

    // Verify navigation still works (even with failed API calls)
    expect(await page.url()).toContain('settings');
  });

  test('Navigation handles slow loading pages', async ({ page }) => {
    // Mock slow API responses
    await page.route('**/api/**', async route => {
      await page.waitForTimeout(2000); // 2 second delay
      await route.continue();
    });

    // Navigate and verify timeout handling
    await navigationPage.goToSettings();
    expect(await page.url()).toContain('settings');
  });

  test('Navigation handles invalid URLs', async ({ page }) => {
    // Navigate to invalid URL
    await page.goto('/invalid-path-that-does-not-exist');

    // Verify error handling
    expect(await page.url()).toContain('invalid-path');

    // Verify navigation still works
    await navigationPage.goToDashboard();
    expect(await page.url()).toContain('dashboard');
  });

  test('Navigation handles rapid clicking', async ({ page }) => {
    // Rapidly click navigation links
    const navLinks = await navigationPage.navLinks.all();

    if (navLinks.length > 1) {
      // Click multiple links rapidly
      await navLinks[0].click();
      await navLinks[1].click();
      await navLinks[0].click();

      // Wait for final navigation to complete
      await navigationPage.waitForNavigation();

      // Verify final state is valid
      const currentUrl = await page.url();
      expect(currentUrl).toBeTruthy();
    }
  });

  test('Navigation handles disabled links', async ({ page }) => {
    // Find any disabled navigation links
    const disabledLinks = page.locator('nav a[disabled], nav a[aria-disabled="true"]');

    if (await disabledLinks.count() > 0) {
      // Verify disabled links don't navigate
      const initialUrl = await page.url();
      await disabledLinks.first().click();

      // URL should remain the same
      const finalUrl = await page.url();
      expect(finalUrl).toBe(initialUrl);
    }
  });

  test('Navigation handles external links', async ({ page }) => {
    // Find external links (if any)
    const externalLinks = page.locator('nav a[target="_blank"], nav a[href^="http"]');

    if (await externalLinks.count() > 0) {
      // Verify external links open in new tab
      const link = externalLinks.first();
      const target = await link.getAttribute('target');
      expect(target).toBe('_blank');
    }
  });
});

test.describe('Navigation - Performance and Reliability', () => {
  let navigationPage: NavigationPage;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    navigationPage = new NavigationPage(page);
    await navigationPage.goto('/');
  });

  test('Navigation performance meets requirements', async ({ page }) => {
    const startTime = Date.now();

    // Navigate through all pages
    await navigationPage.goToDashboard();
    await navigationPage.goToSettings();
    await navigationPage.goToCached();
    await navigationPage.goToLogs();
    await navigationPage.goToDashboard();

    const totalTime = Date.now() - startTime;

    // Performance budget: 10 seconds for full navigation cycle
    expect(totalTime).toBeLessThan(10000);

    console.log(`Full navigation cycle time: ${totalTime}ms`);
  });

  test('Navigation handles high-frequency navigation', async ({ page }) => {
    // Perform rapid navigation
    for (let i = 0; i < 20; i++) {
      await navigationPage.goToSettings();
      await navigationPage.goToDashboard();
    }

    // Verify final state is correct
    expect(await navigationPage.isOnPage('dashboard')).toBeTruthy();

    // Verify page is still functional
    await expect(navigationPage.navBar).toBeVisible();
  });

  test('Navigation maintains stability under load', async ({ page }) => {
    // Simulate heavy page interaction
    const actions = [];

    for (let i = 0; i < 10; i++) {
      actions.push(
        navigationPage.goToSettings(),
        page.waitForTimeout(50),
        navigationPage.goToDashboard(),
        page.waitForTimeout(50)
      );
    }

    // Execute all actions
    await Promise.all(actions);

    // Verify navigation is still functional
    expect(await navigationPage.isOnPage('dashboard')).toBeTruthy();
    await expect(navigationPage.navBar).toBeVisible();
  });

  test('Navigation recovers from JavaScript errors', async ({ page }) => {
    // Inject a JavaScript error
    await page.evaluate(() => {
      setTimeout(() => {
        throw new Error('Simulated JavaScript error');
      }, 100);
    });

    // Wait a bit for error to occur
    await page.waitForTimeout(200);

    // Try to navigate
    await navigationPage.goToSettings();

    // Verify navigation still works
    expect(await page.url()).toContain('settings');
  });
});
