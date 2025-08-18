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

    // Determine which tables to search based on type
    if (type === 'business' || type === 'commercial') {
      // Search only business table
      query = `
        SELECT 
          'business' as source,
          b.id,
          b.type,
          b.building_name_zh as estate_name_zh,
          '' as flat,
          b.building_name_zh,
          b.floor,
          b.unit,
          b.area,
          b.type as house_type,
          b.deal_price as price,
          b.deal_date,
          '' as developer,
          l.province,
          l.city,
          l.town as district,
          l.street,
          l.road,
          l.lat as latitude,
          l.long as longitude,
          CONCAT(l.province, l.city, l.town, l.street, l.road) as address
        FROM business b
        JOIN location_info l ON b.location_id = l.id
        WHERE 1=1
      `;
    } else if (type === 'house' || type === 'residential') {
      // Search only house table
      query = `
        SELECT 
          'house' as source,
          h.id,
          h.type,
          h.estate_name_zh,
          h.flat,
          h.building_name_zh,
          h.floor,
          h.unit,
          h.area,
          h.house_type,
          h.deal_price as price,
          h.deal_date,
          h.developer,
          l.province,
          l.city,
          l.town as district,
          l.street,
          l.road,
          l.lat as latitude,
          l.long as longitude,
          CONCAT(l.province, l.city, l.town, l.street, l.road) as address
        FROM house h
        JOIN location_info l ON h.location_id = l.id
        WHERE 1=1
      `;
    } else {
      // Search both tables
      query = `
        SELECT 
          'house' as source,
          h.id,
          h.type,
          h.estate_name_zh,
          h.flat,
          h.building_name_zh,
          h.floor,
          h.unit,
          h.area,
          h.house_type,
          h.deal_price as price,
          h.deal_date,
          h.developer,
          l.province,
          l.city,
          l.town as district,
          l.street,
          l.road,
          l.lat as latitude,
          l.long as longitude,
          CONCAT(l.province, l.city, l.town, l.street, l.road) as address
        FROM house h
        JOIN location_info l ON h.location_id = l.id
        WHERE 1=1
        
        UNION ALL
        
        SELECT 
          'business' as source,
          b.id,
          b.type,
          b.estate_name_zh,
          b.flat,
          b.building_name_zh,
          b.floor,
          b.unit,
          b.area,
          b.business_type as house_type,
          b.deal_price as price,
          b.deal_date,
          b.developer,
          l.province,
          l.city,
          l.town as district,
          l.street,
          l.road,
          l.lat as latitude,
          l.long as longitude,
          CONCAT(l.province, l.city, l.town, l.street, l.road) as address
        FROM business b
        JOIN location_info l ON b.location_id = l.id
        WHERE 1=1
      `;
    }

    // Add address filter if provided
    if (address && address.trim()) {
      const addressFilter = ` AND (
        l.town ILIKE $${paramIndex} OR 
        l.street ILIKE $${paramIndex} OR 
        l.road ILIKE $${paramIndex} OR
        estate_name_zh ILIKE $${paramIndex} OR
        building_name_zh ILIKE $${paramIndex}
      )`;
      
      if (type === 'all') {
        // For UNION query, we need to add the filter to both parts
        query = query.replace(/WHERE 1=1/g, `WHERE 1=1 ${addressFilter}`);
      } else {
        query += addressFilter;
      }
      
      queryParams.push(`%${address.trim()}%`);
      paramIndex++;
    }

    // Add type filter if provided
    if (category && category !== '全部') {
      const typeFilter = ` AND type = $${paramIndex}`;
      
      if (type === 'all') {
        query = query.replace(/WHERE 1=1/g, `WHERE 1=1 ${typeFilter}`);
      } else {
        query += typeFilter;
      }
      
      queryParams.push(category);
      paramIndex++;
    }

    // Add date filter if provided
    if (filter_date) {
      const dateFilter = ` AND deal_date >= $${paramIndex}`;
      
      if (type === 'all') {
        query = query.replace(/WHERE 1=1/g, `WHERE 1=1 ${dateFilter}`);
      } else {
        query += dateFilter;
      }
      
      queryParams.push(filter_date);
      paramIndex++;
    }

    // Add ordering and pagination
    query += ` ORDER BY deal_date DESC, id DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    queryParams.push(parseInt(limit), offset);

    const client = await pool.connect();
    const result = await client.query(query, queryParams);
    
    // Get total count for pagination (simplified count query)
    let countQuery;
    if (type === 'business' || type === 'commercial') {
      countQuery = 'SELECT COUNT(*) FROM business b JOIN location_info l ON b.location_id = l.id WHERE 1=1';
    } else if (type === 'house' || type === 'residential') {
      countQuery = 'SELECT COUNT(*) FROM house h JOIN location_info l ON h.location_id = l.id WHERE 1=1';
    } else {
      countQuery = `
        SELECT (
          (SELECT COUNT(*) FROM house h JOIN location_info l ON h.location_id = l.id WHERE 1=1) +
          (SELECT COUNT(*) FROM business b JOIN location_info l ON b.location_id = l.id WHERE 1=1)
        ) as count
      `;
    }
    
    const countResult = await client.query(countQuery);
    
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
