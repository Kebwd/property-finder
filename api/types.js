const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    // Get distinct property types
    const typesQuery = `
      SELECT DISTINCT type, COUNT(*) as count 
      FROM business 
      WHERE type IS NOT NULL 
      GROUP BY type 
      ORDER BY count DESC
    `;
    
    const typesResult = await pool.query(typesQuery);
    
    // Get sample data with coordinates
    const sampleQuery = `
      SELECT b.type, b.building_name_zh, l.lat, l.long 
      FROM business b 
      JOIN location_info l ON b.location_id = l.id 
      WHERE b.type IS NOT NULL 
      LIMIT 10
    `;
    
    const sampleResult = await pool.query(sampleQuery);
    
    res.status(200).json({
      success: true,
      available_types: typesResult.rows,
      sample_data: sampleResult.rows,
      message: 'Property types analysis',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Types analysis error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};
