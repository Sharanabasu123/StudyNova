#!/usr/bin/env python3
"""
Test script to verify Cloudinary integration across all upload routes.
Run this after starting the app to test actual uploads.
"""

import os
import sys
import json
import requests
from io import BytesIO

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@test.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# Test credentials - you'll need to provide these
TEST_USER_EMAIL = "test@studynova.com"
TEST_USER_PASSWORD = "test123"

# Create a test session
session = requests.Session()

def log(message, level="INFO"):
    """Print formatted log message."""
    print(f"[{level}] {message}")

def test_cloudinary_config():
    """Check if Cloudinary is properly configured."""
    log("Testing Cloudinary configuration...")
    try:
        response = session.get(f"{BASE_URL}/admin/debug/cloudinary", timeout=5)
        if response.status_code == 200:
            config = response.json()
            log(f"Cloudinary Status: {json.dumps(config, indent=2)}", "OK")
            return config.get("cloudinary_configured", False)
        elif response.status_code == 302:
            log("Need to login first", "WARN")
            return False
        else:
            log(f"Failed to get config: {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"Error checking config: {e}", "ERROR")
        return False

def login(email, password):
    """Login to StudyNova."""
    log(f"Logging in as {email}...")
    try:
        data = {"email": email, "password": password}
        response = session.post(f"{BASE_URL}/login", data=data, allow_redirects=True, timeout=10)
        
        if "dashboard" in response.text or "admin" in response.text or response.status_code == 200:
            log(f"Login successful", "OK")
            return True
        else:
            log(f"Login failed", "ERROR")
            return False
    except Exception as e:
        log(f"Login error: {e}", "ERROR")
        return False

def test_upload(upload_route, file_name="test.pdf", file_content=b"Test PDF content"):
    """Test uploading a file to a specific route."""
    log(f"Testing upload to {upload_route}...")
    
    try:
        files = {"file": (file_name, BytesIO(file_content), "application/pdf")}
        response = session.post(f"{BASE_URL}{upload_route}", files=files, timeout=30)
        
        if response.status_code == 200 or "success" in response.text.lower():
            log(f"Upload successful: {upload_route}", "OK")
            return True
        else:
            log(f"Upload failed for {upload_route}: {response.status_code}", "ERROR")
            log(f"Response: {response.text[:500]}", "DEBUG")
            return False
    except Exception as e:
        log(f"Upload error: {e}", "ERROR")
        return False

def check_cloudinary_library():
    """Check if uploaded files appear in Cloudinary."""
    log("Checking Cloudinary Media Library...")
    log("Please visit https://cloudinary.com/console/media_library to verify uploads", "INFO")
    log("Files should appear in the 'student_uploads', 'admin_notes', 'team_members', etc. folders", "INFO")

def main():
    """Run all Cloudinary integration tests."""
    log("=" * 60)
    log("StudyNova Cloudinary Integration Test")
    log("=" * 60)
    
    # Step 1: Check Cloudinary config (no login needed if debug endpoint is public)
    log("\n[Step 1] Checking Cloudinary Configuration...")
    cloudinary_enabled = test_cloudinary_config()
    
    if not cloudinary_enabled:
        log("Cloudinary is not properly configured!", "ERROR")
        log("Please ensure these environment variables are set:", "WARN")
        log("  - CLOUDINARY_CLOUD_NAME", "WARN")
        log("  - CLOUDINARY_API_KEY", "WARN")
        log("  - CLOUDINARY_API_SECRET", "WARN")
        return 1
    
    log("✓ Cloudinary is properly configured", "OK")
    
    # Step 2: Login as admin
    log("\n[Step 2] Authenticating...")
    if not login(ADMIN_EMAIL, ADMIN_PASSWORD):
        log("Could not authenticate. Check credentials.", "ERROR")
        return 1
    
    log("✓ Authentication successful", "OK")
    
    # Step 3: Test upload routes
    log("\n[Step 3] Testing Upload Routes...")
    
    test_routes = [
        ("/upload", "test_student_upload.pdf"),
        ("/admin/notes/upload", "test_admin_notes.pdf"),
    ]
    
    results = {}
    for route, filename in test_routes:
        results[route] = test_upload(route, filename)
    
    log("\n[Step 4] Upload Results Summary:")
    log("=" * 60)
    for route, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        log(f"{status}: {route}", "OK" if success else "ERROR")
    
    log("\n[Step 5] Verification:")
    log("=" * 60)
    check_cloudinary_library()
    
    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    log(f"\n{'=' * 60}")
    log(f"Test Summary: {passed}/{total} uploads successful", "INFO")
    log(f"{'=' * 60}")
    
    # Check logs for upload messages
    log("\n[Important] Check app console output for these messages:", "WARN")
    log("  - '[cloudinary] Cloudinary upload started: <filename>'", "WARN")
    log("  - '[cloudinary] Cloudinary upload successful: <public_id>'", "WARN")
    log("  - '[cloudinary] Cloudinary upload failed: <error>' (if there were errors)", "WARN")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\nTest interrupted by user", "WARN")
        sys.exit(130)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
