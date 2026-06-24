import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get 2022 scheme
cursor.execute("SELECT id FROM schemes WHERE name = '2022 Scheme'")
scheme = cursor.fetchone()
if scheme:
    scheme_id = scheme['id']
    print(f'2022 Scheme (ID: {scheme_id})')
    
    # Count subjects by branch
    cursor.execute('''
    SELECT b.code, b.name, COUNT(*) as count
    FROM subjects s
    JOIN branches b ON s.branch_id = b.id
    WHERE s.scheme_id = ?
    GROUP BY b.code, b.name
    ORDER BY b.code
    ''', (scheme_id,))
    
    print(f'\n2022 Scheme Subject Counts by Branch:')
    total = 0
    for row in cursor.fetchall():
        print(f'  {row["code"]:10} ({row["name"]:30}): {row["count"]:3} subjects')
        total += row['count']
    
    print(f'\nTotal 2022 Scheme Subjects: {total}')
    
    # Verify semesters
    cursor.execute('SELECT COUNT(*) as cnt FROM semesters WHERE scheme_id = ?', (scheme_id,))
    sem_count = cursor.fetchone()['cnt']
    print(f'Total 2022 Semesters: {sem_count}')
    
    # List semesters
    cursor.execute('SELECT id, semester_number, name FROM semesters WHERE scheme_id = ? ORDER BY semester_number', (scheme_id,))
    print(f'\nSemesters:')
    for row in cursor.fetchall():
        print(f'  Sem {row["semester_number"]}: {row["name"]}')
    
    # Check for fallback/generated subjects
    print(f'\n--- Checking for Fallback/Generated Subjects ---')
    cursor.execute('''
    SELECT id, code, name, semester_id, branch_id
    FROM subjects
    WHERE scheme_id = ? AND (code LIKE '%0401' OR name LIKE '%Semester Core%')
    ORDER BY code
    ''', (scheme_id,))
    
    fallback_subjects = cursor.fetchall()
    if fallback_subjects:
        print(f'Found {len(fallback_subjects)} fallback/generated subjects:')
        for row in fallback_subjects:
            print(f'  ID: {row["id"]}, Code: {row["code"]}, Name: {row["name"]}')
    else:
        print('No fallback/generated subjects found.')
    
    # Check specific branches required
    print(f'\n--- Checking Required Branches ---')
    required_branches = ['CSE', 'ISE', 'AIML', 'CSE_DS', 'CSE_CS', 'ECE', 'EEE', 'ME']
    cursor.execute('''
    SELECT DISTINCT b.code, b.name
    FROM subjects s
    JOIN branches b ON s.branch_id = b.id
    WHERE s.scheme_id = ?
    ORDER BY b.code
    ''', (scheme_id,))
    
    existing_codes = [row['code'] for row in cursor.fetchall()]
    for req_branch in required_branches:
        status = '✓' if req_branch in existing_codes else '✗'
        print(f'  {status} {req_branch}')

conn.close()
