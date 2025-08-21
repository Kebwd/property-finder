#!/usr/bin/env python3
"""
Add street column to house table and update pipeline
"""

import os
import psycopg2
from urllib.parse import urlparse

def add_street_column():
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Add street column if it doesn't exist
        cursor.execute("""
            ALTER TABLE house 
            ADD COLUMN IF NOT EXISTS street TEXT;
        """)
        
        # Check if column was added
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'house' AND column_name = 'street';
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Street column exists: {result}")
        else:
            print("❌ Failed to add street column")
        
        conn.commit()
        conn.close()
        print("✅ Database schema updated successfully")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    add_street_column()
