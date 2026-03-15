const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  let dialogAppeared = false;
  page.on('dialog', async dialog => {
    console.log(`Dialog message: ${dialog.message()}`);
    dialogAppeared = true;
    await dialog.dismiss();
  });

  await page.goto('http://architools.duckdns.org/inspector_test/inspector_test.html');

  const frame = page.frame({ url: /\/inspector_test\/iframe_content\.html/ });
  if (frame) {
    const priceElement = await frame.locator('.price').first();
    await priceElement.click();
  } else {
    console.log('Iframe not found');
  }

  await page.waitForTimeout(1000); // Wait for the dialog to appear

  if (dialogAppeared) {
    console.log('Test passed: Modal window appeared.');
  } else {
    console.log('Test failed: Modal window did not appear.');
  }

  await browser.close();
})();