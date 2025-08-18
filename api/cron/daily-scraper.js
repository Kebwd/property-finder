const { spawn } = require('child_process');
const path = require('path');

module.exports = async function handler(req, res) {
  // Verify the request is from Vercel Cron or has the correct API key
  const authHeader = req.headers.authorization;
  const expectedKey = process.env.SCRAPER_API_KEY;
  
  if (!authHeader || authHeader !== `Bearer ${expectedKey}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    console.log('🕷️ Starting daily scraper via Vercel Cron...');
    
    // This would need the scraper code to be adapted for serverless
    // For now, we'll return a trigger response and use external service
    
    // Option: Trigger GitHub Action via API
    const triggerUrl = `https://api.github.com/repos/${process.env.GITHUB_REPO}/actions/workflows/daily-scraper.yml/dispatches`;
    
    const response = await fetch(triggerUrl, {
      method: 'POST',
      headers: {
        'Authorization': `token ${process.env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ref: 'main'
      })
    });

    if (response.ok) {
      console.log('✅ Successfully triggered GitHub Action scraper');
      return res.status(200).json({
        success: true,
        message: 'Daily scraper triggered successfully',
        timestamp: new Date().toISOString()
      });
    } else {
      throw new Error('Failed to trigger GitHub Action');
    }

  } catch (error) {
    console.error('❌ Scraper trigger error:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};
