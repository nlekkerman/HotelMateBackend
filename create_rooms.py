import os
import django

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from rooms.models import Room

def create_rooms():
    created = 0
    skipped = 0

    room_numbers = (
        list(range(101, 153)) +
        list(range(201, 253)) +
        list(range(301, 353)) +
        list(range(401, 455))
    )

    for number in room_numbers:
        if Room.objects.filter(room_number=number).exists():
            print(f"Room {number} already exists. Skipping.")
            skipped += 1
            continue

        room = Room(room_number=number)
        room.save()

        # Generate all three QR codes
        room.generate_qr_code('room_service')
        room.generate_qr_code('kids_entertainment')
        room.generate_qr_code('in_room_breakfast')

        created += 1
        print(f"Created Room {number} with all QR Codes.")

    print(f"\nDone. {created} new rooms created. {skipped} rooms skipped.")

if __name__ == "__main__":
    create_rooms()
