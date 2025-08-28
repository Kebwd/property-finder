const { Pool } = require('pg');
const https = require('https');
const fs = require('fs');
const path = require('path');

// Initialize pool only if DATABASE_URL is available
let pool = null;
if (process.env.DATABASE_URL) {
  pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: { rejectUnauthorized: false }
  });
} else {
  console.log('DATABASE_URL not set - database functionality disabled');
}

// Geocoding functions
const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search';
const GOOGLE_BASE = 'https://maps.googleapis.com/maps/api/geocode/json';

// Normalize estate-style input for geocoding
function normalizeEstateName(query) {
  return query
    .replace(/\s*中層\s*/g, ' ')     // remove middle floor
    .replace(/\s*高層\s*/g, ' ')     // remove high floor
    .replace(/\s*低層\s*/g, ' ')     // remove low floor
    .replace(/\s*\d+樓[A-Za-z]*\s*/g, ' ')  // remove floor numbers and unit letters
    .replace(/\s*\d+室\s*/g, ' ')    // remove room numbers
    .replace(/\s+/g, ' ')            // normalize whitespace
    .trim();
}

async function tryNominatim(query) {
  return new Promise((resolve, reject) => {
    const url = `${NOMINATIM_BASE}?q=${encodeURIComponent(query)}&format=json&limit=1`;
    const urlObj = new URL(url);

    const options = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers: {
        'User-Agent': 'YourApp/1.0'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          if (res.statusCode !== 200) {
            reject(new Error(`Nominatim HTTP ${res.statusCode}`));
            return;
          }

          const jsonData = JSON.parse(data);
          if (jsonData.length === 0) {
            resolve(null);
            return;
          }

          resolve({
            lat: parseFloat(jsonData[0].lat),
            lng: parseFloat(jsonData[0].lon)
          });
        } catch (err) {
          reject(err);
        }
      });
    });

    req.on('error', (err) => {
      reject(err);
    });

    req.end();
  });
}

async function tryGoogle(query) {
  return new Promise((resolve, reject) => {
    const key = process.env.GEOCODING_API_KEY;
    if (!key) {
      console.log('No Google Maps API key available');
      resolve(null);
      return;
    }

    const url = `${GOOGLE_BASE}?address=${encodeURIComponent(query)}&components=country:HK&key=${key}`;
    const urlObj = new URL(url);

    const options = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: 'GET'
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          if (res.statusCode !== 200) {
            reject(new Error(`Google HTTP ${res.statusCode}`));
            return;
          }

          const jsonData = JSON.parse(data);
          if (jsonData.status !== 'OK' || !jsonData.results || jsonData.results.length === 0) {
            resolve(null);
            return;
          }

          const loc = jsonData.results[0].geometry.location;
          resolve({
            lat: loc.lat,
            lng: loc.lng
          });
        } catch (err) {
          reject(err);
        }
      });
    });

    req.on('error', (err) => {
      reject(err);
    });

    req.end();
  });
}

async function geocode(query) {
  if (!query.trim()) {
    throw new Error('Please enter a location');
  }

  console.log(`Attempting to geocode: "${query}"`);

  // Try different variations of the query
  const queryVariations = [
    query,
    normalizeEstateName(query),
    `${normalizeEstateName(query)}, Hong Kong`,
    `${query}, Hong Kong`,
    // For Chinese addresses, try English translation
    query.replace('荃灣', 'Tsuen Wan').replace('國際企業中心', 'International Enterprise Centre'),
    `${query.replace('荃灣', 'Tsuen Wan').replace('國際企業中心', 'International Enterprise Centre')}, Hong Kong`
  ];

  // Try Nominatim with different variations
  for (const variation of queryVariations) {
    try {
      console.log(`Trying Nominatim with: "${variation}"`);
      const result = await tryNominatim(variation);
      if (result) {
        console.log(`Nominatim success: ${result.lat}, ${result.lng}`);
        return result;
      }
    } catch (err) {
      console.log(`Nominatim failed for "${variation}": ${err.message}`);
    }
  }

  // Try Google Maps with different variations
  for (const variation of queryVariations) {
    try {
      console.log(`Trying Google Maps with: "${variation}"`);
      const result = await tryGoogle(variation);
      if (result) {
        console.log(`Google Maps success: ${result.lat}, ${result.lng}`);
        return result;
      }
    } catch (err) {
      console.log(`Google Maps failed for "${variation}": ${err.message}`);
    }
  }

  console.log(`All geocoding attempts failed for: "${query}"`);
  throw new Error('Geocoding failed for: ' + query);
}

