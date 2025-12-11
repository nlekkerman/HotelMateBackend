"""
Test Firebase JSON parsing
"""
import os
import json
from django.conf import settings

# Setup minimal Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

import django
django.setup()

print("🔍 Firebase JSON Debug")
print("=" * 50)

firebase_json = settings.FIREBASE_SERVICE_ACCOUNT_JSON

if not firebase_json:
    print("❌ No Firebase JSON found in settings")
else:
    print(f"📄 Firebase JSON length: {len(firebase_json)} characters")
    print(f"📄 First 100 chars: {firebase_json[:100]}...")
    print(f"📄 Last 100 chars: ...{firebase_json[-100:]}")
    
    try:
        parsed = json.loads(firebase_json)
        print("✅ JSON is valid!")
        print(f"📋 Project ID: {parsed.get('project_id', 'NOT FOUND')}")
        print(f"📋 Client Email: {parsed.get('client_email', 'NOT FOUND')}")
        print(f"📋 Has private_key: {'private_key' in parsed}")
        
        # Check private key format
        if 'private_key' in parsed:
            private_key = parsed['private_key']
            print(f"🔑 Private key length: {len(private_key)} chars")
            print(f"🔑 Starts with: {private_key[:50]}...")
            print(f"🔑 Contains \\n sequences: {'\\n' in private_key}")
            print(f"🔑 Contains actual newlines: {chr(10) in private_key}")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON is INVALID: {e}")
        print("🔍 Checking for common issues...")
        
        # Check for backslash issues
        if '\\n' in firebase_json and '\n' not in firebase_json:
            print("💡 Found \\n sequences - they might need to be actual newlines")
        
        if firebase_json.count('"') % 2 != 0:
            print("💡 Odd number of quotes - missing quote somewhere")

print("\n" + "=" * 50)