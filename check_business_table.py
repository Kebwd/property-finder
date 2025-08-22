import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        database='property_finder', 
        user='postgres',
        password='admin'
    )
    cursor = conn.cursor()
    
    # Check business table schema
    print("=== BUSINESS TABLE SCHEMA ===")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'business' 
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
    
    # Check if source_url column exists
    has_source_url = any(col[0] == 'source_url' for col in columns)
    print(f"\nSource URL column exists: {has_source_url}")
    
    # Check recent business records
    print("\n=== RECENT BUSINESS RECORDS ===")
    cursor.execute("""
        SELECT id, building_name_zh, deal_date, deal_price, 
               CASE WHEN 'source_url' = ANY(ARRAY(SELECT column_name FROM information_schema.columns WHERE table_name = 'business'))
                    THEN (SELECT source_url FROM business b2 WHERE b2.id = b.id)
                    ELSE 'Column does not exist'
               END as source_url_value
        FROM business b
        WHERE deal_date >= '2025-08-22'
        ORDER BY id DESC
        LIMIT 10
    """)
    
    recent_records = cursor.fetchall()
    print(f"Records from 2025-08-22: {len(recent_records)}")
    
    for record in recent_records:
        print(f"  ID {record[0]}: {record[1]} - {record[2]} - ${record[3]} - URL: {record[4]}")
    
    # Check all recent records regardless of date
    print("\n=== ALL RECENT BUSINESS RECORDS ===")
    cursor.execute("""
        SELECT id, building_name_zh, deal_date, deal_price
        FROM business 
        ORDER BY id DESC
        LIMIT 10
    """)
    
    all_recent = cursor.fetchall()
    for record in all_recent:
        print(f"  ID {record[0]}: {record[1]} - {record[2]} - ${record[3]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
