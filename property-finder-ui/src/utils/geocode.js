const NOMINATIM_BASE = 'https://nominatim.openstreetmap.org/search';
const GOOGLE_BASE = 'https://maps.googleapis.com/maps/api/geocode/json';

// Detect region based on keywords
function detectRegion(query) {
  const lower = query.toLowerCase();
  if (lower.includes('hong kong') || lower.includes('hk')) {
    return 'HK';
  }
  return 'CN';
}

// Normalize estate-style input
function normalizeEstateName(query) {
  return query
    .replace(/\d+號/g, '')     // remove building numbers
    .replace(/第?\d+座/g, '')   // remove block numbers
    .replace(/\d+樓/g, '')     // remove floor numbers
    .trim();
}

// Try Nominatim geocoding
async function tryNominatim(query) {
  const url = `${NOMINATIM_BASE}?q=${encodeURIComponent(query)}&format=json&limit=1`;

  const res = await fetch(url, {
    headers: { 'User-Agent': 'YourApp/1.0' }
  });
  const data = await res.json();
  if (!data.length) {
    throw new Error('Nominatim: no results');
  }
  return {
    lat: parseFloat(data[0].lat),
    lng: parseFloat(data[0].lon)
  };
}

// Try Google Maps geocoding
async function tryGoogle(query, region = 'HK') {
  // Note: This requires VITE_GEOCODING_API_KEY environment variable
  const key = import.meta.env.VITE_GEOCODING_API_KEY;
  if (!key) {
    throw new Error('Google: API key not configured');
  }
  const url = `${GOOGLE_BASE}?address=${encodeURIComponent(query)}&components=country:${region}&key=${key}`;

  const res = await fetch(url);
  const body = await res.json();
  if (body.status !== 'OK' || !body.results.length) {
    throw new Error(`Google: ${body.status}`);
  }
  const loc = body.results[0].geometry.location;
  return { lat: loc.lat, lng: loc.lng };
}

// Main geocode function
export async function geocode(query) {
  if (!query.trim()) {
    throw new Error('Please enter a location');
  }

  const region = detectRegion(query);
  const normalized = normalizeEstateName(query);
  const biased = `${normalized}, ${region === 'HK' ? 'Hong Kong' : 'China'}`;

  try {
    return await tryNominatim(biased);
  } catch (err) {
    console.warn(err.message, '→ falling back to Google Maps');
  }

  try {
    return await tryGoogle(biased, region);
  } catch (err) {
    console.warn(err.message, '→ no more fallbacks available');
  }

  throw new Error('Unable to geocode location with available services');
}
