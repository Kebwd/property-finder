// Debug endpoint for Vercel - completely independent
export default function handler(req, res) {
  try {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.status(200).end();
      return;
    }

    // Check environment variables without importing anything
    const envCheck = {
      NODE_ENV: process.env.NODE_ENV || 'not set',
      SUPABASE_URL: process.env.SUPABASE_URL ? 'Set' : 'Missing',
      SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY ? 'Set' : 'Missing',
      SUPABASE_DB_URL: process.env.SUPABASE_DB_URL ? 'Set' : 'Missing',
      DATABASE_URL: process.env.DATABASE_URL ? 'Set' : 'Missing',
      GEOCODING_API_KEY: process.env.GEOCODING_API_KEY ? 'Set' : 'Missing'
    };

    res.status(200).json({
      status: 'API Debug Info - Independent',
      timestamp: new Date().toISOString(),
      environment: envCheck,
      message: 'This endpoint works independently without server.js',
      vercel: {
        region: process.env.VERCEL_REGION || 'unknown',
        env: process.env.VERCEL_ENV || 'unknown'
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Debug endpoint failed',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : 'hidden'
    });
  }
}
