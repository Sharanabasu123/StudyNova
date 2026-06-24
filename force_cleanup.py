import sqlite3

conn = sqlite3.connect('studynova.db')
cursor = conn.cursor()

print("=== FORCE REMOVING ALL FALLBACK SUBJECTS ===\n")

# Delete ALL fallback subjects from both schemes
cursor.execute("""
    DELETE FROM subjects
    WHERE code LIKE '%0401' OR name LIKE '%Semester Core%'
""")

count = cursor.rowcount
conn.commit()

print(f"✓ Removed {count} fallback subjects from all schemes")

# Verify they're gone
cursor.execute("""
    SELECT COUNT(*) as cnt FROM subjects
    WHERE code LIKE '%0401' OR name LIKE '%Semester Core%'
""")

remaining = cursor.fetchone()[0]
print(f"✓ Remaining: {remaining} fallback subjects")

# Count by scheme
cursor.execute("""
    SELECT sch.id, sch.name, COUNT(*) as cnt
    FROM subjects s
    JOIN schemes sch ON s.scheme_id = sch.id
    GROUP BY sch.id, sch.name
""")

print(f"\nSubjects by Scheme (after cleanup):")
for row in cursor.fetchall():
    print(f"  {row[1]}: {row[2]} subjects")

conn.close()
