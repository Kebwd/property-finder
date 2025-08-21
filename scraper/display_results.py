#!/usr/bin/env python3
"""
Display property results with URL references
"""

import os
import psycopg2
from dotenv import load_dotenv

def display_results_with_urls():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🏠 PROPERTY FINDER RESULTS WITH SOURCE REFERENCES")
        print("="*80)
        
        # Get recent properties with all details including URLs
        cursor.execute("""
            SELECT 
                h.building_name_zh,
                h.street,
                l.town,
                l.lat,
                l.long,
                h.deal_price,
                h.deal_date,
                h.area,
                h.house_type,
                h.source_url
            FROM house h
            JOIN location_info l ON h.location_id = l.id
            WHERE h.source_url IS NOT NULL AND h.source_url != ''
            ORDER BY h.id DESC
            LIMIT 15;
        """)
        
        properties = cursor.fetchall()
        
        if not properties:
            print("❌ No properties with source URLs found")
            return
        
        for i, (building, street, town, lat, lng, price, date, area, house_type, url) in enumerate(properties, 1):
            print(f"🏠 PROPERTY #{i}")
            print(f"   🏢 Building: {building}")
            print(f"   📍 Location: {town}" + (f" - {street}" if street else ""))
            print(f"   🌍 Coordinates: {lat:.6f}, {lng:.6f}" if lat and lng else "   🌍 Coordinates: Not available")
            print(f"   💰 Price: ¥{price:,.0f}" if price else "   💰 Price: Not available")
            print(f"   📅 Deal Date: {date}" if date else "   📅 Deal Date: Not available")
            print(f"   📐 Area: {area}㎡" if area else "   📐 Area: Not available")
            print(f"   🏠 Type: {house_type}" if house_type else "   🏠 Type: Not available")
            print(f"   🔗 SOURCE: {url}")
            print("-" * 60)
        
        print(f"\n📊 SUMMARY:")
        
        # Get overall statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN source_url IS NOT NULL AND source_url != '' THEN 1 END) as with_urls,
                COUNT(CASE WHEN l.lat IS NOT NULL THEN 1 END) as with_coords
            FROM house h
            LEFT JOIN location_info l ON h.location_id = l.id;
        """)
        
        stats = cursor.fetchone()
        total, with_urls, with_coords = stats
        
        print(f"   📈 Total properties: {total}")
        print(f"   🔗 With source URLs: {with_urls} ({with_urls/total*100:.1f}%)")
        print(f"   🌍 With coordinates: {with_coords} ({with_coords/total*100:.1f}%)")
        
        print("\n✅ SUCCESS: Property data now includes trackable source references!")
        print("   You can click on any URL above to view the original property listing.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    display_results_with_urls()
