const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.error('PAGE ERROR:', err.message));

  const baseUrl = 'http://architools.duckdns.org/pricetracker';
  const targetUrl = 'https://www.jonesbootmaker.com/products/bayridge-leather-chelsea-boots-bayridge2-324-403-british-tan/british%20tan/7?gad_source=1&gad_campaignid=22715557436&gclid=Cj0KCQjw8eTFBhCXARIsAIkiuOyJd7cR0g509uKO2DBpjsrZfRNHVRagLFwVAI2FAn4W6Qo8H1K9rn8aAt9WEALw_wcB';

  try {
    // 1. Navigate to login page and login
    console.log('Navigating to login page...');
    await page.goto(`${baseUrl}/login`, { waitUntil: 'networkidle' });
    await page.fill('input[name="username"]', 'aogle');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    console.log('Submitted login form.');

    // Wait for an element that appears after successful login
    await page.waitForSelector('#track-form', { timeout: 30000 });
    console.log('Successfully logged in and #track-form is visible.');
    console.log('Current URL after successful login:', page.url());

    // 2. Input URL and Submit
    console.log('Entering target URL into input field...');
    await page.fill('#url-input', targetUrl);
    await page.click('#track-form button[type="submit"]');
    console.log('Submitted track form.');

    // 3. Wait for iframe to load
    console.log('Waiting for iframe to load...');
    await page.waitForSelector('#page-content iframe', { state: 'visible', timeout: 30000 });
    console.log('Iframe loaded.');

    console.log('Test finished: Page loaded and iframe is visible.');

  } catch (error) {
    console.error('An error occurred:', error);
    console.log('Test failed.');
  } finally {
    await page.screenshot({ path: 'debug/inspector_in_frame_screenshot.png', fullPage: true });
    console.log('Screenshot taken and saved to debug/inspector_in_frame_screenshot.png');
    await browser.close();
  }
})();