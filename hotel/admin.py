from django.contrib import admin
from .models import Hotel

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('name',),
        'subdomain': ('name',)  # auto-fill subdomain from name
    }
    list_display = ('name', 'slug', 'subdomain')
    search_fields = ('name', 'slug', 'subdomain')
