const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.SUPABASE_URL ? 
    `postgresql://postgres:${process.env.SUPABASE_SERVICE_ROLE_KEY}@${process.env.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')}.supabase.co:5432/postgres` :
    process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

module.exports = async function handler(req, res) {
  // Set CORS headers first
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    // Check what types exist in business table
    const businessTypesQuery = `
      SELECT DISTINCT type, COUNT(*) as count 
      FROM business 
      WHERE type IS NOT NULL 
      GROUP BY type 
      ORDER BY count DESC
    `;
    
    // Check what types exist in house table (if any)
    const houseTypesQuery = `
      SELECT DISTINCT type, COUNT(*) as count 
      FROM house 
      WHERE type IS NOT NULL 
      GROUP BY type 
      ORDER BY count DESC
    `;

    const businessResult = await pool.query(businessTypesQuery);
    const houseResult = await pool.query(houseTypesQuery);
    
    res.status(200).json({
      success: true,
      business_types: businessResult.rows,
      house_types: houseResult.rows,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Types check error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};
