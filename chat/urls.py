from django.urls import path
from .views import send_room_message, get_room_messages, validate_chat_pin

urlpatterns = [
    path("<slug:hotel_slug>/messages/room/<int:room_number>/send/", send_room_message, name="send_room_message"),
    path("<slug:hotel_slug>/messages/room/<int:room_number>/", get_room_messages, name="get_room_messages"),
    path("<slug:hotel_slug>/messages/room/<int:room_number>/validate-chat-pin/", validate_chat_pin, name="validate_chat_pin"),
]
