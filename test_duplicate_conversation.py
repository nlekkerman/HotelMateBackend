"""
Test to verify get_or_create_conversation prevents duplicates
"""

from staff_chat.models import StaffConversation
from staff.models import Staff
from hotel.models import Hotel

# Get hotel
hotel = Hotel.objects.get(slug='hotel-killarney')

# Get staff members (let's test with 2 staff)
staff1 = Staff.objects.filter(hotel=hotel, is_active=True).first()
staff2 = Staff.objects.filter(hotel=hotel, is_active=True).exclude(id=staff1.id).first()

print(f"Testing with Staff 1: {staff1.first_name} (ID: {staff1.id})")
print(f"Testing with Staff 2: {staff2.first_name} (ID: {staff2.id})")
print("-" * 50)

# Test 1: Create first conversation
conv1, created1 = StaffConversation.get_or_create_conversation(
    hotel=hotel,
    staff_list=[staff1, staff2],
    title=''
)
print(f"First call: Conversation ID={conv1.id}, Created={created1}")

# Test 2: Try to create again with SAME participants
conv2, created2 = StaffConversation.get_or_create_conversation(
    hotel=hotel,
    staff_list=[staff1, staff2],
    title=''
)
print(f"Second call: Conversation ID={conv2.id}, Created={created2}")

# Test 3: Try with participants in DIFFERENT order
conv3, created3 = StaffConversation.get_or_create_conversation(
    hotel=hotel,
    staff_list=[staff2, staff1],  # REVERSED order
    title=''
)
print(f"Third call (reversed): Conversation ID={conv3.id}, Created={created3}")

print("-" * 50)
if conv1.id == conv2.id == conv3.id:
    print("✅ SUCCESS: All returned same conversation!")
    print(f"   Conversation ID: {conv1.id}")
else:
    print("❌ FAIL: Different conversations returned!")
    print(f"   Conv1: {conv1.id}, Conv2: {conv2.id}, Conv3: {conv3.id}")

print("-" * 50)
print("\nNow testing GROUP conversation (3+ people)...")
staff3 = Staff.objects.filter(hotel=hotel, is_active=True).exclude(
    id__in=[staff1.id, staff2.id]
).first()
print(f"Staff 3: {staff3.first_name} (ID: {staff3.id})")
print("-" * 50)

# Test 4: Create group conversation
group1, g_created1 = StaffConversation.get_or_create_conversation(
    hotel=hotel,
    staff_list=[staff1, staff2, staff3],
    title='Test Group'
)
print(f"First group call: Conversation ID={group1.id}, Created={g_created1}")

# Test 5: Try to create same group again
group2, g_created2 = StaffConversation.get_or_create_conversation(
    hotel=hotel,
    staff_list=[staff1, staff2, staff3],
    title='Test Group'
)
print(f"Second group call: Conversation ID={group2.id}, Created={g_created2}")

# Test 6: Different order
group3, g_created3 = StaffConversation.get_or_create_conversation(
    hotel=hotel,
    staff_list=[staff3, staff1, staff2],  # Different order
    title='Test Group'
)
print(f"Third group call (reordered): Conversation ID={group3.id}, Created={g_created3}")

print("-" * 50)
if group1.id == group2.id == group3.id:
    print("✅ SUCCESS: All returned same group conversation!")
    print(f"   Group Conversation ID: {group1.id}")
else:
    print("❌ FAIL: Different group conversations returned!")
    print(f"   Group1: {group1.id}, Group2: {group2.id}, Group3: {group3.id}")
