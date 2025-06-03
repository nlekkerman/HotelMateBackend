from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Guest
from .serializers import GuestSerializer

class GuestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GuestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        print("Hotel slug from URL:", hotel_slug)
        if not hotel_slug:
            return Guest.objects.none()
        return Guest.objects.filter(hotel__slug=hotel_slug)
