from scrapy.exceptions import DropItem
import os
import psycopg2
from .normalization_pipeline import NormalizationPipeline
import requests
from ..coordinate import geocode
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

normalizer = NormalizationPipeline()

async def get_coordinates(address):
    coords = None
    try:
        coords = await geocode(address)
    except Exception as e:
        pass
    return coords

# Load GeoJSON files and merge into a single GeoDataFrame
geojson_files = ["path/to/district1.geojson", "path/to/district2.geojson"]
districts = gpd.GeoDataFrame(pd.concat([gpd.read_file(file) for file in geojson_files], ignore_index=True))

def assign_district(lat, lon):
    """Assign district based on latitude and longitude."""
    point = Point(lon, lat)
    for _, district in districts.iterrows():
        if district['geometry'].contains(point):
            return district['name']  # Assuming 'name' column contains district names
    return None

class StorePipeline:
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
            spider.logger.info("🗄️  Connected to Supabase database")
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
        
        # Assign district based on geospatial data
        lat = item.get('latitude')
        lon = item.get('longitude')
        if lat and lon:
            item['dist'] = assign_district(lat, lon)
        else:
            spider.logger.warning("⚠️  Missing latitude/longitude for district assignment")

        return item

    def _process_hong_kong_item(self, item, spider):
        """Process Hong Kong property deals"""
        # Check if deal already exists to avoid duplicates
        building_name = item.get("building_name_zh", "")
        deal_price = item.get("deal_price", "")
        deal_date = item.get("deal_date", "")
        floor = item.get("floor", "")
        unit = item.get("unit", "")
        
        # Validate building name - skip if empty or null
        if not building_name or building_name.strip() == '':
            spider.logger.warning(f"⏭️  Skipping item due to missing building name")
            return
        
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
        
        # Get or clean source URL
        source_url = item.get('source_url', '').strip() if item.get('source_url') else None
        if source_url and not source_url.startswith('http'):
            # Handle relative URLs by adding base domain
            start_url = str(item.get('start_url', ''))
            if 'midlandici' in start_url:
                source_url = f"https://www.midlandici.com.hk{source_url}"
            elif 'centanet' in start_url:
                source_url = f"https://oir.centanet.com{source_url}"
            elif 'property.hk' in start_url:
                source_url = f"https://www.property.hk{source_url}"
            elif 'carparkhk.com' in start_url:
                source_url = f"https://carparkhk.com{source_url}"
        # Extract type as string (first element if it's a list)
        item_type = item.get("type")
        if isinstance(item_type, list) and item_type:
            type_string = item_type[0]
        else:
            type_string = str(item_type) if item_type else ""
        
        # Insert business record with source URL
        hk_values = (
            type_string,
            building_name,
            floor,
            unit,
            item.get("area"),
            deal_date,
            deal_price,
            item.get("developer"),
            location_id,
            source_url
        )
        
        self.cur.execute("""
            INSERT INTO business (type, building_name_zh, floor, unit, area, deal_date, deal_price, developer, location_id, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, hk_values)
        
        self.conn.commit()
        spider.logger.info(f"✅ Stored HK deal: {building_name} - {deal_price} (URL: {source_url})")

    def _process_china_item(self, item, spider):
        """Process China property deals"""
        # Similar structure for China deals
        building_name = item.get("building_name_zh", "")
        deal_price = item.get("deal_price", "")
        deal_date = item.get("deal_date", "")
        
        # Validate building name - skip if empty or null
        if not building_name or building_name.strip() == '':
            spider.logger.warning(f"⏭️  Skipping item due to missing building name")
            return
        
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
        
        # Get or clean source URL
        source_url = item.get('source_url', '').strip() if item.get('source_url') else None
        if source_url and not source_url.startswith('http'):
            # Handle relative URLs by adding base domain for Chinese sites
            start_url = str(item.get('start_url', ''))
            if 'lianjia.com' in start_url or 'ke.com' in start_url:
                source_url = f"https://bj.ke.com{source_url}"
            elif source_url.startswith('/'):
                # General relative URL handling
                from urllib.parse import urljoin
                source_url = urljoin(start_url, source_url)

        # Extract type as string (first element if it's a list)
        item_type = item.get("type")
        if isinstance(item_type, list) and item_type:
            type_string = item_type[0]
        else:
            type_string = str(item_type) if item_type else ""

        cn_location_values = (
            item.get("province"),
            item.get("city"),
            item.get("country"),
            item.get("town"),
            item.get("street"),
            item.get("road")
        )
        
        cn_values = (
            type_string,
            building_name,
            item.get("floor"),
            item.get("unit"),
            item.get("area"),
            deal_date,
            deal_price,
            item.get("developer"),
            source_url
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
            INSERT INTO business (type, building_name_zh, floor, unit, area, deal_date, deal_price, developer, location_id, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, cn_values + (location_id,))
        
        self.conn.commit()
        spider.logger.info(f"✅ Stored China deal: {building_name} - {deal_price} (URL: {source_url})")

    def _create_or_get_location_info(self, item, spider):
        """Create or get location_info record based on scraped data with enhanced street extraction"""
        building_name = item.get("building_name_zh", "") or ""
        
        # Extract location details from item (if available)
        address = item.get("address", building_name) or building_name
        district = item.get("district", "") or ""
        area = item.get("area_name", "") or ""
        
        # Enhanced street extraction from building name or address
        street = ""
        extracted_street = self._extract_street_from_text(building_name)
        if extracted_street:
            street = extracted_street
        elif self._extract_street_from_text(address):
            street = self._extract_street_from_text(address)
        
        # Try to create a more specific location record
        # For Hong Kong properties, extract district/area information
        if "Hong Kong" in item.get("zone", ""):
            province = "Hong Kong"
            
            # Enhanced location parsing for Hong Kong
            if building_name and any(keyword in building_name for keyword in ["中環", "Central"]):
                city = "Hong Kong Island"
                country = "Central and Western"
                town = "Central"
                if not street:
                    street = "Central District"
                road = building_name
            elif building_name and any(keyword in building_name for keyword in ["尖沙咀", "Tsim Sha Tsui", "九龍", "Kowloon"]):
                city = "Kowloon"
                country = "Yau Tsim Mong"
                town = "Tsim Sha Tsui"
                if not street:
                    street = "Nathan Road"
                road = building_name
            elif building_name and any(keyword in building_name for keyword in ["筲箕灣", "Shau Kei Wan"]):
                city = "Hong Kong Island"
                country = "Eastern"
                town = "Shau Kei Wan"
                if not street:
                    street = "Shau Kei Wan Road"
                road = building_name
            elif building_name and any(keyword in building_name for keyword in ["銅鑼灣", "Causeway Bay"]):
                city = "Hong Kong Island"
                country = "Wan Chai"
                town = "Causeway Bay"
                if not street:
                    street = "Hennessy Road"
                road = building_name
            elif building_name and any(keyword in building_name for keyword in ["旺角", "Mong Kok"]):
                city = "Kowloon"
                country = "Yau Tsim Mong"
                town = "Mong Kok"
                if not street:
                    street = "Nathan Road"
                road = building_name
            else:
                # Default to Kowloon for other HK properties
                city = "Kowloon"
                country = "Yau Tsim Mong"
                town = "Tsim Sha Tsui"
                if not street:
                    street = "Nathan Road"
                road = building_name or "Unknown Building"
            
            # Check if this location already exists (including street in matching)
            self.cur.execute("""
                SELECT id FROM location_info 
                WHERE province = %s AND city = %s AND country = %s AND town = %s AND street = %s AND road = %s
                LIMIT 1
            """, (province, city, country, town, street, road))
            
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
            
            # Create new location record with street data
            try:
                self.cur.execute("""
                    INSERT INTO location_info (province, city, country, town, street, road, lat, long, geom)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    RETURNING id
                """, (province, city, country, town, street, road, lat, lng, lng, lat))
                
                location_id = self.cur.fetchone()[0]
                spider.logger.info(f"📍 Created new location: {location_id} for {building_name} in {street}, {town}, {city}")
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

    def _extract_street_from_text(self, text):
        """Extract street-level information from Chinese text"""
        if not text:
            return ""
        
        # Common Hong Kong street patterns
        street_patterns = [
            r'(\w+道)',      # 道 (road)
            r'(\w+街)',      # 街 (street)
            r'(\w+路)',      # 路 (road)
            r'(\w+巷)',      # 巷 (lane)
            r'(\w+里)',      # 里 (village/lane)
            r'(\w+坊)',      # 坊 (square)
            r'(\w+徑)',      # 徑 (path)
            r'(\w+園)',      # 園 (garden/estate)
            r'(\w+苑)',      # 苑 (court/garden)
            r'(\w+灣)',      # 灣 (bay)
            r'(\w+角)',      # 角 (corner)
            r'(\w+台)',      # 台 (terrace)
            r'(\w+廣場)',    # 廣場 (plaza)
        ]
        
        import re
        for pattern in street_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""

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