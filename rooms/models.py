from django.db import models
import cloudinary
import cloudinary.uploader
import random
import string
import qrcode
from io import BytesIO


class Room(models.Model):
    room_number = models.IntegerField(unique=True)
    guest_id_pin = models.CharField(max_length=4, unique=True, null=True, blank=True)
    guests = models.ManyToManyField('guests.Guest', related_name='rooms', blank=True)
    is_occupied = models.BooleanField(default=False)

    room_service_qr_code = models.URLField(blank=True, null=True)
    in_room_breakfast_qr_code = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Room {self.room_number}"
    
    def generate_guest_pin(self):
        characters = string.ascii_lowercase + string.digits  # 'a-z' + '0-9'
        pin = ''.join(random.choices(characters, k=4))
        while Room.objects.filter(guest_id_pin=pin).exists():
            pin = ''.join(random.choices(characters, k=4))
        self.guest_id_pin = pin
        self.save()

    def generate_qr_code(self, qr_type="room_service"):
        path_map = {
            "room_service": f"https://dashing-klepon-d9f0c6.netlify.app/room/{self.room_number}/menu/",
            "in_room_breakfast": f"https://dashing-klepon-d9f0c6.netlify.app/breakfast/{self.room_number}",
        }


        qr_field_map = {
            "room_service": "room_service_qr_code",
            "in_room_breakfast": "in_room_breakfast_qr_code",
        }

        url = path_map.get(qr_type)
        if not url:
            return  # invalid type

        # Generate QR
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(img_io, resource_type="image")
        qr_url = upload_result['secure_url']

        # Save the result in the corresponding field
        setattr(self, qr_field_map[qr_type], qr_url)
        self.save()


