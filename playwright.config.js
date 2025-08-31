// @ts-check
import { defineConfig, devices } from '@playwright/test';

/**
 * Comprehensive Playwright configuration for Cacherr
 * Supports multiple browsers, responsive design, accessibility testing
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
  workers: process.env.CI ? 4 : Math.min(4, Math.floor(require('os').cpus().length * 0.5)),

  /* Comprehensive reporter configuration */
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ...(process.env.CI ? [['github']] : [])
  ],

  /* Optimized timeouts for comprehensive testing */
  timeout: 30000,
  expect: {
    timeout: 10000,
  },

  /* Global settings for comprehensive testing */
  use: {
    /* Base URL configuration */
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    apiURL: process.env.API_BASE_URL || 'http://localhost:5445',

    /* Optimized timeouts */
    actionTimeout: 10000,
    navigationTimeout: 20000,

    /* Conditional tracing and artifacts */
    trace: process.env.CI ? 'retain-on-failure' : (process.env.TRACE === 'on' ? 'on' : 'off'),
    screenshot: process.env.CI ? 'only-on-failure' : (process.env.SCREENSHOT === 'on' ? 'on' : 'only-on-failure'),
    video: process.env.CI ? 'retain-on-failure' : (process.env.VIDEO === 'on' ? 'on' : 'off'),

    /* Browser optimizations */
    ignoreHTTPSErrors: true,

    /* Global test data */
    testIdAttribute: 'data-testid',
  },

  /* Multi-browser configuration for comprehensive testing */
  projects: [
    // Desktop browsers
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
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor,TranslateUI',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-renderer-backgrounding',
            '--disable-backgrounding-occluded-windows',
          ]
        }
      },
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
      },
    },

    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
      },
    },

    // Mobile browsers for responsive testing
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        launchOptions: {
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
          ]
        }
      },
    },

    {
      name: 'mobile-safari',
      use: {
        ...devices['iPhone 12'],
      },
    },

    // Responsive design testing
    {
      name: 'tablet',
      use: {
        ...devices['iPad Pro'],
        launchOptions: {
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
          ]
        }
      },
    },

    // Accessibility testing (Chrome with axe-core)
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
          ]
        }
      },
    },
  ],

  /* Web server configuration */
  webServer: {
    command: 'cd frontend && npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    gracefulShutdown: {
      signal: 'SIGTERM',
      timeout: 10000,
    },
  },

  /* Test output and artifacts */
  outputDir: './test-results',

  /* Test file filtering */
  testMatch: '**/*.spec.ts',
  testIgnore: ['**/node_modules/**', '**/*.config.*'],

  /* Global setup and teardown */
  globalSetup: require.resolve('./e2e/utils/global-setup.ts'),
  globalTeardown: require.resolve('./e2e/utils/global-teardown.ts'),

  /* Test metadata */
  metadata: {
    project: 'Cacherr',
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'test',
  },
});

