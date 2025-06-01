import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")

import django
django.setup()

from rooms.models import Room

def regenerate_qr_codes(hotel_id=2):
    rooms = Room.objects.filter(hotel_id=hotel_id)
    count = 0

    for room in rooms:
        room.generate_qr_code('room_service')
        room.generate_qr_code('in_room_breakfast')
        count += 1
        print(f"Regenerated QR codes for Room {room.room_number}")

    print(f"\nDone. Regenerated QR codes for {count} rooms.")

if __name__ == "__main__":
    regenerate_qr_codes()
