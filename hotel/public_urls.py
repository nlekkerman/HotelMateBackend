"""
Hotel Public URLs - Guest Pre-Check-in Endpoints
All public endpoints for guest pre-check-in functionality
"""

from django.urls import path
from . import public_views

urlpatterns = [
    # Guest pre-check-in endpoints
    path(
        'hotel/<slug:hotel_slug>/precheckin/',
        public_views.ValidatePrecheckinTokenView.as_view(),
        name='validate-precheckin-token'
    ),
    path(
        'hotel/<slug:hotel_slug>/precheckin/submit/',
        public_views.SubmitPrecheckinDataView.as_view(),
        name='submit-precheckin-data'
    ),
]