"""Check participant counts"""

from staff_chat.models import StaffConversation
from hotel.models import Hotel
from staff.models import Staff
from django.db.models import Count

hotel = Hotel.objects.first()
staff_members = list(Staff.objects.filter(hotel=hotel, is_active=True)[:2])

print(f"\n🔍 Checking conversations with both {staff_members[0].first_name} and {staff_members[1].first_name}\n")

convs = StaffConversation.objects.filter(
    hotel=hotel,
    is_group=False
).filter(
    participants=staff_members[0]
).filter(
    participants=staff_members[1]
).annotate(
    participant_count=Count('participants')
)

print(f"Found {convs.count()} conversations")
for c in convs:
    parts = list(c.participants.all())
    print(f"Conv {c.id}: is_group={c.is_group}, " +
          f"annotated_count={c.participant_count}, " +
          f"actual_count={len(parts)}, " +
          f"participants={[p.first_name for p in parts]}")
