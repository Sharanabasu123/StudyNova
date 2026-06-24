
import sys
import os

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=== StudyNova Syntax Check ===\n")

print("1. Checking Python syntax for app.py...")
try:
    with open("app.py", "rb") as f:
        source = f.read()
    compile(source, "app.py", "exec")
    print("   ✅ app.py syntax is valid")
except SyntaxError as e:
    print(f"   ❌ app.py syntax error:")
    print(f"   Line {e.lineno}, Column {e.offset}: {e.text}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ {e}")
    sys.exit(1)

print("\n2. Checking imports in app.py...")
try:
    from app import app, init_db, execute_query, get_placeholder
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== All syntax checks passed! ===")
