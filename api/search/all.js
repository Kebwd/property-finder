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
    const { 
      lat, 
      lng, 
      radius = 5000, 
      page = 1, 
      perPage = 10,
      type,
      dateRange 
    } = req.query;

    if (!lat || !lng) {
      return res.status(400).json({ error: 'lat and lng parameters are required' });
    }

    const searchLat = parseFloat(lat);
    const searchLng = parseFloat(lng);
    const limit = parseInt(perPage);
    const offset = (parseInt(page) - 1) * limit;

    if (isNaN(searchLat) || isNaN(searchLng)) {
      return res.status(400).json({ error: 'Invalid latitude or longitude' });
    }

    const connectionString = process.env.DATABASE_URL;
    
    if (!connectionString) {
      return res.status(500).json({
        success: false,
        error: 'No DATABASE_URL configured'
      });
    }

    const pool = new Pool({
      connectionString,
      ssl: { rejectUnauthorized: false }
    });

    const client = await pool.connect();

    // Simple search query without PostGIS for now
    const query = `
      SELECT 
        'business' AS source,
        b.id,
        b.type,
        b.building_name_zh as name,
        NULL as estate_name_zh,
        NULL as flat,
        b.floor,
        b.unit,
        b.area,
        b.deal_price,
        b.deal_date,
        b.developer,
        l.province,
        l.city,
        l.town,
        l.street,
        l.road,
        l.lat,
        l.long,
        ABS(CAST(l.lat AS FLOAT) - $1) + ABS(CAST(l.long AS FLOAT) - $2) AS distance
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      WHERE ABS(CAST(l.lat AS FLOAT) - $1) + ABS(CAST(l.long AS FLOAT) - $2) < 0.1
      ORDER BY distance
      LIMIT $3 OFFSET $4
    `;

    const result = await client.query(query, [searchLat, searchLng, limit, offset]);
    client.release();
    await pool.end();
    
    res.status(200).json({
      success: true,
      data: result.rows,
      pagination: {
        page: parseInt(page),
        perPage: limit,
        total: result.rows.length
      },
      search_params: {
        lat: searchLat,
        lng: searchLng,
        radius: parseInt(radius)
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Search all API error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};
