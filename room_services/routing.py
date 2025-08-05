from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/orders/(?P<order_id>\d+)/$", consumers.OrderStatusConsumer.as_asgi()),
]