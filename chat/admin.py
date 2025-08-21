from django.contrib import admin
from .models import RoomMessage

@admin.register(RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'message_preview', 'timestamp', 'read_by_staff')
    list_filter = ('room', 'read_by_staff')
    search_fields = ('room__room_number', 'message', 'sender')
    ordering = ('-timestamp',)

    def message_preview(self, obj):
        return obj.message[:50]
    message_preview.short_description = 'Message'
