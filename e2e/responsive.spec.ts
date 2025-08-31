/**
 * Responsive Design Test Suite
 *
 * This test suite verifies that the Cacherr application works correctly
 * across different screen sizes and device types including:
 * - Mobile devices (320px - 768px)
 * - Tablet devices (768px - 1024px)
 * - Desktop devices (1024px+)
 * - Navigation behavior on small screens
 * - Touch vs mouse interactions
 * - Layout adaptations and content reflow
 *
 * Uses Playwright's device emulation and viewport capabilities for comprehensive
 * responsive testing coverage.
 */

import { test, expect, devices } from '@playwright/test';
import { DashboardPage } from './pages/DashboardPage';
import { SettingsPage } from './pages/SettingsPage';
import { NavigationPage } from './pages/NavigationPage';

/**
 * Test responsive behavior on mobile devices.
 *
 * These tests verify that the application interface adapts
 * correctly to mobile screen sizes and touch interactions.
 * Uses Playwright's predefined device profiles for accurate emulation.
 */
test.describe('Mobile Responsive Design', () => {

  test('Mobile navigation works correctly', async ({ page }) => {
    // Set mobile viewport using iPhone 12 dimensions
    await page.setViewportSize({ width: 390, height: 844 });
    const navigationPage = new NavigationPage(page);
    await navigationPage.goto('/');

    // Verify mobile navigation is present
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();

    // Test hamburger menu opening
    await page.tap('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-navigation-menu"]')).toBeVisible();

    // Test navigation links work
    await page.tap('[data-testid="mobile-settings-link"]');
    await expect(page).toHaveURL(/.*\/settings/);

    // Verify settings page is mobile-friendly
    const settingsPage = new SettingsPage(page);
    await expect(settingsPage.settingsContainer).toBeVisible();

    // Test form inputs are touch-friendly on mobile
    const urlInput = page.locator('[data-testid="plex-url-input"]');
    await expect(urlInput).toHaveCSS('min-height', /44px|48px/); // iOS touch target size
  });

  test('Dashboard layout adapts to mobile screen', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Verify dashboard container uses full width on mobile
    const dashboard = page.locator('[data-testid="dashboard-container"]');
    await expect(dashboard).toHaveCSS('width', /100%|calc\(/);

    // Test tab navigation on mobile - should be scrollable if needed
    const tabContainer = page.locator('[data-testid="tab-container"]');
    if (await tabContainer.isVisible()) {
      // Test horizontal scrolling if tabs overflow
      const isScrollable = await tabContainer.evaluate(el =>
        el.scrollWidth > el.clientWidth
      );

      if (isScrollable) {
        // Test horizontal scrolling works
        await tabContainer.evaluate(el => el.scrollLeft = 100);
        const scrollPos = await tabContainer.evaluate(el => el.scrollLeft);
        expect(scrollPos).toBeGreaterThan(0);
      }
    }

    // Verify no horizontal scroll at body level
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    expect(hasHorizontalScroll).toBeFalsy();
  });

  test('Settings form adapts to mobile layout', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Verify settings sections stack vertically on mobile
    const settingsSections = page.locator('[data-testid="settings-section"]');
    const sectionsCount = await settingsSections.count();

    // On mobile, sections should be in a single column
    for (let i = 0; i < sectionsCount; i++) {
      const section = settingsSections.nth(i);
      await expect(section).toBeVisible();

      // Verify section takes full width on mobile
      await expect(section).toHaveCSS('width', /100%|calc\(/);
    }

    // Test collapsible sections work on touch
    const firstSection = settingsSections.first();
    const sectionToggle = firstSection.locator('[data-testid="section-toggle"]').first();

    if (await sectionToggle.isVisible()) {
      await sectionToggle.tap();
      await page.waitForTimeout(200); // Allow animation to complete

      // Verify section content visibility toggles
      const sectionContent = firstSection.locator('[data-testid="section-content"]');
      await expect(sectionContent).toBeVisible();
    }
  });

  test('Touch interactions work correctly on mobile', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Test touch scrolling
    await page.touchscreen.tap(200, 200);
    await page.waitForTimeout(100);

    // Test touch on interactive elements
    const refreshButton = page.locator('[data-testid="refresh-button"]');
    if (await refreshButton.isVisible()) {
      await refreshButton.tap();
      await page.waitForTimeout(100);

      // Verify touch interaction worked
      await expect(dashboardPage.dashboardContainer).toBeVisible();
    }

    // Test swipe gestures if applicable
    const scrollableArea = page.locator('[data-testid="dashboard-container"]');
    if (await scrollableArea.isVisible()) {
      // Simulate vertical swipe
      await scrollableArea.evaluate(el => {
        el.scrollTop = 100;
      });
      const scrollPos = await scrollableArea.evaluate(el => el.scrollTop);
      expect(scrollPos).toBeGreaterThan(0);
    }
  });
});

