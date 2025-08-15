import express from 'express';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

const router = express.Router();

// Security middleware - only allow if API key matches
const validateApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'] || req.query.api_key;
  const expectedKey = process.env.SCRAPER_API_KEY || 'scraper-secret-key';
  
  if (apiKey !== expectedKey) {
    return res.status(401).json({ error: 'Unauthorized: Invalid API key' });
  }
  next();
};

// Status tracking
let scrapingStatus = {
  isRunning: false,
  lastRun: null,
  lastResult: null,
  logs: []
};

// Helper function to add log entries
const addLog = (message, type = 'info') => {
  const logEntry = {
    timestamp: new Date().toISOString(),
    message,
    type
  };
  scrapingStatus.logs.push(logEntry);
  
  // Keep only last 50 log entries
  if (scrapingStatus.logs.length > 50) {
    scrapingStatus.logs = scrapingStatus.logs.slice(-50);
  }
  
  console.log(`[SCRAPER ${type.toUpperCase()}] ${message}`);
};

// GET /api/scraper/status - Check scraping status
router.get('/status', (req, res) => {
  res.json(scrapingStatus);
});

// POST /api/scraper/start - Trigger scraping
router.post('/start', validateApiKey, async (req, res) => {
  if (scrapingStatus.isRunning) {
    return res.status(429).json({ 
      error: 'Scraping is already running',
      status: scrapingStatus 
    });
  }

  // Check if we should limit frequency (prevent spam)
  const now = new Date();
  if (scrapingStatus.lastRun) {
    const timeSinceLastRun = now - new Date(scrapingStatus.lastRun);
    const minInterval = 30 * 60 * 1000; // 30 minutes minimum between runs
    
    if (timeSinceLastRun < minInterval) {
      return res.status(429).json({
        error: 'Too frequent scraping requests',
        retryAfter: Math.ceil((minInterval - timeSinceLastRun) / 1000 / 60) + ' minutes'
      });
    }
  }

  // Set running status
  scrapingStatus.isRunning = true;
  scrapingStatus.lastRun = now.toISOString();
  scrapingStatus.logs = [];
  
  addLog('Scraping process started');

  // Respond immediately
  res.json({ 
    message: 'Scraping started', 
    status: 'running',
    startTime: scrapingStatus.lastRun
  });

  // Run scraping in background
  runScraping();
});

// Function to execute the scraping process
async function runScraping() {
  try {
    // Determine scraper path - could be relative to API or absolute
    const scraperPath = process.env.SCRAPER_PATH || '../scraper';
    const scraperDir = path.resolve(scraperPath);
    
    addLog(`Using scraper directory: ${scraperDir}`);
    
    // Check if scraper directory exists
    if (!fs.existsSync(scraperDir)) {
      throw new Error(`Scraper directory not found: ${scraperDir}`);
    }
    
    // Check if daily_scraper.py exists
    const dailyScraperPath = path.join(scraperDir, 'daily_scraper.py');
    if (!fs.existsSync(dailyScraperPath)) {
      throw new Error(`daily_scraper.py not found at: ${dailyScraperPath}`);
    }
    
    addLog('Starting scrapy process...');
    
    // Spawn the scraping process
    const child = spawn('python3', [dailyScraperPath], {
      cwd: scraperDir,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PYTHONPATH: scraperDir
      }
    });
    
    let output = '';
    let errorOutput = '';
    
    // Capture stdout
    child.stdout.on('data', (data) => {
      const chunk = data.toString();
      output += chunk;
      addLog(`STDOUT: ${chunk.trim()}`);
    });
    
    // Capture stderr
    child.stderr.on('data', (data) => {
      const chunk = data.toString();
      errorOutput += chunk;
      addLog(`STDERR: ${chunk.trim()}`, 'warn');
    });
    
    // Handle process completion
    child.on('close', (code) => {
      scrapingStatus.isRunning = false;
      
      if (code === 0) {
        addLog('Scraping completed successfully', 'success');
        scrapingStatus.lastResult = {
          success: true,
          output: output.slice(-1000), // Keep last 1000 chars
          completedAt: new Date().toISOString()
        };
      } else {
        addLog(`Scraping failed with exit code: ${code}`, 'error');
        scrapingStatus.lastResult = {
          success: false,
          error: errorOutput.slice(-1000),
          exitCode: code,
          completedAt: new Date().toISOString()
        };
      }
    });
    
    // Handle process errors
    child.on('error', (error) => {
      scrapingStatus.isRunning = false;
      addLog(`Process error: ${error.message}`, 'error');
      scrapingStatus.lastResult = {
        success: false,
        error: error.message,
        completedAt: new Date().toISOString()
      };
    });
    
    // Set timeout (optional - prevent hanging processes)
    const timeout = setTimeout(() => {
      addLog('Scraping timeout reached, killing process', 'warn');
      child.kill('SIGTERM');
      setTimeout(() => {
        if (!child.killed) {
          child.kill('SIGKILL');
        }
      }, 5000);
    }, 30 * 60 * 1000); // 30 minutes timeout
    
    child.on('close', () => {
      clearTimeout(timeout);
    });
    
  } catch (error) {
    scrapingStatus.isRunning = false;
    addLog(`Scraping setup error: ${error.message}`, 'error');
    scrapingStatus.lastResult = {
      success: false,
      error: error.message,
      completedAt: new Date().toISOString()
    };
  }
}

// GET /api/scraper/logs - Get recent logs
router.get('/logs', (req, res) => {
  const limit = parseInt(req.query.limit) || 20;
  const logs = scrapingStatus.logs.slice(-limit);
  res.json({ logs });
});

export default router;
