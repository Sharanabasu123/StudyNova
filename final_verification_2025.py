import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 80)
print("STUDYNOVA DATABASE VERIFICATION REPORT")
print("=" * 80)

# Get all schemes
cursor.execute("SELECT id, name, description FROM schemes ORDER BY id")
schemes = cursor.fetchall()

for scheme in schemes:
    print(f"\n{'=' * 80}")
    print(f"SCHEME: {scheme['name']}")
    print(f"Description: {scheme['description']}")
    print(f"{'=' * 80}")
    
    scheme_id = scheme['id']
    
    # Count subjects by branch
    cursor.execute('''
    SELECT b.code, b.name, COUNT(*) as count
    FROM subjects s
    JOIN branches b ON s.branch_id = b.id
    WHERE s.scheme_id = ?
    GROUP BY b.code, b.name
    ORDER BY b.code
    ''', (scheme_id,))
    
    print(f"\nSubject Counts by Branch:")
    total = 0
    for row in cursor.fetchall():
        print(f"  {row['code']:10} ({row['name']:35}): {row['count']:3} subjects")
        total += row['count']
    
    print(f"\n  {'TOTAL':10} {' ' * 35}  {total:3} subjects")
    
    # Semesters
    cursor.execute('SELECT COUNT(*) as cnt FROM semesters WHERE scheme_id = ?', (scheme_id,))
    sem_count = cursor.fetchone()['cnt']
    print(f"\nSemesters: {sem_count}")
    
    # Breakdown by semester
    cursor.execute('''
    SELECT s.semester_number, COUNT(*) as count
    FROM subjects sub
    JOIN semesters s ON sub.semester_id = s.id
    WHERE sub.scheme_id = ? AND s.scheme_id = ?
    GROUP BY s.semester_number
    ORDER BY s.semester_number
    ''', (scheme_id, scheme_id))
    
    print(f"\nSubjects by Semester:")
    for row in cursor.fetchall():
        print(f"  Sem {row['semester_number']}: {row['count']:3} subjects")

# Verification checks
print(f"\n{'=' * 80}")
print("VERIFICATION CHECKS")
print(f"{'=' * 80}")

# Check for duplicates
cursor.execute('''
SELECT scheme_id, semester_id, branch_id, code, COUNT(*) as cnt
FROM subjects
GROUP BY scheme_id, semester_id, branch_id, code
HAVING cnt > 1
''')

duplicates = cursor.fetchall()
if duplicates:
    print(f"\n✗ DUPLICATES FOUND: {len(duplicates)}")
    for dup in duplicates:
        print(f"  Scheme {dup['scheme_id']}, Sem {dup['semester_id']}, Branch {dup['branch_id']}, Code: {dup['code']}")
else:
    print("\n✓ No duplicates found")

# Check foreign key integrity
cursor.execute('''
SELECT COUNT(*) as cnt
FROM subjects
WHERE semester_id NOT IN (SELECT id FROM semesters)
   OR branch_id NOT IN (SELECT id FROM branches)
   OR scheme_id NOT IN (SELECT id FROM schemes)
''')

fk_issues = cursor.fetchone()['cnt']
if fk_issues:
    print(f"\n✗ Foreign Key Issues: {fk_issues}")
else:
    print("✓ Foreign key relationships intact")

# Check resource integrity
cursor.execute('''
SELECT COUNT(*) as cnt
FROM resources
WHERE subject_id NOT IN (SELECT id FROM subjects)
''')

resource_issues = cursor.fetchone()['cnt']
if resource_issues:
    print(f"\n✗ Resource FK Issues: {resource_issues}")
else:
    print("✓ Resource relationships intact")

print(f"\n{'=' * 80}")
print("SUMMARY")
print(f"{'=' * 80}")

# Overall stats
cursor.execute('SELECT COUNT(*) as cnt FROM schemes')
scheme_count = cursor.fetchone()['cnt']

cursor.execute('SELECT COUNT(*) as cnt FROM semesters')
semester_count = cursor.fetchone()['cnt']

cursor.execute('SELECT COUNT(*) as cnt FROM branches')
branch_count = cursor.fetchone()['cnt']

cursor.execute('SELECT COUNT(*) as cnt FROM subjects')
subject_count = cursor.fetchone()['cnt']

cursor.execute('SELECT COUNT(*) as cnt FROM resources')
resource_count = cursor.fetchone()['cnt']

print(f"\nDatabase Statistics:")
print(f"  Schemes:   {scheme_count}")
print(f"  Semesters: {semester_count}")
print(f"  Branches:  {branch_count}")
print(f"  Subjects:  {subject_count}")
print(f"  Resources: {resource_count}")

print(f"\n{'=' * 80}")
print("VERIFICATION COMPLETE")
print(f"{'=' * 80}\n")

conn.close()
