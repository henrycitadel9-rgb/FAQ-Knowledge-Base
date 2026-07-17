import sqlite3

conn = sqlite3.connect('data/faq_mvp.sqlite')
cursor = conn.cursor()

# Get table names
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables:', tables)

for table in tables:
    table_name = table[0]
    print(f'\nTable: {table_name}')
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

conn.close()