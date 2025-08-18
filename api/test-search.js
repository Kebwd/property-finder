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

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Use Central Hong Kong coordinates
    const lat = 22.281;
    const lng = 114.161;
    
    const query = `
      SELECT 
        'business' AS source,
        b.id,
        b.type,
        b.building_name_zh as building_name_zh,
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
        l.long,
        ABS(CAST(l.lat AS FLOAT) - $1) + ABS(CAST(l.long AS FLOAT) - $2) AS distance
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      WHERE ABS(CAST(l.lat AS FLOAT) - $1) + ABS(CAST(l.long AS FLOAT) - $2) < 0.1
      ORDER BY distance
      LIMIT 5
    `;

    const result = await pool.query(query, [lat, lng]);
    
    res.status(200).json({
      success: true,
      data: result.rows,
      search_coords: { lat, lng },
      total_found: result.rows.length,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Test search error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};
