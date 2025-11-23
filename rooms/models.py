from django.db import models
from cloudinary.models import CloudinaryField
import cloudinary.uploader
import random
import string
import qrcode
from io import BytesIO


class Room(models.Model):
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)
    room_number = models.IntegerField()
    guest_id_pin = models.CharField(max_length=4, unique=True, null=True, blank=True)
    guests = models.ManyToManyField('guests.Guest', related_name='rooms', blank=True)
    is_occupied = models.BooleanField(default=False)

    room_service_qr_code = models.URLField(blank=True, null=True)
    in_room_breakfast_qr_code = models.URLField(blank=True, null=True)
    dinner_booking_qr_code = models.URLField(blank=True, null=True)
    chat_pin_qr_code = models.URLField(blank=True, null=True)
    
    # FCM token for anonymous guest in this room
    guest_fcm_token = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Firebase Cloud Messaging token for push notifications to guest's device"
    )
    
    class Meta:
        unique_together = ('hotel', 'room_number')

    def __str__(self):
        hotel_name = self.hotel.name if self.hotel else "No Hotel"
        return f"Room {self.room_number} at {hotel_name}"

    def generate_guest_pin(self):
        characters = string.ascii_lowercase + string.digits
        pin = ''.join(random.choices(characters, k=4))
        while Room.objects.filter(guest_id_pin=pin).exists():
            pin = ''.join(random.choices(characters, k=4))
        self.guest_id_pin = pin
        self.save()

    def generate_qr_code(self, qr_type="room_service"):
        if not self.hotel:
            return  # Can't generate QR without hotel

        # Use hotel slug or ID in URL path instead of subdomain
        hotel_identifier = self.hotel.slug if self.hotel.slug else str(self.hotel.id)

        path_map = {
            "room_service": f"https://hotelsmates.com/room_services/{hotel_identifier}/room/{self.room_number}/menu/",
            "in_room_breakfast": f"https://hotelsmates.com/room_services/{hotel_identifier}/room/{self.room_number}/breakfast/",
        }

        qr_field_map = {
            "room_service": "room_service_qr_code",
            "in_room_breakfast": "in_room_breakfast_qr_code",
        }

        url = path_map.get(qr_type)
        if not url:
            return

        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        upload_result = cloudinary.uploader.upload(img_io, resource_type="image")
        qr_url = upload_result['secure_url']

        setattr(self, qr_field_map[qr_type], qr_url)
        self.save()

    def generate_booking_qr_for_restaurant(self, restaurant):
        """
        Generates and uploads a QR code for a booking at a specific restaurant
        for this room. Saves the Cloudinary URL to dinner_booking_qr_code and returns it.
        """

        if not self.hotel or not restaurant:
            return None

        hotel_slug = self.hotel.slug or str(self.hotel.id)
        restaurant_slug = restaurant.slug

        url = f"https://hotelsmates.com/guest-booking/{hotel_slug}/restaurant/{restaurant_slug}/room/{self.room_number}/"

        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"booking_qr/{hotel_slug}_room{self.room_number}_{restaurant_slug.replace('-', '_')}"
        )

        qr_url = upload_result['secure_url']

        # ✅ Save to the Room model
        self.dinner_booking_qr_code = qr_url
        self.save()

        return qr_url
    
    def generate_chat_pin_qr_code(self):
        if not self.hotel:
            return None

        hotel_slug = self.hotel.slug or str(self.hotel.id)
        url = f"https://hotelsmates.com/chat/{hotel_slug}/messages/room/{self.room_number}/validate-chat-pin/"

        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        # ✅ same public_id every time = Cloudinary overwrites old QR
        upload_result = cloudinary.uploader.upload(
            img_io,
            resource_type="image",
            public_id=f"chat_pin_qr/{hotel_slug}_room{self.room_number}",
            overwrite=True
        )

        qr_url = upload_result['secure_url']
        self.chat_pin_qr_code = qr_url
        self.save()

        return qr_url


class RoomType(models.Model):
    """
    Marketing information about room categories (not live inventory).
    Used for public hotel pages to display available room types.
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='room_types'
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional identifier (e.g., 'STD', 'DLX')"
    )
    name = models.CharField(
        max_length=200,
        help_text="e.g., 'Deluxe Suite', 'Standard Room'"
    )
    short_description = models.TextField(
        blank=True,
        help_text="Brief marketing description"
    )
    max_occupancy = models.PositiveSmallIntegerField(
        default=2,
        help_text="Maximum number of guests"
    )
    bed_setup = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., 'King Bed', '2 Queen Beds'"
    )
    photo = CloudinaryField(
        "room_type_photo",
        blank=True,
        null=True,
        help_text="Room type photo"
    )
    starting_price_from = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Marketing 'from' price per night"
    )
    currency = models.CharField(
        max_length=3,
        default="EUR",
        help_text="Currency code (e.g., EUR, USD, GBP)"
    )
    booking_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Code for booking system integration"
    )
    booking_url = models.URLField(
        blank=True,
        help_text="Deep link to book this room type"
    )
    availability_message = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., 'High demand', 'Last rooms available'"
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this room type is shown publicly"
    )

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Room Type"
        verbose_name_plural = "Room Types"

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"
