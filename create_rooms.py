import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")
django.setup()

from rooms.models import Room
from hotel.models import Hotel  # adjust import path to your Hotel model location

def create_rooms():
    created = 0
    skipped = 0

    hotel_id = 34
    try:
        hotel = Hotel.objects.get(id=hotel_id)
    except Hotel.DoesNotExist:
        print(f"Hotel with id {hotel_id} does not exist.")
        return

    room_numbers = (
        list(range(100, 163)) +
        list(range(200, 253)) +
        list(range(300, 353)) +
        list(range(400, 455))
    )

    for number in room_numbers:
        if Room.objects.filter(room_number=number, hotel=hotel).exists():
            print(f"Room {number} at hotel {hotel.name} already exists. Skipping.")
            skipped += 1
            continue

        room = Room(room_number=number, hotel=hotel)
        room.save()

        # Generate all three QR codes
        room.generate_qr_code('room_service')
        room.generate_qr_code('kids_entertainment')
        room.generate_qr_code('in_room_breakfast')

        created += 1
        print(f"Created Room {number} at hotel {hotel.name} with all QR Codes.")

    print(f"\nDone. {created} new rooms created. {skipped} rooms skipped.")

if __name__ == "__main__":
    create_rooms()
