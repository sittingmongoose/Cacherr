# Playwright Setup Instructions

If you want to run Playwright tests for the Cacherr web interface, here are the setup instructions:

## System Dependencies

The system is missing browser dependencies. Install them with:

```bash
# For Ubuntu/Debian systems:
apt-get update && apt-get install -y \
    libnspr4 \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libdrm2 \
    libxss1

# Or use Playwright's built-in dependency installer:
playwright install-deps
```

## Python Packages

The required packages are already installed:
- playwright
- requests
- pyee
- greenlet

## Browser Installation

Install the Chromium browser for Playwright:

```bash
playwright install chromium
```

## Running Tests

Example test script location: The test scripts were removed after completion, but you can create new ones following this pattern:

```python
from playwright.sync_api import sync_playwright
import requests

def test_cached_page():
    base_url = "http://localhost:5445"
    
    # First run a test operation via API
    response = requests.post(f"{base_url}/api/run", json={"test_mode": True})
    
    # Then test the frontend
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(base_url)
        
        # Look for the test results tab
        test_results_tab = page.wait_for_selector('button:has-text("Test Results")')
        test_results_tab.click()
        
        # Verify content is displayed
        page.wait_for_selector('h2:has-text("Test Mode Results")')
        
        browser.close()
```

## Notes

- The Cacherr container needs to be running on port 5445
- Ensure the Plex server is configured and accessible
- Tests should be run from outside the Docker container
- The web interface uses React, so wait for content to load properly