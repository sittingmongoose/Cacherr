#!/usr/bin/env node

/**
 * Comprehensive Test Report Generator for Cacherr
 * Generates detailed HTML reports, coverage analysis, and CI/CD metrics
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TestReportGenerator {
  constructor() {
    this.testResultsDir = path.join(process.cwd(), 'test-results');
    this.reportDir = path.join(process.cwd(), 'playwright-report');
    this.outputDir = path.join(process.cwd(), 'test-reports');
  }

  async generateReport() {
    console.log('📊 Generating comprehensive test report...');

    // Ensure output directory exists
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }

    // Collect all test data
    const testData = await this.collectTestData();

    // Generate different report types
    await this.generateHTMLReport(testData);
    await this.generateJSONReport(testData);
    await this.generateMarkdownReport(testData);
    await this.generateCoverageReport(testData);
    await this.generatePerformanceReport(testData);

    console.log('✅ Test reports generated successfully!');
    console.log(`📁 Reports available in: ${this.outputDir}`);
  }

  async collectTestData() {
    const testData = {
      summary: {
        timestamp: new Date().toISOString(),
        duration: 0,
        total: 0,
        passed: 0,
        failed: 0,
        skipped: 0,
        flaky: 0
      },
      browsers: {},
      tests: [],
      errors: [],
      performance: {
        averageLoadTime: 0,
        slowestTest: null,
        fastestTest: null,
        memoryUsage: null
      },
      coverage: {
        statements: 0,
        branches: 0,
        functions: 0,
        lines: 0
      }
    };

    // Read Playwright results
    if (fs.existsSync(this.testResultsDir)) {
      const resultFiles = fs.readdirSync(this.testResultsDir)
        .filter(file => file.endsWith('.json'));

      for (const file of resultFiles) {
        const filePath = path.join(this.testResultsDir, file);
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

        // Aggregate summary data
        testData.summary.total += data.suites?.length || 0;
        testData.summary.passed += data.passed || 0;
        testData.summary.failed += data.failed || 0;
        testData.summary.skipped += data.skipped || 0;
        testData.summary.duration += data.duration || 0;

        // Collect browser-specific data
        const browser = file.replace('results-', '').replace('.json', '');
        testData.browsers[browser] = {
          passed: data.passed || 0,
          failed: data.failed || 0,
          skipped: data.skipped || 0,
          duration: data.duration || 0
        };

        // Collect individual test results
        if (data.suites) {
          for (const suite of data.suites) {
            if (suite.specs) {
              for (const spec of suite.specs) {
                if (spec.tests) {
                  for (const test of spec.tests) {
                    testData.tests.push({
                      title: test.title,
                      file: spec.file,
                      status: test.results[0]?.status || 'unknown',
                      duration: test.results[0]?.duration || 0,
                      error: test.results[0]?.error?.message || null,
                      browser: browser
                    });

                    if (test.results[0]?.error) {
                      testData.errors.push({
                        test: test.title,
                        file: spec.file,
                        error: test.results[0].error.message,
                        browser: browser
                      });
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    // Calculate performance metrics
    if (testData.tests.length > 0) {
      const durations = testData.tests.map(t => t.duration);
      testData.performance.slowestTest = testData.tests.reduce((max, test) =>
        test.duration > max.duration ? test : max
      );
      testData.performance.fastestTest = testData.tests.reduce((min, test) =>
        test.duration < min.duration ? test : min
      );
      testData.performance.averageLoadTime = durations.reduce((a, b) => a + b, 0) / durations.length;
    }

    return testData;
  }

  async generateHTMLReport(testData) {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cacherr Test Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h3 { color: #667eea; margin-bottom: 15px; }
        .metric { font-size: 2em; font-weight: bold; }
        .metric.success { color: #28a745; }
        .metric.danger { color: #dc3545; }
        .metric.warning { color: #ffc107; }
        .metric.info { color: #17a2b8; }
        .tests { margin-bottom: 30px; }
        .test-item { background: white; margin-bottom: 10px; padding: 15px; border-radius: 5px; border-left: 4px solid; }
        .test-item.passed { border-left-color: #28a745; }
        .test-item.failed { border-left-color: #dc3545; }
        .test-item.skipped { border-left-color: #ffc107; }
        .browser-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .error-list { background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .performance-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 Cacherr Test Report</h1>
            <p>Generated on ${new Date(testData.summary.timestamp).toLocaleString()}</p>
            <p>Total Duration: ${(testData.summary.duration / 1000).toFixed(2)}s</p>
        </div>

        <div class="summary">
            <div class="card">
                <h3>📊 Total Tests</h3>
                <div class="metric">${testData.summary.total}</div>
            </div>
            <div class="card">
                <h3>✅ Passed</h3>
                <div class="metric success">${testData.summary.passed}</div>
            </div>
            <div class="card">
                <h3>❌ Failed</h3>
                <div class="metric danger">${testData.summary.failed}</div>
            </div>
            <div class="card">
                <h3>⏭️ Skipped</h3>
                <div class="metric warning">${testData.summary.skipped}</div>
            </div>
        </div>

        <div class="browser-grid">
            ${Object.entries(testData.browsers).map(([browser, stats]) => `
                <div class="card">
                    <h3>🌐 ${browser.charAt(0).toUpperCase() + browser.slice(1)}</h3>
                    <p>✅ Passed: ${stats.passed}</p>
                    <p>❌ Failed: ${stats.failed}</p>
                    <p>⏭️ Skipped: ${stats.skipped}</p>
                    <p>⏱️ Duration: ${(stats.duration / 1000).toFixed(2)}s</p>
                </div>
            `).join('')}
        </div>

        ${testData.errors.length > 0 ? `
            <div class="error-list">
                <h3>🚨 Test Failures</h3>
                ${testData.errors.map(error => `
                    <div class="test-item failed">
                        <strong>${error.test}</strong><br>
                        <small>${error.file} (${error.browser})</small><br>
                        <code>${error.error}</code>
                    </div>
                `).join('')}
            </div>
        ` : ''}

        <div class="performance-metrics">
            <div class="card">
                <h3>⚡ Performance</h3>
                <p>Average Load Time: ${testData.performance.averageLoadTime.toFixed(2)}ms</p>
                ${testData.performance.slowestTest ? `
                    <p>Slowest Test: ${testData.performance.slowestTest.title} (${testData.performance.slowestTest.duration}ms)</p>
                ` : ''}
                ${testData.performance.fastestTest ? `
                    <p>Fastest Test: ${testData.performance.fastestTest.title} (${testData.performance.fastestTest.duration}ms)</p>
                ` : ''}
            </div>
        </div>

        <div class="tests">
            <h2>🧪 Test Results</h2>
            ${testData.tests.map(test => `
                <div class="test-item ${test.status}">
                    <strong>${test.title}</strong>
                    <br><small>${test.file} (${test.browser}) - ${test.duration}ms</small>
                    ${test.error ? `<br><code style="color: #dc3545;">${test.error}</code>` : ''}
                </div>
            `).join('')}
        </div>
    </div>
</body>
</html>`;

    fs.writeFileSync(path.join(this.outputDir, 'test-report.html'), html);
  }

  async generateJSONReport(testData) {
    fs.writeFileSync(
      path.join(this.outputDir, 'test-report.json'),
      JSON.stringify(testData, null, 2)
    );
  }

  async generateMarkdownReport(testData) {
    const markdown = `# 🎭 Cacherr Test Report

Generated on: ${new Date(testData.summary.timestamp).toLocaleString()}
Total Duration: ${(testData.summary.duration / 1000).toFixed(2)}s

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total Tests | ${testData.summary.total} |
| Passed | ${testData.summary.passed} ✅ |
| Failed | ${testData.summary.failed} ❌ |
| Skipped | ${testData.summary.skipped} ⏭️ |

## 🌐 Browser Results

${Object.entries(testData.browsers).map(([browser, stats]) => `
### ${browser.charAt(0).toUpperCase() + browser.slice(1)}
- ✅ Passed: ${stats.passed}
- ❌ Failed: ${stats.failed}
- ⏭️ Skipped: ${stats.skipped}
- ⏱️ Duration: ${(stats.duration / 1000).toFixed(2)}s
`).join('')}

## ⚡ Performance Metrics

- Average Load Time: ${testData.performance.averageLoadTime.toFixed(2)}ms
${testData.performance.slowestTest ?
  `- Slowest Test: ${testData.performance.slowestTest.title} (${testData.performance.slowestTest.duration}ms)` : ''}
${testData.performance.fastestTest ?
  `- Fastest Test: ${testData.performance.fastestTest.title} (${testData.performance.fastestTest.duration}ms)` : ''}

${testData.errors.length > 0 ? `
## 🚨 Failures

${testData.errors.map(error => `
### ${error.test}
**File:** ${error.file}  
**Browser:** ${error.browser}  
**Error:** ${error.error}
`).join('')}

` : ''}

## 🧪 Test Details

${testData.tests.map(test => `
### ${test.status === 'passed' ? '✅' : test.status === 'failed' ? '❌' : '⏭️'} ${test.title}
- **File:** ${test.file}
- **Browser:** ${test.browser}
- **Duration:** ${test.duration}ms
${test.error ? `- **Error:** ${test.error}` : ''}
`).join('')}

---
*Report generated by Cacherr Test Suite*
`;

    fs.writeFileSync(path.join(this.outputDir, 'test-report.md'), markdown);
  }

  async generateCoverageReport(testData) {
    // This would integrate with coverage tools like istanbul or nyc
    const coverage = {
      timestamp: new Date().toISOString(),
      testCoverage: testData.summary.passed / testData.summary.total * 100,
      browserCoverage: Object.keys(testData.browsers).length,
      errorRate: testData.summary.failed / testData.summary.total * 100
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'coverage-report.json'),
      JSON.stringify(coverage, null, 2)
    );
  }

  async generatePerformanceReport(testData) {
    const performanceReport = {
      timestamp: new Date().toISOString(),
      metrics: {
        totalDuration: testData.summary.duration,
        averageTestDuration: testData.performance.averageLoadTime,
        testCount: testData.summary.total,
        passRate: (testData.summary.passed / testData.summary.total) * 100,
        failureRate: (testData.summary.failed / testData.summary.total) * 100
      },
      slowestTests: testData.tests
        .sort((a, b) => b.duration - a.duration)
        .slice(0, 10),
      browserPerformance: testData.browsers
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'performance-report.json'),
      JSON.stringify(performanceReport, null, 2)
    );
  }
}

// CLI interface
if (require.main === module) {
  const generator = new TestReportGenerator();
  generator.generateReport().catch(console.error);
}

module.exports = TestReportGenerator;
