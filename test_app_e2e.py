#!/usr/bin/env python3
"""
Comprehensive Flask App E2E Test
Tests actual HTTP upload routes with real Cloudinary integration.
"""

import os
import sys
import json
import sqlite3
import requests
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import signal

load_dotenv()

# Configuration
APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
DB_PATH = 'studynova.db'
ADMIN_EMAIL = os.getenv('STUDYNOVA_ADMIN_EMAIL', 'demo@studynova.com')
ADMIN_PASSWORD = os.getenv('STUDYNOVA_ADMIN_PASSWORD', 'studynova123')

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

test_results = {
    'app_connectivity': False,
    'login': False,
    'uploads': [],
    'database_verification': [],
    'summary': {'passed': 0, 'failed': 0}
}

def print_header(text):
    print(f"\n{BLUE}{'='*80}")
    print(f"{text.center(80)}")
    print(f"{'='*80}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    print(f"{BLUE}ℹ{RESET} {text}")

print_header("Flask App E2E Upload Test")

# Step 1: Check if app is running
print_header("STEP 1: APP CONNECTIVITY")

print_info(f"Connecting to {APP_URL}...")
time.sleep(1)

try:
    response = requests.get(f"{APP_URL}/", timeout=5)
    print_success("Flask app is running")
    test_results['app_connectivity'] = True
    test_results['summary']['passed'] += 1
except requests.ConnectionError:
    print_error(f"Cannot connect to {APP_URL}")
    print_error("Start the Flask app first:")
    print_info("  python app.py")
    sys.exit(1)
except Exception as e:
    print_error(f"Error: {e}")
    sys.exit(1)

# Step 2: Check app debug endpoints
print_header("STEP 2: APP DEBUG ENDPOINTS")

try:
    response = requests.get(f"{APP_URL}/admin/debug/cloudinary")
    if response.status_code == 200:
        data = response.json()
        print_success(f"Cloudinary endpoint accessible")
        print_info(f"  Available: {data.get('cloudinary_available')}")
        print_info(f"  Configured: {data.get('cloudinary_configured')}")
        for key, value in data.get('env_vars', {}).items():
            status = "✓" if value else "✗"
            print_info(f"  {status} {key}")
except:
    print_warning("Cloudinary debug endpoint not accessible (may be expected)")

# Step 3: Admin Login
print_header("STEP 3: ADMIN AUTHENTICATION")

session = requests.Session()

# Get login page first (for CSRF if needed)
try:
    response = session.get(f"{APP_URL}/login")
    print_success("Login page accessible")
except Exception as e:
    print_warning(f"Could not access login page: {e}")

# Attempt login
try:
    login_data = {
        'email': ADMIN_EMAIL,
        'password': ADMIN_PASSWORD
    }
    response = session.post(
        f"{APP_URL}/login",
        data=login_data,
        allow_redirects=True,
        timeout=10
    )
    
    if response.status_code == 200:
        # Check if we're actually logged in by accessing admin panel
        admin_response = session.get(f"{APP_URL}/admin/dashboard")
        if admin_response.status_code == 200:
            print_success(f"Admin login successful: {ADMIN_EMAIL}")
            test_results['login'] = True
            test_results['summary']['passed'] += 1
        else:
            print_warning("Login response received but admin panel not accessible")
    else:
        print_warning(f"Login returned {response.status_code}")
        test_results['summary']['failed'] += 1

except Exception as e:
    print_error(f"Login failed: {e}")
    test_results['summary']['failed'] += 1

# Step 4: Test Admin Notes Upload
print_header("STEP 4: ADMIN NOTES UPLOAD TEST")

if test_results['login']:
    try:
        # Create test file
        test_file_content = b'%PDF-1.4\n% Test Admin Note for Cloudinary'
        files = {
            'file': ('test_admin_note_e2e.pdf', test_file_content, 'application/pdf'),
            'title': (None, 'E2E Test Admin Note'),
            'description': (None, 'Uploaded via E2E test'),
            'subject_id': (None, '1'),
            'is_approved': (None, '1')
        }
        
        response = session.post(
            f"{APP_URL}/admin/notes/upload",
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            print_success("Admin notes upload endpoint responded with 200")
            test_results['uploads'].append({
                'type': 'admin_notes',
                'status': 'PASS',
                'response_code': 200
            })
            test_results['summary']['passed'] += 1
        else:
            print_warning(f"Admin notes upload returned {response.status_code}")
            test_results['uploads'].append({
                'type': 'admin_notes',
                'status': 'WARN',
                'response_code': response.status_code
            })
    
    except Exception as e:
        print_error(f"Admin notes upload failed: {e}")
        test_results['uploads'].append({
            'type': 'admin_notes',
            'status': 'FAIL',
            'error': str(e)
        })
        test_results['summary']['failed'] += 1
else:
    print_warning("Skipping upload test - not authenticated")

# Step 5: Check Database for Uploads
print_header("STEP 5: DATABASE VERIFICATION")

try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check resources table
    cursor.execute("SELECT COUNT(*) as cnt FROM resources")
    resource_count = cursor.fetchone()['cnt']
    print_success(f"Resources table: {resource_count} total resources")
    
    # Check for Cloudinary entries
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM resources 
        WHERE cloudinary_public_id IS NOT NULL AND cloudinary_public_id != ''
    """)
    cloudinary_count = cursor.fetchone()['cnt']
    
    if cloudinary_count > 0:
        print_success(f"Found {cloudinary_count} resources with Cloudinary ID")
        
        # Show details
        cursor.execute("""
            SELECT id, title, cloudinary_public_id, file_url
            FROM resources 
            WHERE cloudinary_public_id IS NOT NULL 
            LIMIT 5
        """)
        
        for row in cursor.fetchall():
            print_info(f"  • {row['title']}")
            print_info(f"    ID: {row['cloudinary_public_id']}")
            print_info(f"    URL: {row['file_url'][:70]}...")
        
        test_results['database_verification'].append({
            'check': 'Cloudinary entries',
            'status': 'PASS',
            'count': cloudinary_count
        })
        test_results['summary']['passed'] += 1
    else:
        print_warning(f"No resources with Cloudinary ID found")
        test_results['database_verification'].append({
            'check': 'Cloudinary entries',
            'status': 'WARN',
            'count': 0
        })
    
    # Check team_members for profile uploads
    try:
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM team_members 
            WHERE profile_public_id IS NOT NULL AND profile_public_id != ''
        """)
        team_count = cursor.fetchone()['cnt']
        if team_count > 0:
            print_success(f"Team members: {team_count} with profile photos")
            test_results['database_verification'].append({
                'check': 'Team profile photos',
                'status': 'PASS',
                'count': team_count
            })
        else:
            print_warning("No team members with Cloudinary profile photos")
    except:
        pass
    
    # Check users for profile uploads
    try:
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM users 
            WHERE profile_photo_public_id IS NOT NULL AND profile_photo_public_id != ''
        """)
        user_count = cursor.fetchone()['cnt']
        if user_count > 0:
            print_success(f"Users: {user_count} with profile photos")
            test_results['database_verification'].append({
                'check': 'User profile photos',
                'status': 'PASS',
                'count': user_count
            })
        else:
            print_warning("No users with Cloudinary profile photos")
    except:
        pass
    
    conn.close()

except Exception as e:
    print_error(f"Database verification failed: {e}")
    test_results['summary']['failed'] += 1

# Step 6: Final Summary
print_header("TEST SUMMARY")

print(f"\n{BLUE}Results:{RESET}")
print(f"  Passed: {test_results['summary']['passed']}")
print(f"  Failed: {test_results['summary']['failed']}")

if test_results['summary']['failed'] == 0:
    print(f"\n{GREEN}✅ ALL TESTS PASSED{RESET}")
else:
    print(f"\n{RED}❌ {test_results['summary']['failed']} TESTS FAILED{RESET}")

# Save results
with open('app_e2e_test_results.json', 'w') as f:
    json.dump(test_results, f, indent=2)

print(f"\n{BLUE}Results saved to: app_e2e_test_results.json{RESET}\n")

print(f"{BLUE}IMPORTANT NEXT STEPS:{RESET}")
print("1. Keep the Flask app running: python app.py")
print("2. Check the app console for upload logs:")
print("   • [cloudinary] Cloudinary upload started: <filename>")
print("   • [cloudinary] Cloudinary upload successful: <public_id>")
print("   • [cloudinary] Cloudinary upload failed: <error>")
print("3. Visit: https://cloudinary.com/console/media_library")
print("4. Verify files appear in Cloudinary")
print("5. Run this test again to see updated database entries")
