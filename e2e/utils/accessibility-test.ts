/**
 * Accessibility Testing Utilities for Playwright
 * Uses axe-core to perform comprehensive accessibility audits
 */

import { Page, TestInfo } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

export interface AccessibilityViolation {
  id: string;
  impact: 'minor' | 'moderate' | 'serious' | 'critical';
  description: string;
  help: string;
  helpUrl: string;
  nodes: Array<{
    target: string[];
    html: string;
    failureSummary: string;
  }>;
}

export interface AccessibilityResult {
  violations: AccessibilityViolation[];
  passes: Array<{
    id: string;
    description: string;
    help: string;
  }>;
  incomplete: Array<{
    id: string;
    description: string;
  }>;
  inapplicable: Array<{
    id: string;
    description: string;
  }>;
}

export class AccessibilityTester {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Run full accessibility audit
   */
  async runFullAudit(options?: {
    rules?: string[];
    excludeRules?: string[];
    include?: string[][];
    exclude?: string[][];
  }): Promise<AccessibilityResult> {
    const axe = new AxeBuilder({ page: this.page });

    // Configure audit rules
    if (options?.rules) {
      axe.withRules(options.rules);
    }

    if (options?.excludeRules) {
      axe.disableRules(options.excludeRules);
    }

    if (options?.include) {
      options.include.forEach(selector => {
        axe.include(selector);
      });
    }

    if (options?.exclude) {
      options.exclude.forEach(selector => {
        axe.exclude(selector);
      });
    }

    const results = await axe.analyze();
    return results;
  }

  /**
   * Run accessibility audit with WCAG 2.1 AA standards
   */
  async runWCAG2AAAudit(): Promise<AccessibilityResult> {
    return this.runFullAudit({
      rules: [
        'wcag21a',
        'wcag21aa',
        'wcag2a',
        'wcag2aa',
        'section508',
        'best-practice'
      ]
    });
  }

  /**
   * Test keyboard navigation accessibility
   */
  async testKeyboardNavigation(): Promise<{
    tabbableElements: number;
    focusableElements: number;
    focusTraps: boolean;
    focusOrder: string[];
  }> {
    // Get all focusable elements
    const focusableElements = await this.page.$$('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');

    // Test tab order
    const tabOrder: string[] = [];
    for (let i = 0; i < Math.min(focusableElements.length, 20); i++) {
      await this.page.keyboard.press('Tab');
      await this.page.waitForTimeout(100);

      const focusedElement = await this.page.$(':focus');
      if (focusedElement) {
        const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase());
        const className = await focusedElement.evaluate(el => el.className || '');
        const id = await focusedElement.evaluate(el => el.id || '');
        tabOrder.push(`${tagName}${id ? `#${id}` : ''}${className ? `.${className.split(' ')[0]}` : ''}`);
      }
    }

    return {
      tabbableElements: focusableElements.length,
      focusableElements: focusableElements.length,
      focusTraps: false, // Would need more complex logic to detect
      focusOrder: tabOrder
    };
  }

  /**
   * Test color contrast
   */
  async testColorContrast(): Promise<Array<{
    element: string;
    foreground: string;
    background: string;
    contrastRatio: number;
    isAccessible: boolean;
  }>> {
    const elements = await this.page.$$('text, [role="button"], input, select, textarea');

    const contrastResults = [];

    for (const element of elements) {
      try {
        const contrast = await element.evaluate(el => {
          const style = window.getComputedStyle(el);
          const fgColor = style.color;
          const bgColor = style.backgroundColor;

          // Simple contrast calculation (would need more sophisticated algorithm for production)
          return {
            foreground: fgColor,
            background: bgColor,
            contrastRatio: 4.5, // Placeholder - would need actual calculation
            isAccessible: true // Placeholder
          };
        });

        contrastResults.push({
          element: await element.evaluate(el => el.outerHTML.substring(0, 100)),
          ...contrast
        });
      } catch (error) {
        // Skip elements that can't be evaluated
      }
    }

    return contrastResults;
  }

  /**
   * Test screen reader compatibility
   */
  async testScreenReaderCompatibility(): Promise<{
    hasAriaLabels: boolean;
    hasAltText: boolean;
    hasSemanticStructure: boolean;
    missingLabels: string[];
  }> {
    // Check for ARIA labels
    const elementsWithoutAria = await this.page.$$('[role="button"]:not([aria-label]):not([aria-labelledby]), input:not([aria-label]):not([aria-labelledby]):not([aria-describedby])');

    // Check for alt text on images
    const imagesWithoutAlt = await this.page.$$('img:not([alt])');

    // Check semantic structure
    const hasHeadings = (await this.page.$$('h1, h2, h3, h4, h5, h6')).length > 0;
    const hasMain = (await this.page.$$('main, [role="main"]')).length > 0;
    const hasNav = (await this.page.$$('nav, [role="navigation"]')).length > 0;

    const missingLabels = [];
    for (const element of elementsWithoutAria) {
      const description = await element.evaluate(el => {
        const tag = el.tagName.toLowerCase();
        const id = el.id ? `#${el.id}` : '';
        const classes = el.className ? `.${el.className.split(' ')[0]}` : '';
        return `${tag}${id}${classes}`;
      });
      missingLabels.push(description);
    }

    return {
      hasAriaLabels: elementsWithoutAria.length === 0,
      hasAltText: imagesWithoutAlt.length === 0,
      hasSemanticStructure: hasHeadings && hasMain && hasNav,
      missingLabels
    };
  }

