/**
 * Global setup for Playwright tests
 * This file runs once before all tests start
 */

import { chromium, FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting Cacherr Playwright Test Suite...');

  // Create test results directory
  const testResultsDir = path.join(process.cwd(), 'test-results');
  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true });
  }

  // Create playwright-report directory
  const reportDir = path.join(process.cwd(), 'playwright-report');
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }

  // Verify backend is available (optional)
  if (process.env.CI !== 'true') {
    try {
      const browser = await chromium.launch();
      const page = await browser.newPage();

      // Try to connect to backend API
      const apiResponse = await page.request.get(
        process.env.API_BASE_URL || 'http://localhost:5445/api/health'
      );

      if (apiResponse.ok()) {
        console.log('✅ Backend API is available');
      } else {
        console.warn('⚠️  Backend API may not be available');
      }

      await browser.close();
    } catch (error) {
      console.warn('⚠️  Could not verify backend availability:', error.message);
    }
  }

  // Set up environment variables for tests
  process.env.TEST_START_TIME = new Date().toISOString();

  console.log('✅ Global setup completed');
}

export default globalSetup;
