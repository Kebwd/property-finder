import psycopg2
import os

def check_database_structure():
    """Check what tables and columns exist in your Supabase database"""
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url, client_encoding='utf8')
        cursor = conn.cursor()
        
        print("🗄️ CHECKING YOUR SUPABASE DATABASE STRUCTURE")
        print("=" * 50)
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print(f"\n📋 Available tables:")
        if tables:
            for table in tables:
                print(f"   - {table[0]}")
                
                # Check columns for each table
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table[0],))
                columns = cursor.fetchall()
                
                print(f"     Columns:")
                for col_name, col_type in columns:
                    print(f"       - {col_name} ({col_type})")
                print()
        else:
            print("   No tables found!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database_structure()
