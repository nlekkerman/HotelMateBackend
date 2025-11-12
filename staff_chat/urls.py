from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import StaffListViewSet, StaffConversationViewSet
from . import views_messages, views_attachments

router = DefaultRouter()

# Staff chat URLs are nested under hotel_slug
urlpatterns = [
    # Staff list for chat UI
    path(
        '<slug:hotel_slug>/staff-list/',
        StaffListViewSet.as_view({'get': 'list'}),
        name='staff-list'
    ),
    
    # Conversations
    path(
        '<slug:hotel_slug>/conversations/',
        StaffConversationViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='conversation-list'
    ),
    path(
        '<slug:hotel_slug>/conversations/for-forwarding/',
        StaffConversationViewSet.as_view({
            'get': 'for_forwarding'
        }),
        name='conversation-for-forwarding'
    ),
    path(
        '<slug:hotel_slug>/conversations/unread-count/',
        StaffConversationViewSet.as_view({
            'get': 'unread_count'
        }),
        name='conversation-unread-count'
    ),
    path(
        '<slug:hotel_slug>/conversations/bulk-mark-as-read/',
        StaffConversationViewSet.as_view({
            'post': 'bulk_mark_as_read'
        }),
        name='conversation-bulk-mark-as-read'
    ),
    path(
        '<slug:hotel_slug>/conversations/<int:pk>/',
        StaffConversationViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='conversation-detail'
    ),
    
    # ==================== MESSAGE ENDPOINTS ====================
    
    # Send message (NEW - replaces old send_message)
    path(
        '<slug:hotel_slug>/conversations/<int:conversation_id>/send-message/',
        views_messages.send_message,
        name='send-message'
    ),
    
    # Get messages with pagination
    path(
        '<slug:hotel_slug>/conversations/<int:conversation_id>/messages/',
        views_messages.get_conversation_messages,
        name='conversation-messages'
    ),
    
    # Mark individual message as read
    path(
        '<slug:hotel_slug>/messages/<int:message_id>/mark-as-read/',
        views_messages.mark_message_as_read,
        name='mark-message-as-read'
    ),
    
    # Edit message
    path(
        '<slug:hotel_slug>/messages/<int:message_id>/edit/',
        views_messages.edit_message,
        name='edit-message'
    ),
    
    # Delete message
    path(
        '<slug:hotel_slug>/messages/<int:message_id>/delete/',
        views_messages.delete_message,
        name='delete-message'
    ),
    
    # Add reaction to message
    path(
        '<slug:hotel_slug>/messages/<int:message_id>/react/',
        views_messages.add_reaction,
        name='add-reaction'
    ),
    
    # Remove reaction from message
    path(
        '<slug:hotel_slug>/messages/<int:message_id>/react/<str:emoji>/',
        views_messages.remove_reaction,
        name='remove-reaction'
    ),
    
    # Forward message to conversations
    path(
        '<slug:hotel_slug>/messages/<int:message_id>/forward/',
        views_messages.forward_message,
        name='forward-message'
    ),
    
    # ==================== FILE ATTACHMENT ENDPOINTS ====================
    
    # Upload file attachments
    path(
        '<slug:hotel_slug>/conversations/<int:conversation_id>/upload/',
        views_attachments.upload_attachments,
        name='upload-attachments'
    ),
    
    # Delete attachment
    path(
        '<slug:hotel_slug>/attachments/<int:attachment_id>/delete/',
        views_attachments.delete_attachment,
        name='delete-attachment'
    ),
    
    # Get attachment URL
    path(
        '<slug:hotel_slug>/attachments/<int:attachment_id>/url/',
        views_attachments.get_attachment_url,
        name='get-attachment-url'
    ),
    
    # ============ LEGACY ENDPOINTS (kept for compatibility) ============
    
    # Legacy send message endpoint
    path(
        '<slug:hotel_slug>/conversations/<int:pk>/send_message/',
        StaffConversationViewSet.as_view({'post': 'send_message'}),
        name='conversation-send-message-legacy'
    ),
    
    # Legacy mark as read endpoint
    path(
        '<slug:hotel_slug>/conversations/<int:pk>/mark_as_read/',
        StaffConversationViewSet.as_view({'post': 'mark_as_read'}),
        name='conversation-mark-as-read'
    ),
]
