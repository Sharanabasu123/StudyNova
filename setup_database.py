import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'studynova.db')


def get_stream_for_branch(branch_code):
    if not branch_code:
        return None
    branch_code = branch_code.upper()
    if branch_code in ('CSE', 'AIML', 'CSE_DS', 'CSE_CS', 'ISE'):
        return 'computer_science'
    if branch_code == 'ECE':
        return 'electronics'
    if branch_code == 'EEE':
        return 'electrical'
    if branch_code == 'ME':
        return 'mechanical'
    if branch_code == 'CV':
        return 'civil'
    return None


def validate_sqlite_file(path):
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'rb') as f:
            header = f.read(16)
        return header.startswith(b'SQLite format 3')
    except Exception:
        return False


def ensure_default_subjects(cursor):
    cursor.execute('SELECT id, code, name FROM branches')
    branches = cursor.fetchall()
    cursor.execute('SELECT id, scheme_id, semester_number FROM semesters')
    semesters = cursor.fetchall()

    cursor.execute("SELECT id FROM cycles WHERE name = ?", ('P Cycle',))
    p_cycle_row = cursor.fetchone()
    p_cycle_id = p_cycle_row[0] if p_cycle_row else None
    cursor.execute("SELECT id FROM cycles WHERE name = ?", ('C Cycle',))
    c_cycle_row = cursor.fetchone()
    c_cycle_id = c_cycle_row[0] if c_cycle_row else None

    # DISABLED: Do not create automatic "Core" subjects - use only explicitly defined subjects from populate_2022_scheme.py
    # for sem in semesters:
    #     semester_id, scheme_id, semester_number = sem
    #     cycle_id = p_cycle_id if semester_number == 1 else c_cycle_id if semester_number == 2 else None
    #
    #     for branch in branches:
    #         branch_id, branch_code, branch_name = branch
    #         cursor.execute(
    #             "SELECT id FROM subjects WHERE scheme_id = ? AND semester_id = ? AND branch_id = ?",
    #             (scheme_id, semester_id, branch_id)
    #         )
    #         if cursor.fetchone():
    #             continue
    #
    #         subject_code = f"{branch_code}{semester_number:02d}01"
    #         subject_name = f"{branch_name} Semester {semester_number} Core"
    #         cursor.execute('''
    #             INSERT INTO subjects (name, code, branch_id, semester_id, scheme_id, cycle_id, stream, is_common, credits)
    #             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         ''', (subject_name, subject_code, branch_id, semester_id, scheme_id, cycle_id, get_stream_for_branch(branch_code), 0, 4))


def init_db():
    if os.path.exists(DB_PATH) and not validate_sqlite_file(DB_PATH):
        invalid_path = DB_PATH + '.invalid'
        print(f"[DEBUG] Invalid SQLite database detected. Renaming {DB_PATH} to {invalid_path}")
        os.replace(DB_PATH, invalid_path)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            college TEXT,
            branch_id INTEGER,
            semester_id INTEGER,
            scheme_id INTEGER,
            bio TEXT,
            profile_photo TEXT,
            profile_photo_public_id TEXT,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            branch_id INTEGER,
            semester_id INTEGER,
            scheme_id INTEGER,
            cycle_id INTEGER,
            stream TEXT,
            is_common INTEGER DEFAULT 0,
            credits INTEGER DEFAULT 4
        )
    ''')
    
    # Schemes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Semesters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semesters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_id INTEGER NOT NULL,
            semester_number INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (scheme_id) REFERENCES schemes(id)
        )
    ''')
    
    # Cycles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    
    # Branches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT
        )
    ''')
    
    # Resources table (notes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            file_url TEXT NOT NULL,
            file_type TEXT,
            resource_type TEXT NOT NULL,
            module_number INTEGER,
            uploaded_by INTEGER,
            is_approved INTEGER DEFAULT 1,
            cloudinary_public_id TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            view_count INTEGER DEFAULT 0,
            download_count INTEGER DEFAULT 0,
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    ''')

    # Team members table for About/Founders management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT,
            bio TEXT,
            profile_url TEXT,
            profile_public_id TEXT,
            linkedin_url TEXT,
            github_url TEXT,
            is_founder INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if schemes exist, if not, create them
    cursor.execute("SELECT COUNT(*) FROM schemes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO schemes (name, description) VALUES (?, ?)", 
                      ('2022 Scheme', 'VTU 2022 Scheme for Engineering'))
        cursor.execute("INSERT INTO schemes (name, description) VALUES (?, ?)", 
                      ('2025 Scheme', 'VTU 2025 Scheme for Engineering'))
    
    # Check if cycles exist
    cursor.execute("SELECT COUNT(*) FROM cycles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO cycles (name) VALUES (?)", ('Physics Cycle',))
        cursor.execute("INSERT INTO cycles (name) VALUES (?)", ('Chemistry Cycle',))
    
    # Check if branches exist (all branches for both schemes)
    cursor.execute("SELECT COUNT(*) FROM branches")
    if cursor.fetchone()[0] == 0:
        branches = [
            ('Computer Science & Engineering', 'CSE'),
            ('Artificial Intelligence & Machine Learning', 'AIML'),
            ('Computer Science & Engineering (Data Science)', 'CSE_DS'),
            ('Computer Science & Engineering (Cyber Security)', 'CSE_CS'),
            ('Information Science & Engineering', 'ISE'),
            ('Electronics & Communication Engineering', 'ECE'),
            ('Electrical & Electronics Engineering', 'EEE'),
            ('Mechanical Engineering', 'ME'),
            ('Civil Engineering', 'CV')
        ]
        for name, code in branches:
            cursor.execute("INSERT INTO branches (name, code) VALUES (?, ?)", (name, code))
    
    # Check if admin user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_pw = generate_password_hash('studynova@2026')
        cursor.execute('''
            INSERT INTO users (username, email, password, role) 
            VALUES (?, ?, ?, ?)
        ''', ('StudyNova Admin', 'studynovaofficial@gmail.com', admin_pw, 'admin'))
    
    # Create semesters for both schemes, including 8th semester
    schemes = cursor.execute("SELECT * FROM schemes").fetchall()
    for scheme in schemes:
        # Check if we already have semesters for this scheme
        cursor.execute("SELECT COUNT(*) FROM semesters WHERE scheme_id = ?", (scheme[0],))
        if cursor.fetchone()[0] == 0:
            sem_range = range(1,9)  # 1 to 8 inclusive
            for num in sem_range:
                sem_name = f"{num}{'st' if num == 1 else 'nd' if num == 2 else 'rd' if num == 3 else 'th'} Semester"
                cursor.execute('''
                    INSERT INTO semesters (scheme_id, semester_number, name)
                    VALUES (?, ?, ?)
                ''', (scheme[0], num, sem_name))
    
    # Ensure placeholder subjects exist for every branch and semester
    ensure_default_subjects(cursor)

    conn.commit()
    conn.close()
    print("✅ Database initialized!")

# Now import the populate_2022 and populate_2025 functions!
from populate_2022_scheme import populate as populate_2022
from populate_2025_scheme import populate as populate_2025

if __name__ == "__main__":
    print("🚀 Initializing database...")
    init_db()
    
    # Now connect again to populate
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print("\n📚 Populating 2022 Scheme subjects...")
    populate_2022(conn)
    
    print("\n📚 Populating 2025 Scheme subjects...")
    populate_2025(conn)
    
    conn.close()
    print("\n✅ Database setup complete! Now run `python app.py`")
