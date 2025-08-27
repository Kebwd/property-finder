// store-finder-api/src/routes/business.js
import express from 'express';
import pool from '../db.js';
import { geocode } from '../utils.js';
import multer from 'multer';
import copyStreams from 'pg-copy-streams';
import { Transform } from 'stream';

const { to: copyTo } = copyStreams;
const router = express.Router();
//const upload = multer({ storage: multer.memoryStorage() });
const upload = multer({ dest: 'uploads' });

// Fallback function to find location in database by name
async function findLocationInDB(query) {
  try {
    // Normalize the query for database search
    const normalized = query
      .replace(/\d+號/g, '')     // remove building numbers
      .replace(/第?\d+座/g, '')   // remove block numbers
      .replace(/\d+樓[A-Za-z]*/g, '')     // remove floor numbers and unit letters
      .replace(/\d+室/g, '')     // remove room numbers
      .replace(/中層|高層|低層/g, '') // remove floor level descriptions
      .replace(/\s+/g, ' ')      // normalize whitespace
      .trim();
    
    // Try multiple search strategies
    const searchTerms = [query, normalized];
    
    // Extract key location terms (remove district prefixes for broader search)
    if (query.includes('荃灣')) {
      searchTerms.push(query.replace('荃灣', '').trim());
      searchTerms.push('荃灣'); // also search for just the district
    }
    
    for (const term of searchTerms) {
      if (!term.trim()) continue;
      
      const sql = `
        SELECT DISTINCT l.lat, l.lng, l.building_name_zh, l.name,
               b.building_name_zh as business_building, h.building_name_zh as house_building, h.estate_name_zh
        FROM location_info l
        LEFT JOIN business b ON l.id = b.location_id
        LEFT JOIN house h ON l.id = h.location_id
        WHERE 
          LOWER(l.building_name_zh) LIKE LOWER($1)
          OR LOWER(l.name) LIKE LOWER($1)
          OR LOWER(b.building_name_zh) LIKE LOWER($1)
          OR LOWER(h.building_name_zh) LIKE LOWER($1)
          OR LOWER(h.estate_name_zh) LIKE LOWER($1)
          OR LOWER($1) LIKE LOWER(l.building_name_zh)
          OR LOWER($1) LIKE LOWER(l.name)
        LIMIT 1
      `;
      
      const { rows } = await pool.query(sql, [`%${term}%`]);
      if (rows.length > 0) {
        console.log(`Found location in database for term "${term}": ${rows[0].building_name_zh || rows[0].name}`);
        return { lat: parseFloat(rows[0].lat), lng: parseFloat(rows[0].lng) };
      }
    }
    
    // If database search fails, try deal tracking file as fallback
    console.log('Database search failed, trying deal tracking fallback...');
    return await findLocationInDealTracking(query);
    
  } catch (err) {
    console.error('Database location search error:', err);
    // Try deal tracking as last resort
    return await findLocationInDealTracking(query);
  }
}

// Fallback function to search deal tracking JSON file
async function findLocationInDealTracking(query) {
  try {
    const fs = await import('fs');
    const path = await import('path');
    
    // Path to deal tracking file
    const dealTrackingPath = path.join(process.cwd(), '../../scraper/deal_tracking.json');
    
    if (!fs.existsSync(dealTrackingPath)) {
      console.log('Deal tracking file not found');
      return null;
    }
    
    const data = JSON.parse(fs.readFileSync(dealTrackingPath, 'utf8'));
    const deals = data.current_deals || [];
    
    // Search for query in deal strings
    for (const dealString of deals) {
      if (dealString.includes(query) || query.includes(dealString.split('_')[0])) {
        console.log(`Found location in deal tracking: ${dealString}`);
        
        // Extract location info from deal string
        const parts = dealString.split('_');
        if (parts.length >= 2) {
          const building = parts[0];
          const location = parts[1];
          
          // Use dummy coordinates for Hong Kong (can be improved with actual geocoding later)
          // These are approximate coordinates for Tsuen Wan area
          let lat = 22.3686, lng = 114.1048; // Default Tsuen Wan coordinates
          
          if (location.includes('荃灣')) {
            lat = 22.3686; lng = 114.1048; // Tsuen Wan
          } else if (location.includes('中環')) {
            lat = 22.2819; lng = 114.1588; // Central
          } else if (location.includes('尖沙咀')) {
            lat = 22.2969; lng = 114.1722; // Tsim Sha Tsui
          } else if (location.includes('上環')) {
            lat = 22.2867; lng = 114.1491; // Sheung Wan
          } else if (location.includes('元朗')) {
            lat = 22.4414; lng = 114.0222; // Yuen Long
          }
          
          console.log(`Using coordinates for ${location}: ${lat}, ${lng}`);
          return { lat, lng };
        }
      }
    }
    
    console.log(`No matching deals found for query: ${query}`);
    return null;
    
  } catch (err) {
    console.error('Deal tracking search error:', err);
    return null;
  }
}