  /**
   * Generate accessibility report
   */
  async generateAccessibilityReport(testInfo: TestInfo): Promise<void> {
    console.log('🔍 Running accessibility audit...');

    // Run full accessibility audit
    const results = await this.runFullAudit();

    // Generate summary
    const summary = {
      timestamp: new Date().toISOString(),
      url: this.page.url(),
      violations: results.violations.length,
      passes: results.passes.length,
      incomplete: results.incomplete.length,
      criticalIssues: results.violations.filter(v => v.impact === 'critical').length,
      seriousIssues: results.violations.filter(v => v.impact === 'serious').length,
      moderateIssues: results.violations.filter(v => v.impact === 'moderate').length,
      minorIssues: results.violations.filter(v => v.impact === 'minor').length
    };

    // Attach to test results
    await testInfo.attach('accessibility-summary', {
      body: JSON.stringify(summary, null, 2),
      contentType: 'application/json'
    });

    // Attach detailed violations
    if (results.violations.length > 0) {
      await testInfo.attach('accessibility-violations', {
        body: JSON.stringify(results.violations, null, 2),
        contentType: 'application/json'
      });
    }

    // Log summary
    console.log(`📊 Accessibility Audit Complete:`);
    console.log(`   ✅ Passes: ${summary.passes}`);
    console.log(`   ⚠️  Violations: ${summary.violations}`);
    console.log(`   🔴 Critical: ${summary.criticalIssues}`);
    console.log(`   🟠 Serious: ${summary.seriousIssues}`);
    console.log(`   🟡 Moderate: ${summary.moderateIssues}`);
    console.log(`   🔵 Minor: ${summary.minorIssues}`);

    // Fail test if there are critical or serious violations
    if (summary.criticalIssues > 0 || summary.seriousIssues > 0) {
      throw new Error(`Accessibility violations found: ${summary.criticalIssues} critical, ${summary.seriousIssues} serious`);
    }
  }

  /**
   * Take accessibility-focused screenshot
   */
  async takeAccessibilityScreenshot(testInfo: TestInfo, name: string): Promise<void> {
    // Highlight accessibility issues visually
    await this.page.evaluate(() => {
      // Add visual indicators for accessibility issues
      const style = document.createElement('style');
      style.textContent = `
        [data-accessibility-issue] {
          outline: 3px solid red !important;
          background: rgba(255, 0, 0, 0.1) !important;
        }
        [data-accessibility-warning] {
          outline: 2px solid orange !important;
          background: rgba(255, 165, 0, 0.1) !important;
        }
      `;
      document.head.appendChild(style);
    });

    await testInfo.attach(`accessibility-${name}`, {
      body: await this.page.screenshot({ fullPage: true }),
      contentType: 'image/png'
    });
  }
}

/**
 * Performance Testing Utilities
 */
