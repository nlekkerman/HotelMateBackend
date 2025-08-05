from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Capture hotel_slug (letters, digits, dashes) and order_id (digits)
    re_path(r"ws/orders/(?P<hotel_slug>[\w-]+)/(?P<order_id>\d+)/$", consumers.OrderStatusConsumer.as_asgi()),
]
