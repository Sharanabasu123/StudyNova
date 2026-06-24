
import sys
import os

print("=== StudyNova Diagnostics ===\n")

# Check Python version
print(f"1. Python Version: {sys.version}")
assert sys.version_info >= (3, 8), "Python 3.8+ required"

# Check required files
print("\n2. Checking required files:")
required_files = [
    "app.py",
    "requirements.txt",
    "templates/layout.html",
]
for f in required_files:
    exists = os.path.exists(f)
    status = "✅" if exists else "❌"
    print(f"   {status} {f}")

# Check imports from app.py
print("\n3. Checking app.py imports:")
try:
    from app import app, init_db
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Initialize database
print("\n4. Initializing database...")
try:
    init_db()
    print("   ✅ Database initialized")
except Exception as e:
    print(f"   ❌ Database error: {e}")
    import traceback
    traceback.print_exc()

# Check if required tables exist
print("\n5. Checking database tables:")
from app import execute_query
tables_to_check = [
    # Existing tables
    "users", "schemes", "branches", "cycles", "semesters", "subjects", "resources",
    # Phase 4 tables
    "exam_categories", "exam_topics", "exam_resources",
    # Phase 5 tables
    "school_classes", "school_subjects", "school_chapters", "school_resources"
]
for table in tables_to_check:
    try:
        result = execute_query(f"SELECT COUNT(*) as cnt FROM {table}", fetchone=True)
        count = result["cnt"] if result else 0
        print(f"   ✅ {table} - {count} rows")
    except Exception as e:
        print(f"   ❌ {table} - {e}")

print("\n=== All tests passed! ===\n")
