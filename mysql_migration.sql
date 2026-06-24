CREATE DATABASE IF NOT EXISTS studynova;
USE studynova;

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
    UNIQUE KEY uq_semester_scheme_number (scheme_id, semester_number)
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
    UNIQUE KEY uq_subject_path (scheme_id, semester_id, branch_id, cycle_id, code)
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

CREATE TABLE IF NOT EXISTS feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'unread',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    UNIQUE KEY uq_saved_note (user_id, resource_id)
);

CREATE TABLE IF NOT EXISTS viewed_notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    resource_id INT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);

INSERT IGNORE INTO schemes (name, description, is_active) VALUES
    ('2022 Scheme', 'VTU 2022 Scheme for Engineering', 1),
    ('2025 Scheme', 'VTU 2025 Scheme for Engineering', 1);

INSERT IGNORE INTO cycles (name, code) VALUES
    ('P Cycle', 'P_CYCLE'),
    ('C Cycle', 'C_CYCLE');

INSERT IGNORE INTO branches (name, code, is_active) VALUES
    ('Computer Science & Engineering', 'CSE', 1),
    ('Artificial Intelligence & Machine Learning', 'AIML', 1),
    ('Computer Science & Engineering (Data Science)', 'CSE_DS', 1),
    ('Computer Science & Engineering (Cyber Security)', 'CSE_CS', 1),
    ('Information Science & Engineering', 'ISE', 1),
    ('Electronics & Communication Engineering', 'ECE', 1),
    ('Electrical & Electronics Engineering', 'EEE', 1),
    ('Mechanical Engineering', 'ME', 1),
    ('Civil Engineering', 'CV', 1);

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
) AS seq;

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
CROSS JOIN semesters sem
LEFT JOIN cycles p ON p.code = 'P_CYCLE'
LEFT JOIN cycles c ON c.code = 'C_CYCLE';

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

INSERT IGNORE INTO notes (resource_id, subject_id, title, file_url, file_type, created_at)
SELECT r.id, r.subject_id, r.title, r.file_url, r.file_type, r.upload_date
FROM resources r;
