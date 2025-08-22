import os
import django
from io import BytesIO
import qrcode
import cloudinary.uploader

# --- Setup Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelMateBackend.settings")  # adjust to your project
django.setup()

from rooms.models import Room  # adjust to your app

# --- Generate QR function ---
def generate_qr(url, public_id):
    qr = qrcode.make(url)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    upload_result = cloudinary.uploader.upload(
        img_io,
        resource_type="image",
        public_id=public_id
    )
    return upload_result['secure_url']

# --- Main script ---
def generate_chat_qrs_for_all_rooms():
    rooms = Room.objects.select_related('hotel').all()
    for room in rooms:
        hotel_slug = room.hotel.slug or str(room.hotel.id)

        chat_url = f"https://hotelsmates.com/{hotel_slug}/messages/room/{room.room_number}/validate-chat-pin/"
        room.chat_pin_qr_code = generate_qr(chat_url, f"chat_pin/{hotel_slug}_room{room.room_number}")

        room.save()
        print(f"✅ Generated chat QR code for Room {room.room_number} at {hotel_slug}")

if __name__ == "__main__":
    generate_chat_qrs_for_all_rooms()
    print("🎉 Done generating chat QR codes for all rooms!")
