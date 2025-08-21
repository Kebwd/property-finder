#!/usr/bin/env python3
"""
Check if street data is being stored in the database
"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

def check_street_data():
    # Load environment variables
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get recent houses with street data
        cursor.execute("""
            SELECT building_name_zh, street, town, deal_price, created_at 
            FROM house 
            WHERE street IS NOT NULL AND street != ''
            ORDER BY created_at DESC 
            LIMIT 10;
        """)
        
        recent_houses = cursor.fetchall()
        
        if recent_houses:
            print("✅ Recent houses with street data:")
            print("="*80)
            for i, (building, street, town, price, created) in enumerate(recent_houses, 1):
                print(f"{i:2d}. 🏠 {building}")
                print(f"    🛣️  Street: {street}")
                print(f"    🏙️  Town: {town}")
                print(f"    💰 Price: {price}")
                print(f"    📅 Created: {created}")
                print("-" * 40)
        else:
            print("❌ No houses with street data found")
            
            # Check if any houses exist at all
            cursor.execute("SELECT COUNT(*) FROM house;")
            total_houses = cursor.fetchone()[0]
            print(f"Total houses in database: {total_houses}")
            
            # Check recent houses without street filter
            cursor.execute("""
                SELECT building_name_zh, street, town, created_at 
                FROM house 
                ORDER BY created_at DESC 
                LIMIT 5;
            """)
            
            recent_any = cursor.fetchall()
            if recent_any:
                print("\nRecent houses (with/without street):")
                for building, street, town, created in recent_any:
                    street_display = street if street else "NULL"
                    print(f"  🏠 {building} | Street: {street_display} | Town: {town}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_street_data()
