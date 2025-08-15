import express from 'express';
import rateLimit from 'express-rate-limit';
import cors from 'cors';
import dotenv from 'dotenv';
import { Pool } from 'pg';
import fs from 'fs';
import fetch from 'node-fetch';
import exportRouter from './routes/export.js';
import multer from 'multer';

dotenv.config();

let GEOCODING_API_KEY = process.env.GEOCODING_API_KEY || '';
if (!GEOCODING_API_KEY) {
  try {
    GEOCODING_API_KEY = fs
      .readFileSync('/run/secrets/geocode_api_key', 'utf-8')
      .trim();
  } catch (err) {
    console.error('Failed to read geocoding API key from secret:', err.message);
  }
}

// For Vercel, we'll use environment variables instead of secrets
if (!GEOCODING_API_KEY) {
  console.warn('GEOCODING_API_KEY not found in secrets, using environment variable');
  GEOCODING_API_KEY = process.env.GEOCODING_API_KEY;
}

console.log('GEOCODING_API_KEY:', GEOCODING_API_KEY ? 'Set' : 'Not set');
if (!GEOCODING_API_KEY) {
  console.error(
    'Missing GEOCODING_API_KEY – please set the env var.'
  );
}

const pool = new Pool({ 
  connectionString: process.env.DATABASE_URL || process.env.SUPABASE_DB_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

const app = express();
app.use(cors());
const upload = multer({ storage: multer.memoryStorage() });
app.use(express.json());
import houseRouter from './routes/house.js';
import businessRouter from './routes/business.js';
import searchRouter from './routes/search.js';
import healthRouter from './routes/health.js';
import scraperRouter from './routes/scraper.js';

app.use('/api/house', houseRouter);
app.use('/api/business', businessRouter);
app.use('/api/search', searchRouter);
app.use('/api/export', exportRouter);
app.use('/api/scraper', scraperRouter);
app.use('/health', healthRouter);
app.use(rateLimit({
  windowMs: 60_000,
  max: 30,
  message: { error: 'Too many requests, slow down.' }
}));

// Simple in-memory cache for geocoding (for development)
// In production, consider using Vercel KV or another caching solution
const geocodeCache = new Map();

async function geocode(address) {
  const key = `geo:${address}`;
  const cached = geocodeCache.get(key);
  if (cached) return cached;

  if (!GEOCODING_API_KEY) {
    throw new Error('Geocoding API key not configured');
  }

  const res = await fetch(
    `https://maps.googleapis.com/maps/api/geocode/json?` +
    `address=${encodeURIComponent(address)}` +
    `&key=${GEOCODING_API_KEY}`
  );
  const data = await res.json();
  const loc = data.results?.[0]?.geometry.location;
  if (!loc) throw new Error('Geocode failed');
  
  // Cache for 1 hour (simple in-memory cache)
  geocodeCache.set(key, loc);
  setTimeout(() => geocodeCache.delete(key), 3600000);
  
  return loc;
}

app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: err.message });
});

// For Vercel, export the app instead of listening
const port = process.env.PORT || 5000;
if (process.env.NODE_ENV !== 'production') {
  app.listen(port, () => console.log(`API listening on ${port}`));
}

export default app;