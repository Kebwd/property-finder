const { Pool } = require('pg');

module.exports = async function handler(req, res) {
  // Set CORS headers first
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    // Check environment variables
    const envInfo = {
      has_supabase_url: !!process.env.SUPABASE_URL,
      has_supabase_key: !!process.env.SUPABASE_SERVICE_ROLE_KEY,
      has_database_url: !!process.env.DATABASE_URL,
      supabase_url_preview: process.env.SUPABASE_URL ? 
        process.env.SUPABASE_URL.substring(0, 20) + '...' : null,
      node_version: process.version,
      platform: 'vercel'
    };

    // Try to create connection string
    let connectionString = '';
    if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY) {
      const supabaseUrl = process.env.SUPABASE_URL.replace('https://', '').replace('.supabase.co', '');
      connectionString = `postgresql://postgres:${process.env.SUPABASE_SERVICE_ROLE_KEY}@${supabaseUrl}.supabase.co:5432/postgres`;
    } else if (process.env.DATABASE_URL) {
      connectionString = process.env.DATABASE_URL;
    }

    // Try database connection
    let dbTest = { connected: false, error: null };
    if (connectionString) {
      try {
        const pool = new Pool({
          connectionString,
          ssl: { rejectUnauthorized: false }
        });
        
        const client = await pool.connect();
        const result = await client.query('SELECT NOW() as current_time');
        client.release();
        await pool.end();
        
        dbTest = {
          connected: true,
          current_time: result.rows[0].current_time,
          connection_type: process.env.SUPABASE_URL ? 'supabase' : 'other'
        };
      } catch (error) {
        dbTest = {
          connected: false,
          error: error.message
        };
      }
    }

    res.status(200).json({
      status: 'debug',
      timestamp: new Date().toISOString(),
      environment: envInfo,
      database: dbTest,
      connection_string_preview: connectionString ? 
        connectionString.substring(0, 30) + '...' : 'not configured'
    });

  } catch (error) {
    res.status(500).json({
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
};
