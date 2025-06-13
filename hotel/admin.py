# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Hotel

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ('name',),
        'subdomain': ('name',),
    }
    list_display = (
        'name',
        'slug',
        'subdomain',
        'logo_preview',   # <-- custom column
    )
    search_fields = (
        'name',
        'slug',
        'subdomain',
        # remove 'logo'
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px;"/>',
                obj.logo.url
            )
        return "-"
    logo_preview.short_description = "Logo"
