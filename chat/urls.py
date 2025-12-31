from django.urls import path
from .views import (
    send_conversation_message,
    get_conversation_messages,
    validate_chat_pin,
    get_active_conversations,
    get_or_create_conversation_from_room,
    get_active_rooms,
    get_unread_count,
    mark_conversation_read,
    get_unread_conversation_count,
    initialize_guest_session,
    validate_guest_session,
    get_unread_messages_for_guest,
    assign_staff_to_conversation,
    update_message,
    delete_message,
    upload_message_attachment,
    delete_attachment,
    save_fcm_token,
    test_deletion_broadcast,
    guest_chat_context,  # NEW: Token-based guest chat context
    guest_send_message,  # NEW: Token-based guest send message
)

urlpatterns = [
    path("<slug:hotel_slug>/active-rooms/", get_active_rooms, name="get_active_rooms"),
    path("<slug:hotel_slug>/conversations/from-room/<int:room_number>/", get_or_create_conversation_from_room, name="get_or_create_conversation_from_room"),

    # Fetch all active conversations for a hotel
    path("<slug:hotel_slug>/conversations/", get_active_conversations, name="get_active_conversations"),

    # Fetch all messages in a conversation for a specific hotel
    path("<slug:hotel_slug>/conversations/<int:conversation_id>/messages/", get_conversation_messages, name="get_conversation_messages"),

    # Send a message in a conversation for a specific hotel
    path("<slug:hotel_slug>/conversations/<int:conversation_id>/messages/send/", send_conversation_message, name="send_conversation_message"),

    # === NEW: Token-based Guest Chat Endpoints ===
    path("<slug:hotel_slug>/guest/chat/context/", guest_chat_context, name="guest_chat_context"),
    path("<slug:hotel_slug>/guest/chat/messages/", guest_send_message, name="guest_send_message"),
    
    # === LEGACY: PIN-based endpoints (will be phased out) ===
    # Validate chat PIN (unchanged)
    path("<slug:hotel_slug>/messages/room/<int:room_number>/validate-chat-pin/", validate_chat_pin, name="validate_chat_pin"),
    path(
        "hotels/<slug:hotel_slug>/conversations/unread-count/",
        get_unread_conversation_count,
        name="get_unread_conversation_count"
    ),

    # --- New URLs for unread tracking ---
    path("<slug:hotel_slug>/conversations/unread-count/", get_unread_count, name="get_unread_count"),
    path("conversations/<int:conversation_id>/mark-read/", mark_conversation_read, name="mark_conversation_read"),
    
    # --- Guest session management ---
    path(
        "<slug:hotel_slug>/guest-session/room/<int:room_number>/initialize/",
        initialize_guest_session,
        name="initialize_guest_session"
    ),
    path(
        "guest-session/<uuid:session_token>/validate/",
        validate_guest_session,
        name="validate_guest_session"
    ),
    path(
        "guest-session/<uuid:session_token>/unread-count/",
        get_unread_messages_for_guest,
        name="get_unread_messages_for_guest"
    ),
    
    # --- Staff assignment (conversation handoff) ---
    path(
        "<slug:hotel_slug>/conversations/<int:conversation_id>/assign-staff/",
        assign_staff_to_conversation,
        name="assign_staff_to_conversation"
    ),
    
    # --- Message CRUD operations ---
    path(
        "messages/<int:message_id>/update/",
        update_message,
        name="update_message"
    ),
    path(
        "messages/<int:message_id>/delete/",
        delete_message,
        name="delete_message"
    ),
    
    # --- File attachment operations ---
    path(
        "<slug:hotel_slug>/conversations/<int:conversation_id>/upload-attachment/",
        upload_message_attachment,
        name="upload_message_attachment"
    ),
    path(
        "attachments/<int:attachment_id>/delete/",
        delete_attachment,
        name="delete_attachment"
    ),
    
    # --- FCM TOKEN MANAGEMENT ---
    path(
        "<slug:hotel_slug>/save-fcm-token/",
        save_fcm_token,
        name="save_fcm_token"
    ),
    
    # --- TEST ENDPOINTS (Development/Debug Only) ---
    path(
        "test/<slug:hotel_slug>/room/<int:room_number>/test-deletion/",
        test_deletion_broadcast,
        name="test_deletion_broadcast"
    ),
]
