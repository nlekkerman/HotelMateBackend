#!/usr/bin/env python
"""
Test URL resolution for guest chat context
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory

def test_guest_chat_url():
    """Test if the guest chat context URL resolves correctly"""
    
    try:
        # Try to reverse the URL
        url = reverse('canonical-guest-chat-context', kwargs={'hotel_slug': 'hotel-killarney'})
        print(f"✅ URL reverse successful: {url}")
        
        # Try to resolve the URL
        resolved = resolve(url)
        print(f"✅ URL resolve successful: {resolved.view_name}")
        print(f"   View class: {resolved.func.view_class}")
        
        # Test the actual endpoint path
        expected_path = "/api/guest/hotel/hotel-killarney/chat/context"
        print(f"\n🔍 Expected path: {expected_path}")
        print(f"🔍 Actual path:   {url}")
        print(f"🔍 Match: {url == expected_path}")
        
    except Exception as e:
        print(f"❌ URL resolution failed: {e}")
        import traceback
        traceback.print_exc()
        
    # Test URL patterns manually
    print(f"\n📋 Testing manual URL resolution...")
    factory = RequestFactory()
    
    try:
        # Create a fake request to test the URL
        request = factory.get('/api/guest/hotel/hotel-killarney/chat/context?token=test')
        resolved = resolve('/api/guest/hotel/hotel-killarney/chat/context')
        print(f"✅ Manual URL resolve successful: {resolved.view_name}")
        
    except Exception as e:
        print(f"❌ Manual URL resolution failed: {e}")
        
        # Check if the path is being included correctly
        print(f"\n🔍 Checking if guest URLs are included...")
        try:
            # Test a known working guest URL
            resolved = resolve('/api/guest/hotels/hotel-killarney/site/home/')
            print(f"✅ Guest URL inclusion working: {resolved.view_name}")
        except Exception as e2:
            print(f"❌ Guest URL inclusion broken: {e2}")

if __name__ == "__main__":
    test_guest_chat_url()