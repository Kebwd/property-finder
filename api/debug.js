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

  try {
    const client = await pool.connect();
    
    // Get table information
    const tablesResult = await client.query(`
      SELECT table_name, table_type 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      ORDER BY table_name
    `);
    
    // Get store count
    const storeCountResult = await client.query('SELECT COUNT(*) as count FROM stores');
    
    // Get house count if table exists
    let houseCount = 0;
    try {
      const houseCountResult = await client.query('SELECT COUNT(*) as count FROM houses');
      houseCount = houseCountResult.rows[0].count;
    } catch (e) {
      // houses table might not exist
    }

    client.release();

    res.status(200).json({
      status: 'debug_info',
      timestamp: new Date().toISOString(),
      database: {
        type: process.env.SUPABASE_URL ? 'supabase' : 'postgresql',
        tables: tablesResult.rows,
        data_counts: {
          stores: parseInt(storeCountResult.rows[0].count),
          houses: parseInt(houseCount)
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
