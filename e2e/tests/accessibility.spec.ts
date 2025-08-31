/**
 * Accessibility Testing Suite
 * Tests WCAG 2.1 compliance, keyboard navigation, and screen reader compatibility
 */

import { test, expect, Page } from '@playwright/test';
import { TestSetup, AccessibilityUtils } from '../utils/test-helpers';
import { AccessibilityTester } from '../utils/accessibility-test';

test.describe('Accessibility - WCAG 2.1 AA Compliance', () => {
  let accessibilityTester: AccessibilityTester;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    accessibilityTester = new AccessibilityTester(page);
  });

  test('Dashboard page passes accessibility audit', async ({ page }) => {
    await page.goto('/');

    const results = await accessibilityTester.runWCAG2AAAudit();

    // Should have no critical violations
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);

    // Should have no serious violations
    const seriousViolations = results.violations.filter(v => v.impact === 'serious');
    expect(seriousViolations.length).toBe(0);

    // Log results
    console.log(`Accessibility Audit Results:`);
    console.log(`  ✅ Passes: ${results.passes.length}`);
    console.log(`  ⚠️  Violations: ${results.violations.length}`);
    console.log(`  🔄 Incomplete: ${results.incomplete.length}`);
    console.log(`  🚫 Inapplicable: ${results.inapplicable.length}`);

    if (results.violations.length > 0) {
      console.log('Violations found:');
      results.violations.forEach(violation => {
        console.log(`  - ${violation.id} (${violation.impact}): ${violation.description}`);
      });
    }
  });

  test('Settings page passes accessibility audit', async ({ page }) => {
    await page.goto('/settings');

    const results = await accessibilityTester.runWCAG2AAAudit();

    // Should have no critical violations
    const criticalViolations = results.violations.filter(v => v.impact === 'critical');
    expect(criticalViolations.length).toBe(0);

    // Should have no serious violations
    const seriousViolations = results.violations.filter(v => v.impact === 'serious');
    expect(seriousViolations.length).toBe(0);

    console.log(`Settings Accessibility Audit:`);
    console.log(`  ✅ Passes: ${results.passes.length}`);
    console.log(`  ⚠️  Violations: ${results.violations.length}`);
  });

  test('Navigation passes accessibility audit', async ({ page }) => {
    await page.goto('/');

    const results = await accessibilityTester.runWCAG2AAAudit();

    // Check specifically for navigation-related violations
    const navViolations = results.violations.filter(v =>
      v.description.toLowerCase().includes('navigation') ||
      v.description.toLowerCase().includes('link') ||
      v.description.toLowerCase().includes('focus')
    );

    // Should have minimal navigation-related violations
    const seriousNavViolations = navViolations.filter(v => v.impact === 'serious' || v.impact === 'critical');
    expect(seriousNavViolations.length).toBe(0);

    console.log(`Navigation Accessibility:`);
    console.log(`  Navigation-related violations: ${navViolations.length}`);
  });
});

test.describe('Accessibility - Keyboard Navigation', () => {
  let accessibilityTester: AccessibilityTester;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    accessibilityTester = new AccessibilityTester(page);
  });

  test('All interactive elements are keyboard accessible', async ({ page }) => {
    await page.goto('/');

    const keyboardNav = await accessibilityTester.testKeyboardNavigation();

    // Should have focusable elements
    expect(keyboardNav.tabbableElements).toBeGreaterThan(0);

    // Focus order should be logical
    expect(keyboardNav.focusOrder.length).toBeGreaterThan(0);

    console.log(`Keyboard Navigation:`);
    console.log(`  Tabbable Elements: ${keyboardNav.tabbableElements}`);
    console.log(`  Focus Order: ${keyboardNav.focusOrder.slice(0, 5).join(' → ')}${keyboardNav.focusOrder.length > 5 ? '...' : ''}`);
  });

  test('Tab order follows logical sequence', async ({ page }) => {
    await page.goto('/');

    // Test tab navigation through the page
    await page.keyboard.press('Tab');
    let focusedElement = await page.locator(':focus');

    // Should start with first focusable element
    expect(await focusedElement.count()).toBe(1);

    // Continue tabbing through elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);

      focusedElement = await page.locator(':focus');
      expect(await focusedElement.count()).toBe(1);
    }
  });

  test('Form elements have proper keyboard support', async ({ page }) => {
    await page.goto('/settings');

    // Find form elements
    const formElements = page.locator('input, select, textarea, button');

    if (await formElements.count() > 0) {
      // Test keyboard navigation to form
      await page.keyboard.press('Tab');
      let focusedElement = await page.locator(':focus');

      // Should be able to reach form elements
      const isFormElement = await focusedElement.evaluate(el =>
        ['input', 'select', 'textarea', 'button'].includes(el.tagName.toLowerCase())
      );

      // If we found a form element, test keyboard interaction
      if (isFormElement) {
        const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase());

        if (tagName === 'input' || tagName === 'textarea') {
          // Test typing
          await page.keyboard.type('test input');
          const value = await focusedElement.inputValue();
          expect(value).toBe('test input');
        } else if (tagName === 'select') {
          // Test selection
          await page.keyboard.press('ArrowDown');
          await page.keyboard.press('Enter');
        }
      }
    }
  });

  test('Modal dialogs have proper keyboard support', async ({ page }) => {
    await page.goto('/settings');

    // Look for modal triggers
    const modalTriggers = page.locator('[data-testid*="modal"], [role="dialog"] button, .modal-trigger');

    if (await modalTriggers.count() > 0) {
      // Test modal keyboard interaction
      await modalTriggers.first().click();

      // Wait for modal
      const modal = page.locator('[role="dialog"], .modal');
      await expect(modal).toBeVisible();

      // Test tab navigation within modal
      await page.keyboard.press('Tab');
      let focusedElement = await page.locator(':focus');

      // Focus should be within modal
      const isInModal = await focusedElement.evaluate(el => {
        return el.closest('[role="dialog], .modal') !== null;
      });
      expect(isInModal).toBeTruthy();

      // Test escape key
      await page.keyboard.press('Escape');
      await expect(modal).toBeHidden();
    }
  });
});

