#!/usr/bin/env python3
"""
Safe Database Cleanup Script - Handles Foreign Key Constraints
Safely removes duplicate house and location records while preserving referential integrity.
"""

import psycopg2
from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print("🧹 SAFE DATABASE CLEANUP - REMOVING DUPLICATES")
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
        
        # Step 3: Check what tables reference location_info
        print("\n🔍 STEP 3: Checking foreign key references...")
        cur.execute("""
        SELECT DISTINCT table_name, column_name 
        FROM information_schema.key_column_usage 
        WHERE referenced_table_name = 'location_info'
        """)
        
        references = cur.fetchall()
        print(f"   Tables referencing location_info: {references}")
        
        # Step 4: Safe removal of locations (only remove unreferenced ones)
        print("\n📍 STEP 4: Safely removing unreferenced locations...")
        
        # Build a safe query that checks all referencing tables
        safe_location_query = """
        DELETE FROM location_info 
        WHERE id NOT IN (
            SELECT DISTINCT location_id FROM house WHERE location_id IS NOT NULL
            UNION
            SELECT DISTINCT location_id FROM business WHERE location_id IS NOT NULL
            UNION  
            SELECT DISTINCT location_id FROM store WHERE location_id IS NOT NULL
        )
        """
        
        try:
            cur.execute(safe_location_query)
            removed_locations = cur.rowcount
            print(f"   Removed {removed_locations} unreferenced locations")
        except Exception as e:
            print(f"   Warning: Could not remove some locations: {e}")
            removed_locations = 0
        
        # Step 5: Remove duplicate locations among remaining ones
        print("\n🔄 STEP 5: Removing duplicate locations (safe method)...")
        
        # For locations with same data, keep the one with lowest ID (oldest/most established)
        safe_duplicate_location_query = """
        DELETE FROM location_info l1 
        WHERE EXISTS (
            SELECT 1 FROM location_info l2 
            WHERE COALESCE(l1.town, '') = COALESCE(l2.town, '')
            AND COALESCE(l1.country, '') = COALESCE(l2.country, '')
            AND COALESCE(l1.street, '') = COALESCE(l2.street, '')
            AND l1.id > l2.id  -- Keep the one with lower ID (older)
        )
        AND id NOT IN (
            SELECT DISTINCT location_id FROM house WHERE location_id IS NOT NULL
            UNION
            SELECT DISTINCT location_id FROM business WHERE location_id IS NOT NULL
            UNION  
            SELECT DISTINCT location_id FROM store WHERE location_id IS NOT NULL
        )
        """
        
        try:
            cur.execute(safe_duplicate_location_query)
            removed_duplicate_locations = cur.rowcount
            print(f"   Removed {removed_duplicate_locations} duplicate locations")
        except Exception as e:
            print(f"   Warning: Could not remove some duplicate locations: {e}")
            removed_duplicate_locations = 0
        
        # Step 6: Final counts
        print("\n📊 STEP 6: Final verification...")
        cur.execute('SELECT COUNT(*) FROM house')
        final_house_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM location_info')
        final_location_count = cur.fetchone()[0]
        
        print(f"   Final houses: {final_house_count}")
        print(f"   Final locations: {final_location_count}")
        
        # Step 7: Check for remaining duplicates
        print("\n🔍 STEP 7: Checking for remaining duplicates...")
        cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT building_name_zh, area, deal_price, deal_date, COUNT(*) 
            FROM house 
            GROUP BY building_name_zh, area, deal_price, deal_date
            HAVING COUNT(*) > 1
        ) as dups
        """)
        remaining_house_dups = cur.fetchone()[0]
        
        print(f"   Remaining house duplicates: {remaining_house_dups}")
        
        # Commit the changes
        conn.commit()
        
        print("\n" + "=" * 50)
        print("✅ SAFE CLEANUP COMPLETED!")
        print(f"📉 Houses: {original_house_count} → {final_house_count} (removed {original_house_count - final_house_count})")
        print(f"📉 Locations: {original_location_count} → {final_location_count} (removed {original_location_count - final_location_count})")
        
        if remaining_house_dups == 0:
            print("🎉 All house duplicates successfully removed!")
        else:
            print(f"⚠️  {remaining_house_dups} house duplicate groups remain")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        conn.rollback()
        print("🔄 All changes rolled back")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
