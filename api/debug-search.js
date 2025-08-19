const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.SUPABASE_URL ? 
    `postgresql://postgres:${process.env.SUPABASE_SERVICE_ROLE_KEY}@${process.env.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')}.supabase.co:5432/postgres` :
    process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

module.exports = async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    console.log('Debug search endpoint called');
    console.log('Query params:', req.query);
    
    // Test basic database connection
    const testResult = await pool.query('SELECT 1 as test');
    console.log('Database connection test:', testResult.rows);
    
    // Test a simple query
    const simpleQuery = 'SELECT COUNT(*) as total FROM business LIMIT 1';
    const countResult = await pool.query(simpleQuery);
    console.log('Business count:', countResult.rows);
    
    // Test location info
    const locationQuery = 'SELECT COUNT(*) as total FROM location_info LIMIT 1';
    const locationResult = await pool.query(locationQuery);
    console.log('Location count:', locationResult.rows);
    
    // Test with coordinates if provided
    const { lat, lng, radius = 5000 } = req.query;
    if (lat && lng) {
      const searchLat = parseFloat(lat);
      const searchLng = parseFloat(lng);
      console.log('Testing with coordinates:', { searchLat, searchLng, radius });
      
      const geoQuery = `
        SELECT COUNT(*) as total
        FROM business b
        JOIN location_info l ON b.location_id = l.id
        WHERE ST_DWithin(
          ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
          ST_SetSRID(ST_Point($2, $1), 4326)::geography,
          $3
        )
      `;
      
      const geoResult = await pool.query(geoQuery, [searchLat, searchLng, parseInt(radius)]);
      console.log('Geo search count:', geoResult.rows);
    }
    
    res.status(200).json({
      success: true,
      message: 'Debug endpoint working',
      query: req.query,
      testResult: testResult.rows,
      countResult: countResult.rows,
      locationResult: locationResult.rows,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Debug search error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
  }
};