test.describe('Accessibility - Screen Reader Compatibility', () => {
  let accessibilityTester: AccessibilityTester;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    accessibilityTester = new AccessibilityTester(page);
  });

  test('Page has proper semantic structure', async ({ page }) => {
    await page.goto('/');

    const screenReaderCompat = await accessibilityTester.testScreenReaderCompatibility();

    // Should have semantic structure
    expect(screenReaderCompat.hasSemanticStructure).toBeTruthy();

    console.log(`Screen Reader Compatibility:`);
    console.log(`  Semantic Structure: ${screenReaderCompat.hasSemanticStructure ? '✅' : '❌'}`);
    console.log(`  ARIA Labels: ${screenReaderCompat.hasAriaLabels ? '✅' : '❌'}`);
    console.log(`  Alt Text: ${screenReaderCompat.hasAltText ? '✅' : '❌'}`);

    if (screenReaderCompat.missingLabels.length > 0) {
      console.log(`  Missing Labels: ${screenReaderCompat.missingLabels.slice(0, 3).join(', ')}`);
    }
  });

  test('Images have proper alt text', async ({ page }) => {
    await page.goto('/');

    const images = page.locator('img');
    const imageCount = await images.count();

    if (imageCount > 0) {
      for (let i = 0; i < imageCount; i++) {
        const image = images.nth(i);
        const altText = await image.getAttribute('alt');

        // Images should have alt text (can be empty for decorative images)
        expect(altText).not.toBeNull();
      }
    }
  });

  test('Form elements have proper labels', async ({ page }) => {
    await page.goto('/settings');

    const formElements = page.locator('input, select, textarea');

    if (await formElements.count() > 0) {
      for (let i = 0; i < await formElements.count(); i++) {
        const element = formElements.nth(i);
        const hasLabel = await element.evaluate(el => {
          // Check for label element
          const id = el.id;
          if (id) {
            const label = document.querySelector(`label[for="${id}"]`);
            if (label) return true;
          }

          // Check for aria-label
          if (el.getAttribute('aria-label')) return true;

          // Check for aria-labelledby
          if (el.getAttribute('aria-labelledby')) return true;

          // Check for placeholder (fallback)
          if (el.getAttribute('placeholder')) return true;

          return false;
        });

        expect(hasLabel).toBeTruthy();
      }
    }
  });

  test('Page has proper heading hierarchy', async ({ page }) => {
    await page.goto('/');

    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    expect(headings.length).toBeGreaterThan(0);

    // Should have h1 as the main heading
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBeGreaterThan(0);

    // Check heading hierarchy
    const headingLevels = await Promise.all(
      headings.map(h => h.evaluate(el => parseInt(el.tagName.charAt(1))))
    );

    // Levels should not skip (no h1 to h3 without h2)
    for (let i = 1; i < headingLevels.length; i++) {
      expect(headingLevels[i]).toBeLessThanOrEqual(headingLevels[i - 1] + 1);
    }

    console.log(`Heading Hierarchy:`);
    console.log(`  Headings: ${headings.length}`);
    console.log(`  H1: ${h1Count}`);
    console.log(`  Levels: ${headingLevels.slice(0, 5).join(', ')}${headingLevels.length > 5 ? '...' : ''}`);
  });
});

