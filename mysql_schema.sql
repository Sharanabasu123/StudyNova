CREATE DATABASE IF NOT EXISTS studynova;
USE studynova;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    phone VARCHAR(20),
    college VARCHAR(255),
    branch VARCHAR(100),
    semester VARCHAR(50),
    scheme VARCHAR(50),
    profile_photo VARCHAR(255),
    profile_photo_public_id VARCHAR(255),
    bio TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active TINYINT DEFAULT 1
);

-- Academic schema tables
CREATE TABLE IF NOT EXISTS schemes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active TINYINT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS semesters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    scheme_id INT NOT NULL,
    semester_number INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (scheme_id) REFERENCES schemes(id),
    UNIQUE KEY (scheme_id, semester_number)
);

CREATE TABLE IF NOT EXISTS branches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    is_active TINYINT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS cycles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    scheme_id INT NOT NULL,
    semester_id INT NOT NULL,
    branch_id INT,
    cycle_id INT,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    credits INT,
    stream VARCHAR(50),
    is_common TINYINT DEFAULT 0,
    FOREIGN KEY (scheme_id) REFERENCES schemes(id),
    FOREIGN KEY (semester_id) REFERENCES semesters(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id),
    FOREIGN KEY (cycle_id) REFERENCES cycles(id),
    UNIQUE KEY (scheme_id, semester_id, branch_id, cycle_id, code)
);

CREATE TABLE IF NOT EXISTS resources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    subject_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    module_number INT,
    download_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    uploaded_by INT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved TINYINT DEFAULT 1,
    cloudinary_public_id TEXT,
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resource_id INT UNIQUE,
    subject_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'unread',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_downloads (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    resource_id INT NOT NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

CREATE TABLE IF NOT EXISTS saved_notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    resource_id INT NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    UNIQUE KEY (user_id, resource_id)
);

CREATE TABLE IF NOT EXISTS viewed_notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    resource_id INT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'unread',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exam_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exam_topics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_category_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_category_id) REFERENCES exam_categories(id)
);

CREATE TABLE IF NOT EXISTS exam_resources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    exam_topic_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    download_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    uploaded_by INT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved TINYINT DEFAULT 1,
    cloudinary_public_id TEXT,
    FOREIGN KEY (exam_topic_id) REFERENCES exam_topics(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS school_classes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS school_subjects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    school_class_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_class_id) REFERENCES school_classes(id)
);

CREATE TABLE IF NOT EXISTS school_chapters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    school_subject_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    chapter_number INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (school_subject_id) REFERENCES school_subjects(id)
);

CREATE TABLE IF NOT EXISTS school_resources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    school_chapter_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    download_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    uploaded_by INT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_approved TINYINT DEFAULT 1,
    cloudinary_public_id TEXT,
    FOREIGN KEY (school_chapter_id) REFERENCES school_chapters(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- Seed default academic data
INSERT IGNORE INTO schemes (name, description) VALUES
    ('2022 Scheme', 'VTU 2022 Scheme for Engineering'),
    ('2025 Scheme', 'VTU 2025 Scheme for Engineering');

INSERT IGNORE INTO cycles (name, code) VALUES
    ('P Cycle', 'P_CYCLE'),
    ('C Cycle', 'C_CYCLE');

INSERT IGNORE INTO branches (name, code) VALUES
    ('Computer Science & Engineering', 'CSE'),
    ('Artificial Intelligence & Machine Learning', 'AIML'),
    ('Computer Science & Engineering (Data Science)', 'CSE_DS'),
    ('Computer Science & Engineering (Cyber Security)', 'CSE_CS'),
    ('Information Science & Engineering', 'ISE'),
    ('Electronics & Communication Engineering', 'ECE'),
    ('Electrical & Electronics Engineering', 'EEE'),
    ('Mechanical Engineering', 'ME'),
    ('Civil Engineering', 'CV');

INSERT IGNORE INTO semesters (scheme_id, semester_number, name)
SELECT schemes.id, seq.semester_number, seq.name
FROM schemes
JOIN (
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

INSERT IGNORE INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
SELECT sem.scheme_id,
       sem.id,
       br.id,
       CASE WHEN sem.semester_number = 1 THEN p.id WHEN sem.semester_number = 2 THEN c.id ELSE NULL END,
       CONCAT(br.name, ' Semester ', sem.semester_number, ' Core'),
       CONCAT(br.code, LPAD(sem.semester_number, 2, '0'), '01'),
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
LEFT JOIN subjects s ON s.scheme_id = sem.scheme_id AND s.semester_id = sem.id AND s.branch_id = br.id AND s.code = CONCAT(br.code, LPAD(sem.semester_number, 2, '0'), '01')
WHERE s.id IS NULL;

INSERT IGNORE INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
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
