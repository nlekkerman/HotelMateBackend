# HotelMateBackend/asgi.py
import os

# Ensure DJANGO_SETTINGS_MODULE is set before importing any app modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Import app routing modules lazily and fail-safe: if an app doesn't
# expose a `routing` module (for example during lightweight deployments
# or when the app has no websocket endpoints), fallback to an empty
# list so the ASGI server can start instead of crashing at import time.
websocket_urlpatterns = []
try:
    import room_services.routing as room_services_routing
    websocket_urlpatterns += getattr(room_services_routing, 'websocket_urlpatterns', [])
except Exception:
    # missing module or other import-time error should not prevent the app
    # from starting. We'll log nothing here to avoid import-time logging
    # dependency, but it's safe to add more detailed handling if desired.
    pass

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})