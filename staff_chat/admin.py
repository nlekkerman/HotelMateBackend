from django.contrib import admin
from .models import StaffConversation, StaffChatMessage


@admin.register(StaffConversation)
class StaffConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'hotel', 'get_participants', 'created_at', 'updated_at']
    list_filter = ['hotel', 'created_at']
    search_fields = ['participants__first_name', 'participants__last_name', 'hotel__name']
    filter_horizontal = ['participants']
    
    def get_participants(self, obj):
        return ", ".join([f"{p.first_name} {p.last_name}" for p in obj.participants.all()[:3]])
    get_participants.short_description = 'Participants'


@admin.register(StaffChatMessage)
class StaffChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_preview', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read', 'conversation__hotel']
    search_fields = ['message', 'sender__first_name', 'sender__last_name']
    readonly_fields = ['timestamp']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'
