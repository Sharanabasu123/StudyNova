import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== IDENTIFYING REMAINING FALLBACK SUBJECTS ===\n")

cursor.execute("SELECT id FROM schemes WHERE name = '2022 Scheme'")
scheme_id = cursor.fetchone()['id']

cursor.execute('''
    SELECT id, code, name, scheme_id, semester_id, branch_id
    FROM subjects
    WHERE scheme_id = ? AND (code LIKE '%0401' OR name LIKE '%Semester Core%')
    ORDER BY code
''', (scheme_id,))

remaining = cursor.fetchall()
if remaining:
    print(f"Found {len(remaining)} fallback subjects:")
    for row in remaining:
        print(f"\n  ID: {row['id']}")
        print(f"  Code: {row['code']}")
        print(f"  Name: {row['name']}")
        print(f"  Scheme ID: {row['scheme_id']}")
        print(f"  Semester ID: {row['semester_id']}")
        print(f"  Branch ID: {row['branch_id']}")
        
        # Try to delete
        cursor.execute("DELETE FROM subjects WHERE id = ?", (row['id'],))
        print(f"  Deleted!")
else:
    print("No fallback subjects found (already clean)")

conn.commit()

# Now check branch_id for CSE_CS
print("\n=== CHECKING BRANCH IDs ===\n")
cursor.execute('''
    SELECT id, code, name FROM branches
    ORDER BY code
''')

for row in cursor.fetchall():
    print(f"  Branch ID {row['id']:2}: {row['code']:10} - {row['name']}")

# Check subjects for CSE_CS (usually ID 10)
print("\n=== CSE_CS SEMESTER 4 SUBJECTS ===\n")
cursor.execute('''
    SELECT id FROM branches WHERE code = 'CSE_CS'
''')
branch = cursor.fetchone()
if branch:
    cse_cs_id = branch['id']
    cursor.execute('''
        SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = 4
    ''', (scheme_id,))
    sem = cursor.fetchone()
    if sem:
        sem_id = sem['id']
        cursor.execute('''
            SELECT code, name FROM subjects
            WHERE scheme_id = ? AND semester_id = ? AND branch_id = ?
            ORDER BY code
        ''', (scheme_id, sem_id, cse_cs_id))
        
        subjects = cursor.fetchall()
        print(f"Branch ID {cse_cs_id}, Semester ID {sem_id}: {len(subjects)} subjects")
        for s in subjects[:5]:
            print(f"  {s['code']} - {s['name']}")

conn.close()
