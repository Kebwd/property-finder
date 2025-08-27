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
const typeMap = {
  '全部': [],
  '住宅單位': ['别墅', '公寓', '住宅单位','住宅單位'],
  '寫字樓': ['写字楼','寫字樓'],
  '商舖': ['商铺','商舖'],
  '辦公室': ['办公室','辦公室'],
  '倉庫': ['仓库','倉庫'],
  '土地': ['土地']
};
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
		if (type && type !== '全部') {
      const mappedTypes = typeMap[type] || [type];
      const placeholders = mappedTypes.map((_, i) => `$${idx + i}`);
      where.push(`h.type IN (${placeholders.join(', ')})`);
      params.push(...mappedTypes);
      idx += mappedTypes.length;
    }
    if (dateThreshold) {
      where.push(`h.deal_date >= $${idx}`);
      params.push(dateThreshold);
      idx++;
    }

    const sql = `
      SELECT 
        h.id, h.type, h.estate_name_zh, h.flat, h.building_name_zh, h.floor, h.unit, 
        h.area, h.house_type, h.deal_price, h.deal_date, h.developer, h.source_url,
        l.province, l.city, l.country, l.town, l.street, l.road,
        ST_Distance(
          l.geom::geography,
          ST_SetSRID(ST_Point($1, $2),4326)::geography
        ) AS distance
      FROM house h
      LEFT JOIN location_info l ON h.location_id = l.id
      WHERE ${where.join(' AND ')}
      ORDER BY distance
      LIMIT 50;
    `;

    const { rows } = await pool.query(sql, params);


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