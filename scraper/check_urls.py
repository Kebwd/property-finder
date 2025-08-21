#!/usr/bin/env python3
"""
Check if source URLs are being captured in the database
"""

import os
import psycopg2
from dotenv import load_dotenv

def check_source_urls():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check recent houses with source URLs
        cursor.execute("""
            SELECT building_name_zh, street, source_url, deal_price
            FROM house 
            WHERE source_url IS NOT NULL AND source_url != ''
            ORDER BY id DESC 
            LIMIT 10;
        """)
        
        houses_with_urls = cursor.fetchall()
        
        if houses_with_urls:
            print("✅ Houses with Source URLs:")
            print("="*80)
            for i, (building, street, url, price) in enumerate(houses_with_urls, 1):
                street_info = f" | Street: {street}" if street else ""
                print(f"{i:2d}. 🏠 {building}")
                print(f"    🛣️  {street_info}")
                print(f"    💰 Price: ¥{price:,.0f}")
                print(f"    🔗 URL: {url}")
                print("-" * 40)
        else:
            print("❌ No houses with source URLs found")
        
        # Check total counts
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN source_url IS NOT NULL AND source_url != '' THEN 1 END) as with_urls
            FROM house;
        """)
        
        stats = cursor.fetchone()
        print(f"\nSummary:")
        print(f"Total houses: {stats[0]}")
        print(f"Houses with URLs: {stats[1]}")
        print(f"URL capture rate: {stats[1]/stats[0]*100:.1f}%")
        
        # Show some recent houses without URLs
        cursor.execute("""
            SELECT building_name_zh, source_url
            FROM house 
            ORDER BY id DESC 
            LIMIT 5;
        """)
        
        recent_houses = cursor.fetchall()
        print(f"\nMost recent 5 houses:")
        for building, url in recent_houses:
            url_display = url if url else "NO URL"
            print(f"  🏠 {building} | URL: {url_display}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_source_urls()
