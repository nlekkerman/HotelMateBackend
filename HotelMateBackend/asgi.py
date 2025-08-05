# HotelMateBackend/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import room_services.routing  # ✅ Your existing app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            room_services.routing.websocket_urlpatterns  # ✅ Only include this
        )
    ),
})
