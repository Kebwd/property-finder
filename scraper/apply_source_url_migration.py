#!/usr/bin/env python3
"""
Apply database migration to add source_url column
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_source_url_migration():
    """Apply V4 migration to add source_url columns"""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    try:
        print("🗄️  Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("📋 Checking current schema...")
        
        # Check if source_url column already exists in business table
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'business' AND column_name = 'source_url'
        """)
        business_has_url = cursor.fetchone()
        
        # Check if source_url column already exists in house table  
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'house' AND column_name = 'source_url'
        """)
        house_has_url = cursor.fetchone()
        
        print(f"Business table has source_url: {bool(business_has_url)}")
        print(f"House table has source_url: {bool(house_has_url)}")
        
        migrations_applied = []
        
        # Add source_url to business table if it doesn't exist
        if not business_has_url:
            print("➕ Adding source_url column to business table...")
            cursor.execute("ALTER TABLE business ADD COLUMN source_url TEXT;")
            migrations_applied.append("business.source_url")
        else:
            print("✅ Business table already has source_url column")
        
        # Add source_url to house table if it doesn't exist
        if not house_has_url:
            print("➕ Adding source_url column to house table...")
            cursor.execute("ALTER TABLE house ADD COLUMN source_url TEXT;")
            migrations_applied.append("house.source_url")
        else:
            print("✅ House table already has source_url column")
        
        # Add indexes if columns were created
        if migrations_applied:
            print("📊 Creating indexes...")
            
            if "business.source_url" in migrations_applied:
                cursor.execute("CREATE INDEX idx_business_source_url ON business(source_url);")
                print("✅ Created index on business.source_url")
                
            if "house.source_url" in migrations_applied:
                cursor.execute("CREATE INDEX idx_house_source_url ON house(source_url);")
                print("✅ Created index on house.source_url")
        
        # Commit changes
        conn.commit()
        
        if migrations_applied:
            print(f"🎉 Migration completed! Applied: {', '.join(migrations_applied)}")
        else:
            print("✅ No migration needed - all columns already exist")
        
        # Verify the changes
        print("\n📋 Verifying schema...")
        cursor.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name IN ('business', 'house') AND column_name = 'source_url'
            ORDER BY table_name
        """)
        
        columns = cursor.fetchall()
        for table, column, dtype in columns:
            print(f"✅ {table}.{column}: {dtype}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 APPLYING SOURCE_URL MIGRATION")
    print("=" * 50)
    
    success = apply_source_url_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now run the scraper and source URLs will be saved.")
    else:
        print("\n❌ Migration failed. Please check the errors above.")
