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

ADMIN_EMAIL = os.environ.get('STUDYNOVA_ADMIN_EMAIL', 'demo@studynova.com')
ADMIN_PASSWORD = os.environ.get('STUDYNOVA_ADMIN_PASSWORD', 'studynova123')
ADMIN_NAME = os.environ.get('STUDYNOVA_ADMIN_NAME', 'StudyNova Admin')
DATABASE = os.path.join(os.path.dirname(__file__), 'studynova.db')

def create_admin_user():
    """Create admin user if not exists"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (ADMIN_EMAIL,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        print(f"✓ User with email {ADMIN_EMAIL} already exists")
        print(f"  ID: {existing_user[0]}")
        print(f"  Username: {existing_user[1]}")
        print(f"  Role: {existing_user[4] if len(existing_user) > 4 else 'N/A'}")
        
        # Update to admin role if not already
        if len(existing_user) > 4 and existing_user[4] != 'admin':
            cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (ADMIN_EMAIL,))
            conn.commit()
            print(f"✓ Updated user role to 'admin'")
        conn.close()
        return
    
    # Create admin user
    hashed_password = generate_password_hash(ADMIN_PASSWORD)
    cursor.execute('''
        INSERT INTO users (username, email, password, role, phone, college, branch, semester, scheme)
        VALUES (?, ?, ?, 'admin', '', '', 'Computer Science & Engineering', '3rd Semester', '2022 Scheme')
    ''', (ADMIN_NAME, ADMIN_EMAIL, hashed_password))
    
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