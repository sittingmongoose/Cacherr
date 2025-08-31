/**
 * Global teardown for Playwright tests
 * This file runs once after all tests complete
 */

import { FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Running global teardown...');

  // Clean up any test artifacts if needed
  const testResultsDir = path.join(process.cwd(), 'test-results');

  try {
    // Generate test summary
    const summaryPath = path.join(testResultsDir, 'test-summary.json');
    const summary = {
      project: 'Cacherr',
      environment: process.env.NODE_ENV || 'test',
      startTime: process.env.TEST_START_TIME,
      endTime: new Date().toISOString(),
      baseUrl: process.env.BASE_URL || 'http://localhost:3000',
      apiUrl: process.env.API_BASE_URL || 'http://localhost:5445',
    };

    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    console.log('✅ Test summary generated');
  } catch (error) {
    console.warn('⚠️  Could not generate test summary:', error.message);
  }

  console.log('✅ Global teardown completed');
}

export default globalTeardown;
