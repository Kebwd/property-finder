#!/usr/bin/env python3
"""
Check actual column names in house table
"""

import os
import psycopg2
from dotenv import load_dotenv

def check_table_structure():
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Get all columns in house table
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'house'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        print("House table structure:")
        print("="*50)
        for col_name, data_type, nullable in columns:
            print(f"{col_name:20} | {data_type:15} | {nullable}")
        
        # Check recent entries
        cursor.execute("SELECT * FROM house ORDER BY created_at DESC LIMIT 3;")
        recent = cursor.fetchall()
        
        if recent:
            print("\nRecent entries (first 3):")
            print("="*50)
            for i, row in enumerate(recent, 1):
                print(f"Entry {i}: {row[:5]}...")  # Show first 5 fields
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_table_structure()
