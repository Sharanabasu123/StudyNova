import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get 2022 scheme
cursor.execute("SELECT id FROM schemes WHERE name = '2022 Scheme'")
scheme = cursor.fetchone()
scheme_id = scheme['id']

print("=== REMOVING FALLBACK/GENERATED SUBJECTS ===\n")

# Remove CV0401 and ISE0401
fallback_ids = [927, 926]  # From previous output
for fid in fallback_ids:
    cursor.execute("SELECT code, name FROM subjects WHERE id = ?", (fid,))
    subject = cursor.fetchone()
    if subject:
        cursor.execute("DELETE FROM subjects WHERE id = ?", (fid,))
        print(f"✓ Removed: {subject['code']} - {subject['name']}")

conn.commit()
print("\n=== VERIFICATION ===\n")

# Verify deletion
cursor.execute("""
SELECT id, code, name
FROM subjects
WHERE scheme_id = ? AND (code LIKE '%0401' OR name LIKE '%Semester Core%')
ORDER BY code
""", (scheme_id,))

remaining = cursor.fetchall()
if remaining:
    print(f"❌ Still {len(remaining)} fallback subjects remaining:")
    for row in remaining:
        print(f"  ID: {row['id']}, Code: {row['code']}, Name: {row['name']}")
else:
    print("✓ All fallback subjects removed!")

# Check subject format for CSE 4th semester
print("\n=== SAMPLE SUBJECTS (CSE, 4th Semester) ===\n")
cursor.execute("""
SELECT s.id, s.code, s.name, b.code as branch_code
FROM subjects s
JOIN branches b ON s.branch_id = b.id
JOIN semesters sem ON s.semester_id = sem.id
WHERE s.scheme_id = ? AND sem.semester_number = 4 AND b.code = 'CSE'
ORDER BY s.code
LIMIT 5
""", (scheme_id,))

for row in cursor.fetchall():
    print(f"  {row['code']} - {row['name']}")

# Count total subjects after deletion
cursor.execute("SELECT COUNT(*) as cnt FROM subjects WHERE scheme_id = ?", (scheme_id,))
total = cursor.fetchone()['cnt']
print(f"\nTotal 2022 Scheme Subjects (after cleanup): {total}")

conn.close()
