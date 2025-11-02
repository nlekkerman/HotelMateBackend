from django.contrib import admin
from .models import Conversation, RoomMessage, GuestChatSession


# Inline for RoomMessage inside Conversation
class RoomMessageInline(admin.TabularInline):
    model = RoomMessage
    extra = 0
    readonly_fields = ("timestamp", "sender_type", "staff")
    fields = (
        "staff", "sender_type", "message", "timestamp",
        "read_by_staff", "staff_display_name", "staff_role_name"
    )
    ordering = ("-timestamp",)

    def save_new_instance(self, form, commit=True):
        obj = form.save(commit=False)
        obj.room = self.parent_model.room  # set room automatically
        if commit:
            obj.save()
        return obj

# Conversation admin
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "created_at", "updated_at", "participant_list", "has_unread")
    list_filter = ("room", "created_at", "updated_at")
    search_fields = ("room__room_number", "participants_staff__name")
    inlines = [RoomMessageInline]

    def participant_list(self, obj):
        return ", ".join([staff.name for staff in obj.participants_staff.all()])
    participant_list.short_description = "Participants"

# RoomMessage admin (optional separate admin if you want)
@admin.register(RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id", "conversation", "room", "sender_type", "staff",
        "staff_display_name", "timestamp", "read_by_staff"
    )
    list_filter = ("sender_type", "read_by_staff", "timestamp", "room")
    search_fields = ("message", "staff__name", "room__room_number")
    readonly_fields = ("timestamp",)


@admin.register(GuestChatSession)
class GuestChatSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_token', 'room', 'current_staff_handler',
        'is_active', 'created_at', 'last_activity', 'expires_at'
    ]
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = [
        'session_token', 'room__room_number',
        'current_staff_handler__first_name'
    ]
    readonly_fields = [
        'session_token', 'created_at', 'last_activity', 'last_ip'
    ]
    fieldsets = (
        ('Session Info', {
            'fields': (
                'session_token', 'conversation', 'room',
                'is_active', 'expires_at'
            )
        }),
        ('Staff Handler', {
            'fields': ('current_staff_handler',)
        }),
        ('Tracking', {
            'fields': (
                'created_at', 'last_activity', 'user_agent', 'last_ip'
            )
        }),
    )
