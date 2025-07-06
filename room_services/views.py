from rest_framework import viewsets, mixins, permissions
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from rooms.models import Room
from hotel.models import Hotel  # Assuming you have a Hotel model
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import RoomServiceItem, BreakfastItem, Order, BreakfastOrder
from django.http import Http404
from notifications.utils import notify_porters_of_room_service_order
from django.db import transaction


from .serializers import (
    RoomServiceItemSerializer,
    BreakfastItemSerializer,
    OrderSerializer,
    BreakfastOrderSerializer
)



def get_hotel_from_request(request):
    # Extract hotel_slug from URL kwargs in request
    hotel_slug = None
    if hasattr(request, 'parser_context'):
        hotel_slug = request.parser_context['kwargs'].get('hotel_slug')
    elif hasattr(request, 'resolver_match'):
        hotel_slug = request.resolver_match.kwargs.get('hotel_slug')

    if not hotel_slug:
        raise Http404("Hotel slug not provided")

    return get_object_or_404(Hotel, slug=hotel_slug)

class RoomServiceItemViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RoomServiceItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return RoomServiceItem.objects.filter(hotel=hotel)

    @action(detail=False, methods=['get'], url_path=r'room/(?P<room_number>[^/.]+)/menu')
    def menu(self, request, hotel_slug=None, room_number=None):
        hotel = get_hotel_from_request(request)
        items = RoomServiceItem.objects.filter(hotel=hotel)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

class BreakfastItemViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BreakfastItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return BreakfastItem.objects.filter(hotel=hotel)

    @action(detail=False, methods=['get'], url_path=r'room/(?P<room_number>[^/.]+)/breakfast')
    def menu(self, request, hotel_slug=None, room_number=None):
        hotel = get_hotel_from_request(request)
        items = self.get_queryset()
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        # Filter orders for rooms in this hotel only
        return Order.objects.filter(hotel=hotel).exclude(status="completed")
    
    def perform_create(self, serializer):
        hotel = get_hotel_from_request(self.request)
        order = serializer.save(hotel=hotel)  # Save and capture the order
        notify_porters_of_room_service_order(order)  # Send notification
    
    @action(detail=False, methods=["get"], url_path="pending-count")
    def pending_count(self, request, *args, **kwargs):
        """
        GET /room_services/{hotel_slug}/orders/pending-count/
        Returns JSON: { "count": <int> }
        """
        hotel = get_hotel_from_request(request)
        count = Order.objects.filter(hotel=hotel).filter(status="pending").count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="room-history", permission_classes=[AllowAny])
    def room_order_history(self, request):
        hotel_slug = request.query_params.get("hotel_slug")
        room_number = request.query_params.get("room_number")

        if not hotel_slug or not room_number:
            return Response({"error": "hotel_slug and room_number are required"}, status=400)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        queryset = Order.objects.filter(hotel=hotel, room_number=room_number)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class BreakfastOrderViewSet(viewsets.ModelViewSet):
    serializer_class = BreakfastOrderSerializer

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        queryset = BreakfastOrder.objects.filter(
            hotel=hotel,
            status__in=["pending", "accepted"]
        )
        
        room_number = self.request.query_params.get('room_number')
        if room_number:
            queryset = queryset.filter(room_number=room_number)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        hotel_slug = self.kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        context['hotel'] = hotel
        return context

    def perform_create(self, serializer):
        hotel = self.get_serializer_context()['hotel']
        serializer.save(hotel=hotel)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get("status")

        valid_transitions = {
            "pending": ["accepted"],
            "accepted": ["completed"],
            "completed": [],  # no further change allowed
        }

        if new_status and new_status != instance.status:
            allowed = valid_transitions.get(instance.status, [])
            if new_status not in allowed:
                return Response(
                    {"error": f"Invalid status transition from '{instance.status}' to '{new_status}'."},
                    status=400
                )

        return super().partial_update(request, *args, **kwargs)

    
    @action(detail=False, methods=["get"], url_path="breakfast-pending-count")
    def pending_count(self, request, hotel_slug=None):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        count = BreakfastOrder.objects.filter(hotel=hotel, status="pending").count()
        print("Breakfast pending orders:", BreakfastOrder.objects.filter(hotel=hotel).values_list("id", "status"))
        return Response({"count": count})

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_pin(request, hotel_slug,room_number):  # add hotel_slug here
    hotel = get_hotel_from_request(request)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)
    pin = request.data.get('pin')
    if pin == room.guest_id_pin:
        return Response({'valid': True})
    return Response({'valid': False}, status=401)

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_dinner_pin(request, hotel_slug, restaurant_slug, room_number):
    """
    Validate guest PIN for dinner booking in a specific restaurant and room.
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, hotel=hotel, room_number=room_number)
    pin = request.data.get("pin")

    if pin == room.guest_id_pin:
        return Response({'valid': True})
    return Response({'valid': False}, status=401)
