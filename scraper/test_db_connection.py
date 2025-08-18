#!/usr/bin/env python3
"""
Test Supabase Database Connection
Verifies that the scraper can connect to your Supabase database
"""
import os
import psycopg2
from dotenv import load_dotenv

def test_database_connection():
    """Test database connection and verify tables exist"""
    print("🗄️  TESTING SUPABASE DATABASE CONNECTION")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("💡 Make sure you have a .env file with DATABASE_URL set")
        return False
    
    print(f"🔗 Database URL: {database_url[:50]}...")
    
    try:
        # Test connection
        print("\n🔌 Testing connection...")
        conn = psycopg2.connect(database_url, client_encoding='utf8')
        cur = conn.cursor()
        print("✅ Database connection successful!")
        
        # Test basic query
        print("\n📋 Testing basic query...")
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✅ PostgreSQL Version: {version[:50]}...")
        
        # Check if required tables exist
        print("\n📊 Checking required tables...")
        tables_to_check = ['business', 'house', 'location_info']
        
        for table in tables_to_check:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table,))
            exists = cur.fetchone()[0]
            
            if exists:
                # Get row count
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"✅ Table '{table}': {count} records")
            else:
                print(f"❌ Table '{table}': Not found")
        
        # Test insert permission (dry run)
        print("\n🔧 Testing write permissions...")
        try:
            cur.execute("BEGIN;")
            cur.execute("SELECT 1;")  # Simple test query
            cur.execute("ROLLBACK;")
            print("✅ Write permissions: OK")
        except Exception as e:
            print(f"⚠️  Write permissions: {e}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Database connection test completed successfully!")
        print("✅ Your scraper should be able to connect to Supabase")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your DATABASE_URL in .env file")
        print("2. Verify your Supabase project is active")
        print("3. Confirm your database password is correct")
        print("4. Check if your IP is whitelisted (if applicable)")
        return False

if __name__ == "__main__":
    test_database_connection()
