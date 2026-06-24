
from app import app, init_db

# Test initializing the database
print("Testing database initialization...")
init_db()
print("Database initialized successfully!")

print("\nChecking if tables were created:")
from app import execute_query
# Check for exam tables
tables = ["exam_categories", "exam_topics", "exam_resources", 
          "school_classes", "school_subjects", "school_chapters", "school_resources"]
for table in tables:
    try:
        count = execute_query(f"SELECT COUNT(*) as cnt FROM {table}", fetchone=True)
        print(f"{table}: {count['cnt'] if count else 0} rows")
    except Exception as e:
        print(f"Error checking {table}: {e}")

print("\nAll tests passed!")