/**
 * Test responsive behavior on tablet devices.
 *
 * Verifies intermediate screen size behavior and layout adaptations
 * for tablet-sized screens.
 */
test.describe('Tablet Responsive Design', () => {

  test('Tablet layout shows appropriate navigation', async ({ page }) => {
    // Set tablet viewport using iPad dimensions
    await page.setViewportSize({ width: 768, height: 1024 });
    const navigationPage = new NavigationPage(page);
    await navigationPage.goto('/');

    // Verify tablet navigation layout - should show full navigation without hamburger
    await expect(page.locator('[data-testid="desktop-navigation"]')).toBeVisible();
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeHidden();

    // Test navigation links work
    const settingsLink = page.locator('[data-testid="settings-link"]');
    if (await settingsLink.isVisible()) {
      await settingsLink.click();
      await expect(page).toHaveURL(/.*\/settings/);
    }
  });

  test('Settings page layout adapts to tablet', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Verify settings sections layout for tablet - may use 2-column layout
    const settingsSections = page.locator('[data-testid="settings-section"]');
    const sectionsCount = await settingsSections.count();

    // On tablet, sections might be in 2-column layout or optimized spacing
    for (let i = 0; i < sectionsCount; i++) {
      const section = settingsSections.nth(i);
      await expect(section).toBeVisible();

      // Verify section has appropriate spacing for tablet
      const margin = await section.evaluate(el => {
        const styles = window.getComputedStyle(el);
        return parseFloat(styles.marginBottom || '0');
      });
      expect(margin).toBeGreaterThanOrEqual(16); // Appropriate spacing
    }
  });

  test('Dashboard layout optimizes for tablet screen', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Verify dashboard uses appropriate grid layout for tablet
    const statusCards = page.locator('[data-testid="status-card"]');
    const cardsCount = await statusCards.count();

    if (cardsCount > 0) {
      // Verify cards are appropriately sized for tablet
      const firstCard = statusCards.first();
      const boundingBox = await firstCard.boundingBox();
      expect(boundingBox?.width).toBeGreaterThan(200); // Reasonable width for tablet
      expect(boundingBox?.height).toBeGreaterThan(100); // Reasonable height for tablet
    }

    // Test tablet-specific interactions
    const statsGrid = page.locator('[data-testid="stats-grid"]');
    if (await statsGrid.isVisible()) {
      // Verify grid layout works well on tablet
      const gridItems = statsGrid.locator('[data-testid="stat-item"]');
      const itemCount = await gridItems.count();
      expect(itemCount).toBeGreaterThan(0);
    }
  });
});

/**
 * Test responsive behavior on desktop devices.
 *
 * Verifies large screen optimizations and full feature access
 * for desktop-sized screens.
 */
