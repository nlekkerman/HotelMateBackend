from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, RoomMessage, MessageAttachment, GuestConversationParticipant


# Inline for MessageAttachment inside RoomMessage
class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ("uploaded_at", "file_size", "file_type", "file_url_link")
    fields = ("file", "file_name", "file_type", "file_size", "file_url_link", "uploaded_at")
    
    def file_url_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return "-"
    file_url_link.short_description = "File URL"


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
        "staff_display_name", "timestamp", "read_by_staff", "has_attachments"
    )
    list_filter = ("sender_type", "read_by_staff", "timestamp", "room")
    search_fields = ("message", "staff__name", "room__room_number")
    readonly_fields = ("timestamp",)
    inlines = [MessageAttachmentInline]
    
    def has_attachments(self, obj):
        return obj.attachments.exists()
    has_attachments.boolean = True
    has_attachments.short_description = "Has Files"


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'message_preview', 'file_name', 'file_type',
        'file_size_display', 'file_url_link', 'uploaded_at'
    ]
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['file_name', 'message__message']
    readonly_fields = ['uploaded_at', 'file_size', 'mime_type', 'file_url_link']
    
    def message_preview(self, obj):
        """Show message preview"""
        msg = obj.message.message[:50]
        return f"{msg}..." if len(obj.message.message) > 50 else msg
    message_preview.short_description = "Message"
    
    def file_size_display(self, obj):
        """Display file size in human-readable format"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = "File Size"
    
    def file_url_link(self, obj):
        """Display clickable file URL"""
        if obj.file:
            if obj.is_image():
                return format_html(
                    '<a href="{}" target="_blank">'
                    '<img src="{}" style="max-height:50px;"/> View</a>',
                    obj.file.url, obj.file.url
                )
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.file.url
            )
        return "-"
    file_url_link.short_description = "File"


@admin.register(GuestConversationParticipant)
class GuestConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'staff', 'joined_at']
    list_filter = ['joined_at', 'staff__role', 'conversation__room__hotel']
    search_fields = ['staff__first_name', 'staff__last_name', 'conversation__room__room_number']
    readonly_fields = ['joined_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conversation__room__hotel', 'staff'
        )
