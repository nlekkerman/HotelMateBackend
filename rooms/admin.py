from django.contrib import admin
from django.utils.html import format_html
from .models import Room, RoomType
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
            # Always regenerate Chat PIN QR (overwrite Cloudinary + DB field)
            room.generate_chat_pin_qr_code()

        self.message_user(request, f"✅ Regenerated Chat PIN QR for {queryset.count()} room(s).")

    generate_qr_for_selected_rooms.short_description = "Generate Chat PIN QR for selected rooms"

admin.site.register(Room, RoomAdmin)


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'hotel',
        'code',
        'starting_price_from',
        'currency',
        'max_occupancy',
        'is_active',
        'sort_order',
        'photo_preview'
    )
    list_filter = ('hotel', 'is_active', 'currency')
    search_fields = ('name', 'code', 'hotel__name')
    list_editable = ('is_active', 'sort_order')
    ordering = ('sort_order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('hotel', 'code', 'name')
        }),
        ('Room Details', {
            'fields': (
                'short_description',
                'max_occupancy',
                'bed_setup',
                'photo'
            )
        }),
        ('Pricing', {
            'fields': ('starting_price_from', 'currency')
        }),
        ('Booking', {
            'fields': (
                'booking_code',
                'booking_url',
                'availability_message'
            )
        }),
        ('Display Settings', {
            'fields': ('is_active', 'sort_order')
        }),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.photo.url
            )
        return "-"
    photo_preview.short_description = "Photo"
