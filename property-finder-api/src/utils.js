import fetch from 'node-fetch';

const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search';

// Normalize estate-style input for geocoding
function normalizeEstateName(query) {
  return query
    .replace(/\d+號/g, '')     // remove building numbers
    .replace(/第?\d+座/g, '')   // remove block numbers
    .replace(/\d+樓[A-Za-z]*/g, '')     // remove floor numbers and unit letters
    .replace(/\d+室/g, '')     // remove room numbers
    .replace(/中層|高層|低層/g, '') // remove floor level descriptions
    .replace(/\s+/g, ' ')      // normalize whitespace
    .trim();
}

async function tryNominatim(query) {
  const url = `${NOMINATIM_BASE}`
    + `?q=${encodeURIComponent(query)}`
    + '&format=json&limit=1';

  const res  = await fetch(url, { headers: { 'User-Agent': 'YourApp/1.0' } });
  if (!res.ok) throw new Error(`Nominatim HTTP ${res.status}`);
  const data = await res.json();
  if (data.length === 0) return null;
  return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
}

async function tryGoogle(query) {
  const key = process.env.GEOCODING_API_KEY;
  const url = `https://maps.googleapis.com/maps/api/geocode/json`
    + `?address=${encodeURIComponent(query)}`
    + `&components=country:HK`
    + `&key=${key}`;

  const res  = await fetch(url);
  if (!res.ok) throw new Error(`Google HTTP ${res.status}`);
  const body = await res.json();
  if (body.status !== 'OK' || !body.results.length) return null;
  const loc = body.results[0].geometry.location;
  return { lat: loc.lat, lng: loc.lng };
}

export async function geocode(query) {
  if (!query.trim()) {
    throw new Error('Please enter a location');
  }
  
  // Normalize the query for geocoding
  const normalized = normalizeEstateName(query);
  const biased = `${normalized}, Hong Kong`;
  const originalBiased = `${query}, Hong Kong`;

  // try OSM first with normalized query, then original
  let osm = await tryNominatim(biased);
  if (!osm) {
    osm = await tryNominatim(originalBiased);
  }
  if (osm) return osm;

  // try Google with normalized query, then original
  let g = await tryGoogle(biased);
  if (!g) {
    g = await tryGoogle(originalBiased);
  }
  if (g) return g;

  throw new Error('Geocoding failed for: ' + query);
}