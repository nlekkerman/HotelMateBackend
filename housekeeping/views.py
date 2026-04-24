"""
Housekeeping Views

Staff-authenticated API endpoints for housekeeping workflow management.
All endpoints require staff authentication and hotel scoping.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

# Import existing permission classes
from staff_chat.permissions import IsStaffMember, IsSameHotel
from staff.permissions import (
    CanAssignHousekeepingTask,
    CanCancelHousekeepingTask,
    CanCreateHousekeepingTask,
    CanDeleteHousekeepingTask,
    CanExecuteHousekeepingTask,
    CanOverrideHousekeepingRoomStatus,
    CanReadHousekeepingDashboard,
    CanReadHousekeepingStatusHistory,
    CanReadHousekeepingTasks,
    CanUpdateHousekeepingTask,
    CanViewHousekeepingModule,
    has_capability,
)
from staff.capability_catalog import HOUSEKEEPING_TASK_ASSIGN

from rooms.models import Room
from .models import HousekeepingTask, RoomStatusEvent
from .serializers import (
    HousekeepingTaskSerializer,
    HousekeepingTaskAssignSerializer,
    RoomStatusUpdateSerializer,
    RoomStatusEventSerializer,
    HousekeepingDashboardSerializer,
    RoomSummarySerializer
)
from .services import set_room_status, get_room_dashboard_data


# Writable fields on HousekeepingTaskSerializer (excluding `hotel`,
# `created_by`, `started_at`, `completed_at` which are read-only after the
# Phase 6C serializer fix). Used by `_required_task_update_caps` to decide
# which capability/-ies a PATCH/PUT body actually requires.
_TASK_ACTION_FIELDS = {
    'assigned_to': 'assign',
    'status': 'status',
}
_TASK_GENERIC_UPDATE_FIELDS = {
    'room', 'booking', 'task_type', 'priority', 'note',
}


def _required_task_update_caps(request):
    """
    Phase 6C PATCH/PUT split (mirrors Phase 6B.2 rooms split).

    Inspect the parsed request body and return the set of capability
    permission classes required for it. Pure inspection \u2014 no side
    effects.
    """
    from staff.permissions import (
        CanAssignHousekeepingTask as _Assign,
        CanCancelHousekeepingTask as _Cancel,
        CanExecuteHousekeepingTask as _Execute,
        CanUpdateHousekeepingTask as _Update,
    )

    data = getattr(request, 'data', {}) or {}
    # Form noise that should never trigger a capability requirement.
    keys = {k for k in data.keys() if k != 'csrfmiddlewaretoken'}

    classes = []

    if 'assigned_to' in keys:
        classes.append(_Assign)

    if 'status' in keys:
        new_status = data.get('status')
        if new_status == 'CANCELLED':
            classes.append(_Cancel)
        elif new_status in ('IN_PROGRESS', 'DONE'):
            classes.append(_Execute)
        else:
            # OPEN or anything unknown \u2014 treat as a generic edit so
            # task.update is required at minimum.
            classes.append(_Update)

    # Any other writable field falls under the generic update capability.
    if keys & _TASK_GENERIC_UPDATE_FIELDS:
        classes.append(_Update)

    # If body is empty or contains only ignored keys, still require the
    # generic update capability so an empty PATCH cannot bypass auth.
    if not classes:
        classes.append(_Update)

    # De-duplicate while preserving order.
    seen = set()
    unique = []
    for cls in classes:
        if cls not in seen:
            seen.add(cls)
            unique.append(cls)
    return unique


class HousekeepingTaskViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for housekeeping tasks.
    """
    serializer_class = HousekeepingTaskSerializer

    def get_permissions(self):
        # Phase 6C: capability-only enforcement. Module visibility is
        # CanViewHousekeepingModule; the per-action class is added on
        # top. PATCH/PUT routes through a payload-aware split so the
        # generic task.update capability cannot mutate action fields
        # (assigned_to / status) without the corresponding capability.
        base = [
            IsAuthenticated(), IsStaffMember(), IsSameHotel(),
            CanViewHousekeepingModule(),
        ]

        action = self.action
        if action in ('list', 'retrieve'):
            base.append(CanReadHousekeepingTasks())
        elif action == 'create':
            base.append(CanReadHousekeepingTasks())
            base.append(CanCreateHousekeepingTask())
        elif action in ('update', 'partial_update'):
            base.append(CanReadHousekeepingTasks())
            for cls in _required_task_update_caps(self.request):
                base.append(cls())
        elif action == 'destroy':
            base.append(CanDeleteHousekeepingTask())
        elif action == 'assign':
            base.append(CanReadHousekeepingTasks())
            base.append(CanAssignHousekeepingTask())
        elif action in ('start', 'complete'):
            base.append(CanReadHousekeepingTasks())
            base.append(CanExecuteHousekeepingTask())
        else:
            # Unknown action — read gate only; subclasses must opt in.
            base.append(CanReadHousekeepingTasks())
        return base
    
    def get_queryset(self):
        """Filter tasks by staff's hotel"""
        staff = self.request.user.staff_profile
        hotel = staff.hotel
        
        queryset = HousekeepingTask.objects.filter(
            hotel=hotel
        ).select_related(
            'room', 'room__room_type', 'assigned_to', 'created_by', 'booking'
        ).order_by('-priority', '-created_at')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        task_type_filter = self.request.query_params.get('task_type')
        if task_type_filter:
            queryset = queryset.filter(task_type=task_type_filter)
        
        assigned_to_me = self.request.query_params.get('assigned_to')
        if assigned_to_me == 'me':
            queryset = queryset.filter(assigned_to=staff)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set hotel and created_by when creating tasks"""
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel, created_by=staff)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, hotel_slug=None, pk=None):
        """
        POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{task_id}/assign/
        
        Assign task to a staff member.
        """
        task = self.get_object()
        serializer = HousekeepingTaskAssignSerializer(
            data=request.data,
            context={'request': request, 'task': task}
        )
        
        if serializer.is_valid():
            from staff.models import Staff
            requesting_staff = request.user.staff_profile
            # Hotel-scoped lookup mirrors the serializer fix; safe because
            # the serializer already validated same-hotel existence.
            assigned_staff = Staff.objects.get(
                id=serializer.validated_data['assigned_to_id'],
                hotel_id=requesting_staff.hotel_id,
            )

            task.assigned_to = assigned_staff
            task.save(update_fields=['assigned_to'])
            
            # Return updated task
            task_serializer = HousekeepingTaskSerializer(task)
            return Response({
                'message': f'Task assigned to {f"{assigned_staff.first_name} {assigned_staff.last_name}".strip() or assigned_staff.email or "Staff"}',
                'task': task_serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def start(self, request, hotel_slug=None, pk=None):
        """
        POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{task_id}/start/
        
        Start working on a task.
        """
        task = self.get_object()
        staff = request.user.staff_profile
        
        # Validate staff can start this task
        if task.assigned_to and task.assigned_to != staff:
            return Response(
                {'error': 'Task is assigned to another staff member'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if task.status not in ['OPEN']:
            return Response(
                {'error': f'Cannot start task with status {task.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update task status
        task.status = 'IN_PROGRESS'
        task.started_at = timezone.now()
        if not task.assigned_to:
            task.assigned_to = staff
        task.save(update_fields=['status', 'started_at', 'assigned_to'])
        
        task_serializer = HousekeepingTaskSerializer(task)
        return Response({
            'message': 'Task started',
            'task': task_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, hotel_slug=None, pk=None):
        """
        POST /api/staff/hotel/{hotel_slug}/housekeeping/tasks/{task_id}/complete/
        
        Mark task as completed.
        """
        task = self.get_object()
        staff = request.user.staff_profile
        
        # Validate staff can complete this task
        if task.assigned_to and task.assigned_to != staff:
            return Response(
                {'error': 'Task is assigned to another staff member'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if task.status not in ['IN_PROGRESS']:
            return Response(
                {'error': f'Cannot complete task with status {task.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update task status
        task.status = 'DONE'
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'completed_at'])
        
        task_serializer = HousekeepingTaskSerializer(task)
        return Response({
            'message': 'Task completed',
            'task': task_serializer.data
        })


class HousekeepingDashboardViewSet(viewsets.ViewSet):
    """
    Housekeeping dashboard with room status overview and task summary.

    Phase 6C: capability-gated end-to-end. Tier no longer affects the
    payload — callers who hold housekeeping.task.assign see the
    hotel-wide open task queue; everyone else only sees their own.
    """
    permission_classes = [
        IsAuthenticated, IsStaffMember, IsSameHotel,
        CanViewHousekeepingModule, CanReadHousekeepingDashboard,
    ]

    def list(self, request, hotel_slug=None):
        staff = request.user.staff_profile
        hotel = staff.hotel

        dashboard_data = get_room_dashboard_data(hotel)

        my_tasks = HousekeepingTask.objects.filter(
            hotel=hotel,
            assigned_to=staff,
            status__in=['OPEN', 'IN_PROGRESS']
        ).select_related('room', 'room__room_type', 'assigned_to', 'created_by')

        open_tasks = []
        if has_capability(request.user, HOUSEKEEPING_TASK_ASSIGN):
            open_tasks = HousekeepingTask.objects.filter(
                hotel=hotel,
                status='OPEN'
            ).select_related('room', 'room__room_type', 'assigned_to', 'created_by')[:20]

        return Response({
            'counts': dashboard_data['counts'],
            'rooms_by_status': dashboard_data['rooms_by_status'],
            'my_open_tasks': HousekeepingTaskSerializer(my_tasks, many=True).data,
            'open_tasks': HousekeepingTaskSerializer(open_tasks, many=True).data,
            'total_rooms': dashboard_data['total_rooms'],
        })


class RoomStatusViewSet(viewsets.ViewSet):
    """
    Room status management endpoints.

    Phase 6C: module visibility is capability-based
    (CanViewHousekeepingModule). update_status delegates the per-action
    capability check to ``housekeeping.policy.can_change_room_status``
    (one of the three room_status capabilities). manager_override is
    additionally gated by HOUSEKEEPING_ROOM_STATUS_OVERRIDE; tier no
    longer participates. status_history requires
    HOUSEKEEPING_ROOM_STATUS_HISTORY_READ.
    """
    def get_permissions(self):
        base = [
            IsAuthenticated(), IsStaffMember(), IsSameHotel(),
            CanViewHousekeepingModule(),
        ]
        if self.action == 'manager_override':
            base.append(CanOverrideHousekeepingRoomStatus())
        elif self.action == 'status_history':
            base.append(CanReadHousekeepingStatusHistory())
        # update_status: capability check happens inside
        # policy.can_change_room_status (one of transition / front_desk /
        # override). Module visibility above is the only class-level gate.
        return base
    
    def update_status(self, request, hotel_slug=None, room_id=None):
        """
        POST /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status/
        
        Update room status using canonical service.
        """
        staff = request.user.staff_profile
        hotel = staff.hotel
        
        # Get room
        room = get_object_or_404(Room, id=room_id, hotel=hotel)
        
        # Validate and process status update
        serializer = RoomStatusUpdateSerializer(
            data=request.data,
            context={'request': request, 'room': room}
        )
        
        if serializer.is_valid():
            try:
                # Use canonical service for status update
                updated_room = set_room_status(
                    room=room,
                    to_status=serializer.validated_data['to_status'],
                    staff=staff,
                    source=serializer.validated_data['source'],
                    note=serializer.validated_data.get('note', '')
                )
                
                # Get latest status event for response
                latest_event = RoomStatusEvent.objects.filter(room=room).first()
                
                return Response({
                    'message': f'Room {room.room_number} status updated to {updated_room.room_status}',
                    'room': {
                        'id': updated_room.id,
                        'room_number': updated_room.room_number,
                        'room_status': updated_room.room_status,
                        'last_cleaned_at': updated_room.last_cleaned_at,
                        'last_inspected_at': updated_room.last_inspected_at,
                        'maintenance_required': updated_room.maintenance_required,
                    },
                    'status_event': RoomStatusEventSerializer(latest_event).data if latest_event else None
                })
            
            except DjangoValidationError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def manager_override(self, request, hotel_slug=None, room_id=None):
        """
        POST /api/staff/hotel/{hotel_slug}/housekeeping/rooms/{room_id}/manager_override/
        
        Manager override to change room status bypassing normal restrictions.
        Requires staff_admin+ tier (canonical RBAC).
        """
        staff = request.user.staff_profile
        hotel = staff.hotel
        
        # Get room
        room = get_object_or_404(Room, id=room_id, hotel=hotel)
        
        # Get parameters
        to_status = request.data.get('to_status')
        note = request.data.get('note', 'Manager override')
        
        if not to_status:
            return Response(
                {'error': 'to_status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status exists
        valid_statuses = dict(Room.ROOM_STATUS_CHOICES)
        if to_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status: {to_status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use manager override to bypass normal restrictions
            updated_room = set_room_status(
                room=room,
                to_status=to_status,
                staff=staff,
                source="MANAGER_OVERRIDE",
                note=note
            )
            
            # Get latest status event for response
            latest_event = RoomStatusEvent.objects.filter(room=room).first()
            
            return Response({
                'message': f'Manager override: Room {room.room_number} status changed to {updated_room.room_status}',
                'room': {
                    'id': updated_room.id,
                    'room_number': updated_room.room_number,
                    'room_status': updated_room.room_status,
                    'last_cleaned_at': updated_room.last_cleaned_at,
                    'last_inspected_at': updated_room.last_inspected_at,
                    'maintenance_required': updated_room.maintenance_required,
                },
                'status_event': RoomStatusEventSerializer(latest_event).data if latest_event else None
            })
        
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def status_history(self, request, hotel_slug=None, room_id=None):
        """
        GET /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status-history/
        
        Get room status change history.
        """
        staff = request.user.staff_profile
        hotel = staff.hotel
        
        # Get room
        room = get_object_or_404(Room, id=room_id, hotel=hotel)
        
        # Get status history
        limit = min(int(request.query_params.get('limit', 50)), 100)
        events = RoomStatusEvent.objects.filter(
            room=room
        ).select_related(
            'changed_by', 'hotel'
        ).order_by('-created_at')[:limit]
        
        serializer = RoomStatusEventSerializer(events, many=True)
        return Response({
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'current_status': room.room_status,
            },
            'status_history': serializer.data,
            'total_events': len(serializer.data)
        })
