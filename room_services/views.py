from rest_framework import viewsets, mixins, permissions
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from rooms.models import Room
from hotel.models import Hotel  # Assuming you have a Hotel model
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import RoomServiceItem, BreakfastItem, Order, BreakfastOrder
from .serializers import (
    RoomServiceItemSerializer,
    BreakfastItemSerializer,
    OrderSerializer,
    BreakfastOrderSerializer
)


def get_hotel_from_request(request):
    # Extract subdomain from request, e.g. "hotel1.example.com"
    host = request.get_host().split(':')[0]  # remove port if present
    subdomain = host.split('.')[0]
    hotel = get_object_or_404(Hotel, subdomain=subdomain)
    return hotel


class RoomServiceItemViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RoomServiceItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return RoomServiceItem.objects.filter(hotel=hotel)

    @action(detail=False, methods=['get'], url_path='room/(?P<room_number>[^/.]+)/menu')
    def menu(self, request, room_number=None):
        hotel = get_hotel_from_request(request)
        # You could also filter items by availability to the room's hotel
        items = self.get_queryset()
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class BreakfastItemViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BreakfastItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return BreakfastItem.objects.filter(hotel=hotel)

    @action(detail=False, methods=['get'], url_path='room/(?P<room_number>[^/.]+)/breakfast')
    def menu(self, request, room_number=None):
        hotel = get_hotel_from_request(request)
        items = self.get_queryset()
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        # Filter orders for rooms in this hotel only
        return Order.objects.filter(room__hotel=hotel)


class BreakfastOrderViewSet(viewsets.ModelViewSet):
    serializer_class = BreakfastOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return BreakfastOrder.objects.filter(room__hotel=hotel)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_pin(request, room_number):
    hotel = get_hotel_from_request(request)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)
    pin = request.data.get('pin')
    if pin == room.guest_id_pin:
        return Response({'valid': True})
    return Response({'valid': False}, status=401)
