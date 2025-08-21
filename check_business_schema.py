import psycopg2

conn = psycopg2.connect(host='localhost', database='property_finder', user='postgres', password='admin')
cursor = conn.cursor()

cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'business' ORDER BY ordinal_position;")
columns = cursor.fetchall()

print('business table columns:')
for col in columns:
    print(f'  {col[0]}: {col[1]}')

cursor.close()
conn.close()
