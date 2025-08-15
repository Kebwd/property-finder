import fetch from 'node-fetch';

const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search';

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
  // bias results to Hong Kong
  const biased = `${query}, Hong Kong`;

  // try OSM first, then Google
  const osm = await tryNominatim(biased);
  if (osm) return osm;

  const g = await tryGoogle(biased);
  if (g) return g;

  throw new Error('Geocoding failed for: ' + query);
}