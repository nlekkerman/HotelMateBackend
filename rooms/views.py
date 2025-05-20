from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Room
from .serializers import RoomSerializer


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

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
