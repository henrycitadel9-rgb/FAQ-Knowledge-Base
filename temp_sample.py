import sqlite3

conn = sqlite3.connect('data/faq_mvp.sqlite')
cursor = conn.cursor()

# Show first 5 faqs
cursor.execute('SELECT faq_number, category, canonical_question, official_answer FROM faqs LIMIT 5')
rows = cursor.fetchall()
print('Sample FAQs:')
for row in rows:
    print(f'FAQ {row[0]} ({row[1]}): {row[2]}')
    print(f'Answer: {row[3][:100]}...' if len(row[3]) > 100 else f'Answer: {row[3]}')
    print()

conn.close()