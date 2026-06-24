import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== TESTING API RESPONSE SIMULATION ===\n")

# Get 2022 scheme
cursor.execute("SELECT id FROM schemes WHERE name = '2022 Scheme'")
scheme = cursor.fetchone()
scheme_id = scheme['id']

# Get CSE branch
cursor.execute("SELECT id FROM branches WHERE code = 'CSE'")
branch = cursor.fetchone()
branch_id = branch['id']

# Get 4th semester
cursor.execute("SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = 4", (scheme_id,))
semester = cursor.fetchone()
semester_id = semester['id']

print(f"Test Case: 2022 Scheme (ID:{scheme_id}) -> CSE Branch (ID:{branch_id}) -> 4th Semester (ID:{semester_id})\n")

# Get branch-specific subjects
cursor.execute('''
    SELECT id, code, name
    FROM subjects
    WHERE scheme_id = ? AND semester_id = ? AND branch_id = ?
    ORDER BY code
''', (scheme_id, semester_id, branch_id))

subjects = cursor.fetchall()
print(f"Branch-specific subjects: {len(subjects)}")
if subjects:
    for s in subjects[:5]:
        print(f"  {s['code']} - {s['name']}")
    if len(subjects) > 5:
        print(f"  ... and {len(subjects) - 5} more")

# Get common subjects
cursor.execute('''
    SELECT id, code, name
    FROM subjects
    WHERE scheme_id = ? AND semester_id = ? AND is_common = 1
    ORDER BY code
''', (scheme_id, semester_id))

common = cursor.fetchall()
print(f"\nCommon subjects: {len(common)}")
if common:
    for s in common:
        print(f"  {s['code']} - {s['name']}")

# Test all branches for 4th semester
print("\n=== 4TH SEMESTER SUBJECT COUNT BY BRANCH ===\n")
cursor.execute('''
    SELECT b.code, COUNT(*) as count
    FROM subjects s
    JOIN branches b ON s.branch_id = b.id
    WHERE s.scheme_id = ? AND s.semester_id = ?
    GROUP BY b.code, b.name
    ORDER BY b.code
''', (scheme_id, semester_id))

for row in cursor.fetchall():
    print(f"  {row['code']:10}: {row['count']:2} subjects")

# Get common subjects count
cursor.execute('''
    SELECT COUNT(*) as count
    FROM subjects
    WHERE scheme_id = ? AND semester_id = ? AND is_common = 1
''', (scheme_id, semester_id))

common_count = cursor.fetchone()['count']
print(f"  {'COMMON':10}: {common_count:2} subjects")

conn.close()
