"""
Quick test for conversation duplication fix
Run with: python manage.py shell < test_conv_fix.py
"""

from staff_chat.models import StaffConversation
from hotel.models import Hotel
from staff.models import Staff

print("\n🧪 Testing Conversation Duplication Fix\n")

# Get test data
hotel = Hotel.objects.first()
if not hotel:
    print("❌ No hotel found")
    exit()

staff_members = list(Staff.objects.filter(
    hotel=hotel, 
    is_active=True
)[:3])

if len(staff_members) < 3:
    print(f"❌ Need 3 staff, found {len(staff_members)}")
    exit()

print(f"✅ Hotel: {hotel.name}")
print(f"✅ Staff: {staff_members[0].first_name}, " + 
      f"{staff_members[1].first_name}, {staff_members[2].first_name}\n")

# Test 1: 1-on-1
print("📝 Test 1: 1-on-1 Conversation")
list1 = [staff_members[0], staff_members[1]]
conv1, created1 = StaffConversation.get_or_create_conversation(
    hotel, list1, ''
)
print(f"   First: ID {conv1.id}, Created: {created1}")

conv2, created2 = StaffConversation.get_or_create_conversation(
    hotel, list1, ''
)
print(f"   Second: ID {conv2.id}, Created: {created2}")

if conv1.id == conv2.id and not created2:
    print("   ✅ SUCCESS: No duplicate!\n")
else:
    print("   ❌ FAILED: Duplicate created!\n")

# Test 2: Group
print("📝 Test 2: Group Conversation (3 people)")
list_group = staff_members
conv3, created3 = StaffConversation.get_or_create_conversation(
    hotel, list_group, 'Test Group'
)
print(f"   First: ID {conv3.id}, Created: {created3}")

conv4, created4 = StaffConversation.get_or_create_conversation(
    hotel, list_group, 'Test Group'
)
print(f"   Second: ID {conv4.id}, Created: {created4}")

if conv3.id == conv4.id and not created4:
    print("   ✅ SUCCESS: No duplicate!\n")
else:
    print("   ❌ FAILED: Duplicate created!\n")

# Test 3: Different order
print("📝 Test 3: Same Participants (Different Order)")
list_rev = [staff_members[2], staff_members[0], staff_members[1]]
conv5, created5 = StaffConversation.get_or_create_conversation(
    hotel, list_rev, 'Test Group'
)
print(f"   Reversed: ID {conv5.id}, Created: {created5}")

if conv5.id == conv3.id and not created5:
    print("   ✅ SUCCESS: Same conversation!\n")
else:
    print("   ❌ FAILED: New conversation!\n")

print("=" * 50)
total = StaffConversation.objects.filter(hotel=hotel).count()
print(f"📊 Total conversations: {total}")
print("=" * 50)
