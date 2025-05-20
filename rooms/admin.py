from django.contrib import admin
from django.http import HttpResponseRedirect
from .models import  Room
from django.utils.html import mark_safe, format_html

class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'room_number', 'is_occupied', 'get_guests_count',
        'room_service_qr_link',  'breakfast_qr_link',
        'generate_qr_buttons'
    )

    search_fields = ('room_number',)
    list_filter = ('is_occupied',)

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

    def generate_qr_buttons(self, obj):
        buttons = []
        if not obj.room_service_qr_code:
            buttons.append('Room Service')
        
        if not obj.in_room_breakfast_qr_code:
            buttons.append('Breakfast')
        return ", ".join(buttons) if buttons else "All Generated"
    generate_qr_buttons.short_description = "Missing QR Codes"

    def generate_all_qrs(self, request, queryset):
        for room in queryset:
            room.generate_qr_code("room_service")
            room.generate_qr_code("in_room_breakfast")
        self.message_user(request, "All QR codes generated successfully.")

    actions = ['generate_all_qrs']


# Register Room model with the custom admin interface
admin.site.register(Room, RoomAdmin)


