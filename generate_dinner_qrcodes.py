import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")

import django
django.setup()

from rooms.models import Room
from bookings.models import Restaurant  # Adjust if your Restaurant model is elsewhere

def generate_dinner_qr_codes():
    rooms = Room.objects.select_related('hotel').all()
    count = 0
    skipped = 0

    for room in rooms:
        try:
            restaurant = Restaurant.objects.filter(hotel=room.hotel, is_active=True).first()

            if not restaurant:
                print(f"⚠️ No active restaurant for {room.hotel.name}, room {room.room_number}")
                skipped += 1
                continue

            # This function MUST save the QR to room.dinner_booking_qr_code
            qr_url = room.generate_booking_qr_for_restaurant(restaurant)

            if qr_url:
                print(f"✅ Saved QR for Room {room.room_number} at {room.hotel.name} [{restaurant.name}]")
                count += 1
            else:
                print(f"❌ QR not returned for Room {room.room_number} at {room.hotel.name}")
                skipped += 1

        except Exception as e:
            print(f"❌ Error for Room {room.room_number} at {room.hotel.name} — {e}")
            skipped += 1

    print(f"\n🎉 Done. Generated QR codes for {count} rooms. Skipped {skipped}.")

if __name__ == "__main__":
    generate_dinner_qr_codes()
