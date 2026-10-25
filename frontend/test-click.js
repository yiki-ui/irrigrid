const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  await page.goto('http://localhost:3000', {waitUntil: 'networkidle2'});
  
  // Try to find the step items
  const items = await page.$$('.step-item');
  console.log('Found step items:', items.length);
  
  if (items.length > 1) {
    console.log('Clicking second step item...');
    await items[1].click();
    await page.waitForTimeout(1000);
    
    const active = await page.$('.step-item.active');
    const text = await page.evaluate(el => el ? el.textContent : 'none', active);
    console.log('Active tab after click:', text);
  }
  
  await browser.close();
})();