function filterEmptyRows() {
  return new Transform({
    objectMode: true,
    transform(row, _enc, cb) {
      // if every value is '' (after your mapValues), skip it
      if (Object.values(row).every(v => v === '')) {
        return cb();     // consume & drop
      }
      cb(null, row);     // keep the row
    }
  });
}

router.get('/search', async (req, res, next) => {
  try {
    const { q, lat, lng, radius = '3000',type, dateRange } = req.query;
    let searchLat, searchLng;
    let dateThreshold;
    if (dateRange && !isNaN(parseInt(dateRange, 10))) {
      const days = parseInt(dateRange, 10);
      const now = new Date();
      now.setDate(now.getDate() - days);
      dateThreshold = now.toISOString().split('T')[0]; // format as YYYY-MM-DD
    }

    // 1) If they gave us a text query, geocode it
    if (q && q.trim()) {
      try {
        const coords = await geocode(q.trim());
        searchLat = coords.lat;
        searchLng = coords.lng;
        console.log('geocoded result:', coords);
      } catch (geocodeErr) {
        console.warn('Geocoding failed, trying database fallback:', geocodeErr.message);
        
        // Try to find location in database by name
        const dbCoords = await findLocationInDB(q.trim());
        if (dbCoords) {
          searchLat = dbCoords.lat;
          searchLng = dbCoords.lng;
          console.log(`Found location in database: ${searchLat}, ${searchLng}`);
        } else {
          return res
            .status(404)
            .json({ error: `Could not find location "${q.trim()}" in geocoding services or database` });
        }
      }

    // 2) Otherwise, if they passed coordinates directly, use them
    } else if (lat && lng) {
      searchLat = parseFloat(lat);
      searchLng = parseFloat(lng);
      if (isNaN(searchLat) || isNaN(searchLng)) {
        return res
          .status(400)
          .json({ error: 'Invalid latitude or longitude' });
      }

    // 3) Neither a query nor coords? Tell them to enter something
    } else {
      return res
        .status(400)
        .json({ error: 'Please enter a location or provide lat & lng' });
    }

    // 4) Run your PostGIS “nearby” search
    const where   = [
			`ST_DWithin(
				geom::geography,
				ST_SetSRID(ST_Point($1, $2),4326)::geography,
				$3
			)`
		];

		const params = [searchLng, searchLat, parseInt(radius, 10)];
		let idx = 4;

		// If the client sent a specific type, add it
		if (type) {
			where.push(`b.type = $${idx}`);
			params.push(type);
			idx++;
		}
    if (dateThreshold) {
      where.push(`b.deal_date >= $${idx}`);
      params.push(dateThreshold);
      idx++;
    }

    const sql = `
      SELECT 
        b.id, b.type, b.building_name_zh, b.floor, b.unit, 
        b.area, b.deal_price, b.deal_date, b.developer, b.source_url,
        l.province, l.city, l.country, l.town, l.street, l.road,
        ST_Distance(
          l.geom::geography,
          ST_SetSRID(ST_Point($1, $2),4326)::geography
        ) AS distance
      FROM business b
      LEFT JOIN location_info l ON b.location_id = l.id
      WHERE ${where.join(' AND ')}
      ORDER BY distance
      LIMIT 50
    `;    const { rows } = await pool.query(sql, params);

    res.json(rows);

  } catch (err) {
    console.error('Search error:', err);
    res.status(500).json({ error: err.message });
    next(err);
  }
});

// POST endpoint disabled - manual deal creation not supported
// router.post('/', async (req, res) => {
//   res.status(405).json({ error: 'Manual deal creation is disabled. Use data import instead.' });
// });



export default router;