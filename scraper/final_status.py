#!/usr/bin/env python3
"""
Final Cleanup and Status Check
"""

import psycopg2
from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print('🧹 FINAL CLEANUP & STATUS')
    print('=' * 40)
    
    try:
        # Check which locations are still used
        cur.execute('SELECT COUNT(DISTINCT location_id) FROM house WHERE location_id IS NOT NULL')
        used_by_houses = cur.fetchone()[0]
        
        print(f'Locations used by houses: {used_by_houses}')
        
        # Check if there are unused locations we can safely remove
        cur.execute("""
        SELECT COUNT(*) FROM location_info 
        WHERE id NOT IN (SELECT DISTINCT location_id FROM house WHERE location_id IS NOT NULL)
        AND id != 1
        """)
        unused_locations = cur.fetchone()[0]
        
        print(f'Unused locations (safe to remove): {unused_locations}')
        
        if unused_locations > 0:
            print('\n📍 Removing unused locations...')
            cur.execute("""
            DELETE FROM location_info 
            WHERE id NOT IN (SELECT DISTINCT location_id FROM house WHERE location_id IS NOT NULL)
            AND id != 1
            """)
            removed = cur.rowcount
            print(f'   Removed {removed} unused locations')
            conn.commit()
        
        # Final summary
        cur.execute('SELECT COUNT(*) FROM house')
        final_houses = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM location_info')
        final_locations = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM house WHERE source_url IS NOT NULL AND source_url != ''")
        houses_with_urls = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM location_info WHERE street IS NOT NULL AND street != ''")
        locations_with_streets = cur.fetchone()[0]
        
        print(f'\n📊 FINAL DATABASE STATUS:')
        print(f'   Houses: {final_houses}')
        print(f'   Locations: {final_locations}')
        print(f'   Houses with URLs: {houses_with_urls}')
        print(f'   Locations with street data: {locations_with_streets}')
        print(f'\n✅ Database is now clean and optimized!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
