
import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(__file__), 'studynova.db')

def check_database():
    if not os.path.exists(DATABASE):
        print(f"Database file {DATABASE} not found!")
        return
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n=== SCHEMES ===")
    cursor.execute("SELECT * FROM schemes")
    schemes = cursor.fetchall()
    for scheme in schemes:
        print(f"ID: {scheme['id']}, Name: {scheme['name']}")
    
    print("\n=== SEMESTERS ===")
    cursor.execute("SELECT * FROM semesters")
    semesters = cursor.fetchall()
    for sem in semesters:
        print(f"ID: {sem['id']}, Scheme: {sem['scheme_id']}, Number: {sem['semester_number']}, Name: {sem['name']}")
    
    print("\n=== BRANCHES ===")
    cursor.execute("SELECT * FROM branches")
    branches = cursor.fetchall()
    for branch in branches:
        print(f"ID: {branch['id']}, Name: {branch['name']}, Code: {branch['code']}")
    
    print("\n=== SUBJECTS (First 10 per branch) ===")
    for branch in branches:
        print(f"\nBranch: {branch['name']} (ID: {branch['id']})")
        cursor.execute("SELECT * FROM subjects WHERE branch_id = ? LIMIT 10", (branch['id'],))
        subjects = cursor.fetchall()
        if not subjects:
            print("  No subjects found for this branch!")
        else:
            for sub in subjects:
                print(f"  Code: {sub['code']}, Name: {sub['name']}, Scheme: {sub['scheme_id']}, Semester: {sub['semester_id']}")
    
    print("\n=== COMMON SUBJECTS ===")
    cursor.execute("SELECT * FROM subjects WHERE is_common = 1 LIMIT 10")
    common_subs = cursor.fetchall()
    if common_subs:
        for sub in common_subs:
            print(f"Code: {sub['code']}, Name: {sub['name']}")
    else:
        print("No common subjects found!")
    
    conn.close()

if __name__ == "__main__":
    check_database()
