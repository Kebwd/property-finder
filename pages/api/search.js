// Delegate Vercel's /pages/api/search.js to the canonical handler in /api/search.js
// This ensures the same logic is used locally and on Vercel (geocoding, fallbacks, debugging)
module.exports = require('../../api/search.js');
