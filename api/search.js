// Search endpoint for Vercel
import { Pool } from 'pg';

// Create database pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || process.env.SUPABASE_DB_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const { query, lat, lng, radius = 1000 } = req.query;

    // Simple search without geocoding for now
    if (query) {
      const result = await pool.query(
        'SELECT * FROM stores WHERE name ILIKE $1 OR address ILIKE $1 LIMIT 50',
        [`%${query}%`]
      );
      
      res.status(200).json({
        success: true,
        results: result.rows,
        count: result.rows.length
      });
    } else if (lat && lng) {
      // Geographic search
      const result = await pool.query(`
        SELECT *, 
        ST_Distance(geom, ST_SetSRID(ST_Point($2, $1), 4326)::geography) as distance
        FROM stores 
        WHERE ST_DWithin(geom, ST_SetSRID(ST_Point($2, $1), 4326)::geography, $3)
        ORDER BY distance
        LIMIT 50
      `, [lat, lng, radius]);
      
      res.status(200).json({
        success: true,
        results: result.rows,
        count: result.rows.length
      });
    } else {
      // Return all stores (limited)
      const result = await pool.query('SELECT * FROM stores LIMIT 50');
      
      res.status(200).json({
        success: true,
        results: result.rows,
        count: result.rows.length
      });
    }
  } catch (error) {
    console.error('Search API error:', error);
    res.status(500).json({
      success: false,
      error: 'Search failed',
      message: error.message,
      details: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
}
