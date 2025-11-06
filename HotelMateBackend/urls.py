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
    'notifications',
    'maintenance',
    'home',
    'attendance',
    'chat',
    'entertainment',
    'staff_chat',
    'stock_tracker',
]


def home(request):
    # Create list of API URLs for each app
    urls = [f"/api/{app}/" for app in apps]
    urls.append("/api/hotels/{hotel_identifier}/theme/")
    # Build HTML list to display
    list_items = "".join(
        f'<li><a href="#">{url}</a></li>' for url in urls
    )
    urls_html = f"<ul>{list_items}</ul>"
    title = "<h1>Welcome to HotelMate API</h1>"
    intro = "<p>Available API endpoints:</p>"
    return HttpResponse(f"{title}{intro}{urls_html}")


# --- custom 404 handler ---
# Place this above urlpatterns
handler404 = 'common.views.custom_404'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),  # root URL shows home page
]

urlpatterns += [
    path(f'api/{app}/', include(f'{app}.urls')) for app in apps
]
# Common app is hotel-based
urlpatterns.append(path('api/hotels/', include('common.urls')))

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

