/**
 * Navigation page object for testing application navigation
 * Extends BasePage with navigation-specific interactions and assertions
 */
import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class NavigationPage extends BasePage {
  // Navigation elements
  readonly navBar: Locator;
  readonly navLinks: Locator;
  readonly mobileMenuButton: Locator;
  readonly mobileMenu: Locator;
  readonly breadcrumb: Locator;

  // Page indicators
  readonly pageTitle: Locator;
  readonly activeNavLink: Locator;
  readonly currentPageIndicator: Locator;

  // Navigation states
  readonly loadingIndicator: Locator;
  readonly errorIndicator: Locator;

  constructor(page: Page) {
    super(page);

    // Navigation elements
    this.navBar = page.locator('nav, [role="navigation"]');
    this.navLinks = page.locator('nav a, [role="navigation"] a');
    this.mobileMenuButton = page.locator('[data-testid="mobile-menu-button"], .mobile-menu-button');
    this.mobileMenu = page.locator('[data-testid="mobile-menu"], .mobile-menu');
    this.breadcrumb = page.locator('[data-testid="breadcrumb"], .breadcrumb');

    // Page indicators
    this.pageTitle = page.locator('h1, [data-testid="page-title"]');
    this.activeNavLink = page.locator('nav a.active, nav a[aria-current="page"]');
    this.currentPageIndicator = page.locator('[data-testid="current-page"], .current-page');

    // Navigation states
    this.loadingIndicator = page.locator('[data-testid="nav-loading"], .nav-loading');
    this.errorIndicator = page.locator('[data-testid="nav-error"], .nav-error');
  }

  /**
   * Get all navigation links
   */
  async getNavigationLinks(): Promise<string[]> {
    await this.waitForVisible(this.navBar);
    const links = await this.navLinks.all();
    const linkTexts: string[] = [];

    for (const link of links) {
      const text = await link.textContent();
      if (text) {
        linkTexts.push(text.trim());
      }
    }

    return linkTexts;
  }

  /**
   * Navigate to page by link text
   */
  async navigateByText(linkText: string) {
    await this.waitForVisible(this.navBar);
    const link = this.navLinks.filter({ hasText: linkText });
    await link.click();
    await this.waitForNavigation();
  }

  /**
   * Navigate to page by href
   */
  async navigateByHref(href: string) {
    await this.waitForVisible(this.navBar);
    const link = this.navLinks.filter({ has: this.page.locator(`[href="${href}"]`) });
    await link.click();
    await this.waitForNavigation();
  }

  /**
   * Test mobile navigation
   */
  async testMobileNavigation() {
    // Set mobile viewport
    await this.page.setViewportSize({ width: 375, height: 667 });

    // Check if mobile menu button exists
    const hasMobileMenu = await this.mobileMenuButton.isVisible();

    if (hasMobileMenu) {
      // Test mobile menu toggle
      await this.mobileMenuButton.click();
      await this.waitForVisible(this.mobileMenu);

      // Test navigation from mobile menu
      const mobileLinks = this.mobileMenu.locator('a');
      const firstLink = mobileLinks.first();
      await firstLink.click();
      await this.waitForNavigation();

      // Close mobile menu
      await this.mobileMenuButton.click();
      await this.waitForHidden(this.mobileMenu);
    }
  }

  /**
   * Test desktop navigation
   */
  async testDesktopNavigation() {
    // Set desktop viewport
    await this.page.setViewportSize({ width: 1280, height: 720 });

    // Verify navigation bar is visible
    expect(await this.isVisible(this.navBar)).toBeTruthy();

    // Test all navigation links
    const links = await this.navLinks.all();

    for (const link of links) {
      const href = await link.getAttribute('href');
      if (href && href !== '#') {
        await link.click();
        await this.waitForNavigation();

        // Verify URL changed
        expect(await this.page.url()).toContain(href);

        // Verify active state
        expect(await this.isVisible(this.activeNavLink)).toBeTruthy();
      }
    }
  }

  /**
   * Test breadcrumb navigation
   */
  async testBreadcrumbNavigation() {
    // Check if breadcrumbs exist
    const hasBreadcrumbs = await this.breadcrumb.isVisible();

    if (hasBreadcrumbs) {
      // Get breadcrumb links
      const breadcrumbLinks = this.breadcrumb.locator('a');
      const linkCount = await breadcrumbLinks.count();

      if (linkCount > 1) {
        // Click second breadcrumb (first is usually home)
        const secondLink = breadcrumbLinks.nth(1);
        const href = await secondLink.getAttribute('href');

        if (href) {
          await secondLink.click();
          await this.waitForNavigation();
          expect(await this.page.url()).toContain(href);
        }
      }
    }
  }

  /**
   * Test keyboard navigation
   */
  async testKeyboardNavigation() {
    await this.waitForVisible(this.navBar);

    // Focus first navigation link
    await this.page.keyboard.press('Tab');
    let focusedElement = await this.page.locator(':focus');

    // Verify focus is on a navigation element
    const isNavElement = await focusedElement.evaluate(el => {
      return el.closest('nav') !== null || el.getAttribute('role') === 'navigation';
    });
    expect(isNavElement).toBeTruthy();

    // Navigate through navigation links
    const navLinks = await this.navLinks.all();

    for (let i = 0; i < Math.min(navLinks.length, 5); i++) {
      await this.page.keyboard.press('Tab');
      await this.page.waitForTimeout(100);
    }

    // Test Enter key activation
    await this.page.keyboard.press('Enter');
    await this.waitForNavigation();
  }

  /**
   * Test navigation accessibility
   */
  async testNavigationAccessibility() {
    await this.waitForVisible(this.navBar);

    // Check navigation role
    const navRole = await this.navBar.getAttribute('role');
    expect(navRole).toBe('navigation');

    // Check ARIA labels
    const navLabel = await this.navBar.getAttribute('aria-label');
    expect(navLabel).toBeTruthy();

    // Check navigation links
    const links = await this.navLinks.all();

    for (const link of links) {
      // Check for accessible name
      const accessibleName = await link.evaluate(el => {
        return el.textContent ||
               el.getAttribute('aria-label') ||
               el.getAttribute('title');
      });
      expect(accessibleName).toBeTruthy();

      // Check href attribute
      const href = await link.getAttribute('href');
      expect(href).toBeTruthy();
      expect(href).not.toBe('#');
    }
  }

  /**
   * Test navigation loading states
   */
  async testNavigationLoadingStates() {
    await this.waitForVisible(this.navBar);

    // Click a navigation link
    const firstLink = this.navLinks.first();
    await firstLink.click();

    // Check for loading indicators
    const hasLoadingIndicator = await this.loadingIndicator.isVisible();

    if (hasLoadingIndicator) {
      // Wait for loading to complete
      await this.waitForHidden(this.loadingIndicator);
    }

    // Verify page loaded successfully
    expect(await this.page.url()).not.toBe('about:blank');
  }

  /**
   * Test navigation error handling
   */
  async testNavigationErrorHandling() {
    // Try to navigate to non-existent page
    await this.page.goto('/non-existent-page');

    // Check for error indicators
    const hasErrorIndicator = await this.errorIndicator.isVisible();

    if (hasErrorIndicator) {
      const errorText = await this.getText(this.errorIndicator);
      expect(errorText).toBeTruthy();
    }

    // Verify navigation still works from error page
    await this.navigateByHref('/');
    expect(await this.page.url()).toContain('/');
  }

  /**
   * Test navigation persistence (active states)
   */
  async testNavigationPersistence() {
    await this.waitForVisible(this.navBar);

    // Navigate to different pages and check active states
    const links = await this.navLinks.all();

    for (const link of links) {
      const href = await link.getAttribute('href');
      if (href && href !== '#') {
        await link.click();
        await this.waitForNavigation();

        // Check active navigation link
        const activeLink = await this.activeNavLink.getAttribute('href');
        expect(activeLink).toBe(href);
      }
    }
  }

  /**
   * Test responsive navigation behavior
   */
  async testResponsiveNavigation() {
    // Test mobile viewport
    await this.page.setViewportSize({ width: 375, height: 667 });
    await this.page.waitForTimeout(500);

    // Test mobile navigation
    await this.testMobileNavigation();

    // Test tablet viewport
    await this.page.setViewportSize({ width: 768, height: 1024 });
    await this.page.waitForTimeout(500);

    // Test hybrid navigation (might show both mobile and desktop)
    const navVisible = await this.isVisible(this.navBar);
    expect(navVisible).toBeTruthy();

    // Test desktop viewport
    await this.page.setViewportSize({ width: 1280, height: 720 });
    await this.page.waitForTimeout(500);

    // Test desktop navigation
    await this.testDesktopNavigation();
  }

  /**
   * Get current page information
   */
  async getCurrentPageInfo() {
    return {
      title: await this.getText(this.pageTitle),
      url: await this.page.url(),
      activeLink: await this.activeNavLink.getAttribute('href'),
      breadcrumb: await this.getText(this.breadcrumb),
    };
  }

  /**
   * Verify navigation state
   */
  async verifyNavigationState(expectedPage: string) {
    // Check URL
    expect(await this.page.url()).toContain(expectedPage);

    // Check active navigation link
    const activeHref = await this.activeNavLink.getAttribute('href');
    expect(activeHref).toContain(expectedPage);

    // Check page title
    const title = await this.getText(this.pageTitle);
    expect(title).toBeTruthy();
  }

  /**
   * Test navigation performance
   */
  async testNavigationPerformance() {
    await this.waitForVisible(this.navBar);

    const links = await this.navLinks.all();
    const performanceResults: { href: string; loadTime: number }[] = [];

    for (const link of links) {
      const href = await link.getAttribute('href');
      if (href && href !== '#') {
        const startTime = Date.now();

        await link.click();
        await this.waitForNavigation();

        const loadTime = Date.now() - startTime;
        performanceResults.push({ href, loadTime });

        // Assert reasonable load time (< 5 seconds)
        expect(loadTime).toBeLessThan(5000);
      }
    }

    // Log performance results
    console.log('Navigation Performance Results:');
    performanceResults.forEach(result => {
      console.log(`${result.href}: ${result.loadTime}ms`);
    });

    return performanceResults;
  }

  /**
   * Comprehensive navigation test
   */
  async runFullNavigationTest() {
    // Test navigation links
    const navLinks = await this.getNavigationLinks();
    expect(navLinks.length).toBeGreaterThan(0);

    // Test desktop navigation
    await this.testDesktopNavigation();

    // Test mobile navigation
    await this.testMobileNavigation();

    // Test breadcrumb navigation
    await this.testBreadcrumbNavigation();

    // Test keyboard navigation
    await this.testKeyboardNavigation();

    // Test accessibility
    await this.testNavigationAccessibility();

    // Test loading states
    await this.testNavigationLoadingStates();

    // Test error handling
    await this.testNavigationErrorHandling();

    // Test persistence
    await this.testNavigationPersistence();

    // Test responsive behavior
    await this.testResponsiveNavigation();

    // Test performance
    await this.testNavigationPerformance();
  }
}
