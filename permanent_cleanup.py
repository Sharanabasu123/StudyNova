import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== PERMANENT REMOVAL OF FALLBACK SUBJECTS ===\n")

cursor.execute("SELECT id FROM schemes WHERE name = '2022 Scheme'")
scheme_id = cursor.fetchone()['id']

# First, let's check what the verification script is looking for
cursor.execute('''
    SELECT id, code, name, scheme_id, semester_id
    FROM subjects
    WHERE scheme_id = ? AND (code LIKE '%0401' OR name LIKE '%Semester Core%')
''', (scheme_id,))

subjects_to_remove = cursor.fetchall()
print(f"Current fallback subjects in scheme_id {scheme_id}:")
for row in subjects_to_remove:
    print(f"  ID: {row['id']:4} | Code: {row['code']:10} | Name: {row['name']}")

# Let me check if perhaps these are being added back by init_db
# Check ALL schemes for fallback subjects
print(f"\n=== CHECKING ALL SCHEMES ===\n")
cursor.execute('''
    SELECT DISTINCT scheme_id FROM subjects
    WHERE code LIKE '%0401' OR name LIKE '%Semester Core%'
''')

for row in cursor.fetchall():
    scheme_id_to_fix = row['scheme_id']
    cursor.execute('''
        SELECT COUNT(*) as cnt FROM subjects
        WHERE scheme_id = ? AND (code LIKE '%0401' OR name LIKE '%Semester Core%')
    ''', (scheme_id_to_fix,))
    count = cursor.fetchone()['cnt']
    print(f"Scheme ID {scheme_id_to_fix}: {count} fallback subjects")

# Now let's delete from ALL schemes
cursor.execute('''
    DELETE FROM subjects
    WHERE code LIKE '%0401' OR name LIKE '%Semester Core%'
''')

conn.commit()
print(f"\n✓ Deleted all fallback subjects from all schemes")

# Verify deletion
cursor.execute('''
    SELECT COUNT(*) as cnt FROM subjects
    WHERE code LIKE '%0401' OR name LIKE '%Semester Core%'
''')
remaining = cursor.fetchone()['cnt']
print(f"✓ Remaining fallback subjects: {remaining}")

# Re-count subjects by scheme
print(f"\n=== SUBJECT COUNT BY SCHEME (AFTER CLEANUP) ===\n")
cursor.execute('''
    SELECT sch.id, sch.name, COUNT(*) as cnt
    FROM subjects s
    JOIN schemes sch ON s.scheme_id = sch.id
    GROUP BY sch.id, sch.name
    ORDER BY sch.name
''')

for row in cursor.fetchall():
    print(f"{row['name']}: {row['cnt']} subjects")

conn.close()
