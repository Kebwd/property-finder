#!/usr/bin/env python3
"""
Preview Duplicate Cleanup - Shows what will be removed
Run this first to see what duplicates will be cleaned up.
"""

import psycopg2
from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print("🔍 DUPLICATE CLEANUP PREVIEW")
    print("=" * 50)
    
    # Preview duplicate houses that will be removed
    print("\n🏠 DUPLICATE HOUSES TO BE REMOVED:")
    cur.execute("""
    SELECT h1.id, h1.building_name_zh, h1.area, h1.deal_price/10000 as price_wan, h1.deal_date,
           'WILL BE REMOVED (keeping ID ' || MAX(h2.id) || ')' as action
    FROM house h1
    JOIN house h2 ON (
        h1.building_name_zh = h2.building_name_zh 
        AND h1.area = h2.area 
        AND h1.deal_price = h2.deal_price 
        AND h1.deal_date = h2.deal_date
        AND h1.id < h2.id
    )
    GROUP BY h1.id, h1.building_name_zh, h1.area, h1.deal_price, h1.deal_date
    ORDER BY h1.building_name_zh, h1.id
    """)
    
    duplicate_houses = cur.fetchall()
    for row in duplicate_houses:
        print(f"   ID {row[0]}: {row[1]} - {row[2]}㎡ - ¥{row[3]:.0f}万 - {row[4]} - {row[5]}")
    
    if not duplicate_houses:
        print("   No duplicate houses found")
    
    # Preview orphaned locations
    print(f"\n📍 ORPHANED LOCATIONS TO BE REMOVED:")
    cur.execute("""
    SELECT id, town, country, street, 'ORPHANED (no houses reference this)' as reason
    FROM location_info 
    WHERE id NOT IN (SELECT DISTINCT location_id FROM house WHERE location_id IS NOT NULL)
    ORDER BY id
    """)
    
    orphaned_locations = cur.fetchall()
    for row in orphaned_locations:
        street_display = row[3] if row[3] else 'NULL'
        print(f"   ID {row[0]}: {row[1]}, {row[2]}, Street: {street_display} - {row[4]}")
    
    if not orphaned_locations:
        print("   No orphaned locations found")
    
    # Preview duplicate locations
    print(f"\n🔄 DUPLICATE LOCATIONS TO BE REMOVED:")
    cur.execute("""
    SELECT l1.id, l1.town, l1.country, l1.street,
           'DUPLICATE (keeping ID ' || l2.id || ')' as action
    FROM location_info l1
    JOIN location_info l2 ON (
        COALESCE(l1.town, '') = COALESCE(l2.town, '')
        AND COALESCE(l1.country, '') = COALESCE(l2.country, '')
        AND COALESCE(l1.street, '') = COALESCE(l2.street, '')
        AND l1.id < l2.id
    )
    WHERE NOT EXISTS (SELECT 1 FROM house WHERE location_id = l1.id)
    ORDER BY l1.town, l1.id
    """)
    
    duplicate_locations = cur.fetchall()
    for row in duplicate_locations:
        street_display = row[3] if row[3] else 'NULL'
        print(f"   ID {row[0]}: {row[1]}, {row[2]}, Street: {street_display} - {row[4]}")
    
    if not duplicate_locations:
        print("   No duplicate locations found")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CLEANUP SUMMARY:")
    print(f"   Houses to remove: {len(duplicate_houses)}")
    print(f"   Orphaned locations to remove: {len(orphaned_locations)}")
    print(f"   Duplicate locations to remove: {len(duplicate_locations)}")
    print(f"   Total records to remove: {len(duplicate_houses) + len(orphaned_locations) + len(duplicate_locations)}")
    
    if duplicate_houses or orphaned_locations or duplicate_locations:
        print("\n⚠️  To proceed with cleanup, run: python cleanup_duplicates.py")
    else:
        print("\n✅ No duplicates found! Database is clean.")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
