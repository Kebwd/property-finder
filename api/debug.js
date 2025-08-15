// Debug endpoint for Vercel
export default function handler(req, res) {
  try {
    // Check environment variables
    const envCheck = {
      NODE_ENV: process.env.NODE_ENV,
      SUPABASE_URL: process.env.SUPABASE_URL ? 'Set' : 'Missing',
      SUPABASE_DB_URL: process.env.SUPABASE_DB_URL ? 'Set' : 'Missing',
      GEOCODING_API_KEY: process.env.GEOCODING_API_KEY ? 'Set' : 'Missing'
    };

    res.status(200).json({
      status: 'API Debug Info',
      timestamp: new Date().toISOString(),
      environment: envCheck,
      message: 'If you see this, the serverless function is working'
    });
  } catch (error) {
    res.status(500).json({
      error: 'Debug endpoint failed',
      message: error.message,
      stack: error.stack
    });
  }
}
