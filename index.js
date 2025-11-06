// const { chromium } = require("playwright");

// (async () => {
//     const browser = await chromium.launch({ headless: true});
//     const page = await browser.newPage();
//     await page.goto('https://cas.duffandphelps.com/Correspondence/MailCorrespondence');
//     const title = await page.title;
//     console.log('Page title:', title);
//     await browser.close();
// })();

// const { extractClassMemberId } = require('./extractId');

// (async () => {
//   const id = await extractClassMemberId('claim_form.pdf');
//   console.log('Extracted ID:', id);
// })();
// const { chromium } = require('playwright');
// const Tesseract = require('tesseract.js');

// async function extractClassMemberId(imagePath) {
//   const result = await Tesseract.recognize(imagePath, 'eng');
//   const text = result.data.text;
//   console.log('\n📄 OCR Text:\n', text);

//   const match = text.match(/Class Member ID[:\s]*([A-Z0-9\-]+)/i);
//   if (match) {
//     console.log('\n✅ Extracted Class Member ID:', match[1]);
//     return match[1];
//   } else {
//     console.log('\n❌ Class Member ID not found.');
//     return null;
//   }
// }

// (async () => {
//   const browser = await chromium.launch({ headless: true }); // use headless: true for speed
//   const page = await browser.newPage();

//   // Replace with local file path or test URL
//   await page.goto('file:///workspaces/CAS-Linking-Automation-Tool/claim_form.html'); // or a test PDF viewer page

//   await page.screenshot({ path: 'claim_form.png' });

//   await extractClassMemberId('claim_form.png');

//   await browser.close();
// })();
const { chromium } = require('playwright');
const { extractClassMemberId } = require('./extractId');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('file:///workspaces/CAS-Linking-Automation-Tool/claim_form.pdf');
  await page.screenshot({ path: 'claim_form.png' });

  const id = await extractClassMemberId('claim_form.png');
  console.log('Final ID:', id);

  await browser.close();
})();
