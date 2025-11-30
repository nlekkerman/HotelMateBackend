from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

apps = [
    'rooms',
    'guests',
    'staff',
    'hotel_info',
    'room_services',
    'hotel',
    'bookings',
    'common',
    'notifications',
    'stock_tracker',
    'maintenance',
    'home',
    'attendance',
    'chat',
    'entertainment',
    'staff_chat',
]


def home(request):
    # Create list of API URLs for each app
    urls = [f"/api/{app}/" for app in apps]
    # Build HTML list to display
    list_items = "".join(
        f'<li><a href="{url}">{url}</a></li>' for url in urls
    )
    urls_html = f"<ul>{list_items}</ul>"
    return HttpResponse(
        f"<h1>Welcome to HotelMate API</h1>"
        f"<p>Available API endpoints:</p>{urls_html}"
    )


# --- custom 404 handler ---
# Place this above urlpatterns
handler404 = 'common.views.custom_404'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),  # root URL shows home page
    # Phase 1: New STAFF zone - /api/staff/hotels/<hotel_slug>/<app>/
    path('api/staff/', include('staff_urls')),
    # Phase 1: New GUEST zone - /api/guest/hotels/<hotel_slug>/site/
    path('api/guest/', include('guest_urls')),
    # Public zone - No auth required (landing page, hotel discovery)
    path('api/public/', include('public_urls')),
]

# Legacy routes - kept for backward compatibility  
# Exclude 'attendance' to avoid namespace conflict with staff zone
legacy_apps = [app for app in apps if app != 'attendance']
urlpatterns += [path(f'api/{app}/', include(f'{app}.urls')) for app in legacy_apps]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

