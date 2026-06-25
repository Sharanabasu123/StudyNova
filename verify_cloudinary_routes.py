#!/usr/bin/env python3
"""
Verify that all StudyNova upload routes use store_uploaded_file() and Cloudinary.
This script analyzes the codebase to ensure no routes bypass Cloudinary.
"""

import re
import os

def check_upload_routes():
    """Extract all upload routes and verify they use store_uploaded_file()."""
    
    app_file = "app.py"
    with open(app_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find all routes that handle file uploads
    upload_route_pattern = r"@app\.route\('([^']+)',\s*methods=\['(GET|POST).*'POST'[^]]*\].*?\)\s*(?:@[a-z_]+\n)*def\s+(\w+)\(([^)]*)\):"
    routes = re.finditer(upload_route_pattern, content, re.MULTILINE)
    
    upload_routes = []
    for match in routes:
        route = match.group(1)
        method = match.group(2)
        func_name = match.group(3)
        
        # Check if route likely handles uploads
        if any(keyword in route.lower() or keyword in func_name.lower() 
               for keyword in ['upload', 'add', 'replace', 'profile', 'team', 'photo', 'resource']):
            upload_routes.append({
                'route': route,
                'method': method,
                'function': func_name,
                'match_pos': match.start()
            })
    
    # Extract function bodies and check for store_uploaded_file usage
    results = []
    for route_info in upload_routes:
        func_name = route_info['function']
        
        # Find the function definition
        func_pattern = rf"def {func_name}\([^)]*\):.*?(?=\ndef\s+\w+|$)"
        func_match = re.search(func_pattern, content, re.DOTALL)
        
        if func_match:
            func_body = func_match.group(0)
            uses_store_uploaded = 'store_uploaded_file' in func_body
            uses_file_save = 'file.save(' in func_body and 'store_uploaded_file' not in func_body
            uses_upload_cloudinary = 'upload_file_to_cloudinary' in func_body
            
            results.append({
                'route': route_info['route'],
                'function': func_name,
                'uses_store_uploaded_file': uses_store_uploaded,
                'uses_direct_file_save': uses_file_save,
                'uses_upload_cloudinary': uses_upload_cloudinary,
                'verdict': 'OK' if uses_store_uploaded else 'NEEDS FIX' if uses_file_save else 'UNKNOWN'
            })
    
    return results

def print_report(results):
    """Print a formatted report of upload routes."""
    print("=" * 80)
    print("StudyNova Upload Routes Cloudinary Integration Check")
    print("=" * 80)
    print()
    
    # Group by verdict
    ok_routes = [r for r in results if r['verdict'] == 'OK']
    fix_routes = [r for r in results if r['verdict'] == 'NEEDS FIX']
    unknown_routes = [r for r in results if r['verdict'] == 'UNKNOWN']
    
    print(f"✓ OK Routes ({len(ok_routes)}):")
    print("-" * 80)
    for r in ok_routes:
        print(f"  {r['route']:<40} → {r['function']:<30} uses store_uploaded_file()")
    
    if fix_routes:
        print()
        print(f"✗ NEEDS FIX Routes ({len(fix_routes)}):")
        print("-" * 80)
        for r in fix_routes:
            print(f"  {r['route']:<40} → {r['function']:<30}")
            print(f"    Issues: Direct file.save() call detected - needs refactoring to use store_uploaded_file()")
    
    if unknown_routes:
        print()
        print(f"? UNKNOWN Routes ({len(unknown_routes)}):")
        print("-" * 80)
        for r in unknown_routes:
            print(f"  {r['route']:<40} → {r['function']:<30}")
    
    print()
    print("=" * 80)
    print(f"Summary: {len(ok_routes)} OK, {len(fix_routes)} need fixes, {len(unknown_routes)} unknown")
    print("=" * 80)
    
    # Recommendations
    print()
    print("RECOMMENDED UPLOAD ROUTES TO TEST:")
    print("-" * 80)
    test_routes = [
        "POST /upload (user notes upload)",
        "POST /admin/notes/upload (admin notes upload)",
        "POST /admin/notes/replace/<note_id> (replace admin note)",
        "POST /admin/team/add (team member profile photo)",
        "POST /admin/team/edit/<member_id> (edit team member profile photo)",
        "POST /profile/save (user profile photo)",
        "POST /admin/syllabus/upload (syllabus with file)",
        "POST /admin/competitive-exams/topic/<id>/resource/add (exam resource)",
        "POST /admin/school-notes/chapter/<id>/resource/add (school resource)",
    ]
    for route in test_routes:
        print(f"  • {route}")
    
    print()
    print("VERIFICATION STEPS:")
    print("-" * 80)
    print("1. Set environment variables:")
    print("   export CLOUDINARY_CLOUD_NAME=<your_cloud_name>")
    print("   export CLOUDINARY_API_KEY=<your_api_key>")
    print("   export CLOUDINARY_API_SECRET=<your_api_secret>")
    print()
    print("2. Run the app and check console output for:")
    print("   [cloudinary] Cloudinary upload started: <filename>")
    print("   [cloudinary] Cloudinary upload successful: <public_id>")
    print()
    print("3. Visit https://cloudinary.com/console/media_library to verify files appear")
    print()
    print("4. Run test_cloudinary_upload.py to test all upload routes")

if __name__ == "__main__":
    results = check_upload_routes()
    print_report(results)
