#!/usr/bin/env python
"""
Check if the frontend token e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0
matches the database token hash 2832bba5a6df6f4595eb1013bb36b19db46827f5da370d6a8f33d4a572efa846
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from common.guest_access import hash_token

def check_token_match():
    # Frontend token from logs
    frontend_token = "e5hMCAwE1XmvDFIkCU9RQX9FHQi2hFcDlnyxxOofPx0"
    
    # Database hash from our previous query
    database_hash = "2832bba5a6df6f4595eb1013bb36b19db46827f5da370d6a8f33d4a572efa846"
    
    # Hash the frontend token
    frontend_hash = hash_token(frontend_token)
    
    print(f"🔍 Frontend token: {frontend_token}")
    print(f"🔍 Frontend hash:  {frontend_hash}")
    print(f"🔍 Database hash:  {database_hash}")
    print(f"🔍 Match: {frontend_hash == database_hash}")
    
    if frontend_hash == database_hash:
        print("✅ SAME TOKEN! The frontend token IS the correct token!")
        print("❓ So why is it returning 401?")
        
        # Test the token resolution directly
        print(f"\n🧪 Token hash matches — resolve_guest_chat_context was removed.")
        print(f"   Use bootstrap → session grant flow for chat access.")
            
    else:
        print("❌ DIFFERENT TOKENS! Frontend token doesn't match database.")

if __name__ == "__main__":
    check_token_match()