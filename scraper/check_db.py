import os
import psycopg2

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Query recent deals
cur.execute("""
SELECT deal_date, deal_price, type_raw, area, created_at 
FROM stores 
WHERE deal_date >= '2025-08-19' 
ORDER BY deal_date DESC, created_at DESC
LIMIT 10
""")

print('Recent deals from 19/8 and later:')
for row in cur.fetchall():
    print(f'Date: {row[0]}, Price: {row[1]}, Type: {row[2]}, Area: {row[3]}, Created: {row[4]}')

# Also check all deals from last few days
cur.execute("""
SELECT COUNT(*) as count, deal_date 
FROM stores 
WHERE deal_date >= '2025-08-15' 
GROUP BY deal_date 
ORDER BY deal_date DESC
""")

print('\nDeal counts by date (recent):')
for row in cur.fetchall():
    print(f'Date: {row[1]}, Count: {row[0]}')

cur.close()
conn.close()
