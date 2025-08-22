import psycopg2
import json
import os
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
import hashlib
import re

class PropertyDatabaseIntegration:
    """
    Database integration pipeline for scraped property data
    Handles PostgreSQL insertion, deduplication, and data management
    """
    
    def __init__(self, db_config: Dict[str, str] = None):
        self.db_config = db_config or self.load_db_config()
        self.setup_logging()
        self.connection = None
        
    def load_db_config(self) -> Dict[str, str]:
        """Load database configuration using same method as scrapy"""
        # Use the same DATABASE_URL approach as your working scrapy system
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            self.database_url = database_url
            self.logger.info("✅ Using DATABASE_URL (same as scrapy system)")
            return {'use_url': True, 'database_url': database_url}
        else:
            # Fallback to individual environment variables (same as scrapy)
            config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'postgres'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'k0410')
            }
            self.logger.info("⚠️ Using fallback DB settings (same as scrapy)")
            return config
    
    def setup_logging(self):
        """Setup logging for database operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def connect(self) -> bool:
        """Establish database connection using same method as scrapy"""
        try:
            # Use the same connection logic as your working scrapy system
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.connection = psycopg2.connect(
                    database_url,
                    client_encoding='utf8'
                )
                self.logger.info("✅ Database connection established using DATABASE_URL (same as scrapy)")
            else:
                # Fallback to individual environment variables (same as scrapy)
                self.connection = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", 5432),
                    dbname=os.getenv("DB_NAME", "postgres"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", "k0410"),
                    client_encoding='utf8'
                )
                self.logger.info("✅ Database connection established using individual settings (same as scrapy)")
            
            self.logger.info("🗄️ Connected to Supabase database (same as your scrapy system)")
            return True
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("🔌 Database connection closed")
    
    def create_tables(self):
        """Create necessary tables for scraped property data"""
        try:
            cursor = self.connection.cursor()
            
            # Create scraped_properties table
            create_properties_table = """
            CREATE TABLE IF NOT EXISTS scraped_properties (
                id SERIAL PRIMARY KEY,
                property_hash VARCHAR(64) UNIQUE NOT NULL,
                title TEXT NOT NULL,
                price DECIMAL(15,2),
                location TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                size_sqft INTEGER,
                property_type VARCHAR(100),
                source_url TEXT,
                source_site VARCHAR(100),
                city VARCHAR(100),
                district VARCHAR(100),
                description TEXT,
                image_urls JSON,
                contact_info JSON,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # Create scraping_runs table for tracking
            create_runs_table = """
            CREATE TABLE IF NOT EXISTS scraping_runs (
                id SERIAL PRIMARY KEY,
                run_date DATE NOT NULL,
                run_type VARCHAR(50) NOT NULL,
                properties_scraped INTEGER DEFAULT 0,
                properties_new INTEGER DEFAULT 0,
                properties_updated INTEGER DEFAULT 0,
                cities_scraped TEXT[],
                success_rate DECIMAL(5,2),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status VARCHAR(20) DEFAULT 'completed',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # Create indexes for performance
            create_indexes = """
            CREATE INDEX IF NOT EXISTS idx_scraped_properties_hash ON scraped_properties(property_hash);
            CREATE INDEX IF NOT EXISTS idx_scraped_properties_city ON scraped_properties(city);
            CREATE INDEX IF NOT EXISTS idx_scraped_properties_type ON scraped_properties(property_type);
            CREATE INDEX IF NOT EXISTS idx_scraped_properties_price ON scraped_properties(price);
            CREATE INDEX IF NOT EXISTS idx_scraped_properties_scraped_at ON scraped_properties(scraped_at);
            CREATE INDEX IF NOT EXISTS idx_scraping_runs_date ON scraping_runs(run_date);
            """
            
            cursor.execute(create_properties_table)
            cursor.execute(create_runs_table)
            cursor.execute(create_indexes)
            
            self.connection.commit()
            cursor.close()
            
            self.logger.info("✅ Database tables created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create tables: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def generate_property_hash(self, property_data: Dict[str, Any]) -> str:
        """Generate unique hash for property to detect duplicates"""
        # Use title, location, and price to create unique identifier
        hash_string = f"{property_data.get('title', '')}_{property_data.get('location', '')}_{property_data.get('price', '')}"
        hash_string = re.sub(r'\s+', ' ', hash_string.lower().strip())
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def normalize_property_data(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize property data for database insertion"""
        normalized = {}
        
        # Required fields
        normalized['title'] = str(property_data.get('title', '')).strip()
        normalized['property_hash'] = self.generate_property_hash(property_data)
        
        # Price processing
        price_str = str(property_data.get('price', '0'))
        price_clean = re.sub(r'[^\d.]', '', price_str)
        try:
            normalized['price'] = float(price_clean) if price_clean else None
        except:
            normalized['price'] = None
        
        # Location fields
        normalized['location'] = str(property_data.get('location', '')).strip() or None
        normalized['city'] = str(property_data.get('city', '')).strip() or None
        normalized['district'] = str(property_data.get('district', '')).strip() or None
        
        # Property details
        try:
            normalized['bedrooms'] = int(property_data.get('bedrooms', 0)) or None
        except:
            normalized['bedrooms'] = None
            
        try:
            normalized['bathrooms'] = int(property_data.get('bathrooms', 0)) or None
        except:
            normalized['bathrooms'] = None
            
        try:
            size_str = str(property_data.get('size', '0'))
            size_clean = re.sub(r'[^\d.]', '', size_str)
            normalized['size_sqft'] = int(float(size_clean)) if size_clean else None
        except:
            normalized['size_sqft'] = None
        
        # Property type normalization
        prop_type = str(property_data.get('type', '')).strip()
        if isinstance(property_data.get('type'), list):
            prop_type = ', '.join(property_data['type'])
        normalized['property_type'] = prop_type or None
        
        # URLs and metadata
        normalized['source_url'] = str(property_data.get('url', '')).strip() or None
        normalized['source_site'] = str(property_data.get('source', '')).strip() or None
        normalized['description'] = str(property_data.get('description', '')).strip() or None
        
        # JSON fields
        normalized['image_urls'] = property_data.get('images', []) if property_data.get('images') else None
        normalized['contact_info'] = property_data.get('contact', {}) if property_data.get('contact') else None
        
        return normalized
    
    def insert_property(self, property_data: Dict[str, Any]) -> bool:
        """Insert or update a single property"""
        try:
            normalized = self.normalize_property_data(property_data)
            cursor = self.connection.cursor()
            
            # Check if property already exists
            check_query = "SELECT id, updated_at FROM scraped_properties WHERE property_hash = %s"
            cursor.execute(check_query, (normalized['property_hash'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing property
                update_query = """
                UPDATE scraped_properties SET
                    title = %s, price = %s, location = %s, bedrooms = %s, bathrooms = %s,
                    size_sqft = %s, property_type = %s, source_url = %s, source_site = %s,
                    city = %s, district = %s, description = %s, image_urls = %s,
                    contact_info = %s, updated_at = CURRENT_TIMESTAMP
                WHERE property_hash = %s
                """
                cursor.execute(update_query, (
                    normalized['title'], normalized['price'], normalized['location'],
                    normalized['bedrooms'], normalized['bathrooms'], normalized['size_sqft'],
                    normalized['property_type'], normalized['source_url'], normalized['source_site'],
                    normalized['city'], normalized['district'], normalized['description'],
                    json.dumps(normalized['image_urls']) if normalized['image_urls'] else None,
                    json.dumps(normalized['contact_info']) if normalized['contact_info'] else None,
                    normalized['property_hash']
                ))
                cursor.close()
                return 'updated'
            else:
                # Insert new property
                insert_query = """
                INSERT INTO scraped_properties (
                    property_hash, title, price, location, bedrooms, bathrooms, size_sqft,
                    property_type, source_url, source_site, city, district, description,
                    image_urls, contact_info
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    normalized['property_hash'], normalized['title'], normalized['price'],
                    normalized['location'], normalized['bedrooms'], normalized['bathrooms'],
                    normalized['size_sqft'], normalized['property_type'], normalized['source_url'],
                    normalized['source_site'], normalized['city'], normalized['district'],
                    normalized['description'],
                    json.dumps(normalized['image_urls']) if normalized['image_urls'] else None,
                    json.dumps(normalized['contact_info']) if normalized['contact_info'] else None
                ))
                cursor.close()
                return 'inserted'
                
        except Exception as e:
            self.logger.error(f"❌ Failed to insert property: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def import_scraping_results(self, file_path: str) -> Dict[str, int]:
        """Import scraped property data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats = {
                'total_processed': 0,
                'inserted': 0,
                'updated': 0,
                'errors': 0
            }
            
            properties = []
            
            # Handle different file formats
            if 'properties' in data:
                properties = data['properties']
            elif 'results' in data:
                # Handle expanded scraper format
                for city_data in data['results'].values():
                    if isinstance(city_data, dict) and 'properties' in city_data:
                        properties.extend(city_data['properties'])
            elif isinstance(data, list):
                properties = data
            
            self.logger.info(f"📊 Processing {len(properties)} properties from {file_path}")
            
            for prop in properties:
                stats['total_processed'] += 1
                result = self.insert_property(prop)
                
                if result == 'inserted':
                    stats['inserted'] += 1
                elif result == 'updated':
                    stats['updated'] += 1
                else:
                    stats['errors'] += 1
                
                # Commit every 100 properties
                if stats['total_processed'] % 100 == 0:
                    self.connection.commit()
                    self.logger.info(f"✅ Processed {stats['total_processed']} properties...")
            
            # Final commit
            self.connection.commit()
            
            self.logger.info(f"✅ Import complete: {stats['inserted']} new, {stats['updated']} updated, {stats['errors']} errors")
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Import failed: {e}")
            if self.connection:
                self.connection.rollback()
            return {'error': str(e)}
    
    def log_scraping_run(self, run_type: str, stats: Dict[str, Any]):
        """Log scraping run statistics"""
        try:
            cursor = self.connection.cursor()
            
            insert_run = """
            INSERT INTO scraping_runs (
                run_date, run_type, properties_scraped, properties_new, properties_updated,
                cities_scraped, success_rate, start_time, end_time, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_run, (
                datetime.now().date(),
                run_type,
                stats.get('total_processed', 0),
                stats.get('inserted', 0),
                stats.get('updated', 0),
                stats.get('cities', []),
                stats.get('success_rate', 0.0),
                stats.get('start_time'),
                stats.get('end_time'),
                'completed'
            ))
            
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log scraping run: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            cursor = self.connection.cursor()
            
            stats = {}
            
            # Total properties
            cursor.execute("SELECT COUNT(*) FROM scraped_properties")
            stats['total_properties'] = cursor.fetchone()[0]
            
            # Properties by city
            cursor.execute("""
                SELECT city, COUNT(*) 
                FROM scraped_properties 
                WHERE city IS NOT NULL 
                GROUP BY city 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            stats['top_cities'] = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute("""
                SELECT DATE(scraped_at) as date, COUNT(*) 
                FROM scraped_properties 
                WHERE scraped_at > CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(scraped_at) 
                ORDER BY date DESC
            """)
            stats['recent_activity'] = dict(cursor.fetchall())
            
            # Average price by city
            cursor.execute("""
                SELECT city, ROUND(AVG(price), 2) as avg_price
                FROM scraped_properties 
                WHERE price IS NOT NULL AND city IS NOT NULL
                GROUP BY city 
                ORDER BY avg_price DESC 
                LIMIT 10
            """)
            stats['avg_prices'] = dict(cursor.fetchall())
            
            cursor.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def import_all_daily_files(self, date_str: str = None) -> Dict[str, Any]:
        """Import all scraping files for a specific date"""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')
        
        files_to_import = [
            f'morning_scrape_{date_str}.json',
            f'afternoon_scrape_{date_str}.json'
        ]
        
        total_stats = {
            'total_processed': 0,
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'files_processed': []
        }
        
        for file_path in files_to_import:
            if os.path.exists(file_path):
                self.logger.info(f"📁 Importing {file_path}...")
                file_stats = self.import_scraping_results(file_path)
                
                if 'error' not in file_stats:
                    total_stats['total_processed'] += file_stats['total_processed']
                    total_stats['inserted'] += file_stats['inserted']
                    total_stats['updated'] += file_stats['updated']
                    total_stats['errors'] += file_stats['errors']
                    total_stats['files_processed'].append(file_path)
        
        # Log the combined run
        self.log_scraping_run('daily_import', total_stats)
        
        return total_stats

def main():
    """Main function for database integration testing"""
    print("🗄️ PROPERTY DATABASE INTEGRATION PIPELINE")
    print("=" * 50)
    
    # Initialize database integration
    db_integration = PropertyDatabaseIntegration()
    
    if not db_integration.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        # Create tables
        print("\n📋 Creating database tables...")
        if db_integration.create_tables():
            print("✅ Tables created successfully")
        
        # Import today's files
        print("\n📥 Importing today's scraping results...")
        today = datetime.now().strftime('%Y%m%d')
        import_stats = db_integration.import_all_daily_files(today)
        
        print(f"\n📊 IMPORT RESULTS:")
        print(f"   Total processed: {import_stats['total_processed']}")
        print(f"   New properties: {import_stats['inserted']}")
        print(f"   Updated properties: {import_stats['updated']}")
        print(f"   Errors: {import_stats['errors']}")
        print(f"   Files processed: {import_stats['files_processed']}")
        
        # Show database statistics
        print(f"\n📈 DATABASE STATISTICS:")
        stats = db_integration.get_database_stats()
        print(f"   Total properties in database: {stats.get('total_properties', 0)}")
        
        if stats.get('top_cities'):
            print(f"   Top cities:")
            for city, count in list(stats['top_cities'].items())[:5]:
                print(f"     - {city}: {count} properties")
        
        print(f"\n🎉 Database integration completed successfully!")
        
    finally:
        db_integration.disconnect()

if __name__ == "__main__":
    main()
