# hotel/middleware.py
from django.http import Http404
from .models import Hotel

class HotelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # handle ports, e.g. localhost:8000
        domain_parts = host.split('.')

        # Skip hotel lookup if localhost or IP
        if host in ('localhost', '127.0.0.1'):
            request.hotel = None
            return self.get_response(request)

        # Ensure there is a subdomain part
        if len(domain_parts) < 3:
            # e.g. example.com or no subdomain
            request.hotel = None
            # Optionally: raise Http404 or redirect to a landing page here
            return self.get_response(request)

        subdomain = domain_parts[0]

        try:
            hotel = Hotel.objects.get(slug=subdomain)
            request.hotel = hotel
        except Hotel.DoesNotExist:
            request.hotel = None

        return self.get_response(request)
