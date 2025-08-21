#!/usr/bin/env python3
"""
Check street data in the house table
"""

import os
import psycopg2
from dotenv import load_dotenv

def check_street_data():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get houses with street data
        cursor.execute("""
            SELECT building_name_zh, street, deal_price, deal_date
            FROM house 
            WHERE street IS NOT NULL AND street != ''
            ORDER BY id DESC 
            LIMIT 10;
        """)
        
        houses_with_street = cursor.fetchall()
        
        if houses_with_street:
            print("✅ Houses with street data:")
            print("="*80)
            for i, (building, street, price, date) in enumerate(houses_with_street, 1):
                print(f"{i:2d}. 🏠 {building}")
                print(f"    🛣️  Street: {street}")
                print(f"    💰 Price: {price}")
                print(f"    📅 Date: {date}")
                print("-" * 40)
        else:
            print("❌ No houses with street data found")
        
        # Check total count
        cursor.execute("SELECT COUNT(*) FROM house WHERE street IS NOT NULL AND street != '';")
        street_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM house;")
        total_count = cursor.fetchone()[0]
        
        print(f"\nSummary:")
        print(f"Houses with street data: {street_count}")
        print(f"Total houses: {total_count}")
        
        # Show some recent houses regardless of street data
        cursor.execute("""
            SELECT building_name_zh, street 
            FROM house 
            ORDER BY id DESC 
            LIMIT 5;
        """)
        
        recent_houses = cursor.fetchall()
        print(f"\nMost recent 5 houses:")
        for building, street in recent_houses:
            street_display = street if street else "NO STREET"
            print(f"  🏠 {building} | Street: {street_display}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_street_data()
