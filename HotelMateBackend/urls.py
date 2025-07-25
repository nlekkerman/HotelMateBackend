from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.views.generic import TemplateView

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
]


def home(request):
    # Create list of API URLs for each app
    urls = [f"/api/{app}/" for app in apps]
    # Build HTML list to display
    urls_html = "<ul>" + "".join(f'<li><a href="{url}">{url}</a></li>' for url in urls) + "</ul>"
    return HttpResponse(f"<h1>Welcome to HotelMate API</h1><p>Available API endpoints:</p>{urls_html}")

# --- custom 404 handler ---
# Place this above urlpatterns
handler404 = 'common.views.custom_404'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),  # root URL shows home page
]

urlpatterns += [path(f'api/{app}/', include(f'{app}.urls')) for app in apps]

