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
      specificType,
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

    // Build dynamic query with filtering
    let whereConditions = [`
      6371000 * acos(
        cos(radians($1)) * cos(radians(CAST(l.lat AS FLOAT))) *
        cos(radians(CAST(l.long AS FLOAT)) - radians($2)) +
        sin(radians($1)) * sin(radians(CAST(l.lat AS FLOAT)))
      ) <= ${parseInt(radius)}
    `];
    let queryParams = [searchLat, searchLng];
    let paramIndex = 3;

    // Add specific type filter if provided
    if (specificType && specificType !== '全部') {
      whereConditions.push(`b.type = $${paramIndex}`);
      queryParams.push(specificType);
      paramIndex++;
    }

    // Add date filter 
    if (dateRange) {
      const days = parseInt(dateRange);
      if (!isNaN(days)) {
        whereConditions.push(`b.deal_date >= CURRENT_DATE - INTERVAL '${days} days'`);
      }
    }

    const whereClause = whereConditions.join(' AND ');

    // Simple search query with proper distance calculation in meters
    const query = `
      SELECT 
        'business' AS source,
        b.id,
        b.type,
        b.building_name_zh as building_name_zh,
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
        ROUND(
          6371000 * acos(
            cos(radians($1)) * cos(radians(CAST(l.lat AS FLOAT))) *
            cos(radians(CAST(l.long AS FLOAT)) - radians($2)) +
            sin(radians($1)) * sin(radians(CAST(l.lat AS FLOAT)))
          )
        ) AS distance
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      WHERE ${whereClause}
      ORDER BY distance
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `;

    queryParams.push(limit, offset);

    const result = await client.query(query, queryParams);
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
