#!/usr/bin/env python3
"""
Verify Scraper Database Integration
Check if scraped data is being saved to Supabase
"""
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

def check_recent_data():
    """Check for recently scraped data in the database"""
    print("🔍 CHECKING RECENT SCRAPED DATA")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(database_url, client_encoding='utf8')
        cur = conn.cursor()
        
        # Check total records
        print("\n📊 CURRENT DATABASE STATUS:")
        
        # Business table
        cur.execute("SELECT COUNT(*) FROM business;")
        business_count = cur.fetchone()[0]
        print(f"🏢 Business properties: {business_count} records")
        
        # House table  
        cur.execute("SELECT COUNT(*) FROM house;")
        house_count = cur.fetchone()[0]
        print(f"🏠 Residential properties: {house_count} records")
        
        # Location info
        cur.execute("SELECT COUNT(*) FROM location_info;")
        location_count = cur.fetchone()[0]
        print(f"📍 Location records: {location_count} records")
        
        # Check recent entries by deal_date (today)
        print("\n⏰ RECENT ACTIVITY (Today's deals):")
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Recent business entries by deal_date
        cur.execute("""
            SELECT COUNT(*) FROM business 
            WHERE deal_date::date = %s
        """, (today,))
        recent_business = cur.fetchone()
        if recent_business and recent_business[0] > 0:
            print(f"✅ Today's business deals: {recent_business[0]}")
        else:
            print("ℹ️  No business deals for today's date")
        
        # Show latest entries by ID (most recently scraped)
        print("\n📋 LATEST SCRAPED DATA:")
        cur.execute("""
            SELECT building_name_zh, type, deal_price, deal_date 
            FROM business 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        recent_data = cur.fetchall()
        if recent_data:
            for i, row in enumerate(recent_data, 1):
                building, prop_type, price, date = row
                print(f"🏢 #{i}: {building} - {prop_type} - ${price:,.0f} ({date})")
        else:
            print("ℹ️  No business data found")
        
        cur.close()
        conn.close()
        
        print(f"\n🎯 TOTAL PROPERTIES: {business_count + house_count}")
        print("✅ Database integration is working!")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_recent_data()
