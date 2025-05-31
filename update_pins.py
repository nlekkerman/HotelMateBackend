import os
import django
import random
import string
from django.db.models import Q

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from rooms.models import Room


def generate_unique_pin(existing_pins, length=4):
    chars = string.ascii_lowercase + string.digits
    while True:
        pin = ''.join(random.choices(chars, k=length))
        if pin not in existing_pins:
            return pin


def update_guest_id_pins_and_generate_qr():
    updated = 0
    skipped = 0

    existing_pins = set(
        Room.objects.exclude(guest_id_pin__isnull=True)
        .exclude(guest_id_pin__exact="")
        .values_list('guest_id_pin', flat=True)
    )

    # Filter rooms only for hotel id 34 and missing/empty guest_id_pin
    rooms = Room.objects.filter(hotel_id=34).filter(
            Q(guest_id_pin__isnull=True) | Q(guest_id_pin__exact="")
    )

    for room in rooms:
        pin = generate_unique_pin(existing_pins)
        room.guest_id_pin = pin
        room.save()
        existing_pins.add(pin)

        # Generate all QR codes for this room
        room.generate_qr_code('room_service')
        room.generate_qr_code('in_room_breakfast')

        updated += 1
        print(f"Updated Room {room.room_number} with PIN: {pin} and generated QR codes.")

    print(f"\nDone. {updated} rooms updated. {skipped} skipped.")


if __name__ == "__main__":
    update_guest_id_pins_and_generate_qr()