// Helper function to get available deals for debugging
async function getAvailableDeals() {
  try {
    const possiblePaths = [
      path.join(process.cwd(), 'deal_tracking.json'),  // Local copy in api directory (highest priority)
      path.join(process.cwd(), '../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../../scraper/deal_tracking.json'),
      path.join(process.cwd(), 'scraper/deal_tracking.json'),
      '/tmp/deal_tracking.json'
    ];

    for (const testPath of possiblePaths) {
      if (fs.existsSync(testPath)) {
        const data = JSON.parse(fs.readFileSync(testPath, 'utf8'));
        return (data.current_deals || []).map(deal => deal.split('_')[0]);
      }
    }
    return [];
  } catch (err) {
    console.error('Error getting available deals:', err);
    return [];
  }
}
// Find location_info IDs that look like the query (exact then wildcard)
async function findLocationInfoIds(query) {
  if (!query || !pool) return [];
  const qText = query.trim();
  if (!qText) return [];
  try {
    // Try exact matches first on common address fields
    const exactSql = `
      SELECT id FROM location_info
      WHERE LOWER(town) = LOWER($1)
         OR LOWER(street) = LOWER($1)
         OR LOWER(CONCAT(town, ' ', street)) = LOWER($1)
      LIMIT 10
    `;
    let res = await pool.query(exactSql, [qText]);
    if (res.rows && res.rows.length) return res.rows.map(r => r.id);

    // Fallback to wildcard search
    const likeSql = `
      SELECT id FROM location_info
      WHERE town ILIKE $1 OR street ILIKE $1 OR CONCAT(town, ' ', street) ILIKE $1
      LIMIT 50
    `;
    res = await pool.query(likeSql, [`%${qText}%`]);
    return (res.rows || []).map(r => r.id);
  } catch (err) {
    console.log('findLocationInfoIds error:', err.message);
    return [];
  }
}

// Fetch rows from house/business that belong to any of the given location_ids
async function fetchRowsByLocationIds(locationIds, limit) {
  if (!locationIds || !locationIds.length || !pool) return [];
  // build parameter placeholders
  const placeholders = locationIds.map((_, i) => `$${i + 1}`).join(',');
  const limitParam = `$${locationIds.length + 1}`;

  const sql = `
    SELECT * FROM (
      SELECT
        'business' AS source,
        b.id,
        b.type,
        b.building_name_zh as name,
        NULL as estate_name_zh,
        b.building_name_zh,
        b.floor,
        b.unit,
        b.area,
        b.deal_price,
        b.deal_date,
        l.province,
        l.city,
        l.town,
        l.street,
        l.lat,
        l.long,
        0 as distance
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      WHERE b.location_id IN (${placeholders})

      UNION ALL

      SELECT
        'house' AS source,
        h.id,
        h.type,
        COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
        h.estate_name_zh,
        h.building_name_zh,
        h.floor,
        h.unit,
        h.area,
        h.deal_price,
        h.deal_date,
        l.province,
        l.city,
        l.town,
        l.street,
        l.lat,
        l.long,
        0 as distance
      FROM house h
      JOIN location_info l ON h.location_id = l.id
      WHERE h.location_id IN (${placeholders})
    ) AS t
    LIMIT ${limitParam}
  `;

  const params = [...locationIds, parseInt(limit)];
  try {
    const res = await pool.query(sql, params);
    return res.rows || [];
  } catch (err) {
    console.log('fetchRowsByLocationIds error:', err.message);
    return [];
  }
}
async function checkDealTracking(query) {
  if (!query) return { found: false };
  try {
    const dealCoords = await findLocationInDealTracking(query);
    return dealCoords ? {
      found: true,
      coordinates: { lat: dealCoords.lat, lng: dealCoords.lng },
      deal: dealCoords.deal
    } : { found: false };
  } catch (err) {
    return { found: false, error: err.message };
  }
}

