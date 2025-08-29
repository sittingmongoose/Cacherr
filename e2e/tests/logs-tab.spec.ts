import { test, expect } from '@playwright/test';

test.describe('Logs Tab Integration', () => {
  test('should load logs page without errors', async ({ page }) => {
    // Navigate to logs page
    await page.goto('/logs');
    
    // Wait for page to load with increased timeout
    await page.waitForLoadState('domcontentloaded');
    
    // Wait for React to hydrate
    await page.waitForTimeout(2000);
    
    // Check if logs page loaded
    const title = page.locator('h2').filter({ hasText: 'Application Logs' });
    await expect(title).toBeVisible({ timeout: 15000 });
    
    // Check if LogViewer component is present (looking for the main container)
    const logViewer = page.locator('div').filter({ has: page.locator('h2:has-text("Application Logs")') });
    await expect(logViewer).toBeVisible({ timeout: 10000 });
    
    // Check for filter button
    const filterButton = page.locator('button[title="Toggle filters"]');
    await expect(filterButton).toBeVisible({ timeout: 10000 });
    
    // Check for refresh button
    const refreshButton = page.locator('button[title="Refresh logs (Ctrl+R)"]');
    await expect(refreshButton).toBeVisible({ timeout: 10000 });
    
    // Check for export button
    const exportButton = page.locator('button[title="Export logs"]');
    await expect(exportButton).toBeVisible({ timeout: 10000 });
    
    console.log('✅ Logs page loaded successfully with all controls');
  });

  test('should be able to toggle filters', async ({ page }) => {
    await page.goto('/logs');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // Wait for filter button to be visible
    const filterButton = page.locator('button[title="Toggle filters"]');
    await expect(filterButton).toBeVisible({ timeout: 10000 });
    
    // Click filter button
    await filterButton.click();
    await page.waitForTimeout(500);
    
    // Check for search input (should appear when filters are opened)
    const searchInput = page.locator('input[placeholder*="Search logs"]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    
    // Check for log level checkboxes (at least one should exist)
    const levelCheckboxes = page.locator('input[type="checkbox"]');
    await expect(levelCheckboxes.first()).toBeVisible({ timeout: 5000 });
    
    console.log('✅ Log filters functionality works correctly');
  });

  test('should handle page load gracefully', async ({ page }) => {
    await page.goto('/logs');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000); // Give more time for API calls
    
    // Check that the main logs container exists
    const title = page.locator('h2').filter({ hasText: 'Application Logs' });
    await expect(title).toBeVisible({ timeout: 15000 });
    
    // The log container should be present (either with logs or empty state)
    const logSection = page.locator('[role="log"]');
    await expect(logSection).toBeVisible({ timeout: 10000 });
    
    console.log('✅ Log viewer handles page load correctly');
  });

  test('should navigate to logs page correctly', async ({ page }) => {
    // Navigate directly to logs page
    await page.goto('/logs');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // Verify we're on logs page
    expect(page.url()).toContain('/logs');
    
    // Check for logs page content
    const title = page.locator('h2').filter({ hasText: 'Application Logs' });
    await expect(title).toBeVisible({ timeout: 15000 });
    
    console.log('✅ Navigation to logs page works correctly');
  });

  test('should have responsive design', async ({ page }) => {
    await page.goto('/logs');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
    // Wait for title to ensure page is loaded
    const title = page.locator('h2').filter({ hasText: 'Application Logs' });
    await expect(title).toBeVisible({ timeout: 15000 });
    
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await expect(title).toBeVisible({ timeout: 5000 });
    
    // Test mobile view  
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(title).toBeVisible({ timeout: 5000 });
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(title).toBeVisible({ timeout: 5000 });
    
    console.log('✅ Logs page is responsive across different screen sizes');
  });
});