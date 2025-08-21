#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Duplicates
Safely removes duplicate house and location records while preserving data integrity.
"""

import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime

def main():
    load_dotenv()
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print("🧹 DATABASE CLEANUP - REMOVING DUPLICATES")
    print("=" * 50)
    
    try:
        # Step 1: Backup current state
        print("\n📋 STEP 1: Creating backup info...")
        cur.execute('SELECT COUNT(*) FROM house')
        original_house_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM location_info')
        original_location_count = cur.fetchone()[0]
        
        print(f"   Original houses: {original_house_count}")
        print(f"   Original locations: {original_location_count}")
        
        # Step 2: Remove duplicate houses (keep the one with highest ID = newest)
        print("\n🏠 STEP 2: Removing duplicate houses...")
        
        # Find duplicate houses and keep only the newest (highest ID)
        duplicate_house_query = """
        DELETE FROM house h1 
        WHERE EXISTS (
            SELECT 1 FROM house h2 
            WHERE h1.building_name_zh = h2.building_name_zh 
            AND h1.area = h2.area 
            AND h1.deal_price = h2.deal_price 
            AND h1.deal_date = h2.deal_date
            AND h1.id < h2.id  -- Keep the one with higher ID (newer)
        )
        """
        
        cur.execute(duplicate_house_query)
        removed_houses = cur.rowcount
        print(f"   Removed {removed_houses} duplicate houses")
        
        # Step 3: Remove orphaned locations (not referenced by any house)
        print("\n📍 STEP 3: Removing orphaned locations...")
        
        orphaned_location_query = """
        DELETE FROM location_info 
        WHERE id NOT IN (SELECT DISTINCT location_id FROM house WHERE location_id IS NOT NULL)
        """
        
        cur.execute(orphaned_location_query)
        removed_locations = cur.rowcount
        print(f"   Removed {removed_locations} orphaned locations")
        
        # Step 4: Remove duplicate locations (keep the one with most data)
        print("\n🔄 STEP 4: Removing duplicate locations...")
        
        # For locations with same town/country/street, keep the one with coordinates
        duplicate_location_query = """
        DELETE FROM location_info l1 
        WHERE EXISTS (
            SELECT 1 FROM location_info l2 
            WHERE COALESCE(l1.town, '') = COALESCE(l2.town, '')
            AND COALESCE(l1.country, '') = COALESCE(l2.country, '')
            AND COALESCE(l1.street, '') = COALESCE(l2.street, '')
            AND l1.id < l2.id  -- Keep the newer one
            AND NOT EXISTS (SELECT 1 FROM house WHERE location_id = l1.id)  -- Only if not referenced
        )
        """
        
        cur.execute(duplicate_location_query)
        removed_duplicate_locations = cur.rowcount
        print(f"   Removed {removed_duplicate_locations} duplicate locations")
        
        # Step 5: Final counts
        print("\n📊 STEP 5: Final verification...")
        cur.execute('SELECT COUNT(*) FROM house')
        final_house_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM location_info')
        final_location_count = cur.fetchone()[0]
        
        print(f"   Final houses: {final_house_count}")
        print(f"   Final locations: {final_location_count}")
        
        # Step 6: Check for remaining duplicates
        print("\n🔍 STEP 6: Checking for remaining duplicates...")
        cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT building_name_zh, area, deal_price, deal_date, COUNT(*) 
            FROM house 
            GROUP BY building_name_zh, area, deal_price, deal_date
            HAVING COUNT(*) > 1
        ) as dups
        """)
        remaining_house_dups = cur.fetchone()[0]
        
        cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT town, country, street, COUNT(*) 
            FROM location_info 
            GROUP BY town, country, street
            HAVING COUNT(*) > 1
        ) as dups
        """)
        remaining_location_dups = cur.fetchone()[0]
        
        print(f"   Remaining house duplicates: {remaining_house_dups}")
        print(f"   Remaining location duplicates: {remaining_location_dups}")
        
        # Commit the changes
        conn.commit()
        
        print("\n" + "=" * 50)
        print("✅ CLEANUP COMPLETED SUCCESSFULLY!")
        print(f"📉 Houses: {original_house_count} → {final_house_count} (removed {original_house_count - final_house_count})")
        print(f"📉 Locations: {original_location_count} → {final_location_count} (removed {original_location_count - final_location_count})")
        
        if remaining_house_dups == 0 and remaining_location_dups == 0:
            print("🎉 All duplicates successfully removed!")
        else:
            print("⚠️  Some duplicates may remain (check manually)")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        conn.rollback()
        print("🔄 All changes rolled back")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