// Run prioritized text search (exact -> normalized exact -> wildcard) and return rows
async function runTextSearchPrimary(qText, limitParam) {
  if (!pool || !qText || qText.length < 2) return [];
  try {
    const limit = parseInt(limitParam) || 20;
    // exact
    const exactSql = `
      SELECT * FROM (
        SELECT
          'business' AS source,
          b.id,
          b.type,
          b.building_name_zh as name,
          NULL as estate_name_zh,
          b.building_name_zh,
          b.floor,
          b.unit,
          b.area,
          b.deal_price,
          b.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          0 as distance
        FROM business b
        JOIN location_info l ON b.location_id = l.id
        WHERE (LOWER(b.building_name_zh) = LOWER($1) OR LOWER(b.building_name) = LOWER($1))

        UNION ALL

        SELECT
          'house' AS source,
          h.id,
          h.type,
          COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
          h.estate_name_zh,
          h.building_name_zh,
          h.floor,
          h.unit,
          h.area,
          h.deal_price,
          h.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          0 as distance
        FROM house h
        JOIN location_info l ON h.location_id = l.id
        WHERE (LOWER(h.estate_name_zh) = LOWER($1) OR LOWER(h.building_name_zh) = LOWER($1) OR LOWER(h.building_name) = LOWER($1))
      ) AS t
      LIMIT $2
    `;

    let textRes = await pool.query(exactSql, [qText, limit]);
    if (textRes.rows && textRes.rows.length) return textRes.rows;

    // normalized exact
    const normExactSql = `
      SELECT * FROM (
        SELECT
          'business' AS source,
          b.id,
          b.type,
          b.building_name_zh as name,
          NULL as estate_name_zh,
          b.building_name_zh,
          b.floor,
          b.unit,
          b.area,
          b.deal_price,
          b.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          0 as distance
        FROM business b
        JOIN location_info l ON b.location_id = l.id
        WHERE LOWER(REPLACE(b.building_name_zh, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
           OR LOWER(REPLACE(b.building_name, ' ', '')) = LOWER(REPLACE($1, ' ', ''))

        UNION ALL

        SELECT
          'house' AS source,
          h.id,
          h.type,
          COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
          h.estate_name_zh,
          h.building_name_zh,
          h.floor,
          h.unit,
          h.area,
          h.deal_price,
          h.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          0 as distance
        FROM house h
        JOIN location_info l ON h.location_id = l.id
        WHERE LOWER(REPLACE(h.estate_name_zh, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
           OR LOWER(REPLACE(h.building_name_zh, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
           OR LOWER(REPLACE(h.building_name, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
      ) AS t
      LIMIT $2
    `;

    const normRes = await pool.query(normExactSql, [qText, limit]);
    if (normRes.rows && normRes.rows.length) return normRes.rows;

    // wildcard
    const textSql = `
      SELECT * FROM (
        SELECT
          'business' AS source,
          b.id,
          b.type,
          b.building_name_zh as name,
          NULL as estate_name_zh,
          b.building_name_zh,
          b.floor,
          b.unit,
          b.area,
          b.deal_price,
          b.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          0 as distance
        FROM business b
        JOIN location_info l ON b.location_id = l.id
        WHERE (b.building_name_zh ILIKE $1 OR b.building_name ILIKE $1)

        UNION ALL

        SELECT
          'house' AS source,
          h.id,
          h.type,
          COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
          h.estate_name_zh,
          h.building_name_zh,
          h.floor,
          h.unit,
          h.area,
          h.deal_price,
          h.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          0 as distance
        FROM house h
        JOIN location_info l ON h.location_id = l.id
        WHERE (h.estate_name_zh ILIKE $1 OR h.building_name_zh ILIKE $1 OR h.building_name ILIKE $1)
      ) AS t
      LIMIT $2
    `;

    const wildRes = await pool.query(textSql, [`%${qText}%`, limit]);
    return wildRes.rows || [];
  } catch (err) {
    console.log('runTextSearchPrimary error:', err.message);
    return [];
  }
}
async function findLocationInDealTracking(query) {
  console.log(`🔍 Searching deal tracking for: "${query}"`);
  console.log(`📂 Current working directory: ${process.cwd()}`);

  try {
    // Try multiple possible paths for Vercel deployment
    const possiblePaths = [
      path.join(process.cwd(), 'deal_tracking.json'),  // Local copy in api directory (highest priority)
      path.join(process.cwd(), '../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../../scraper/deal_tracking.json'),
      path.join(process.cwd(), 'scraper/deal_tracking.json'),
      '/tmp/deal_tracking.json'  // In case it's copied to tmp
    ];

    console.log('🔍 Checking possible paths:');
    possiblePaths.forEach(p => console.log(`   - ${p}`));

    let dealTrackingPath = null;
    for (const testPath of possiblePaths) {
      console.log(`🔍 Checking: ${testPath}`);
      if (fs.existsSync(testPath)) {
        dealTrackingPath = testPath;
        console.log(`✅ Found deal tracking file at: ${testPath}`);
        break;
      } else {
        console.log(`❌ Not found: ${testPath}`);
      }
    }

    if (!dealTrackingPath) {
      console.log('❌ Deal tracking file not found in any expected location');
      return null;
    }

    const data = JSON.parse(fs.readFileSync(dealTrackingPath, 'utf8'));
    const deals = data.current_deals || [];

    console.log(`📋 Found ${deals.length} deals in file`);

    // Search for query in deal strings with improved matching
    for (const dealString of deals) {
      const parts = dealString.split('_');
      if (parts.length < 2) continue;

      const building = parts[0];
      const fullAddress = parts[1];

      console.log(`🔍 Checking deal: ${building} -> ${fullAddress}`);

      // Multiple matching strategies
      const matches = [
        // Exact building match
        building === query,
        // Query contains building
        query.includes(building),
        // Building contains query
        building.includes(query),
        // Full address contains query
        fullAddress.includes(query),
        // Query contains part of address
        query.split(' ').some(word => fullAddress.includes(word) && word.length > 2)
      ];

      if (matches.some(match => match)) {
        console.log(`✅ Found matching deal: ${dealString}`);

        // Extract location info from deal string
        const location = parts[1];

        // Use coordinates based on location keywords
        let lat = 22.3686, lng = 114.1048; // Default Tsuen Wan coordinates

        if (location.includes('荃灣') || location.includes('Tsuen Wan')) {
          lat = 22.3686; lng = 114.1048; // Tsuen Wan
        } else if (location.includes('中環') || location.includes('Central')) {
          lat = 22.2819; lng = 114.1588; // Central
        } else if (location.includes('尖沙咀') || location.includes('Tsim Sha Tsui')) {
          lat = 22.2969; lng = 114.1722; // Tsim Sha Tsui
        } else if (location.includes('上環') || location.includes('Sheung Wan')) {
          lat = 22.2867; lng = 114.1491; // Sheung Wan
        } else if (location.includes('元朗') || location.includes('Yuen Long')) {
          lat = 22.4414; lng = 114.0222; // Yuen Long
        }

        console.log(`📍 Using coordinates for ${location}: ${lat}, ${lng}`);
        return { lat, lng, source: 'deal_tracking', deal: dealString };
      }
    }

    console.log(`❌ No matching deals found for query: "${query}"`);
    return null;

  } catch (err) {
    console.error('❌ Deal tracking search error:', err);
    return null;
  }
}

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
    console.log('Search API called with query params:', req.query);


    const {
      q,  // Add query parameter for geocoding
      type = 'all',
      page = 1,
      limit = 20,
      lat,
      lng,
      radius = 4000,
      date_from,
      date_to
    } = req.query;

    console.log('Parsed params:', { q, type, page, limit, lat, lng, radius });

  let searchLat, searchLng;
  // Extra debug info collected during processing
  const debugExtras = {};


    // Always geocode if query is provided
    if (q && q.trim()) {
      try {
        const coords = await geocode(q.trim());
        searchLat = coords.lat;
        searchLng = coords.lng;
        console.log('✅ Geocoding successful:', coords);
      } catch (geocodeErr) {
        console.warn('❌ Geocoding failed:', geocodeErr.message);
        console.log('🔄 Trying deal tracking fallback...');
        // Try to find location in deal tracking
        const dealCoords = await findLocationInDealTracking(q.trim());
        if (dealCoords) {
          searchLat = dealCoords.lat;
          searchLng = dealCoords.lng;
          console.log(`✅ Found location in deal tracking: ${searchLat}, ${searchLng} from deal: ${dealCoords.deal}`);
        } else {
          console.log('❌ Deal tracking also failed');
          // Try with normalized query as well
          const normalizedQuery = normalizeEstateName(q.trim());
          if (normalizedQuery !== q.trim()) {
            console.log(`🔄 Trying normalized query: "${normalizedQuery}"`);
            const normalizedCoords = await findLocationInDealTracking(normalizedQuery);
            if (normalizedCoords) {
              searchLat = normalizedCoords.lat;
              searchLng = normalizedCoords.lng;
              console.log(`✅ Found location with normalized query: ${searchLat}, ${searchLng}`);
            } else {
              console.log('❌ Normalized query also failed');
              return res.status(404).json({
                error: `Could not find location "${q.trim()}" in geocoding services or deal tracking`,
                geocoding_error: geocodeErr.message,
                normalized_query: normalizedQuery,
                available_deals: await getAvailableDeals(),
                deal_tracking_check: await checkDealTracking(q)
              });
            }
          } else {
            console.log('❌ No fallback options available');
            return res.status(404).json({
              error: `Could not find location "${q.trim()}" in geocoding services or deal tracking`,
              geocoding_error: geocodeErr.message,
              available_deals: await getAvailableDeals(),
              deal_tracking_check: await checkDealTracking(q)
            });
          }
        }
      }
    } else if (lat && lng) {
      // Use provided coordinates
      searchLat = parseFloat(lat);
      searchLng = parseFloat(lng);
      if (isNaN(searchLat) || isNaN(searchLng)) {
        return res.status(400).json({ error: 'Invalid latitude or longitude' });
      }
    } else {
      return res.status(400).json({ error: 'Please provide either a query (q) or lat/lng coordinates' });
    }

    const offset = (parseInt(page) - 1) * parseInt(limit);
    const searchRadius = parseInt(radius);


    // Build dynamic SQL filters for type and date range
    let typeFilter = '';
    let dateFilter = '';
    let paramIdx = 6; // $1-$5 are used for lat, lng, radius, limit, offset
    const queryParams = [searchLat, searchLng, searchRadius, parseInt(limit), offset];

    if (type && type !== 'all') {
      typeFilter = ` AND b.type = $${paramIdx}`;
      queryParams.push(type);
      paramIdx++;
    }
    if (date_from) {
      dateFilter += ` AND b.deal_date >= $${paramIdx}`;
      queryParams.push(date_from);
      paramIdx++;
    }
    if (date_to) {
      dateFilter += ` AND b.deal_date <= $${paramIdx}`;
      queryParams.push(date_to);
      paramIdx++;
    }

    let typeFilterH = '';
    let dateFilterH = '';
    let paramIdxH = paramIdx;
    if (type && type !== 'all') {
      typeFilterH = ` AND h.type = $${paramIdxH}`;
      queryParams.push(type);
      paramIdxH++;
    }
    if (date_from) {
      dateFilterH += ` AND h.deal_date >= $${paramIdxH}`;
      queryParams.push(date_from);
      paramIdxH++;
    }
    if (date_to) {
      dateFilterH += ` AND h.deal_date <= $${paramIdxH}`;
      queryParams.push(date_to);
      paramIdxH++;
    }

    const query = `
      SELECT * FROM (
        SELECT
          'business' AS source,
          b.id,
          b.type,
          b.building_name_zh as name,
          NULL as estate_name_zh,
          b.building_name_zh,
          b.floor,
          b.unit,
          b.area,
          b.deal_price,
          b.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          ST_Distance(
            ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
            ST_SetSRID(ST_Point($2, $1), 4326)::geography
          ) AS distance
        FROM business b
        JOIN location_info l ON b.location_id = l.id
        WHERE ST_DWithin(
          ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
          ST_SetSRID(ST_Point($2, $1), 4326)::geography,
          $3
        )
        ${typeFilter}
        ${dateFilter}

        UNION ALL

        SELECT
          'house' AS source,
          h.id,
          h.type,
          COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
          h.estate_name_zh,
          h.building_name_zh,
          h.floor,
          h.unit,
          h.area,
          h.deal_price,
          h.deal_date,
          l.province,
          l.city,
          l.town,
          l.street,
          l.lat,
          l.long,
          ST_Distance(
            ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
            ST_SetSRID(ST_Point($2, $1), 4326)::geography
          ) AS distance
        FROM house h
        JOIN location_info l ON h.location_id = l.id
        WHERE ST_DWithin(
          ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
          ST_SetSRID(ST_Point($2, $1), 4326)::geography,
          $3
        )
        ${typeFilterH}
        ${dateFilterH}
      ) AS combined_results
      ORDER BY distance
      LIMIT $4 OFFSET $5
    `;

    // Check if database is available
    if (!pool) {
      console.log('Database not available, returning coordinates only');
      return res.status(200).json({
        success: true,
        data: [],
        debug: {
          query: q,
          coordinates: { lat: searchLat, lng: searchLng },
          source: 'deal_tracking_no_database'
        ,
          deal_tracking_check: await checkDealTracking(q)
        },
        message: 'Database not configured - deal tracking coordinates found successfully',
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total: 0
        },
        timestamp: new Date().toISOString()
      });
    }

    console.log('Database pool available, testing connection...');
    try {
      // Test database connection first
      const testClient = await pool.connect();
      await testClient.query('SELECT 1');
      testClient.release();
      console.log('Database connection test successful');
    } catch (connError) {
      console.log(`Database connection test failed: ${connError.message}`);
      // If database connection fails, try deal tracking as primary source
      if (q && q.trim()) {
        console.log('Using deal tracking as primary source due to connection failure...');
        const dealCoords = await findLocationInDealTracking(q.trim());
        if (dealCoords) {
          console.log(`Found deal tracking coordinates: ${dealCoords.lat}, ${dealCoords.lng}`);
          return res.status(200).json({
            success: true,
            data: [],
            debug: {
              query: q,
              coordinates: { lat: dealCoords.lat, lng: dealCoords.lng },
              source: 'deal_tracking_primary'
              ,
                deal_tracking_check: await checkDealTracking(q)
              },
            message: 'Database connection failed, using deal tracking coordinates',
            pagination: {
              page: parseInt(page),
              limit: parseInt(limit),
              total: 0
            },
            timestamp: new Date().toISOString()
          });
        }
      }
      return res.status(500).json({
        success: false,
        error: 'Database connection failed',
        debug: {
          query: q,
          source: 'database_connection_error'
        },
        timestamp: new Date().toISOString()
      });
    }

    console.log('Executing main database query...');
    let result;
    try {
      result = await pool.query(query, queryParams);
      console.log(`Database query returned ${result.rows.length} rows`);

      // Compute nearest DB point distance to the searched coordinates for diagnostics
      try {
        const nearSql = `
          SELECT l.lat, l.long,
            ST_Distance(
              ST_SetSRID(ST_Point(l.long, l.lat), 4326)::geography,
              ST_SetSRID(ST_Point($2, $1), 4326)::geography
            ) AS distance
          FROM location_info l
          ORDER BY distance
          LIMIT 1
        `;
        const nearRes = await pool.query(nearSql, [searchLat, searchLng]);
        if (nearRes.rows && nearRes.rows[0]) {
          console.log('Nearest DB point distance (m):', nearRes.rows[0].distance);
          // attach to result debug for later
          result.nearest_distance_m = nearRes.rows[0].distance;
        }
      } catch (nearErr) {
        console.log('Nearest-point diagnostic failed:', nearErr.message);
      }

      // If the spatial query did not return any row that matches the query text
      // (e.g., building name), run a lightweight text-search fallback to find
      // properties by name and merge them into the results. This helps when
      // geocoding places the search point away from the actual property.
      const rows = result.rows || [];
      const qText = (q || '').trim();
      try {
        const hasNameMatch = rows.some(r => {
          const candidates = [r.building_name_zh, r.estate_name_zh, r.building_name, r.name].filter(Boolean);
          return candidates.some(c => String(c).includes(qText));
        });

        if (qText && qText.length > 1 && !hasNameMatch) {
          console.log('No name match in spatial results — running prioritized text-search for:', qText);

          // 1) Try exact case-insensitive match first (prioritize exact building/estate names)
          const exactSql = `
            SELECT * FROM (
              SELECT
                'business' AS source,
                b.id,
                b.type,
                b.building_name_zh as name,
                NULL as estate_name_zh,
                b.building_name_zh,
                b.floor,
                b.unit,
                b.area,
                b.deal_price,
                b.deal_date,
                l.province,
                l.city,
                l.town,
                l.street,
                l.lat,
                l.long,
                0 as distance
              FROM business b
              JOIN location_info l ON b.location_id = l.id
              WHERE (LOWER(b.building_name_zh) = LOWER($1) OR LOWER(b.building_name) = LOWER($1))

              UNION ALL

              SELECT
                'house' AS source,
                h.id,
                h.type,
                COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
                h.estate_name_zh,
                h.building_name_zh,
                h.floor,
                h.unit,
                h.area,
                h.deal_price,
                h.deal_date,
                l.province,
                l.city,
                l.town,
                l.street,
                l.lat,
                l.long,
                0 as distance
              FROM house h
              JOIN location_info l ON h.location_id = l.id
              WHERE (LOWER(h.estate_name_zh) = LOWER($1) OR LOWER(h.building_name_zh) = LOWER($1) OR LOWER(h.building_name) = LOWER($1))
            ) AS t
            LIMIT $2
          `;

          let textRes = await pool.query(exactSql, [qText, parseInt(limit)]);
          console.log(`Exact-name text-search returned ${textRes.rows.length} rows`);
          debugExtras.exact_name_count = textRes.rows.length;

          // Attempt a normalized-exact match (strip spaces) if exact returned none
          if (!textRes.rows.length) {
            const normExactSql = `
              SELECT * FROM (
                SELECT
                  'business' AS source,
                  b.id,
                  b.type,
                  b.building_name_zh as name,
                  NULL as estate_name_zh,
                  b.building_name_zh,
                  b.floor,
                  b.unit,
                  b.area,
                  b.deal_price,
                  b.deal_date,
                  l.province,
                  l.city,
                  l.town,
                  l.street,
                  l.lat,
                  l.long,
                  0 as distance
                FROM business b
                JOIN location_info l ON b.location_id = l.id
                WHERE LOWER(REPLACE(b.building_name_zh, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
                   OR LOWER(REPLACE(b.building_name, ' ', '')) = LOWER(REPLACE($1, ' ', ''))

                UNION ALL

                SELECT
                  'house' AS source,
                  h.id,
                  h.type,
                  COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
                  h.estate_name_zh,
                  h.building_name_zh,
                  h.floor,
                  h.unit,
                  h.area,
                  h.deal_price,
                  h.deal_date,
                  l.province,
                  l.city,
                  l.town,
                  l.street,
                  l.lat,
                  l.long,
                  0 as distance
                FROM house h
                JOIN location_info l ON h.location_id = l.id
                WHERE LOWER(REPLACE(h.estate_name_zh, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
                   OR LOWER(REPLACE(h.building_name_zh, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
                   OR LOWER(REPLACE(h.building_name, ' ', '')) = LOWER(REPLACE($1, ' ', ''))
              ) AS t
              LIMIT $2
            `;
            const normRes = await pool.query(normExactSql, [qText, parseInt(limit)]);
            console.log(`Normalized-exact text-search returned ${normRes.rows.length} rows`);
            debugExtras.normalized_exact_count = normRes.rows.length;
            if (normRes.rows.length) textRes = normRes;
          }

          // 2) If no exact matches, run the looser wildcard ILIKE search
          if (!textRes.rows.length) {
            console.log('No exact-name matches found, running wildcard ILIKE text search');
            const textSql = `
              SELECT * FROM (
                SELECT
                  'business' AS source,
                  b.id,
                  b.type,
                  b.building_name_zh as name,
                  NULL as estate_name_zh,
                  b.building_name_zh,
                  b.floor,
                  b.unit,
                  b.area,
                  b.deal_price,
                  b.deal_date,
                  l.province,
                  l.city,
                  l.town,
                  l.street,
                  l.lat,
                  l.long,
                  0 as distance
                FROM business b
                JOIN location_info l ON b.location_id = l.id
                WHERE (b.building_name_zh ILIKE $1 OR b.building_name ILIKE $1)

                UNION ALL

                SELECT
                  'house' AS source,
                  h.id,
                  h.type,
                  COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name,
                  h.estate_name_zh,
                  h.building_name_zh,
                  h.floor,
                  h.unit,
                  h.area,
                  h.deal_price,
                  h.deal_date,
                  l.province,
                  l.city,
                  l.town,
                  l.street,
                  l.lat,
                  l.long,
                  0 as distance
                FROM house h
                JOIN location_info l ON h.location_id = l.id
                WHERE (h.estate_name_zh ILIKE $1 OR h.building_name_zh ILIKE $1 OR h.building_name ILIKE $1)
              ) AS t
              LIMIT $2
            `;

            textRes = await pool.query(textSql, [`%${qText}%`, parseInt(limit)]);
            console.log(`Wildcard text-search returned ${textRes.rows.length} rows`);
            debugExtras.wildcard_count = textRes.rows.length;
          }

          // Merge unique rows (by source + id)
          const existing = new Set(rows.map(r => `${r.source}_${r.id}`));
          for (const r of (textRes.rows || [])) {
            const key = `${r.source}_${r.id}`;
            if (!existing.has(key)) {
              rows.push(r);
              existing.add(key);
            }
          }
          // Replace result.rows with merged rows
          result.rows = rows;
          debugExtras.merged_text_fallback = (textRes.rows || []).length;
          // If still not containing an exact-name or if user expects a location-name match,
          // try searching `location_info` table first and fetch associated rows by location_id.
          try {
            // 1. Find all properties where building_name_zh ILIKE %query%
            const broadNameSql = `
              SELECT * FROM (
                SELECT 'business' AS source, b.id, b.type, b.building_name_zh as name, NULL as estate_name_zh, b.building_name_zh, b.floor, b.unit, b.area, b.deal_price, b.deal_date, l.province, l.city, l.town, l.street, l.lat, l.long, 0 as distance
                FROM business b JOIN location_info l ON b.location_id = l.id
                WHERE b.building_name_zh ILIKE $1
                UNION ALL
                SELECT 'house' AS source, h.id, h.type, COALESCE(NULLIF(h.estate_name_zh, ''), NULLIF(h.building_name_zh, ''), h.building_name_zh) as name, h.estate_name_zh, h.building_name_zh, h.floor, h.unit, h.area, h.deal_price, h.deal_date, l.province, l.city, l.town, l.street, l.lat, l.long, 0 as distance
                FROM house h JOIN location_info l ON h.location_id = l.id
                WHERE h.building_name_zh ILIKE $1 OR h.estate_name_zh ILIKE $1
              ) AS t
              LIMIT 200
            `;
            const broadNameRows = (await pool.query(broadNameSql, [`%${qText}%`])).rows || [];
            debugExtras.broad_name_count = broadNameRows.length;

            // 2. Find location_info IDs by text (town/city/street)
            const locationIds = await findLocationInfoIds(qText);
            debugExtras.location_info_ids = locationIds;
            let locRows = [];
            if (locationIds && locationIds.length) {
              console.log('Found location_info IDs for query, fetching associated rows:', locationIds.slice(0,10));
              locRows = await fetchRowsByLocationIds(locationIds, 200);
              debugExtras.location_rows_count = locRows.length;
            }

            // 3. If geocoded, find all location_info within 4km (spatial fallback)
            let spatialRows = [];
            if (searchLat && searchLng) {
              const spatialSql = `
                SELECT id FROM location_info
                WHERE ST_DWithin(
                  ST_SetSRID(ST_Point(long, lat), 4326)::geography,
                  ST_SetSRID(ST_Point($2, $1), 4326)::geography,
                  4000
                )
                LIMIT 200
              `;
              const spatialIds = (await pool.query(spatialSql, [searchLat, searchLng])).rows.map(r => r.id);
              if (spatialIds.length) {
                spatialRows = await fetchRowsByLocationIds(spatialIds, 200);
                debugExtras.spatial_rows_count = spatialRows.length;
              }
            }

            // 4. If query matches dist or geom in location_info (as string)
            let distRows = [];
            const distSql = `SELECT id FROM location_info WHERE dist ILIKE $1 OR CAST(geom AS TEXT) ILIKE $1 LIMIT 200`;
            const distIds = (await pool.query(distSql, [`%${qText}%`])).rows.map(r => r.id);
            if (distIds.length) {
              distRows = await fetchRowsByLocationIds(distIds, 200);
              debugExtras.dist_rows_count = distRows.length;
            }

            // Merge all fallback rows and dedupe by source+id
            const allFallbackRows = [...broadNameRows, ...locRows, ...spatialRows, ...distRows];
            const existing = new Set(result.rows.map(r => `${r.source}_${r.id}`));
            const merged = [];
            for (const r of allFallbackRows) {
              const key = `${r.source}_${r.id}`;
              if (!existing.has(key)) {
                merged.push(r);
                existing.add(key);
              }
            }
            for (const r of result.rows) merged.push(r);
            result.rows = merged;
          } catch (locErr) {
            console.log('location_info/broad fallback failed:', locErr.message);
          }
        }
      } catch (textErr) {
        console.log('Text-search fallback failed:', textErr.message);
      }
    } catch (dbError) {
      console.log(`Main database query failed: ${dbError.message}`);
      // If database fails completely, try deal tracking as primary source
      if (q && q.trim()) {
        console.log('Trying deal tracking as primary source due to query failure...');
        const dealCoords = await findLocationInDealTracking(q.trim());
        if (dealCoords) {
          console.log(`Found deal tracking coordinates: ${dealCoords.lat}, ${dealCoords.lng}`);
          return res.status(200).json({
            success: true,
            data: [],
            debug: {
              query: q,
              coordinates: { lat: dealCoords.lat, lng: dealCoords.lng },
              source: 'deal_tracking_primary'
              ,
                deal_tracking_check: await checkDealTracking(q)
              },
            message: 'Database query failed, using deal tracking coordinates',
            pagination: {
              page: parseInt(page),
              limit: parseInt(limit),
              total: 0
            },
            timestamp: new Date().toISOString()
          });
        }
      }
      // If no deal tracking, return error
      return res.status(500).json({
        success: false,
        error: 'Database query failed and no deal tracking available',
        debug: {
          query: q,
          source: 'database_query_error'
        },
        timestamp: new Date().toISOString()
      });
    }

    // Check if we should use deal tracking instead
    const dealCheck = await checkDealTracking(q);
    const shouldUseDealTracking = result.rows.length === 0 && dealCheck.found;

    if (shouldUseDealTracking) {
      console.log('Using deal tracking coordinates instead of empty database results');
      return res.status(200).json({
        success: true,
        data: [],
        debug: {
          query: q,
          original_coordinates: { lat: searchLat, lng: searchLng },
          deal_tracking_coordinates: dealCheck.coordinates,
          source: 'deal_tracking_fallback_empty_db'
        ,
          debugExtras: debugExtras || {},
          nearest_distance_m: result.nearest_distance_m || null
        },
        message: 'Database returned no results, using deal tracking coordinates',
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total: 0
        },
        timestamp: new Date().toISOString()
      });
    }

    // Group by location_id to collapse units into one building row
    const grouped = new Map();
    for (const r of result.rows) {
      const lid = r.location_id;
      if (!grouped.has(lid)) {
        grouped.set(lid, { ...r, units_count: 0, sample_units: [] });
      }
      const g = grouped.get(lid);
      g.units_count += 1;
      if (g.sample_units.length < 3) g.sample_units.push({ id: r.id, floor: r.floor, unit: r.unit, type: r.source });
    }
    const groupedRows = Array.from(grouped.values());

    res.status(200).json({
      success: true,
      data: groupedRows,
      debug: {
        query: q,
        coordinates: { lat: searchLat, lng: searchLng },
        source: 'database_query',
        row_count: groupedRows.length,
        deal_tracking_check: dealCheck,
        debugExtras: debugExtras || {},
        nearest_distance_m: result.nearest_distance_m || null,
        grouped_by_location_id: true
      },
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: groupedRows.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Search API error:', error);
    console.error('Error stack:', error.stack);
    console.error('Query params:', req.query);

    // Check if this is a database connection error
    if (error.message && error.message.includes('connect')) {
      console.log('Database connection error - returning deal tracking coordinates only');
      return res.status(200).json({
        success: true,
        data: [],
        debug: {
          query: q,
          coordinates: { lat: searchLat, lng: searchLng },
          source: 'deal_tracking_database_error'
        ,
          deal_tracking_check: await checkDealTracking(q)
        },
        coordinates: { lat: searchLat, lng: searchLng },
        source: 'deal_tracking_fallback',
        message: 'Database connection failed, but deal tracking coordinates found successfully',
        error: error.message,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total: 0
        },
        timestamp: new Date().toISOString()
      });
    }

    res.status(500).json({
      success: false,
      error: error.message || 'Internal server error',
      details: error.stack,
      timestamp: new Date().toISOString()
    });
  }
};
