from scrapy.exceptions import DropItem
import os
import psycopg2
from .normalization_pipeline import NormalizationPipeline
import requests
from ..coordinate import geocode

normalizer = NormalizationPipeline()

async def get_coordinates(address):
    coords = None
    try:
        coords = await geocode(address)
    except Exception as e:
        pass
    return coords

class HousePipeline:
    def open_spider(self, spider):
        try:
            # First try to use DATABASE_URL (preferred for Supabase)
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.conn = psycopg2.connect(
                    database_url,
                    client_encoding='utf8'
                )
                spider.logger.info("✅ Database connection established using DATABASE_URL")
            else:
                # Fallback to individual environment variables
                self.conn = psycopg2.connect(
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", 5432),
                    dbname=os.getenv("DB_NAME", "postgres"),
                    user=os.getenv("DB_USER", "postgres"),
                    password=os.getenv("DB_PASSWORD", "k0410"),
                    client_encoding='utf8'
                )
                spider.logger.info("✅ Database connection established using individual settings")
            
            self.cur = self.conn.cursor()
            spider.logger.info("🗄️  Connected to Supabase database for HousePipeline")
        except Exception as e:
            spider.logger.error(f"❌ Database connection failed: {e}")
            self.conn = None
            self.cur = None

    def process_item(self, item, spider):
        # Skip if no database connection
        if not self.conn or not self.cur:
            spider.logger.warning("⚠️  Skipping database insert - no connection")
            return item
            
        item = normalizer.process_item(item, spider)
        if spider.name != "house_spider":
            return item
            
        try:
            # Log the item being processed
            spider.logger.info(f"💾 Storing house: {item.get('building_name_zh', 'N/A')} - {item.get('type_raw', 'N/A')}")
            
            # Insert into house table (similar structure to store pipeline)
            insert_query = """
                INSERT INTO house (
                    location_id, type, building_name_zh, flat, floor, unit,
                    area, deal_price, deal_date, developer, house_type, estate_name_zh
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Execute the insert
            self.cur.execute(insert_query, (
                item.get('location_id', 1),  # Default location_id
                item.get('type', ''),
                item.get('building_name_zh', ''),
                item.get('flat', ''),
                item.get('floor', ''),
                item.get('unit', ''),
                item.get('area', 0),
                item.get('deal_price', 0),
                item.get('deal_date'),
                item.get('developer', ''),
                item.get('house_type', ''),
                item.get('estate_name_zh', '')
            ))
            
            self.conn.commit()
            spider.logger.info(f"✅ House item saved to database")
            
        except Exception as e:
            spider.logger.error(f"❌ Failed to save house item: {e}")
            self.conn.rollback()
            
        return item

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()
            spider.logger.info("🔌 Database connection closed for HousePipeline")