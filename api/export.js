const { Pool } = require('pg');

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

  let pool;
  try {
    console.log('Starting export...');
    
    // Create new pool connection for this request
    pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
      max: 1,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 10000,
    });

    console.log('Testing database connection...');
    
    // Get basic business data without joins to avoid complexity
    const businessQuery = `
      SELECT
        type,
        building_name_zh,
        floor,
        unit,
        area,
        deal_price,
        deal_date
      FROM business
      ORDER BY id
      LIMIT 100
    `;

    console.log('Executing main query...');
    const businessResult = await pool.query(businessQuery);
    console.log('Query result:', businessResult.rows.length, 'rows');

    if (businessResult.rows.length === 0) {
      await pool.end();
      return res.status(200).json({
        success: false,
        error: 'No data found',
        timestamp: new Date().toISOString()
      });
    }

    // Create simple CSV
    const headers = ['Type', 'Building', 'Floor', 'Unit', 'Area', 'Price', 'Date'];
    let csvContent = headers.join(',') + '\n';
    
    businessResult.rows.forEach(row => {
      const values = [
        `"${(row.type || '').replace(/"/g, '""')}"`,
        `"${(row.building_name_zh || '').replace(/"/g, '""')}"`,
        `"${(row.floor || '').replace(/"/g, '""')}"`,
        `"${(row.unit || '').replace(/"/g, '""')}"`,
        row.area || '',
        row.deal_price || '',
        row.deal_date ? row.deal_date.toISOString().split('T')[0] : ''
      ];
      csvContent += values.join(',') + '\n';
    });

    console.log('CSV content length:', csvContent.length);

    // Set response headers for CSV download
    const filename = `properties_${new Date().toISOString().split('T')[0]}.csv`;
    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    
    console.log('Sending CSV response...');
    res.end(csvContent);
    console.log('Export completed successfully');
    
    await pool.end();

  } catch (error) {
    console.error('Export error details:', error);
    if (pool) {
      try {
        await pool.end();
      } catch (e) {
        console.error('Error closing pool:', e);
      }
    }
    res.status(500).json({
      success: false,
      error: `Export failed: ${error.message}`,
      timestamp: new Date().toISOString()
    });
  }
};
