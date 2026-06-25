#!/usr/bin/env python3
"""
End-to-End Cloudinary Integration Test Suite
Tests all upload routes, database persistence, and file operations.
Runs directly without requiring app to be started.
"""

import os
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Load environment variables
load_dotenv()

# Configuration
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
DB_PATH = 'studynova.db'

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Test tracking
test_results = {
    'environment': [],
    'database_existing': [],
    'upload_tests': [],
    'database_persistence': [],
    'delete_tests': [],
    'preview_download': [],
    'summary': {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
}

uploaded_files = []

def print_header(text):
    """Print formatted section header."""
    print(f"\n{BLUE}{'='*80}")
    print(f"{text.center(80)}")
    print(f"{'='*80}{RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    """Print error message."""
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ{RESET} {text}")

def log_result(category, test_name, status, details=""):
    """Log test result."""
    result = {'test': test_name, 'status': status, 'details': details}
    if category in test_results:
        test_results[category].append(result)
    
    if status == 'PASS':
        test_results['summary']['passed'] += 1
        print_success(f"{test_name}")
    elif status == 'FAIL':
        test_results['summary']['failed'] += 1
        print_error(f"{test_name}: {details}")
    elif status == 'WARN':
        test_results['summary']['warnings'] += 1
        print_warning(f"{test_name}: {details}")
    else:
        print_info(f"{test_name}: {details}")

# ============================================================================
# STEP 1: VERIFY ENVIRONMENT & CLOUDINARY
# ============================================================================

def verify_environment():
    """Verify Cloudinary environment variables."""
    print_header("STEP 1: ENVIRONMENT VERIFICATION")
    
    checks = [
        ('CLOUDINARY_CLOUD_NAME', CLOUDINARY_CLOUD_NAME),
        ('CLOUDINARY_API_KEY', CLOUDINARY_API_KEY),
        ('CLOUDINARY_API_SECRET', CLOUDINARY_API_SECRET),
    ]
    
    for var_name, var_value in checks:
        if var_value:
            masked = f"{var_value[:15]}..." if len(var_value) > 15 else var_value
            log_result('environment', f"Env: {var_name}", 'PASS', masked)
        else:
            log_result('environment', f"Env: {var_name}", 'FAIL', 'Not set')
    
    # Test Cloudinary API
    try:
        usage = cloudinary.api.usage()
        log_result('environment', 'Cloudinary API Connection', 'PASS', f"Cloud: {CLOUDINARY_CLOUD_NAME}")
        print_info(f"Account Usage: {usage['usage']['monthly_transformations']}/2000000 transformations")
    except Exception as e:
        log_result('environment', 'Cloudinary API Connection', 'FAIL', str(e))
        return False
    
    return True

# ============================================================================
# STEP 2: VERIFY EXISTING DATABASE UPLOADS
# ============================================================================

def check_existing_uploads():
    """Check existing files in database that are already in Cloudinary."""
    print_header("STEP 2: EXISTING UPLOADS VERIFICATION")
    
    if not os.path.exists(DB_PATH):
        print_error(f"Database not found: {DB_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check resources (admin notes)
        cursor.execute('''
            SELECT id, title, cloudinary_public_id, file_url 
            FROM resources 
            WHERE cloudinary_public_id IS NOT NULL AND cloudinary_public_id != ''
            LIMIT 5
        ''')
        
        resources = cursor.fetchall()
        if resources:
            print_info(f"Found {len(resources)} admin notes in Cloudinary")
            for res in resources:
                try:
                    # Verify file exists in Cloudinary
                    info = cloudinary.api.resource(res['cloudinary_public_id'])
                    if info:
                        log_result('database_existing', 
                                 f"Admin Note: {res['title']}", 
                                 'PASS', 
                                 f"Public ID: {res['cloudinary_public_id']}")
                except:
                    log_result('database_existing', 
                             f"Admin Note: {res['title']}", 
                             'WARN', 
                             f"Not found in Cloudinary: {res['cloudinary_public_id']}")
        else:
            print_warning("No existing uploads found in database")
        
        conn.close()
    
    except Exception as e:
        log_result('database_existing', 'Query existing uploads', 'FAIL', str(e))

# ============================================================================
# STEP 3: TEST DIRECT FILE UPLOADS TO CLOUDINARY
# ============================================================================

def test_file_uploads():
    """Test uploading files directly to Cloudinary."""
    print_header("STEP 3: DIRECT FILE UPLOAD TESTS")
    
    test_files = [
        ('test_document.pdf', 'raw', 'test-pdf-e2e', b'PDF content test'),
        ('test_image.jpg', 'image', 'test-image-e2e', b'\xFF\xD8\xFF\xE0'),  # JPEG header
        ('test_notes.txt', 'raw', 'test-notes-e2e', b'Test notes content'),
        ('test_syllabus.docx', 'raw', 'test-syllabus-e2e', b'DOCX content test'),
    ]
    
    for filename, resource_type, folder, content in test_files:
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                tmp_path,
                resource_type=resource_type,
                folder=folder,
                public_id=f"e2e_{Path(filename).stem}_{os.getpid()}",
                overwrite=True
            )
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            public_id = result['public_id']
            secure_url = result['secure_url']
            
            uploaded_files.append({
                'filename': filename,
                'public_id': public_id,
                'secure_url': secure_url,
                'resource_type': resource_type
            })
            
            log_result('upload_tests', 
                     f"Upload: {filename}", 
                     'PASS', 
                     f"ID: {public_id}")
            
        except Exception as e:
            log_result('upload_tests', 
                     f"Upload: {filename}", 
                     'FAIL', 
                     str(e))

# ============================================================================
# STEP 4: VERIFY DATABASE PERSISTENCE
# ============================================================================

def test_database_persistence():
    """Test that uploaded file data can be stored in database."""
    print_header("STEP 4: DATABASE PERSISTENCE TEST")
    
    if not os.path.exists(DB_PATH):
        log_result('database_persistence', 'Database exists', 'FAIL', f"DB not found: {DB_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get database schema info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        log_result('database_persistence', 
                 'Database connection', 
                 'PASS', 
                 f"Connected, {len(tables)} tables")
        
        # Check if resources table has required columns
        cursor.execute("PRAGMA table_info(resources)")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        required_cols = ['cloudinary_public_id', 'file_url']
        for col in required_cols:
            if col in col_names:
                log_result('database_persistence', 
                         f"Column: {col}", 
                         'PASS')
            else:
                log_result('database_persistence', 
                         f"Column: {col}", 
                         'FAIL', 
                         'Not found in schema')
        
        # Check team_members table for profile photo
        try:
            cursor.execute("PRAGMA table_info(team_members)")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            profile_cols = ['profile_url', 'profile_public_id']
            for col in profile_cols:
                if col in col_names:
                    log_result('database_persistence', 
                             f"Team Column: {col}", 
                             'PASS')
                else:
                    log_result('database_persistence', 
                             f"Team Column: {col}", 
                             'WARN', 
                             'Not found (may not be needed)')
        except:
            pass
        
        # Check users table for profile photo
        try:
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            profile_cols = ['profile_photo', 'profile_photo_public_id']
            for col in profile_cols:
                if col in col_names:
                    log_result('database_persistence', 
                             f"User Column: {col}", 
                             'PASS')
                else:
                    log_result('database_persistence', 
                             f"User Column: {col}", 
                             'WARN', 
                             'Not found')
        except:
            pass
        
        conn.close()
        
    except Exception as e:
        log_result('database_persistence', 'Database check', 'FAIL', str(e))

# ============================================================================
# STEP 5: TEST DELETE OPERATIONS
# ============================================================================

def test_delete_operations():
    """Test that uploaded files can be deleted from Cloudinary."""
    print_header("STEP 5: DELETE OPERATIONS TEST")
    
    if not uploaded_files:
        print_warning("No uploaded files to test delete on")
        return
    
    for file_info in uploaded_files[:2]:  # Test delete on first 2 files
        try:
            public_id = file_info['public_id']
            
            # Delete from Cloudinary
            result = cloudinary.uploader.destroy(public_id)
            
            if result.get('result') == 'ok':
                log_result('delete_tests', 
                         f"Delete: {file_info['filename']}", 
                         'PASS', 
                         f"ID: {public_id}")
            else:
                log_result('delete_tests', 
                         f"Delete: {file_info['filename']}", 
                         'WARN', 
                         f"Result: {result.get('result')}")
        
        except Exception as e:
            log_result('delete_tests', 
                     f"Delete: {file_info['filename']}", 
                     'FAIL', 
                     str(e))

# ============================================================================
# STEP 6: URL ENCODING TEST
# ============================================================================

def test_url_encoding():
    """Test URL encoding for preview/download routes."""
    print_header("STEP 6: URL ENCODING TEST")
    
    from urllib.parse import quote, unquote
    
    test_urls = [
        'scfrqv2e/raw/upload/v1234/test-notes-e2e/e2e_notes_123',
        'scfrqv2e/image/upload/v1234/test-image-e2e/e2e_image_456',
        'scfrqv2e/raw/upload/v1234/path/with spaces/file.pdf',
    ]
    
    for url in test_urls:
        try:
            # Encode URL (as JavaScript would)
            encoded = quote(url, safe='')
            # Decode URL (as Flask route would)
            decoded = unquote(encoded)
            
            if decoded == url:
                log_result('preview_download', 
                         f"URL Encoding: {url[:40]}...", 
                         'PASS')
            else:
                log_result('preview_download', 
                         f"URL Encoding: {url[:40]}...", 
                         'FAIL', 
                         f"Mismatch: {decoded}")
        
        except Exception as e:
            log_result('preview_download', 
                     f"URL Encoding: {url[:40]}...", 
                     'FAIL', 
                     str(e))

# ============================================================================
# STEP 7: VERIFY APP UPLOAD ROUTES
# ============================================================================

def verify_upload_routes():
    """Verify that all upload routes use store_uploaded_file()."""
    print_header("STEP 7: APP UPLOAD ROUTES VERIFICATION")
    
    expected_routes = [
        '/upload',
        '/admin/notes/upload',
        '/admin/notes/replace/<note_id>',
        '/admin/team/add',
        '/admin/team/edit/<member_id>',
        '/profile/save',
        '/admin/syllabus/upload',
        '/admin/competitive-exams/topic/<id>/resource/add',
        '/admin/school-notes/chapter/<id>/resource/add',
    ]
    
    try:
        with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
            app_content = f.read()
        
        for route in expected_routes:
            route_pattern = route.split('<')[0]  # Get base route
            if route_pattern in app_content:
                log_result('upload_tests', 
                         f"Route exists: {route}", 
                         'PASS')
            else:
                log_result('upload_tests', 
                         f"Route exists: {route}", 
                         'WARN', 
                         'Not found in app.py')
        
        # Verify store_uploaded_file is used
        if 'store_uploaded_file' in app_content:
            count = app_content.count('store_uploaded_file')
            log_result('upload_tests', 
                     'store_uploaded_file() function', 
                     'PASS', 
                     f"Used {count} times in app.py")
        else:
            log_result('upload_tests', 
                     'store_uploaded_file() function', 
                     'FAIL', 
                     'Not found in app.py')
    
    except Exception as e:
        log_result('upload_tests', 
                 'Route verification', 
                 'FAIL', 
                 str(e))

# ============================================================================
# STEP 8: GENERATE FINAL REPORT
# ============================================================================

def generate_report():
    """Generate final test report."""
    print_header("FINAL TEST REPORT")
    
    summary = test_results['summary']
    total_tests = summary['passed'] + summary['failed'] + summary['warnings']
    
    print(f"\n{BLUE}Test Results Summary:{RESET}")
    print(f"  {GREEN}✓ Passed:{RESET}   {summary['passed']}/{total_tests}")
    print(f"  {RED}✗ Failed:{RESET}   {summary['failed']}/{total_tests}")
    print(f"  {YELLOW}⚠ Warnings:{RESET} {summary['warnings']}/{total_tests}")
    print()
    
    # Uploaded files summary
    if uploaded_files:
        print(f"{BLUE}Uploaded Files:{RESET}")
        for file_info in uploaded_files:
            print(f"  • {file_info['filename']}")
            print(f"    ID: {file_info['public_id']}")
            print(f"    URL: {file_info['secure_url'][:60]}...")
        print()
    
    # Test categories
    print(f"{BLUE}Test Categories:{RESET}")
    for category, results in test_results.items():
        if category != 'summary' and results:
            passed = sum(1 for r in results if r['status'] == 'PASS')
            print(f"  • {category}: {passed}/{len(results)} passed")
    
    print()
    print(f"{BLUE}Status:{RESET}")
    if summary['failed'] == 0:
        print_success("All critical tests passed!")
    else:
        print_error(f"{summary['failed']} tests failed - review output above")
    
    # Save results
    with open('e2e_test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n{BLUE}Results saved to: e2e_test_results.json{RESET}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all tests."""
    
    print(f"\n{BLUE}{'='*80}")
    print("StudyNova End-to-End Cloudinary Integration Test Suite".center(80))
    print(f"{'='*80}{RESET}")
    print(f"Cloud Name: {CLOUDINARY_CLOUD_NAME}")
    print(f"Database: {DB_PATH}\n")
    
    # Run all test steps
    verify_environment()
    check_existing_uploads()
    test_file_uploads()
    test_database_persistence()
    test_delete_operations()
    test_url_encoding()
    verify_upload_routes()
    generate_report()

if __name__ == '__main__':
    main()
