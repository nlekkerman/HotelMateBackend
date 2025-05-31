from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, filters, status
from .models import Room
from .serializers import RoomSerializer
from guests.serializers import GuestSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend


class RoomPagination(PageNumberPagination):
    page_size = 10  # items per page
    page_size_query_param = 'page_size'  # allow client to set page size with ?page_size=xx
    max_page_size = 100


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]  # Optional: restrict access to authenticated users

    serializer_class = RoomSerializer
    pagination_class = RoomPagination
    lookup_field = 'room_number'
    filter_backends = [filters.SearchFilter]
    search_fields = ['room_number', 'is_occupied']

    def get_queryset(self):
        user = self.request.user
        print("Search param:", self.request.query_params.get('search'))
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

    @action(detail=True, methods=['post'])
    def add_guest(self, request, room_number=None):
        room = self.get_object()
        serializer = GuestSerializer(data=request.data)

        if serializer.is_valid():
            guest = serializer.save()
            guest.room = room
            if room.guest_id_pin:
                guest.id_pin = room.guest_id_pin
            guest.save()
            room.is_occupied = True
            room.save()
            return Response(GuestSerializer(guest).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

