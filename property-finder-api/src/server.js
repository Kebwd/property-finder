import express from 'express';
import rateLimit from 'express-rate-limit';
import cors from 'cors';
import dotenv from 'dotenv';
import { Pool } from 'pg';
import fs from 'fs';
import fetch from 'node-fetch';
import { createClient } from 'redis';
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
console.log('GEOCODING_API_KEY:', GEOCODING_API_KEY);
if (!GEOCODING_API_KEY) {
  console.error(
    'Missing GEOCODING_API_KEY – please set the env var or mount the secret file.'
  );
  process.exit(1);
}


const pool = new Pool({ connectionString: process.env.DATABASE_URL });
// const redis = createClient({ url: process.env.REDIS_URL });
// await redis.connect();

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

const port = process.env.PORT || 5000;
console.log('ENV PORT is', process.env.PORT, '— binding to', port);
app.listen(port, () => console.log(`API listening on ${port}`));

async function geocode(address) {
  const key = `geo:${address}`;
  // const cached = await redis.get(key);
  // if (cached) return JSON.parse(cached);

  const res = await fetch(
    `https://maps.googleapis.com/maps/api/geocode/json?` +
    `address=${encodeURIComponent(address)}` +
    `&key=${GEOCODING_API_KEY}`
  );
  const data = await res.json();
  const loc = data.results?.[0]?.geometry.location;
  if (!loc) throw new Error('Geocode failed');
  // await redis.set(key, JSON.stringify(loc), { EX: 86400 });
  return loc;
}

app.use((err, req, res, next) => {
  console.error('Unhandled error in CSV import:', err);
  res.status(500).json({ error: err.message });
});