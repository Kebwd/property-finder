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
    console.log('Starting export...');
    
    // Get business data with location info - simplified query first
    const businessQuery = `
      SELECT
        l.province,
        l.city,
        l.town,
        l.street,
        b.type,
        b.building_name_zh,
        b.floor,
        b.unit,
        b.area,
        b.deal_price,
        b.deal_date
      FROM location_info l
      JOIN business b ON l.id = b.location_id
      ORDER BY b.deal_date DESC
      LIMIT 100
    `;

    console.log('Executing query...');
    const businessResult = await pool.query(businessQuery);
    console.log('Query result:', businessResult.rows.length, 'rows');

    // Create simple CSV
    const headers = ['Province', 'City', 'Town', 'Street', 'Type', 'Building', 'Floor', 'Unit', 'Area', 'Price', 'Date'];
    let csvContent = headers.join(',') + '\n';
    
    businessResult.rows.forEach(row => {
      const values = [
        row.province || '',
        row.city || '',
        row.town || '',
        row.street || '',
        row.type || '',
        row.building_name_zh || '',
        row.floor || '',
        row.unit || '',
        row.area || '',
        row.deal_price || '',
        row.deal_date || ''
      ];
      csvContent += values.join(',') + '\n';
    });

    // Set response headers for CSV download
    const filename = `properties_${new Date().toISOString().split('T')[0]}.csv`;
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    
    res.end(csvContent);
    console.log('Export completed successfully');

  } catch (error) {
    console.error('Export error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};
