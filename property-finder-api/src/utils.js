import fetch from 'node-fetch';

const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search';

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