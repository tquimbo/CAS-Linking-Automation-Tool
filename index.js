const { extractClassMemberId } = require('./extractId');

(async () => {
  const id = await extractClassMemberId('form.png'); // ✅ use the actual filename
  console.log('\nFinal ID:', id);
})();