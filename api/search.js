import pkg from 'pg';
const { Pool } = pkg;

const pool = new Pool({
  connectionString: process.env.SUPABASE_URL ? 
    `postgresql://postgres:${process.env.SUPABASE_SERVICE_ROLE_KEY}@${process.env.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')}.supabase.co:5432/postgres` :
    process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { 
      address, 
      type = 'all', 
      page = 1, 
      limit = 20,
      filter_date,
      category 
    } = req.query;

    const offset = (parseInt(page) - 1) * parseInt(limit);
    let query = '';
    let queryParams = [];
    let paramIndex = 1;

    // Determine which table to search based on type
    if (type === 'business' || type === 'store') {
      query = `
        SELECT id, type, district, address, area, deal_date, price, 
               ST_X(coordinates) as longitude, ST_Y(coordinates) as latitude,
               created_at, updated_at
        FROM stores
        WHERE 1=1
      `;
    } else if (type === 'house' || type === 'residential') {
      query = `
        SELECT id, type, district, address, area, deal_date, price,
               ST_X(coordinates) as longitude, ST_Y(coordinates) as latitude,
               created_at, updated_at
        FROM houses
        WHERE 1=1
      `;
    } else {
      // Search both tables
      query = `
        SELECT 'store' as source, id, type, district, address, area, deal_date, price,
               ST_X(coordinates) as longitude, ST_Y(coordinates) as latitude,
               created_at, updated_at
        FROM stores
        WHERE 1=1
        UNION ALL
        SELECT 'house' as source, id, type, district, address, area, deal_date, price,
               ST_X(coordinates) as longitude, ST_Y(coordinates) as latitude,
               created_at, updated_at
        FROM houses
        WHERE 1=1
      `;
    }

    // Add address filter if provided
    if (address && address.trim()) {
      query += ` AND (address ILIKE $${paramIndex} OR district ILIKE $${paramIndex})`;
      queryParams.push(`%${address.trim()}%`);
      paramIndex++;
    }

    // Add category filter if provided
    if (category && category !== '全部') {
      query += ` AND type = $${paramIndex}`;
      queryParams.push(category);
      paramIndex++;
    }

    // Add date filter if provided
    if (filter_date) {
      query += ` AND deal_date >= $${paramIndex}`;
      queryParams.push(filter_date);
      paramIndex++;
    }

    // Add ordering and pagination
    query += ` ORDER BY deal_date DESC, created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    queryParams.push(parseInt(limit), offset);

    const client = await pool.connect();
    const result = await client.query(query, queryParams);
    
    // Get total count for pagination
    let countQuery = query.replace(/SELECT.*?FROM/, 'SELECT COUNT(*) FROM').replace(/ORDER BY.*/, '');
    const countResult = await client.query(countQuery, queryParams.slice(0, -2)); // Remove limit and offset params
    
    client.release();

    res.status(200).json({
      success: true,
      data: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: parseInt(countResult.rows[0].count),
        pages: Math.ceil(parseInt(countResult.rows[0].count) / parseInt(limit))
      },
      filters: {
        address,
        type,
        category,
        filter_date
      }
    });

  } catch (error) {
    console.error('Search API error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}
