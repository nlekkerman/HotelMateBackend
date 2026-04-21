from rest_framework import viewsets, permissions
from .models import MaintenanceRequest, MaintenanceComment, MaintenancePhoto
from .serializers import MaintenanceRequestSerializer, MaintenanceCommentSerializer, MaintenancePhotoSerializer, BulkMaintenancePhotoSerializer
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from staff.serializers import StaffSerializer
from hotel.permissions import IsHotelStaff
from staff.permissions import HasMaintenanceNav, CanManageMaintenance
from staff_chat.permissions import IsStaffMember, IsSameHotel
from common.mixins import HotelScopedQuerysetMixin


class MaintenanceRequestViewSet(HotelScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = MaintenanceRequest.objects.all().order_by('-created_at')
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsAuthenticated, HasMaintenanceNav, IsStaffMember, IsSameHotel]
    reported_by = StaffSerializer(read_only=True)
    accepted_by = StaffSerializer(read_only=True)

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'staff_profile'):
            serializer.save(
                reported_by=user.staff_profile,
                hotel=user.staff_profile.hotel
            )
        else:
            raise PermissionDenied("Only staff can report maintenance.")

    def perform_update(self, serializer):
        instance = serializer.instance
        new_status = self.request.data.get("status")
        user = self.request.user

        if new_status == "in_progress" and instance.accepted_by is None:
            if hasattr(user, "staff_profile"):
                serializer.save(accepted_by=user.staff_profile)
            else:
                raise PermissionDenied("Only staff can accept maintenance.")
        else:
            serializer.save()


class MaintenanceCommentViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceComment.objects.all()
    serializer_class = MaintenanceCommentSerializer
    permission_classes = [IsAuthenticated, HasMaintenanceNav, IsStaffMember, IsSameHotel]

    def get_queryset(self):
        hotel = self.request.user.staff_profile.hotel
        return MaintenanceComment.objects.filter(
            maintenance_request__hotel=hotel
        )

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'staff_profile'):
            raise PermissionDenied("Only staff can comment")
        serializer.save(staff=user.staff_profile)


class MaintenancePhotoViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePhoto.objects.all()
    serializer_class = MaintenancePhotoSerializer
    permission_classes = [IsAuthenticated, HasMaintenanceNav, IsStaffMember, IsSameHotel]

    def get_queryset(self):
        hotel = self.request.user.staff_profile.hotel
        return MaintenancePhoto.objects.filter(
            maintenance_request__hotel=hotel
        )

    def create(self, request, *args, **kwargs):
        if not hasattr(request.user, 'staff_profile'):
            raise PermissionDenied("Only staff can upload maintenance photos.")

        serializer = BulkMaintenancePhotoSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": f"{len(request.FILES.getlist('images'))} photo(s) uploaded."}, status=status.HTTP_201_CREATED)

