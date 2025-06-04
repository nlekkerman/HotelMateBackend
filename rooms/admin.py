from django.contrib import admin
from django.utils.html import format_html
from .models import Room

class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number', 'hotel', 'is_occupied', 'get_guests_count',
        'room_service_qr_link', 'breakfast_qr_link', 'dinner_qr_link',
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

    def generate_qr_buttons(self, obj):
        buttons = []
        if not obj.room_service_qr_code:
            buttons.append('Room Service')
        if not obj.in_room_breakfast_qr_code:
            buttons.append('Breakfast')
        if not obj.dinner_booking_qr_code:
            buttons.append('Dinner')
        return ", ".join(buttons) if buttons else "All Generated"
    generate_qr_buttons.short_description = "Missing QR Codes"

    # ❌ Removed generate_all_qrs
    actions = []  # No admin action anymore

admin.site.register(Room, RoomAdmin)
