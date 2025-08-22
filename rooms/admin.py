from django.contrib import admin
from django.utils.html import format_html
from .models import Room
import qrcode
from io import BytesIO
import cloudinary.uploader
import string
import random

class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number', 'hotel', 'is_occupied', 'get_guests_count',
        'room_service_qr_link', 'breakfast_qr_link', 'dinner_qr_link',
        'chat_pin_qr_link',  # <-- Chat PIN QR
        'generate_qr_buttons'
    )

    search_fields = ('room_number', 'hotel__name')
    list_filter = ('is_occupied', 'hotel')

    def get_guests_count(self, obj):
        return obj.guests.count()
    get_guests_count.short_description = 'Number of Guests'

    def room_service_qr_link(self, obj):
        if obj.room_service_qr_code:
            return format_html('<a href="{}" target="_blank">Room Service</a>', obj.room_service_qr_code)
        return 'Not Generated'
    room_service_qr_link.short_description = 'Room Service QR'

    def breakfast_qr_link(self, obj):
        if obj.in_room_breakfast_qr_code:
            return format_html('<a href="{}" target="_blank">Breakfast</a>', obj.in_room_breakfast_qr_code)
        return 'Not Generated'
    breakfast_qr_link.short_description = 'Breakfast QR'

    def dinner_qr_link(self, obj):
        if obj.dinner_booking_qr_code:
            return format_html('<a href="{}" target="_blank">Dinner</a>', obj.dinner_booking_qr_code)
        return 'Not Generated'
    dinner_qr_link.short_description = 'Dinner QR'

    def chat_pin_qr_link(self, obj):
        if obj.chat_pin_qr_code:
            return format_html('<a href="{}" target="_blank">Chat PIN</a>', obj.chat_pin_qr_code)
        return 'Not Generated'
    chat_pin_qr_link.short_description = 'Chat PIN QR'

    def generate_qr_buttons(self, obj):
        buttons = []
        if not obj.room_service_qr_code:
            buttons.append('Room Service')
        if not obj.in_room_breakfast_qr_code:
            buttons.append('Breakfast')
        if not obj.dinner_booking_qr_code:
            buttons.append('Dinner')
        if not obj.chat_pin_qr_code:
            buttons.append('Chat PIN')
        return ", ".join(buttons) if buttons else "All Generated"
    generate_qr_buttons.short_description = "Missing QR Codes"

    # --- Admin action ---
    actions = ['generate_qr_for_selected_rooms']

    def generate_qr_for_selected_rooms(self, request, queryset):
        for room in queryset:
            # 1️⃣ Generate chat PIN if missing
            if not room.guest_id_pin:
                characters = string.ascii_lowercase + string.digits
                pin = ''.join(random.choices(characters, k=4))
                while Room.objects.filter(guest_id_pin=pin).exists():
                    pin = ''.join(random.choices(characters, k=4))
                room.guest_id_pin = pin

            # 2️⃣ Generate Chat PIN QR
            if not room.chat_pin_qr_code:
                chat_url = f"https://hotelsmates.com/chat/{room.hotel.slug}/messages/room/{room.room_number}/validate-chat-pin/"
                qr = qrcode.make(chat_url)
                img_io = BytesIO()
                qr.save(img_io, 'PNG')
                img_io.seek(0)
                upload_result = cloudinary.uploader.upload(
                    img_io,
                    resource_type="image",
                    public_id=f"chat_qr/{room.hotel.slug}_room{room.room_number}"
                )
                room.chat_pin_qr_code = upload_result['secure_url']

            room.save()

        self.message_user(request, f"✅ Generated chat PIN QR for {queryset.count()} room(s).")
    generate_qr_for_selected_rooms.short_description = "Generate Chat PIN QR for selected rooms"

admin.site.register(Room, RoomAdmin)
