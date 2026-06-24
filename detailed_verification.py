import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('\n' + '=' * 100)
print('DETAILED SUBJECT VERIFICATION BY BRANCH & SEMESTER')
print('=' * 100 + '\n')

# Get scheme
cursor.execute("SELECT id FROM schemes WHERE name = ?", ('2022 Scheme',))
scheme_id = cursor.fetchone()['id']

# Focus on ECE, EEE, ME for now
for branch_code in ['ECE', 'EEE', 'ME']:
    cursor.execute("SELECT id, name FROM branches WHERE code = ?", (branch_code,))
    branch = cursor.fetchone()
    
    print(f"\n{'=' * 100}")
    print(f"BRANCH: {branch_code}")
    print('=' * 100)
    
    total = 0
    for sem in range(3, 8):
        cursor.execute('''
            SELECT s.code, s.name FROM subjects s
            JOIN semesters sem ON s.semester_id = sem.id
            WHERE s.scheme_id = ? AND s.branch_id = ? AND sem.semester_number = ?
            ORDER BY s.code
        ''', (scheme_id, branch['id'], sem))
        
        subjects = cursor.fetchall()
        count = len(subjects)
        total += count
        
        print(f"\nSemester {sem}: {count} subjects")
        print('-' * 100)
        
        for subj in subjects:
            print(f"  {subj['code']:12} - {subj['name']}")
    
    print(f"\n{'─' * 100}")
    print(f"TOTAL FOR {branch_code}: {total} subjects")

# Cross-check semester table
print(f"\n\n{'=' * 100}")
print('SEMESTER CONFIGURATION')
print('=' * 100)

cursor.execute("SELECT semester_number, COUNT(*) as cnt FROM semesters WHERE scheme_id = ? GROUP BY semester_number", (scheme_id,))
semesters = cursor.fetchall()

for sem in semesters:
    print(f"Semester {sem['semester_number']}: {sem['cnt']} records")

conn.close()
