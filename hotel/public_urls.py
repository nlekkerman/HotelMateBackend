"""
Hotel Public URLs - Guest Pre-Check-in and Survey Endpoints
All public endpoints for guest pre-check-in and survey functionality
"""

from django.urls import path
from . import public_views

urlpatterns = [
    # Cancellation policy endpoint
    path(
        'hotel/<slug:hotel_slug>/cancellation-policy/',
        public_views.HotelCancellationPolicyView.as_view(),
        name='hotel-cancellation-policy'
    ),
    
    # Guest booking management endpoints
    path(
        'hotel/<slug:hotel_slug>/booking-management/',
        public_views.ValidateBookingManagementTokenView.as_view(),
        name='validate-booking-management-token'
    ),
    path(
        'hotel/<slug:hotel_slug>/booking-management/cancel/',
        public_views.CancelBookingView.as_view(),
        name='cancel-booking'
    ),
    
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
    
    # Guest survey endpoints
    path(
        'hotel/<slug:hotel_slug>/survey/',
        public_views.ValidateSurveyTokenView.as_view(),
        name='validate-survey-token'
    ),
    path(
        'hotel/<slug:hotel_slug>/survey/submit/',
        public_views.SubmitSurveyDataView.as_view(),
        name='submit-survey-data'
    ),
]