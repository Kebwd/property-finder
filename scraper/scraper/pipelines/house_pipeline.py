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

    def get_or_create_location(self, item, spider):
        """
        Find or create a location record based on the item data.
        Returns the location_id to use for the house record.
        """
        try:
            # Extract location data from item
            zone = item.get('zone', '')
            town = item.get('town', '')
            street = item.get('street', '')
            
            if not town:
                spider.logger.warning("⚠️  No town data, using default location_id=1")
                return 1
            
            # Determine country and province based on zone
            if zone == 'China':
                country = '中国'
                province = '广东省'  # Assuming Shenzhen area for now
                city = '深圳市'
            else:
                country = '香港'
                province = '香港'
                city = town  # For HK, city might be the same as town
            
            # First, try to find existing location (including street data)
            if street and street.strip():
                self.cur.execute("""
                    SELECT id FROM location_info 
                    WHERE town = %s AND country = %s AND street = %s
                    LIMIT 1
                """, (town, country, street))
            else:
                self.cur.execute("""
                    SELECT id FROM location_info 
                    WHERE town = %s AND country = %s AND (street IS NULL OR street = '')
                    LIMIT 1
                """, (town, country))
            
            result = self.cur.fetchone()
            if result:
                location_id = result[0]
                spider.logger.debug(f"📍 Found existing location_id {location_id} for {town}, {country}" + (f" - {street}" if street else ""))
                return location_id
            
            # If not found, create new location record with geocoding
            lat, lng, geom = None, None, None
            
            # Attempt to geocode the location
            try:
                # Create address for geocoding - use street + town for better accuracy
                address_parts = []
                if street and street.strip():
                    address_parts.append(street)
                address_parts.append(town)
                
                if zone == 'China':
                    address_parts.extend(['深圳市', '广东省', '中国'])
                    geocode_address = ', '.join(address_parts)
                    coords = geocode(geocode_address, zone="China")
                else:
                    address_parts.append('香港')
                    geocode_address = ', '.join(address_parts)
                    coords = geocode(geocode_address, zone="HK")
                
                if coords:
                    lat = coords['lat']
                    lng = coords['lng']
                    # Create PostGIS point geometry
                    geom = f"POINT({lng} {lat})"
                    spider.logger.info(f"🌍 Geocoded {geocode_address}: {lat}, {lng}")
                
            except Exception as geo_error:
                spider.logger.warning(f"⚠️  Geocoding failed for {town}: {geo_error}")
            
            # Insert new location record (including street data)
            if lat and lng:
                self.cur.execute("""
                    INSERT INTO location_info (province, city, country, town, street, lat, long, geom)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))
                    RETURNING id
                """, (province, city, country, town, street, lat, lng, geom))
            else:
                self.cur.execute("""
                    INSERT INTO location_info (province, city, country, town, street)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (province, city, country, town, street))
            
            location_id = self.cur.fetchone()[0]
            self.conn.commit()
            spider.logger.info(f"🆕 Created new location_id {location_id} for {town}, {country}")
            return location_id
            
        except Exception as e:
            spider.logger.error(f"❌ Error handling location data: {e}")
            self.conn.rollback()
            return 1  # Fallback to default location_id

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
            
            # Handle location data - find or create location record
            location_id = self.get_or_create_location(item, spider)
            
            # Insert into house table (with source_url field, street stored in location_info)
            insert_query = """
                INSERT INTO house (
                    location_id, type, building_name_zh, flat, floor, unit,
                    area, deal_price, deal_date, developer, house_type, estate_name_zh, source_url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Execute the insert
            self.cur.execute(insert_query, (
                location_id,  # Use the found/created location_id
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
                item.get('estate_name_zh', ''),
                item.get('source_url', '')
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