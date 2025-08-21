#!/usr/bin/env python3
"""
Script to update existing location records with geocoding
"""

import os
import psycopg2
import sys
import time
from dotenv import load_dotenv

# Add the scraper directory to the path to import coordinate module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scraper.coordinate import geocode

def update_null_coordinates():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Find locations with NULL coordinates
        cursor.execute("""
            SELECT id, province, city, country, town 
            FROM location_info 
            WHERE lat IS NULL OR long IS NULL OR geom IS NULL
            ORDER BY id;
        """)
        
        null_locations = cursor.fetchall()
        
        if not null_locations:
            print("✅ No locations with NULL coordinates found")
            return
        
        print(f"Found {len(null_locations)} locations with NULL coordinates")
        print("="*60)
        
        updated_count = 0
        failed_count = 0
        
        for location_id, province, city, country, town in null_locations:
            print(f"Processing location {location_id}: {town}, {country}")
            
            try:
                # Create address for geocoding
                address_parts = [town]
                
                if country == '中国':
                    # Chinese location
                    address_parts.extend(['深圳市', '广东省', '中国'])
                    geocode_address = ', '.join(address_parts)
                    coords = geocode(geocode_address, zone="China")
                else:
                    # Hong Kong location
                    address_parts.append('香港')
                    geocode_address = ', '.join(address_parts)
                    coords = geocode(geocode_address, zone="HK")
                
                if coords:
                    lat = coords['lat']
                    lng = coords['lng']
                    geom = f"POINT({lng} {lat})"
                    
                    # Update the location record
                    cursor.execute("""
                        UPDATE location_info 
                        SET lat = %s, long = %s, geom = ST_GeomFromText(%s, 4326)
                        WHERE id = %s
                    """, (lat, lng, geom, location_id))
                    
                    conn.commit()
                    updated_count += 1
                    print(f"  ✅ Updated: {lat}, {lng}")
                else:
                    failed_count += 1
                    print(f"  ❌ No coordinates returned")
                
                # Add small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                failed_count += 1
                print(f"  ❌ Error: {e}")
                conn.rollback()
                
                # Add longer delay on error
                time.sleep(1)
        
        print("="*60)
        print(f"Summary:")
        print(f"  Successfully updated: {updated_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Total processed: {len(null_locations)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("🌍 Starting geocoding update for NULL coordinates...")
    update_null_coordinates()
    print("✅ Geocoding update completed!")
