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
    const searchRadius = parseInt(radius);
    const limit = parseInt(perPage);
    const offset = (parseInt(page) - 1) * limit;

    if (isNaN(searchLat) || isNaN(searchLng)) {
      return res.status(400).json({ error: 'Invalid latitude or longitude' });
    }

    // Build dynamic WHERE clause for date filtering
    let dateFilter = '';
    const params = [searchLat, searchLng, searchRadius];
    let paramIndex = 4;

    if (dateRange && !isNaN(parseInt(dateRange, 10))) {
      const days = parseInt(dateRange, 10);
      const now = new Date();
      now.setDate(now.getDate() - days);
      const dateThreshold = now.toISOString().split('T')[0];
      dateFilter = `AND h.deal_date >= $${paramIndex}`;
      params.push(dateThreshold);
      paramIndex++;
    }

    // Geospatial search query with both business and house tables
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
        ST_Distance(
          ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
          ST_SetSRID(ST_Point($2, $1), 4326)::geography
        ) AS distance
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      WHERE ST_DWithin(
        ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
        ST_SetSRID(ST_Point($2, $1), 4326)::geography,
        $3
      )
      ${dateFilter.replace('h.', 'b.')}
      
      UNION ALL
      
      SELECT 
        'house' AS source,
        h.id,
        h.type,
        h.estate_name_zh as name,
        h.estate_name_zh,
        h.flat,
        h.floor,
        h.unit,
        h.area,
        h.deal_price,
        h.deal_date,
        h.developer,
        l.province,
        l.city,
        l.town,
        l.street,
        l.road,
        l.lat,
        l.long,
        ST_Distance(
          ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
          ST_SetSRID(ST_Point($2, $1), 4326)::geography
        ) AS distance
      FROM house h
      JOIN location_info l ON h.location_id = l.id
      WHERE ST_DWithin(
        ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
        ST_SetSRID(ST_Point($2, $1), 4326)::geography,
        $3
      )
      ${dateFilter}
      
      ORDER BY distance
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    params.push(limit, offset);

    const result = await pool.query(query, params);
    
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
        radius: searchRadius
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
