# End-to-End Testing with Playwright

## Overview

This directory contains comprehensive end-to-end tests for the PlexCacheUltra webgui using Playwright. The tests cover all major user workflows, component interactions, and edge cases to ensure the application works correctly across different browsers and scenarios.

## Test Structure

```
e2e/
├── README.md                    # This documentation
├── fixtures/                    # Test data and fixtures
│   ├── test-data.json          # Mock API responses
│   └── users.json              # Test user scenarios
├── pages/                       # Page Object Models
│   ├── BasePage.ts             # Common page functionality
│   ├── DashboardPage.ts        # Dashboard page interactions
│   ├── CachedPage.ts           # Cached files page
│   └── NavigationPage.ts       # Navigation and routing
├── tests/                       # Test specifications
│   ├── dashboard.spec.ts       # Dashboard functionality tests
│   ├── navigation.spec.ts      # Navigation and routing tests
│   ├── api-integration.spec.ts # API integration tests
│   ├── accessibility.spec.ts   # Accessibility compliance tests
│   ├── responsive.spec.ts      # Responsive design tests
│   └── error-handling.spec.ts  # Error scenarios and recovery
├── utils/                       # Test utilities
│   ├── test-helpers.ts         # Common test functions
│   ├── mock-api.ts             # API mocking utilities
│   └── assertions.ts           # Custom assertions
└── playwright-report/           # Test execution reports
```

## Test Categories

### 1. **Functional Tests**
- Dashboard data display and updates
- Navigation between pages
- Form interactions and validation
- Real-time data updates

### 2. **UI/UX Tests**
- Theme switching (light/dark/auto)
- Responsive design across viewports
- Loading states and animations
- Toast notifications

### 3. **Accessibility Tests**
- Keyboard navigation
- Screen reader compatibility
- ARIA labels and roles
- Color contrast compliance

### 4. **Error Handling Tests**
- Network failures
- API errors
- Invalid data scenarios
- Error boundary recovery

### 5. **Cross-Browser Tests**
- Chromium compatibility
- Firefox compatibility
- WebKit compatibility
- Mobile viewport testing

## Running Tests

### Prerequisites
- Docker and Docker Compose installed
- Development environment running (ports 3000 and 5445)

### Quick Start
```bash
# Run all tests
./run-playwright.sh test

# Run specific test file
./run-playwright.sh test --grep "dashboard"

# Run with UI mode
./run-playwright.sh test-ui

# Run specific browser
./run-playwright.sh test-chrome
```

### Manual Docker Commands
```bash
# Build test image
docker-compose build playwright

# Run all tests
docker-compose run --rm playwright

# Run specific test
docker-compose run --rm playwright npx playwright test dashboard.spec.ts

# Debug mode
docker-compose run --rm playwright npx playwright test --debug
```

## Test Development

### Adding New Tests
1. Create test file in `e2e/tests/`
2. Use existing page objects or create new ones
3. Follow naming convention: `*.spec.ts`
4. Include descriptive test names and proper assertions

### Page Object Model
- **BasePage**: Common functionality (navigation, common elements)
- **Specific Pages**: Page-specific interactions and elements
- **Reusable Components**: Common UI components across pages

### Test Data Management
- Use fixtures for consistent test data
- Mock API responses for predictable testing
- Clean up test data after each test

## Configuration

### Playwright Config
- Located in `playwright.config.js`
- Configured for Docker environment
- Browser-specific launch options
- Parallel test execution

### Environment Variables
- `BASE_URL`: Application base URL (default: http://localhost:3000)
- `API_BASE_URL`: Backend API URL (default: http://localhost:5445)
- `HEADLESS`: Run tests in headless mode (default: true in CI)

## Best Practices

### Test Design
- **Isolation**: Each test should be independent
- **Descriptive Names**: Clear test descriptions
- **Proper Assertions**: Test actual behavior, not implementation
- **Error Handling**: Test both success and failure scenarios

### Performance
- Use `test.describe.parallel()` for parallel execution
- Minimize setup/teardown overhead
- Use appropriate timeouts for async operations

### Maintenance
- Keep page objects up to date with UI changes
- Regular test execution to catch regressions
- Update test data when API responses change

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports 3000 and 5445 are available
2. **Docker Issues**: Check Docker daemon and available resources
3. **Test Failures**: Review test reports and browser console logs
4. **Timing Issues**: Adjust timeouts for slower environments

### Debug Mode
```bash
# Run single test with debug
npx playwright test dashboard.spec.ts --debug

# Run with headed mode
npx playwright test --headed

# Generate trace for failed tests
npx playwright test --trace on
```

## Continuous Integration

### GitHub Actions
- Automated test execution on pull requests
- Parallel test execution across browsers
- Test result reporting and artifacts
- Performance regression detection

### Local Development
- Pre-commit test execution
- Watch mode for development
- Coverage reporting
- Performance benchmarking

## Reporting

### Test Reports
- HTML reports in `playwright-report/`
- Screenshots for failed tests
- Video recordings for debugging
- Trace files for detailed analysis

### Coverage Metrics
- Test execution time
- Browser compatibility results
- Accessibility compliance scores
- Performance benchmarks

## Contributing

When adding new tests:
1. Follow existing patterns and conventions
2. Include proper documentation
3. Ensure tests are reliable and fast
4. Add appropriate error handling
5. Test edge cases and error scenarios

## Support

For issues with the testing framework:
1. Check the Playwright documentation
2. Review existing test examples
3. Check Docker container logs
4. Verify environment configuration
