from django.contrib import admin
from django.utils.html import format_html
from .models import ARAnchor

@admin.register(ARAnchor)
class ARAnchorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'floor', 'next_anchor', 'order', 'preview')
    readonly_fields = ('preview',)
    search_fields = ('name', 'hotel__name')

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return "(No image)"
    preview.short_description = "Image Preview"
