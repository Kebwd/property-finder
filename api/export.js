const { Pool } = require('pg');
const XLSX = require('xlsx');

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
    
    // Get comprehensive property data with location information
    const propertyQuery = `
      SELECT
        'business' as record_type,
        COALESCE(l.province, '香港') as province,
        COALESCE(l.city, '香港') as city,
        COALESCE(l.country, '') as district,
        COALESCE(l.street, '') as street,
        COALESCE(l.road, '') as road,
        b.type as property_type,
        b.building_name_zh as building_name,
        '' as block_number,
        b.floor as floor,
        b.unit as unit,
        b.area as area,
        b.deal_price as price,
        b.deal_date as deal_date,
        COALESCE(b.developer, '') as developer,
        '' as house_type,
        '' as estate_name
      FROM business b
      LEFT JOIN location_info l ON b.location_id = l.id
      
      UNION ALL
      
      SELECT
        'house' as record_type,
        COALESCE(l.province, '香港') as province,
        COALESCE(l.city, '香港') as city,
        COALESCE(l.country, '') as district,
        COALESCE(l.street, '') as street,
        COALESCE(l.road, '') as road,
        h.type as property_type,
        h.building_name_zh as building_name,
        COALESCE(h.flat, '') as block_number,
        h.floor as floor,
        h.unit as unit,
        h.area as area,
        h.deal_price as price,
        h.deal_date as deal_date,
        COALESCE(h.developer, '') as developer,
        COALESCE(h.house_type, '') as house_type,
        COALESCE(h.estate_name_zh, '') as estate_name
      FROM house h
      LEFT JOIN location_info l ON h.location_id = l.id
      
      ORDER BY deal_date DESC
      LIMIT 1000
    `;

    console.log('Executing comprehensive property query...');
    const result = await pool.query(propertyQuery);
    console.log('Query result:', result.rows.length, 'rows');

    if (result.rows.length === 0) {
      await pool.end();
      return res.status(200).json({
        success: false,
        error: 'No data found',
        timestamp: new Date().toISOString()
      });
    }

    // Transform data to match the expected format with Chinese headers
    const excelData = result.rows.map(row => {
      // Combine street and road information
      const streetAddress = [row.street, row.road].filter(Boolean).join(' ');
      
      return {
        '記錄類型': row.record_type === 'business' ? '商業物業' : '住宅物業',
        '市': row.city,
        '區': row.district,
        '物業': row.estate_name || row.building_name || '',
        '街道及門牌': streetAddress,
        '座': row.block_number,
        '物業類別': row.property_type || '',
        '大廈名稱': row.building_name || '',
        '樓層': row.floor || '',
        '單位': row.unit || '',
        '實用面積（平方呎）': row.area || '',
        '成交價格': row.price || '',
        '成交日期': row.deal_date ? new Date(row.deal_date).toLocaleDateString('zh-HK') : '',
        '發展商': row.developer || '',
        '房屋類型': row.house_type || ''
      };
    });

    console.log('Creating Excel workbook...');
    
    // Create workbook and worksheet
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.json_to_sheet(excelData);

    // Set column widths for better readability
    worksheet['!cols'] = [
      { wch: 10 },  // 記錄類型
      { wch: 8 },   // 市
      { wch: 12 },  // 區
      { wch: 20 },  // 物業
      { wch: 25 },  // 街道及門牌
      { wch: 8 },   // 座
      { wch: 12 },  // 物業類別
      { wch: 20 },  // 大廈名稱
      { wch: 8 },   // 樓層
      { wch: 8 },   // 單位
      { wch: 15 },  // 實用面積
      { wch: 12 },  // 成交價格
      { wch: 12 },  // 成交日期
      { wch: 15 },  // 發展商
      { wch: 12 }   // 房屋類型
    ];

    // Add the worksheet to workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, '物業成交記錄');

    // Generate Excel buffer
    const buffer = XLSX.write(workbook, { 
      type: 'buffer', 
      bookType: 'xlsx'
    });

    console.log('Excel buffer created, size:', buffer.length);

    // Set response headers for Excel download
    const filename = `property_transactions_${new Date().toISOString().split('T')[0]}.xlsx`;
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    
    console.log('Sending Excel response...');
    res.end(buffer);
    console.log('Excel export completed successfully');
    
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
