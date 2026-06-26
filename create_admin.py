#!/usr/bin/env python3
"""
Script to create admin user in existing StudyNova database
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

ADMIN_EMAIL = os.environ.get('STUDYNOVA_ADMIN_EMAIL', 'demo@studynova.com').strip().lower()
ADMIN_PASSWORD = os.environ.get('STUDYNOVA_ADMIN_PASSWORD', 'studynova123')
ADMIN_NAME = os.environ.get('STUDYNOVA_ADMIN_NAME', 'StudyNova Admin')
DATABASE = os.path.join(os.path.dirname(__file__), 'studynova.db')

def create_admin_user():
    """Create admin user if not exists"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if 'password_hash' not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if 'is_admin' not in existing_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    conn.commit()
    
    # Check if admin already exists
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (ADMIN_EMAIL,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        print(f"✓ User with email {ADMIN_EMAIL} already exists")
        print(f"  ID: {existing_user['id']}")
        print(f"  Username: {existing_user['username']}")
        print(f"  Role: {existing_user['role']}")

        hashed_password = generate_password_hash(ADMIN_PASSWORD)
        cursor.execute("""
            UPDATE users
            SET username = ?,
                email = ?,
                password = ?,
                password_hash = ?,
                role = 'admin',
                is_admin = 1
            WHERE id = ?
        """, (ADMIN_NAME, ADMIN_EMAIL, hashed_password, hashed_password, existing_user['id']))
        conn.commit()
        print("✓ Admin credentials synchronized")
        conn.close()
        return
    
    # Create admin user
    hashed_password = generate_password_hash(ADMIN_PASSWORD)
    cursor.execute('''
        INSERT INTO users (username, email, password, password_hash, role, is_admin, phone, college, branch, semester, scheme)
        VALUES (?, ?, ?, ?, 'admin', 1, '', '', 'Computer Science & Engineering', '3rd Semester', '2022 Scheme')
    ''', (ADMIN_NAME, ADMIN_EMAIL, hashed_password, hashed_password))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Admin user created successfully!")
    print(f"  Email: {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print(f"  Name: {ADMIN_NAME}")
    print(f"\nYou can now login with these credentials at http://localhost:5000/login")

if __name__ == '__main__':
    try:
        create_admin_user()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
