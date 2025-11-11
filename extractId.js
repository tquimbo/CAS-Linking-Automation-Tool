const Tesseract = require('tesseract.js');

async function extractClassMemberId(imagePath) {
  try {
    const result = await Tesseract.recognize(imagePath, 'eng');
    const text = result.data.text;

    console.log('\n📄 OCR Text:\n', text);

    const match = text.match(/Class Member ID[:\s]*([A-Z0-9\-]+)/i);
    if (match) {
      console.log('\n✅ Extracted Class Member ID:', match[1]);
      return match[1];
    } else {
      console.log('\n❌ Class Member ID not found.');
      return null;
    }
  } catch (err) {
    console.error('OCR error:', err);
    return null;
  }
}

module.exports = { extractClassMemberId }; // ✅ this line is critical
