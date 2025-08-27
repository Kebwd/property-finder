// Alternative Database Integration for Property Scraper
// Integrates with existing property-finder-api database

import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import pkg from 'pg';
const { Pool } = pkg;

class ScrapedDataImporter {
    constructor() {
        this.pool = new Pool({
            connectionString: process.env.DATABASE_URL,
            // Production database configuration matches API
        });
        
        console.log('🗄️ SCRAPED DATA IMPORTER');
        console.log('========================');
    }
    
    async importDealTrackingData(filePath) {
        try {
            console.log(`📁 Loading deal tracking data from: ${filePath}`);
            
            const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            const deals = data.current_deals || [];
            
            console.log(`📊 Processing ${deals.length} deals`);
            
            let inserted = 0;
            let skipped = 0;
            let errors = 0;
            
            for (const dealString of deals) {
                try {
                    const result = await this.insertDeal(dealString);
                    if (result === 'inserted') inserted++;
                    else if (result === 'skipped') skipped++;
                } catch (error) {
                    console.error(`❌ Error processing deal: ${error.message}`);
                    errors++;
                }
            }
            
            console.log('\n📈 IMPORT RESULTS:');
            console.log(`   New deals: ${inserted}`);
            console.log(`   Skipped (already exist): ${skipped}`);
            console.log(`   Errors: ${errors}`);
            console.log(`   Total processed: ${deals.length}`);
            
            return { inserted, skipped, errors, total: deals.length };
            
        } catch (error) {
            console.error(`❌ Import failed: ${error.message}`);
            throw error;
        }
    }
    
    async insertDeal(dealString) {
        // Parse deal string format: "building_location_room_price_date"
        const parts = dealString.split('_');
        if (parts.length < 5) {
            throw new Error(`Invalid deal format: ${dealString}`);
        }
        
        const building = parts[0];
        const location = parts[1];
        const room = parts[2];
        const price = parts[3];
        const date = parts[4];
        
        // Parse price (remove $ and convert 萬 to number)
        const priceNum = this.parsePrice(price);
        
        // Parse date (DD/MM/YYYY to YYYY-MM-DD)
        const [day, month, year] = date.split('/');
        const isoDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        
        // Extract location components
        const locationParts = location.split(' ');
        const district = locationParts[0]; // e.g., "荃灣"
        const address = locationParts.slice(1).join(' '); // rest of address
        
        // Determine property type (business if commercial building names)
        const isBusiness = this.isBusinessProperty(building, address);
        const propertyType = isBusiness ? 'business' : 'house';
        
        const client = await this.pool.connect();
        
        try {
            // Check if deal already exists
            const existingQuery = `
                SELECT id FROM ${propertyType} 
                WHERE building_name_zh = $1 
                AND deal_date = $2 
                AND deal_price = $3
            `;
            const existing = await client.query(existingQuery, [building, isoDate, priceNum]);
            
            if (existing.rows.length > 0) {
                return 'skipped';
            }
            
            // Get or create location
            let locationId;
            const locationQuery = `
                SELECT id FROM location_info 
                WHERE building_name_zh = $1 
                OR name = $1
                LIMIT 1
            `;
            const existingLocation = await client.query(locationQuery, [building]);
            
            if (existingLocation.rows.length > 0) {
                locationId = existingLocation.rows[0].id;
            } else {
                // Create new location (we'll need coordinates - for now use dummy coordinates)
                const insertLocationQuery = `
                    INSERT INTO location_info (
                        building_name_zh, name, province, city, country, town, street, road,
                        lat, lng, geom
                    ) VALUES ($1, $1, '香港', $2, '中國', $2, $3, $3, 
                             22.3193, 114.1694, 
                             ST_SetSRID(ST_Point(114.1694, 22.3193), 4326))
                    RETURNING id
                `;
                const locationResult = await client.query(insertLocationQuery, [building, district, address]);
                locationId = locationResult.rows[0].id;
                console.log(`📍 Created new location: ${building} in ${district}`);
            }
            
            // Insert deal
            let insertQuery, values;
            if (propertyType === 'business') {
                insertQuery = `
                    INSERT INTO business (
                        type, building_name_zh, floor, unit, area, deal_price, deal_date, developer, location_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                `;
                values = [
                    '商舖', building, this.extractFloor(address), room, null, priceNum, isoDate, null, locationId
                ];
            } else {
                insertQuery = `
                    INSERT INTO house (
                        type, estate_name_zh, flat, building_name_zh, floor, unit, area, 
                        house_type, deal_price, deal_date, developer, location_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                `;
                values = [
                    '住宅', building, room, building, this.extractFloor(address), room, null,
                    '住宅', priceNum, isoDate, null, locationId
                ];
            }
            
            await client.query(insertQuery, values);
            console.log(`✅ Inserted ${propertyType} deal: ${building} - ${price}`);
            return 'inserted';
            
        } finally {
            client.release();
        }
    }
    
