import sqlite3

conn = sqlite3.connect('data/faq_mvp.sqlite')
cursor = conn.cursor()

# Get table names
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables in faq_mvp.sqlite:')
for table in tables:
    print(f'- {table[0]}')

conn.close()