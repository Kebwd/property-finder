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

class StorePipeline:
    def open_spider(self, spider):
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", 5432),
                dbname=os.getenv("DB_NAME", "postgres"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "k0410"),
                client_encoding='utf8'  # Fix encoding issue
            )
            self.cur = self.conn.cursor()
            spider.logger.info("✅ Database connection established")
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
        if spider.name != "store_spider":
            return item
            
        try:
            # Log the item being processed
            spider.logger.info(f"💾 Storing: {item.get('building_name_zh', 'N/A')} - {item.get('type_raw', 'N/A')}")
            
            # Get zone from item instead of spider
            zone = item.get("zone", "Unknown")
            
            if zone == "Hong Kong":
                self._process_hong_kong_item(item, spider)
            elif zone == "China":
                self._process_china_item(item, spider)
            else:
                spider.logger.warning(f"⚠️  Unknown zone: {zone}")
                
        except Exception as e:
            self.conn.rollback()
            spider.logger.error(f"❌ Database error: {e}")
            spider.logger.error(f"   Item: {item}")
        
        return item

    def _process_hong_kong_item(self, item, spider):
        """Process Hong Kong property deals"""
        # Check if deal already exists to avoid duplicates
        building_name = item.get("building_name_zh", "")
        deal_price = item.get("deal_price", "")
        deal_date = item.get("deal_date", "")
        floor = item.get("floor", "")
        unit = item.get("unit", "")
        
        # Check for existing deal
        self.cur.execute("""
            SELECT id FROM business 
            WHERE building_name_zh = %s 
            AND deal_price = %s 
            AND deal_date = %s 
            AND floor = %s 
            AND unit = %s
        """, (building_name, deal_price, deal_date, floor, unit))
        
        if self.cur.fetchone():
            spider.logger.debug(f"⏭️  Deal already exists in database: {building_name}")
            return
        
        # Create location_info record with scraped address data
        location_id = self._create_or_get_location_info(item, spider)
        
        # Insert business record
        hk_values = (
            item.get("type"),
            building_name,
            floor,
            unit,
            item.get("area"),
            deal_date,
            deal_price,
            item.get("developer"),
            location_id
        )
        
        self.cur.execute("""
            INSERT INTO business (type, building_name_zh, floor, unit, area, deal_date, deal_price, developer, location_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, hk_values)
        
        self.conn.commit()
        spider.logger.info(f"✅ Stored HK deal: {building_name} - {deal_price}")

    def _process_china_item(self, item, spider):
        """Process China property deals"""
        # Similar structure for China deals
        building_name = item.get("building_name_zh", "")
        deal_price = item.get("deal_price", "")
        deal_date = item.get("deal_date", "")
        
        # Check for existing deal
        self.cur.execute("""
            SELECT id FROM business 
            WHERE building_name_zh = %s 
            AND deal_price = %s 
            AND deal_date = %s
        """, (building_name, deal_price, deal_date))
        
        if self.cur.fetchone():
            spider.logger.debug(f"⏭️  Deal already exists in database: {building_name}")
            return
        
        cn_location_values = (
            item.get("province"),
            item.get("city"),
            item.get("country"),
            item.get("town"),
            item.get("street"),
            item.get("road")
        )
        
        cn_values = (
            item.get("type"),
            building_name,
            item.get("floor"),
            item.get("unit"),
            item.get("area"),
            deal_date,
            deal_price,
            item.get("developer")
        )
        
        # Get coordinates
        try:
            # Call geocode directly instead of the async wrapper
            from ..coordinate import geocode
            location = geocode(str(cn_location_values))
        except:
            location = None
            spider.logger.warning(f"⚠️  Could not geocode China location")
        
        # Insert location and business record
        if location:
            self.cur.execute("""
                INSERT INTO location_info (province, city, country, town, street, road, lat, long, geom)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                RETURNING id
            """, cn_location_values + (location.lat, location.lng, location.lng, location.lat))
            location_id = self.cur.fetchone()[0]
        else:
            location_id = None
        
        self.cur.execute("""
            INSERT INTO business (type, building_name_zh, floor, unit, area, deal_date, deal_price, developer, location_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, cn_values + (location_id,))
        
        self.conn.commit()
        spider.logger.info(f"✅ Stored China deal: {building_name} - {deal_price}")

    def _create_or_get_location_info(self, item, spider):
        """Create or get location_info record based on scraped data"""
        building_name = item.get("building_name_zh", "") or ""
        
        # Extract location details from item (if available)
        address = item.get("address", building_name) or building_name
        district = item.get("district", "") or ""
        area = item.get("area_name", "") or ""
        
        # Try to create a more specific location record
        # For Hong Kong properties, extract district/area information
        if "Hong Kong" in item.get("zone", ""):
            province = "Hong Kong"
            
            # Try to determine city/district from building name or other fields
            if building_name and any(keyword in building_name for keyword in ["中環", "Central"]):
                city = "Hong Kong Island"
                country = "Central and Western"
                town = "Central"
                street = "Central District"
                road = building_name
            elif building_name and any(keyword in building_name for keyword in ["尖沙咀", "Tsim Sha Tsui", "九龍", "Kowloon"]):
                city = "Kowloon"
                country = "Yau Tsim Mong"
                town = "Tsim Sha Tsui"
                street = "Nathan Rd"
                road = building_name
            elif building_name and any(keyword in building_name for keyword in ["筲箕灣", "Shau Kei Wan"]):
                city = "Hong Kong Island"
                country = "Eastern"
                town = "Shau Kei Wan"
                street = "Shau Kei Wan Road"
                road = building_name
            else:
                # Default to Kowloon for other HK properties
                city = "Kowloon"
                country = "Yau Tsim Mong"
                town = "Tsim Sha Tsui"
                street = "Nathan Rd"
                road = building_name or "Unknown Building"
            
            # Check if this location already exists
            self.cur.execute("""
                SELECT id FROM location_info 
                WHERE province = %s AND city = %s AND country = %s AND road = %s
                LIMIT 1
            """, (province, city, country, road))
            
            existing_location = self.cur.fetchone()
            if existing_location:
                spider.logger.debug(f"📍 Using existing location: {existing_location[0]} for {building_name}")
                return existing_location[0]
            
            # Try to geocode the address
            try:
                from ..coordinate import geocode
                location = geocode(address)
                if location:
                    lat, lng = location.lat, location.lng
                    spider.logger.debug(f"📍 Geocoded {building_name}: {lat}, {lng}")
                else:
                    # Use default Hong Kong coordinates
                    lat, lng = 22.298, 114.172
                    spider.logger.warning(f"⚠️  Using default coordinates for {building_name}")
            except Exception as e:
                # Use default Hong Kong coordinates
                lat, lng = 22.298, 114.172
                spider.logger.warning(f"⚠️  Geocoding failed for {building_name}, using default coordinates")
            
            # Create new location record
            try:
                self.cur.execute("""
                    INSERT INTO location_info (province, city, country, town, street, road, lat, long, geom)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    RETURNING id
                """, (province, city, country, town, street, road, lat, lng, lng, lat))
                
                location_id = self.cur.fetchone()[0]
                spider.logger.info(f"📍 Created new location: {location_id} for {building_name} in {town}, {city}")
                return location_id
                
            except Exception as e:
                spider.logger.error(f"❌ Failed to create location for {building_name}: {e}")
                # Fall back to default Hong Kong location
                self.cur.execute("""
                    SELECT id FROM location_info 
                    WHERE province = 'Hong Kong' 
                    LIMIT 1
                """)
                fallback = self.cur.fetchone()
                if fallback:
                    return fallback[0]
                else:
                    return None
        
        else:
            # For non-Hong Kong properties, use simpler logic
            spider.logger.warning(f"⚠️  Non-Hong Kong property, using default location logic")
            return None

    def close_spider(self, spider):
        if self.conn and self.cur:
            try:
                self.conn.commit()
                self.cur.close()
                self.conn.close()
                spider.logger.info("✅ Database connection closed")
            except Exception as e:
                spider.logger.error(f"❌ Error closing database: {e}")
        else:
            spider.logger.warning("⚠️  No database connection to close")