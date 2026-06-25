#!/usr/bin/env python3
"""Search for test files in Cloudinary."""
import cloudinary
import cloudinary.api
from dotenv import load_dotenv
import os

load_dotenv()
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

print("Searching for uploaded test files...\n")

# Try to get admin_notes
try:
    results = cloudinary.api.resources(prefix="admin_notes", max_results=10)
    count = len(results.get('resources', []))
    print(f"Files in 'admin_notes' folder: {count}")
    for r in results.get('resources', []):
        print(f"  • {r['public_id']}")
except Exception as e:
    print(f"admin_notes search error: {e}")

# Try user_notes
try:
    results = cloudinary.api.resources(prefix="user_notes", max_results=10)
    count = len(results.get('resources', []))
    print(f"\nFiles in 'user_notes' folder: {count}")
    for r in results.get('resources', []):
        print(f"  • {r['public_id']}")
except Exception as e:
    print(f"user_notes search error: {e}")

# Try syllabus
try:
    results = cloudinary.api.resources(prefix="syllabus", max_results=10)
    count = len(results.get('resources', []))
    print(f"\nFiles in 'syllabus' folder: {count}")
    for r in results.get('resources', []):
        print(f"  • {r['public_id']}")
except Exception as e:
    print(f"syllabus search error: {e}")

# Try studynova
try:
    results = cloudinary.api.resources(prefix="studynova", max_results=10)
    count = len(results.get('resources', []))
    print(f"\nFiles in 'studynova' folder: {count}")
    for r in results.get('resources', []):
        print(f"  • {r['public_id']}")
except Exception as e:
    print(f"studynova search error: {e}")

print("\n" + "="*60)
print("All resources in account (non-samples only):")
try:
    results = cloudinary.api.resources(max_results=100, type='upload')
    all_res = results.get('resources', [])
    non_samples = [r for r in all_res if 'sample' not in r['public_id'].lower()]
    print(f"Total: {len(non_samples)} non-sample resources")
    for r in non_samples[:20]:
        print(f"  • {r['public_id']} ({r['resource_type']})")
except Exception as e:
    print(f"Error: {e}")
