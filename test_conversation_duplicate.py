"""
Test script to verify conversation duplication fix
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from staff_chat.models import StaffConversation
from hotel.models import Hotel
from staff.models import Staff

def test_conversation_creation():
    """Test that sharing to same people doesn't create duplicates"""
    
    print("🧪 Testing Conversation Duplication Fix\n")
    
    # Get test data
    try:
        hotel = Hotel.objects.first()
        if not hotel:
            print("❌ No hotel found in database")
            return
        
        staff_members = list(Staff.objects.filter(hotel=hotel, is_active=True)[:3])
        if len(staff_members) < 3:
            print(f"❌ Need at least 3 staff members, found {len(staff_members)}")
            return
        
        print(f"✅ Using hotel: {hotel.name}")
        print(f"✅ Found {len(staff_members)} staff members")
        for i, staff in enumerate(staff_members):
            print(f"   {i+1}. {staff.first_name} {staff.last_name} (ID: {staff.id})")
        print()
        
        # Test 1: Create 1-on-1 conversation
        print("📝 Test 1: 1-on-1 Conversation")
        staff_list_1on1 = [staff_members[0], staff_members[1]]
        conv1, created1 = StaffConversation.get_or_create_conversation(
            hotel=hotel,
            staff_list=staff_list_1on1,
            title=''
        )
        print(f"   First call: Conversation ID {conv1.id}, Created: {created1}")
        
        # Try again with same participants
        conv2, created2 = StaffConversation.get_or_create_conversation(
            hotel=hotel,
            staff_list=staff_list_1on1,
            title=''
        )
        print(f"   Second call: Conversation ID {conv2.id}, Created: {created2}")
        
        if conv1.id == conv2.id and not created2:
            print("   ✅ SUCCESS: Same conversation returned, no duplicate!")
        else:
            print("   ❌ FAILED: Different conversations or duplicate created!")
        print()
        
        # Test 2: Create group conversation
        print("📝 Test 2: Group Conversation (3 people)")
        staff_list_group = [staff_members[0], staff_members[1], staff_members[2]]
        conv3, created3 = StaffConversation.get_or_create_conversation(
            hotel=hotel,
            staff_list=staff_list_group,
            title='Test Group'
        )
        print(f"   First call: Conversation ID {conv3.id}, Created: {created3}")
        
        # Try again with same participants
        conv4, created4 = StaffConversation.get_or_create_conversation(
            hotel=hotel,
            staff_list=staff_list_group,
            title='Test Group'
        )
        print(f"   Second call: Conversation ID {conv4.id}, Created: {created4}")
        
        if conv3.id == conv4.id and not created4:
            print("   ✅ SUCCESS: Same conversation returned, no duplicate!")
        else:
            print("   ❌ FAILED: Different conversations or duplicate created!")
        print()
        
        # Test 3: Different order of participants
        print("📝 Test 3: Group with Same Participants (Different Order)")
        staff_list_reversed = [staff_members[2], staff_members[0], staff_members[1]]
        conv5, created5 = StaffConversation.get_or_create_conversation(
            hotel=hotel,
            staff_list=staff_list_reversed,
            title='Test Group'
        )
        print(f"   Call with reversed order: Conversation ID {conv5.id}, Created: {created5}")
        
        if conv5.id == conv3.id and not created5:
            print("   ✅ SUCCESS: Same conversation returned regardless of order!")
        else:
            print("   ❌ FAILED: Different conversation created for same participants!")
        print()
        
        # Summary
        print("=" * 60)
        print("📊 Test Summary:")
        total_convs = StaffConversation.objects.filter(hotel=hotel).count()
        print(f"   Total conversations in database: {total_convs}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_conversation_creation()
