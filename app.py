from functools import wraps
from flask import Flask, abort, flash, jsonify, make_response, render_template, request, redirect, session, url_for, send_from_directory, send_file
import json
import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import shutil
import smtplib
from uuid import uuid4
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Admin notification settings - all contact form messages are forwarded to this email
ADMIN_NOTIFICATION_EMAIL = os.environ.get('MAIL_DEFAULT_SENDER', 'demo@studynova.com')

# Cloudinary Integration
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True

    # Configure Cloudinary from environment variables
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )
except ImportError:
    CLOUDINARY_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('STUDYNOVA_SECRET_KEY') or os.urandom(32)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
DATABASE = os.path.join(os.path.dirname(__file__), 'studynova.db')
ALLOWED_UPLOAD_EXTENSIONS = {'pdf', 'ppt', 'pptx', 'doc', 'docx'}
_database_initialized = False

@app.before_request
def ensure_database_initialized():
    """Ensure the database schema and academic data exist once per process."""
    global _database_initialized
    if not _database_initialized:
        init_db()
        _database_initialized = True

# Route to serve uploaded files
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Make execute_query available in templates
@app.context_processor
def utility_processor():
    return dict(execute_query=execute_query, get_placeholder=get_placeholder)


MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'user': os.environ.get('MYSQL_USER', 'studynova'),
    'password': os.environ.get('MYSQL_PASSWORD', 'studynova'),
    'database': os.environ.get('MYSQL_DATABASE', 'studynova'),
}

USE_MYSQL = all([
    os.environ.get('MYSQL_HOST'),
    os.environ.get('MYSQL_USER'),
    os.environ.get('MYSQL_PASSWORD'),
    os.environ.get('MYSQL_DATABASE'),
])

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    mysql = None
    MYSQL_AVAILABLE = False


def mysql_enabled():
    return USE_MYSQL and MYSQL_AVAILABLE


def get_db_connection():
    if mysql_enabled():
        return mysql.connector.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
        )

    if os.path.exists(DATABASE):
        try:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute('PRAGMA schema_version')
            return conn
        except sqlite3.DatabaseError:
            try:
                conn.close()
            except Exception:
                pass
            invalid_path = DATABASE + '.invalid'
            if os.path.exists(invalid_path):
                invalid_path = DATABASE + f".invalid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"[DEBUG] Invalid SQLite database detected. Renaming {DATABASE} to {invalid_path} and creating a fresh database.")
            os.replace(DATABASE, invalid_path)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def get_placeholder():
    return '%s' if mysql_enabled() else '?'


def execute_query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    params = params or ()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) if mysql_enabled() else conn.cursor()
    try:
        cursor.execute(sql, params)
        if commit:
            conn.commit()
        if fetchone:
            row = cursor.fetchone()
            if mysql_enabled():
                return row
            else:
                # Convert sqlite3.Row to dict for consistent access with .get()
                return dict(row) if row else None
        if fetchall:
            rows = cursor.fetchall()
            if mysql_enabled():
                return rows
            else:
                # Convert all sqlite3.Row to dict
                return [dict(row) for row in rows]
    finally:
        cursor.close()
        conn.close()


# Read a user record by email address.
def get_user_by_email(email):
    placeholder = get_placeholder()
    query = f'SELECT * FROM users WHERE email = {placeholder}'
    return execute_query(query, (email,), fetchone=True)


def create_user(username, email, password):
    placeholder = get_placeholder()
    hashed_password = generate_password_hash(password)
    query = f'INSERT INTO users (username, email, password) VALUES ({placeholder}, {placeholder}, {placeholder})'
    execute_query(query, (username, email, hashed_password), commit=True)


def column_exists(cursor, table_name, column_name):
    if mysql_enabled():
        cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (column_name,))
        return cursor.fetchone() is not None

    cursor.execute(f"PRAGMA table_info({table_name})")
    return column_name in [col[1] for col in cursor.fetchall()]


def add_column_if_missing(cursor, table_name, column_name, column_definition):
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def insert_ignore_sql(table, columns):
    placeholder = get_placeholder()
    placeholders = ", ".join([placeholder] * len(columns))
    column_list = ", ".join(columns)
    verb = "INSERT IGNORE" if mysql_enabled() else "INSERT OR IGNORE"
    return f"{verb} INTO {table} ({column_list}) VALUES ({placeholders})"


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if users table exists and has required columns
    users_table_exists = False
    has_role_column = True
    has_bio_column = True
    has_profile_photo_id_column = True
    existing_columns = []
    if mysql_enabled():
        cursor.execute("SHOW TABLES LIKE 'users'")
        users_table_exists = cursor.fetchone() is not None
        if users_table_exists:
            cursor.execute("DESCRIBE users")
            existing_columns = [col[0] for col in cursor.fetchall()]
            has_role_column = 'role' in existing_columns
            has_bio_column = 'bio' in existing_columns
            has_profile_photo_id_column = 'profile_photo_public_id' in existing_columns
        else:
            has_role_column = False
            has_bio_column = False
            has_profile_photo_id_column = False
    else:
        cursor.execute("PRAGMA table_info(users)")
        users_columns = cursor.fetchall()
        users_table_exists = len(users_columns) > 0
        if users_table_exists:
            existing_columns = [col[1] for col in users_columns]
            has_role_column = 'role' in existing_columns
            has_bio_column = 'bio' in existing_columns
            has_profile_photo_id_column = 'profile_photo_public_id' in existing_columns
        else:
            has_role_column = False
            has_bio_column = False
            has_profile_photo_id_column = False

    if users_table_exists and (not has_role_column or not has_bio_column or not has_profile_photo_id_column):
        # Migrate users table
        print("Migrating users table...")

        # Columns we want to keep
        keep_columns = ['id', 'username', 'email', 'password']
        # Add columns that exist
        if 'role' in existing_columns:
            keep_columns.append('role')
        if 'phone' in existing_columns:
            keep_columns.append('phone')
        if 'college' in existing_columns:
            keep_columns.append('college')
        if 'branch' in existing_columns:
            keep_columns.append('branch')
        if 'semester' in existing_columns:
            keep_columns.append('semester')
        if 'scheme' in existing_columns:
            keep_columns.append('scheme')
        if 'profile_photo' in existing_columns:
            keep_columns.append('profile_photo')
        if 'is_active' in existing_columns:
            keep_columns.append('is_active')

        if mysql_enabled():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users_new (
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
                )
            ''')
            # Build insert query dynamically
            insert_cols = ", ".join(keep_columns)
            select_cols = ", ".join(keep_columns)
            cursor.execute(f'''
                INSERT IGNORE INTO users_new ({insert_cols})
                SELECT {select_cols} FROM users
            ''')
            cursor.execute('DROP TABLE users')
            cursor.execute('RENAME TABLE users_new TO users')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
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
                )
            ''')
            insert_cols = ", ".join(keep_columns)
            select_cols = ", ".join(keep_columns)
            cursor.execute(f'''
                INSERT INTO users_new ({insert_cols})
                SELECT {select_cols} FROM users
            ''')
            cursor.execute('DROP TABLE users')
            cursor.execute('ALTER TABLE users_new RENAME TO users')
        print("Users table migrated successfully!")

    if not users_table_exists:
        if mysql_enabled():
            cursor.execute('''
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
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
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
                )
            ''')

    try:
        add_column_if_missing(cursor, 'users', 'role', "VARCHAR(50) DEFAULT 'user'" if mysql_enabled() else "TEXT DEFAULT 'user'")
        add_column_if_missing(cursor, 'users', 'phone', "VARCHAR(20)" if mysql_enabled() else "TEXT")
        add_column_if_missing(cursor, 'users', 'college', "VARCHAR(255)" if mysql_enabled() else "TEXT")
        add_column_if_missing(cursor, 'users', 'branch', "VARCHAR(100)" if mysql_enabled() else "TEXT")
        add_column_if_missing(cursor, 'users', 'semester', "VARCHAR(50)" if mysql_enabled() else "TEXT")
        add_column_if_missing(cursor, 'users', 'scheme', "VARCHAR(50)" if mysql_enabled() else "TEXT")
        add_column_if_missing(cursor, 'users', 'profile_photo', "VARCHAR(255)" if mysql_enabled() else "TEXT")
        add_column_if_missing(cursor, 'users', 'profile_photo_public_id', "VARCHAR(255)" if mysql_enabled() else "TEXT")
        add_column_if_missing(cursor, 'users', 'bio', "TEXT")
        add_column_if_missing(cursor, 'users', 'registration_date', "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if mysql_enabled() else "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        add_column_if_missing(cursor, 'users', 'is_active', "TINYINT DEFAULT 1" if mysql_enabled() else "INTEGER DEFAULT 1")
    except Exception as e:
        print(f"Error ensuring users columns: {e}")

    # Create schemes table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schemes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                is_active TINYINT DEFAULT 1
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schemes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')

    # Create semesters table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semesters (
                id INT PRIMARY KEY AUTO_INCREMENT,
                scheme_id INT NOT NULL,
                semester_number INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                FOREIGN KEY (scheme_id) REFERENCES schemes(id),
                UNIQUE KEY (scheme_id, semester_number)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semesters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheme_id INTEGER NOT NULL,
                semester_number INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (scheme_id) REFERENCES schemes(id),
                UNIQUE(scheme_id, semester_number)
            )
        ''')

    # Create branches table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS branches (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL,
                is_active TINYINT DEFAULT 1
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                code TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')

    # Create cycles table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cycles (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                code TEXT UNIQUE NOT NULL
            )
        ''')

    # Create streams table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streams (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL,
                description TEXT
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                code TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')

    # Create subjects table
    if mysql_enabled():
        cursor.execute('''
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
            )
        ''')
    else:
        cursor.execute('''
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
                UNIQUE(scheme_id, semester_id, branch_id, cycle_id, code)
            )
        ''')

    # Add stream and is_common columns if they don't exist
    try:
        if mysql_enabled():
            cursor.execute("SHOW COLUMNS FROM subjects LIKE 'stream'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE subjects ADD COLUMN stream VARCHAR(50)")
                conn.commit()
            cursor.execute("SHOW COLUMNS FROM subjects LIKE 'is_common'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE subjects ADD COLUMN is_common TINYINT DEFAULT 0")
                conn.commit()
            cursor.execute("SHOW COLUMNS FROM subjects LIKE 'is_lab'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE subjects ADD COLUMN is_lab TINYINT DEFAULT 0")
                conn.commit()
        else:
            cursor.execute("PRAGMA table_info(subjects)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'stream' not in columns:
                cursor.execute("ALTER TABLE subjects ADD COLUMN stream TEXT")
                conn.commit()
            if 'is_common' not in columns:
                cursor.execute("ALTER TABLE subjects ADD COLUMN is_common INTEGER DEFAULT 0")
                conn.commit()
            if 'is_lab' not in columns:
                cursor.execute("ALTER TABLE subjects ADD COLUMN is_lab INTEGER DEFAULT 0")
                conn.commit()
    except Exception as e:
        print(f"Error adding columns: {e}")

    # Create resources table
    if mysql_enabled():
        cursor.execute('''
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
            )
        ''')
    else:
        cursor.execute('''
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
            )
        ''')

    # Add cloudinary_public_id column if it doesn't exist (for existing databases)
    try:
        if mysql_enabled():
            cursor.execute("SHOW COLUMNS FROM resources LIKE 'cloudinary_public_id'")
            if not cursor.fetchone():
                cursor.execute('ALTER TABLE resources ADD COLUMN cloudinary_public_id TEXT')
                conn.commit()
        else:
            cursor.execute('ALTER TABLE resources ADD COLUMN cloudinary_public_id TEXT')
            conn.commit()
    except Exception:
        # Column already exists, that's fine
        pass

    # Create notes compatibility table. StudyNova stores note files in resources;
    # this table keeps a one-to-one note record for reporting and legacy tooling.
    create_notes_table(cursor)

    # Create contact_messages table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'unread',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'unread',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    # Create user_downloads table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_downloads (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                resource_id INT NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            )
        ''')

    # Create saved_notes table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_notes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                resource_id INT NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                UNIQUE KEY (user_id, resource_id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                UNIQUE(user_id, resource_id)
            )
        ''')

    # Create viewed_notes table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viewed_notes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                resource_id INT NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viewed_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_id INTEGER NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            )
        ''')

    # Create notifications table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) NOT NULL,
                is_read TINYINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

    # Create feedback table for contact form submissions and admin review
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                status VARCHAR(50) DEFAULT 'unread',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'unread',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    # Phase 4: Competitive Exams Tables
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_categories (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_topics (
                id INT PRIMARY KEY AUTO_INCREMENT,
                exam_category_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_category_id) REFERENCES exam_categories(id)
            )
        ''')
        cursor.execute('''
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
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_category_id) REFERENCES exam_categories(id)
            )
        ''')
        cursor.execute('''
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
            )
        ''')

    # Phase 5: School Notes Tables
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_classes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_subjects (
                id INT PRIMARY KEY AUTO_INCREMENT,
                school_class_id INT NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_class_id) REFERENCES school_classes(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_chapters (
                id INT PRIMARY KEY AUTO_INCREMENT,
                school_subject_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                chapter_number INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_subject_id) REFERENCES school_subjects(id)
            )
        ''')
        cursor.execute('''
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
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_class_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_class_id) REFERENCES school_classes(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS school_chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                school_subject_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                chapter_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (school_subject_id) REFERENCES school_subjects(id)
            )
        ''')
        cursor.execute('''
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
            )
        ''')

    # Insert default exam categories if they don't exist
    exam_cats = [
        ("KPSC", "Karnataka Public Service Commission"),
        ("SSC", "Staff Selection Commission"),
        ("RRB", "Railway Recruitment Board"),
        ("Banking", "Banking Exams (IBPS, SBI, etc.)"),
        ("Karnataka GK", "Karnataka General Knowledge"),
        ("Current Affairs", "Current Affairs and News")
    ]
    placeholder = get_placeholder()
    for cat_name, cat_desc in exam_cats:
        check_query = f"SELECT id FROM exam_categories WHERE name = {placeholder}"
        cursor.execute(check_query, (cat_name,))
        if not cursor.fetchone():
            insert_query = f"INSERT INTO exam_categories (name, description) VALUES ({placeholder}, {placeholder})"
            cursor.execute(insert_query, (cat_name, cat_desc))

    # Insert default school classes if they don't exist
    school_classes = [
        ("6th Standard", "Class 6"),
        ("7th Standard", "Class 7"),
        ("8th Standard", "Class 8"),
        ("9th Standard", "Class 9"),
        ("10th Standard", "Class 10")
    ]
    for class_name, class_desc in school_classes:
        check_query = f"SELECT id FROM school_classes WHERE name = {placeholder}"
        cursor.execute(check_query, (class_name,))
        if not cursor.fetchone():
            insert_query = f"INSERT INTO school_classes (name, description) VALUES ({placeholder}, {placeholder})"
            cursor.execute(insert_query, (class_name, class_desc))
            # Get last inserted id
            if mysql_enabled():
                new_class_id = cursor.lastrowid
            else:
                new_class_id = cursor.lastrowid
            # Insert default subjects for each class
            for subj_name in ("Science", "Social Science"):
                insert_subj_query = f"INSERT INTO school_subjects (school_class_id, name) VALUES ({placeholder}, {placeholder})"
                cursor.execute(insert_subj_query, (new_class_id, subj_name))

    # Insert default schemes
    placeholder = get_placeholder()
    cursor.execute("SELECT COUNT(*) FROM schemes")
    if cursor.fetchone()[0] == 0:
        cursor.execute(f"INSERT INTO schemes (name, description) VALUES ({placeholder}, {placeholder})",
                      ('2022 Scheme', 'VTU 2022 Scheme for Engineering'))
        cursor.execute(f"INSERT INTO schemes (name, description) VALUES ({placeholder}, {placeholder})",
                      ('2025 Scheme', 'VTU 2025 Scheme for Engineering'))
        print("Default schemes created!")

    # Insert default branches
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
            cursor.execute(f"INSERT INTO branches (name, code) VALUES ({placeholder}, {placeholder})", (name, code))
        print("Default branches created!")

    # Insert default cycles
    cursor.execute("SELECT COUNT(*) FROM cycles")
    if cursor.fetchone()[0] == 0:
        cursor.execute(f"INSERT INTO cycles (name, code) VALUES ({placeholder}, {placeholder})", ('P Cycle', 'P_CYCLE'))
        cursor.execute(f"INSERT INTO cycles (name, code) VALUES ({placeholder}, {placeholder})", ('C Cycle', 'C_CYCLE'))
        print("Default cycles created!")

    # Insert semesters for 2022 Scheme
    if mysql_enabled():
        cursor.execute('''SELECT COUNT(*) FROM semesters WHERE scheme_id =
                         (SELECT id FROM schemes WHERE name = '2022 Scheme')''')
    else:
        cursor.execute('''SELECT COUNT(*) FROM semesters WHERE scheme_id =
                         (SELECT id FROM schemes WHERE name = '2022 Scheme')''')
    if cursor.fetchone()[0] == 0:
        if mysql_enabled():
            cursor.execute("SELECT id FROM schemes WHERE name = '2022 Scheme'")
        else:
            cursor.execute("SELECT id FROM schemes WHERE name = '2022 Scheme'")
        scheme_id = cursor.fetchone()[0]
        semesters_2022 = [
            (1, '1st Semester'),
            (2, '2nd Semester'),
            (3, '3rd Semester'),
            (4, '4th Semester'),
            (5, '5th Semester'),
            (6, '6th Semester'),
            (7, '7th Semester')
        ]
        for sem_num, sem_name in semesters_2022:
            cursor.execute(f'''INSERT INTO semesters (scheme_id, semester_number, name)
                            VALUES ({placeholder}, {placeholder}, {placeholder})''', (scheme_id, sem_num, sem_name))
        print("2022 Scheme semesters created!")

    # Insert semesters for 2025 Scheme
    if mysql_enabled():
        cursor.execute('''SELECT COUNT(*) FROM semesters WHERE scheme_id =
                         (SELECT id FROM schemes WHERE name = '2025 Scheme')''')
    else:
        cursor.execute('''SELECT COUNT(*) FROM semesters WHERE scheme_id =
                         (SELECT id FROM schemes WHERE name = '2025 Scheme')''')
    if cursor.fetchone()[0] == 0:
        if mysql_enabled():
            cursor.execute("SELECT id FROM schemes WHERE name = '2025 Scheme'")
        else:
            cursor.execute("SELECT id FROM schemes WHERE name = '2025 Scheme'")
        scheme_id = cursor.fetchone()[0]
        semesters_2025 = [
            (1, '1st Semester'),
            (2, '2nd Semester'),
            (3, '3rd Semester'),
            (4, '4th Semester'),
            (5, '5th Semester'),
            (6, '6th Semester'),
            (7, '7th Semester')
        ]
        for sem_num, sem_name in semesters_2025:
            cursor.execute(f'''INSERT INTO semesters (scheme_id, semester_number, name)
                             VALUES ({placeholder}, {placeholder}, {placeholder})''', (scheme_id, sem_num, sem_name))
        print("2025 Scheme semesters created!")

    # Insert VTU 2025 default subjects
    if mysql_enabled():
        cursor.execute("SELECT id FROM schemes WHERE name = '2025 Scheme'")
    else:
        cursor.execute("SELECT id FROM schemes WHERE name = '2025 Scheme'")
    scheme_row = cursor.fetchone()
    scheme_2025_id = scheme_row[0] if scheme_row else None

    if mysql_enabled():
        cursor.execute("SELECT id FROM semesters WHERE scheme_id = %s AND semester_number = 1", (scheme_2025_id,))
    else:
        cursor.execute("SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = 1", (scheme_2025_id,))
    sem1_row = cursor.fetchone()
    sem_1_id = sem1_row[0] if sem1_row else None

    if mysql_enabled():
        cursor.execute("SELECT id FROM semesters WHERE scheme_id = %s AND semester_number = 2", (scheme_2025_id,))
    else:
        cursor.execute("SELECT id FROM semesters WHERE scheme_id = ? AND semester_number = 2", (scheme_2025_id,))
    sem2_row = cursor.fetchone()
    sem_2_id = sem2_row[0] if sem2_row else None

    if mysql_enabled():
        cursor.execute("SELECT id FROM cycles WHERE name = 'P Cycle'")
    else:
        cursor.execute("SELECT id FROM cycles WHERE name = 'P Cycle'")
    p_cycle_row = cursor.fetchone()
    p_cycle_id = p_cycle_row[0] if p_cycle_row else None

    if mysql_enabled():
        cursor.execute("SELECT id FROM cycles WHERE name = 'C Cycle'")
    else:
        cursor.execute("SELECT id FROM cycles WHERE name = 'C Cycle'")
    c_cycle_row = cursor.fetchone()
    c_cycle_id = c_cycle_row[0] if c_cycle_row else None

    if scheme_2025_id and sem_1_id and sem_2_id and p_cycle_id and c_cycle_id:
        # Check if subjects already exist for 2025 scheme
        if mysql_enabled():
            cursor.execute("SELECT COUNT(*) FROM subjects WHERE scheme_id = %s", (scheme_2025_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM subjects WHERE scheme_id = ?", (scheme_2025_id,))
        if cursor.fetchone()[0] == 0:
            # 1st Semester P Cycle Computer Science Stream
            vtu_2025_subjects = [
                # 1st Semester
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BMATS101 - Applied Mathematics-I', '1BMATS101', 4, 'computer_science', 0),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BPHYS102 - Quantum Physics and Applications', '1BPHYS102', 3, 'computer_science', 0),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BCEDS103 - Computer-Aided Engineering Drawing', '1BCEDS103', 3, 'computer_science', 0),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BESC104E - Essentials of Information Technology', '1BESC104E', 3, 'computer_science', 0),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BEIT105 - Programming in C', '1BEIT105', 4, 'computer_science', 0),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BSKS106 - Soft Skills', '1BSKS106', 2, None, 1),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BPOPL107 - C Programming Lab', '1BPOPL107', 2, 'computer_science', 0),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BIDTL158 - Innovation and Design Thinking Lab', '1BIDTL158', 2, None, 1),
                (scheme_2025_id, sem_1_id, None, p_cycle_id, '1BKSK109 - Samskrutika Kannada', '1BKSK109', 2, None, 1),
                # 2nd Semester C Cycle Computer Science Stream
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BMATS201 - Numerical Methods', '1BMATS201', 4, 'computer_science', 0),
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BCHES202 - Applied Chemistry for Smart Systems', '1BCHES202', 3, 'computer_science', 0),
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BAIA203 - Introduction to AI and Applications', '1BAIA203', 3, None, 1),
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BESC204E - Essentials of Information Technology', '1BESC204E', 3, 'computer_science', 0),
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BPLC205B - Python Programming', '1BPLC205B', 4, 'computer_science', 0),
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BENG206 - Communication Skills', '1BENG206', 2, None, 1),
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BIC0207 - Indian Constitution & Engineering Ethics', '1BIC0207', 2, None, 1),
                (scheme_2025_id, sem_2_id, None, c_cycle_id, '1BPRJ258 - Interdisciplinary Project-Based Learning', '1BPRJ258', 2, None, 1)
            ]
            for s in vtu_2025_subjects:
                insert_subject = f'''
                    INSERT INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                '''
                cursor.execute(insert_subject, s)
            print("VTU 2025 default subjects created!")

    # Insert default subjects if not exists
    cursor.execute("SELECT COUNT(*) FROM subjects")
    if cursor.fetchone()[0] == 0:
        # Get scheme using existing cursor
        cursor.execute("SELECT * FROM schemes LIMIT 1")
        scheme_row = cursor.fetchone()
        scheme = None
        if scheme_row:
            if mysql_enabled():
                scheme = dict(scheme_row)
            else:
                scheme = scheme_row
        # Get semester using existing cursor
        cursor.execute("SELECT * FROM semesters LIMIT 1")
        semester_row = cursor.fetchone()
        semester = None
        if semester_row:
            if mysql_enabled():
                semester = dict(semester_row)
            else:
                semester = semester_row
        if scheme and semester:
            subjects = [
                (scheme['id'], semester['id'], None, None, 'Engineering Mathematics', 'MAT101', 4),
                (scheme['id'], semester['id'], None, None, 'Basic Electronics', 'ECE101', 3),
                (scheme['id'], semester['id'], None, None, 'Programming in C', 'CSE101', 4),
            ]
            for s in subjects:
                insert_subject = f'''
                    INSERT INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                '''
                cursor.execute(insert_subject, s)
            print("Default subjects created!")

    # Ensure every scheme/semester/branch has at least one subject
    ensure_default_academic_data(cursor)
    migrate_legacy_notes(cursor)

    # Add stars column to users table for contribution system
    try:
        if mysql_enabled():
            cursor.execute("SHOW COLUMNS FROM users LIKE 'stars'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN stars INT DEFAULT 0")
                conn.commit()
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'stars' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN stars INTEGER DEFAULT 0")
                conn.commit()
    except Exception as e:
        print(f"Error adding stars column: {e}")

    # Add achievement_level column to users table
    try:
        if mysql_enabled():
            cursor.execute("SHOW COLUMNS FROM users LIKE 'achievement_level'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD COLUMN achievement_level VARCHAR(50) DEFAULT 'Beginner'")
                conn.commit()
        else:
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'achievement_level' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN achievement_level TEXT DEFAULT 'Beginner'")
                conn.commit()
    except Exception as e:
        print(f"Error adding achievement_level column: {e}")

    # Create activity_logs table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT,
                admin_id INT,
                action VARCHAR(255) NOT NULL,
                details TEXT,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (admin_id) REFERENCES users(id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (admin_id) REFERENCES users(id)
            )
        ''')

    # Create report_notes table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_notes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                resource_id INT NOT NULL,
                reported_by INT NOT NULL,
                report_type VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                resolved_by INT,
                resolved_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (reported_by) REFERENCES users(id),
                FOREIGN KEY (resolved_by) REFERENCES users(id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                reported_by INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                resolved_by INTEGER,
                resolved_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (reported_by) REFERENCES users(id),
                FOREIGN KEY (resolved_by) REFERENCES users(id)
            )
        ''')

    # Create syllabus table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS syllabus (
                id INT PRIMARY KEY AUTO_INCREMENT,
                subject_id INT NOT NULL,
                file_url TEXT NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                cloudinary_public_id TEXT,
                course_description TEXT,
                course_outcomes TEXT,
                module1 TEXT,
                module2 TEXT,
                module3 TEXT,
                module4 TEXT,
                module5 TEXT,
                text_books TEXT,
                reference_books TEXT,
                uploaded_by INT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS syllabus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                file_url TEXT NOT NULL,
                file_type TEXT NOT NULL,
                cloudinary_public_id TEXT,
                course_description TEXT,
                course_outcomes TEXT,
                module1 TEXT,
                module2 TEXT,
                module3 TEXT,
                module4 TEXT,
                module5 TEXT,
                text_books TEXT,
                reference_books TEXT,
                uploaded_by INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        ''')

    # Create password_reset_tokens table
    if mysql_enabled():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used TINYINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
    else:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

    # Create single admin user if not exists
    placeholder = get_placeholder()
    cursor.execute(f"SELECT * FROM users WHERE role = {placeholder}", ('admin',))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        admin_email = os.environ.get('STUDYNOVA_ADMIN_EMAIL')
        admin_password = os.environ.get('STUDYNOVA_ADMIN_PASSWORD')
        admin_name = os.environ.get('STUDYNOVA_ADMIN_NAME', 'StudyNova Admin')
        if admin_email and admin_password:
            hashed_admin_password = generate_password_hash(admin_password)
            cursor.execute(f'''
                INSERT INTO users (username, email, password, role, phone, college, branch, semester, scheme)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (admin_name, admin_email,
                  hashed_admin_password, 'admin', '', '', 'Computer Science & Engineering', '3rd Semester', '2022 Scheme'))
            print(f"Admin user created from STUDYNOVA_ADMIN_EMAIL: {admin_email}")
        else:
            print("No admin user exists. Set STUDYNOVA_ADMIN_EMAIL and STUDYNOVA_ADMIN_PASSWORD before first production startup.")

    # Create demo user if not exists
    cursor.execute(f"SELECT * FROM users WHERE email = {placeholder}", ('demo@studynova.com',))
    demo_user = cursor.fetchone()

    if not demo_user and os.environ.get('STUDYNOVA_CREATE_DEMO_USER') == '1':
        hashed_demo_password = generate_password_hash('studynova123')
        cursor.execute(f'''
            INSERT INTO users (username, email, password, role, phone, college, branch, semester, scheme)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', ('Demo Student', 'demo@studynova.com', hashed_demo_password, 'user',
              '9876543210', 'Demo College', 'Computer Science & Engineering', '2nd Semester', '2022 Scheme'))
        print("Demo user created from local development seed settings.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully with academic structure!")


