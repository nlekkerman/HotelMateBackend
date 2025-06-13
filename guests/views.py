from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Guest
from .serializers import GuestSerializer
from hotel.models import Hotel

class GuestViewSet(viewsets.ModelViewSet):
    serializer_class = GuestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        hotel_slug = self.request.headers.get('x-hotel-slug')
        if not hotel_slug:
            return Guest.objects.none()
        return Guest.objects.filter(hotel__slug=hotel_slug)

    def get_object(self):
        hotel_slug = self.request.headers.get('x-hotel-slug')
        return Guest.objects.get(pk=self.kwargs['pk'], hotel__slug=hotel_slug)
    
    