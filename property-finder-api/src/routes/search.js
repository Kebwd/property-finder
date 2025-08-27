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

// Fallback function to find location in database by name
async function findLocationInDB(query) {
  try {
    // Normalize the query for database search
    const normalized = query
      .replace(/\s*中層\s*/g, ' ')     // remove middle floor
      .replace(/\s*高層\s*/g, ' ')     // remove high floor
      .replace(/\s*低層\s*/g, ' ')     // remove low floor
      .replace(/\s*\d+樓[A-Za-z]*\s*/g, ' ')  // remove floor numbers and unit letters
      .replace(/\s*\d+室\s*/g, ' ')    // remove room numbers
      .replace(/\s+/g, ' ')            // normalize whitespace
      .trim();

    // Try multiple search strategies
    const searchTerms = [query, normalized];

    // Extract key location terms (remove district prefixes for broader search)
    if (query.includes('荃灣')) {
      searchTerms.push(query.replace('荃灣', '').trim());
      searchTerms.push('荃灣'); // also search for just the district
    }

    // First try database search
    for (const term of searchTerms) {
      if (!term.trim()) continue;

      console.log(`Searching database for term: "${term}"`);

      try {
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
          LIMIT 5
        `;

        const { rows } = await pool.query(sql, [`%${term}%`]);
        console.log(`Database search for "${term}" returned ${rows.length} results`);

        if (rows.length > 0) {
          console.log(`Found location in database for term "${term}": ${rows[0].building_name_zh || rows[0].name}`);
          // Log all found locations for debugging
          rows.forEach((row, index) => {
            console.log(`  Result ${index + 1}: ${JSON.stringify({
              building: row.building_name_zh,
              name: row.name,
              business_building: row.business_building,
              house_building: row.house_building,
              estate: row.estate_name_zh,
              lat: row.lat,
              lng: row.lng
            })}`);
          });
          return { lat: parseFloat(rows[0].lat), lng: parseFloat(rows[0].lng) };
        }
      } catch (dbError) {
        console.log(`Database search failed for "${term}": ${dbError.message}`);
        // Continue to deal tracking fallback
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

    // Try multiple possible paths for Vercel deployment
    const possiblePaths = [
      path.join(process.cwd(), 'deal_tracking.json'),  // Local copy in API directory
      path.join(process.cwd(), '../../../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../../../../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../scraper/deal_tracking.json'),
      '/tmp/deal_tracking.json'
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
      console.log('Deal tracking file not found, using embedded data');
      // Use embedded data as fallback
      for (const deal of EMBEDDED_DEALS) {
        if (deal.building === query || query.includes(deal.building) || deal.building.includes(query) || deal.address.includes(query)) {
          console.log(`Found embedded deal: ${deal.building}`);
          return { lat: deal.lat, lng: deal.lng, source: 'embedded_deal_tracking', deal: deal.building };
        }
      }
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
    // Return embedded data as last resort
    console.log('Falling back to embedded deal data');
    for (const deal of EMBEDDED_DEALS) {
      if (deal.building === query || query.includes(deal.building) || deal.building.includes(query) || deal.address.includes(query)) {
        console.log(`Found embedded deal: ${deal.building}`);
        return { lat: deal.lat, lng: deal.lng, source: 'embedded_deal_tracking', deal: deal.building };
      }
    }
    return null;
  }
}

// Helper function to get available deals for debugging
async function getAvailableDeals() {
  try {
    const fs = await import('fs');
    const path = await import('path');

    const possiblePaths = [
      path.join(process.cwd(), 'deal_tracking.json'),  // Local copy in API directory
      path.join(process.cwd(), '../../../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../../../../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../../scraper/deal_tracking.json'),
      path.join(process.cwd(), '../scraper/deal_tracking.json'),
      '/tmp/deal_tracking.json'
    ];

    for (const testPath of possiblePaths) {
      try {
        if (fs.existsSync(testPath)) {
          const data = JSON.parse(fs.readFileSync(testPath, 'utf8'));
          return (data.current_deals || []).map(deal => deal.split('_')[0]);
        }
      } catch (err) {
        // Continue to next path
      }
    }

    // No fallback data available
    return [];
  } catch (err) {
    console.error('Error getting available deals:', err);
    return [];
  }
}
router.get('/all', async (req, res, next) => {
  try {
    const { q, lat, lng, radius = '3000', type, dateRange } = req.query;
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
      try {
        const coords = await geocode(q.trim());
        searchLat = coords.lat;
        searchLng = coords.lng;
        console.log('Geocoded coordinates:', coords);
      } catch (geocodeErr) {
        console.warn('Geocoding failed, trying database fallback:', geocodeErr.message);

        // Try to find location in database by name
        const dbCoords = await findLocationInDB(q.trim());
        if (dbCoords) {
          searchLat = dbCoords.lat;
          searchLng = dbCoords.lng;
          console.log(`Found location in database: ${searchLat}, ${searchLng}`);
        } else {
          // Try with normalized query as additional fallback
          const normalizedQuery = q.trim()
            .replace(/\s*中層\s*/g, ' ')
            .replace(/\s*高層\s*/g, ' ')
            .replace(/\s*低層\s*/g, ' ')
            .replace(/\s*\d+樓[A-Za-z]*\s*/g, ' ')
            .replace(/\s*\d+室\s*/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();

          if (normalizedQuery !== q.trim()) {
            console.log(`Trying normalized query: "${normalizedQuery}"`);
            const normalizedCoords = await findLocationInDB(normalizedQuery);
            if (normalizedCoords) {
              searchLat = normalizedCoords.lat;
              searchLng = normalizedCoords.lng;
              console.log(`Found location with normalized query: ${searchLat}, ${searchLng}`);
            } else {
              return res.status(404).json({
                error: `Could not find location "${q.trim()}" in geocoding services or database`,
                geocoding_error: geocodeErr.message,
                normalized_query: normalizedQuery,
                available_deals: await getAvailableDeals()
              });
            }
          } else {
            return res.status(404).json({
              error: `Could not find location "${q.trim()}" in geocoding services or database`,
              geocoding_error: geocodeErr.message,
              available_deals: await getAvailableDeals()
            });
          }
        }
      }
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
        h.id, h.type, h.building_name_zh, h.estate_name_zh, h.flat,
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
    // Add fallback: for house, if estate_name_zh is null, use building_name_zh as name
    const result = rows.map(row => {
      // Helper to treat empty string as null
      const safe = v => (v && v.trim() ? v : null);
      if (row.deal_type === 'house') {
        return {
          ...row,
          name: safe(row.estate_name_zh) || safe(row.building_name_zh) || null
        };
      } else {
        return {
          ...row,
          name: safe(row.building_name_zh) || null
        };
      }
    });
    res.json(result);

  } catch (err) {
    console.error('Search error:', err);
    res.status(500).json({ error: err.message });
    next(err);
  }
});

// Debug endpoint to check database contents
router.get('/debug', async (req, res) => {
  try {
    const { q } = req.query;
    
    if (q) {
      // Test the database search function
      const result = await findLocationInDB(q);
      return res.json({
        query: q,
        found: result !== null,
        coordinates: result
      });
    }
    
    // Show sample locations from database
    const sql = `
      SELECT DISTINCT l.building_name_zh, l.name, l.lat, l.lng,
             COUNT(b.id) as business_count, COUNT(h.id) as house_count
      FROM location_info l
      LEFT JOIN business b ON l.id = b.location_id
      LEFT JOIN house h ON l.id = h.location_id
      GROUP BY l.id, l.building_name_zh, l.name, l.lat, l.lng
      HAVING business_count > 0 OR house_count > 0
      LIMIT 20
    `;
    
    const { rows } = await pool.query(sql);
    res.json({
      total_locations: rows.length,
      sample_locations: rows.map(row => ({
        building: row.building_name_zh,
        name: row.name,
        coordinates: `${row.lat}, ${row.lng}`,
        business_count: parseInt(row.business_count),
        house_count: parseInt(row.house_count)
      }))
    });
  } catch (err) {
    console.error('Debug endpoint error:', err);
    res.status(500).json({ error: err.message });
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