def table_exists(cursor, table_name):
    if mysql_enabled():
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        return cursor.fetchone() is not None

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None


def create_notes_table(cursor):
    if mysql_enabled():
        cursor.execute('''
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
            )
        ''')
    else:
        cursor.execute('''
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
            )
        ''')


def get_or_create_general_notes_subject(cursor):
    placeholder = get_placeholder()
    query = f"SELECT id FROM subjects WHERE code = {placeholder} LIMIT 1"
    row = execute_query(query, ('GENERAL_NOTES',), fetchone=True)
    if row:
        return row['id']

    scheme = execute_query("SELECT id FROM schemes ORDER BY id LIMIT 1", fetchone=True)
    semester = None
    if scheme:
        semester = execute_query(
            "SELECT id FROM semesters WHERE scheme_id = %s ORDER BY semester_number LIMIT 1" if mysql_enabled() else "SELECT id FROM semesters WHERE scheme_id = ? ORDER BY semester_number LIMIT 1",
            (scheme['id'],),
            fetchone=True
        )

    if not scheme or not semester:
        return None

    insert_query = f"INSERT INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common) VALUES ({placeholder}, {placeholder}, NULL, NULL, {placeholder}, {placeholder}, 0, NULL, 1)"
    execute_query(insert_query, (
        scheme['id'],
        semester['id'],
        'General StudyNova Notes',
        'GENERAL_NOTES'
    ), commit=True)

    return execute_query(query, ('GENERAL_NOTES',), fetchone=True)['id']


def migrate_legacy_notes(cursor):
    if not table_exists(cursor, 'notes'):
        return

    if mysql_enabled():
        cursor.execute("SHOW COLUMNS FROM notes")
        note_columns = [col[0] for col in cursor.fetchall()]
    else:
        cursor.execute("PRAGMA table_info(notes)")
        note_columns = [col[1] for col in cursor.fetchall()]

    if 'filename' not in note_columns or 'category' not in note_columns:
        return

    print("Legacy notes table detected: starting migration into resources...")

    resources_count = execute_query("SELECT COUNT(*) as count FROM resources", fetchone=True)
    existing_resources = resources_count['count']
    if existing_resources > 0:
        print("Resources table already contains data; converting legacy notes table only.")
        legacy_table_name = "notes_legacy"
        suffix = 1
        while table_exists(cursor, legacy_table_name):
            suffix += 1
            legacy_table_name = f"notes_legacy_{suffix}"
        if mysql_enabled():
            cursor.execute(f"RENAME TABLE notes TO {legacy_table_name}")
        else:
            cursor.execute(f"ALTER TABLE notes RENAME TO {legacy_table_name}")
        create_notes_table(cursor)
        cursor.connection.commit()
        sync_sql = insert_ignore_sql('notes', ['resource_id', 'subject_id', 'title', 'file_url', 'file_type'])
        resources = execute_query("SELECT id, subject_id, title, file_url, file_type FROM resources", fetchall=True)
        for resource in resources:
            execute_query(sync_sql, (resource['id'], resource['subject_id'], resource['title'], resource['file_url'], resource['file_type']), commit=True)
        return

    general_subject_id = get_or_create_general_notes_subject(cursor)
    if not general_subject_id:
        print("Unable to create general notes subject for legacy migration.")
        return

    if mysql_enabled():
        insert_sql = '''
            INSERT INTO resources (subject_id, title, description, file_url, file_type, resource_type, module_number, uploaded_by, is_approved, upload_date, view_count, download_count)
            SELECT %s, title, '', filename, LOWER(SUBSTRING_INDEX(filename, '.', -1)), category, NULL, NULL, 1, upload_date, 0, 0
            FROM notes
        '''
    else:
        insert_sql = '''
            INSERT INTO resources (subject_id, title, description, file_url, file_type, resource_type, module_number, uploaded_by, is_approved, upload_date, view_count, download_count)
            SELECT ?, title, '', filename,
                   LOWER(CASE WHEN instr(filename, '.') > 0 THEN substr(filename, instr(filename, '.') + 1) ELSE 'pdf' END),
                   category, NULL, NULL, 1, upload_date, 0, 0
            FROM notes
        '''
    execute_query(insert_sql, (general_subject_id,), commit=True)
    legacy_table_name = "notes_legacy"
    suffix = 1
    while table_exists(cursor, legacy_table_name):
        suffix += 1
        legacy_table_name = f"notes_legacy_{suffix}"

    if mysql_enabled():
        cursor.execute(f"RENAME TABLE notes TO {legacy_table_name}")
    else:
        cursor.execute(f"ALTER TABLE notes RENAME TO {legacy_table_name}")
    create_notes_table(cursor)
    cursor.connection.commit()

    sync_sql = insert_ignore_sql('notes', ['resource_id', 'subject_id', 'title', 'file_url', 'file_type'])
    resources = execute_query("SELECT id, subject_id, title, file_url, file_type FROM resources", fetchall=True)
    for resource in resources:
        execute_query(sync_sql, (resource['id'], resource['subject_id'], resource['title'], resource['file_url'], resource['file_type']), commit=True)

    print(f"Legacy note rows migrated into resources; old table renamed to {legacy_table_name}.")


def get_file_icon(extension):
    icons = {
        'pdf': 'fas fa-file-pdf text-danger',
        'ppt': 'fas fa-file-powerpoint text-warning',
        'pptx': 'fas fa-file-powerpoint text-warning',
        'doc': 'fas fa-file-word text-primary',
        'docx': 'fas fa-file-word text-primary',
        'zip': 'fas fa-file-archive text-secondary',
        'jpg': 'fas fa-file-image text-success',
        'jpeg': 'fas fa-file-image text-success',
        'png': 'fas fa-file-image text-success'
    }
    return icons.get(extension.lower(), 'fas fa-file text-muted')


def get_resource_type_label(resource_type):
    labels = {
        'module1': 'Module 1 Notes',
        'module2': 'Module 2 Notes',
        'module3': 'Module 3 Notes',
        'module4': 'Module 4 Notes',
        'module5': 'Module 5 Notes',
        'important_questions': 'Important Questions',
        'pyq': 'Question Papers',
        'solutions': 'Question Paper Solutions',
        'passing_package': 'Passing Package',
        'lab_manual': 'Lab Manual'
    }
    return labels.get(resource_type, resource_type)

def get_branch_stream(branch):
    if not branch:
        return None
    branch_name = branch.get('name', '').lower() if isinstance(branch, dict) else str(branch).lower()
    if 'civil' in branch_name:
        return 'civil'
    elif 'mechanical' in branch_name:
        return 'mechanical'
    elif 'electrical' in branch_name and 'electronics' not in branch_name:
        return 'electrical'
    elif 'electronics' in branch_name:
        return 'electronics'
    elif 'cse' in branch_name or 'computer' in branch_name or 'ise' in branch_name or 'information' in branch_name:
        return 'computer_science'
    return None


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_email'):
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_email'):
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login', next=request.path))

        # Get user role from database
        user = get_user_by_email(session['user_email'])
        if not user or user.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('home'))

        return view(*args, **kwargs)
    return wrapped_view


