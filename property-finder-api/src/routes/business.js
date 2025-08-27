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
    // Search for the query in building_name_zh or estate_name_zh fields
    const sql = `
      SELECT DISTINCT l.lat, l.lng, l.building_name_zh, l.name
      FROM location_info l
      LEFT JOIN business b ON l.id = b.location_id
      LEFT JOIN house h ON l.id = h.location_id
      WHERE 
        LOWER(l.building_name_zh) LIKE LOWER($1)
        OR LOWER(l.name) LIKE LOWER($1)
        OR LOWER(b.building_name_zh) LIKE LOWER($1)
        OR LOWER(h.building_name_zh) LIKE LOWER($1)
        OR LOWER(h.estate_name_zh) LIKE LOWER($1)
      LIMIT 1
    `;
    
    const { rows } = await pool.query(sql, [`%${query}%`]);
    if (rows.length > 0) {
      return { lat: parseFloat(rows[0].lat), lng: parseFloat(rows[0].lng) };
    }
    return null;
  } catch (err) {
    console.error('Database location search error:', err);
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