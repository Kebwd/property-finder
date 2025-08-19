const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

module.exports = async function handler(req, res) {
  // Set CORS headers first
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Test basic connection
    const basicTest = await pool.query('SELECT 1 as test');
    
    // Test business table
    const businessTest = await pool.query('SELECT COUNT(*) as total FROM business LIMIT 1');
    
    // Test location_info table
    const locationTest = await pool.query('SELECT COUNT(*) as total FROM location_info LIMIT 1');
    
    // Test PostGIS extension
    const postgisTest = await pool.query("SELECT PostGIS_version() as version");
    
    res.status(200).json({
      success: true,
      tests: {
        basic: basicTest.rows[0],
        business: businessTest.rows[0],
        location: locationTest.rows[0],
        postgis: postgisTest.rows[0]
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Database test error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
  }
};
