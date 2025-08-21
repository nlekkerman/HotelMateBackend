from django.urls import path
from .views import send_room_message, get_room_messages

urlpatterns = [
    path("<slug:hotel_slug>/messages/send/", send_room_message, name="send_room_message"),
    path("<slug:hotel_slug>/messages/<int:room_id>/", get_room_messages, name="get_room_messages"),
]
