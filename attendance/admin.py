from django.contrib import admin
from django.utils.html import format_html
from .models import StaffFace, ClockLog


@admin.register(StaffFace)
class StaffFaceAdmin(admin.ModelAdmin):
    list_display   = ('staff', 'hotel', 'created_at', 'image_preview')
    list_filter    = ('hotel',)
    search_fields  = ('staff__first_name', 'staff__last_name', 'hotel__name')
    readonly_fields = ('created_at', 'encoding', 'image_preview')
    fields = (
        'hotel',
        'staff',
        'image',
        'image_preview',
        'encoding',
        'created_at',
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:100px; max-width:100px;"/>',
                obj.image.url
            )
        return "(no image)"
    image_preview.short_description = 'Preview'


@admin.register(ClockLog)
class ClockLogAdmin(admin.ModelAdmin):
    list_display   = ('staff', 'hotel', 'time_in', 'time_out', 'verified_by_face')
    list_filter    = ('hotel', 'verified_by_face')
    search_fields  = ('staff__first_name', 'staff__last_name', 'hotel__name')
    readonly_fields = ('time_in',)

    # If you’d like to see location_note or verified_by_face on the detail page:
    fields = (
        'hotel',
        'staff',
        'time_in',
        'time_out',
        'verified_by_face',
        'location_note',
    )
