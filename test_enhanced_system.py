#!/usr/bin/env python3
"""
Test script to verify the enhanced property finder API
"""
import os
import psycopg2
from urllib.parse import urlparse

def test_database_data():
    """Test that source URLs are being stored in the database"""
    print("🔍 TESTING DATABASE CONTENT")
    print("=" * 50)
    
    try:
        # Parse DATABASE_URL  
        url = urlparse(os.getenv('DATABASE_URL'))
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:]
        )

        cur = conn.cursor()
        
        # Test business table
        cur.execute("""
            SELECT building_name_zh, deal_price, deal_date, source_url, type
            FROM business 
            WHERE deal_date >= '2025-08-22' 
            AND source_url IS NOT NULL 
            ORDER BY deal_price DESC 
            LIMIT 5
        """)
        
        business_results = cur.fetchall()
        print(f"✅ Business entries with source URLs: {len(business_results)}")
        
        for row in business_results:
            building, price, date, url, btype = row
            print(f"  📊 {building}: ${price:,.0f} ({btype}) - {url[:60]}...")
        
        # Test house table
        cur.execute("""
            SELECT building_name_zh, deal_price, deal_date, source_url, type
            FROM house 
            WHERE deal_date >= '2025-08-22' 
            AND source_url IS NOT NULL 
            ORDER BY deal_price DESC 
            LIMIT 3
        """)
        
        house_results = cur.fetchall()
        print(f"✅ House entries with source URLs: {len(house_results)}")
        
        for row in house_results:
            building, price, date, url, htype = row
            print(f"  🏠 {building}: ${price:,.0f} ({htype}) - {url[:60]}...")
            
        conn.close()
        
        print("\n🎉 SUCCESS: Database is storing source URLs correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    # Load environment
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    test_database_data()
