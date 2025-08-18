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
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    const client = await pool.connect();
    
    // Get table information
    const tablesResult = await client.query(`
      SELECT table_name, table_type 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name
    `);
    
    // Get location_info count
    const locationCountResult = await client.query('SELECT COUNT(*) as count FROM location_info');
    
    // Get house count
    let houseCount = 0;
    try {
      const houseCountResult = await client.query('SELECT COUNT(*) as count FROM house');
      houseCount = houseCountResult.rows[0].count;
    } catch (e) {
      // house table might not exist
    }

    // Get sample data from both tables
    const sampleHousesResult = await client.query(`
      SELECT 
        h.type,
        h.estate_name_zh,
        h.deal_price,
        h.deal_date,
        l.town,
        l.street
      FROM house h
      JOIN location_info l ON h.location_id = l.id
      ORDER BY h.deal_date DESC
      LIMIT 5
    `);

    const sampleLocationsResult = await client.query(`
      SELECT province, city, town, street, lat, long
      FROM location_info
      ORDER BY id
      LIMIT 5
    `);

    client.release();

    res.status(200).json({
      status: 'debug_info',
      timestamp: new Date().toISOString(),
      database: {
        type: process.env.SUPABASE_URL ? 'supabase' : 'postgresql',
        tables: tablesResult.rows,
        data_counts: {
          location_info: parseInt(locationCountResult.rows[0].count),
          house: parseInt(houseCount)
        },
        sample_data: {
          houses: sampleHousesResult.rows,
          locations: sampleLocationsResult.rows
        }
      },
      environment: {
        node_version: process.version,
        platform: 'vercel',
        has_supabase_url: !!process.env.SUPABASE_URL,
        has_database_url: !!process.env.DATABASE_URL
      }
    });
  } catch (error) {
    console.error('Debug endpoint error:', error);
    res.status(500).json({
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
}
