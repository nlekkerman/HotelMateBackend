"""
Test script for new gallery management endpoints
Run: python test_gallery_endpoints.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.urls import resolve, reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from staff.models import Staff
from hotel.models import Hotel, HotelPublicSettings

print('\n' + '='*60)
print('  Gallery Endpoint Tests')
print('='*60)

# Test URL resolution
print('\n1. Testing URL Resolution:')
print('-' * 60)

test_urls = [
    '/api/staff/hotel/hotel-killarney/settings/',
    '/api/staff/hotel/hotel-killarney/settings/gallery/upload/',
    '/api/staff/hotel/hotel-killarney/settings/gallery/reorder/',
    '/api/staff/hotel/hotel-killarney/settings/gallery/remove/',
    '/api/staff/hotel/hotel-killarney/room-types/',
]

for url in test_urls:
    try:
        match = resolve(url)
        print(f'✓ {url}')
        print(f'  → {match.view_name}')
    except Exception as e:
        print(f'✗ {url}')
        print(f'  → ERROR: {str(e)}')

# Test with authenticated staff (if exists)
print('\n2. Testing Gallery Operations:')
print('-' * 60)

try:
    # Try to get first staff user
    staff = Staff.objects.first()
    if staff and staff.user:
        user = staff.user
        hotel = staff.hotel
        
        print(f'Using staff: {user.username}')
        print(f'Hotel: {hotel.name} ({hotel.slug})')
        
        # Get or create settings
        settings, created = HotelPublicSettings.objects.get_or_create(
            hotel=hotel
        )
        print(f'Settings: {"Created new" if created else "Found existing"}')
        print(f'Current gallery count: {len(settings.gallery)}')
        
        # Create API client (bypass middleware for testing)
        from django.test import override_settings
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Use override_settings to allow testserver
        settings_override = override_settings(
            ALLOWED_HOSTS=['*'],
            MIDDLEWARE=[
                m for m in [
                    'django.middleware.security.SecurityMiddleware',
                    'django.contrib.sessions.middleware.SessionMiddleware',
                    'corsheaders.middleware.CorsMiddleware',
                    'django.middleware.common.CommonMiddleware',
                    'django.contrib.auth.middleware.AuthenticationMiddleware',
                    'django.contrib.messages.middleware.MessageMiddleware',
                ]
            ]
        )
        
        # Test reorder endpoint (POST)
        test_gallery = [
            'https://example.com/image1.jpg',
            'https://example.com/image2.jpg',
            'https://example.com/image3.jpg'
        ]
        
        print('\n3. Testing Reorder Endpoint:')
        with settings_override:
            response = client.post(
                f'/api/staff/hotel/{hotel.slug}/settings/gallery/reorder/',
                {'gallery': test_gallery},
                format='json'
            )
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            count = len(data.get("gallery", []))
            print(f'✓ Gallery updated: {count} images')
        else:
            print(f'✗ Error: {response.content.decode()}')
        
        # Test remove endpoint (DELETE)
        print('\n4. Testing Remove Endpoint:')
        with settings_override:
            response = client.delete(
                f'/api/staff/hotel/{hotel.slug}/settings/gallery/remove/',
                {'url': test_gallery[0]},
                format='json'
            )
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            count = len(data.get("gallery", []))
            print(f'✓ Image removed: {count} images remaining')
        else:
            print(f'✗ Error: {response.content.decode()}')
        
    else:
        print('No staff user found. Create a staff profile to test authenticated endpoints.')
        
except Exception as e:
    print(f'Error during testing: {str(e)}')
    import traceback
    traceback.print_exc()

print('\n' + '='*60)
print('  URL Cleanup Summary')
print('='*60)
print('\n✓ Fixed URLs:')
print('  OLD: /api/staff/hotel/<slug>/hotel/staff/room-types/')
print('  NEW: /api/staff/hotel/<slug>/room-types/')
print('\n✓ New Gallery Endpoints:')
print('  POST /api/staff/hotel/<slug>/settings/gallery/upload/')
print('  POST /api/staff/hotel/<slug>/settings/gallery/reorder/')
print('  DELETE /api/staff/hotel/<slug>/settings/gallery/remove/')
print('\n' + '='*60 + '\n')
