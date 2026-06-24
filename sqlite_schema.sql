PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    phone TEXT,
    college TEXT,
    branch TEXT,
    semester TEXT,
    scheme TEXT,
    profile_photo TEXT,
    profile_photo_public_id TEXT,
    bio TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS semesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_id INTEGER NOT NULL,
    semester_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (scheme_id) REFERENCES schemes(id),
    UNIQUE (scheme_id, semester_number)
);

CREATE TABLE IF NOT EXISTS branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    code TEXT UNIQUE NOT NULL,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    code TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_id INTEGER NOT NULL,
    semester_id INTEGER NOT NULL,
    branch_id INTEGER,
    cycle_id INTEGER,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    credits INTEGER,
    stream TEXT,
    is_common INTEGER DEFAULT 0,
    FOREIGN KEY (scheme_id) REFERENCES schemes(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (cycle_id) REFERENCES cycles(id),
    UNIQUE (scheme_id, semester_id, branch_id, cycle_id, code)
);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    module_number INTEGER,
    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    uploaded_by INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved INTEGER DEFAULT 1,
    cloudinary_public_id TEXT,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER UNIQUE,
    subject_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'unread',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'unread',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

CREATE TABLE IF NOT EXISTS saved_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    UNIQUE (user_id, resource_id)
);

CREATE TABLE IF NOT EXISTS viewed_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    resource_id INTEGER NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS exam_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exam_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_category_id) REFERENCES exam_categories(id)
);

CREATE TABLE IF NOT EXISTS exam_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_topic_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    uploaded_by INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved INTEGER DEFAULT 1,
    cloudinary_public_id TEXT,
    FOREIGN KEY (exam_topic_id) REFERENCES exam_topics(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS school_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS school_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_class_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_class_id) REFERENCES school_classes(id)
);

CREATE TABLE IF NOT EXISTS school_chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_subject_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    chapter_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_subject_id) REFERENCES school_subjects(id)
);

CREATE TABLE IF NOT EXISTS school_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_chapter_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    uploaded_by INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved INTEGER DEFAULT 1,
    cloudinary_public_id TEXT,
    FOREIGN KEY (school_chapter_id) REFERENCES school_chapters(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

INSERT OR IGNORE INTO schemes (name, description, is_active) VALUES
    ('2022 Scheme', 'VTU 2022 Scheme for Engineering', 1),
    ('2025 Scheme', 'VTU 2025 Scheme for Engineering', 1);

INSERT OR IGNORE INTO cycles (name, code) VALUES
    ('P Cycle', 'P_CYCLE'),
    ('C Cycle', 'C_CYCLE');

INSERT OR IGNORE INTO branches (name, code, is_active) VALUES
    ('Computer Science & Engineering', 'CSE', 1),
    ('Artificial Intelligence & Machine Learning', 'AIML', 1),
    ('Computer Science & Engineering (Data Science)', 'CSE_DS', 1),
    ('Computer Science & Engineering (Cyber Security)', 'CSE_CS', 1),
    ('Information Science & Engineering', 'ISE', 1),
    ('Electronics & Communication Engineering', 'ECE', 1),
    ('Electrical & Electronics Engineering', 'EEE', 1),
    ('Mechanical Engineering', 'ME', 1),
    ('Civil Engineering', 'CV', 1);

INSERT OR IGNORE INTO semesters (scheme_id, semester_number, name)
SELECT schemes.id, seq.semester_number, seq.name
FROM schemes
CROSS JOIN (
    SELECT 1 AS semester_number, '1st Semester' AS name UNION ALL
    SELECT 2, '2nd Semester' UNION ALL
    SELECT 3, '3rd Semester' UNION ALL
    SELECT 4, '4th Semester' UNION ALL
    SELECT 5, '5th Semester' UNION ALL
    SELECT 6, '6th Semester' UNION ALL
    SELECT 7, '7th Semester' UNION ALL
    SELECT 8, '8th Semester'
) AS seq
LEFT JOIN semesters ON semesters.scheme_id = schemes.id AND semesters.semester_number = seq.semester_number
WHERE semesters.id IS NULL;

INSERT OR IGNORE INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
SELECT sem.scheme_id,
       sem.id,
       br.id,
       CASE WHEN sem.semester_number = 1 THEN p.id WHEN sem.semester_number = 2 THEN c.id ELSE NULL END,
       br.name || ' Semester ' || sem.semester_number || ' Core',
       br.code || printf('%02d', sem.semester_number) || '01',
       4,
       CASE
           WHEN br.code IN ('CSE', 'AIML', 'CSE_DS', 'CSE_CS', 'ISE') THEN 'computer_science'
           WHEN br.code = 'ECE' THEN 'electronics'
           WHEN br.code = 'EEE' THEN 'electrical'
           WHEN br.code = 'ME' THEN 'mechanical'
           WHEN br.code = 'CV' THEN 'civil'
           ELSE NULL
       END,
       0
FROM branches br
JOIN semesters sem ON sem.scheme_id IN (
    SELECT id FROM schemes WHERE name IN ('2022 Scheme', '2025 Scheme')
)
LEFT JOIN cycles p ON p.code = 'P_CYCLE'
LEFT JOIN cycles c ON c.code = 'C_CYCLE'
WHERE NOT EXISTS (
    SELECT 1 FROM subjects s
    WHERE s.scheme_id = sem.scheme_id
      AND s.semester_id = sem.id
      AND s.branch_id = br.id
      AND s.code = br.code || printf('%02d', sem.semester_number) || '01'
);

INSERT OR IGNORE INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
VALUES (
    (SELECT id FROM schemes ORDER BY id LIMIT 1),
    (SELECT id FROM semesters WHERE scheme_id = (SELECT id FROM schemes ORDER BY id LIMIT 1) ORDER BY semester_number LIMIT 1),
    NULL,
    NULL,
    'General StudyNova Notes',
    'GENERAL_NOTES',
    0,
    NULL,
    1
);
