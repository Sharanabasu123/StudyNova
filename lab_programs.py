"""
StudyNova Lab Programs Module
Interactive Programming Portal for Laboratory Subjects
"""

def init_lab_programs_db(cursor, db_type):
    """Initialize lab programs database tables"""
    
    if db_type == 'sqlite':
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viva_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
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
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                changes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
    
    elif db_type == 'mysql':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                code VARCHAR(50) NOT NULL UNIQUE,
                branch VARCHAR(100) NOT NULL,
                scheme VARCHAR(50) NOT NULL,
                semester INT NOT NULL,
                credits INT DEFAULT 4,
                cie_marks INT DEFAULT 40,
                see_marks INT DEFAULT 60,
                total_marks INT DEFAULT 100,
                teaching_hours_l INT DEFAULT 0,
                teaching_hours_t INT DEFAULT 0,
                teaching_hours_p INT DEFAULT 3,
                teaching_hours_s INT DEFAULT 0,
                subject_image_url TEXT,
                subject_image_public_id VARCHAR(255),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_programs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_id INT NOT NULL,
                program_number INT NOT NULL,
                question LONGTEXT NOT NULL,
                code LONGTEXT NOT NULL,
                programming_language VARCHAR(50) DEFAULT 'python',
                is_published BOOLEAN DEFAULT FALSE,
                sort_order INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES lab_subjects(id) ON DELETE CASCADE,
                UNIQUE KEY unique_subject_program (subject_id, program_number)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS program_outputs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                program_id INT NOT NULL,
                output_type VARCHAR(50) NOT NULL,
                content LONGTEXT,
                image_url TEXT,
                image_public_id VARCHAR(255),
                display_order INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viva_questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                program_id INT NOT NULL,
                question_number INT NOT NULL,
                question LONGTEXT NOT NULL,
                display_order INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                program_id INT NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                is_bookmarked BOOLEAN DEFAULT FALSE,
                completion_date TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_program (user_id, program_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS program_feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                program_id INT NOT NULL,
                user_id INT NOT NULL,
                feedback_type VARCHAR(50) NOT NULL,
                message TEXT,
                is_resolved BOOLEAN DEFAULT FALSE,
                admin_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_admin_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admin_id INT,
                action VARCHAR(255) NOT NULL,
                table_name VARCHAR(100),
                record_id INT,
                changes LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')
    
    elif db_type == 'postgres':
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_subjects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                code VARCHAR(50) NOT NULL UNIQUE,
                branch VARCHAR(100) NOT NULL,
                scheme VARCHAR(50) NOT NULL,
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
                subject_image_public_id VARCHAR(255),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_programs (
                id SERIAL PRIMARY KEY,
                subject_id INTEGER NOT NULL,
                program_number INTEGER NOT NULL,
                question TEXT NOT NULL,
                code TEXT NOT NULL,
                programming_language VARCHAR(50) DEFAULT 'python',
                is_published BOOLEAN DEFAULT FALSE,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES lab_subjects(id) ON DELETE CASCADE,
                UNIQUE(subject_id, program_number)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS program_outputs (
                id SERIAL PRIMARY KEY,
                program_id INTEGER NOT NULL,
                output_type VARCHAR(50) NOT NULL,
                content TEXT,
                image_url TEXT,
                image_public_id VARCHAR(255),
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viva_questions (
                id SERIAL PRIMARY KEY,
                program_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_progress (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                program_id INTEGER NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                is_bookmarked BOOLEAN DEFAULT FALSE,
                completion_date TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE,
                UNIQUE(user_id, program_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS program_feedback (
                id SERIAL PRIMARY KEY,
                program_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                feedback_type VARCHAR(50) NOT NULL,
                message TEXT,
                is_resolved BOOLEAN DEFAULT FALSE,
                admin_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES lab_programs(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lab_admin_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER,
                action VARCHAR(255) NOT NULL,
                table_name VARCHAR(100),
                record_id INTEGER,
                changes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')


def get_branches():
    """Get all available branches"""
    return ['CSE', 'ISE', 'ECE', 'EEE', 'ME', 'CE']


def get_schemes():
    """Get all available schemes"""
    return ['2018', '2022', '2025']


def get_semesters():
    """Get all available semesters"""
    return list(range(1, 9))
