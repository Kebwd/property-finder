#!/usr/bin/env python3
"""
Final verification of the geocoding fixes
"""

import os
import psycopg2
from dotenv import load_dotenv

def final_verification():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔍 FINAL VERIFICATION REPORT")
        print("="*60)
        
        # 1. Check total location statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(lat) as with_coords,
                COUNT(CASE WHEN country = '中国' THEN 1 END) as china_locations,
                COUNT(CASE WHEN country = '中国' AND lat IS NOT NULL THEN 1 END) as china_with_coords
            FROM location_info;
        """)
        
        stats = cursor.fetchone()
        print(f"📊 Location Statistics:")
        print(f"   Total locations: {stats[0]}")
        print(f"   With coordinates: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
        print(f"   Chinese locations: {stats[2]}")
        print(f"   Chinese with coords: {stats[3]} ({stats[3]/stats[2]*100:.1f}%)")
        print()
        
        # 2. Show Chinese locations with coordinates
        cursor.execute("""
            SELECT town, lat, long
            FROM location_info 
            WHERE country = '中国' AND lat IS NOT NULL
            ORDER BY town;
        """)
        
        china_coords = cursor.fetchall()
        print(f"🇨🇳 Chinese Locations with Coordinates ({len(china_coords)}):")
        for town, lat, lng in china_coords:
            print(f"   {town}: {lat:.6f}, {lng:.6f}")
        print()
        
        # 3. Check recent house records with Chinese locations
        cursor.execute("""
            SELECT h.building_name_zh, h.street, l.town, l.lat, l.long
            FROM house h
            JOIN location_info l ON h.location_id = l.id
            WHERE l.country = '中国' AND l.lat IS NOT NULL
            ORDER BY h.id DESC
            LIMIT 5;
        """)
        
        recent_houses = cursor.fetchall()
        print(f"🏠 Recent Chinese Houses with Geocoded Locations:")
        for building, street, town, lat, lng in recent_houses:
            street_info = f" | Street: {street}" if street else ""
            print(f"   {building} → {town} ({lat:.6f}, {lng:.6f}){street_info}")
        print()
        
        # 4. Check for any remaining NULL coordinates
        cursor.execute("""
            SELECT COUNT(*) 
            FROM location_info 
            WHERE lat IS NULL OR long IS NULL OR geom IS NULL;
        """)
        
        null_count = cursor.fetchone()[0]
        if null_count == 0:
            print("✅ SUCCESS: All locations have complete coordinate data!")
        else:
            print(f"⚠️  WARNING: {null_count} locations still have NULL coordinates")
        
        print("="*60)
        print("🎉 Geocoding fix verification completed!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    final_verification()
