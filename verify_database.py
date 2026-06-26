
import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(__file__), 'studynova.db')
print(f"Using database: {db_path}")
print(f"Database file exists: {os.path.exists(db_path)}")

if not os.path.exists(db_path):
    print("Database file not found.")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n=== TABLES IN DATABASE ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table['name']}")

print("\n=== COUNT OF RECORDS IN EACH TABLE ===")
for table in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table['name']};")
        count = cursor.fetchone()['count']
        print(f"  {table['name']}: {count} records")
    except Exception as e:
        print(f"  {table['name']}: ERROR - {e}")

print("\n=== USERS TABLE CONTENTS ===")
try:
    cursor.execute("SELECT id, username, email, role, is_active FROM users;")
    users = cursor.fetchall()
    if users:
        for user in users:
            print(f"  ID: {user['id']} | Username: {user['username']} | Email: {user['email']} | Role: {user['role']} | Active: {user['is_active']}")
    else:
        print("  No users found.")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== RESOURCES TABLE CONTENTS ===")
try:
    cursor.execute("SELECT id, title, file_url, uploaded_by, upload_date FROM resources LIMIT 10;")
    resources = cursor.fetchall()
    if resources:
        for res in resources:
            print(f"  ID: {res['id']} | Title: {res['title']} | File: {res['file_url']} | Uploaded By: {res['uploaded_by']} | Date: {res['upload_date']}")
    else:
        print("  No resources found.")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== TEAM MEMBERS TABLE CONTENTS ===")
try:
    cursor.execute("SELECT id, name, title, is_founder, is_active FROM team_members;")
    team = cursor.fetchall()
    if team:
        for member in team:
            print(f"  ID: {member['id']} | Name: {member['name']} | Title: {member['title']} | Founder: {member['is_founder']} | Active: {member['is_active']}")
    else:
        print("  No team members found.")
except Exception as e:
    print(f"  ERROR: {e}")

conn.close()
