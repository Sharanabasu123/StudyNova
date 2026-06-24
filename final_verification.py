#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('studynova.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('\n' + '='*100)
print('STUDYNOVA 2022 SCHEME - FINAL VERIFICATION REPORT')
print('='*100 + '\n')

cursor.execute("SELECT id FROM schemes WHERE name = ?", ('2022 Scheme',))
scheme_id = cursor.fetchone()['id']

# Expected counts per user specification
expected = {
    'AIML': 69,  # 12+15+12+18+12
    'CSE_DS': 69,  # 12+15+12+18+12
    'ME': 71,  # 13+15+12+19+12
    'ECE': 69,  # 14+15+11+17+12
    'EEE': 69  # 14+15+11+17+12
}

print('📊 SUBJECT COUNT VERIFICATION')
print('-'*100)
print(f"{'Branch':<12} {'Expected':<12} {'Actual':<12} {'Status':<20}")
print('-'*100)

branches_to_check = ['AIML', 'CSE_DS', 'ME', 'ECE', 'EEE']
all_match = True

for branch_code in branches_to_check:
    cursor.execute("SELECT id FROM branches WHERE code = ?", (branch_code,))
    branch = cursor.fetchone()
    
    if not branch:
        print(f"{branch_code:<12} {expected.get(branch_code, 'N/A'):<12} {'NOT FOUND':<12} ❌ MISSING")
        all_match = False
        continue
    
    cursor.execute("SELECT COUNT(*) as cnt FROM subjects WHERE scheme_id = ? AND branch_id = ?", 
                   (scheme_id, branch['id']))
    actual = cursor.fetchone()['cnt']
    expected_val = expected.get(branch_code)
    
    if actual == expected_val:
        status = '✅ MATCH'
    else:
        status = f'❌ MISMATCH ({actual-expected_val:+d})'
        all_match = False
    
    print(f"{branch_code:<12} {expected_val:<12} {actual:<12} {status:<20}")

print('\n' + '-'*100)

if all_match:
    print('✨ ALL SUBJECT COUNTS VERIFIED AND CORRECT')
else:
    print('⚠️  DISCREPANCIES FOUND - SEE ABOVE')

print('\n' + '='*100)
print('DETAILED SEMESTER BREAKDOWN')
print('='*100)

for branch_code in branches_to_check:
    cursor.execute("SELECT id FROM branches WHERE code = ?", (branch_code,))
    branch_result = cursor.fetchone()
    if not branch_result:
        continue
    
    print(f"\n{branch_code.upper()}")
    print('-'*100)
    
    total = 0
    for sem in range(3, 8):
        cursor.execute('''
            SELECT COUNT(*) as cnt FROM subjects s
            JOIN semesters sem ON s.semester_id = sem.id
            WHERE s.scheme_id = ? AND s.branch_id = ? AND sem.semester_number = ?
        ''', (scheme_id, branch_result['id'], sem))
        
        count = cursor.fetchone()['cnt']
        total += count
        print(f"  Semester {sem}: {count:2} subjects")
    
    print(f"  {'─'*50}")
    print(f"  TOTAL: {total} subjects")

# Integrity checks
print('\n' + '='*100)
print('DATABASE INTEGRITY CHECKS')
print('='*100 + '\n')

# Check for duplicates
cursor.execute('''
    SELECT code, branch_id, semester_id, COUNT(*) as cnt FROM subjects
    WHERE scheme_id = ?
    GROUP BY code, branch_id, semester_id
    HAVING cnt > 1
''', (scheme_id,))

duplicates = cursor.fetchall()
if duplicates:
    print('❌ Duplicate subjects found:')
    for dup in duplicates:
        print(f"   Code {dup['code']} in branch {dup['branch_id']}, semester {dup['semester_id']}: {dup['cnt']} instances")
else:
    print('✓ No duplicate subjects within same branch/semester')

# Check FK integrity
cursor.execute('''
    SELECT COUNT(*) as cnt FROM subjects
    WHERE scheme_id NOT IN (SELECT id FROM schemes)
    OR semester_id NOT IN (SELECT id FROM semesters)
    OR branch_id NOT IN (SELECT id FROM branches)
''')

fk_issues = cursor.fetchone()['cnt']
if fk_issues > 0:
    print(f'❌ {fk_issues} foreign key violations')
else:
    print('✓ All foreign key relationships valid')

# Common subjects verification
print('\n' + '-'*100)
print('COMMON SUBJECTS VERIFICATION')
print('-'*100 + '\n')

common_subjects = [
    ('BCS301', 'Mathematics for Computer Science', 'AIML', 'CSE_DS', 'ECE', 'ME', 'EEE'),
    ('BSCK307', 'Social Connect and Responsibility', 'AIML', 'CSE_DS', 'ECE', 'ME', 'EEE'),
    ('BBOC407', 'Biology for Engineers', 'AIML', 'CSE_DS', 'ECE', 'ME', 'EEE'),
    ('BRMK557', 'Research Methodology and IPR', 'AIML', 'CSE_DS', 'ECE', 'ME', 'EEE'),
]

for code, name, *branches in common_subjects:
    print(f"{code} - {name}")
    all_branches_have = True
    for b in branches:
        cursor.execute('''
            SELECT s.code FROM subjects s
            JOIN branches b ON s.branch_id = b.id
            WHERE s.code = ? AND b.code = ? AND s.scheme_id = ?
        ''', (code, b, scheme_id))
        
        result = cursor.fetchone()
        if result:
            print(f"  ✓ {b}")
        else:
            print(f"  ✗ {b} (MISSING)")
            all_branches_have = False

print('\n' + '='*100)
print('REPORT COMPLETE')
print('='*100 + '\n')

conn.close()
