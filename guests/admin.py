from django.contrib import admin
from .models import Guest
from rooms.models import Room

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'email', 'get_room_number', 'get_hotel_name',
        'check_in_date', 'check_out_date', 'days_booked', 'id_pin', 'phone_number'
    )
    search_fields = (
        'first_name', 'last_name', 'email',
        'room__room_number', 'id_pin', 'phone_number'
    )
    list_filter = ('check_in_date', 'check_out_date')
    ordering = ('-check_in_date',)

    # Optimize DB queries: auto-follow foreign keys
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('room__hotel')

    # Custom field to avoid calling Room.__str__ (which may be expensive)
    def get_room_number(self, obj):
        return obj.room.room_number if obj.room else "-"
    get_room_number.short_description = 'Room'

    def get_hotel_name(self, obj):
        return obj.room.hotel.name if obj.room and obj.room.hotel else "-"
    get_hotel_name.short_description = 'Hotel'
    
    # Restrict dropdown to only occupied rooms
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "room":
            kwargs["queryset"] = Room.objects.filter(is_occupied=True).only("id", "room_number")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
