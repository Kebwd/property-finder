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
    
    async importScrapedProperties(filePath) {
        try {
            console.log(`📁 Loading scraped data from: ${filePath}`);
            
            const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            let properties = [];
            
            // Handle different file formats from scrapers
            if (data.properties) {
                properties = data.properties;
            } else if (data.results) {
                // Expanded scraper format
                for (const cityData of Object.values(data.results)) {
                    if (cityData && cityData.properties) {
                        properties.push(...cityData.properties);
                    }
                }
            } else if (Array.isArray(data)) {
                properties = data;
            }
            
            console.log(`📊 Processing ${properties.length} scraped properties`);
            
            let inserted = 0;
            let updated = 0;
            let errors = 0;
            
            for (const property of properties) {
                try {
                    const result = await this.insertProperty(property);
                    if (result === 'inserted') inserted++;
                    else if (result === 'updated') updated++;
                } catch (error) {
                    console.error(`❌ Error processing property: ${error.message}`);
                    errors++;
                }
            }
            
            console.log('\n📈 IMPORT RESULTS:');
            console.log(`   New properties: ${inserted}`);
            console.log(`   Updated properties: ${updated}`);
            console.log(`   Errors: ${errors}`);
            console.log(`   Total processed: ${properties.length}`);
            
            return { inserted, updated, errors, total: properties.length };
            
        } catch (error) {
            console.error(`❌ Import failed: ${error.message}`);
            throw error;
        }
    }
    
    async insertProperty(propertyData) {
        // Generate unique hash for deduplication
        const hash = this.generatePropertyHash(propertyData);
        
        // Normalize the data to match existing schema
        const normalized = this.normalizePropertyData(propertyData);
        
        const client = await this.pool.connect();
        
        try {
            // Check if property already exists
            const existingQuery = 'SELECT id FROM scraped_properties WHERE property_hash = $1';
            const existing = await client.query(existingQuery, [hash]);
            
            if (existing.rows.length > 0) {
                // Update existing property
                const updateQuery = `
                    UPDATE scraped_properties SET
                        title = $2, price = $3, location = $4, property_type = $5,
                        source_url = $6, source_site = $7, city = $8,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE property_hash = $1
                `;
                
                await client.query(updateQuery, [
                    hash,
                    normalized.title,
                    normalized.price,
                    normalized.location,
                    normalized.property_type,
                    normalized.source_url,
                    normalized.source_site,
                    normalized.city
                ]);
                
                return 'updated';
            } else {
                // Insert new property
                const insertQuery = `
                    INSERT INTO scraped_properties (
                        property_hash, title, price, location, property_type,
                        source_url, source_site, city, scraped_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
                `;
                
                await client.query(insertQuery, [
                    hash,
                    normalized.title,
                    normalized.price,
                    normalized.location,
                    normalized.property_type,
                    normalized.source_url,
                    normalized.source_site,
                    normalized.city
                ]);
                
                return 'inserted';
            }
        } finally {
            client.release();
        }
    }
    
    generatePropertyHash(property) {
        const hashString = `${property.title || ''}_${property.location || ''}_${property.price || ''}`;
        return crypto.createHash('md5').update(hashString.toLowerCase()).digest('hex');
    }
    
    normalizePropertyData(property) {
        return {
            title: String(property.title || property.name || '').trim(),
            price: this.parsePrice(property.price),
            location: String(property.location || property.address || '').trim(),
            property_type: Array.isArray(property.type) ? property.type.join(', ') : String(property.type || ''),
            source_url: String(property.url || '').trim(),
            source_site: String(property.source || '').trim(),
            city: String(property.city || '').trim()
        };
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
        return;
    }
    
    const filePath = process.argv[2];
    const importer = new ScrapedDataImporter();
    
    try {
        await importer.createScrapedPropertiesTable();
        await importer.importScrapedProperties(filePath);
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
