import express from 'express';
import pool from '../db.js';

const router = express.Router();

router.get('/', async (req, res) => {
  try {
    // Check database connection
    const result = await pool.query('SELECT 1 as status');
    
    // Check if we have data
    const locationCount = await pool.query('SELECT COUNT(*) as count FROM location_info');
    const businessCount = await pool.query('SELECT COUNT(*) as count FROM business');
    
    res.status(200).json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: 'connected',
      uptime: Math.floor(process.uptime()),
      data: {
        locations: parseInt(locationCount.rows[0].count),
        businesses: parseInt(businessCount.rows[0].count)
      },
      version: process.env.npm_package_version || '1.0.0'
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

export default router;
