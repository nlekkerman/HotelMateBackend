"""
Room Turnover Workflow Staff URLs
All room turnover endpoints under:
/api/staff/hotel/{hotel_slug}/rooms/...
"""

from django.urls import path
from . import views

urlpatterns = [
    # Room turnover workflow - all staff-only
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/start-cleaning/', views.start_cleaning, name='start_cleaning'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/mark-cleaned/', views.mark_cleaned, name='mark_cleaned'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/inspect/', views.inspect_room, name='inspect_room'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/mark-maintenance/', views.mark_maintenance, name='mark_maintenance'),
    path('hotels/<slug:hotel_slug>/rooms/<str:room_number>/complete-maintenance/', views.complete_maintenance, name='complete_maintenance'),
    
    # Dashboard endpoints
    path('hotels/<slug:hotel_slug>/turnover/rooms/', views.turnover_rooms, name='turnover_rooms'),
    path('hotels/<slug:hotel_slug>/turnover/stats/', views.turnover_stats, name='turnover_stats'),
]