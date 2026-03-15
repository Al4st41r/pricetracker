
const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.error('PAGE ERROR:', err.message));

  const inspectorTestUrl = 'http://architools.duckdns.org/pricetracker/static/inspector_test.html'; // Corrected URL

  try {
    console.log(`Navigating to ${inspectorTestUrl}...`);
    await page.goto(inspectorTestUrl, { waitUntil: 'networkidle' });
    console.log('Page loaded successfully.');

    // The inspector_test.html already loads inspector.js and calls initInspector
    // It also has mock functions for showModal, Toastify, and loadTrackedItems
    // We just need to wait for the modal to appear.

    // Wait for the modal to appear
    await page.waitForSelector('#custom-modal[style*="display: block"]', { timeout: 10000 });
    console.log('Test passed: Custom modal appeared.');

  } catch (error) {
    console.error('An error occurred:', error);
    console.log('Test failed.');
  } finally {
    await page.screenshot({ path: 'debug/inspector_test_html_screenshot.png', fullPage: true });
    console.log('Screenshot taken and saved to debug/inspector_test_html_screenshot.png');
    await browser.close();
  }
})();
