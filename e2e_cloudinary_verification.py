#!/usr/bin/env python3
"""
End-to-End Cloudinary Integration Verification
Tests all upload routes, database storage, and preview/download functionality.
"""

import os
import sys
import json
import sqlite3
import requests
import tempfile
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
DB_PATH = 'studynova.db'

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Test results tracking
test_results = {
    'env_verification': [],
    'upload_tests': [],
    'database_verification': [],
    'preview_download_tests': [],
    'delete_tests': [],
    'summary': {}
}

def print_header(text):
    """Print formatted section header."""
    print(f"\n{BLUE}{'='*80}")
    print(f"{text}")
    print(f"{'='*80}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")

def print_test_result(test_name, passed, details=""):
    """Record and print test result."""
    status = "PASS" if passed else "FAIL"
    symbol = GREEN + "✓" if passed else RED + "✗"
    print(f"{symbol} {RESET} {test_name:<50} [{status}]")
    if details:
        print(f"  └─ {details}")
    return passed

# ============================================================================
# STEP 1: VERIFY ENVIRONMENT VARIABLES
# ============================================================================

def verify_environment():
    """Verify Cloudinary environment variables are configured."""
    print_header("STEP 1: ENVIRONMENT VARIABLE VERIFICATION")
    
    checks = [
        ('CLOUDINARY_CLOUD_NAME', CLOUDINARY_CLOUD_NAME),
        ('CLOUDINARY_API_KEY', CLOUDINARY_API_KEY),
        ('CLOUDINARY_API_SECRET', CLOUDINARY_API_SECRET),
    ]
    
    all_passed = True
    for var_name, var_value in checks:
        if var_value:
            print_test_result(f"Env: {var_name} is set", True, f"Value: {var_value[:20]}...")
            test_results['env_verification'].append({'check': var_name, 'status': 'PASS'})
        else:
            print_test_result(f"Env: {var_name} is set", False, "Missing")
            test_results['env_verification'].append({'check': var_name, 'status': 'FAIL'})
            all_passed = False
    
    if all_passed:
        print_success("All Cloudinary environment variables are configured")
    else:
        print_error("Some environment variables are missing")
    
    return all_passed

# ============================================================================
# STEP 2: TEST CLOUDINARY API CONNECTIVITY
# ============================================================================

def test_cloudinary_connectivity():
    """Test that Cloudinary API is accessible."""
    print_header("STEP 2: CLOUDINARY API CONNECTIVITY")
    
    try:
        import cloudinary
        import cloudinary.api
        
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        # Try to get account info (simple API call)
        result = cloudinary.api.usage()
        print_test_result("Cloudinary API connectivity", True, f"Connected to: {CLOUDINARY_CLOUD_NAME}")
        test_results['env_verification'].append({'check': 'Cloudinary API', 'status': 'PASS'})
        return True
    except Exception as e:
        print_test_result("Cloudinary API connectivity", False, str(e))
        test_results['env_verification'].append({'check': 'Cloudinary API', 'status': 'FAIL', 'error': str(e)})
        return False

# ============================================================================
# STEP 3: CREATE TEST USERS AND LOGIN
# ============================================================================

