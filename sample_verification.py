import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('\nSAMPLE VERIFICATION - AIML Semester 3:')
print('=' * 70)
cursor.execute('''SELECT code, name FROM subjects 
                  WHERE branch_id = (SELECT id FROM branches WHERE code = 'AIML')
                  AND semester_id = (SELECT id FROM semesters WHERE semester_number = 3 AND scheme_id = 1)
                  ORDER BY code LIMIT 6''')
for row in cursor.fetchall():
    print(f'{row["code"]} - {row["name"]}')

print('\nSAMPLE VERIFICATION - Data Science Semester 3:')
print('=' * 70)
cursor.execute('''SELECT code, name FROM subjects 
                  WHERE branch_id = (SELECT id FROM branches WHERE code = 'CSE_DS')
                  AND semester_id = (SELECT id FROM semesters WHERE semester_number = 3 AND scheme_id = 1)
                  ORDER BY code LIMIT 6''')
for row in cursor.fetchall():
    print(f'{row["code"]} - {row["name"]}')

print('\nSAMPLE VERIFICATION - AIML Semester 7:')
print('=' * 70)
cursor.execute('''SELECT code, name FROM subjects 
                  WHERE branch_id = (SELECT id FROM branches WHERE code = 'AIML')
                  AND semester_id = (SELECT id FROM semesters WHERE semester_number = 7 AND scheme_id = 1)
                  ORDER BY code LIMIT 6''')
for row in cursor.fetchall():
    print(f'{row["code"]} - {row["name"]}')

print('\nSAMPLE VERIFICATION - Data Science Semester 7:')
print('=' * 70)
cursor.execute('''SELECT code, name FROM subjects 
                  WHERE branch_id = (SELECT id FROM branches WHERE code = 'CSE_DS')
                  AND semester_id = (SELECT id FROM semesters WHERE semester_number = 7 AND scheme_id = 1)
                  ORDER BY code LIMIT 6''')
for row in cursor.fetchall():
    print(f'{row["code"]} - {row["name"]}')

conn.close()
