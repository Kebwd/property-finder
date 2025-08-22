import json
import os
import psycopg2
from datetime import datetime
import sys

def import_demo_data_to_database():
    """Import generated demo data into PostgreSQL database"""
    
    print("📥 IMPORTING DEMO DATA TO DATABASE")
    print("=" * 50)
    
    # Load demo data
    demo_file = os.path.join(os.path.dirname(__file__), 'chinese_property_demo_data.json')
    if not os.path.exists(demo_file):
        print("❌ Demo data file not found. Run demo_data_generator.py first.")
        return
    
    with open(demo_file, 'r', encoding='utf-8') as f:
        demo_data = json.load(f)
    
    # Database connection parameters (adjust as needed)
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'property_finder'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    try:
        # Connect to database
        print(f"🔌 Connecting to database: {db_params['host']}:{db_params['port']}")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Clear existing demo data (optional)
        print("🧹 Clearing existing demo data...")
        cursor.execute("DELETE FROM houses WHERE data_source = 'Demo Data Generator'")
        
        # Prepare insert statement
        insert_query = """
        INSERT INTO houses (
            building_name_zh, deal_price, area, location, zone, city, province,
            type_raw, type, deal_date, source_url, data_source, scraped_city, start_url
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        total_inserted = 0
        
        # Import data for each city
        for city_key, properties in demo_data.items():
            print(f"📊 Importing {len(properties)} properties for {city_key}...")
            
            for property_data in properties:
                try:
                    # Prepare values
                    values = (
                        property_data['building_name_zh'],
                        property_data['deal_price'],
                        property_data['area'],
                        property_data['location'],
                        property_data['zone'],
                        property_data['city'],
                        property_data['province'],
                        property_data['type_raw'],
                        property_data['type'][0],  # Convert array to string
                        property_data['deal_date'],
                        property_data['source_url'],
                        property_data['data_source'],
                        property_data['scraped_city'],
                        property_data['start_url']
                    )
                    
                    cursor.execute(insert_query, values)
                    total_inserted += 1
                    
                except Exception as e:
                    print(f"⚠️  Error inserting property: {e}")
                    continue
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ IMPORT COMPLETE")
        print(f"📊 Total properties imported: {total_inserted}")
        print(f"🏙️  Cities covered: {len(demo_data)}")
        
        # Show database summary
        cursor.execute("SELECT COUNT(*) FROM houses WHERE data_source = 'Demo Data Generator'")
        count = cursor.fetchone()[0]
        print(f"🗄️  Total demo records in database: {count}")
        
        # Show city breakdown
        cursor.execute("""
            SELECT city, COUNT(*) as property_count 
            FROM houses 
            WHERE data_source = 'Demo Data Generator' 
            GROUP BY city 
            ORDER BY property_count DESC
        """)
        
        print(f"\n📈 CITY BREAKDOWN:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} properties")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 SUCCESS: Demo data ready for testing!")
        print(f"💡 You can now test your application with realistic Chinese property data")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        print(f"💡 Make sure your database is running and credentials are correct")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def show_database_info():
    """Show current database configuration"""
    print("🗄️  DATABASE CONFIGURATION")
    print("=" * 30)
    print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"Port: {os.getenv('DB_PORT', '5432')}")
    print(f"Database: {os.getenv('DB_NAME', 'property_finder')}")
    print(f"User: {os.getenv('DB_USER', 'postgres')}")
    print(f"Password: {'*' * len(os.getenv('DB_PASSWORD', 'password'))}")
    print()

if __name__ == "__main__":
    show_database_info()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--info-only':
        exit()
    
    success = import_demo_data_to_database()
    
    if success:
        print("\n🚀 NEXT STEPS:")
        print("1. Start your API server: cd property-finder-api && npm start")
        print("2. Test the search functionality with Chinese cities")
        print("3. Verify data displays correctly in your UI")
        print("4. Continue working on real scraping solutions in parallel")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify database credentials")
        print("3. Ensure 'houses' table exists with correct schema")
        print("4. Run: python import_demo_data.py --info-only to check config")
