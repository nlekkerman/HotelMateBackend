#!/usr/bin/env python
"""
Direct unit test for ConflictError handling.
"""
import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from room_bookings.services.overstay import ConflictError


def test_conflict_error():
    """Test the ConflictError exception structure directly."""
    print("🧪 Testing ConflictError structure...")
    
    # Create a sample ConflictError
    conflicts = [
        {
            'room_id': 123,
            'conflicting_booking_id': 'BK-2026-001',
            'starts': '2026-01-24',
            'ends': '2026-01-26'
        }
    ]
    
    suggestions = [
        {
            'room_id': 124,
            'room_number': '102',
            'room_type': 'Standard Room'
        },
        {
            'room_id': 125,
            'room_number': '103', 
            'room_type': 'Standard Room'
        }
    ]
    
    # Create the exception
    error = ConflictError(
        "Extension conflicts with an incoming reservation for this room.",
        conflicts,
        suggestions
    )
    
    print(f"✓ ConflictError created")
    print(f"  Message: {error.message}")
    print(f"  str(error): {str(error)}")
    print(f"  Conflicts: {error.conflicts}")
    print(f"  Suggestions: {error.suggestions}")
    
    # Simulate the view response
    response_data = {
        "detail": str(error),
        "conflicts": error.conflicts,
        "suggested_rooms": error.suggestions
    }
    
    import json
    response_json = json.dumps(response_data)
    print(f"\n📦 Response size: {len(response_json)} bytes")
    print("📋 Response structure:")
    print(json.dumps(response_data, indent=2))
    
    # Validate structure
    assert "detail" in response_data
    assert "conflicts" in response_data
    assert "suggested_rooms" in response_data
    assert isinstance(response_data["conflicts"], list)
    assert isinstance(response_data["suggested_rooms"], list)
    assert len(response_data["conflicts"]) == 1
    assert len(response_data["suggested_rooms"]) == 2
    
    print("\n✅ ConflictError structure is correct!")
    return True


if __name__ == "__main__":
    success = test_conflict_error()
    print(f"\n🎯 Result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)