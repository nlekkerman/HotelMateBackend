from rest_framework import viewsets, mixins, permissions
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from rooms.models import Room
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import RoomServiceItem, BreakfastItem, Order, BreakfastOrder
from .serializers import (
    RoomServiceItemSerializer,
    BreakfastItemSerializer,
    OrderSerializer,
    BreakfastOrderSerializer
)


class RoomServiceItemViewSet(mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    queryset = RoomServiceItem.objects.all()
    serializer_class = RoomServiceItemSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='room/(?P<room_number>[^/.]+)/menu')
    def menu(self, request, room_number=None):
        # Optionally: filter or log room_number
        items = self.get_queryset()
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class BreakfastItemViewSet(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    queryset = BreakfastItem.objects.all()
    serializer_class = BreakfastItemSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='room/(?P<room_number>[^/.]+)/breakfast')
    def menu(self, request, room_number=None):
        items = self.get_queryset()
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]


class BreakfastOrderViewSet(viewsets.ModelViewSet):
    queryset = BreakfastOrder.objects.all()
    serializer_class = BreakfastOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

# views.py
@api_view(['POST'])
@permission_classes([AllowAny])
def validate_pin(request, room_number):
    room = get_object_or_404(Room, room_number=room_number)
    pin = request.data.get('pin')
    if pin == room.guest_id_pin:
        return Response({'valid': True})
    return Response({'valid': False}, status=401)
