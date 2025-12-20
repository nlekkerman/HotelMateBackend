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

from hotel.models import Hotel
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
from .policy import can_view_dashboard


class HousekeepingDashboardViewSet(viewsets.ViewSet):
    """
    Housekeeping dashboard with room status overview and task summary.
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def list(self, request, hotel_slug=None):
        """
        GET /api/staff/hotel/{hotel_slug}/housekeeping/dashboard/
        
        Returns:
        - Room counts by status
        - Rooms grouped by status
        - Tasks assigned to requesting staff
        - All open tasks (optional)
        """
        staff = request.user.staff_profile
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Validate staff belongs to hotel
        if staff.hotel_id != hotel.id:
            return Response(
                {'error': 'Access denied to this hotel'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check dashboard access permissions
        if not can_view_dashboard(staff):
            return Response(
                {'error': 'Insufficient permissions to view housekeeping dashboard'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get room dashboard data
        dashboard_data = get_room_dashboard_data(hotel)
        
        # Get staff's assigned tasks
        my_tasks = HousekeepingTask.objects.filter(
            hotel=hotel,
            assigned_to=staff,
            status__in=['OPEN', 'IN_PROGRESS']
        ).select_related('room', 'room__room_type', 'assigned_to', 'created_by')
        
        # Get all open tasks (for managers)
        open_tasks = []
        if staff.access_level in ['staff_admin', 'super_staff_admin']:
            open_tasks = HousekeepingTask.objects.filter(
                hotel=hotel,
                status='OPEN'
            ).select_related('room', 'room__room_type', 'assigned_to', 'created_by')[:20]
        
        # Serialize data
        response_data = {
            'counts': dashboard_data['counts'],
            'rooms_by_status': dashboard_data['rooms_by_status'],
            'my_open_tasks': HousekeepingTaskSerializer(my_tasks, many=True).data,
            'open_tasks': HousekeepingTaskSerializer(open_tasks, many=True).data,
            'total_rooms': dashboard_data['total_rooms']
        }
        
        return Response(response_data)


class HousekeepingTaskViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for housekeeping tasks.
    """
    serializer_class = HousekeepingTaskSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def get_queryset(self):
        """Filter tasks by staff's hotel"""
        staff = self.request.user.staff_profile
        hotel = get_object_or_404(Hotel, slug=self.kwargs['hotel_slug'])
        
        # Validate staff belongs to hotel
        if staff.hotel_id != hotel.id:
            return HousekeepingTask.objects.none()
        
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
        hotel = get_object_or_404(Hotel, slug=self.kwargs['hotel_slug'])
        
        # Validate staff belongs to hotel
        if staff.hotel_id != hotel.id:
            raise DjangoValidationError("Access denied to this hotel")
        
        serializer.save(hotel=hotel, created_by=staff)
    
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
            # Get assigned staff member
            from staff.models import Staff
            assigned_staff = Staff.objects.get(id=serializer.validated_data['assigned_to_id'])
            
            # Update task
            task.assigned_to = assigned_staff
            if task.status == 'OPEN':
                # Optionally keep status as OPEN, or change to IN_PROGRESS
                pass
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


class RoomStatusViewSet(viewsets.ViewSet):
    """
    Room status management endpoints.
    """
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    
    def update_status(self, request, hotel_slug=None, room_id=None):
        """
        POST /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status/
        
        Update room status using canonical service.
        """
        staff = request.user.staff_profile
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Validate staff belongs to hotel
        if staff.hotel_id != hotel.id:
            return Response(
                {'error': 'Access denied to this hotel'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
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
    
    def status_history(self, request, hotel_slug=None, room_id=None):
        """
        GET /api/staff/hotel/{hotel_slug}/rooms/{room_id}/status-history/
        
        Get room status change history.
        """
        staff = request.user.staff_profile
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Validate staff belongs to hotel
        if staff.hotel_id != hotel.id:
            return Response(
                {'error': 'Access denied to this hotel'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
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
