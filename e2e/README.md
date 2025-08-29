# End-to-End Testing Suite

This directory contains comprehensive end-to-end tests for the PlexCache web application using Playwright.

## Overview

The test suite validates:
- **API Health**: Backend services and endpoints
- **Frontend Functionality**: React components and user interface
- **Cache Engine**: Initialization and status monitoring
- **Performance**: Load times and responsiveness
- **Cross-browser Compatibility**: Chromium, Firefox, WebKit
- **Responsive Design**: Mobile, tablet, desktop viewports
- **Accessibility**: Basic accessibility compliance

## Quick Start

### Prerequisites

1. **Docker** must be installed and running
2. **Node.js** (for local development, optional)

### Running Tests

#### Using Docker (Recommended)

```bash
# Navigate to project root
cd /workspace

# Run all tests
./run-playwright.sh test

# Run specific test file
./run-playwright.sh test-chrome e2e/tests/api-health-check.spec.ts

# Run with UI mode
./run-playwright.sh test-ui
```

#### Using npm (Local Development)

```bash
# Install dependencies
npm install

# Run tests
npm run test

# Run with UI mode
npm run test:ui

# Run on specific browser
npx playwright test --project=chromium
```

## Test Structure

```
e2e/
├── README.md                    # This documentation
├── run-tests.sh                 # Advanced test runner
├── fixtures/                    # Test data and fixtures
│   └── test-data.json          # Mock API responses
├── pages/                       # Page Object Models
│   ├── BasePage.ts             # Common page functionality
│   └── DashboardPage.ts        # Dashboard-specific interactions
├── tests/                       # Test specifications
│   ├── api-health-check.spec.ts # API endpoint validation
│   └── dashboard.spec.ts        # Dashboard functionality
└── utils/                       # Test utilities
    └── test-helpers.ts          # Common test functions
```

## Test Categories

### 1. API Health Check Tests (`api-health-check.spec.ts`)

**Purpose**: Validate backend API functionality, specifically testing the `/api/status` endpoint that was failing with 500 errors due to cache engine initialization issues.

**Test Cases**:
- **API Endpoint Health**: Ensures `/api/status` returns 200 OK instead of 500
- **Cache Status Validation**: Verifies cache engine is properly initialized
- **WebSocket Health**: Tests real-time connection functionality
- **Dashboard Loading**: Confirms dashboard loads without cache errors
- **Performance**: Validates API response times

### 2. Dashboard Tests (`dashboard.spec.ts`)

**Purpose**: Comprehensive testing of the PlexCache dashboard interface and functionality.

**Test Cases**:
- **Page Loading**: Validates dashboard loads without JavaScript errors
- **Cache Status Display**: Checks for proper cache status information
- **Error Handling**: Tests graceful handling of API failures
- **System Status**: Validates system health indicators
- **Responsive Design**: Tests across different screen sizes
- **Theme Switching**: Tests light/dark theme functionality
- **Navigation**: Validates navigation elements and links

## Configuration

### Playwright Configuration

The `playwright.config.js` file contains:
- **Browser Projects**: Chromium, Firefox, WebKit
- **Base URL**: `http://192.168.50.223:5445`
- **Test Directory**: `./e2e/tests`
- **Timeout Settings**: 60 seconds for long-running tests
- **Screenshot/Video**: Automatic capture on failures

### Test Data

The `fixtures/test-data.json` contains:
- **API Endpoints**: Base URLs and endpoint definitions
- **Expected Responses**: Mock response structures
- **Performance Thresholds**: Acceptable response times
- **UI Selectors**: Common element selectors

## Advanced Test Runner

The `run-tests.sh` script provides advanced testing capabilities:

### Usage

```bash
./run-tests.sh [COMMAND] [OPTIONS]
```

### Commands

- `help` - Show help information
- `test` - Run all tests
- `test-ui` - Run tests with Playwright UI
- `test-chrome` - Run tests only on Chromium
- `test-firefox` - Run tests only on Firefox
- `test-webkit` - Run tests only on WebKit
- `build` - Build the Docker image
- `clean` - Clean up Docker resources
- `shell` - Open a shell in the container
- `install` - Install Playwright browsers
- `report` - Show test report

### Options

- `-b, --browsers` - Specify browsers (all, chrome, firefox, webkit)
- `-w, --workers` - Number of parallel workers
- `-t, --timeout` - Test timeout in milliseconds
- `--trace` - Enable tracing (on, off)
- `--video` - Enable video recording (on, off)
- `-d, --debug` - Run in debug mode

### Examples

```bash
# Run all tests with tracing and video
./run-tests.sh test -b all --trace on --video on

# Run specific test with debug mode
./run-tests.sh test -f dashboard.spec.ts -d

# Run API tests only on Chrome
./run-tests.sh test-chrome -f api-health-check.spec.ts
```

## Page Object Model

The testing framework uses the **Page Object Model** pattern for maintainable tests:

### BasePage (`pages/BasePage.ts`)
Provides common functionality for all pages:
- Navigation methods
- Element interaction helpers
- Error detection utilities
- Screenshot and logging functions

