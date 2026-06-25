#!/usr/bin/env python3
"""Check Cloudinary uploads."""
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

try:
    resources = cloudinary.api.resources(max_results=30)
    all_resources = resources.get('resources', [])
    print(f'Total resources in Cloudinary: {len(all_resources)}')
    print('\nRecent uploads (last 15):')
    for r in all_resources[:15]:
        print(f'  • {r["public_id"]} - Type: {r["resource_type"]}')
except Exception as e:
    print(f'Error: {e}')
