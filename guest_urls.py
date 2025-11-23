"""
GUEST Zone Routing Wrapper - Phase 1
Routes for guest-facing public hotel pages.
Returns stub JSON responses in Phase 1.
"""

from django.urls import path
from django.http import JsonResponse


def guest_home_stub(request, hotel_slug):
    """Stub view for guest home page"""
    return JsonResponse({
        'message': 'Guest home page stub',
        'hotel_slug': hotel_slug,
        'endpoint': '/api/guest/hotels/{hotel_slug}/site/home/',
        'status': 'Phase 1 - Stub endpoint'
    })


def guest_rooms_stub(request, hotel_slug):
    """Stub view for guest rooms page"""
    return JsonResponse({
        'message': 'Guest rooms page stub',
        'hotel_slug': hotel_slug,
        'endpoint': '/api/guest/hotels/{hotel_slug}/site/rooms/',
        'status': 'Phase 1 - Stub endpoint'
    })


def guest_offers_stub(request, hotel_slug):
    """Stub view for guest offers page"""
    return JsonResponse({
        'message': 'Guest offers page stub',
        'hotel_slug': hotel_slug,
        'endpoint': '/api/guest/hotels/{hotel_slug}/site/offers/',
        'status': 'Phase 1 - Stub endpoint'
    })


urlpatterns = [
    path(
        'hotels/<str:hotel_slug>/site/home/',
        guest_home_stub,
        name='guest-home'
    ),
    path(
        'hotels/<str:hotel_slug>/site/rooms/',
        guest_rooms_stub,
        name='guest-rooms'
    ),
    path(
        'hotels/<str:hotel_slug>/site/offers/',
        guest_offers_stub,
        name='guest-offers'
    ),
]
