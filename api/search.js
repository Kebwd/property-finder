const { Pool } = require('pg');
const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false }
});

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
  const url = `${NOMINATIM_BASE}?q=${encodeURIComponent(query)}&format=json&limit=1`;
  const res = await fetch(url, { headers: { 'User-Agent': 'YourApp/1.0' } });
  if (!res.ok) throw new Error(`Nominatim HTTP ${res.status}`);
  const data = await res.json();
  if (data.length === 0) return null;
  return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
}

async function tryGoogle(query) {
  const key = process.env.GEOCODING_API_KEY;
  const url = `${GOOGLE_BASE}?address=${encodeURIComponent(query)}&components=country:HK&key=${key}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Google HTTP ${res.status}`);
  const body = await res.json();
  if (body.status !== 'OK' || !body.results.length) return null;
  const loc = body.results[0].geometry.location;
  return { lat: loc.lat, lng: loc.lng };
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
async function findLocationInDealTracking(query) {
  try {
    // Try multiple possible paths for Vercel deployment
    const possiblePaths = [
      path.join(process.cwd(), '../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../../scraper/deal_tracking.json'),
      path.join(process.cwd(), 'scraper/deal_tracking.json'),
      '/tmp/deal_tracking.json'  // In case it's copied to tmp
    ];

    let dealTrackingPath = null;
    for (const testPath of possiblePaths) {
      if (fs.existsSync(testPath)) {
        dealTrackingPath = testPath;
        console.log(`Found deal tracking file at: ${testPath}`);
        break;
      }
    }

    if (!dealTrackingPath) {
      console.log('Deal tracking file not found in any expected location');
      return null;
    }

    const data = JSON.parse(fs.readFileSync(dealTrackingPath, 'utf8'));
    const deals = data.current_deals || [];

    console.log(`Searching ${deals.length} deals for query: "${query}"`);

    // Search for query in deal strings with improved matching
    for (const dealString of deals) {
      const parts = dealString.split('_');
      if (parts.length < 2) continue;

      const building = parts[0];
      const fullAddress = parts[1];

      console.log(`Checking deal: ${building} -> ${fullAddress}`);

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
        console.log(`Found matching deal: ${dealString}`);

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

        console.log(`Using coordinates for ${location}: ${lat}, ${lng}`);
        return { lat, lng, source: 'deal_tracking', deal: dealString };
      }
    }

    console.log(`No matching deals found for query: "${query}"`);
    return null;

  } catch (err) {
    console.error('Deal tracking search error:', err);
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
      radius = 3000
    } = req.query;

    console.log('Parsed params:', { q, type, page, limit, lat, lng, radius });

    let searchLat, searchLng;

    // If query provided, geocode it first
    if (q && q.trim()) {
      try {
        const coords = await geocode(q.trim());
        searchLat = coords.lat;
        searchLng = coords.lng;
        console.log('Geocoded coordinates:', coords);
      } catch (geocodeErr) {
        console.warn('Geocoding failed, trying deal tracking fallback:', geocodeErr.message);

        // Try to find location in deal tracking
        const dealCoords = await findLocationInDealTracking(q.trim());
        if (dealCoords) {
          searchLat = dealCoords.lat;
          searchLng = dealCoords.lng;
          console.log(`Found location in deal tracking: ${searchLat}, ${searchLng} from deal: ${dealCoords.deal}`);
        } else {
          // Try with normalized query as well
          const normalizedQuery = normalizeEstateName(q.trim());
          if (normalizedQuery !== q.trim()) {
            console.log(`Trying normalized query: "${normalizedQuery}"`);
            const normalizedCoords = await findLocationInDealTracking(normalizedQuery);
            if (normalizedCoords) {
              searchLat = normalizedCoords.lat;
              searchLng = normalizedCoords.lng;
              console.log(`Found location with normalized query: ${searchLat}, ${searchLng}`);
            } else {
              return res.status(404).json({
                error: `Could not find location "${q.trim()}" in geocoding services or deal tracking`,
                geocoding_error: geocodeErr.message,
                normalized_query: normalizedQuery,
                available_deals: await getAvailableDeals()
              });
            }
          } else {
            return res.status(404).json({
              error: `Could not find location "${q.trim()}" in geocoding services or deal tracking`,
              geocoding_error: geocodeErr.message,
              available_deals: await getAvailableDeals()
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

    // Geospatial search query
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
      ) AS combined_results
      ORDER BY distance
      LIMIT $4 OFFSET $5
    `;

    const queryParams = [searchLat, searchLng, searchRadius, parseInt(limit), offset];
    const result = await pool.query(query, queryParams);

    res.status(200).json({
      success: true,
      data: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: result.rows.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Search API error:', error);
    console.error('Error stack:', error.stack);
    console.error('Query params:', req.query);
    res.status(500).json({
      success: false,
      error: error.message || 'Internal server error',
      details: error.stack,
      timestamp: new Date().toISOString()
    });
  }
};
