const { chromium } = require("playwright");

(async () => {
    const browser = await chromium.launch({ headless: true});
    const page = await browser.newPage();
    await page.goto('https://cas.duffandphelps.com/Correspondence/MailCorrespondence');
    const title = await page.title;
    console.log('Page title:', title);
    await browser.close();
})();

