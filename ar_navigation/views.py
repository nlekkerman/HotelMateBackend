from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework import status
from .models import ARAnchor
from .serializers import ARAnchorSerializer
from hotel.models import Hotel

class ARNavigationView(APIView):
    def get(self, request, hotel_slug, room_number):
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            return Response({"error": "Hotel not found."}, status=status.HTTP_404_NOT_FOUND)

        anchors = ARAnchor.objects.filter(hotel=hotel).order_by("order")
        serializer = ARAnchorSerializer(anchors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ARAnchorDetailView(RetrieveAPIView):
    queryset = ARAnchor.objects.all()
    serializer_class = ARAnchorSerializer
    lookup_field = 'id'