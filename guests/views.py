from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from .models import Guest
from .serializers import GuestSerializer
from staff_chat.permissions import IsStaffMember, IsSameHotel
from staff.permissions import CanReadGuests, CanUpdateGuests


class GuestViewSet(viewsets.ModelViewSet):
    """Staff-zone guest endpoint. Hotel-scoped, capability-gated.

    Mounted at /api/staff/hotel/<hotel_slug>/guests/ via staff_urls.py.
    Reads require guest.record.read; updates require guest.record.update.
    Create / delete are intentionally not exposed here.
    """

    serializer_class = GuestSerializer
    http_method_names = ['get', 'head', 'options', 'put', 'patch']

    def get_permissions(self):
        base = [
            permissions.IsAuthenticated(),
            IsStaffMember(),
            IsSameHotel(),
            CanReadGuests(),
        ]
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            base.append(CanUpdateGuests())
        return base

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug:
            return Guest.objects.none()
        return Guest.objects.filter(hotel__slug=hotel_slug)

    def get_object(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        obj = get_object_or_404(
            Guest,
            pk=self.kwargs['pk'],
            hotel__slug=hotel_slug,
        )
        self.check_object_permissions(self.request, obj)
        return obj

