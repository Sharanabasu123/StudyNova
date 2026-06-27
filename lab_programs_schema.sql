-- Lab Programs Module Database Schema
-- Created for StudyNova Interactive Programming Portal

-- Lab Subjects Table
CREATE TABLE IF NOT EXISTS lab_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    branch TEXT NOT NULL,
    scheme TEXT NOT NULL,
    semester INTEGER NOT NULL,
    credits INTEGER DEFAULT 4,
    cie_marks INTEGER DEFAULT 40,
    see_marks INTEGER DEFAULT 60,
    total_marks INTEGER DEFAULT 100,
    teaching_hours_l INTEGER DEFAULT 0,
    teaching_hours_t INTEGER DEFAULT 0,
    teaching_hours_p INTEGER DEFAULT 3,
    teaching_hours_s INTEGER DEFAULT 0,
    subject_image_url TEXT,
    subject_image_public_id TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lab Programs Table
CREATE TABLE IF NOT EXISTS lab_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    program_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    code TEXT NOT NULL,
    programming_language TEXT DEFAULT 'python',
    is_published BOOLEAN DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES lab_subjects(id) ON DELETE CASCADE,
    UNIQUE(subject_id, program_number)
);

-- Program Output Table (for console output and output images)
CREATE TABLE IF NOT EXISTS program_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    output_type TEXT NOT NULL,
    content TEXT,
    image_url TEXT,
    image_public_id TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE
);
-- output_type: 'console', 'screenshot', 'graph', 'output_image'

-- Viva Questions Table
CREATE TABLE IF NOT EXISTS viva_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    question_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE
);

-- Student Progress Table (to track completed programs and bookmarks)
CREATE TABLE IF NOT EXISTS student_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    program_id INTEGER NOT NULL,
    is_completed BOOLEAN DEFAULT 0,
    is_bookmarked BOOLEAN DEFAULT 0,
    completion_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE,
    UNIQUE(user_id, program_id)
);

-- Program Feedback Table (for reporting issues)
CREATE TABLE IF NOT EXISTS program_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    feedback_type TEXT NOT NULL,
    message TEXT,
    is_resolved BOOLEAN DEFAULT 0,
    admin_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
-- feedback_type: 'bug_report', 'code_error', 'incorrect_output', 'suggestion'

-- Admin Activity Log
CREATE TABLE IF NOT EXISTS lab_admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    table_name TEXT,
    record_id INTEGER,
    changes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
);
