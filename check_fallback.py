import sqlite3
conn = sqlite3.connect('studynova.db')
cursor = conn.cursor()
cursor.execute("SELECT id, code, name, scheme_id FROM subjects WHERE code LIKE '%0401' OR name LIKE '%Semester Core%' ORDER BY scheme_id, code")
print("Remaining fallback subjects:")
for row in cursor.fetchall():
    print(f"  Scheme {row[3]}: {row[1]:10} - {row[2]}")
conn.close()
