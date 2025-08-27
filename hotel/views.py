from rest_framework import viewsets
from rest_framework import generics
from rest_framework.response import Response
from .models import Hotel
from .serializers import HotelSerializer
from django.shortcuts import get_object_or_404

class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = []  # You can add IsAdminUser, etc.
    
class HotelBySlugView(generics.RetrieveAPIView):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    lookup_field = "slug"

    def get_object(self):
        slug = self.kwargs.get("slug")
        hotel = get_object_or_404(Hotel, slug=slug)
        return hotel
