#!/usr/bin/env python
"""
Quick test script to verify the StaffRoomBookingDetailSerializer includes the required fields.
This bypasses Django test database creation issues.
"""

import os
import sys
import django

# Setup Django
sys.path.append('c:\\Users\\nlekk\\HMB\\HotelMateBackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from hotel.canonical_serializers import StaffRoomBookingDetailSerializer

def test_serializer_fields():
    """Test that the serializer has the required fields"""
    
    # Get the field names from the serializer
    serializer = StaffRoomBookingDetailSerializer()
    meta_fields = serializer.Meta.fields
    
    print("🔍 StaffRoomBookingDetailSerializer fields:")
    print("=" * 50)
    
    for field in sorted(meta_fields):
        print(f"  ✓ {field}")
    
    print("\n🎯 Checking required fields for NO-FALLBACKS contract:")
    print("=" * 50)
    
    required_fields = [
        'adults',                 # Occupancy info
        'children',               # Occupancy info  
        'party_complete',         # Party completion status
        'party_missing_count',    # Missing party count
        'precheckin_submitted_at',# Precheckin completion
        'precheckin_payload',     # Precheckin data
    ]
    
    missing_fields = []
    present_fields = []
    
    for field in required_fields:
        if field in meta_fields:
            present_fields.append(field)
            print(f"  ✅ {field} - PRESENT")
        else:
            missing_fields.append(field)
            print(f"  ❌ {field} - MISSING")
    
    print(f"\n📊 Summary:")
    print(f"  Present: {len(present_fields)}")
    print(f"  Missing: {len(missing_fields)}")
    
    if missing_fields:
        print(f"\n⚠️  Missing fields: {missing_fields}")
        return False
    else:
        print(f"\n✅ All required fields are present in the serializer!")
        return True

if __name__ == "__main__":
    success = test_serializer_fields()
    sys.exit(0 if success else 1)