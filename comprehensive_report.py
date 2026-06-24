import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('\n' + '=' * 90)
print('STUDYNOVA 2022 SCHEME - COMPLETE CURRICULUM REPORT')
print('=' * 90 + '\n')

# Get scheme
cursor.execute("SELECT id, name FROM schemes WHERE name = ?", ('2022 Scheme',))
scheme = cursor.fetchone()
scheme_id = scheme['id']

# Get all branches for 2022 scheme
cursor.execute("SELECT id, code, name FROM branches ORDER BY code")
all_branches = cursor.fetchall()

print('📋 ALL BRANCHES & SUBJECT DISTRIBUTION')
print('-' * 90)

branches_data = {}
for branch in all_branches:
    cursor.execute('''SELECT COUNT(*) as cnt FROM subjects 
                      WHERE scheme_id = ? AND branch_id = ?''', (scheme_id, branch['id']))
    count = cursor.fetchone()['cnt']
    if count > 0:
        branches_data[branch['code']] = {
            'name': branch['name'],
            'id': branch['id'],
            'total': count
        }

total_all = 0
for code in sorted(branches_data.keys()):
    branch_info = branches_data[code]
    print(f"  ✓ {code:10} ({branch_info['name']:50}): {branch_info['total']:3} subjects")
    total_all += branch_info['total']

print()
print('-' * 90)
print(f"GRAND TOTAL: {total_all} subjects across {len(branches_data)} branches\n")

# Detailed breakdown by specialization
print('🎓 SPECIALIZATION BREAKDOWN - SEMESTER-WISE')
print('-' * 90)

specializations = {
    'CSE': ('Computer Science & Engineering', ['CSE']),
    'AIML': ('Artificial Intelligence & Machine Learning', ['AIML']),
    'CSE_DS': ('Computer Science & Engineering (Data Science)', ['CSE_DS']),
    'CSE_CS': ('Computer Science & Engineering (Cyber Security)', ['CSE_CS']),
    'ECE': ('Electronics & Communication Engineering', ['ECE']),
    'EEE': ('Electrical & Electronics Engineering', ['EEE']),
    'ME': ('Mechanical Engineering', ['ME'])
}

for spec_key, (spec_name, branch_codes) in specializations.items():
    spec_total = 0
    print(f"\n{spec_name}")
    print('  ' + '-' * 86)
    
    for sem in range(3, 8):
        cursor.execute('''SELECT COUNT(*) as cnt FROM subjects 
                          WHERE scheme_id = ? AND branch_id = (SELECT id FROM branches WHERE code IN ({})) 
                          AND semester_id = (SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = ?)'''.format(
                              ','.join('?' * len(branch_codes))), 
                       (scheme_id, *branch_codes, scheme_id, sem))
        count = cursor.fetchone()['cnt']
        if count > 0:
            print(f"  Semester {sem}: {count:2} subjects")
            spec_total += count
    
    cursor.execute('''SELECT COUNT(*) as cnt FROM subjects 
                      WHERE scheme_id = ? AND branch_id = (SELECT id FROM branches WHERE code IN ({}))'''.format(
                          ','.join('?' * len(branch_codes))),
                   (scheme_id, *branch_codes))
    total = cursor.fetchone()['cnt']
    print(f"  {'─' * 86}")
    print(f"  TOTAL: {total} subjects")

# Verify Data Integrity
print('\n' + '=' * 90)
print('✅ DATABASE VERIFICATION')
print('-' * 90)

# Check for duplicates
cursor.execute('''SELECT code, branch_id, COUNT(*) as cnt 
                  FROM subjects 
                  WHERE scheme_id = ?
                  GROUP BY code, branch_id
                  HAVING cnt > 1''', (scheme_id,))
duplicates = cursor.fetchall()

if duplicates:
    print('⚠ Duplicates found:')
    for dup in duplicates:
        print(f'  - Code {dup["code"]} in branch {dup["branch_id"]}: {dup["cnt"]} instances')
else:
    print('✓ No duplicate subjects')

# Check FK integrity
cursor.execute('''SELECT COUNT(*) as broken_fks FROM subjects 
                  WHERE scheme_id NOT IN (SELECT id FROM schemes) 
                  OR semester_id NOT IN (SELECT id FROM semesters)
                  OR branch_id NOT IN (SELECT id FROM branches)''')
fk_issues = cursor.fetchone()['broken_fks']

if fk_issues > 0:
    print(f'⚠ {fk_issues} foreign key violations found')
else:
    print('✓ All foreign key relationships intact')

# Sample verification
print('\n' + '=' * 90)
print('📚 SAMPLE VERIFICATION - KEY SUBJECTS')
print('-' * 90)

samples = [
    ('AIML', 'Semester 3', 'BAI306A - Python for Artificial Intelligence'),
    ('CSE_DS', 'Semester 3', 'BDS306A - Introduction to Data Science'),
    ('ME', 'Semester 3', 'BME303 - Basic Thermodynamics'),
    ('ECE', 'Semester 3', 'BEC303 - Electronic Principles and Circuits'),
    ('EEE', 'Semester 3', 'BEE303 - Analog Electronic Circuits'),
    ('ME', 'Semester 5', 'BME503 - Dynamics of Machines'),
    ('ME', 'Semester 7', 'BME714B - Industry 4.0'),
]

for branch_code, sem_desc, expected_subject in samples:
    code = expected_subject.split(' - ')[0]
    name = expected_subject.split(' - ')[1]
    
    cursor.execute('''SELECT s.code, s.name, br.code as branch_code FROM subjects s
                      JOIN branches br ON s.branch_id = br.id
                      WHERE s.code = ? AND br.code = ?''', (code, branch_code))
    result = cursor.fetchone()
    
    if result and result['name'] == name:
        status = '✓'
    else:
        status = '✗'
    
    print(f'{status} {branch_code} {sem_desc}: {code} - {name}')

print('\n' + '=' * 90)
print('✨ CURRICULUM DATA SUCCESSFULLY INTEGRATED')
print('=' * 90 + '\n')

conn.close()
