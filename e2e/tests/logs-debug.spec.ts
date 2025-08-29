import { test, expect } from '@playwright/test';

test.describe('Logs Debug Tests', () => {
  test('debug page loading', async ({ page }) => {
    console.log('🔍 Starting debug test...');
    
    // Enable browser console logs
    page.on('console', msg => console.log('BROWSER:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
    
    console.log('📍 Navigating to /logs...');
    await page.goto('/logs');
    
    console.log('⏳ Waiting for DOM...');
    await page.waitForLoadState('domcontentloaded');
    
    console.log('📄 Page loaded, checking content...');
    const pageTitle = await page.title();
    console.log('Page title:', pageTitle);
    
    const url = page.url();
    console.log('Current URL:', url);
    
    // Get page HTML to see what's actually there
    const bodyContent = await page.locator('body').innerHTML();
    console.log('Body HTML (first 500 chars):', bodyContent.substring(0, 500));
    
    // Check for any React error boundaries
    const errorBoundary = page.locator('[data-testid="error-boundary"], .error-boundary');
    const hasError = await errorBoundary.count();
    console.log('Error boundaries found:', hasError);
    
    // Look for loading indicators
    const loadingSpinners = page.locator('.loading, .spinner, [data-testid="loading"]');
    const spinnerCount = await loadingSpinners.count();
    console.log('Loading spinners found:', spinnerCount);
    
    // Wait a bit more and check again
    await page.waitForTimeout(5000);
    
    // Try to find any h2 elements
    const h2Elements = page.locator('h2');
    const h2Count = await h2Elements.count();
    console.log('H2 elements found:', h2Count);
    
    for (let i = 0; i < Math.min(h2Count, 3); i++) {
      const text = await h2Elements.nth(i).textContent();
      console.log(`H2 ${i + 1}:`, text);
    }
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'debug-logs-page.png' });
    console.log('📸 Screenshot saved as debug-logs-page.png');
    
    console.log('✅ Debug test completed');
  });
});