const { Pool } = require('pg');
const https = require('https');
const fs = require('fs');
const path = require('path');

// Guard: require token matching DIAG_ENDPOINT_KEY
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') { res.status(200).end(); return; }

  const token = req.query.token;
  const required = process.env.DIAG_ENDPOINT_KEY;
  if (required) {
    if (!token || token !== required) {
      return res.status(403).json({ success: false, error: 'Invalid or missing token' });
    }
  } else {
    // If no token configured, refuse to run on deployed environment by default
    return res.status(403).json({ success: false, error: 'Diagnostic endpoint disabled. Set DIAG_ENDPOINT_KEY to enable.' });
  }

  const q = (req.query.q || '').trim();
  const limit = parseInt(req.query.limit) || 10;
  if (!q) return res.status(400).json({ success: false, error: 'Missing q parameter' });

  // Setup DB pool only if DATABASE_URL exists
  let pool = null;
  if (process.env.DATABASE_URL) {
    pool = new Pool({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
  }

  // Geocoding helpers (Nominatim + Google)
  const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search';
  const GOOGLE_BASE = 'https://maps.googleapis.com/maps/api/geocode/json';

  function tryNominatim(query) {
    return new Promise((resolve, reject) => {
      const url = `${NOMINATIM_BASE}?q=${encodeURIComponent(query)}&format=json&limit=1`;
      const u = new URL(url);
      const options = { hostname: u.hostname, path: u.pathname + u.search, method: 'GET', headers: { 'User-Agent': 'Diag/1.0' } };
      const r = https.request(options, (resp) => {
        let d = '';
        resp.on('data', c => d += c);
        resp.on('end', () => {
          try {
            if (resp.statusCode !== 200) return resolve(null);
            const json = JSON.parse(d);
            if (!json || !json.length) return resolve(null);
            resolve({ lat: parseFloat(json[0].lat), lng: parseFloat(json[0].lon) });
          } catch (e) { resolve(null); }
        });
      });
      r.on('error', () => resolve(null));
      r.end();
    });
  }

  function tryGoogle(query) {
    return new Promise((resolve, reject) => {
      const key = process.env.GEOCODING_API_KEY;
      if (!key) return resolve(null);
      const url = `${GOOGLE_BASE}?address=${encodeURIComponent(query)}&components=country:HK&key=${key}`;
      const u = new URL(url);
      const options = { hostname: u.hostname, path: u.pathname + u.search, method: 'GET' };
      const r = https.request(options, (resp) => {
        let d = '';
        resp.on('data', c => d += c);
        resp.on('end', () => {
          try {
            if (resp.statusCode !== 200) return resolve(null);
            const json = JSON.parse(d);
            if (!json || json.status !== 'OK' || !json.results || !json.results.length) return resolve(null);
            const loc = json.results[0].geometry.location;
            resolve({ lat: loc.lat, lng: loc.lng });
          } catch (e) { resolve(null); }
        });
      });
      r.on('error', () => resolve(null));
      r.end();
    });
  }

  async function geocode(query) {
    const variations = [query, `${query}, Hong Kong`, query.replace('荃灣', 'Tsuen Wan')];
    for (const v of variations) {
      const nom = await tryNominatim(v).catch(() => null);
      if (nom) return nom;
    }
    for (const v of variations) {
      const g = await tryGoogle(v).catch(() => null);
      if (g) return g;
    }
    return null;
  }

  // DB checks
  const out = { query: q, geocode: null, nearest_distance_m: null, location_info_matches: [], business_matches: [], house_matches: [], deal_tracking: [] };

  try {
    // 1) geocode
    out.geocode = await geocode(q);

    // 2) nearest DB point
    if (pool && out.geocode) {
      const nearSql = `SELECT l.id, l.lat, l.long, ST_Distance(ST_SetSRID(ST_Point(l.long, l.lat),4326)::geography, ST_SetSRID(ST_Point($2,$1),4326)::geography) AS distance FROM location_info l ORDER BY distance LIMIT 1`;
      const nearRes = await pool.query(nearSql, [out.geocode.lat, out.geocode.lng]);
      if (nearRes.rows && nearRes.rows[0]) out.nearest_distance_m = nearRes.rows[0].distance;
    }

    // 3) location_info matches (exact, wildcard)
    if (pool) {
      const exactSql = `SELECT id, province, city, town, street FROM location_info WHERE LOWER(town)=LOWER($1) OR LOWER(street)=LOWER($1) LIMIT 50`;
      const exact = await pool.query(exactSql, [q]);
      out.location_info_matches = out.location_info_matches.concat(exact.rows || []);

      if (out.location_info_matches.length === 0) {
        const likeSql = `SELECT id, province, city, town, street FROM location_info WHERE town ILIKE $1 OR street ILIKE $1 OR CONCAT(town,' ',street) ILIKE $1 LIMIT 50`;
        const like = await pool.query(likeSql, [`%${q}%`]);
        out.location_info_matches = out.location_info_matches.concat(like.rows || []);
      }
    }

    // 4) fetch business/house rows tied to matched location_ids
    if (pool && out.location_info_matches.length) {
      const ids = out.location_info_matches.map(r => r.id);
      const placeholders = ids.map((_,i)=>`$${i+1}`).join(',');
      const params = [...ids, limit];
      const sql = `SELECT * FROM (SELECT 'business' as source, b.id, b.building_name_zh as name, b.location_id, l.town, l.street FROM business b JOIN location_info l ON b.location_id = l.id WHERE b.location_id IN (${placeholders}) UNION ALL SELECT 'house' as source, h.id, COALESCE(NULLIF(h.estate_name_zh,''), NULLIF(h.building_name_zh,''), h.building_name_zh) as name, h.location_id, l.town, l.street FROM house h JOIN location_info l ON h.location_id = l.id WHERE h.location_id IN (${placeholders})) t LIMIT $${ids.length + 1}`;
      const rows = await pool.query(sql, params);
      for (const r of (rows.rows||[])) {
        if (r.source === 'business') out.business_matches.push(r); else out.house_matches.push(r);
      }
    }

    // 5) check deal_tracking.json for any string matches
    try {
      const possible = [
        path.join(process.cwd(), 'deal_tracking.json'),
        path.join(process.cwd(), '../scraper/deal_tracking.json'),
        path.join(process.cwd(), '../../scraper/deal_tracking.json'),
        '/tmp/deal_tracking.json'
      ];
      for (const p of possible) {
        if (fs.existsSync(p)) {
          const data = JSON.parse(fs.readFileSync(p,'utf8'));
          const deals = data.current_deals || [];
          for (const d of deals) {
            if (String(d).includes(q)) out.deal_tracking.push(d);
          }
          break;
        }
      }
    } catch (dtErr) { /* ignore */ }

    return res.status(200).json({ success: true, diagnostic: out });
  } catch (err) {
    console.error('Diagnose error:', err);
    return res.status(500).json({ success: false, error: err.message });
  } finally {
    if (pool) await pool.end().catch(()=>{});
  }
};
