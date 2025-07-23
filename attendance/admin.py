from django.contrib import admin
from .models import StaffFace, ClockLog


@admin.register(StaffFace)
class StaffFaceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'hotel', 'created_at')
    list_filter = ('hotel',)
    search_fields = ('staff__first_name', 'staff__last_name', 'hotel__name')


@admin.register(ClockLog)
class ClockLogAdmin(admin.ModelAdmin):
    list_display = ('staff', 'hotel', 'time_in', 'time_out', 'verified_by_face')
    list_filter = ('hotel', 'verified_by_face')
    search_fields = ('staff__first_name', 'staff__last_name', 'hotel__name')
    readonly_fields = ('time_in',)