    parsePrice(priceStr) {
        // Remove $ and convert Chinese numbers
        let numStr = priceStr.replace('$', '').replace('萬', '');
        const multiplier = priceStr.includes('萬') ? 10000 : 1;
        return parseFloat(numStr) * multiplier;
    }
    
    isBusinessProperty(building, address) {
        // Determine if this is a business/commercial property
        const businessKeywords = ['商業中心', '企業中心', '大厦', '商業大厦', '寫字樓', '商舖'];
        return businessKeywords.some(keyword => 
            building.includes(keyword) || address.includes(keyword)
        );
    }
    
    extractFloor(address) {
        // Extract floor number from address
        const floorMatch = address.match(/([中高低])層/);
        if (floorMatch) {
            const floorType = floorMatch[1];
            switch (floorType) {
                case '低': return '低層';
                case '中': return '中層';
                case '高': return '高層';
                default: return '中層';
            }
        }
        return '中層'; // default
    }
    
    parsePrice(priceStr) {
        if (!priceStr) return null;
        const cleaned = String(priceStr).replace(/[^\d.]/g, '');
        const parsed = parseFloat(cleaned);
        return isNaN(parsed) ? null : parsed;
    }
    
    async createScrapedPropertiesTable() {
        const client = await this.pool.connect();
        
        try {
            const createTableQuery = `
                CREATE TABLE IF NOT EXISTS scraped_properties (
                    id SERIAL PRIMARY KEY,
                    property_hash VARCHAR(64) UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    price DECIMAL(15,2),
                    location TEXT,
                    property_type VARCHAR(200),
                    source_url TEXT,
                    source_site VARCHAR(100),
                    city VARCHAR(100),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_scraped_properties_hash 
                ON scraped_properties(property_hash);
                
                CREATE INDEX IF NOT EXISTS idx_scraped_properties_city 
                ON scraped_properties(city);
            `;
            
            await client.query(createTableQuery);
            console.log('✅ Scraped properties table ready');
            
        } finally {
            client.release();
        }
    }
    
    async close() {
        await this.pool.end();
        console.log('🔌 Database connection closed');
    }
}

// Command line interface
async function main() {
    if (process.argv.length < 3) {
        console.log('Usage: node scraped_data_importer.js <json_file_path>');
        console.log('Example: node scraped_data_importer.js morning_scrape_20250822.json');
        console.log('For deal tracking: node scraped_data_importer.js deal_tracking.json');
        return;
    }
    
    const filePath = process.argv[2];
    const importer = new ScrapedDataImporter();
    
    try {
        // Check if this is deal tracking data
        if (filePath.includes('deal_tracking.json')) {
            console.log('📋 Importing deal tracking data...');
            await importer.importDealTrackingData(filePath);
        } else {
            // Regular scraped properties import
            await importer.createScrapedPropertiesTable();
            await importer.importScrapedProperties(filePath);
        }
        console.log('\n🎉 Import completed successfully!');
    } catch (error) {
        console.error('❌ Import failed:', error.message);
    } finally {
        await importer.close();
    }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main();
}

export default ScrapedDataImporter;
