from django.urls import path
from .views import (
    send_conversation_message,
    get_conversation_messages,
    validate_chat_pin,
    get_active_conversations
)

urlpatterns = [
    # Fetch all active conversations for a hotel
    path("<slug:hotel_slug>/conversations/", get_active_conversations, name="get_active_conversations"),

    # Fetch all messages in a conversation for a specific hotel
    path("<slug:hotel_slug>/conversations/<int:conversation_id>/messages/", get_conversation_messages, name="get_conversation_messages"),

    # Send a message in a conversation for a specific hotel
    path("<slug:hotel_slug>/conversations/<int:conversation_id>/messages/send/", send_conversation_message, name="send_conversation_message"),

    # Validate chat PIN (unchanged)
    path("<slug:hotel_slug>/messages/room/<int:room_number>/validate-chat-pin/", validate_chat_pin, name="validate_chat_pin"),
]