### DashboardPage (`pages/DashboardPage.ts`)
Extends BasePage with dashboard-specific functionality:
- Cache status checking
- System status monitoring
- Theme switching tests
- Responsive design validation

## Test Utilities

### TestHelpers (`utils/test-helpers.ts`)
Comprehensive utility functions:
- **Error Detection**: JavaScript, console, and network errors
- **Performance Monitoring**: API response times and page metrics
- **Accessibility Checking**: Basic accessibility validation
- **Responsive Testing**: Multi-viewport testing utilities

### CustomAssertions (`utils/test-helpers.ts`)
Custom assertion helpers:
- **API Success Validation**: Verify API responses
- **Cache Initialization**: Confirm cache engine status
- **Page Loading**: Validate error-free page loads

## Debugging and Troubleshooting

### Common Issues

1. **Docker Not Running**
   ```bash
   # Check Docker status
   docker info

   # Start Docker service
   sudo systemctl start docker
   ```

2. **Port Conflicts**
   ```bash
   # Check if port 9323 is available
   lsof -i :9323

   # Kill process using the port
   sudo kill -9 <PID>
   ```

3. **Browser Launch Failures**
   ```bash
   # Rebuild Docker image
   ./run-playwright.sh build

   # Check Docker logs
   docker-compose logs playwright
   ```

### Debug Mode

```bash
# Run tests in debug mode
./run-playwright.sh test -d

# Run specific test in debug mode
./run-playwright.sh test -f dashboard.spec.ts -d

# Use Playwright UI for debugging
./run-playwright.sh test-ui
```

### Logs and Reports

```bash
# View test results
ls -la test-results/

# View HTML report
./run-playwright.sh report

# Check browser logs
docker-compose logs playwright
```

## Performance Testing

### Metrics Collected

- **API Response Time**: Target < 1 second
- **Page Load Time**: Target < 5 seconds
- **Cache Operation Time**: Target < 100ms

### Performance Assertions

```typescript
// API performance
expect(responseTime).toBeLessThan(1000); // 1 second

// Page load performance
const metrics = await TestHelpers.getPerformanceMetrics(page);
expect(metrics.totalTime).toBeLessThan(5000); // 5 seconds
```

## Accessibility Testing

### Checks Performed

- **Missing Alt Text**: Images without alt attributes
- **Missing Labels**: Form elements without labels
- **Missing Titles**: Frames without titles
- **Empty Buttons**: Buttons without text or labels

### Accessibility Assertions

```typescript
const issues = await TestHelpers.checkAccessibility(page);
expect(issues.missingAlt).toBe(0);
expect(issues.missingLabels).toBeLessThanOrEqual(2);
```

## Cross-Browser Testing

### Supported Browsers

- **Chromium**: Latest stable version
- **Firefox**: Latest stable version
- **WebKit**: Latest stable version

### Browser-Specific Configuration

```javascript
// Chromium with sandbox disabled for Docker
launchOptions: {
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage'
  ]
}
```

## Continuous Integration

### GitHub Actions Support

The configuration includes CI/CD support:
- Automated test execution on pull requests
- Parallel test execution across browsers
- Test result reporting and artifacts

### Local CI Simulation

```bash
# Run tests in CI mode
CI=true ./run-playwright.sh test

# Run with specific browser for CI
CI=true ./run-playwright.sh test-chrome
```

## Best Practices

### Test Organization

1. **Descriptive Test Names**: Clear, descriptive test names
2. **Independent Tests**: Each test should be self-contained
3. **Proper Assertions**: Test actual behavior, not implementation
4. **Error Handling**: Test both success and failure scenarios

### Page Object Pattern

1. **Separation of Concerns**: UI logic separate from test logic
2. **Reusable Components**: Common functionality in base classes
3. **Maintainable**: Easy to update when UI changes
4. **Readable**: Tests read like user interactions

### Performance Considerations

1. **Parallel Execution**: Use multiple workers for faster execution
2. **Selective Testing**: Run only relevant tests for changes
3. **Caching**: Leverage Docker layer caching
4. **Resource Management**: Clean up resources after tests

## Contributing

### Adding New Tests

1. **Create Page Object**: Extend `BasePage` for new components
2. **Write Test Specifications**: Use descriptive test names and proper assertions
3. **Add Test Data**: Update `fixtures/test-data.json` with mock data
4. **Update Documentation**: Document new test coverage in this README

### Code Standards

1. **TypeScript**: Use TypeScript for type safety
2. **Page Objects**: Follow Page Object Model pattern
3. **Descriptive Names**: Use clear, descriptive names for tests and functions
4. **Error Handling**: Include proper error handling and assertions
5. **Documentation**: Document complex test scenarios

## Support

For issues with the testing framework:

1. Check the [Playwright Documentation](https://playwright.dev/)
2. Review the [Docker Troubleshooting](#debugging-and-troubleshooting)
3. Check the [GitHub Issues](../../issues) for known problems
4. Create a new issue with detailed reproduction steps

## License

This testing framework is part of the PlexCache project and follows the same license terms.