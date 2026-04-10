from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Guest
from .serializers import GuestSerializer
from hotel.models import Hotel
from staff_chat.permissions import IsStaffMember, IsSameHotel
from staff.permissions import HasNavPermission

class GuestViewSet(viewsets.ModelViewSet):
    serializer_class = GuestSerializer

    def get_permissions(self):
        # RBAC: guest records are part of rooms/bookings workflow
        base = [permissions.IsAuthenticated(), HasNavPermission('rooms'), IsStaffMember(), IsSameHotel()]
        return base

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug:
            return Guest.objects.none()
        return Guest.objects.filter(hotel__slug=hotel_slug)

    def get_object(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        return Guest.objects.get(pk=self.kwargs['pk'], hotel__slug=hotel_slug)
    
    