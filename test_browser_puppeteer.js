const puppeteer = require('puppeteer');

async function testWebGUI() {
  console.log('🌐 Testing Cacherr Web GUI with Puppeteer...\n');
  
  let browser;
  try {
    // Launch browser
    browser = await puppeteer.launch({
      headless: true,
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
    });
    
    const page = await browser.newPage();
    
    // Set viewport
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Enable console logging
    page.on('console', msg => {
      const type = msg.type();
      const text = msg.text();
      if (type === 'error') {
        console.log(`❌ Console Error: ${text}`);
      } else if (type === 'warn') {
        console.log(`⚠️  Console Warning: ${text}`);
      } else if (type === 'log') {
        console.log(`ℹ️  Console Log: ${text}`);
      }
    });
    
    // Enable network monitoring
    page.on('requestfailed', request => {
      console.log(`❌ Network Error: ${request.url()} - ${request.failure().errorText}`);
    });
    
    // Enable response monitoring
    page.on('response', response => {
      if (!response.ok()) {
        console.log(`❌ HTTP Error: ${response.url()} - ${response.status()} ${response.statusText()}`);
      }
    });
    
    console.log('✅ Browser launched successfully');
    
    // Navigate to the application
    console.log('🌐 Navigating to http://localhost:5445...');
    await page.goto('http://localhost:5445', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    console.log('✅ Page loaded successfully');
    
    // Check for JavaScript errors
    const jsErrors = await page.evaluate(() => {
      return window.jsErrors || [];
    });
    
    if (jsErrors.length > 0) {
      console.log('❌ JavaScript Errors Found:');
      jsErrors.forEach(error => console.log(`   - ${error}`));
    } else {
      console.log('✅ No JavaScript errors detected');
    }
    
    // Check page title
    const title = await page.title();
    console.log(`📄 Page Title: ${title}`);
    
    // Check if main content loaded
    const mainContent = await page.$('main, #root, #app');
    if (mainContent) {
      console.log('✅ Main content container found');
    } else {
      console.log('❌ Main content container not found');
    }
    
    // Check for React app
    const reactRoot = await page.$('[data-reactroot], #root');
    if (reactRoot) {
      console.log('✅ React app detected');
    } else {
      console.log('❌ React app not detected');
    }
    
    // Check for WebSocket connection
    const wsStatus = await page.evaluate(() => {
      return window.webSocketStatus || 'unknown';
    });
    console.log(`🔌 WebSocket Status: ${wsStatus}`);
    
    // Check for any loading spinners
    const loadingSpinners = await page.$$('[data-testid="loading"], .loading, .spinner');
    if (loadingSpinners.length > 0) {
      console.log(`⏳ Found ${loadingSpinners.length} loading indicators`);
    }
    
    // Take a screenshot
    await page.screenshot({ 
      path: 'test-results/web-gui-test.png',
      fullPage: true 
    });
    console.log('📸 Screenshot saved to test-results/web-gui-test.png');
    
    // Check for common UI elements
    const dashboardElements = await page.$$('[data-testid*="dashboard"], [data-testid*="status"], [data-testid*="stats"]');
    console.log(`🎛️  Found ${dashboardElements.length} dashboard elements`);
    
    // Check for navigation
    const navElements = await page.$$('nav, [role="navigation"], [data-testid*="nav"]');
    console.log(`🧭 Found ${navElements.length} navigation elements`);
    
    // Check for buttons
    const buttons = await page.$$('button, [role="button"], input[type="button"]');
    console.log(`🔘 Found ${buttons.length} interactive buttons`);
    
    // Test basic interactions
    console.log('🖱️  Testing basic interactions...');
    
    // Try to click a button if available
    const firstButton = await page.$('button');
    if (firstButton) {
      try {
        await firstButton.click();
        console.log('✅ Button click successful');
      } catch (error) {
        console.log(`❌ Button click failed: ${error.message}`);
      }
    }
    
    // Check for any error messages
    const errorMessages = await page.$$('[data-testid*="error"], .error, .alert-error');
    if (errorMessages.length > 0) {
      console.log(`❌ Found ${errorMessages.length} error messages`);
      for (let i = 0; i < errorMessages.length; i++) {
        const text = await errorMessages[i].textContent();
        console.log(`   - ${text}`);
      }
    }
    
    // Check for success messages
    const successMessages = await page.$$('[data-testid*="success"], .success, .alert-success');
    if (successMessages.length > 0) {
      console.log(`✅ Found ${successMessages.length} success messages`);
    }
    
    // Check page performance
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        totalTime: navigation.loadEventEnd - navigation.fetchStart
      };
    });
    
    console.log('📊 Performance Metrics:');
    console.log(`   - Load Time: ${performanceMetrics.loadTime}ms`);
    console.log(`   - DOM Content Loaded: ${performanceMetrics.domContentLoaded}ms`);
    console.log(`   - Total Time: ${performanceMetrics.totalTime}ms`);
    
    // Test WebSocket connection
    console.log('🔌 Testing WebSocket connection...');
    try {
      await page.evaluate(() => {
        return new Promise((resolve, reject) => {
          const ws = new WebSocket('ws://localhost:5445/ws');
          ws.onopen = () => {
            console.log('✅ WebSocket connection opened');
            ws.close();
            resolve(true);
          };
          ws.onerror = (error) => {
            console.log('❌ WebSocket connection failed:', error);
            reject(error);
          };
          ws.onclose = () => {
            resolve(true);
          };
        });
      });
    } catch (error) {
      console.log(`❌ WebSocket test failed: ${error.message}`);
    }
    
    // Test API calls
    console.log('🔌 Testing API calls...');
    try {
      const apiResponse = await page.evaluate(async () => {
        const response = await fetch('/api/status');
        return {
          status: response.status,
          ok: response.ok,
          data: await response.text()
        };
      });
      console.log(`✅ API call successful: ${apiResponse.status} ${apiResponse.ok ? 'OK' : 'Error'}`);
    } catch (error) {
      console.log(`❌ API call failed: ${error.message}`);
    }
    
    console.log('\n🎉 Web GUI testing completed successfully!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test
testWebGUI().catch(console.error);
