#!/usr/bin/env python3
"""
Test creating a new location to verify geocoding works automatically
"""

import os
import psycopg2
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the geocoding directly
from scraper.coordinate import geocode

def test_new_location_geocoding():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        # Test geocoding first
        print("Testing geocoding for new Chinese location...")
        test_address = "宝安, 深圳市, 广东省, 中国"
        coords = geocode(test_address, zone="China")
        print(f"Geocoded {test_address}: {coords}")
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if 宝安 already exists
        cursor.execute("SELECT id FROM location_info WHERE town = '宝安' AND country = '中国'")
        existing = cursor.fetchone()
        
        if existing:
            print(f"宝安 already exists with ID {existing[0]}")
        else:
            # Insert a new test location with geocoding
            lat = coords['lat']
            lng = coords['lng']
            geom = f"POINT({lng} {lat})"
            
            cursor.execute("""
                INSERT INTO location_info (province, city, country, town, lat, long, geom)
                VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))
                RETURNING id, lat, long
            """, ('广东省', '深圳市', '中国', '宝安', lat, lng, geom))
            
            new_location = cursor.fetchone()
            conn.commit()
            
            print(f"✅ Created new location ID {new_location[0]} with coordinates: {new_location[1]}, {new_location[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_new_location_geocoding()
