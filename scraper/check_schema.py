#!/usr/bin/env python3

import os
import psycopg2

print('🔍 Checking database schema...')
print()

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url, client_encoding='utf8')
cur = conn.cursor()

# Check what tables exist
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
""")
tables = cur.fetchall()
print('📋 Available tables:')
for table in tables:
    print(f'  - {table[0]}')

print()

# Check if house table exists and its structure
try:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'house' ORDER BY ordinal_position;")
    house_columns = cur.fetchall()
    if house_columns:
        print('🏠 House table columns:')
        for col in house_columns:
            print(f'  - {col[0]}: {col[1]}')
    else:
        print('❌ House table does not exist')
except Exception as e:
    print(f'❌ Error checking house table: {e}')

print()

# Check if location_info table exists
try:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'location_info' ORDER BY ordinal_position;")
    location_columns = cur.fetchall()
    if location_columns:
        print('📍 Location_info table columns:')
        for col in location_columns:
            print(f'  - {col[0]}: {col[1]}')
    else:
        print('❌ Location_info table does not exist')
except Exception as e:
    print(f'❌ Error checking location_info table: {e}')

conn.close()
print()
print('✅ Schema check complete!')
