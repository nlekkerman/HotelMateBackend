from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from .models import Room
from .serializers import RoomSerializer
from guests.serializers import GuestSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from hotel.models import Hotel
from guests.models import Guest
from datetime import timedelta
from datetime import datetime
from room_services.models import Order, BreakfastOrder
from chat.models import Conversation, RoomMessage
from rest_framework.decorators import api_view, permission_classes
from django.db import transaction
from django.utils.timezone import now


class RoomPagination(PageNumberPagination):
    page_size = 10  # items per page
    page_size_query_param = 'page_size'  # allow client to set page size with ?page_size=xx
    max_page_size = 100


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated] 
    serializer_class = RoomSerializer
    pagination_class = RoomPagination
    lookup_field = 'room_number'
    filter_backends = [filters.SearchFilter]
    search_fields = ['room_number', 'is_occupied']

    def get_queryset(self):
        user = self.request.user
        staff = getattr(user, 'staff_profile', None)

        queryset = Room.objects.none()

        if staff and staff.hotel:
            queryset = Room.objects.filter(hotel=staff.hotel)

        hotel_id = self.request.query_params.get('hotel_id')
        if hotel_id:
            queryset = queryset.filter(hotel_id=hotel_id)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(room_number__icontains=search)

        return queryset.order_by('room_number')

    def perform_create(self, serializer):
        staff = getattr(self.request.user, 'staff_profile', None)
        if staff and staff.hotel:
            serializer.save(hotel=staff.hotel)
        else:
            raise PermissionDenied("You must be assigned to a hotel to create a room.")

    @action(detail=True, methods=['post'])
    def generate_pin(self, request, pk=None):
        room = self.get_object()
        room.generate_guest_pin()
        return Response({'guest_id_pin': room.guest_id_pin})

    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        qr_type = request.data.get('qr_type', 'room_service')
        room = self.get_object()
        room.generate_qr_code(qr_type=qr_type)
        qr_url = getattr(room, f"{qr_type}_qr_code", None)
        return Response({'qr_url': qr_url})


class AddGuestToRoomView(APIView):
    def post(self, request, hotel_identifier, room_number):
        hotel = get_object_or_404(Hotel, slug=hotel_identifier)
        room = get_object_or_404(Room, hotel=hotel, room_number=room_number)

        guest_data = request.data.copy()
        guest_data['hotel'] = hotel.id
        guest_data['room'] = room.id

        # Auto-calculate check_out_date if not provided
        if (
            guest_data.get('check_in_date') and
            guest_data.get('days_booked') and
            not guest_data.get('check_out_date')
        ):
            try:
                check_in = datetime.strptime(guest_data['check_in_date'], '%Y-%m-%d').date()
                days = int(guest_data['days_booked'])
                check_out = check_in + timedelta(days=days)
                guest_data['check_out_date'] = check_out.isoformat()
            except Exception:
                return Response(
                    {"error": "Invalid check_in_date or days_booked for date calculation."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Use default room PIN if guest doesn't provide one
        if not guest_data.get('id_pin') and room.guest_id_pin:
            guest_data['id_pin'] = room.guest_id_pin

        serializer = GuestSerializer(data=guest_data)
        if serializer.is_valid():
            guest = serializer.save()
            room.guests.add(guest)
            room.is_occupied = True
            room.save()
            return Response(GuestSerializer(guest).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoomByHotelAndNumberView(APIView):
    def get(self, request, hotel_identifier, room_number):
        hotel = get_object_or_404(Hotel, slug=hotel_identifier)
        room = get_object_or_404(Room, hotel=hotel, room_number=room_number)
        serializer = RoomSerializer(room)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_rooms(request, hotel_slug):
    """
    POST /api/hotels/{hotel_slug}/rooms/checkout/
    {
      "room_ids": [3, 7, 11]
    }
    """
    room_ids = request.data.get('room_ids')
    if not isinstance(room_ids, list) or not room_ids:
        return Response(
            {"detail": "`room_ids` must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Only rooms in this hotel that match the IDs
    rooms = Room.objects.filter(hotel__slug=hotel_slug, id__in=room_ids)

    if not rooms.exists():
        return Response(
            {"detail": "No matching rooms found for this hotel."},
            status=status.HTTP_404_NOT_FOUND
        )

    with transaction.atomic():
        for room in rooms:
            # Remove M2M links
            room.guests.clear()

            # Delete all Guest objects linked to this room
            Guest.objects.filter(room=room).delete()

            # Delete all conversations & their messages for this room
            Conversation.objects.filter(room=room).delete()
            # RoomMessage objects will cascade delete automatically because they have FK to Conversation with on_delete=models.CASCADE
            # Optionally, if RoomMessage has FK to Room separately, delete explicitly:
            RoomMessage.objects.filter(room=room).delete()

            # Mark room unoccupied & regenerate guest PIN
            room.is_occupied = False
            room.generate_guest_pin()

            # Delete any open room-service & breakfast orders
            Order.objects.filter(hotel=room.hotel, room_number=room.room_number).delete()
            BreakfastOrder.objects.filter(hotel=room.hotel, room_number=room.room_number).delete()

            room.save()

    return Response(
        {"detail": f"Checked out {rooms.count()} room(s) in hotel '{hotel_slug}', deleted guests, conversations, and messages."},
        status=status.HTTP_200_OK
    ) 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def checkout_needed(request, hotel_slug):
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    today = now().date()

    rooms = Room.objects.filter(
        hotel=hotel,
        is_occupied=True,
        guests__check_out_date__lt=today
    ).distinct()

    serializer = RoomSerializer(rooms, many=True)
    return Response(serializer.data)
