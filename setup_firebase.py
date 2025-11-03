"""
Setup Firebase credentials for local development
Run this script after downloading firebase-service-account.json
"""
import os
import shutil

# Source file (from Downloads)
source = r'c:\Users\nlekk\Downloads\firebase-service-account.json.json'

# Destination (project root)
destination = r'c:\Users\nlekk\HMB\HotelMateBackend\firebase-service-account.json'

if os.path.exists(source):
    # Rename and move the file
    shutil.copy(source, destination)
    print(f"✅ Firebase credentials copied to: {destination}")
    print("✅ File is in .gitignore - will NOT be committed to Git")
    
    # Optional: remove the original
    try:
        os.remove(source)
        print(f"✅ Removed original file from Downloads")
    except:
        print(f"⚠️ Original file still in Downloads - you can delete it manually")
        
    print("\n🎉 Firebase setup complete!")
    print("\nNext steps:")
    print("1. Test locally by creating a room service order")
    print("2. Set up Heroku config var with the JSON content")
    
else:
    print(f"❌ File not found: {source}")
    print("\nPlease:")
    print("1. Download the Firebase service account JSON from Firebase Console")
    print("2. Save it to your Downloads folder")
    print("3. Run this script again")