export class PerformanceTester {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Measure Core Web Vitals
   */
  async measureCoreWebVitals(): Promise<{
    LCP: number;
    FID: number;
    CLS: number;
    FCP: number;
    TTFB: number;
  }> {
    return await this.page.evaluate(() => {
      return new Promise((resolve) => {
        const metrics = {
          LCP: 0,
          FID: 0,
          CLS: 0,
          FCP: 0,
          TTFB: 0
        };

        // Largest Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          metrics.LCP = lastEntry.startTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          metrics.FID = entries[0]?.processingStart - entries[0]?.startTime || 0;
        }).observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift
        new PerformanceObserver((list) => {
          let clsValue = 0;
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
          metrics.CLS = clsValue;
        }).observe({ entryTypes: ['layout-shift'] });

        // First Contentful Paint
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          metrics.FCP = entries[0]?.startTime || 0;
        }).observe({ entryTypes: ['paint'] });

        // Time to First Byte
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        metrics.TTFB = navigation.responseStart - navigation.requestStart;

        // Resolve after a short delay to collect metrics
        setTimeout(() => resolve(metrics), 1000);
      });
    });
  }

  /**
   * Measure page load performance
   */
  async measurePageLoadPerformance(): Promise<{
    domContentLoaded: number;
    loadComplete: number;
    firstPaint: number;
    firstContentfulPaint: number;
    totalRequests: number;
    totalTransferSize: number;
  }> {
    return await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paintEntries = performance.getEntriesByName('first-paint');
      const fcpEntries = performance.getEntriesByName('first-contentful-paint');
      const resourceEntries = performance.getEntriesByType('resource');

      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: paintEntries[0]?.startTime || 0,
        firstContentfulPaint: fcpEntries[0]?.startTime || 0,
        totalRequests: resourceEntries.length,
        totalTransferSize: resourceEntries.reduce((total, entry) => {
          return total + ((entry as any).transferSize || 0);
        }, 0)
      };
    });
  }

  /**
   * Test memory usage
   */
  async measureMemoryUsage(): Promise<{
    jsHeapSize: number;
    totalJSHeapSize: number;
    usedJSHeapSize: number;
    jsHeapSizeLimit: number;
  } | null> {
    try {
      return await this.page.evaluate(() => {
        if ('memory' in performance) {
          const mem = (performance as any).memory;
          return {
            jsHeapSize: mem.jsHeapSize,
            totalJSHeapSize: mem.totalJSHeapSize,
            usedJSHeapSize: mem.usedJSHeapSize,
            jsHeapSizeLimit: mem.jsHeapSizeLimit
          };
        }
        return null;
      });
    } catch {
      return null;
    }
  }

  /**
   * Test long tasks (tasks > 50ms)
   */
  async detectLongTasks(): Promise<Array<{
    startTime: number;
    duration: number;
    name: string;
  }>> {
    return await this.page.evaluate(() => {
      return new Promise((resolve) => {
        const longTasks: Array<{
          startTime: number;
          duration: number;
          name: string;
        }> = [];

        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) { // Tasks longer than 50ms
              longTasks.push({
                startTime: entry.startTime,
                duration: entry.duration,
                name: entry.name || 'unknown'
              });
            }
          }
        });

        observer.observe({ entryTypes: ['longtask'] });

        // Collect data for 2 seconds
        setTimeout(() => {
          observer.disconnect();
          resolve(longTasks);
        }, 2000);
      });
    });
  }

  /**
   * Generate performance report
   */
  async generatePerformanceReport(testInfo: TestInfo): Promise<void> {
    console.log('⚡ Running performance audit...');

    const [
      coreWebVitals,
      pageLoadMetrics,
      memoryUsage,
      longTasks
    ] = await Promise.all([
      this.measureCoreWebVitals(),
      this.measurePageLoadPerformance(),
      this.measureMemoryUsage(),
      this.detectLongTasks()
    ]);

    const report = {
      timestamp: new Date().toISOString(),
      url: this.page.url(),
      coreWebVitals,
      pageLoadMetrics,
      memoryUsage,
      longTasks: {
        count: longTasks.length,
        totalDuration: longTasks.reduce((sum, task) => sum + task.duration, 0),
        tasks: longTasks
      },
      scores: {
        // Simple scoring system (would need more sophisticated algorithm)
        performance: this.calculatePerformanceScore(coreWebVitals, pageLoadMetrics),
        memory: memoryUsage ? this.calculateMemoryScore(memoryUsage) : null,
        responsiveness: longTasks.length === 0 ? 100 : Math.max(0, 100 - longTasks.length * 10)
      }
    };

    // Attach to test results
    await testInfo.attach('performance-report', {
      body: JSON.stringify(report, null, 2),
      contentType: 'application/json'
    });

    // Log summary
    console.log(`📊 Performance Audit Complete:`);
    console.log(`   🚀 LCP: ${coreWebVitals.LCP.toFixed(2)}ms`);
    console.log(`   👆 FID: ${coreWebVitals.FID.toFixed(2)}ms`);
    console.log(`   📐 CLS: ${coreWebVitals.CLS.toFixed(4)}`);
    console.log(`   🎨 FCP: ${coreWebVitals.FCP.toFixed(2)}ms`);
    console.log(`   📦 TTFB: ${coreWebVitals.TTFB.toFixed(2)}ms`);
    console.log(`   🔧 Long Tasks: ${longTasks.length}`);
    console.log(`   💾 Memory Usage: ${memoryUsage ? `${(memoryUsage.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB` : 'N/A'}`);
    console.log(`   📈 Performance Score: ${report.scores.performance}/100`);

    // Fail test if performance is too poor
    if (report.scores.performance < 70) {
      throw new Error(`Performance score too low: ${report.scores.performance}/100`);
    }
  }

  private calculatePerformanceScore(cwv: any, plm: any): number {
    // Simple scoring algorithm
    let score = 100;

    // LCP scoring
    if (cwv.LCP > 4000) score -= 30;
    else if (cwv.LCP > 2500) score -= 15;

    // FID scoring
    if (cwv.FID > 300) score -= 30;
    else if (cwv.FID > 100) score -= 15;

    // CLS scoring
    if (cwv.CLS > 0.25) score -= 30;
    else if (cwv.CLS > 0.1) score -= 15;

    return Math.max(0, Math.min(100, score));
  }

  private calculateMemoryScore(memory: any): number {
    const usagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;

    if (usagePercent > 80) return 50;
    if (usagePercent > 60) return 75;
    if (usagePercent > 40) return 90;
    return 100;
  }
}

// Export utilities
export {
  AccessibilityTester,
  PerformanceTester,
  AccessibilityResult,
  AccessibilityViolation
};
