import sqlite3

conn = sqlite3.connect('data/faq_mvp.sqlite')
cursor = conn.cursor()

# Get table names
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f'\nTable: {table_name}')
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    print('Columns:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    # Count rows
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'Row count: {count}')

conn.close()