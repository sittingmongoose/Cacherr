// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Optimized Playwright configuration for production testing
 * Based on Context7 best practices for efficient test execution
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  /* Run tests in files in parallel for faster execution */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only - fewer retries for faster local development */
  retries: process.env.CI ? 2 : 0,
  /* Use 50% of CPU cores for workers, max 4 for stability */
  workers: process.env.CI ? 2 : Math.min(4, Math.floor(require('os').cpus().length * 0.5)),
  /* Use list reporter for clean output, HTML for detailed reports */
  reporter: process.env.CI ? [['list'], ['html']] : [['list']],
  /* Optimized timeouts for production testing */
  timeout: 20000, // Reduced from 30s for faster feedback
  expect: {
    timeout: 8000, // Reduced from 10s for better performance
  },

  /* Global settings optimized for production testing */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:3000',

    /* Optimized timeouts for production */
    actionTimeout: 10000, // Reduced from 15s
    navigationTimeout: 15000, // Reduced from 15s

    /* Conditional tracing - only on failure in CI for storage efficiency */
    trace: process.env.CI ? 'retain-on-failure' : 'off',

    /* Screenshots and videos only on failure to save storage */
    screenshot: 'only-on-failure',
    video: process.env.CI ? 'retain-on-failure' : 'off',

    /* Additional production optimizations */
    ignoreHTTPSErrors: true,
  },

  /* Single browser configuration for production efficiency */
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process', // Faster startup for tests
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor,TranslateUI',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
            '--disable-client-side-phishing-detection',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-hang-monitor',
            '--disable-ipc-flooding-protection',
            '--disable-popup-blocking',
            '--disable-prompt-on-repost',
            '--no-default-browser-check',
            '--use-mock-keychain',
            '--disable-component-update',
            '--disable-logging',
            '--disable-dev-tools',
          ]
        }
      },
    },
  ],

  /* Optimized web server configuration */
  webServer: {
    command: 'cd frontend && npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60000, // Reduced from 120s for faster startup
    gracefulShutdown: {
      signal: 'SIGTERM',
      timeout: 5000,
    },
  },

  /* Output directory for test artifacts */
  outputDir: './test-results',

  /* Test file filtering for production */
  testMatch: '**/*.spec.ts',
  testIgnore: ['**/node_modules/**', '**/*.config.*'],
});

