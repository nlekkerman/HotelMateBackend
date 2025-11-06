"""Debug the filter query"""

from staff_chat.models import StaffConversation
from hotel.models import Hotel
from staff.models import Staff
from django.db.models import Count

print("\n🔍 Testing Filter Query\n")

hotel = Hotel.objects.first()
staff_members = list(Staff.objects.filter(hotel=hotel, is_active=True)[:2])

print(f"Staff 1: {staff_members[0].first_name} (ID: {staff_members[0].id})")
print(f"Staff 2: {staff_members[1].first_name} (ID: {staff_members[1].id})")
print()

# Create a test conversation
print("📝 Creating test conversation...")
conv = StaffConversation.objects.create(
    hotel=hotel,
    title='',
    is_group=False,
    created_by=staff_members[0],
    has_unread=False
)
conv.participants.add(staff_members[0], staff_members[1])
print(f"Created Conv {conv.id}, is_group={conv.is_group}")
print(f"Participants: {conv.participants.count()}")
print()

# Now test the query
print("🔍 Testing query step by step:")

q1 = StaffConversation.objects.filter(hotel=hotel, is_group=False)
print(f"Step 1 - Filter by hotel and is_group=False: {q1.count()} results")

q2 = q1.filter(participants=staff_members[0])
print(f"Step 2 - Filter by participant 1: {q2.count()} results")

q3 = q2.filter(participants=staff_members[1])
print(f"Step 3 - Filter by participant 2: {q3.count()} results")

q4 = q3.annotate(participant_count=Count('participants'))
print(f"Step 4 - Annotate participant count: {q4.count()} results")

q5 = q4.filter(participant_count=2)
print(f"Step 5 - Filter participant_count=2: {q5.count()} results")
print()

if q5.exists():
    found = q5.first()
    print(f"✅ Found conversation {found.id}")
else:
    print("❌ No conversation found!")
