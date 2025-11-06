const Tesseract = require('tesseract.js');

async function extractClassMemberId(imagePath) {
  const result = await Tesseract.recognize(imagePath, 'eng');
  const match = result.data.text.match(/Class Member ID[:\s]*([A-Z0-9\-]+)/i);
  return match ? match[1] : null;
}

module.exports = { extractClassMemberId };
