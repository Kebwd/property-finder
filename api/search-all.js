const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.SUPABASE_URL ? 
    `postgresql://postgres:${process.env.SUPABASE_SERVICE_ROLE_KEY}@${process.env.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')}.supabase.co:5432/postgres` :
    process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

// Geocoding function (simplified for serverless)
async function geocode(address) {
  // This would need Google Maps API key - for now return null
  // You can implement this later with your GEOCODING_API_KEY
  return null;
}

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
    const { q, lat, lng, radius = '5000', type, dateRange } = req.query;
    let searchLat, searchLng;
    let dateThreshold;

    // Handle date range
    if (dateRange && !isNaN(parseInt(dateRange, 10))) {
      const days = parseInt(dateRange, 10);
      const now = new Date();
      now.setDate(now.getDate() - days);
      dateThreshold = now.toISOString().split('T')[0];
    }

    // Geocode or use lat/lng
    if (q && q.trim()) {
      const coords = await geocode(q.trim());
      if (!coords) {
        return res.status(404).json({ error: `Could not find location "${q.trim()}"` });
      }
      searchLat = coords.lat;
      searchLng = coords.lng;
    } else if (lat && lng) {
      searchLat = parseFloat(lat);
      searchLng = parseFloat(lng);
      if (isNaN(searchLat) || isNaN(searchLng)) {
        return res.status(400).json({ error: 'Invalid latitude or longitude' });
      }
    } else {
      return res.status(400).json({ error: 'Please enter a location or provide lat & lng' });
    }

    // Build dynamic WHERE clause
    const filters = [];
    const params = [searchLng, searchLat, parseInt(radius, 10)];
    let idx = 4;

    if (type) {
      filters.push(`type = $${idx}`);
      params.push(type);
      idx++;
    }

    if (dateThreshold) {
      filters.push(`deal_date >= $${idx}`);
      params.push(dateThreshold);
      idx++;
    }

    const filterClause = filters.length ? `AND ${filters.join(' AND ')}` : '';

    // Unified SQL with UNION ALL (based on your existing route)
    const sql = `
      SELECT 
        'business' AS deal_type,
        b.id, b.type, b.building_name_zh, NULL AS estate_name_zh, NULL AS flat,
        b.floor, b.unit, b.area, b.deal_price, b.deal_date, b.developer,
        l.province, l.city, l.country, l.town, l.street, l.road,
        ST_Distance(
          l.geom::geography,
          ST_SetSRID(ST_Point($1, $2),4326)::geography
        ) AS distance
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      WHERE ST_DWithin(
        l.geom::geography,
        ST_SetSRID(ST_Point($1, $2),4326)::geography,
        $3
      )
      ${filterClause}

      UNION ALL

      SELECT 
        'house' AS deal_type,
        h.id, h.type, NULL AS building_name_zh, h.estate_name_zh, h.flat,
        h.floor, h.unit, h.area, h.deal_price, h.deal_date, h.developer,
        l.province, l.city, l.country, l.town, l.street, l.road,
        ST_Distance(
          l.geom::geography,
          ST_SetSRID(ST_Point($1, $2),4326)::geography
        ) AS distance
      FROM house h
      JOIN location_info l ON h.location_id = l.id
      WHERE ST_DWithin(
        l.geom::geography,
        ST_SetSRID(ST_Point($1, $2),4326)::geography,
        $3
      )
      ${filterClause}

      ORDER BY distance
      LIMIT 50
    `;

    const { rows } = await pool.query(sql, params);
    
    res.status(200).json({
      success: true,
      data: rows,
      count: rows.length,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Search error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};
