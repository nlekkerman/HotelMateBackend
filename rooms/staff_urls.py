"""
Room Turnover Workflow Staff URLs

These URLs are INCLUDED under:
 /api/staff/hotel/<hotel_slug>/

So hotel_slug MUST NOT appear here.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Room turnover workflow - all staff-only
    path('rooms/<str:room_number>/start-cleaning/', views.start_cleaning, name='start_cleaning'),
    path('rooms/<str:room_number>/mark-cleaned/', views.mark_cleaned, name='mark_cleaned'),
    path('rooms/<str:room_number>/inspect/', views.inspect_room, name='inspect_room'),
    path('rooms/<str:room_number>/mark-maintenance/', views.mark_maintenance, name='mark_maintenance'),
    path('rooms/<str:room_number>/complete-maintenance/', views.complete_maintenance, name='complete_maintenance'),

    # Guest check-in/check-out - canonical endpoints
    path('rooms/<str:room_number>/checkin/', views.checkin_room, name='checkin_room'),
    path('rooms/<str:room_number>/checkout/', views.checkout_room, name='checkout_room'),

    # Dashboard endpoints
    path('turnover/rooms/', views.turnover_rooms, name='turnover_rooms'),
    path('turnover/stats/', views.turnover_stats, name='turnover_stats'),
]
