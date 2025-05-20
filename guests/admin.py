from django.contrib import admin
from .models import Guest

class GuestAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'email', 'room', 
        'check_in_date', 'check_out_date', 
        'days_booked', 'id_pin', 'phone_number'
    )
    search_fields = (
        'first_name', 'last_name', 'email', 
        'room__room_number', 'id_pin', 'phone_number'
    )
    list_filter = ('room', 'check_in_date', 'check_out_date')
    ordering = ('-check_in_date',)

admin.site.register(Guest, GuestAdmin)
