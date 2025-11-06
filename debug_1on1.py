"""Debug script to check 1-on-1 conversations"""

from staff_chat.models import StaffConversation
from hotel.models import Hotel
from staff.models import Staff
from django.db.models import Count

print("\n🔍 Debugging 1-on-1 Conversations\n")

hotel = Hotel.objects.first()
staff_members = list(Staff.objects.filter(hotel=hotel, is_active=True)[:2])

print(f"Hotel: {hotel.name}")
print(f"Staff 1: {staff_members[0].first_name} (ID: {staff_members[0].id})")
print(f"Staff 2: {staff_members[1].first_name} (ID: {staff_members[1].id})")
print()

# Check existing conversations
print("📋 Existing 1-on-1 conversations between them:")
convs = StaffConversation.objects.filter(
    hotel=hotel,
    is_group=False
).filter(
    participants=staff_members[0]
).filter(
    participants=staff_members[1]
).annotate(
    participant_count=Count('participants')
).filter(participant_count=2)

print(f"Found: {convs.count()} conversations")
for c in convs:
    parts = list(c.participants.all())
    print(f"  - Conv {c.id}: is_group={c.is_group}, participants={[p.first_name for p in parts]}")
print()

# Try to create
print("🧪 Calling get_or_create_conversation:")
staff_list = [staff_members[0], staff_members[1]]
conv, created = StaffConversation.get_or_create_conversation(
    hotel, staff_list, ''
)
print(f"Result: Conv {conv.id}, Created: {created}, is_group: {conv.is_group}")
parts = list(conv.participants.all())
print(f"Participants: {[p.first_name for p in parts]}")
print()

# Try again
print("🔁 Calling again (should reuse):")
conv2, created2 = StaffConversation.get_or_create_conversation(
    hotel, staff_list, ''
)
print(f"Result: Conv {conv2.id}, Created: {created2}, is_group: {conv2.is_group}")
print(f"Same conversation? {conv.id == conv2.id}")
