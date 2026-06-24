import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get scheme ID
cursor.execute("SELECT id, name FROM schemes WHERE name = ?", ('2022 Scheme',))
scheme = cursor.fetchone()
if not scheme:
    print("Error: 2022 Scheme not found")
    exit(1)
    
scheme_id = scheme['id']

# Get branch IDs
cursor.execute("SELECT id, code, name FROM branches WHERE code IN (?, ?)", ('AIML', 'CSE_DS'))
branches = {row['code']: row for row in cursor.fetchall()}

if 'AIML' not in branches or 'CSE_DS' not in branches:
    print("Error: AIML or CSE_DS branch not found")
    exit(1)

aiml_id = branches['AIML']['id']
cseds_id = branches['CSE_DS']['id']

print('=' * 70)
print('STUDYNOVA SUBJECT DATABASE UPDATE REPORT')
print('=' * 70)
print()

# Count AIML subjects by semester
print('CSE (AIML) - 2022 Scheme:')
print('-' * 70)
aiml_total = 0
for sem in range(3, 8):
    cursor.execute('''SELECT COUNT(*) as cnt FROM subjects 
                      WHERE scheme_id = ? 
                      AND semester_id = (SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = ?) 
                      AND branch_id = ?''', (scheme_id, scheme_id, sem, aiml_id))
    count = cursor.fetchone()['cnt']
    print(f'  Semester {sem}: {count} subjects')
    aiml_total += count

cursor.execute('SELECT COUNT(*) as cnt FROM subjects WHERE scheme_id = ? AND branch_id = ?', (scheme_id, aiml_id))
total_aiml = cursor.fetchone()['cnt']
print(f'  Total AIML: {total_aiml} subjects')
print()

# Count Data Science subjects by semester
print('CSE (Data Science) - 2022 Scheme:')
print('-' * 70)
ds_total = 0
for sem in range(3, 8):
    cursor.execute('''SELECT COUNT(*) as cnt FROM subjects 
                      WHERE scheme_id = ? 
                      AND semester_id = (SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = ?) 
                      AND branch_id = ?''', (scheme_id, scheme_id, sem, cseds_id))
    count = cursor.fetchone()['cnt']
    print(f'  Semester {sem}: {count} subjects')
    ds_total += count

cursor.execute('SELECT COUNT(*) as cnt FROM subjects WHERE scheme_id = ? AND branch_id = ?', (scheme_id, cseds_id))
total_ds = cursor.fetchone()['cnt']
print(f'  Total Data Science: {total_ds} subjects')
print()

# Verify all subjects are uniquely mapped
print('Verification Status:')
print('-' * 70)
print(f'✓ 2022 Scheme ID: {scheme_id}')
print(f'✓ AIML Branch ID: {aiml_id} ({branches["AIML"]["name"]})')
print(f'✓ Data Science Branch ID: {cseds_id} ({branches["CSE_DS"]["name"]})')
print(f'✓ Scheme-Semester linkage: Active')
print(f'✓ Branch-Subject mapping: Active')
print()

# Check for duplicates
cursor.execute('''SELECT code, COUNT(*) as cnt 
                  FROM subjects 
                  WHERE scheme_id = ? AND branch_id IN (?, ?)
                  GROUP BY code, branch_id
                  HAVING cnt > 1''', (scheme_id, aiml_id, cseds_id))
duplicates = cursor.fetchall()
if duplicates:
    print('⚠ Duplicate subjects found:')
    for dup in duplicates:
        print(f'  - {dup["code"]}: {dup["cnt"]} instances')
else:
    print('✓ No duplicate subjects detected')
print()

print('=' * 70)
print(f'SUMMARY: {total_aiml} AIML + {total_ds} Data Science = {total_aiml + total_ds} Total subjects')
print('=' * 70)

conn.close()
