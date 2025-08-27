const fs = require('fs');
const path = require('path');

// Test the updated deal tracking path resolution
async function testUpdatedPaths() {
  // Try multiple possible paths for Vercel deployment (updated order)
  const possiblePaths = [
    path.join(process.cwd(), 'deal_tracking.json'),  // Local copy in api directory (highest priority)
    path.join(process.cwd(), '../scraper/deal_tracking.json'),
    path.join(process.cwd(), '../../scraper/deal_tracking.json'),
    path.join(process.cwd(), 'scraper/deal_tracking.json'),
    '/tmp/deal_tracking.json'
  ];

  let dealTrackingPath = null;
  for (const testPath of possiblePaths) {
    try {
      if (fs.existsSync(testPath)) {
        dealTrackingPath = testPath;
        console.log(`✅ Found deal tracking file at: ${testPath}`);
        break;
      } else {
        console.log(`❌ Path not found: ${testPath}`);
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

  console.log(`\n📋 Found ${deals.length} deals in file: ${dealTrackingPath}`);

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
        console.log(`  📍 Will use coordinates for: ${fullAddress}`);
        break;
      }
    }
  });
}

testUpdatedPaths();
