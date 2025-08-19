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
    console.log('Search API called with query params:', req.query);
    
    const { 
      type = 'all', 
      page = 1, 
      limit = 20,
      lat,
      lng,
      radius = 5000
    } = req.query;

    console.log('Parsed params:', { type, page, limit, lat, lng, radius });

    const offset = (parseInt(page) - 1) * parseInt(limit);
    let query = '';
    let queryParams = [];

    // If lat/lng provided, use geospatial search
    if (lat && lng) {
      const searchLat = parseFloat(lat);
      const searchLng = parseFloat(lng);
      const searchRadius = parseInt(radius);

      if (isNaN(searchLat) || isNaN(searchLng)) {
        return res.status(400).json({ error: 'Invalid latitude or longitude' });
      }

      // Geospatial search with UNION for both business and house tables
      query = `
        SELECT * FROM (
          SELECT 
            'business' AS source,
            b.id,
            b.type,
            b.building_name_zh as name,
            NULL as estate_name_zh,
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
          
          UNION ALL
          
          SELECT 
            'house' AS source,
            h.id,
            h.type,
            h.estate_name_zh as name,
            h.estate_name_zh,
            h.floor,
            h.unit,
            h.area,
            h.deal_price,
            h.deal_date,
            l.province,
            l.city,
            l.town,
            l.street,
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
        ) AS combined_results
        ORDER BY distance
        LIMIT $4 OFFSET $5
      `;

      queryParams = [searchLat, searchLng, searchRadius, parseInt(limit), offset];
    } else {
      // Simple search without geospatial filtering
      query = `
        SELECT * FROM (
          SELECT 
            'business' as source,
            b.id,
            b.type,
            b.building_name_zh as name,
            NULL as estate_name_zh,
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
          
          UNION ALL
          
          SELECT 
            'house' as source,
            h.id,
            h.type,
            h.estate_name_zh as name,
            h.estate_name_zh,
            h.floor,
            h.unit,
            h.area,
            h.deal_price,
            h.deal_date,
            l.province,
            l.city,
            l.town,
            l.street,
            l.lat,
            l.long
          FROM house h
          JOIN location_info l ON h.location_id = l.id
        ) AS combined_results
        ORDER BY deal_date DESC
        LIMIT $1 OFFSET $2
      `;
      queryParams = [parseInt(limit), offset];
    }

    const result = await pool.query(query, queryParams);
    
    res.status(200).json({
      success: true,
      data: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: result.rows.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Search API error:', error);
    console.error('Error stack:', error.stack);
    console.error('Query params:', req.query);
    res.status(500).json({
      success: false,
      error: error.message || 'Internal server error',
      details: error.stack,
      timestamp: new Date().toISOString()
    });
  }
};
