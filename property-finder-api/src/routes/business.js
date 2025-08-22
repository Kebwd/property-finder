// store-finder-api/src/routes/stores.js
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
    const { q, lat, lng, radius = '5000',type, dateRange } = req.query;
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
      const coords = await geocode(q.trim());
      if (!coords) {
        return res
          .status(404)
          .json({ error: `Could not find location "${q.trim()}"` });
      }
      searchLat = coords.lat;
      searchLng = coords.lng;
      console.log('geocoded result:', coords);

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

// POST /stores 
router.post('/', async (req, res) => {
  const { 
    type,
    province, city, country, town, street, road,
    building_name_zh, floor, unit, area, deal_price, deal_date, developer, source_url,
    // house specific fields
    estate_name_zh, flat, house_type
  } = req.body;

  if (!type || !deal_date || !deal_price) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');

    // 1. First insert location info
    const locationSQL = `
      INSERT INTO location_info (
        province, city, country, town, street, road,
        geom
      ) VALUES (
        $1, $2, $3, $4, $5, $6,
        ST_SetSRID(ST_Point($7, $8), 4326)
      )
      RETURNING id;
    `;

    // Get coordinates from address components
    const address = [province, city, country, town, street, road]
      .filter(Boolean)
      .join(', ');
    const { lat, lng } = await geocode(address);

    const locationVals = [
      province || null,
      city || null,
      country || null,
      town || null,
      street || null,
      road || null,
      parseFloat(lng),
      parseFloat(lat)
    ];

    const { rows: [location] } = await client.query(locationSQL, locationVals);

    // 2. Then insert the business or house record
    let insertSQL, vals;
    
    if (type === 'house') {
      insertSQL = `
        INSERT INTO house (
          type, estate_name_zh, flat, building_name_zh, floor, unit,
          area, house_type, deal_price, deal_date, developer, location_id
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        )
        RETURNING *;
      `;
      vals = [
        type,
        estate_name_zh,
        flat,
        building_name_zh,
        floor,
        unit,
        area,
        house_type,
        deal_price,
        deal_date,
        developer,
        location.id
      ];
    } else {
      insertSQL = `
        INSERT INTO business (
          type, building_name_zh, floor, unit,
          area, deal_price, deal_date, developer, source_url, location_id
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
        )
        RETURNING *;
      `;
      vals = [
        type,
        building_name_zh,
        floor,
        unit,
        area,
        deal_price,
        deal_date,
        developer,
        source_url,
        location.id
      ];
    }

    const { rows: [result] } = await client.query(insertSQL, vals);
    
    await client.query('COMMIT');
    res.status(201).json({ ...result, ...location });

  } catch (err) {
    await client.query('ROLLBACK');
    console.error('POST /stores error:', err);
    return res.status(500).json({ error: err.message });
  } finally {
    client.release();
  }
});



export default router;