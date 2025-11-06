// const Tesseract = require('tesseract.js');

// async function extractClassMemberId(imagePath) {
//   const result = await Tesseract.recognize(imagePath, 'eng');
//   const match = result.data.text.match(/Class Member ID[:\s]*([A-Z0-9\-]+)/i);
//   return match ? match[1] : null;
// }

// module.exports = { extractClassMemberId };
// const poppler = require('pdf-poppler');
// const path = require('path');

// const file = path.join(__dirname, 'claim_form.pdf');
// const opts = {
//   format: 'png',
//   out_dir: path.dirname(file),
//   out_prefix: 'claim_form',
//   page: 1
// };

// poppler.convert(file, opts)
//   .then(() => console.log('PDF converted to image'))
//   .catch(err => console.error('Conversion error:', err));
// const { fromPath } = require('pdf2pic');
// const Tesseract = require('tesseract.js');
// const path = require('path');

// async function extractClassMemberId(pdfPath) {
//   const convert = fromPath(pdfPath, {
//     density: 300,
//     saveFilename: 'claim_form',
//     savePath: './',
//     format: 'png',
//     width: 1000,
//     height: 1000
//   });

//   try {
//     const result = await convert(1); // Convert first page
//     const imagePath = result.path;

//     const ocr = await Tesseract.recognize(imagePath, 'eng');
//     const text = ocr.data.text;

//     console.log('\n📄 OCR Text:\n', text);

//     const match = text.match(/Class Member ID[:\s]*([A-Z0-9\-]+)/i);
//     if (match) {
//       console.log('\n✅ Extracted Class Member ID:', match[1]);
//       return match[1];
//     } else {
//       console.log('\n❌ Class Member ID not found.');
//       return null;
//     }
//   } catch (err) {
//     console.error('Error during extraction:', err);
//     return null;
//   }
// }

// extractClassMemberId('005E9D4D.pdf');
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

module.exports = { extractClassMemberId };
