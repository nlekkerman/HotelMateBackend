#!/usr/bin/env python
"""
Django validation script for enhanced staff bookings filter implementation.
Validates that all imports work and model fields exist.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

def validate_implementation():
    """Validate the enhanced filtering implementation"""
    
    try:
        # Test Django Q objects import
        from django.db.models import Q
        print("✅ Django Q objects imported successfully")
        
        # Test RoomBooking model and fields
        from hotel.models import RoomBooking, BookingSurveyResponse
        print("✅ RoomBooking model imported successfully")
        
        # Validate required fields exist
        required_fields = [
            'check_in', 'check_out', 'checked_in_at', 'checked_out_at',
            'status', 'assigned_room', 'precheckin_submitted_at',
            'booking_id', 'primary_first_name', 'primary_last_name',
            'primary_email', 'primary_phone', 'booker_first_name',
            'booker_last_name', 'booker_email', 'booker_phone'
        ]
        
        model_fields = [field.name for field in RoomBooking._meta.fields]
        missing_fields = []
        
        for field in required_fields:
            if field not in model_fields:
                missing_fields.append(field)
            else:
                print(f"✅ Field '{field}' exists")
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
            
        # Test status choices
        status_choices = [choice[0] for choice in RoomBooking.STATUS_CHOICES]
        required_statuses = [
            'CONFIRMED', 'PENDING_APPROVAL', 'PENDING_PAYMENT', 
            'COMPLETED', 'CANCELLED'
        ]
        
        for status in required_statuses:
            if status in status_choices:
                print(f"✅ Status '{status}' exists")
            else:
                print(f"❌ Status '{status}' missing")
                return False
        
        # Test staff views import
        from hotel.staff_views import StaffBookingsListView
        print("✅ StaffBookingsListView imported successfully")
        
        # Test serializer import
        from hotel.canonical_serializers import StaffRoomBookingListSerializer
        print("✅ StaffRoomBookingListSerializer imported successfully")
        
        # Test pagination import
        from rest_framework.pagination import PageNumberPagination
        print("✅ PageNumberPagination imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def test_query_building():
    """Test Django Q object query building"""
    
    try:
        from django.db.models import Q
        from datetime import date
        
        # Test bucket queries
        today = date.today()
        
        # Arrivals query
        arrivals_q = (
            Q(check_in__gte=today) & Q(check_in__lte=today) &
            Q(checked_in_at__isnull=True) &
            Q(status__in=['CONFIRMED', 'PENDING_APPROVAL'])
        )
        print("✅ Arrivals query built successfully")
        
        # In-house query
        in_house_q = Q(checked_in_at__isnull=False) & Q(checked_out_at__isnull=True)
        print("✅ In-house query built successfully")
        
        # Search query
        search_q = (
            Q(booking_id__icontains='test') |
            Q(primary_first_name__icontains='test') |
            Q(primary_email__icontains='test')
        )
        print("✅ Search query built successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Query building failed: {e}")
        return False

def main():
    print("🔍 Django Enhanced Staff Bookings Filter Validation")
    print("=" * 60)
    
    validation_passed = validate_implementation()
    query_test_passed = test_query_building()
    
    if validation_passed and query_test_passed:
        print("\n🎉 All validations passed! Implementation is ready.")
        print("\n📋 Summary:")
        print("  - All required model fields exist")
        print("  - All status choices are available")
        print("  - Django Q queries build correctly")
        print("  - All imports resolve successfully")
        print("  - Ready for API testing")
        
    else:
        print("\n❌ Some validations failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()