# Forward a contact-form submission to the configured admin email.
# Sends through Gmail SMTP using credentials supplied via environment variables.
#   MAIL_USERNAME   - Gmail address used as the sender (e.g. studynovaofficial@gmail.com)
#   MAIL_PASSWORD   - Gmail App Password for the sender account
def get_email_template(subject, content, recipient_name="User"):
    """Generate professional HTML email template"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Poppins', Arial, sans-serif; background-color: #f4f4f4;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f4f4f4;">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #4b0082 0%, #6a5acd 100%); padding: 30px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">StudyNova</h1>
                                <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Your Ultimate Academic Resource Platform</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                {content}
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 20px 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                                <p style="margin: 0; font-size: 12px; color: #666666;">
                                    © 2025 StudyNova. All rights reserved.
                                </p>
                                <p style="margin: 5px 0 0 0; font-size: 11px; color: #999999;">
                                    This is an automated email. Please do not reply to this message.
                                </p>
                                <p style="margin: 5px 0 0 0; font-size: 11px; color: #999999;">
                                    Contact us: studynovaofficial@gmail.com
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html


def send_email(to_email, subject, body, is_html=False):
    """Generic email sending function using Gmail SMTP"""
    smtp_host = os.environ.get('MAIL_SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('MAIL_SMTP_PORT', 587))
    mail_username = os.environ.get('MAIL_USERNAME', 'studynovaofficial@gmail.com')
    mail_password = os.environ.get('MAIL_PASSWORD')

    if not mail_password:
        print("[email] MAIL_PASSWORD not configured, skipping email send")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = mail_username
        msg['To'] = to_email
        msg['Subject'] = subject

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_username, [to_email], msg.as_string())
        return True
    except Exception as exc:
        print(f"[email] Failed to send email: {exc}")
        return False


def send_admin_notification(name, sender_email, subject, message):
    """Forward contact form submission to admin email"""
    content = f"""
        <h2>New Contact Form Submission</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;"><strong>From:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">{name} <{sender_email}></td>
            </tr>
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;"><strong>Subject:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">{subject}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;"><strong>Message:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">{message}</td>
            </tr>
        </table>
    """
    html_body = get_email_template(f"[StudyNova Contact] {subject}", content)
    return send_email(ADMIN_NOTIFICATION_EMAIL, f"[StudyNova Contact] {subject}", html_body, is_html=True)


def send_welcome_email(user_email, username):
    """Send welcome email to newly registered user"""
    subject = "Welcome to StudyNova!"
    content = f"""
        <p>Dear <strong>{username}</strong>,</p>
        <p>Welcome to <strong>StudyNova</strong> - Your Ultimate Academic Resource Platform!</p>
        <p>We're excited to have you on board. StudyNova provides:</p>
        <ul>
            <li>Quality notes and study materials</li>
            <li>Syllabus and question papers</li>
            <li>Placement preparation resources</li>
            <li>And much more!</li>
        </ul>
        <p>Start exploring now: <a href="http://studynova.com" style="color: #4b0082;">StudyNova</a></p>
        <p>Best regards,<br><strong>StudyNova Team</strong></p>
    """
    html_body = get_email_template(subject, content)
    return send_email(user_email, subject, html_body, is_html=True)


def send_password_reset_email(user_email, username, reset_token):
    """Send password reset email"""
    reset_url = f"http://studynova.com/reset-password?token={reset_token}"
    subject = "StudyNova - Password Reset Request"
    content = f"""
        <p>Dear <strong>{username}</strong>,</p>
        <p>You have requested to reset your password. Click the button below to reset it:</p>
        <p style="text-align: center;">
            <a href="{reset_url}" style="background: linear-gradient(135deg, #4b0082, #6a5acd); color: #fff; padding: 12px 30px; border-radius: 30px; text-decoration: none; font-weight: 600; display: inline-block;">Reset Password</a>
        </p>
        <p>This link will expire in <strong>1 hour</strong>.</p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Best regards,<br><strong>StudyNova Team</strong></p>
    """
    html_body = get_email_template(subject, content)
    return send_email(user_email, subject, html_body, is_html=True)


def send_note_approved_email(user_email, username, note_title):
    """Send notification when a note is approved"""
    subject = "StudyNova - Your Note Has Been Approved!"
    content = f"""
        <p>Dear <strong>{username}</strong>,</p>
        <p>🎉 Great news! Your note <strong>"{note_title}"</strong> has been approved and is now visible to all students.</p>
        <p>Thank you for contributing to the StudyNova community!</p>
        <p>Best regards,<br><strong>StudyNova Team</strong></p>
    """
    html_body = get_email_template(subject, content)
    return send_email(user_email, subject, html_body, is_html=True)


def send_note_rejected_email(user_email, username, note_title, reason=""):
    """Send notification when a note is rejected"""
    subject = "StudyNova - Note Submission Update"
    reason_html = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
    content = f"""
        <p>Dear <strong>{username}</strong>,</p>
        <p>Your note <strong>"{note_title}"</strong> was not approved.</p>
        {reason_html}
        <p>Please review our guidelines and try again.</p>
        <p>Best regards,<br><strong>StudyNova Team</strong></p>
    """
    html_body = get_email_template(subject, content)
    return send_email(user_email, subject, html_body, is_html=True)


def send_feedback_notification_email(feedback_id, name, email, subject_fb, message):
    """Send notification to user when feedback is received"""
    subject = f"[StudyNova] Feedback Received: {subject_fb}"
    content = f"""
        <p>Dear <strong>{name}</strong>,</p>
        <p>Thank you for your feedback! We have received your message:</p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;"><strong>Subject:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">{subject_fb}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;"><strong>Message:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">{message}</td>
            </tr>
        </table>
        <p>We will get back to you soon.</p>
        <p>Feedback ID: {feedback_id}</p>
        <p>Best regards,<br><strong>StudyNova Team</strong></p>
    """
    html_body = get_email_template(subject, content)
    return send_email(email, subject, html_body, is_html=True)


def send_contact_notification_email(contact_id, name, email, subject_ct, message):
    """Send notification to user when contact form is submitted"""
    subject = f"[StudyNova] Contact Form Received: {subject_ct}"
    content = f"""
        <p>Dear <strong>{name}</strong>,</p>
        <p>Thank you for contacting us! We have received your message:</p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;"><strong>Subject:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">{subject_ct}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;"><strong>Message:</strong></td>
                <td style="padding: 10px 0; border-bottom: 1px solid #e0e0e0;">{message}</td>
            </tr>
        </table>
        <p>We will get back to you soon.</p>
        <p>Contact ID: {contact_id}</p>
        <p>Best regards,<br><strong>StudyNova Team</strong></p>
    """
    html_body = get_email_template(subject, content)
    return send_email(email, subject, html_body, is_html=True)


def log_activity(admin_id=None, user_id=None, action="", details="", ip_address=None):
    """Log admin/user activity"""
    try:
        placeholder = get_placeholder()
        query = f'''
            INSERT INTO activity_logs (admin_id, user_id, action, details, ip_address)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        execute_query(query, (admin_id, user_id, action, details, ip_address), commit=True)
    except Exception as e:
        print(f"Error logging activity: {e}")


def get_all_resources():
    placeholder = get_placeholder()
    query = f'''
        SELECT r.*, s.name as subject_name, u.username as uploader_name
        FROM resources r
        LEFT JOIN subjects s ON r.subject_id = s.id
        LEFT JOIN users u ON r.uploaded_by = u.id
        WHERE r.is_approved = 1
        ORDER BY r.upload_date DESC
    '''
    return execute_query(query, fetchall=True)


def get_stats():
    placeholder = get_placeholder()

    def safe_get_count(query, params=()):
        result = execute_query(query, params, fetchone=True)
        if result and 'count' in result:
            return result['count'] or 0
        return 0

    total_users = safe_get_count("SELECT COUNT(*) as count FROM users")
    total_notes = safe_get_count("SELECT COUNT(*) as count FROM resources WHERE is_approved = 1")
    total_downloads = safe_get_count("SELECT SUM(download_count) as count FROM resources")
    total_views = safe_get_count("SELECT SUM(view_count) as count FROM resources")

    # Get admin count and regular users count
    admin_count = safe_get_count(f"SELECT COUNT(*) as count FROM users WHERE role = {placeholder}", ('admin',))
    regular_users = total_users - admin_count

    # Get messages count
    total_messages = safe_get_count("SELECT COUNT(*) as count FROM contact_messages")
    unread_messages = safe_get_count(f"SELECT COUNT(*) as count FROM contact_messages WHERE status = {placeholder}", ('unread',))

    # Get pending/approved/rejected notes count
    pending_notes = safe_get_count("SELECT COUNT(*) as count FROM resources WHERE is_approved = 0")
    approved_notes = safe_get_count("SELECT COUNT(*) as count FROM resources WHERE is_approved = 1")
    rejected_notes = safe_get_count("SELECT COUNT(*) as count FROM resources WHERE is_approved = -1") if mysql_enabled() else safe_get_count("SELECT COUNT(*) as count FROM resources WHERE is_approved = 2")

    # Get total subjects, branches, syllabus files
    total_subjects = safe_get_count("SELECT COUNT(*) as count FROM subjects")
    total_branches = safe_get_count("SELECT COUNT(*) as count FROM branches")
    total_syllabus = safe_get_count("SELECT COUNT(*) as count FROM syllabus")

    # Get total stars awarded
    total_stars = safe_get_count("SELECT SUM(stars) as count FROM users")

    return {
        'total_users': total_users,
        'total_notes': total_notes,
        'downloads': total_downloads,
        'total_views': total_views,
        'admin_users': admin_count,
        'regular_users': regular_users,
        'total_resources': total_notes,
        'pending_resources': pending_notes,
        'approved_resources': approved_notes,
        'rejected_resources': rejected_notes,
        'total_messages': total_messages,
        'unread_messages': unread_messages,
        'total_subjects': total_subjects,
        'total_branches': total_branches,
        'total_syllabus': total_syllabus,
        'total_stars': total_stars
    }


def get_schemes():
    return execute_query("SELECT * FROM schemes ORDER BY name", fetchall=True)


def get_semesters():
    return execute_query("SELECT * FROM semesters ORDER BY scheme_id, semester_number", fetchall=True)


def get_branches():
    return execute_query("SELECT * FROM branches ORDER BY name", fetchall=True)


def get_cycles():
    return execute_query("SELECT * FROM cycles ORDER BY name", fetchall=True)


def get_subjects():
    query = f'''
        SELECT s.*, sch.name as scheme_name, sem.name as semester_name
        FROM subjects s
        LEFT JOIN schemes sch ON s.scheme_id = sch.id
        LEFT JOIN semesters sem ON s.semester_id = sem.id
        ORDER BY s.name
    '''
    return execute_query(query, fetchall=True)


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


CYBER_SECURITY_2022_SUBJECTS = {
    3: [
        ('BCS301', 'Mathematics for Computer Science'),
        ('BCS302', 'Digital Design & Computer Organization'),
        ('BCS303', 'Operating Systems'),
        ('BCS304', 'Data Structures and Applications'),
        ('BCSL305', 'Data Structures Lab'),
        ('BCY306A', 'Fundamentals of Cyber Security'),
        ('BSCK307', 'Social Connect and Responsibility'),
        ('BCYL358A', 'Linux System Administration'),
        ('BCYL358B', 'Python for Cyber Security'),
        ('BCYL358C', 'Network Administration'),
        ('BCYL358D', 'Cyber Security Essentials'),
    ],
    4: [
        ('BCS401', 'Analysis & Design of Algorithms'),
        ('BCY402', 'Elements of Cyber Security'),
        ('BCS403', 'Database Management Systems'),
        ('BCSL404', 'Analysis & Design of Algorithms Lab'),
        ('BCY405A', 'Discrete Mathematical Structures'),
        ('BCY405B', 'Graph Theory'),
        ('BCY405C', 'Optimization Techniques'),
        ('BCY405D', 'Linear Algebra'),
        ('BCY456A', 'Green IT and Sustainability'),
        ('BCY456B', 'Capacity Planning for IT'),
        ('BCY456C', 'UI/UX'),
        ('BCYL456D', 'Technical Writing using LaTeX'),
        ('BBOC407', 'Biology for Computer Engineers'),
        ('BUHK408', 'Universal Human Values'),
    ],
    5: [
        ('BCS501', 'Software Engineering & Project Management'),
        ('BCS502', 'Computer Networks'),
        ('BCS503', 'Theory of Computation'),
        ('BCYL504', 'Advanced Cyber Security Lab'),
        ('BCY515A', 'Wireless and Mobile Device Security'),
        ('BCY515B', 'Ethical Hacking'),
        ('BCY515C', 'Digital Forensics'),
        ('BCY515D', 'Web Application Security'),
        ('BCY586', 'Mini Project'),
        ('BRMK557', 'Research Methodology and IPR'),
        ('BCS508', 'Environmental Studies and E-Waste Management'),
    ],
    6: [
        ('BCO601', 'Microcontrollers & Embedded Systems'),
        ('BCY602', 'Cryptography & Network Security'),
        ('BCY613A', 'Blockchain Technology'),
        ('BCY613B', 'Cyber Threat Intelligence'),
        ('BCY613C', 'Cloud Security'),
        ('BCY613D', 'Malware Analysis'),
        ('BCS654A', 'Introduction to Data Structures'),
        ('BCS654B', 'Fundamentals of Operating Systems'),
        ('BIS654C', 'Mobile Application Development'),
        ('BAI654D', 'Introduction to Artificial Intelligence'),
        ('BCY685', 'Project Phase-I'),
        ('BCYL606', 'Network Security Lab'),
        ('BCYL657A', 'Industrial Cyber Security'),
        ('BCSL657B', 'React'),
        ('BAIL657C', 'Generative AI'),
        ('BCSL657D', 'DevOps'),
        ('BIKS609', 'Indian Knowledge System'),
    ],
    7: [
        ('BCY701', 'Vulnerability Assessment & Penetration Testing'),
        ('BCY702', 'Ethical Hacking'),
        ('BIC703', 'Machine Learning'),
        ('BCY714A', 'Introduction to Cyber Forensics'),
        ('BCY714B', 'Software Defined Networks'),
        ('BCY714C', 'Cyber Policies and CERT-IN'),
        ('BCY714D', 'Cyber Security Management, Compliance and Governance'),
        ('BCY755A', 'Introduction to Cyber Security'),
        ('BCY755B', 'Information Security'),
        ('BCY755C', 'Network Security'),
        ('BCY786', 'Major Project Phase-II'),
    ],
}


def seed_2022_cyber_security_subjects(cursor):
    placeholder = get_placeholder()
    cursor.execute(f"SELECT id FROM schemes WHERE name = {placeholder}", ('2022 Scheme',))
    scheme_row = cursor.fetchone()
    cursor.execute(f"SELECT id FROM branches WHERE code = {placeholder}", ('CSE_CS',))
    branch_row = cursor.fetchone()
    if not scheme_row or not branch_row:
        return

    scheme_id = scheme_row[0]
    branch_id = branch_row[0]
    first_subject_by_semester = {}

    for semester_number, subjects in CYBER_SECURITY_2022_SUBJECTS.items():
        cursor.execute(
            f"SELECT id FROM semesters WHERE scheme_id = {placeholder} AND semester_number = {placeholder}",
            (scheme_id, semester_number)
        )
        semester_row = cursor.fetchone()
        if not semester_row:
            continue
        semester_id = semester_row[0]

        for index, (code, name) in enumerate(subjects):
            cursor.execute(f'''
                SELECT id FROM subjects
                WHERE scheme_id = {placeholder}
                  AND semester_id = {placeholder}
                  AND branch_id = {placeholder}
                  AND code = {placeholder}
            ''', (scheme_id, semester_id, branch_id, code))
            subject_row = cursor.fetchone()
            if subject_row:
                subject_id = subject_row[0]
                cursor.execute(
                    f"UPDATE subjects SET name = {placeholder}, stream = {placeholder}, is_common = 0 WHERE id = {placeholder}",
                    (name, 'computer_science', subject_id)
                )
            else:
                cursor.execute(f'''
                    INSERT INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
                    VALUES ({placeholder}, {placeholder}, {placeholder}, NULL, {placeholder}, {placeholder}, 4, {placeholder}, 0)
                ''', (scheme_id, semester_id, branch_id, name, code, 'computer_science'))
                subject_id = cursor.lastrowid

            if index == 0:
                first_subject_by_semester[semester_id] = subject_id

        generated_code = f"CSE_CS{semester_number:02d}01"
        target_subject_id = first_subject_by_semester.get(semester_id)
        if target_subject_id:
            cursor.execute(f'''
                SELECT id FROM subjects
                WHERE scheme_id = {placeholder}
                  AND semester_id = {placeholder}
                  AND branch_id = {placeholder}
                  AND code = {placeholder}
            ''', (scheme_id, semester_id, branch_id, generated_code))
            generated_row = cursor.fetchone()
            if generated_row:
                generated_subject_id = generated_row[0]
                cursor.execute(
                    f"UPDATE resources SET subject_id = {placeholder} WHERE subject_id = {placeholder}",
                    (target_subject_id, generated_subject_id)
                )
                cursor.execute(
                    f"UPDATE notes SET subject_id = {placeholder} WHERE subject_id = {placeholder}",
                    (target_subject_id, generated_subject_id)
                )
                cursor.execute(f"DELETE FROM subjects WHERE id = {placeholder}", (generated_subject_id,))


def ensure_default_academic_data(cursor):
    placeholder = get_placeholder()

    default_schemes = [
        ('2022 Scheme', 'VTU 2022 Scheme for Engineering'),
        ('2025 Scheme', 'VTU 2025 Scheme for Engineering')
    ]
    for name, description in default_schemes:
        cursor.execute(f"SELECT id FROM schemes WHERE name = {placeholder}", (name,))
        if not cursor.fetchone():
            cursor.execute(f"INSERT INTO schemes (name, description) VALUES ({placeholder}, {placeholder})", (name, description))

    default_branches = [
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
    for name, code in default_branches:
        cursor.execute(f"SELECT id FROM branches WHERE code = {placeholder}", (code,))
        if not cursor.fetchone():
            cursor.execute(f"INSERT INTO branches (name, code) VALUES ({placeholder}, {placeholder})", (name, code))

    default_cycles = [
        'P Cycle',
        'C Cycle'
    ]
    for name in default_cycles:
        cursor.execute(f"SELECT id FROM cycles WHERE name = {placeholder}", (name,))
        if not cursor.fetchone():
            cursor.execute(f"INSERT INTO cycles (name) VALUES ({placeholder})", (name,))

    # Ensure semesters for all schemes include semesters 1-8
    cursor.execute("SELECT id FROM schemes")
    scheme_rows = cursor.fetchall()
    for scheme_row in scheme_rows:
        scheme_id = scheme_row[0]
        for semester_number in range(1, 9):
            sem_name = f"{semester_number}{'st' if semester_number == 1 else 'nd' if semester_number == 2 else 'rd' if semester_number == 3 else 'th'} Semester"
            cursor.execute(f"SELECT id FROM semesters WHERE scheme_id = {placeholder} AND semester_number = {placeholder}", (scheme_id, semester_number))
            if not cursor.fetchone():
                cursor.execute(f"INSERT INTO semesters (scheme_id, semester_number, name) VALUES ({placeholder}, {placeholder}, {placeholder})", (scheme_id, semester_number, sem_name))

    cursor.execute("SELECT id, code, name FROM branches")
    branch_rows = cursor.fetchall()
    cursor.execute("SELECT id, scheme_id, semester_number FROM semesters")
    semester_rows = cursor.fetchall()
    cursor.execute("SELECT id FROM cycles WHERE name = 'P Cycle'")
    p_cycle_row = cursor.fetchone()
    p_cycle_id = p_cycle_row[0] if p_cycle_row else None
    cursor.execute("SELECT id FROM cycles WHERE name = 'C Cycle'")
    c_cycle_row = cursor.fetchone()
    c_cycle_id = c_cycle_row[0] if c_cycle_row else None

    for semester_row in semester_rows:
        semester_id = semester_row[0]
        scheme_id = semester_row[1]
        semester_number = semester_row[2]
        cycle_id = p_cycle_id if semester_number == 1 else c_cycle_id if semester_number == 2 else None

        for branch_row in branch_rows:
            branch_id = branch_row[0]
            branch_code = branch_row[1]
            branch_name = branch_row[2]

            cursor.execute(f"SELECT id FROM subjects WHERE scheme_id = {placeholder} AND semester_id = {placeholder} AND branch_id = {placeholder}", (scheme_id, semester_id, branch_id))
            if cursor.fetchone():
                continue

            stream = get_stream_for_branch(branch_code)
            subject_code = f"{branch_code}{semester_number:02d}01"
            subject_name = f"{branch_name} Semester {semester_number} Core"
            cursor.execute(f'''
                INSERT INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (scheme_id, semester_id, branch_id, cycle_id, subject_name, subject_code, 4, stream, 0))

    seed_2022_cyber_security_subjects(cursor)

    conn = cursor.connection
    conn.commit()


def get_most_downloaded_notes(limit=5):
    placeholder = get_placeholder()
    query = f'''
        SELECT r.*, s.name as subject_name
        FROM resources r
        LEFT JOIN subjects s ON r.subject_id = s.id
        WHERE r.is_approved = 1
        ORDER BY r.download_count DESC
        LIMIT {placeholder}
    '''
    return execute_query(query, (limit,), fetchall=True)


def get_most_viewed_notes(limit=5):
    placeholder = get_placeholder()
    query = f'''
        SELECT r.*, s.name as subject_name
        FROM resources r
        LEFT JOIN subjects s ON r.subject_id = s.id
        WHERE r.is_approved = 1
        ORDER BY r.view_count DESC
        LIMIT {placeholder}
    '''
    return execute_query(query, (limit,), fetchall=True)


def get_most_downloaded_subjects(limit=5):
    placeholder = get_placeholder()
    query = f'''
        SELECT s.name as subject_name, SUM(r.download_count) as total_downloads
        FROM resources r
        LEFT JOIN subjects s ON r.subject_id = s.id
        WHERE r.is_approved = 1
        GROUP BY s.id
        ORDER BY total_downloads DESC
        LIMIT {placeholder}
    '''
    return execute_query(query, (limit,), fetchall=True)


def get_most_viewed_subjects(limit=5):
    placeholder = get_placeholder()
    query = f'''
        SELECT s.name as subject_name, SUM(r.view_count) as total_views
        FROM resources r
        LEFT JOIN subjects s ON r.subject_id = s.id
        WHERE r.is_approved = 1
        GROUP BY s.id
        ORDER BY total_views DESC
        LIMIT {placeholder}
    '''
    return execute_query(query, (limit,), fetchall=True)


def upload_to_cloudinary(file_path):
    if not CLOUDINARY_AVAILABLE:
        return None, None
    try:
        upload_result = cloudinary.uploader.upload(file_path, resource_type="auto")
        return upload_result['secure_url'], upload_result['public_id']
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None, None


def delete_from_cloudinary(public_id):
    if not CLOUDINARY_AVAILABLE or not public_id:
        return
    try:
        cloudinary.api.delete_resources([public_id])
    except Exception as e:
        print(f"Cloudinary delete error: {e}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_UPLOAD_EXTENSIONS


def save_upload_file(file, path_parts=None):
    if not file or not file.filename:
        raise ValueError('Please choose a file to upload.')
    if not allowed_file(file.filename):
        raise ValueError('Only PDF, PPT, PPTX, DOC, and DOCX files are allowed.')

    safe_parts = []
    for part in path_parts or []:
        if not part:
            continue
        safe_part = secure_filename(str(part)).strip('._')
        if safe_part:
            safe_parts.append(safe_part)

    target_dir = os.path.join(app.config['UPLOAD_FOLDER'], *safe_parts)
    os.makedirs(target_dir, exist_ok=True)

    original = secure_filename(file.filename)
    stem, ext = os.path.splitext(original)
    filename = f"{stem[:80]}_{uuid4().hex[:10]}{ext.lower()}"
    file_path = os.path.join(target_dir, filename)
    file.save(file_path)

    relative_path = '/'.join(['uploads'] + safe_parts + [filename])
    return file_path, relative_path, ext.lower().lstrip('.')


def create_note_record(resource_id, subject_id, title, file_url, file_type):
    query = insert_ignore_sql('notes', ['resource_id', 'subject_id', 'title', 'file_url', 'file_type'])
    try:
        execute_query(query, (resource_id, subject_id, title, file_url, file_type), commit=True)
    except Exception as exc:
        print(f"[notes] Unable to create compatibility note record: {exc}")


def get_filtered_subjects(scheme_id=None, semester_id=None, cycle_id=None, branch_id=None):
    placeholder = get_placeholder()
    params = []
    where_parts = []

    if scheme_id:
        where_parts.append(f"s.scheme_id = {placeholder}")
        params.append(int(scheme_id))
    if semester_id:
        where_parts.append(f"s.semester_id = {placeholder}")
        params.append(int(semester_id))
    if cycle_id:
        where_parts.append(f"(s.cycle_id = {placeholder} OR s.cycle_id IS NULL)")
        params.append(int(cycle_id))
    if branch_id:
        branch = execute_query(f"SELECT * FROM branches WHERE id = {placeholder}", (int(branch_id),), fetchone=True)
        stream = get_stream_for_branch(branch.get('code')) if branch else None
        branch_parts = [f"s.branch_id = {placeholder}", "s.is_common = 1"]
        params.append(int(branch_id))
        if stream:
            branch_parts.append(f"(s.branch_id IS NULL AND s.stream = {placeholder})")
            params.append(stream)
        where_parts.append(f"({' OR '.join(branch_parts)})")

    where_clause = " AND ".join(where_parts) if where_parts else "1=1"
    return execute_query(f'''
        SELECT s.*, sch.name as scheme_name, sem.name as semester_name
        FROM subjects s
        LEFT JOIN schemes sch ON s.scheme_id = sch.id
        LEFT JOIN semesters sem ON s.semester_id = sem.id
        WHERE {where_clause}
        ORDER BY s.name
    ''', tuple(params), fetchall=True)


def ensure_subjects_for_selection(scheme_id, semester_id, branch_id=None, cycle_id=None):
    if not scheme_id or not semester_id or get_filtered_subjects(scheme_id, semester_id, cycle_id, branch_id):
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    placeholder = get_placeholder()
    try:
        if branch_id:
            cursor.execute(f"SELECT id, code, name FROM branches WHERE id = {placeholder}", (int(branch_id),))
        else:
            cursor.execute("SELECT id, code, name FROM branches")
        branch_rows = cursor.fetchall()

        cursor.execute(f"SELECT semester_number FROM semesters WHERE id = {placeholder}", (int(semester_id),))
        semester_row = cursor.fetchone()
        semester_number = int(semester_row[0]) if semester_row else 1

        for branch_row in branch_rows:
            b_id, b_code, b_name = branch_row[0], branch_row[1], branch_row[2]
            subject_code = f"{b_code}{semester_number:02d}01"
            subject_name = f"{b_name} Semester {semester_number} Core"
            cursor.execute(f"SELECT id FROM subjects WHERE scheme_id = {placeholder} AND semester_id = {placeholder} AND branch_id = {placeholder}", (int(scheme_id), int(semester_id), b_id))
            if cursor.fetchone():
                continue
            cursor.execute(f'''
                INSERT INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ''', (int(scheme_id), int(semester_id), b_id, cycle_id, subject_name, subject_code, 4, get_stream_for_branch(b_code), 0))
        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"[subjects] Unable to auto-create subjects: {exc}")
    finally:
        cursor.close()
        conn.close()


@app.context_processor
def utility_processor():
    return dict(
        get_all_resources=get_all_resources,
        get_resource_type_label=get_resource_type_label,
        get_stats=get_stats,
        execute_query=execute_query,
        get_placeholder=get_placeholder
    )


@app.route('/')
def home():
    stats = get_stats()

    # Get notes data for homepage
    all_resources = get_all_resources()

    notes = []
    trending_notes = []
    most_downloaded_notes_list = []
    most_viewed_notes_list = []

    for res in all_resources:
        ext = res['file_url'].split('.')[-1] if '.' in res['file_url'] else 'pdf'
        note_data = {
            'id': res['id'],
            'title': res['title'],
            'filename': res['file_url'],
            'subject': res.get('subject_name', 'General'),
            'category': get_resource_type_label(res['resource_type']),
            'date': str(res['upload_date']).split(' ')[0],
            'icon': get_file_icon(ext),
            'download_count': res['download_count'],
            'view_count': res['view_count']
        }
        if len(notes) < 6:
            notes.append(note_data)
        trending_notes.append(note_data)

    # Sort trending notes by interactions (download + views)
    trending_notes.sort(key=lambda x: x['download_count'] + x['view_count'], reverse=True)
    trending_notes = trending_notes[:5]

    # Get top notes from DB
    db_most_downloaded = get_most_downloaded_notes(5)
    for res in db_most_downloaded:
        ext = res['file_url'].split('.')[-1] if '.' in res['file_url'] else 'pdf'
        most_downloaded_notes_list.append({
            'id': res['id'],
            'title': res['title'],
            'filename': res['file_url'],
            'subject': res.get('subject_name', 'General'),
            'category': get_resource_type_label(res['resource_type']),
            'date': str(res['upload_date']).split(' ')[0],
            'icon': get_file_icon(ext),
            'download_count': res['download_count'],
            'view_count': res['view_count']
        })

    db_most_viewed = get_most_viewed_notes(5)
    for res in db_most_viewed:
        ext = res['file_url'].split('.')[-1] if '.' in res['file_url'] else 'pdf'
        most_viewed_notes_list.append({
            'id': res['id'],
            'title': res['title'],
            'filename': res['file_url'],
            'subject': res.get('subject_name', 'General'),
            'category': get_resource_type_label(res['resource_type']),
            'date': str(res['upload_date']).split(' ')[0],
            'icon': get_file_icon(ext),
            'download_count': res['download_count'],
            'view_count': res['view_count']
        })

    return render_template('index.html',
                           stats=stats,
                           notes=notes,
                           trending_notes=trending_notes,
                           most_downloaded_notes=most_downloaded_notes_list,
                           most_viewed_notes=most_viewed_notes_list)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_user_by_email(email)

        if user and check_password_hash(user['password'], password):
            session['user_email'] = user['email']
            session['user_name'] = user['username']
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            flash('Login successful!', 'success')

            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password!', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        if get_user_by_email(email):
            flash('Email already registered!', 'danger')
            return render_template('register.html')

        create_user(username, email, password)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = get_user_by_email(session['user_email'])
    is_admin = user.get('role') == 'admin'
    schemes = get_schemes()
    branches = get_branches()
    return render_template('dashboard_v2.html', user=user, is_admin=is_admin, schemes=schemes, branches=branches)


@app.route('/profile')
@login_required
def profile():
    user = get_user_by_email(session['user_email'])
    schemes = get_schemes()
    branches = get_branches()
    return render_template('profile.html', user=user, schemes=schemes, branches=branches)

@app.route('/profile/edit')
@login_required
def profile_edit():
    user = get_user_by_email(session['user_email'])
    schemes = get_schemes()
    branches = get_branches()
    return render_template('profile.html', user=user, schemes=schemes, branches=branches, editing=True)

@app.route('/profile/save', methods=['POST'])
@login_required
def profile_save():
    user = get_user_by_email(session['user_email'])
    username = request.form.get('full_name')
    phone = request.form.get('phone')
    college = request.form.get('college')
    branch = request.form.get('branch')
    semester = request.form.get('semester')
    scheme = request.form.get('scheme')
    bio = request.form.get('bio')

    # Handle profile photo upload
    profile_photo = user.get('profile_photo')
    profile_photo_public_id = user.get('profile_photo_public_id')
    if 'profile_photo' in request.files and request.files['profile_photo'].filename:
        file = request.files['profile_photo']
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Upload to Cloudinary if available
        cloud_url, cloud_public_id = upload_to_cloudinary(file_path)
        if cloud_url:
            profile_photo = cloud_url
            profile_photo_public_id = cloud_public_id
            try:
                os.remove(file_path)
            except:
                pass
        else:
            profile_photo = filename

    # Update user in database
    placeholder = get_placeholder()
    update_query = f'''
        UPDATE users
        SET username = {placeholder},
            phone = {placeholder},
            college = {placeholder},
            branch = {placeholder},
            semester = {placeholder},
            scheme = {placeholder},
            bio = {placeholder},
            profile_photo = {placeholder},
            profile_photo_public_id = {placeholder}
        WHERE id = {placeholder}
    '''
    execute_query(update_query, (
        username, phone, college, branch, semester, scheme, bio,
        profile_photo, profile_photo_public_id,
        user.get('id')
    ), commit=True)

    # Update session
    session['user_name'] = username

    flash('Profile Updated Successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/remove-photo', methods=['POST'])
@login_required
def profile_remove_photo():
    user = get_user_by_email(session['user_email'])
    # Remove from Cloudinary if exists
    if user.get('profile_photo_public_id'):
        delete_from_cloudinary(user.get('profile_photo_public_id'))

    placeholder = get_placeholder()
    update_query = f'UPDATE users SET profile_photo = NULL, profile_photo_public_id = NULL WHERE id = {placeholder}'
    execute_query(update_query, (user.get('id'),), commit=True)

    flash('Profile Photo Removed', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def profile_change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = get_user_by_email(session['user_email'])

        if not check_password_hash(user.get('password'), current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('profile_change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('profile_change_password'))

        placeholder = get_placeholder()
        hashed_new = generate_password_hash(new_password)
        update_query = f'UPDATE users SET password = {placeholder} WHERE id = {placeholder}'
        execute_query(update_query, (hashed_new, user.get('id')), commit=True)

        flash('Password Changed Successfully', 'success')
        return redirect(url_for('profile'))

    return render_template('change_password.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        placeholder = get_placeholder()
        query = '''
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        ''' if mysql_enabled() else '''
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        '''
        execute_query(query, (name, email, subject, message), commit=True)

        feedback_query = '''
            INSERT INTO feedback (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        ''' if mysql_enabled() else '''
            INSERT INTO feedback (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        '''
        try:
            execute_query(feedback_query, (name, email, subject, message), commit=True)
        except Exception:
            pass

        # Forward the message to the configured admin email (studynovaofficial@gmail.com)
        send_admin_notification(name, email, subject, message)

        flash('Message sent successfully! We will get back to you soon.', 'success')

    return render_template('contact.html')


@app.route('/notes/search')
def notes_search():
    schemes = get_schemes()
    branches = get_branches()
    return render_template('notes_search.html', schemes=schemes, branches=branches)

@app.route('/leaderboard')
@login_required
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/syllabus')
@login_required
def syllabus():
    schemes = get_schemes()
    branches = get_branches()
    return render_template('syllabus.html', schemes=schemes, branches=branches)

@app.route('/placement')
@login_required
def placement():
    return render_template('placement.html')

@app.route('/founders')
def founders():
    return render_template('founders.html')

@app.route('/notes')
def notes_library():
    # Get all schemes
    schemes = get_schemes()

    # Get query params - convert to int to ensure type consistency
    scheme_id = request.args.get('scheme_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    cycle_id = request.args.get('cycle_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    section = request.args.get('section')
    resource_id = request.args.get('resource_id', type=int)

    # DEBUG LOGGING
    print(f"[DEBUG] /notes - scheme_id={scheme_id}, semester_id={semester_id}, branch_id={branch_id}, subject_id={subject_id}")

    filtered_semesters = []
    if scheme_id:
        placeholder = get_placeholder()
        filtered_semesters = execute_query(f"SELECT * FROM semesters WHERE scheme_id = {placeholder} ORDER BY semester_number", (int(scheme_id),), fetchall=True)
        print(f"[DEBUG] Filtered semesters for scheme {scheme_id}: {len(filtered_semesters)} found")

    is_first_year = False
    if semester_id:
        semester = execute_query("SELECT * FROM semesters WHERE id = ?" if not mysql_enabled() else "SELECT * FROM semesters WHERE id = %s", (semester_id,), fetchone=True)
        if semester and (semester['semester_number'] == 1 or semester['semester_number'] == 2):
            is_first_year = True

    branches = get_branches() if semester_id else []
    cycles = get_cycles() if is_first_year else []

    filtered_subjects = []
    subject = None
    if subject_id:
        # Get subject details
        subject = execute_query("SELECT * FROM subjects WHERE id = ?" if not mysql_enabled() else "SELECT * FROM subjects WHERE id = %s", (int(subject_id),), fetchone=True)
        print(f"[DEBUG] Selected subject {subject_id}: {subject}")
    else:
        ensure_subjects_for_selection(scheme_id, semester_id, branch_id, cycle_id)
        filtered_subjects = get_filtered_subjects(scheme_id, semester_id, cycle_id, branch_id)
        
        print(f"[DEBUG] Filtered subjects: {len(filtered_subjects)} found")
        if filtered_subjects:
            print(f"[DEBUG] Sample subject: {filtered_subjects[0] if filtered_subjects else 'None'}")

    # Get resources and selected resource
    all_resources = []
    selected_resource = None
    if subject_id:
        placeholder = get_placeholder()
        resources = execute_query(f'''
            SELECT r.*, s.name as subject_name, u.username as uploader_name
            FROM resources r
            LEFT JOIN subjects s ON r.subject_id = s.id
            LEFT JOIN users u ON r.uploaded_by = u.id
            WHERE r.subject_id = {placeholder} AND r.is_approved = 1
            ORDER BY r.upload_date DESC
        ''', (int(subject_id),), fetchall=True)

        print(f"[DEBUG] Resources for subject {subject_id}: {len(resources)} found")
        if resources:
            print(f"[DEBUG] Sample resource: {resources[0]}")

        # Process all resources
        for res in resources:
            ext = res['file_url'].split('.')[-1] if '.' in res['file_url'] else 'pdf'
            all_resources.append({
                'id': res['id'],
                'title': res['title'],
                'filename': res['file_url'],
                'subject': res.get('subject_name', 'General'),
                'category': get_resource_type_label(res['resource_type']),
                'resource_type': res['resource_type'],
                'module_number': res.get('module_number'),
                'date': str(res['upload_date']).split(' ')[0],
                'icon': get_file_icon(ext),
                'download_count': res['download_count'],
                'view_count': res['view_count']
            })

        # If resource_id is provided, select that resource and increment view count
        if resource_id:
            selected_resource = next((r for r in all_resources if str(r['id']) == str(resource_id)), None)
            if selected_resource:
                # Increment view count
                placeholder = get_placeholder()
                update_query = f"UPDATE resources SET view_count = view_count + 1 WHERE id = {placeholder}"
                execute_query(update_query, (int(resource_id),), commit=True)

    return render_template('notes.html',
                           schemes=schemes,
                           scheme_id=scheme_id,
                           semesters=filtered_semesters,
                           semester_id=semester_id,
                           is_first_year=is_first_year,
                           branches=branches,
                           branch_id=branch_id,
                           cycles=cycles,
                           cycle_id=cycle_id,
                           subjects=filtered_subjects,
                           subject_id=subject_id,
                           subject=subject,
                           section=section,
                           all_resources=all_resources,
                           selected_resource=selected_resource)


@app.route('/preview/<path:filename>')
def preview(filename):
    # Find resource by filename or file_url
    placeholder = get_placeholder()
    query = f"SELECT * FROM resources WHERE file_url LIKE {placeholder}"
    resource = execute_query(query, (f'%{filename}%',), fetchone=True)

    if resource:
        # Increment view count
        update_query = f"UPDATE resources SET view_count = view_count + 1 WHERE id = {placeholder}"
        execute_query(update_query, (resource['id'],), commit=True)

    return render_template('preview.html', filename=filename)


@app.route('/download/<path:filename>')
def download(filename):
    # Find resource by filename or file_url
    placeholder = get_placeholder()
    query = f"SELECT * FROM resources WHERE file_url LIKE {placeholder}"
    resource = execute_query(query, (f'%{filename}%',), fetchone=True)

    if resource:
        # Increment download count
        update_query = f"UPDATE resources SET download_count = download_count + 1 WHERE id = {placeholder}"
        execute_query(update_query, (resource['id'],), commit=True)

        # If it's a cloudinary URL, redirect there
        if resource['cloudinary_public_id']:
            return redirect(resource['file_url'])

    # Otherwise serve locally
    try:
        # If filename starts with "uploads/", strip that part
        if filename.startswith('uploads/'):
            filename = filename[len('uploads/'):]
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception:
        flash('File not found!', 'danger')
        return redirect(url_for('notes_library'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    categories = [
        'Module 1 Notes', 'Module 2 Notes', 'Module 3 Notes', 'Module 4 Notes',
        'Module 5 Notes', 'Passing Package', 'Previous Year Question Papers', 'Solutions'
    ]

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        subject_name = request.form.get('subject', 'General')
        category = request.form.get('category', '').strip()
        file = request.files.get('file')

        if not title or not category:
            flash('Title and category are required.', 'danger')
            return redirect(url_for('upload'))

        try:
            file_path, file_url, file_type = save_upload_file(file, ['student_uploads'])
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect(url_for('upload'))

        cloudinary_public_id = None
        cld_url, cld_public_id = upload_to_cloudinary(file_path)
        if cld_url:
            file_url = cld_url
            cloudinary_public_id = cld_public_id
            os.remove(file_path)

        placeholder = get_placeholder()
        subject_record = execute_query("SELECT * FROM subjects LIMIT 1", fetchone=True)
        subject_id = subject_record['id'] if subject_record else get_or_create_general_notes_subject(None)

        resource_type_map = {
            'Module 1 Notes': 'module1',
            'Module 2 Notes': 'module2',
            'Module 3 Notes': 'module3',
            'Module 4 Notes': 'module4',
            'Module 5 Notes': 'module5',
            'Passing Package': 'passing_package',
            'Previous Year Question Papers': 'pyq',
            'Solutions': 'solutions'
        }
        resource_type = resource_type_map.get(category, 'module1')

        user = get_user_by_email(session['user_email'])
        insert_query = f'''
            INSERT INTO resources (subject_id, title, description, file_url, file_type, resource_type, uploaded_by, cloudinary_public_id, is_approved)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        execute_query(insert_query, (
            subject_id,
            title,
            f'Subject: {subject_name}',
            file_url,
            file_type,
            resource_type,
            user['id'] if user else None,
            cloudinary_public_id,
            0  # Pending approval
        ), commit=True)

        resource = execute_query(f"SELECT id FROM resources WHERE file_url = {placeholder} ORDER BY id DESC LIMIT 1", (file_url,), fetchone=True)
        if resource:
            create_note_record(resource['id'], subject_id, title, file_url, file_type)

        flash('Upload successful!', 'success')
        return redirect(url_for('notes_library'))

    return render_template('upload.html', categories=categories)


# Admin Dashboard Routes

@app.route('/admin')
@admin_required
def admin_dashboard():
    return redirect(url_for('admin_analytics'))


@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    stats = get_stats()
    return render_template('admin_analytics.html',
                           stats=stats,
                           most_downloaded_notes=get_most_downloaded_notes(),
                           most_viewed_notes=get_most_viewed_notes(),
                           most_downloaded_subjects=get_most_downloaded_subjects(),
                           most_viewed_subjects=get_most_viewed_subjects())


@app.route('/admin/notes')
@admin_required
def admin_notes():
    notes = get_all_resources()
    return render_template('admin_notes.html', notes=notes)


@app.route('/admin/api/semesters')
@admin_required
def admin_api_semesters():
    scheme_id = request.args.get('scheme_id', type=int)
    if not scheme_id:
        return jsonify([])

    placeholder = get_placeholder()
    semesters = execute_query(f'''
        SELECT id, semester_number, name
        FROM semesters
        WHERE scheme_id = {placeholder}
        ORDER BY semester_number
    ''', (scheme_id,), fetchall=True)
    return jsonify(semesters)


@app.route('/admin/api/branches')
@admin_required
def admin_api_branches():
    scheme_id = request.args.get('scheme_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    if not scheme_id or not semester_id:
        return jsonify([])

    placeholder = get_placeholder()
    branches = execute_query(f'''
        SELECT DISTINCT b.id, b.name, b.code
        FROM branches b
        JOIN subjects s ON s.branch_id = b.id
        WHERE s.scheme_id = {placeholder}
          AND s.semester_id = {placeholder}
        ORDER BY b.name
    ''', (scheme_id, semester_id), fetchall=True)
    return jsonify(branches)


@app.route('/admin/api/subjects')
@admin_required
def admin_api_subjects():
    scheme_id = request.args.get('scheme_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    if not scheme_id or not semester_id or not branch_id:
        print(f"[ADMIN_API_SUBJECTS] Missing params - scheme_id={scheme_id}, semester_id={semester_id}, branch_id={branch_id}")
        return jsonify([])

    placeholder = get_placeholder()
    
    # Get branch-specific subjects
    subjects = execute_query(f'''
        SELECT id, code, name
        FROM subjects
        WHERE scheme_id = {placeholder}
          AND semester_id = {placeholder}
          AND branch_id = {placeholder}
        ORDER BY code
    ''', (scheme_id, semester_id, branch_id), fetchall=True)
    
    # Also get common subjects for this semester
    common_subjects = execute_query(f'''
        SELECT id, code, name
        FROM subjects
        WHERE scheme_id = {placeholder}
          AND semester_id = {placeholder}
          AND is_common = 1
        ORDER BY code
    ''', (scheme_id, semester_id), fetchall=True)
    
    all_subjects = subjects + common_subjects
    all_subjects.sort(key=lambda x: x['code'])
    
    print(f"\n[ADMIN_API_SUBJECTS] Query Execution:")
    print(f"  scheme_id={scheme_id}, semester_id={semester_id}, branch_id={branch_id}")
    print(f"  Branch-specific subjects: {len(subjects)}")
    print(f"  Common subjects: {len(common_subjects)}")
    print(f"  Total subjects: {len(all_subjects)}")
    
    if all_subjects:
        print(f"\n  Subject List:")
        for subj in all_subjects[:10]:  # Show first 10
            print(f"    - {subj['code']:15} | {subj['name']}")
        if len(all_subjects) > 10:
            print(f"    ... and {len(all_subjects) - 10} more subjects")
    else:
        print(f"  ⚠️  No subjects found!")
    
    return jsonify(all_subjects)


@app.route('/admin/users')
@admin_required
def admin_users():
    users = execute_query("SELECT id, username, email, role, phone, college, branch, semester, scheme, registration_date, is_active FROM users ORDER BY registration_date DESC, id DESC", fetchall=True)
    return render_template('admin_users.html', users=users)


@app.route('/admin/academic')
@admin_required
def admin_academic():
    return render_template(
        'admin_academic.html',
        schemes=get_schemes(),
        semesters=get_semesters(),
        branches=get_branches()
    )


@app.route('/admin/schemes/add', methods=['GET', 'POST'])
@admin_required
def admin_add_scheme():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Scheme name is required.', 'danger')
            return redirect(url_for('admin_add_scheme'))
        try:
            execute_query(insert_ignore_sql('schemes', ['name', 'description', 'is_active']), (name, description, 1), commit=True)
            init_db()
            flash('Scheme added successfully!', 'success')
        except Exception as exc:
            flash(f'Unable to add scheme: {exc}', 'danger')
        return redirect(url_for('admin_academic'))
    return render_template('admin_academic.html', mode='scheme', schemes=get_schemes(), semesters=get_semesters(), branches=get_branches())


@app.route('/admin/semesters/add', methods=['GET', 'POST'])
@admin_required
def admin_add_semester():
    if request.method == 'POST':
        scheme_id = request.form.get('scheme_id', type=int)
        semester_number = request.form.get('semester_number', type=int)
        name = request.form.get('name', '').strip()
        if not scheme_id or not semester_number or not name:
            flash('Scheme, semester number, and name are required.', 'danger')
            return redirect(url_for('admin_add_semester'))
        try:
            execute_query(insert_ignore_sql('semesters', ['scheme_id', 'semester_number', 'name']), (scheme_id, semester_number, name), commit=True)
            init_db()
            flash('Semester added successfully!', 'success')
        except Exception as exc:
            flash(f'Unable to add semester: {exc}', 'danger')
        return redirect(url_for('admin_academic'))
    return render_template('admin_academic.html', mode='semester', schemes=get_schemes(), semesters=get_semesters(), branches=get_branches())


@app.route('/admin/branches/add', methods=['GET', 'POST'])
@admin_required
def admin_add_branch():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper().replace(' ', '_')
        if not name or not code:
            flash('Branch name and code are required.', 'danger')
            return redirect(url_for('admin_add_branch'))
        try:
            execute_query(insert_ignore_sql('branches', ['name', 'code', 'is_active']), (name, code, 1), commit=True)
            init_db()
            flash('Branch added successfully!', 'success')
        except Exception as exc:
            flash(f'Unable to add branch: {exc}', 'danger')
        return redirect(url_for('admin_academic'))
    return render_template('admin_academic.html', mode='branch', schemes=get_schemes(), semesters=get_semesters(), branches=get_branches())


@app.route('/admin/subjects/add', methods=['GET', 'POST'])
@admin_required
def admin_add_subject():
    if request.method == 'POST':
        scheme_id = request.form.get('scheme_id', type=int)
        semester_id = request.form.get('semester_id', type=int)
        cycle_id = request.form.get('cycle_id', type=int) if request.form.get('cycle_id') else None
        branch_id = request.form.get('branch_id', type=int) if request.form.get('branch_id') else None
        subject_name = request.form.get('subject_name')
        subject_code = request.form.get('subject_code')
        credits = request.form.get('credits', type=int, default=4)
        stream = request.form.get('stream') or None
        is_common = 1 if request.form.get('is_common') else 0

        if not scheme_id or not semester_id or not subject_name or not subject_code:
            flash('Scheme, semester, subject name and code are required.', 'danger')
            return redirect(url_for('admin_add_subject'))

        placeholder = get_placeholder()
        existing = execute_query(f'''
            SELECT id FROM subjects
            WHERE scheme_id = {placeholder}
              AND semester_id = {placeholder}
              AND COALESCE(branch_id, 0) = COALESCE({placeholder}, 0)
              AND COALESCE(cycle_id, 0) = COALESCE({placeholder}, 0)
              AND code = {placeholder}
        ''', (scheme_id, semester_id, branch_id, cycle_id, subject_code), fetchone=True)
        if existing:
            flash('That subject already exists for this scheme, semester, branch, and cycle.', 'warning')
            return redirect(url_for('admin_add_subject'))

        insert_query = f'''
            INSERT INTO subjects (scheme_id, semester_id, branch_id, cycle_id, name, code, credits, stream, is_common)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        execute_query(insert_query, (
            scheme_id, semester_id, branch_id, cycle_id, subject_name, subject_code, credits, stream, is_common
        ), commit=True)

        flash('Subject added successfully!', 'success')
        return redirect(url_for('admin_notes'))

    return render_template('admin_add_subject.html',
                         schemes=get_schemes(),
                         semesters=get_semesters(),
                         branches=get_branches(),
                         cycles=get_cycles())


@app.route('/admin/notes/upload', methods=['GET', 'POST'])
@admin_required
def admin_upload_note():
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        resource_type = request.form.get('resource_type', '').strip()
        file = request.files.get('file')

        # Extract module number if resource type is module1-5
        module_number = None
        if resource_type.startswith('module'):
            module_number = int(resource_type[-1])

        if not subject_id or not resource_type:
            flash('Please choose a valid subject and file before uploading.', 'danger')
            return redirect(url_for('admin_upload_note'))

        placeholder = get_placeholder()

        # Get subject with is_lab flag
        subject = execute_query(f'''
            SELECT s.*, sch.name as scheme_name, sem.name as semester_name,
                   sem.semester_number, b.name as branch_name, b.code as branch_code,
                   c.name as cycle_name
            FROM subjects s
            JOIN schemes sch ON s.scheme_id = sch.id
            JOIN semesters sem ON s.semester_id = sem.id
            LEFT JOIN branches b ON s.branch_id = b.id
            LEFT JOIN cycles c ON s.cycle_id = c.id
            WHERE s.id = {placeholder}
        ''', (subject_id,), fetchone=True)

        if not subject:
            flash('Subject not found!', 'danger')
            return redirect(url_for('admin_upload_note'))

        # Enforce Lab/Theory subject rules
        is_lab_subject = subject.get('is_lab', 0)
        if is_lab_subject and resource_type != 'lab_manual':
            flash('Lab subjects can only have Lab Manual resources.', 'danger')
            return redirect(url_for('admin_upload_note'))
        if not is_lab_subject and resource_type == 'lab_manual':
            flash('Theory subjects cannot have Lab Manual resources. Please select a lab subject.', 'danger')
            return redirect(url_for('admin_upload_note'))

        parts = [
            subject['scheme_name'],
            subject['semester_name'],
            subject.get('cycle_name'),
            subject.get('branch_code') or subject.get('branch_name'),
            subject['code'],
            resource_type
        ]

        try:
            file_path, file_url, file_type = save_upload_file(file, parts)
        except ValueError as exc:
            flash(str(exc), 'danger')
            return redirect(url_for('admin_upload_note'))

        cloudinary_public_id = None

        type_names = {
            'important_questions': 'Important Questions',
            'lab_manual': 'Lab Manual',
            'pyq': 'Question Paper',
            'solutions': 'Question Paper Solution',
            'passing_package': 'Passing Package'
        }
        title_parts = [f"{subject['code']} - {subject['name']}"]
        title_parts.append(f"Module {module_number} Notes" if module_number else type_names.get(resource_type, resource_type))
        title = ' '.join(title_parts)

        user = get_user_by_email(session['user_email'])
        insert_query = f'''
            INSERT INTO resources (subject_id, title, description, file_url, file_type, resource_type, module_number, uploaded_by, cloudinary_public_id, is_approved)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        '''
        execute_query(insert_query, (
            subject_id,
            title,
            '',
            file_url,
            file_type,
            resource_type,
            module_number,
            user['id'] if user else None,
            cloudinary_public_id,
            1
        ), commit=True)

        resource = execute_query(f"SELECT id FROM resources WHERE file_url = {placeholder} ORDER BY id DESC LIMIT 1", (file_url,), fetchone=True)
        if resource:
            create_note_record(resource['id'], subject_id, title, file_url, file_type)

        flash('Upload successful!', 'success')
        return redirect(url_for('admin_notes'))

    return render_template('admin_upload.html',
                           schemes=get_schemes(),
                           semesters=get_semesters(),
                           branches=get_branches(),
                           cycles=get_cycles(),
                           subjects=get_subjects())


@app.route('/admin/notes/edit/<int:note_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_note(note_id):
    placeholder = get_placeholder()
    note = execute_query(f"SELECT * FROM resources WHERE id = {placeholder}", (note_id,), fetchone=True)

    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('admin_notes'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        module_number = request.form.get('module_number', type=int)
        resource_type = request.form['resource_type']
        if resource_type.startswith('module') and not module_number:
            module_number = int(resource_type[-1])

        update_query = f'''
            UPDATE resources
            SET title = {placeholder}, description = {placeholder}, module_number = {placeholder}, resource_type = {placeholder}
            WHERE id = {placeholder}
        '''
        execute_query(update_query, (title, description, module_number, resource_type, note_id), commit=True)

        flash('Note updated successfully!', 'success')
        return redirect(url_for('admin_notes'))

    return render_template('admin_edit.html', note=note)


@app.route('/admin/notes/replace/<int:note_id>', methods=['GET', 'POST'])
@admin_required
def admin_replace_note(note_id):
    placeholder = get_placeholder()
    note = execute_query(f"SELECT * FROM resources WHERE id = {placeholder}", (note_id,), fetchone=True)

    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('admin_notes'))

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            file_url = filename
            cloudinary_public_id = None
            file_type = filename.split('.')[-1] if '.' in filename else 'pdf'

            # Upload to cloudinary if available
            cld_url, cld_public_id = upload_to_cloudinary(file_path)
            if cld_url:
                file_url = cld_url
                cloudinary_public_id = cld_public_id
                os.remove(file_path)

                # Delete old file from Cloudinary if exists
                if note['cloudinary_public_id']:
                    delete_from_cloudinary(note['cloudinary_public_id'])

            # Update database
            update_query = f'''
                UPDATE resources
                SET file_url = {placeholder}, file_type = {placeholder}, cloudinary_public_id = {placeholder}
                WHERE id = {placeholder}
            '''
            execute_query(update_query, (file_url, file_type, cloudinary_public_id, note_id), commit=True)

            flash('File replaced successfully and message sent!', 'success')
            return redirect(url_for('admin_notes'))

    return render_template('admin_replace.html', note=note)


@app.route('/admin/notes/delete/<int:note_id>', methods=['POST'])
@admin_required
def admin_delete_note(note_id):
    placeholder = get_placeholder()
    note = execute_query(f"SELECT * FROM resources WHERE id = {placeholder}", (note_id,), fetchone=True)

    if note:
        # Delete from cloudinary if needed
        if note['cloudinary_public_id']:
            delete_from_cloudinary(note['cloudinary_public_id'])

        execute_query(f"DELETE FROM resources WHERE id = {placeholder}", (note_id,), commit=True)
        flash('Note deleted successfully!', 'success')

    return redirect(url_for('admin_notes'))


@app.route('/admin/notes/approve/<int:note_id>', methods=['POST'])
@admin_required
def admin_approve_note(note_id):
    admin_id = session.get('user_id')
    placeholder = get_placeholder()
    
    # Get note details
    note = execute_query(f"SELECT * FROM resources WHERE id = {placeholder}", (note_id,), fetchone=True)
    
    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('admin_notes'))
    
    # Approve the note
    execute_query(f"UPDATE resources SET is_approved = 1 WHERE id = {placeholder}", (note_id,), commit=True)
    
    # Award stars to the uploader (only if not already approved)
    if note['uploaded_by'] and note['is_approved'] == 0:
        stars_to_award = 5  # Award 5 stars for each approved note
        execute_query(f"UPDATE users SET stars = stars + {placeholder} WHERE id = {placeholder}", 
                     (stars_to_award, note['uploaded_by']), commit=True)
        
        # Create notification for the user
        execute_query(f'''
            INSERT INTO notifications (user_id, title, message, type)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', (note['uploaded_by'], 'Note Approved!', 
              f'Your note "{note["title"]}" has been approved. You earned {stars_to_award} stars!',
              'success'), commit=True)
        
        # Send email notification
        user = execute_query(f"SELECT * FROM users WHERE id = {placeholder}", (note['uploaded_by'],), fetchone=True)
        if user:
            send_note_approved_email(user['email'], user['username'], note['title'])
    
    # Log activity
    log_activity(admin_id=admin_id, action='Note approved', 
                details=f'Note ID: {note_id}, Title: {note["title"]}',
                ip_address=request.remote_addr)
    
    flash('Note approved successfully! Stars awarded to the uploader.', 'success')
    return redirect(url_for('admin_notes'))


@app.route('/admin/notes/reject/<int:note_id>', methods=['POST'])
@admin_required
def admin_reject_note(note_id):
    admin_id = session.get('user_id')
    placeholder = get_placeholder()
    reason = request.form.get('reason', '')
    
    # Get note details
    note = execute_query(f"SELECT * FROM resources WHERE id = {placeholder}", (note_id,), fetchone=True)
    
    if not note:
        flash('Note not found!', 'danger')
        return redirect(url_for('admin_notes'))
    
    # Reject the note (mark as -1 for MySQL, 2 for SQLite)
    rejected_value = -1 if mysql_enabled() else 2
    execute_query(f"UPDATE resources SET is_approved = {placeholder} WHERE id = {placeholder}", 
                 (rejected_value, note_id), commit=True)
    
    # Send email notification to uploader
    if note['uploaded_by']:
        user = execute_query(f"SELECT * FROM users WHERE id = {placeholder}", (note['uploaded_by'],), fetchone=True)
        if user:
            send_note_rejected_email(user['email'], user['username'], note['title'], reason)
    
    # Log activity
    log_activity(admin_id=admin_id, action='Note rejected', 
                details=f'Note ID: {note_id}, Title: {note["title"]}, Reason: {reason}',
                ip_address=request.remote_addr)
    
    flash('Note rejected. Uploader has been notified.', 'warning')
    return redirect(url_for('admin_notes'))


@app.route('/admin/storage')
@admin_required
def admin_storage():
    stats = get_stats()
    return render_template('admin_storage.html', stats=stats)


@app.route('/admin/storage/delete-old', methods=['POST'])
@admin_required
def admin_delete_old():
    placeholder = get_placeholder()
    one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
    delete_query = f"DELETE FROM resources WHERE upload_date < {placeholder}"
    execute_query(delete_query, (one_year_ago,), commit=True)
    flash('Old files deleted successfully!', 'success')
    return redirect(url_for('admin_storage'))


@app.route('/admin/backup/download')
@admin_required
def admin_download_backup():
    backup_filename = f"studynova_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(app.config['UPLOAD_FOLDER'], backup_filename)

    shutil.copy(DATABASE, backup_path)
    response = send_file(backup_path, as_attachment=True, download_name=backup_filename)

    return response


@app.route('/admin/backup/restore', methods=['POST'])
@admin_required
def admin_restore_backup():
    backup_file = request.files.get('backup_file')
    if backup_file and backup_file.filename:
        backup_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(backup_file.filename))
        backup_file.save(backup_path)

        # Restore backup (replace current DB)
        try:
            shutil.copy(backup_path, DATABASE)
            flash('Database restored successfully!', 'success')
        except Exception as e:
            flash(f'Failed to restore database: {e}', 'danger')
        finally:
            os.remove(backup_path)

    return redirect(url_for('admin_storage'))


# --------------------------
# Phase 4: Competitive Exams
# --------------------------

def get_exam_categories():
    return execute_query("SELECT * FROM exam_categories ORDER BY name", fetchall=True)

def get_exam_topics(category_id):
    placeholder = get_placeholder()
    return execute_query(f"SELECT * FROM exam_topics WHERE exam_category_id = {placeholder} ORDER BY name", (category_id,), fetchall=True)

def get_exam_resources(topic_id):
    placeholder = get_placeholder()
    return execute_query(f"SELECT * FROM exam_resources WHERE exam_topic_id = {placeholder} AND is_approved = 1 ORDER BY upload_date DESC", (topic_id,), fetchall=True)

# Competitive Exams Routes
@app.route('/competitive-exams')
def competitive_exams_home():
    return render_template('competitive_exams_home.html', categories=get_exam_categories())

@app.route('/competitive-exams/category/<int:category_id>')
def competitive_exams_category(category_id):
    placeholder = get_placeholder()
    category = execute_query(f"SELECT * FROM exam_categories WHERE id = {placeholder}", (category_id,), fetchone=True)
    topics = get_exam_topics(category_id)
    return render_template('competitive_exams_category.html', category=category, topics=topics)

@app.route('/competitive-exams/topic/<int:topic_id>')
def competitive_exams_topic(topic_id):
    placeholder = get_placeholder()
    topic = execute_query(f"SELECT t.*, c.name as category_name FROM exam_topics t JOIN exam_categories c ON t.exam_category_id = c.id WHERE t.id = {placeholder}", (topic_id,), fetchone=True)
    resources = get_exam_resources(topic_id)
    return render_template('competitive_exams_topic.html', topic=topic, resources=resources)

@app.route('/competitive-exams/preview/<int:resource_id>')
def competitive_exams_preview(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM exam_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if resource:
        update_query = f"UPDATE exam_resources SET view_count = view_count + 1 WHERE id = {placeholder}"
        execute_query(update_query, (resource_id,), commit=True)
    return render_template('preview.html', filename=resource['file_url'])

@app.route('/competitive-exams/download/<int:resource_id>')
def competitive_exams_download(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM exam_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if resource:
        update_query = f"UPDATE exam_resources SET download_count = download_count + 1 WHERE id = {placeholder}"
        execute_query(update_query, (resource_id,), commit=True)
        if resource['cloudinary_public_id']:
            return redirect(resource['file_url'])
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], resource['file_url'])
        except:
            flash('File not found!', 'danger')
            return redirect(url_for('competitive_exams_home'))

@app.route('/competitive-exams/search')
def competitive_exams_search():
    query = request.args.get('q', '')
    category_id = request.args.get('category_id')
    resource_type = request.args.get('resource_type')
    placeholder = get_placeholder()
    sql = '''
        SELECT r.*, t.name as topic_name, c.name as category_name
        FROM exam_resources r
        JOIN exam_topics t ON r.exam_topic_id = t.id
        JOIN exam_categories c ON t.exam_category_id = c.id
        WHERE r.is_approved = 1
    '''
    params = []
    if query:
        sql += f" AND (r.title LIKE {placeholder} OR r.description LIKE {placeholder})"
        params.extend([f'%{query}%', f'%{query}%'])
    if category_id:
        sql += f" AND c.id = {placeholder}"
        params.append(int(category_id))
    if resource_type:
        sql += f" AND r.resource_type = {placeholder}"
        params.append(resource_type)
    sql += " ORDER BY r.upload_date DESC"
    results = execute_query(sql, tuple(params), fetchall=True)
    return render_template('competitive_exams_search.html', results=results, query=query, categories=get_exam_categories())


# --------------------------
# Phase 5: School Notes
# --------------------------

def get_school_classes():
    return execute_query("SELECT * FROM school_classes ORDER BY name", fetchall=True)

def get_school_subjects(class_id):
    placeholder = get_placeholder()
    return execute_query(f"SELECT * FROM school_subjects WHERE school_class_id = {placeholder} ORDER BY name", (class_id,), fetchall=True)

def get_school_chapters(subject_id):
    placeholder = get_placeholder()
    return execute_query(f"SELECT * FROM school_chapters WHERE school_subject_id = {placeholder} ORDER BY chapter_number, name", (subject_id,), fetchall=True)

def get_school_resources(chapter_id):
    placeholder = get_placeholder()
    return execute_query(f"SELECT * FROM school_resources WHERE school_chapter_id = {placeholder} AND is_approved = 1 ORDER BY upload_date DESC", (chapter_id,), fetchall=True)

# School Notes Routes
@app.route('/school-notes')
def school_notes_home():
    return render_template('school_notes_home.html', classes=get_school_classes())

@app.route('/school-notes/class/<int:class_id>')
def school_notes_class(class_id):
    placeholder = get_placeholder()
    cls = execute_query(f"SELECT * FROM school_classes WHERE id = {placeholder}", (class_id,), fetchone=True)
    subjects = get_school_subjects(class_id)
    return render_template('school_notes_class.html', cls=cls, subjects=subjects)

@app.route('/school-notes/subject/<int:subject_id>')
def school_notes_subject(subject_id):
    placeholder = get_placeholder()
    subject = execute_query(f"SELECT s.*, c.name as class_name, c.id as class_id FROM school_subjects s JOIN school_classes c ON s.school_class_id = c.id WHERE s.id = {placeholder}", (subject_id,), fetchone=True)
    chapters = get_school_chapters(subject_id)
    return render_template('school_notes_subject.html', subject=subject, chapters=chapters)

@app.route('/school-notes/chapter/<int:chapter_id>')
def school_notes_chapter(chapter_id):
    placeholder = get_placeholder()
    chapter = execute_query(f"SELECT ch.*, s.name as subject_name, s.id as subject_id, c.name as class_name, c.id as class_id FROM school_chapters ch JOIN school_subjects s ON ch.school_subject_id = s.id JOIN school_classes c ON s.school_class_id = c.id WHERE ch.id = {placeholder}", (chapter_id,), fetchone=True)
    resources = get_school_resources(chapter_id)
    return render_template('school_notes_chapter.html', chapter=chapter, resources=resources)

@app.route('/school-notes/preview/<int:resource_id>')
def school_notes_preview(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM school_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if resource:
        update_query = f"UPDATE school_resources SET view_count = view_count + 1 WHERE id = {placeholder}"
        execute_query(update_query, (resource_id,), commit=True)
    return render_template('preview.html', filename=resource['file_url'])

@app.route('/school-notes/download/<int:resource_id>')
def school_notes_download(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM school_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if resource:
        update_query = f"UPDATE school_resources SET download_count = download_count + 1 WHERE id = {placeholder}"
        execute_query(update_query, (resource_id,), commit=True)
        if resource['cloudinary_public_id']:
            return redirect(resource['file_url'])
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], resource['file_url'])
        except:
            flash('File not found!', 'danger')
            return redirect(url_for('school_notes_home'))

@app.route('/school-notes/search')
def school_notes_search():
    query = request.args.get('q', '')
    class_id = request.args.get('class_id')
    subject_id = request.args.get('subject_id')
    placeholder = get_placeholder()
    sql = '''
        SELECT r.*, ch.name as chapter_name, s.name as subject_name, c.name as class_name
        FROM school_resources r
        JOIN school_chapters ch ON r.school_chapter_id = ch.id
        JOIN school_subjects s ON ch.school_subject_id = s.id
        JOIN school_classes c ON s.school_class_id = c.id
        WHERE r.is_approved = 1
    '''
    params = []
    if query:
        sql += f" AND (r.title LIKE {placeholder} OR r.description LIKE {placeholder})"
        params.extend([f'%{query}%', f'%{query}%'])
    if class_id:
        sql += f" AND c.id = {placeholder}"
        params.append(int(class_id))
    if subject_id:
        sql += f" AND s.id = {placeholder}"
        params.append(int(subject_id))
    sql += " ORDER BY r.upload_date DESC"
    results = execute_query(sql, tuple(params), fetchall=True)
    return render_template('school_notes_search.html', results=results, query=query, classes=get_school_classes())


# --------------------------
# Admin Features for Phases 4 & 5
# --------------------------

# Admin: Competitive Exams
@app.route('/admin/competitive-exams')
@admin_required
def admin_competitive_exams():
    categories = get_exam_categories()
    return render_template('admin_competitive_exams.html', categories=categories)

@app.route('/admin/competitive-exams/category/add', methods=['GET', 'POST'])
@admin_required
def admin_add_exam_category():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        placeholder = get_placeholder()
        execute_query(f"INSERT INTO exam_categories (name, description) VALUES ({placeholder}, {placeholder})", (name, description), commit=True)
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin_competitive_exams'))
    return render_template('admin_add_exam_category.html')

@app.route('/admin/competitive-exams/category/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_exam_category(category_id):
    placeholder = get_placeholder()
    category = execute_query(f"SELECT * FROM exam_categories WHERE id = {placeholder}", (category_id,), fetchone=True)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        execute_query(f"UPDATE exam_categories SET name = {placeholder}, description = {placeholder} WHERE id = {placeholder}", (name, description, category_id), commit=True)
        flash('Category updated!', 'success')
        return redirect(url_for('admin_competitive_exams'))
    return render_template('admin_edit_exam_category.html', category=category)

@app.route('/admin/competitive-exams/category/delete/<int:category_id>', methods=['POST'])
@admin_required
def admin_delete_exam_category(category_id):
    placeholder = get_placeholder()
    # Delete all topics and resources first
    topics = execute_query(f"SELECT id FROM exam_topics WHERE exam_category_id = {placeholder}", (category_id,), fetchall=True)
    for topic in topics:
        resources = execute_query(f"SELECT id, cloudinary_public_id FROM exam_resources WHERE exam_topic_id = {placeholder}", (topic['id'],), fetchall=True)
        for res in resources:
            if res['cloudinary_public_id']:
                delete_from_cloudinary(res['cloudinary_public_id'])
        execute_query(f"DELETE FROM exam_resources WHERE exam_topic_id = {placeholder}", (topic['id'],), commit=True)
    execute_query(f"DELETE FROM exam_topics WHERE exam_category_id = {placeholder}", (category_id,), commit=True)
    execute_query(f"DELETE FROM exam_categories WHERE id = {placeholder}", (category_id,), commit=True)
    flash('Category deleted!', 'success')
    return redirect(url_for('admin_competitive_exams'))

@app.route('/admin/competitive-exams/category/<int:category_id>/topic/add', methods=['GET', 'POST'])
@admin_required
def admin_add_exam_topic(category_id):
    placeholder = get_placeholder()
    category = execute_query(f"SELECT * FROM exam_categories WHERE id = {placeholder}", (category_id,), fetchone=True)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        execute_query(f"INSERT INTO exam_topics (exam_category_id, name, description) VALUES ({placeholder}, {placeholder}, {placeholder})", (category_id, name, description), commit=True)
        flash('Topic added!', 'success')
        return redirect(url_for('competitive_exams_category', category_id=category_id))
    return render_template('admin_add_exam_topic.html', category=category)

@app.route('/admin/competitive-exams/topic/<int:topic_id>/resource/add', methods=['GET', 'POST'])
@admin_required
def admin_add_exam_resource(topic_id):
    placeholder = get_placeholder()
    topic = execute_query(f"SELECT * FROM exam_topics WHERE id = {placeholder}", (topic_id,), fetchone=True)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        resource_type = request.form['resource_type']
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_url = filename
            cloudinary_public_id = None
            file_type = filename.split('.')[-1] if '.' in filename else 'pdf'
            cld_url, cld_public_id = upload_to_cloudinary(file_path)
            if cld_url:
                file_url = cld_url
                cloudinary_public_id = cld_public_id
                os.remove(file_path)
            user = get_user_by_email(session['user_email'])
            execute_query(f'''INSERT INTO exam_resources (exam_topic_id, title, description, file_url, file_type, resource_type, uploaded_by, cloudinary_public_id)
                            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})''',
                         (topic_id, title, description, file_url, file_type, resource_type, user['id'] if user else None, cloudinary_public_id), commit=True)
            flash('Resource added!', 'success')
            return redirect(url_for('competitive_exams_topic', topic_id=topic_id))
    return render_template('admin_add_exam_resource.html', topic=topic)

@app.route('/admin/competitive-exams/resource/<int:resource_id>/replace', methods=['GET', 'POST'])
@admin_required
def admin_replace_exam_resource(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM exam_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_url = filename
            cloudinary_public_id = None
            file_type = filename.split('.')[-1] if '.' in filename else 'pdf'
            cld_url, cld_public_id = upload_to_cloudinary(file_path)
            if cld_url:
                file_url = cld_url
                cloudinary_public_id = cld_public_id
                os.remove(file_path)
                if resource['cloudinary_public_id']:
                    delete_from_cloudinary(resource['cloudinary_public_id'])
            execute_query(f'''UPDATE exam_resources
                            SET file_url = {placeholder}, file_type = {placeholder}, cloudinary_public_id = {placeholder}
                            WHERE id = {placeholder}''', (file_url, file_type, cloudinary_public_id, resource_id), commit=True)
            flash('File replaced!', 'success')
            return redirect(url_for('admin_competitive_exams'))
    return render_template('admin_replace_resource.html', resource=resource, type='exam')

@app.route('/admin/competitive-exams/resource/<int:resource_id>/delete', methods=['POST'])
@admin_required
def admin_delete_exam_resource(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM exam_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if resource and resource['cloudinary_public_id']:
        delete_from_cloudinary(resource['cloudinary_public_id'])
    execute_query(f"DELETE FROM exam_resources WHERE id = {placeholder}", (resource_id,), commit=True)
    flash('Resource deleted!', 'success')
    return redirect(url_for('admin_competitive_exams'))

# Admin: School Notes
@app.route('/admin/school-notes')
@admin_required
def admin_school_notes():
    classes = get_school_classes()
    return render_template('admin_school_notes.html', classes=classes)

@app.route('/admin/school-notes/class/add', methods=['GET', 'POST'])
@admin_required
def admin_add_school_class():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        placeholder = get_placeholder()
        execute_query(f"INSERT INTO school_classes (name, description) VALUES ({placeholder}, {placeholder})", (name, description), commit=True)
        flash('Class added!', 'success')
        return redirect(url_for('admin_school_notes'))
    return render_template('admin_add_school_class.html')

@app.route('/admin/school-notes/subject/add/<int:class_id>', methods=['GET', 'POST'])
@admin_required
def admin_add_school_subject(class_id):
    placeholder = get_placeholder()
    cls = execute_query(f"SELECT * FROM school_classes WHERE id = {placeholder}", (class_id,), fetchone=True)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        execute_query(f"INSERT INTO school_subjects (school_class_id, name, description) VALUES ({placeholder}, {placeholder}, {placeholder})", (class_id, name, description), commit=True)
        flash('Subject added!', 'success')
        return redirect(url_for('school_notes_class', class_id=class_id))
    return render_template('admin_add_school_subject.html', cls=cls)

@app.route('/admin/school-notes/chapter/add/<int:subject_id>', methods=['GET', 'POST'])
@admin_required
def admin_add_school_chapter(subject_id):
    placeholder = get_placeholder()
    subject = execute_query(f"SELECT * FROM school_subjects WHERE id = {placeholder}", (subject_id,), fetchone=True)
    if request.method == 'POST':
        name = request.form['name']
        chapter_number = request.form.get('chapter_number', type=int)
        description = request.form.get('description', '')
        execute_query(f"INSERT INTO school_chapters (school_subject_id, name, chapter_number, description) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})", (subject_id, name, chapter_number, description), commit=True)
        flash('Chapter added!', 'success')
        return redirect(url_for('school_notes_subject', subject_id=subject_id))
    return render_template('admin_add_school_chapter.html', subject=subject)

@app.route('/admin/school-notes/chapter/<int:chapter_id>/resource/add', methods=['GET', 'POST'])
@admin_required
def admin_add_school_resource(chapter_id):
    placeholder = get_placeholder()
    chapter = execute_query(f"SELECT * FROM school_chapters WHERE id = {placeholder}", (chapter_id,), fetchone=True)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        resource_type = request.form['resource_type']
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_url = filename
            cloudinary_public_id = None
            file_type = filename.split('.')[-1] if '.' in filename else 'pdf'
            cld_url, cld_public_id = upload_to_cloudinary(file_path)
            if cld_url:
                file_url = cld_url
                cloudinary_public_id = cld_public_id
                os.remove(file_path)
            user = get_user_by_email(session['user_email'])
            execute_query(f'''INSERT INTO school_resources (school_chapter_id, title, description, file_url, file_type, resource_type, uploaded_by, cloudinary_public_id)
                            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})''',
                         (chapter_id, title, description, file_url, file_type, resource_type, user['id'] if user else None, cloudinary_public_id), commit=True)
            flash('Resource added!', 'success')
            return redirect(url_for('school_notes_chapter', chapter_id=chapter_id))
    return render_template('admin_add_school_resource.html', chapter=chapter)

@app.route('/admin/school-notes/resource/<int:resource_id>/replace', methods=['GET', 'POST'])
@admin_required
def admin_replace_school_resource(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM school_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_url = filename
            cloudinary_public_id = None
            file_type = filename.split('.')[-1] if '.' in filename else 'pdf'
            cld_url, cld_public_id = upload_to_cloudinary(file_path)
            if cld_url:
                file_url = cld_url
                cloudinary_public_id = cld_public_id
                os.remove(file_path)
                if resource['cloudinary_public_id']:
                    delete_from_cloudinary(resource['cloudinary_public_id'])
            execute_query(f'''UPDATE school_resources
                            SET file_url = {placeholder}, file_type = {placeholder}, cloudinary_public_id = {placeholder}
                            WHERE id = {placeholder}''', (file_url, file_type, cloudinary_public_id, resource_id), commit=True)
            flash('File replaced!', 'success')
            return redirect(url_for('admin_school_notes'))
    return render_template('admin_replace_resource.html', resource=resource, type='school')

@app.route('/admin/school-notes/resource/<int:resource_id>/delete', methods=['POST'])
@admin_required
def admin_delete_school_resource(resource_id):
    placeholder = get_placeholder()
    resource = execute_query(f"SELECT * FROM school_resources WHERE id = {placeholder}", (resource_id,), fetchone=True)
    if resource and resource['cloudinary_public_id']:
        delete_from_cloudinary(resource['cloudinary_public_id'])
    execute_query(f"DELETE FROM school_resources WHERE id = {placeholder}", (resource_id,), commit=True)
    flash('Resource deleted!', 'success')
    return redirect(url_for('admin_school_notes'))


# ========== DEBUG ROUTES FOR TROUBLESHOOTING ==========

@app.route('/debug/data-summary')
@admin_required
def debug_data_summary():
    """Comprehensive data summary for diagnostics"""
    placeholder = get_placeholder()
    
    # Count records in each table
    schemes_count = execute_query("SELECT COUNT(*) as count FROM schemes", fetchone=True)['count']
    semesters_count = execute_query("SELECT COUNT(*) as count FROM semesters", fetchone=True)['count']
    branches_count = execute_query("SELECT COUNT(*) as count FROM branches", fetchone=True)['count']
    subjects_count = execute_query("SELECT COUNT(*) as count FROM subjects", fetchone=True)['count']
    resources_count = execute_query("SELECT COUNT(*) as count FROM resources", fetchone=True)['count']
    approved_resources = execute_query("SELECT COUNT(*) as count FROM resources WHERE is_approved = 1", fetchone=True)['count']
    
    # Get sample data
    sample_schemes = execute_query("SELECT * FROM schemes LIMIT 3", fetchall=True)
    sample_semesters = execute_query("SELECT * FROM semesters LIMIT 3", fetchall=True)
    sample_subjects = execute_query("SELECT * FROM subjects LIMIT 5", fetchall=True)
    sample_resources = execute_query("SELECT r.*, s.name as subject_name FROM resources r LEFT JOIN subjects s ON r.subject_id = s.id LIMIT 5", fetchall=True)
    
    # Check for orphaned resources (subject_id doesn't exist)
    orphaned_resources = execute_query("""
        SELECT COUNT(*) as count FROM resources 
        WHERE subject_id NOT IN (SELECT id FROM subjects)
    """, fetchone=True)['count']
    
    # Check subject-resource mapping
    subjects_with_resources = execute_query("""
        SELECT COUNT(DISTINCT r.subject_id) as count FROM resources r
    """, fetchone=True)['count']
    
    summary = {
        'database': 'SQLite' if not mysql_enabled() else 'MySQL',
        'tables': {
            'schemes': schemes_count,
            'semesters': semesters_count,
            'branches': branches_count,
            'subjects': subjects_count,
            'resources': resources_count,
            'approved_resources': approved_resources
        },
        'data_quality': {
            'orphaned_resources': orphaned_resources,
            'subjects_with_resources': subjects_with_resources
        },
        'sample_data': {
            'schemes': sample_schemes,
            'semesters': sample_semesters,
            'subjects': sample_subjects,
            'resources': sample_resources
        }
    }
    
    return render_template('debug_summary.html', summary=summary)


@app.route('/debug/subjects')
@admin_required
def debug_subjects():
    """Debug subjects retrieval"""
    scheme_id = request.args.get('scheme_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    
    placeholder = get_placeholder()
    
    # Get all subjects with full details
    all_subjects = execute_query("""
        SELECT s.*, sch.name as scheme_name, sem.name as semester_name, b.name as branch_name
        FROM subjects s
        LEFT JOIN schemes sch ON s.scheme_id = sch.id
        LEFT JOIN semesters sem ON s.semester_id = sem.id
        LEFT JOIN branches b ON s.branch_id = b.id
        ORDER BY s.name
    """, fetchall=True)
    
    filtered_subjects = all_subjects
    
    if scheme_id:
        filtered_subjects = [s for s in filtered_subjects if s['scheme_id'] == scheme_id]
    if semester_id:
        filtered_subjects = [s for s in filtered_subjects if s['semester_id'] == semester_id]
    if branch_id:
        filtered_subjects = [s for s in filtered_subjects if s['branch_id'] == branch_id or s['is_common']]
    
    return render_template('debug_subjects.html', 
                         all_subjects=all_subjects,
                         filtered_subjects=filtered_subjects,
                         scheme_id=scheme_id,
                         semester_id=semester_id,
                         branch_id=branch_id)


@app.route('/debug/resources')
@admin_required
def debug_resources():
    """Debug resources retrieval"""
    subject_id = request.args.get('subject_id', type=int)
    approved_only = request.args.get('approved_only', 'yes') == 'yes'
    
    placeholder = get_placeholder()
    
    # Get all resources with full details
    query = """
        SELECT r.*, s.name as subject_name, u.username as uploader_name
        FROM resources r
        LEFT JOIN subjects s ON r.subject_id = s.id
        LEFT JOIN users u ON r.uploaded_by = u.id
    """
    
    if approved_only:
        query += " WHERE r.is_approved = 1"
    
    query += " ORDER BY r.upload_date DESC"
    
    all_resources = execute_query(query, fetchall=True)
    
    filtered_resources = all_resources
    if subject_id:
        filtered_resources = [r for r in filtered_resources if r['subject_id'] == subject_id]
    
    return render_template('debug_resources.html',
                         all_resources=all_resources,
                         filtered_resources=filtered_resources,
                         subject_id=subject_id,
                         approved_only=approved_only)


@app.route('/debug/test-flow')
@admin_required
def debug_test_flow():
    """Test the complete flow: scheme -> semester -> branch -> subject -> resources"""
    scheme_id = request.args.get('scheme_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    
    placeholder = get_placeholder()
    
    # Step 1: Get all schemes
    schemes = execute_query("SELECT * FROM schemes ORDER BY name", fetchall=True)
    
    # Step 2: Get semesters for selected scheme
    semesters = []
    if scheme_id:
        semesters = execute_query(f"SELECT * FROM semesters WHERE scheme_id = {placeholder} ORDER BY semester_number", (scheme_id,), fetchall=True)
    
    # Step 3: Get branches
    branches = execute_query("SELECT * FROM branches ORDER BY name", fetchall=True)
    
    # Step 4: Get subjects for selected scheme/semester/branch
    subjects = []
    if scheme_id and semester_id:
        where_parts = [f"s.scheme_id = {placeholder}", f"s.semester_id = {placeholder}"]
        params = [scheme_id, semester_id]
        
        if branch_id:
            where_parts.append(f"(s.branch_id = {placeholder} OR s.is_common = 1)")
            params.append(branch_id)
        
        where_clause = " AND ".join(where_parts)
        subjects = execute_query(f"""
            SELECT s.*, sch.name as scheme_name, sem.name as semester_name
            FROM subjects s
            LEFT JOIN schemes sch ON s.scheme_id = sch.id
            LEFT JOIN semesters sem ON s.semester_id = sem.id
            WHERE {where_clause}
        """, tuple(params), fetchall=True)
    
    # Step 5: Get resources for selected subject
    resources = []
    if subject_id:
        resources = execute_query(f"""
            SELECT r.*, s.name as subject_name, u.username as uploader_name
            FROM resources r
            LEFT JOIN subjects s ON r.subject_id = s.id
            LEFT JOIN users u ON r.uploaded_by = u.id
            WHERE r.subject_id = {placeholder} AND r.is_approved = 1
            ORDER BY r.upload_date DESC
        """, (subject_id,), fetchall=True)
    
    flow = {
        'scheme_id': scheme_id,
        'scheme_name': next((s['name'] for s in schemes if s['id'] == scheme_id), None) if scheme_id else None,
        'semester_id': semester_id,
        'semester_name': next((s['name'] for s in semesters if s['id'] == semester_id), None) if semester_id else None,
        'branch_id': branch_id,
        'branch_name': next((b['name'] for b in branches if b['id'] == branch_id), None) if branch_id else None,
        'subject_id': subject_id,
        'subject_name': next((s['name'] for s in subjects if s['id'] == subject_id), None) if subject_id else None,
        'schemes_available': len(schemes),
        'semesters_available': len(semesters),
        'subjects_available': len(subjects),
        'resources_available': len(resources),
        'schemes': schemes,
        'semesters': semesters,
        'branches': branches,
        'subjects': subjects,
        'resources': resources
    }
    
    return render_template('debug_flow.html', flow=flow)


# ========== PHASE 3: NEW API ENDPOINTS ==========

# Dashboard API
@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    user = get_user_by_email(session['user_email'])
    user_id = user['id']
    
    # Get user's download count
    user_downloads = execute_query(f"SELECT COUNT(*) as count FROM user_downloads WHERE user_id = {get_placeholder()}", (user_id,), fetchone=True)
    total_downloads = user_downloads['count'] if user_downloads else 0
    
    # Get user's stars
    user_stars = user.get('stars', 0)
    achievement_level = user.get('achievement_level', 'Beginner')
    
    # Get unread notifications count
    notifications = execute_query(f"SELECT COUNT(*) as count FROM notifications WHERE user_id = {get_placeholder()} AND is_read = 0", (user_id,), fetchone=True)
    unread_notifications = notifications['count'] if notifications else 0
    
    # Get total approved notes
    total_notes = execute_query("SELECT COUNT(*) as count FROM resources WHERE is_approved = 1", fetchone=True)
    total_approved_notes = total_notes['count'] if total_notes else 0
    
    # Get total syllabus files
    total_syllabus = execute_query("SELECT COUNT(*) as count FROM syllabus", fetchone=True)
    total_syllabus_count = total_syllabus['count'] if total_syllabus else 0
    
    return jsonify({
        'stars': user_stars,
        'achievement_level': achievement_level,
        'notifications_count': unread_notifications,
        'total_downloads': total_downloads,
        'total_approved_notes': total_approved_notes,
        'total_syllabus': total_syllabus_count
    })


# Leaderboard API
@app.route('/api/leaderboard')
@login_required
def api_leaderboard():
    limit = request.args.get('limit', 50, type=int)
    leaders = execute_query(f'''
        SELECT id, username, branch, semester, stars, achievement_level, profile_photo
        FROM users
        WHERE role = 'user' AND is_active = 1
        ORDER BY stars DESC
        LIMIT {get_placeholder()}
    ''', (limit,), fetchall=True)
    
    result = []
    for idx, leader in enumerate(leaders, 1):
        result.append({
            'rank': idx,
            'id': leader['id'],
            'name': leader['username'],
            'branch': leader['branch'],
            'stars': leader['stars'],
            'achievement_level': leader['achievement_level'],
            'profile_photo': leader['profile_photo']
        })
    
    return jsonify(result)


# Notifications API
@app.route('/api/notifications')
@login_required
def api_notifications():
    user = get_user_by_email(session['user_email'])
    user_id = user['id']
    
    notifications = execute_query(f'''
        SELECT * FROM notifications
        WHERE user_id = {get_placeholder()}
        ORDER BY created_at DESC
        LIMIT 50
    ''', (user_id,), fetchall=True)
    
    return jsonify(notifications)


@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def api_notifications_mark_read():
    user = get_user_by_email(session['user_email'])
    user_id = user['id']
    notification_id = request.form.get('notification_id', type=int)
    
    if notification_id:
        execute_query(f"UPDATE notifications SET is_read = 1 WHERE id = {get_placeholder()} AND user_id = {get_placeholder()}", 
                     (notification_id, user_id), commit=True)
    else:
        execute_query(f"UPDATE notifications SET is_read = 1 WHERE user_id = {get_placeholder()}", (user_id,), commit=True)
    
    return jsonify({'success': True})


@app.route('/api/notifications/unread-count')
@login_required
def api_notifications_unread_count():
    user = get_user_by_email(session['user_email'])
    user_id = user['id']
    
    result = execute_query(f"SELECT COUNT(*) as count FROM notifications WHERE user_id = {get_placeholder()} AND is_read = 0", 
                          (user_id,), fetchone=True)
    count = result['count'] if result else 0
    
    return jsonify({'count': count})


# Search API
@app.route('/api/search')
@login_required
def api_search():
    query = request.args.get('q', '').strip()
    subject_code = request.args.get('subject_code', '').strip()
    subject_name = request.args.get('subject_name', '').strip()
    branch = request.args.get('branch', '').strip()
    semester = request.args.get('semester', type=int)
    scheme = request.args.get('scheme', type=int)
    resource_type = request.args.get('resource_type', '').strip()
    
    placeholder = get_placeholder()
    sql = '''
        SELECT r.*, s.name as subject_name, s.code as subject_code, b.name as branch_name, sem.name as semester_name
        FROM resources r
        LEFT JOIN subjects s ON r.subject_id = s.id
        LEFT JOIN branches b ON s.branch_id = b.id
        LEFT JOIN semesters sem ON s.semester_id = sem.id
        WHERE r.is_approved = 1
    '''
    params = []
    
    if query:
        sql += f" AND (r.title LIKE {placeholder} OR r.description LIKE {placeholder})"
        params.extend([f'%{query}%', f'%{query}%'])
    if subject_code:
        sql += f" AND s.code LIKE {placeholder}"
        params.append(f'%{subject_code}%')
    if subject_name:
        sql += f" AND s.name LIKE {placeholder}"
        params.append(f'%{subject_name}%')
    if branch:
        sql += f" AND b.name LIKE {placeholder}"
        params.append(f'%{branch}%')
    if semester:
        sql += f" AND sem.semester_number = {placeholder}"
        params.append(semester)
    if scheme:
        sql += f" AND s.scheme_id = {placeholder}"
        params.append(scheme)
    if resource_type:
        sql += f" AND r.resource_type = {placeholder}"
        params.append(resource_type)
    
    sql += " ORDER BY r.upload_date DESC LIMIT 100"
    
    results = execute_query(sql, tuple(params), fetchall=True)
    return jsonify(results)


# Syllabus API
@app.route('/api/syllabus/subjects')
@login_required
def api_syllabus_subjects():
    scheme_id = request.args.get('scheme_id', type=int)
    semester_id = request.args.get('semester_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    
    if not scheme_id or not semester_id:
        return jsonify([])
    
    placeholder = get_placeholder()
    sql = '''
        SELECT s.id, s.code, s.name
        FROM subjects s
        WHERE s.scheme_id = %s AND s.semester_id = %s
    ''' if mysql_enabled() else '''
        SELECT s.id, s.code, s.name
        FROM subjects s
        WHERE s.scheme_id = ? AND s.semester_id = ?
    '''
    params = [scheme_id, semester_id]
    
    if branch_id:
        sql += " AND (s.branch_id = %s OR s.is_common = 1)" if mysql_enabled() else " AND (s.branch_id = ? OR s.is_common = 1)"
        params.append(branch_id)
    
    sql += " ORDER BY s.code"
    
    subjects = execute_query(sql, tuple(params), fetchall=True)
    return jsonify(subjects)


@app.route('/api/syllabus/<int:subject_id>')
@login_required
def api_syllabus_get(subject_id):
    placeholder = get_placeholder()
    syllabus = execute_query(f"SELECT * FROM syllabus WHERE subject_id = {placeholder}", (subject_id,), fetchone=True)
    return jsonify(syllabus) if syllabus else jsonify(None)


# Report Note API
@app.route('/api/report-note', methods=['POST'])
@login_required
def api_report_note():
    user = get_user_by_email(session['user_email'])
    resource_id = request.form.get('resource_id', type=int)
    report_type = request.form.get('report_type', '').strip()
    description = request.form.get('description', '').strip()
    
    if not resource_id or not report_type:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    placeholder = get_placeholder()
    execute_query(f'''
        INSERT INTO report_notes (resource_id, reported_by, report_type, description)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
    ''', (resource_id, user['id'], report_type, description), commit=True)
    
    return jsonify({'success': True})


# Password Reset API
@app.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    email = request.form.get('email', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent.'})
    
    # Generate reset token
    reset_token = str(uuid4())
    expires_at = datetime.now() + timedelta(hours=1)
    
    placeholder = get_placeholder()
    execute_query(f'''
        INSERT INTO password_reset_tokens (user_id, token, expires_at)
        VALUES ({placeholder}, {placeholder}, {placeholder})
    ''', (user['id'], reset_token, expires_at), commit=True)
    
    # Send email
    send_password_reset_email(user['email'], user['username'], reset_token)
    
    return jsonify({'success': True, 'message': 'If that email exists, a reset link has been sent.'})


@app.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    token = request.form.get('token', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not token or not new_password or not confirm_password:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})
    
    # Find valid token
    placeholder = get_placeholder()
    token_record = execute_query(f'''
        SELECT * FROM password_reset_tokens 
        WHERE token = {placeholder} AND used = 0 AND expires_at > NOW()
    ''', (token,), fetchone=True)
    
    if not token_record:
        return jsonify({'success': False, 'message': 'Invalid or expired reset token'})
    
    # Update password
    hashed_password = generate_password_hash(new_password)
    execute_query(f"UPDATE users SET password = {placeholder} WHERE id = {placeholder}", 
                 (hashed_password, token_record['user_id']), commit=True)
    
    # Mark token as used
    execute_query(f"UPDATE password_reset_tokens SET used = 1 WHERE id = {placeholder}", 
                 (token_record['id'],), commit=True)
    
    return jsonify({'success': True, 'message': 'Password reset successful'})


# Feedback API
@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()
    
    if not all([name, email, subject, message]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    placeholder = get_placeholder()
    execute_query(f'''
        INSERT INTO feedback (name, email, subject, message)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
    ''', (name, email, subject, message), commit=True)
    
    # Get feedback ID
    feedback = execute_query(f"SELECT id FROM feedback WHERE email = {placeholder} ORDER BY id DESC LIMIT 1", (email,), fetchone=True)
    feedback_id = feedback['id'] if feedback else 0
    
    # Send notification email
    send_feedback_notification_email(feedback_id, name, email, subject, message)
    
    return jsonify({'success': True, 'message': 'Feedback submitted successfully'})


# ========== PHASE 5: ADMIN API ENDPOINTS ==========

# Admin: Activity Logs
@app.route('/admin/api/activity-logs')
@admin_required
def admin_api_activity_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    admin_id = session.get('user_id')
    
    # Get total count
    total = execute_query("SELECT COUNT(*) as count FROM activity_logs", fetchone=True)
    total_count = total['count'] if total else 0
    
    # Get logs
    logs = execute_query(f'''
        SELECT al.*, u.username as admin_name
        FROM activity_logs al
        LEFT JOIN users u ON al.admin_id = u.id
        ORDER BY al.created_at DESC
        LIMIT {get_placeholder()} OFFSET {get_placeholder()}
    ''', (per_page, offset), fetchall=True)
    
    return jsonify({
        'logs': logs,
        'total': total_count,
        'page': page,
        'per_page': per_page
    })


# Admin: Report Notes
@app.route('/admin/report-notes')
@admin_required
def admin_report_notes():
    status = request.args.get('status', 'pending')
    placeholder = get_placeholder()
    
    reports = execute_query(f'''
        SELECT rn.*, r.title as resource_title, r.file_url,
               u.username as reported_by_name
        FROM report_notes rn
        LEFT JOIN resources r ON rn.resource_id = r.id
        LEFT JOIN users u ON rn.reported_by = u.id
        WHERE rn.status = {placeholder}
        ORDER BY rn.created_at DESC
    ''', (status,), fetchall=True)
    
    return render_template('admin_report_notes.html', reports=reports, status=status)


@app.route('/admin/report-notes/resolve/<int:report_id>', methods=['POST'])
@admin_required
def admin_resolve_report(report_id):
    admin_id = session.get('user_id')
    action = request.form.get('action', 'resolved')
    
    placeholder = get_placeholder()
    execute_query(f'''
        UPDATE report_notes
        SET status = {placeholder}, resolved_by = {placeholder}, resolved_at = NOW()
        WHERE id = {placeholder}
    ''', (action, admin_id, report_id), commit=True)
    
    log_activity(admin_id=admin_id, action=f'Report {action}', 
                details=f'Report ID: {report_id}', 
                ip_address=request.remote_addr)
    
    flash(f'Report marked as {action}!', 'success')
    return redirect(url_for('admin_report_notes'))


# Admin: Feedback Management
@app.route('/admin/feedback')
@admin_required
def admin_feedback():
    status = request.args.get('status', 'all')
    placeholder = get_placeholder()
    
    sql = "SELECT * FROM feedback"
    params = []
    
    if status != 'all':
        sql += f" WHERE status = {placeholder}"
        params.append(status)
    
    sql += " ORDER BY created_at DESC"
    
    feedbacks = execute_query(sql, tuple(params), fetchall=True)
    return render_template('admin_feedback.html', feedbacks=feedbacks, status=status)


@app.route('/admin/feedback/mark-read/<int:feedback_id>', methods=['POST'])
@admin_required
def admin_feedback_mark_read(feedback_id):
    admin_id = session.get('user_id')
    placeholder = get_placeholder()
    execute_query(f"UPDATE feedback SET status = 'read' WHERE id = {placeholder}", (feedback_id,), commit=True)
    
    log_activity(admin_id=admin_id, action='Feedback marked as read', 
                details=f'Feedback ID: {feedback_id}',
                ip_address=request.remote_addr)
    
    return jsonify({'success': True})


@app.route('/admin/feedback/delete/<int:feedback_id>', methods=['POST'])
@admin_required
def admin_feedback_delete(feedback_id):
    admin_id = session.get('user_id')
    placeholder = get_placeholder()
    execute_query(f"DELETE FROM feedback WHERE id = {placeholder}", (feedback_id,), commit=True)
    
    log_activity(admin_id=admin_id, action='Feedback deleted', 
                details=f'Feedback ID: {feedback_id}',
                ip_address=request.remote_addr)
    
    flash('Feedback deleted!', 'success')
    return redirect(url_for('admin_feedback'))


# Admin: User Management
@app.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    admin_id = session.get('user_id')
    placeholder = get_placeholder()
    
    user = execute_query(f"SELECT * FROM users WHERE id = {placeholder}", (user_id,), fetchone=True)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin_users'))
    
    if user['role'] == 'admin':
        flash('Cannot deactivate admin users!', 'danger')
        return redirect(url_for('admin_users'))
    
    new_status = 0 if user['is_active'] else 1
    execute_query(f"UPDATE users SET is_active = {placeholder} WHERE id = {placeholder}", 
                 (new_status, user_id), commit=True)
    
    action = 'activated' if new_status else 'deactivated'
    log_activity(admin_id=admin_id, action=f'User {action}', 
                details=f'User: {user["username"]} (ID: {user_id})',
                ip_address=request.remote_addr)
    
    flash(f'User {action} successfully!', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    admin_id = session.get('user_id')
    placeholder = get_placeholder()
    
    user = execute_query(f"SELECT * FROM users WHERE id = {placeholder}", (user_id,), fetchone=True)
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('admin_users'))
    
    if user['role'] == 'admin':
        flash('Cannot delete admin users!', 'danger')
        return redirect(url_for('admin_users'))
    
    execute_query(f"DELETE FROM users WHERE id = {placeholder}", (user_id,), commit=True)
    
    log_activity(admin_id=admin_id, action='User deleted', 
                details=f'User: {user["username"]} (ID: {user_id})',
                ip_address=request.remote_addr)
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))


# Admin: Stream Management
@app.route('/admin/streams')
@admin_required
def admin_streams():
    streams = execute_query("SELECT * FROM streams ORDER BY name", fetchall=True)
    return render_template('admin_streams.html', streams=streams)

@app.route('/admin/streams/add', methods=['POST'])
@admin_required
def admin_add_stream():
    stream_name = request.form.get('stream_name', '').strip()
    stream_code = request.form.get('stream_code', '').strip().lower().replace(' ', '_')
    description = request.form.get('description', '').strip()
    
    if not stream_name or not stream_code:
        flash('Stream name and code are required!', 'danger')
        return redirect(url_for('admin_streams'))
    
    placeholder = get_placeholder()
    try:
        execute_query(f"INSERT INTO streams (name, code, description) VALUES ({placeholder}, {placeholder}, {placeholder})",
                     (stream_name, stream_code, description), commit=True)
        flash('Stream added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding stream: {e}', 'danger')
    
    return redirect(url_for('admin_streams'))

@app.route('/admin/streams/update', methods=['POST'])
@admin_required
def admin_update_stream():
    stream_id = request.form.get('stream_id', type=int)
    stream_name = request.form.get('stream_name', '').strip()
    stream_code = request.form.get('stream_code', '').strip().lower().replace(' ', '_')
    description = request.form.get('description', '').strip()
    
    if not stream_id or not stream_name or not stream_code:
        flash('Stream ID, name and code are required!', 'danger')
        return redirect(url_for('admin_streams'))
    
    placeholder = get_placeholder()
    try:
        execute_query(f"UPDATE streams SET name = {placeholder}, code = {placeholder}, description = {placeholder} WHERE id = {placeholder}",
                     (stream_name, stream_code, description, stream_id), commit=True)
        flash('Stream updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating stream: {e}', 'danger')
    
    return redirect(url_for('admin_streams'))

@app.route('/admin/streams/delete', methods=['POST'])
@admin_required
def admin_delete_stream():
    stream_id = request.form.get('stream_id', type=int)
    
    if not stream_id:
        flash('Stream ID is required!', 'danger')
        return redirect(url_for('admin_streams'))
    
    placeholder = get_placeholder()
    try:
        execute_query(f"DELETE FROM streams WHERE id = {placeholder}", (stream_id,), commit=True)
        flash('Stream deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting stream: {e}', 'danger')
    
    return redirect(url_for('admin_streams'))

# Admin: Syllabus Management
@app.route('/admin/syllabus')
@admin_required
def admin_syllabus():
    return render_template('admin_syllabus.html')


@app.route('/admin/syllabus/upload', methods=['GET', 'POST'])
@admin_required
def admin_syllabus_upload():
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        course_description = request.form.get('course_description', '')
        course_outcomes = request.form.get('course_outcomes', '')
        module1 = request.form.get('module1', '')
        module2 = request.form.get('module2', '')
        module3 = request.form.get('module3', '')
        module4 = request.form.get('module4', '')
        module5 = request.form.get('module5', '')
        text_books = request.form.get('text_books', '')
        reference_books = request.form.get('reference_books', '')
        file = request.files.get('file')
        
        if not subject_id:
            flash('Subject is required!', 'danger')
            return redirect(url_for('admin_syllabus_upload'))
        
        file_url = ''
        file_type = ''
        cloudinary_public_id = None
        
        if file and file.filename:
            try:
                file_path, file_url, file_type = save_upload_file(file, ['syllabus'])
                cld_url, cld_public_id = upload_to_cloudinary(file_path)
                if cld_url:
                    file_url = cld_url
                    cloudinary_public_id = cld_public_id
                    os.remove(file_path)
            except Exception as e:
                flash(f'File upload error: {e}', 'danger')
                return redirect(url_for('admin_syllabus_upload'))
        
        user = get_user_by_email(session['user_email'])
        placeholder = get_placeholder()
        execute_query(f'''
            INSERT INTO syllabus (subject_id, file_url, file_type, cloudinary_public_id,
                                 course_description, course_outcomes, module1, module2, module3,
                                 module4, module5, text_books, reference_books, uploaded_by)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        ''', (subject_id, file_url, file_type, cloudinary_public_id, course_description,
              course_outcomes, module1, module2, module3, module4, module5,
              text_books, reference_books, user['id']), commit=True)
        
        flash('Syllabus uploaded successfully!', 'success')
        return redirect(url_for('admin_syllabus'))
    
    # GET request - show form
    schemes = get_schemes()
    semesters = get_semesters()
    branches = get_branches()
    subjects = get_subjects()
    
    return render_template('admin_syllabus_upload.html',
                         schemes=schemes, semesters=semesters,
                         branches=branches, subjects=subjects)


# ========== PWA ROUTES ==========

@app.route('/manifest.json')
def manifest():
    return jsonify({
        'name': 'StudyNova',
        'short_name': 'StudyNova',
        'description': 'Your Ultimate Academic Resource Platform',
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#4e73df',
        'icons': [
            {
                'src': '/static/images/icon-192.png',
                'sizes': '192x192',
                'type': 'image/png'
            },
            {
                'src': '/static/images/icon-512.png',
                'sizes': '512x512',
                'type': 'image/png'
            }
        ]
    })


@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