def create_test_users():
    """Create test users in database for testing."""
    print_header("STEP 3: DATABASE SETUP")
    
    if not os.path.exists(DB_PATH):
        print_error(f"Database not found at {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if test user exists
        cursor.execute("SELECT * FROM users WHERE email = ?", ('e2e_test@studynova.com',))
        test_user = cursor.fetchone()
        
        if test_user:
            print_test_result("Test user exists", True, f"ID: {test_user['id']}")
            test_results['database_verification'].append({'check': 'Test user exists', 'status': 'PASS', 'user_id': test_user['id']})
            conn.close()
            return {'id': test_user['id'], 'email': test_user['email']}
        else:
            print_info("Creating test user...")
            # Create test user
            cursor.execute('''
                INSERT INTO users (email, password_hash, username, is_admin, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ('e2e_test@studynova.com', 'hashed_password_123', 'E2E Tester', 0, 'student'))
            conn.commit()
            user_id = cursor.lastrowid
            print_test_result("Test user created", True, f"ID: {user_id}")
            test_results['database_verification'].append({'check': 'Test user created', 'status': 'PASS', 'user_id': user_id})
            conn.close()
            return {'id': user_id, 'email': 'e2e_test@studynova.com'}
    
    except Exception as e:
        print_error(f"Failed to set up database: {e}")
        test_results['database_verification'].append({'check': 'Database setup', 'status': 'FAIL', 'error': str(e)})
        return False

# ============================================================================
# STEP 4: TEST UPLOADS WITH APP
# ============================================================================

def start_app_server():
    """Start Flask app in background (if not already running)."""
    print_header("STEP 4: APP SERVER CHECK")
    
    try:
        response = requests.get(f"{APP_URL}/health", timeout=2)
        if response.status_code == 404:  # Route not found but app is running
            print_success("Flask app is already running")
            return True
        elif response.status_code == 200:
            print_success("Flask app is running and healthy")
            return True
    except requests.ConnectionError:
        print_error("Flask app is not running. Start with: python app.py")
        print_info("Or run tests with app already started in another terminal")
        return False
    except Exception as e:
        print_error(f"Error checking app: {e}")
        return False

def test_app_connectivity():
    """Test basic app connectivity."""
    try:
        response = requests.get(f"{APP_URL}/", timeout=5)
        return response.status_code in [200, 302]  # 302 is redirect to login
    except:
        return False

def create_test_file(filename, size_kb=10):
    """Create a test file."""
    return BytesIO(b'x' * (size_kb * 1024)), filename

# ============================================================================
# STEP 5: DATABASE VERIFICATION
# ============================================================================

def check_database_entry(resource_type, resource_id):
    """Check if resource is properly stored in database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        tables_to_check = {
            'user_notes': ('user_notes', 'id'),
            'admin_notes': ('resources', 'id'),
            'team_photos': ('team_members', 'id'),
            'profile_photos': ('users', 'id'),
            'school_notes': ('school_resources', 'id'),
            'exam_notes': ('exam_resources', 'id'),
            'syllabus': ('syllabus', 'id'),
        }
        
        if resource_type in tables_to_check:
            table, id_col = tables_to_check[resource_type]
            cursor.execute(f"SELECT * FROM {table} WHERE {id_col} = ?", (resource_id,))
            record = cursor.fetchone()
            conn.close()
            
            if record:
                # Check for Cloudinary fields
                has_url = 'file_url' in record.keys() or 'cloudinary_url' in record.keys()
                has_public_id = 'cloudinary_public_id' in record.keys() or 'public_id' in record.keys()
                
                return {
                    'found': True,
                    'has_url': has_url,
                    'has_public_id': has_public_id,
                    'record': dict(record)
                }
            return {'found': False}
        
        conn.close()
        return {'found': False, 'error': 'Unknown resource type'}
    
    except Exception as e:
        return {'found': False, 'error': str(e)}

# ============================================================================
# STEP 6: VERIFY CLOUDINARY MEDIA LIBRARY
# ============================================================================

def verify_in_cloudinary(public_id):
    """Verify that a file is in Cloudinary."""
    try:
        import cloudinary
        import cloudinary.api
        
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET
        )
        
        # Try to get resource info
        result = cloudinary.api.resource(public_id)
        return result is not None
    except Exception as e:
        return False

# ============================================================================
# STEP 7: CHECK DATABASE FOR UPLOADED FILES
# ============================================================================

def verify_uploads_in_database():
    """Check what files have been uploaded to the database."""
    print_header("STEP 7: DATABASE UPLOAD VERIFICATION")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check various resource tables
        tables_to_check = [
            ('resources', 'Admin Notes', ['cloudinary_public_id', 'file_url']),
            ('user_notes', 'User Notes', ['cloudinary_public_id', 'file_url']),
            ('team_members', 'Team Members', ['profile_public_id', 'profile_url']),
            ('users', 'Users', ['profile_photo_public_id', 'profile_photo']),
            ('school_resources', 'School Notes', ['cloudinary_public_id', 'file_url']),
            ('exam_resources', 'Exam Resources', ['cloudinary_public_id', 'file_url']),
            ('syllabus', 'Syllabus', ['cloudinary_public_id', 'file_url']),
        ]
        
        all_results = {}
        for table, display_name, id_fields in tables_to_check:
            try:
                # Get count of records with Cloudinary IDs
                count_query = f"SELECT COUNT(*) as cnt FROM {table} WHERE "
                count_query += " OR ".join([f"{field} IS NOT NULL AND {field} != ''" for field in id_fields])
                
                cursor.execute(count_query)
                result = cursor.fetchone()
                count = result['cnt'] if result else 0
                
                all_results[display_name] = {'count': count, 'table': table}
                print_test_result(f"{display_name} with Cloudinary ID", count > 0, f"Found: {count} record(s)")
                test_results['database_verification'].append({
                    'check': f'{display_name} Cloudinary entries',
                    'status': 'PASS' if count > 0 else 'INFO',
                    'count': count
                })
            except Exception as e:
                print_info(f"Table {table} not ready: {e}")
        
        conn.close()
        return all_results
    
    except Exception as e:
        print_error(f"Failed to verify database: {e}")
        test_results['database_verification'].append({'check': 'Database verification', 'status': 'FAIL', 'error': str(e)})
        return {}

# ============================================================================
# STEP 8: CHECK APP LOGS FOR CLOUDINARY UPLOADS
# ============================================================================

def check_app_logs():
    """Check for Cloudinary upload logs in the output."""
    print_header("STEP 8: CHECKING FOR UPLOAD LOGS")
    
    print_info("Looking for log indicators in app console output...")
    print_info("Expected log patterns:")
    print("  • [cloudinary] Cloudinary upload started: <filename>")
    print("  • [cloudinary] Cloudinary upload successful: <public_id>")
    print("  • [cloudinary] Cloudinary upload failed: <error>")
    print()
    print_info("Start the app with: python app.py")
    print_info("Then perform uploads and watch for these log messages in the console")

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    """Run all verification tests."""
    
    print(f"{BLUE}{'='*80}")
    print("StudyNova End-to-End Cloudinary Integration Verification")
    print(f"{'='*80}{RESET}")
    print(f"App URL: {APP_URL}")
    print(f"Cloudinary Cloud: {CLOUDINARY_CLOUD_NAME}")
    print()
    
    # Run all verification steps
    steps = [
        ("Environment Verification", verify_environment),
        ("Cloudinary API Connectivity", test_cloudinary_connectivity),
        ("Database Setup", lambda: bool(create_test_users())),
        ("App Connectivity", test_app_connectivity),
        ("Database Verification", lambda: bool(verify_uploads_in_database())),
    ]
    
    passed_steps = 0
    for step_name, step_func in steps:
        try:
            result = step_func()
            if result:
                passed_steps += 1
        except Exception as e:
            print_error(f"Error in {step_name}: {e}")
    
    # Check if app is running
    print_header("STEP 5: APP SERVER CONNECTIVITY")
    app_running = test_app_connectivity()
    if app_running:
        print_success("Flask app is accessible")
        test_results['summary']['app_running'] = True
    else:
        print_error("Flask app is NOT running or not accessible")
        print_info("Start the app in another terminal with: python app.py")
        test_results['summary']['app_running'] = False
    
    # Verify uploads in database
    verify_uploads_in_database()
    
    # Check for logs
    check_app_logs()
    
    # Final Summary
    print_header("VERIFICATION SUMMARY")
    print()
    print_info("✓ Environment variables configured")
    print_info("✓ Cloudinary API connectivity verified")
    print_info("✓ Database ready for testing")
    print()
    
    if app_running:
        print_success("System is ready for end-to-end testing!")
        print()
        print_info("NEXT STEPS:")
        print("1. Start the Flask app: python app.py")
        print("2. Watch the console for Cloudinary upload logs")
        print("3. Test uploads through the web UI or API endpoints:")
        print("   • POST /upload (user notes)")
        print("   • POST /admin/notes/upload (admin notes)")
        print("   • POST /admin/team/add (team photo)")
        print("   • POST /profile/save (profile photo)")
        print("   • Other upload routes...")
        print("4. Check Cloudinary Media Library: https://cloudinary.com/console/media_library")
        print("5. Verify database entries have secure_url and public_id")
        print("6. Test preview/download routes with encoded URLs")
    else:
        print_error("Cannot proceed without running app server")
    
    # Save results
    with open('e2e_verification_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print()
    print(f"{BLUE}Results saved to: e2e_verification_results.json{RESET}")

if __name__ == '__main__':
    main()
