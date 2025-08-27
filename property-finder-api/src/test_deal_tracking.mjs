import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test the deal tracking fallback logic for Vercel API
async function testDealTracking() {
  // Try multiple possible paths for Vercel deployment
  const possiblePaths = [
    path.join(__dirname, 'deal_tracking.json'),  // Local copy in API directory
    path.join(__dirname, '../../../scraper/deal_tracking.json'),
    path.join(__dirname, '../../../../scraper/deal_tracking.json'),
    path.join(__dirname, '../../scraper/deal_tracking.json'),
    path.join(__dirname, '../scraper/deal_tracking.json'),
    '/tmp/deal_tracking.json'
  ];

  let dealTrackingPath = null;
  for (const testPath of possiblePaths) {
    try {
      if (fs.existsSync(testPath)) {
        dealTrackingPath = testPath;
        console.log(`✅ Found deal tracking file at: ${testPath}`);
        break;
      }
    } catch (err) {
      console.log(`❌ Error checking path ${testPath}: ${err.message}`);
    }
  }

  if (!dealTrackingPath) {
    console.log('❌ Deal tracking file not found in any expected location');
    return;
  }

  const data = JSON.parse(fs.readFileSync(dealTrackingPath, 'utf8'));
  const deals = data.current_deals || [];

  console.log(`\n📋 Found ${deals.length} deals:`);
  deals.forEach(deal => {
    const parts = deal.split('_');
    if (parts.length >= 2) {
      console.log(`🏢 Building: "${parts[0]}"`);
      console.log(`📍 Full address: "${parts[1]}"`);
    }
  });

  // Test specific queries
  const testQueries = [
    '國際企業中心1期',
    '荃灣 國際企業中心1期 中層 8室'
  ];

  console.log('\n🔍 Testing queries:');
  testQueries.forEach(query => {
    console.log(`\n❓ Query: "${query}"`);

    for (const dealString of deals) {
      const parts = dealString.split('_');
      if (parts.length < 2) continue;

      const building = parts[0];
      const fullAddress = parts[1];

      const matches = [
        building === query,
        query.includes(building),
        building.includes(query),
        fullAddress.includes(query),
        query.split(' ').some(word => fullAddress.includes(word) && word.length > 2)
      ];

      if (matches.some(match => match)) {
        console.log(`  ✅ MATCH: ${dealString}`);

        // Extract location info from deal string
        const location = parts[1];

        // Use coordinates based on location keywords
        let lat = 22.3686, lng = 114.1048; // Default Tsuen Wan coordinates

        if (location.includes('荃灣') || location.includes('Tsuen Wan')) {
          lat = 22.3686; lng = 114.1048; // Tsuen Wan
        } else if (location.includes('中環') || location.includes('Central')) {
          lat = 22.2819; lng = 114.1588; // Central
        } else if (location.includes('尖沙咀') || location.includes('Tsim Sha Tsui')) {
          lat = 22.2969; lng = 114.1722; // Tsim Sha Tsui
        } else if (location.includes('上環') || location.includes('Sheung Wan')) {
          lat = 22.2867; lng = 114.1491; // Sheung Wan
        } else if (location.includes('元朗') || location.includes('Yuen Long')) {
          lat = 22.4414; lng = 114.0222; // Yuen Long
        }

        console.log(`  📍 Coordinates: ${lat}, ${lng}`);
        break; // Only show first match
      }
    }
  });
}

testDealTracking();
