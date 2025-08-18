// store-finder-api/src/routes/search.js
import express from 'express';
import pool from '../db.js';
import { geocode } from '../utils.js';
import multer from 'multer';
import csvParser from 'csv-parser';
import { parseChinesePrice } from '../parsePrice.js';
import fs from 'fs';
const router = express.Router();
const upload = multer({ dest: 'uploads' });

// Common function to build WHERE clause for geospatial queries
export const buildWhereClause = (lat, lng, radius) => {
  return {
    where: [
      `ST_DWithin(
        l.geom::geography,
        ST_SetSRID(ST_Point($1, $2),4326)::geography,
        $3
      )`
    ],
    params: [lng, lat, parseInt(radius, 10)]
  };
};
router.get('/all', async (req, res, next) => {
  try {
    const { q, lat, lng, radius = '5000', type, dateRange } = req.query;
    let searchLat, searchLng;
    let dateThreshold;

    // Handle date range
    if (dateRange && !isNaN(parseInt(dateRange, 10))) {
      const days = parseInt(dateRange, 10);
      const now = new Date();
      now.setDate(now.getDate() - days);
      dateThreshold = now.toISOString().split('T')[0];
    }

    // Geocode or use lat/lng
    if (q && q.trim()) {
      const coords = await geocode(q.trim());
      if (!coords) {
        return res.status(404).json({ error: `Could not find location "${q.trim()}"` });
      }
      searchLat = coords.lat;
      searchLng = coords.lng;
    } else if (lat && lng) {
      searchLat = parseFloat(lat);
      searchLng = parseFloat(lng);
      if (isNaN(searchLat) || isNaN(searchLng)) {
        return res.status(400).json({ error: 'Invalid latitude or longitude' });
      }
    } else {
      return res.status(400).json({ error: 'Please enter a location or provide lat & lng' });
    }

    // Build dynamic WHERE clause
    const filters = [];
    const params = [searchLng, searchLat, parseInt(radius, 10)];
    let idx = 4;

    if (type) {
      filters.push(`type = $${idx}`);
      params.push(type);
      idx++;
    }

    if (dateThreshold) {
      filters.push(`deal_date >= $${idx}`);
      params.push(dateThreshold);
      idx++;
    }

    const filterClause = filters.length ? `AND ${filters.join(' AND ')}` : '';

    // Unified SQL with UNION ALL
    const sql = `
      SELECT 
        'business' AS deal_type,
        b.id, b.type, b.building_name_zh, NULL AS estate_name_zh, NULL AS flat,
        b.floor, b.unit, b.area, b.deal_price, b.deal_date, b.developer,
        l.province, l.city, l.country, l.town, l.street, l.road,
        ST_Distance(
          l.geom::geography,
          ST_SetSRID(ST_Point($1, $2),4326)::geography
        ) AS distance
      FROM business b
      JOIN location_info l ON b.location_id = l.id
      WHERE ST_DWithin(
        l.geom::geography,
        ST_SetSRID(ST_Point($1, $2),4326)::geography,
        $3
      )
      ${filterClause}

      UNION ALL

      SELECT 
        'house' AS deal_type,
        h.id, h.type, NULL AS building_name_zh, h.estate_name_zh, h.flat,
        h.floor, h.unit, h.area, h.deal_price, h.deal_date, h.developer,
        l.province, l.city, l.country, l.town, l.street, l.road,
        ST_Distance(
          l.geom::geography,
          ST_SetSRID(ST_Point($1, $2),4326)::geography
        ) AS distance
      FROM house h
      JOIN location_info l ON h.location_id = l.id
      WHERE ST_DWithin(
        l.geom::geography,
        ST_SetSRID(ST_Point($1, $2),4326)::geography,
        $3
      )
      ${filterClause}

      ORDER BY distance
      LIMIT 50
    `;

    const { rows } = await pool.query(sql, params);
    res.json(rows);

  } catch (err) {
    console.error('Search error:', err);
    res.status(500).json({ error: err.message });
    next(err);
  }
});

// Generic search endpoint that redirects to specific type handlers
router.get('/', async (req, res) => {
  const { q, type = 'business' } = req.query;
  
  if (type === 'house') {
    res.redirect(`/api/house/search?${new URLSearchParams(req.query)}`);
  } else if (type === 'business') {
    res.redirect(`/api/business/search?${new URLSearchParams(req.query)}`);
  } else {
    res.status(400).json({ error: 'Invalid type specified' });
  }
});

