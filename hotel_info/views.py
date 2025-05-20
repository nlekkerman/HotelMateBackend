from rest_framework import viewsets
from .models import HotelInfo
from .serializers import HotelInfoSerializer

class HotelInfoViewSet(viewsets.ModelViewSet):
    queryset = HotelInfo.objects.all()
    serializer_class = HotelInfoSerializer
