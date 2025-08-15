// Independent search endpoint for Vercel
import { Pool } from 'pg';

// Create database pool with minimal configuration
let pool;

function getPool() {
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL || process.env.SUPABASE_DB_URL,
      ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
      max: 1, // Minimal connection pool for serverless
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });
  }
  return pool;
}

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  let client;
  try {
    const dbPool = getPool();
    client = await dbPool.connect();
    
    const { query, lat, lng, radius = 1000 } = req.query;

    let result;
    
    if (query) {
      // Text search
      result = await client.query(
        'SELECT * FROM stores WHERE name ILIKE $1 OR address ILIKE $1 ORDER BY id LIMIT 50',
        [`%${query}%`]
      );
    } else if (lat && lng) {
      // Geographic search
      result = await client.query(`
        SELECT *, 
        ST_Distance(geom, ST_SetSRID(ST_Point($2, $1), 4326)::geography) as distance
        FROM stores 
        WHERE ST_DWithin(geom, ST_SetSRID(ST_Point($2, $1), 4326)::geography, $3)
        ORDER BY distance
        LIMIT 50
      `, [parseFloat(lat), parseFloat(lng), parseInt(radius)]);
    } else {
      // Return recent stores
      result = await client.query('SELECT * FROM stores ORDER BY id DESC LIMIT 50');
    }
    
    res.status(200).json({
      success: true,
      results: result.rows,
      count: result.rows.length,
      query: { query, lat, lng, radius }
    });
    
  } catch (error) {
    console.error('Search API error:', error);
    res.status(500).json({
      success: false,
      error: 'Search failed',
      message: error.message,
      details: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  } finally {
    if (client) {
      try {
        client.release();
      } catch (e) {
        console.error('Error releasing client:', e);
      }
    }
  }
}