// CSV upload endpoint for both types
router.post('/upload', upload.single('file'), (req, res, next) => {
  console.log('CSV import started');
  const rows = [];
  const filePath = req.file.path;

  fs.createReadStream(filePath)
    .pipe(csvParser({
      bom: true,
      mapHeaders: ({ header }) => header.trim().toLowerCase(),
      mapValues: ({ value }) => (value || '').trim(),
      skipRecordsWithEmptyValues: true
    }))
    .on('data', row => {
      const dateRaw = row.deal_date;
      const typeRaw = ((row.type || '').trim() || 'business');
      const priceRaw = row.deal_price;

      if (!priceRaw || !dateRaw) {
        console.warn('Skipping row – missing required fields:', row);
        return;
      }

      // Parse price and date
      let dealPriceNum;
      try {
        dealPriceNum = parseChinesePrice(priceRaw);
      } catch (err) {
        console.warn(`Skipping row due to price parse error: ${err.message}`);
        return;
      }

      const [d, m, y] = dateRaw.split('/');
      if (!y) return;
      const isoDate = `${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`;

      // Common fields
      const record = {
        type: typeRaw,
        province: row.province || null,
        city: row.city || null,
        country: row.country || null,
        town: row.town || null,
        street: row.street || null,
        road: row.road || null,
        deal_price: dealPriceNum,
        deal_date: isoDate,
        developer: row.developer || null,
        floor: row.floor || null,
        unit: row.unit || null,
        area: row.area || null
      };

      // Add type-specific fields
      if (typeRaw === 'house') {
        record.estate_name_zh = row.estate_name_zh || null;
        record.flat = row.flat || null;
        record.house_type = row.house_type || null;
        record.building_name_zh = row.building_name_zh || null;
      } else {
        record.building_name_zh = row.building_name_zh || null;
      }

      rows.push(record);
    })
    .on('end', async () => {
      let client;
      const inserted = [];

      try {
        client = await pool.connect();
        await client.query('BEGIN');

        for (const record of rows) {
          // 1. Insert location info
          const address = [record.province, record.city, record.country, record.town, record.street, record.road]
            .filter(Boolean)
            .join(', ');
          
          const coords = await geocode(address);
          if (!coords) {
            console.warn(`No coordinates found for address: ${address}, skipping`);
            continue;
          }

          const locationSQL = `
            INSERT INTO location_info (
              province, city, country, town, street, road, geom
            ) VALUES ($1, $2, $3, $4, $5, $6, ST_SetSRID(ST_Point($7, $8), 4326))
            RETURNING id
          `;

          const { rows: [location] } = await client.query(locationSQL, [
            record.province,
            record.city,
            record.country,
            record.town,
            record.street,
            record.road,
            coords.lng,
            coords.lat
          ]);

          // 2. Insert into appropriate table based on type
          let insertSQL, values;
          if (record.type === 'house') {
            insertSQL = `
              INSERT INTO house (
                type, estate_name_zh, flat, building_name_zh, floor, unit,
                area, house_type, deal_price, deal_date, developer, location_id
              ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
              RETURNING id
            `;
            values = [
              record.type,
              record.estate_name_zh,
              record.flat,
              record.building_name_zh,
              record.floor,
              record.unit,
              record.area,
              record.house_type,
              record.deal_price,
              record.deal_date,
              record.developer,
              location.id
            ];
          } else {
            insertSQL = `
              INSERT INTO business (
                type, building_name_zh, floor, unit,
                area, deal_price, deal_date, developer, location_id
              ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
              RETURNING id
            `;
            values = [
              record.type,
              record.building_name_zh,
              record.floor,
              record.unit,
              record.area,
              record.deal_price,
              record.deal_date,
              record.developer,
              location.id
            ];
          }

          const { rows: [newRow] } = await client.query(insertSQL, values);
          inserted.push({ 
            id: newRow.id, 
            type: record.type,
            location_id: location.id
          });
        }

        await client.query('COMMIT');
        console.log('CSV import finished');
        res.json({ success: true, imported: inserted.length });

      } catch (err) {
        if (client) await client.query('ROLLBACK');
        return next(err);
      } finally {
        if (client) client.release();
        fs.unlinkSync(filePath);
      }
    })
    .on('error', err => {
      fs.unlinkSync(filePath);
      next(err);
    });
});

export default router;