test.describe('Desktop Responsive Design', () => {

  test('Desktop layout maximizes screen real estate', async ({ page }) => {
    // Set desktop viewport using standard desktop dimensions
    await page.setViewportSize({ width: 1920, height: 1080 });
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Verify dashboard uses full desktop layout
    const dashboard = page.locator('[data-testid="dashboard-container"]');
    const viewportSize = page.viewportSize();
    const dashboardWidth = await dashboard.evaluate(el => el.clientWidth);

    // Dashboard should use significant portion of desktop width
    expect(dashboardWidth).toBeGreaterThan(viewportSize!.width * 0.8);

    // Verify multi-column layouts are used
    const statusCards = page.locator('[data-testid="status-card"]');
    const cardsCount = await statusCards.count();

    if (cardsCount > 1) {
      // Cards should be arranged in multiple columns on desktop
      const firstCard = statusCards.first();
      const secondCard = statusCards.nth(1);

      const firstRect = await firstCard.boundingBox();
      const secondRect = await secondCard.boundingBox();

      // Verify cards are side-by-side (multi-column layout)
      if (firstRect && secondRect) {
        expect(Math.abs(firstRect.y - secondRect.y)).toBeLessThan(50); // Same row
      }
    }
  });

  test('Settings page uses full desktop layout', async ({ page }) => {
    const settingsPage = new SettingsPage(page);
    await settingsPage.gotoSettings();

    // Verify all settings sections are visible simultaneously
    const settingsSections = page.locator('[data-testid="settings-section"]');
    const visibleSections = await settingsSections.locator(':visible').count();
    const totalSections = await settingsSections.count();

    expect(visibleSections).toBe(totalSections); // All sections should be visible on desktop

    // Verify sections use multi-column layout effectively
    const mainContainer = page.locator('[data-testid="settings-main"]');
    const containerWidth = await mainContainer.evaluate(el => el.clientWidth);
    expect(containerWidth).toBeGreaterThan(800); // Sufficient width for multi-column layout
  });

  test('Navigation uses full desktop navigation', async ({ page }) => {
    const navigationPage = new NavigationPage(page);
    await navigationPage.goto('/');

    // Verify full navigation is visible
    await expect(page.locator('[data-testid="desktop-navigation"]')).toBeVisible();
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeHidden();

    // Test all navigation links are accessible
    const navLinks = page.locator('[data-testid="nav-link"]');
    const linkCount = await navLinks.count();

    for (let i = 0; i < linkCount; i++) {
      const link = navLinks.nth(i);
      await expect(link).toBeVisible();
      await expect(link).toHaveCSS('cursor', 'pointer');
    }
  });
});

/**
 * Test cross-device compatibility and adaptive behaviors.
 *
 * Verifies that the application adapts correctly when switching
 * between different screen sizes and device types.
 */
test.describe('Cross-Device Compatibility', () => {

  test('Application adapts when viewport changes dynamically', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Start with mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="desktop-navigation"]')).toBeHidden();

    // Switch to tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    // Verify tablet layout
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeHidden();
    await expect(page.locator('[data-testid="desktop-navigation"]')).toBeVisible();

    // Switch to desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });

    // Verify desktop layout
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeHidden();
    await expect(page.locator('[data-testid="desktop-navigation"]')).toBeVisible();

    // Verify dashboard remains functional throughout
    await expect(dashboardPage.dashboardContainer).toBeVisible();
  });

  test('High DPI displays render correctly', async ({ page }) => {
    // Set high DPI viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.evaluate(() => {
      // Simulate high DPI display
      Object.defineProperty(window, 'devicePixelRatio', { value: 2 });
    });

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Verify high DPI rendering
    await expect(dashboardPage.dashboardContainer).toBeVisible();

    // Check that elements scale properly for high DPI
    const statusCard = page.locator('[data-testid="status-card"]').first();
    if (await statusCard.isVisible()) {
      const boundingBox = await statusCard.boundingBox();
      expect(boundingBox?.width).toBeGreaterThan(200); // Should be reasonably sized for high DPI
      expect(boundingBox?.height).toBeGreaterThan(100); // Should be reasonably sized for high DPI
    }
  });

  test('Orientation changes are handled correctly', async ({ page }) => {
    // Start in portrait mode (mobile)
    await page.setViewportSize({ width: 375, height: 667 });

    const dashboardPage = new DashboardPage(page);
    await dashboardPage.gotoDashboard();

    // Verify portrait layout
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible();

    // Simulate landscape mode
    await page.setViewportSize({ width: 667, height: 375 });

    // Verify landscape layout adapts
    await expect(dashboardPage.dashboardContainer).toBeVisible();

    // Content should still be accessible in landscape
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    expect(hasHorizontalScroll).toBeFalsy();
  });
});
