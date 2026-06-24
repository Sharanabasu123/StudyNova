import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get scheme ID for 2025
cursor.execute("SELECT id FROM schemes WHERE name = '2025 Scheme'")
scheme = cursor.fetchone()
if scheme:
    scheme_id = scheme['id']
    print(f'✓ 2025 Scheme exists (ID: {scheme_id})')
    
    # Count subjects by branch
    cursor.execute('''
    SELECT b.code, b.name, COUNT(*) as count
    FROM subjects s
    JOIN branches b ON s.branch_id = b.id
    WHERE s.scheme_id = ?
    GROUP BY b.code, b.name
    ORDER BY b.code
    ''', (scheme_id,))
    
    print(f'\n2025 Scheme Subject Counts by Branch:')
    total = 0
    for row in cursor.fetchall():
        print(f'  {row["code"]:10} ({row["name"]:30}): {row["count"]:3} subjects')
        total += row['count']
    
    print(f'\nTotal 2025 Scheme Subjects: {total}')
    
    # Verify semesters
    cursor.execute('SELECT COUNT(*) as cnt FROM semesters WHERE scheme_id = ?', (scheme_id,))
    sem_count = cursor.fetchone()['cnt']
    print(f'Total 2025 Semesters: {sem_count}')
    
    # Check by semester
    print('\nSubjects by Semester:')
    cursor.execute('''
    SELECT s.semester_number, COUNT(*) as count
    FROM subjects sub
    JOIN semesters s ON sub.semester_id = s.id
    WHERE sub.scheme_id = ? AND s.scheme_id = ?
    GROUP BY s.semester_number
    ORDER BY s.semester_number
    ''', (scheme_id, scheme_id))
    
    for row in cursor.fetchall():
        print(f'  Sem {row["semester_number"]}: {row["count"]} subjects')
else:
    print('✗ 2025 Scheme not found')

conn.close()
