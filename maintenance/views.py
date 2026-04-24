"""
Maintenance module views (Phase 6D.1).

Capability-first enforcement. Nav/tier/role-slug checks are retired.
Action fields (`status`, `accepted_by`) are mutated only through the
dedicated `@action` endpoints, each gated by its own capability.
"""
from __future__ import annotations

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.mixins import HotelScopedQuerysetMixin
from staff.permissions import (
    CanAcceptMaintenanceRequest,
    CanCloseMaintenanceRequest,
    CanCreateMaintenanceComment,
    CanCreateMaintenanceRequest,
    CanDeleteMaintenancePhoto,
    CanDeleteMaintenanceRequest,
    CanModerateMaintenanceComment,
    CanReadMaintenanceRequests,
    CanReassignMaintenanceRequest,
    CanReopenMaintenanceRequest,
    CanResolveMaintenanceRequest,
    CanUpdateMaintenanceRequest,
    CanUploadMaintenancePhoto,
    CanViewMaintenanceModule,
)
from staff_chat.permissions import IsSameHotel, IsStaffMember

from .models import MaintenanceComment, MaintenancePhoto, MaintenanceRequest
from .serializers import (
    BulkMaintenancePhotoSerializer,
    MaintenanceCommentSerializer,
    MaintenancePhotoSerializer,
    MaintenanceRequestReassignSerializer,
    MaintenanceRequestSerializer,
)


# ---------------------------------------------------------------------------
# Base chain — every maintenance endpoint requires this.
# ---------------------------------------------------------------------------

_BASE_CHAIN = (
    IsAuthenticated,
    IsStaffMember,
    IsSameHotel,
    CanViewMaintenanceModule,
)


def _base_instances():
    return [cls() for cls in _BASE_CHAIN]


# ---------------------------------------------------------------------------
# Maintenance requests
# ---------------------------------------------------------------------------

