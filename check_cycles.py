import sqlite3

conn = sqlite3.connect('studynova.db')
cursor = conn.cursor()

# Get the schema for the cycles table
cursor.execute("PRAGMA table_info(cycles)")
columns = cursor.fetchall()

print("Cycles table schema:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

# Also check if the table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cycles'")
if cursor.fetchone():
    print("\n✓ Cycles table exists")
else:
    print("\n✗ Cycles table does NOT exist")

conn.close()
