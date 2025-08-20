#!/usr/bin/env python3
import sys
import os

# Add the scraper directory to the path to access the pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.pipelines.store_pipeline import StorePipeline
from datetime import datetime, timedelta

# Create pipeline instance and connect to database
pipeline = StorePipeline()
pipeline.open_spider(None)

try:
    # Query for recent deals (last 5 days)
    recent_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    
    query = """
    SELECT deal_date, deal_price, type_raw, area, floor, unit, building_name_zh, created_at
    FROM stores 
    WHERE deal_date >= %s 
    ORDER BY deal_date DESC, deal_price DESC
    LIMIT 10
    """
    
    pipeline.cursor.execute(query, (recent_date,))
    results = pipeline.cursor.fetchall()
    
    print(f"Recent deals from {recent_date} onwards:")
    print("=" * 80)
    
    if results:
        for row in results:
            deal_date, price, type_raw, area, floor, unit, building, created_at = row
            price_m = price / 1000000 if price else 0
            print(f"Date: {deal_date} | Price: ${price_m:.2f}M | Type: {type_raw} | Area: {area}")
            print(f"  Building: {building or 'N/A'} | Floor: {floor or 'N/A'} | Unit: {unit or 'N/A'}")
            print(f"  Created: {created_at}")
            print("-" * 80)
    else:
        print("No recent deals found in database")
        
    # Also check total count
    pipeline.cursor.execute("SELECT COUNT(*) FROM stores WHERE deal_date >= %s", (recent_date,))
    count = pipeline.cursor.fetchone()[0]
    print(f"\nTotal deals from {recent_date}: {count}")
    
    # Check August 19th specifically
    pipeline.cursor.execute("SELECT COUNT(*) FROM stores WHERE deal_date = '2025-08-19'")
    aug19_count = pipeline.cursor.fetchone()[0]
    print(f"Deals on 2025-08-19: {aug19_count}")
    
finally:
    pipeline.close_spider(None)
