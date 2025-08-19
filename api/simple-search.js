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
    console.log('Simple search API called with params:', req.query);

    // Very simple query without PostGIS to test basic connectivity
    const result = await pool.query(`
      SELECT 
        'business' AS source,
        b.id,
        b.type,
        b.building_name_zh as name,
        b.floor,
        b.unit,
        b.area,
        b.deal_price,
        b.deal_date,
        l.province,
        l.city,
        l.town,
        l.street,
        l.lat,
        l.long
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      LIMIT 5
    `);
    
    console.log('Simple search query executed, rows returned:', result.rows.length);
    
    res.status(200).json({
      success: true,
      data: result.rows,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Simple search API error:', error);
    console.error('Error stack:', error.stack);
    res.status(500).json({
      success: false,
      error: error.message || 'Unknown error occurred',
      errorName: error.name,
      timestamp: new Date().toISOString()
    });
  }
};
