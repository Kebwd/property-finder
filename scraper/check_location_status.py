#!/usr/bin/env python3
"""
Check the current status of location_info records
"""

import os
import psycopg2
from dotenv import load_dotenv

def check_location_status():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check total locations and how many have coordinates
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(lat) as with_lat,
                COUNT(long) as with_lng,
                COUNT(geom) as with_geom
            FROM location_info;
        """)
        
        stats = cursor.fetchone()
        print("Location_info statistics:")
        print(f"  Total locations: {stats[0]}")
        print(f"  With latitude: {stats[1]}")
        print(f"  With longitude: {stats[2]}")
        print(f"  With geometry: {stats[3]}")
        print("="*50)
        
        # Show locations without coordinates
        cursor.execute("""
            SELECT id, province, city, country, town, lat, long
            FROM location_info 
            WHERE lat IS NULL OR long IS NULL
            ORDER BY id
            LIMIT 20;
        """)
        
        null_coords = cursor.fetchall()
        
        if null_coords:
            print("Locations without coordinates:")
            for location_id, province, city, country, town, lat, lng in null_coords:
                print(f"  ID {location_id:2d}: {town}, {country} | lat: {lat} | lng: {lng}")
        else:
            print("✅ All locations have coordinates!")
        
        print("="*50)
        
        # Show some locations with coordinates
        cursor.execute("""
            SELECT id, province, city, country, town, lat, long
            FROM location_info 
            WHERE lat IS NOT NULL AND long IS NOT NULL
            ORDER BY id DESC
            LIMIT 10;
        """)
        
        with_coords = cursor.fetchall()
        
        if with_coords:
            print("Recent locations with coordinates:")
            for location_id, province, city, country, town, lat, lng in with_coords:
                print(f"  ID {location_id:2d}: {town}, {country} | {lat:.6f}, {lng:.6f}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_location_status()