class MaintenanceRequestViewSet(
    HotelScopedQuerysetMixin, viewsets.ModelViewSet
):
    queryset = MaintenanceRequest.objects.all().order_by('-created_at')
    serializer_class = MaintenanceRequestSerializer

    # ------------------------------------------------------------------
    # Capability routing
    # ------------------------------------------------------------------
    def get_permissions(self):
        base = _base_instances()
        action = self.action

        if action in ('list', 'retrieve'):
            base.append(CanReadMaintenanceRequests())
        elif action == 'create':
            base.append(CanCreateMaintenanceRequest())
        elif action in ('update', 'partial_update'):
            base.append(CanReadMaintenanceRequests())
            base.append(CanUpdateMaintenanceRequest())
        elif action == 'destroy':
            base.append(CanDeleteMaintenanceRequest())
        elif action == 'accept':
            base.append(CanReadMaintenanceRequests())
            base.append(CanAcceptMaintenanceRequest())
        elif action == 'resolve':
            base.append(CanReadMaintenanceRequests())
            base.append(CanResolveMaintenanceRequest())
        elif action == 'reopen':
            base.append(CanReadMaintenanceRequests())
            base.append(CanReopenMaintenanceRequest())
        elif action == 'close':
            base.append(CanReadMaintenanceRequests())
            base.append(CanCloseMaintenanceRequest())
        elif action == 'reassign':
            base.append(CanReadMaintenanceRequests())
            base.append(CanReassignMaintenanceRequest())
        else:
            base.append(CanReadMaintenanceRequests())
        return base

    # ------------------------------------------------------------------
    # Create — auto-stamp hotel + reporter.
    # ------------------------------------------------------------------
    def perform_create(self, serializer):
        staff = self.request.user.staff_profile
        serializer.save(reported_by=staff, hotel=staff.hotel)

    # ------------------------------------------------------------------
    # Action endpoints
    # ------------------------------------------------------------------
    def _render(self, instance):
        data = MaintenanceRequestSerializer(
            instance, context={'request': self.request},
        ).data
        return data

    @action(detail=True, methods=['post'])
    def accept(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == 'closed':
            return Response(
                {'error': 'Cannot accept a closed request.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if instance.status not in ('open', 'in_progress'):
            return Response(
                {'error': f'Cannot accept from status {instance.status!r}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        staff = request.user.staff_profile
        with transaction.atomic():
            instance.status = 'in_progress'
            instance.accepted_by = staff
            instance.save(update_fields=['status', 'accepted_by', 'updated_at'])
        return Response(self._render(instance))

    @action(detail=True, methods=['post'])
    def resolve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 'in_progress':
            return Response(
                {'error': f'Cannot resolve from status {instance.status!r}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = 'resolved'
        instance.save(update_fields=['status', 'updated_at'])
        return Response(self._render(instance))

    @action(detail=True, methods=['post'])
    def reopen(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status not in ('resolved', 'closed'):
            return Response(
                {'error': f'Cannot reopen from status {instance.status!r}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            instance.status = 'open'
            instance.accepted_by = None
            instance.save(update_fields=['status', 'accepted_by', 'updated_at'])
        return Response(self._render(instance))

    @action(detail=True, methods=['post'])
    def close(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status not in ('resolved', 'in_progress'):
            return Response(
                {'error': f'Cannot close from status {instance.status!r}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = 'closed'
        instance.save(update_fields=['status', 'updated_at'])
        return Response(self._render(instance))

    @action(detail=True, methods=['post'])
    def reassign(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = MaintenanceRequestReassignSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        target = serializer.validated_data['accepted_by']
        instance.accepted_by = target
        instance.save(update_fields=['accepted_by', 'updated_at'])
        return Response(self._render(instance))


# ---------------------------------------------------------------------------
# Maintenance comments
# ---------------------------------------------------------------------------

class MaintenanceCommentViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceComment.objects.all()
    serializer_class = MaintenanceCommentSerializer

    def get_permissions(self):
        base = _base_instances()
        action = self.action

        if action in ('list', 'retrieve'):
            base.append(CanReadMaintenanceRequests())
        elif action == 'create':
            base.append(CanReadMaintenanceRequests())
            base.append(CanCreateMaintenanceComment())
        elif action in ('update', 'partial_update', 'destroy'):
            # Authorship is resolved per-object in check_object_permissions.
            base.append(CanReadMaintenanceRequests())
            base.append(CanCreateMaintenanceComment())
        else:
            base.append(CanReadMaintenanceRequests())
        return base

    def get_queryset(self):
        staff = self.request.user.staff_profile
        return MaintenanceComment.objects.filter(
            request__hotel=staff.hotel,
        )

    def perform_create(self, serializer):
        staff = self.request.user.staff_profile
        request_obj = serializer.validated_data.get('request')
        # Defence in depth: serializer already hotel-scopes, but re-check.
        if request_obj is None or request_obj.hotel_id != staff.hotel_id:
            raise PermissionDenied("Maintenance request not found.")
        serializer.save(staff=staff)

    def check_object_permissions(self, request, obj):
        # IsSameHotel.has_object_permission can't introspect
        # MaintenanceComment (no `.hotel` or `.conversation`); tenant
        # isolation is enforced by get_queryset (foreign → 404) and the
        # view-level IsSameHotel.has_permission check. Skip it here.
        for permission in self.get_permissions():
            if isinstance(permission, IsSameHotel):
                continue
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request,
                    message=getattr(permission, 'message', None),
                    code=getattr(permission, 'code', None),
                )
        if self.action in ('update', 'partial_update', 'destroy'):
            staff = request.user.staff_profile
            is_author = obj.staff_id == staff.id
            if not is_author:
                moderator = CanModerateMaintenanceComment()
                if not moderator.has_permission(request, self):
                    raise PermissionDenied(moderator.message)


# ---------------------------------------------------------------------------
# Maintenance photos
# ---------------------------------------------------------------------------

class MaintenancePhotoViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePhoto.objects.all()
    serializer_class = MaintenancePhotoSerializer

    def get_permissions(self):
        base = _base_instances()
        action = self.action

        if action in ('list', 'retrieve'):
            base.append(CanReadMaintenanceRequests())
        elif action == 'create':
            base.append(CanReadMaintenanceRequests())
            base.append(CanUploadMaintenancePhoto())
        elif action in ('update', 'partial_update', 'destroy'):
            base.append(CanReadMaintenanceRequests())
            base.append(CanDeleteMaintenancePhoto())
        else:
            base.append(CanReadMaintenanceRequests())
        return base

    def get_queryset(self):
        staff = self.request.user.staff_profile
        return MaintenancePhoto.objects.filter(
            request__hotel=staff.hotel,
        )

    def check_object_permissions(self, request, obj):
        # MaintenancePhoto has no `.hotel`; skip IsSameHotel's object-
        # level check (view-level + queryset handle tenant isolation).
        for permission in self.get_permissions():
            if isinstance(permission, IsSameHotel):
                continue
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request,
                    message=getattr(permission, 'message', None),
                    code=getattr(permission, 'code', None),
                )

    def create(self, request, *args, **kwargs):
        serializer = BulkMaintenancePhotoSerializer(
            data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        uploaded = len(request.FILES.getlist('images') or [])
        return Response(
            {'message': f'{uploaded} photo(s) uploaded.'},
            status=status.HTTP_201_CREATED,
        )