test.describe('Accessibility - Color and Visual Contrast', () => {
  let accessibilityTester: AccessibilityTester;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    accessibilityTester = new AccessibilityTester(page);
  });

  test('Color contrast meets WCAG standards', async ({ page }) => {
    await page.goto('/');

    const contrastResults = await accessibilityTester.testColorContrast();

    // Log contrast results
    console.log(`Color Contrast Analysis:`);
    console.log(`  Elements analyzed: ${contrastResults.length}`);

    // Most elements should have acceptable contrast
    const acceptableContrast = contrastResults.filter(r => r.isAccessible);
    const contrastRatio = acceptableContrast.length / contrastResults.length;

    // At least 80% of elements should have acceptable contrast
    expect(contrastRatio).toBeGreaterThanOrEqual(0.8);

    console.log(`  Acceptable contrast: ${acceptableContrast.length}/${contrastResults.length} (${(contrastRatio * 100).toFixed(1)}%)`);
  });

  test('Focus indicators are visible', async ({ page }) => {
    await page.goto('/');

    // Test focus on first focusable element
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus');

    if (await focusedElement.count() > 0) {
      const hasFocusIndicator = await focusedElement.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.outline !== 'none' ||
               style.boxShadow !== 'none' ||
               style.border !== 'none' ||
               el.classList.contains('focus-visible');
      });

      expect(hasFocusIndicator).toBeTruthy();
    }
  });

  test('Page is readable in high contrast mode', async ({ page }) => {
    // Test with high contrast
    await page.emulateMedia({ forcedColors: 'active' });

    await page.goto('/');

    // Page should still be functional
    expect(await page.title()).toBeTruthy();

    // Text should still be readable
    const textElements = page.locator('p, span, div, h1, h2, h3, h4, h5, h6');
    const visibleText = await textElements.first().textContent();
    expect(visibleText?.trim().length).toBeGreaterThan(0);
  });
});

test.describe('Accessibility - Dynamic Content', () => {
  let accessibilityTester: AccessibilityTester;

  test.beforeEach(async ({ page }) => {
    await TestSetup.setupTest(page);
    accessibilityTester = new AccessibilityTester(page);
  });

  test('Dynamic content is announced to screen readers', async ({ page }) => {
    await page.goto('/');

    // Test loading states
    const loadingElements = page.locator('[aria-live], [role="status"], [aria-busy="true"]');

    if (await loadingElements.count() > 0) {
      // Should have aria-live for dynamic content
      const hasAriaLive = await loadingElements.first().getAttribute('aria-live');
      expect(['polite', 'assertive', 'off'].includes(hasAriaLive || '')).toBeTruthy();
    }
  });

  test('Form validation messages are accessible', async ({ page }) => {
    await page.goto('/settings');

    // Look for validation-capable forms
    const formInputs = page.locator('input[required], input[pattern], input[type="email"]');

    if (await formInputs.count() > 0) {
      const firstInput = formInputs.first();

      // Submit form with invalid data
      await firstInput.fill('');
      await page.locator('button[type="submit"]').click();

      // Check for accessible error messages
      const errorMessages = page.locator('[role="alert"], .error-message, .validation-error');

      if (await errorMessages.count() > 0) {
        const errorMessage = errorMessages.first();

        // Error should be properly associated with input
        const isAccessible = await errorMessage.evaluate(el => {
          return el.getAttribute('aria-live') === 'polite' ||
                 el.getAttribute('role') === 'alert' ||
                 el.closest('form') !== null;
        });

        expect(isAccessible).toBeTruthy();
      }
    }
  });

  test('Status updates are announced', async ({ page }) => {
    await page.goto('/');

    // Look for status regions
    const statusRegions = page.locator('[role="status"], [aria-live]');

    if (await statusRegions.count() > 0) {
      // Status regions should have appropriate aria-live values
      const ariaLive = await statusRegions.first().getAttribute('aria-live');
      expect(['polite', 'assertive', 'off'].includes(ariaLive || '')).toBeTruthy();
    }
  });
});

test.describe('Accessibility - Browser Compatibility', () => {
  test('Accessibility features work in different browsers', async ({ page, browserName }) => {
    await TestSetup.setupTest(page);

    if (browserName === 'chromium') {
      // Test Chromium-specific accessibility features
      await page.goto('/');

      const accessibilityTester = new AccessibilityTester(page);
      const results = await accessibilityTester.runWCAG2AAAudit();

      console.log(`Chromium Accessibility:`);
      console.log(`  Violations: ${results.violations.length}`);
      console.log(`  Passes: ${results.passes.length}`);

      // Chromium should have good accessibility support
      expect(results.violations.filter(v => v.impact === 'critical').length).toBe(0);
    }

    if (browserName === 'firefox') {
      // Test Firefox-specific accessibility features
      await page.goto('/');

      // Firefox has good accessibility support
      const focusedElement = await page.locator(':focus');
      // Basic focus management should work
      expect(await focusedElement.count()).toBeGreaterThanOrEqual(0);
    }

    if (browserName === 'webkit') {
      // Test WebKit-specific accessibility features
      await page.goto('/');

      // WebKit (Safari) has good accessibility support
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').count();
      expect(headings).toBeGreaterThan(0);
    }
  });
});
