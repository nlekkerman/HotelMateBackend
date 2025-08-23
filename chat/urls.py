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
    conversation_unread_messages_count,
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

    # Validate chat PIN (unchanged)
    path("<slug:hotel_slug>/messages/room/<int:room_number>/validate-chat-pin/", validate_chat_pin, name="validate_chat_pin"),
    path(
        "conversations/<int:conversation_id>/unread-count/",
        conversation_unread_messages_count,
        name="conversation_unread_messages_count"
    ),
    # --- New URLs for unread tracking ---
    path("<slug:hotel_slug>/conversations/unread-count/", get_unread_count, name="get_unread_count"),
    path("conversations/<int:conversation_id>/mark-read/", mark_conversation_read, name="mark_conversation_read"),
]
