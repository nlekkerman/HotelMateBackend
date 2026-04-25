from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, filters, status
from .models import Room, RoomType, RoomImage
from .serializers import RoomSerializer, RoomStaffSerializer, RoomImageSerializer, BulkRoomImageUploadSerializer, RoomImageReorderSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from hotel.models import Hotel
from guests.models import Guest
from room_services.models import Order, BreakfastOrder
from chat.models import Conversation, RoomMessage
from rest_framework.decorators import api_view, permission_classes
from django.db import models, transaction
from django.utils.timezone import now
from django.utils import timezone
from staff_chat.permissions import IsStaffMember, IsSameHotel
from staff.permissions import (
    CanViewRooms,
    CanReadRoomInventory,
    CanCreateRoomInventory,
    CanUpdateRoomInventory,
    CanDeleteRoomInventory,
    CanReadRoomMedia,
    CanManageRoomMedia,
    CanReadRoomStatus,
    CanTransitionRoomStatus,
    CanInspectRoom,
    CanFlagRoomMaintenance,
    CanClearRoomMaintenance,
    CanSetRoomOutOfOrder,
    CanBulkCheckoutRooms,
    CanDestructiveCheckoutRooms,
)
from django.db.models import Count
from chat.utils import pusher_client
import logging

logger = logging.getLogger(__name__)


def _payload_changes_out_of_order(request) -> bool:
    """
    Return True if the incoming write request mutates the
    ``is_out_of_order`` flag on a Room row.

    Used to escalate inventory-update to the room.out_of_order.set
    capability without forcing every inventory patch through the
    out-of-order gate.
    """
    if request is None:
        return False
    if request.method not in ('POST', 'PUT', 'PATCH'):
        return False
    data = getattr(request, 'data', None) or {}
    return 'is_out_of_order' in data


def _payload_changes_only_out_of_order(request) -> bool:
    """
    Return True iff the incoming PATCH/PUT body targets
    ``is_out_of_order`` and nothing else writable on the Room row.

    Used to permit ``room.out_of_order.set``-holding roles
    (e.g. maintenance_manager) to flip OOO without also holding
    ``room.inventory.update``. When other fields are present, the
    inventory-update capability is required.
    """
    if request is None:
        return False
    if request.method not in ('PUT', 'PATCH'):
        return False
    data = getattr(request, 'data', None) or {}
    if 'is_out_of_order' not in data:
        return False
    # Keys treated as no-op metadata (not real Room fields).
    ignorable = {'csrfmiddlewaretoken'}
    payload_keys = {k for k in data.keys() if k not in ignorable}
    return payload_keys == {'is_out_of_order'}


class RoomPagination(PageNumberPagination):
    page_size = 10  # items per page
    page_size_query_param = 'page_size'  # allow client to set page size with ?page_size=xx
    max_page_size = 100


class StaffRoomViewSet(viewsets.ModelViewSet):
    """
    Canonical staff CRUD for rooms (inventory management).
    Hotel-scoped, staff-only, hotel injected server-side.
    """
    serializer_class = RoomStaffSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]
    pagination_class = RoomPagination
    lookup_field = 'room_number'
    filter_backends = [filters.SearchFilter]
    search_fields = ['room_number']

    def get_permissions(self):
        perms = [
            IsAuthenticated(),
            IsStaffMember(),
            IsSameHotel(),
            CanViewRooms(),
        ]
        if self.action in ('list', 'retrieve'):
            perms.append(CanReadRoomInventory())
        elif self.action == 'create':
            perms.append(CanCreateRoomInventory())
        elif self.action in ('update', 'partial_update'):
            # Phase 6B.2 — drift fix for room.out_of_order.set.
            # A payload that ONLY toggles is_out_of_order requires
            # CanReadRoomInventory + CanSetRoomOutOfOrder (no
            # inventory-update), so roles like maintenance_manager whose
            # only manage-bucket leak is OOO can actually use it.
            # Any other field in the payload keeps the classic
            # CanUpdateRoomInventory requirement; a mixed payload
            # requires BOTH caps.
            if _payload_changes_only_out_of_order(self.request):
                perms.append(CanReadRoomInventory())
                perms.append(CanSetRoomOutOfOrder())
            elif _payload_changes_out_of_order(self.request):
                perms.append(CanUpdateRoomInventory())
                perms.append(CanSetRoomOutOfOrder())
            else:
                perms.append(CanUpdateRoomInventory())
        elif self.action == 'destroy':
            perms.append(CanDeleteRoomInventory())
        else:
            perms.append(CanUpdateRoomInventory())
        return perms

    def get_queryset(self):
        try:
            staff = self.request.user.staff_profile
            return Room.objects.filter(
                hotel=staff.hotel
            ).select_related('room_type').order_by('room_number')
        except AttributeError:
            return Room.objects.none()

    def perform_create(self, serializer):
        staff = self.request.user.staff_profile
        serializer.save(hotel=staff.hotel)

    def perform_update(self, serializer):
        serializer.save()


@api_view(['POST'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanBulkCheckoutRooms,
])
def checkout_rooms(request, hotel_slug):
    """
    Bulk room checkout - Non-destructive by default
    POST /api/staff/hotel/{hotel_slug}/rooms/checkout/
    {
      "room_ids": [3, 7, 11],
      "destructive": false  // true requires room.checkout.destructive capability
    }
    """
    from room_bookings.services.checkout import checkout_booking
    from hotel.models import Hotel, RoomBooking

    room_ids = request.data.get('room_ids')
    destructive = request.data.get('destructive', False)

    if not isinstance(room_ids, list) or not room_ids:
        return Response(
            {"detail": "`room_ids` must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Destructive mode requires an additional capability.
    if destructive and not CanDestructiveCheckoutRooms().has_permission(request, None):
        return Response(
            {"detail": "Destructive checkout requires the room.checkout.destructive capability."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    staff_user = request.user.staff_profile
    
    # Only rooms in this hotel that match the IDs
    rooms = Room.objects.filter(hotel=hotel, id__in=room_ids)
    
    if not rooms.exists():
        return Response(
            {"detail": "No matching rooms found for this hotel."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    results = {
        "checked_out_bookings": [],
        "rooms_cleared": [],
        "destructive_mode": destructive
    }
    
    with transaction.atomic():
        for room in rooms:
            if destructive:
                # DESTRUCTIVE MODE: Old behavior (nuclear option)
                # Delete all Guest objects linked to this room
                Guest.objects.filter(room=room).delete()
                
                # Note: GuestChatSession removed - using token-based auth now
                
                # Delete all conversations & their messages for this room
                Conversation.objects.filter(room=room).delete()
                RoomMessage.objects.filter(room=room).delete()
                
                # Delete any open room-service & breakfast orders
                Order.objects.filter(
                    hotel=room.hotel,
                    room_number=room.room_number
                ).delete()
                BreakfastOrder.objects.filter(
                    hotel=room.hotel,
                    room_number=room.room_number
                ).delete()
                
                # Use canonical housekeeping service for room status
                from housekeeping.services import set_room_status
                staff = getattr(request.user, 'staff_profile', None)
                
                # Clear occupancy and FCM token manually (not handled by housekeeping service)
                room.is_occupied = False
                room.guest_fcm_token = None
                room.save(update_fields=['is_occupied', 'guest_fcm_token'])
                
                # Set status through canonical service
                try:
                    set_room_status(
                        room=room,
                        to_status='CHECKOUT_DIRTY',
                        staff=staff,
                        source='SYSTEM',
                        note='Destructive bulk checkout'
                    )
                except ValidationError as e:
                    logger.error(f"Failed to set room status for room {room.room_number} during destructive checkout: {e}")
                    # Continue with bulk operation but log the failure
                    continue
                
                results["rooms_cleared"].append(room.room_number)
                
                # Log destructive action
                logger.warning(
                    f"DESTRUCTIVE bulk checkout on room {room.room_number} "
                    f"by {staff_user.email} at hotel {hotel.name}"
                )
                
            else:
                # NON-DESTRUCTIVE MODE: Use booking-driven checkout
                # Find active bookings in this room
                active_bookings = RoomBooking.objects.filter(
                    assigned_room=room,
                    checked_out_at__isnull=True,
                    hotel=hotel
                )
                
                for booking in active_bookings:
                    try:
                        checkout_booking(
                            booking=booking,
                            performed_by=staff_user,
                            source="bulk_room_checkout",
                        )
                        results["checked_out_bookings"].append(booking.booking_id)
                    except ValueError as e:
                        logger.warning(f"Could not checkout booking {booking.booking_id}: {e}")
                
                # If room has no bookings but is marked occupied, clear it
                if room.is_occupied and not active_bookings.exists():
                    # Use canonical housekeeping service
                    from housekeeping.services import set_room_status
                    
                    # Clear occupancy and FCM token manually
                    room.is_occupied = False
                    room.guest_fcm_token = None
                    room.save(update_fields=['is_occupied', 'guest_fcm_token'])
                    
                    # Set status through canonical service
                    staff_name = f"{staff_user.first_name} {staff_user.last_name}".strip() or staff_user.email
                    try:
                        set_room_status(
                            room=room,
                            to_status='CHECKOUT_DIRTY',
                            staff=staff_user if hasattr(staff_user, 'staff_profile') else None,
                            source='SYSTEM',
                            note=f"Room cleared (no active bookings) at {now().strftime('%Y-%m-%d %H:%M')} by {staff_name}"
                        )
                    except ValidationError as e:
                        logger.error(f"Failed to set room status for room {room.room_number} during bulk checkout: {e}")
                        # Continue with bulk operation but log the failure
                        continue
                    results["rooms_cleared"].append(room.room_number)
            
            # Real-time notification handled by canonical service
    
    return Response({
        "detail": f"Processed {rooms.count()} room(s) in hotel '{hotel_slug}'",
        "results": results
    }, status=status.HTTP_200_OK)


# ============================================================================
# ROOM TURNOVER WORKFLOW ENDPOINTS (Staff-Only)
# ============================================================================

@api_view(['POST'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanTransitionRoomStatus,
])
def start_cleaning(request, hotel_slug, room_number):
    """Transition room to CLEANING_IN_PROGRESS"""
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('CLEANING_IN_PROGRESS'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to CLEANING_IN_PROGRESS'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    
    # Use canonical housekeeping service
    from housekeeping.services import set_room_status
    staff = getattr(request.user, 'staff_profile', None)
    
    try:
        set_room_status(
            room=room,
            to_status='CLEANING_IN_PROGRESS',
            staff=staff,
            source='HOUSEKEEPING',
            note='Cleaning started'
        )
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Real-time notification handled by canonical service
    # pusher_client.trigger removed - service handles via transaction.on_commit
    return Response({
        'message': 'Cleaning started',
        'old_status': old_status,
            'new_status': 'CLEANING_IN_PROGRESS',
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room cleaning started'})


@api_view(['POST'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanTransitionRoomStatus,
])
def mark_cleaned(request, hotel_slug, room_number):
    """Mark room as cleaned, transition to CLEANED_UNINSPECTED"""
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('CLEANED_UNINSPECTED'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to CLEANED_UNINSPECTED'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    notes = request.data.get('notes', '')
    old_status = room.room_status
    
    # Use canonical housekeeping service
    from housekeeping.services import set_room_status
    staff = getattr(request.user, 'staff_profile', None)
    
    note_text = "Room cleaned"
    if notes:
        note_text += f" - {notes}"
    
    try:
        set_room_status(
            room=room,
            to_status='CLEANED_UNINSPECTED',
            staff=staff,
            source='HOUSEKEEPING',
            note=note_text
        )
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Real-time notification handled by canonical service
    return Response({
        'message': 'Room marked as cleaned',
        'old_status': old_status,
        'new_status': 'CLEANED_UNINSPECTED'
    })


@api_view(['POST'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanInspectRoom,
])
def inspect_room(request, hotel_slug, room_number):
    """Inspect room - pass -> READY_FOR_GUEST, fail -> CHECKOUT_DIRTY"""
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if room.room_status != 'CLEANED_UNINSPECTED':
        return Response(
            {'error': f'Cannot inspect room in {room.room_status} status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    passed = request.data.get('passed', False)
    notes = request.data.get('notes', '')
    old_status = room.room_status
    
    # Use canonical housekeeping service
    from housekeeping.services import set_room_status
    staff = getattr(request.user, 'staff_profile', None)
    
    if passed:
        to_status = 'READY_FOR_GUEST'
        note_text = "Inspection passed - ready for guest"
    else:
        to_status = 'CHECKOUT_DIRTY'
        note_text = "Inspection failed - needs re-cleaning"
    
    if notes:
        note_text += f" - {notes}"
        
    try:
        set_room_status(
            room=room,
            to_status=to_status,
            staff=staff,
            source='HOUSEKEEPING',
            note=note_text
        )
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Real-time notification handled by canonical service
    return Response({
        'message': 'Room inspection completed',
        'passed': passed,
        'status': room.room_status
    })


@api_view(['POST'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanFlagRoomMaintenance,
])
def mark_maintenance(request, hotel_slug, room_number):
    """Mark room as requiring maintenance."""
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('MAINTENANCE_REQUIRED'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to MAINTENANCE_REQUIRED'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    priority = request.data.get('priority', 'MED')
    notes = request.data.get('notes', '')
    
    if priority not in ['LOW', 'MED', 'HIGH']:
        return Response(
            {'error': 'Priority must be LOW, MED, or HIGH'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    
    # Use canonical housekeeping service
    from housekeeping.services import set_room_status
    staff = getattr(request.user, 'staff_profile', None)
    
    # Set priority and notes first (service will update these too but this ensures consistency)
    room.maintenance_priority = priority
    room.save(update_fields=['maintenance_priority'])
    
    try:
        set_room_status(
            room=room,
            to_status='MAINTENANCE_REQUIRED',
            staff=staff,
            source='HOUSEKEEPING',
            note=f"Maintenance required ({priority} priority): {notes}"
        )
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Real-time notification handled by canonical service
    return Response({
        'message': 'Maintenance marked',
        'old_status': old_status,
            'new_status': 'MAINTENANCE_REQUIRED',
            'priority': priority,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room marked for maintenance'})


@api_view(['POST'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanClearRoomMaintenance,
])
def complete_maintenance(request, hotel_slug, room_number):
    """Mark maintenance as completed."""
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if room.room_status != 'MAINTENANCE_REQUIRED':
        return Response(
            {'error': f'Room is not in maintenance status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    
    # Use canonical housekeeping service
    from housekeeping.services import set_room_status
    staff = getattr(request.user, 'staff_profile', None)
    
    # If room was cleaned and inspected, go to ready, otherwise back to dirty
    if room.last_cleaned_at and room.last_inspected_at:
        # Check if cleaning/inspection happened after last checkout
        # For now, default to ready if both exist
        to_status = 'READY_FOR_GUEST'
        note_text = "Maintenance completed"
    else:
        to_status = 'CHECKOUT_DIRTY'
        note_text = "Maintenance completed - needs cleaning"
    
    try:
        set_room_status(
            room=room,
            to_status=to_status,
            staff=staff,
            source='HOUSEKEEPING',
            note=note_text
        )
    except ValidationError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Real-time notification handled by canonical service
    return Response({
        'message': 'Maintenance completed',
        'old_status': old_status,
            'new_status': room.room_status,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({
        'message': 'Maintenance completed',
        'new_status': room.room_status
    })


# ============================================================================
# ROOM TURNOVER DASHBOARD ENDPOINTS (Staff-Only)
# ============================================================================

@api_view(['GET'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanReadRoomStatus,
])
def turnover_rooms(request, hotel_slug):
    """Get rooms grouped by turnover status"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    rooms_by_status = {}
    for status_code, status_label in Room.ROOM_STATUS_CHOICES:
        rooms = Room.objects.filter(
            hotel=hotel,
            room_status=status_code
        ).select_related('room_type', 'cleaned_by_staff', 'inspected_by_staff')
        
        rooms_by_status[status_code] = {
            'label': status_label,
            'count': rooms.count(),
            'rooms': RoomSerializer(rooms, many=True).data
        }
    
    return Response(rooms_by_status)


@api_view(['GET']) 
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanReadRoomStatus,
])
def turnover_stats(request, hotel_slug):
    """Get turnover statistics and metrics"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    total_rooms = hotel.rooms.filter(is_active=True).count()
    
    stats = {
        'total_rooms': total_rooms,
        'bookable_rooms': hotel.rooms.filter(
            room_status__in=['READY_FOR_GUEST'],
            is_active=True,
            is_out_of_order=False,  # Hard override flag
            maintenance_required=False
        ).count(),
        'occupied_rooms': hotel.rooms.filter(room_status='OCCUPIED').count(),
        'dirty_rooms': hotel.rooms.filter(room_status='CHECKOUT_DIRTY').count(),
        'cleaning_in_progress': hotel.rooms.filter(room_status='CLEANING_IN_PROGRESS').count(),
        'awaiting_inspection': hotel.rooms.filter(room_status='CLEANED_UNINSPECTED').count(),
        'maintenance_required': hotel.rooms.filter(maintenance_required=True).count(),
        'out_of_order': hotel.rooms.filter(room_status='OUT_OF_ORDER').count(),
    }
    
    # Add maintenance breakdown
    maintenance_by_priority = hotel.rooms.filter(
        maintenance_required=True
    ).values('maintenance_priority').annotate(count=Count('id'))
    
    stats['maintenance_by_priority'] = {
        item['maintenance_priority']: item['count'] 
        for item in maintenance_by_priority
    }
    
    return Response(stats)


# ============================================================================
# CANONICAL CHECK-IN / CHECK-OUT ENDPOINTS (Staff-Only)
# ============================================================================


# ============================================================================
# BULK ROOM CREATION ENDPOINT (Staff-Only)
# ============================================================================

@api_view(['POST'])
@permission_classes([
    IsAuthenticated, IsStaffMember, IsSameHotel,
    CanViewRooms, CanCreateRoomInventory,
])
def bulk_create_rooms(request, hotel_slug, room_type_id):
    """
    POST: Bulk create Room instances for a room type
    
    Payload formats:
    1. {"room_numbers": [101, 102, 201]}
    2. {"ranges": [{"start": 101, "end": 110}, {"start": 201, "end": 205}]}
    """
    from housekeeping.models import RoomStatusEvent

    # Resolve hotel and enforce scoping
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Ensure room type belongs to this hotel and is active
    room_type = get_object_or_404(RoomType, id=room_type_id, hotel=hotel)
    if not room_type.is_active:
        return Response(
            {'error': 'Cannot create rooms under an inactive room type'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Resolve staff for audit trail
    staff = getattr(request.user, 'staff_profile', None)
    
    # Parse request payload
    room_numbers = request.data.get('room_numbers', [])
    ranges = request.data.get('ranges', [])
    
    # Expand ranges and collect all room numbers
    all_room_numbers = set(room_numbers)
    
    for range_spec in ranges:
        start = range_spec.get('start')
        end = range_spec.get('end')
        
        if not isinstance(start, int) or not isinstance(end, int):
            return Response(
                {'error': 'Range start and end must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if start > end:
            return Response(
                {'error': 'Range start cannot be greater than end'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Expand range inclusive
        all_room_numbers.update(range(start, end + 1))
    
    # Validate room numbers
    invalid_numbers = [num for num in all_room_numbers if not isinstance(num, int) or num < 1 or num > 99999]
    if invalid_numbers:
        return Response(
            {
                'error': 'Invalid room numbers',
                'invalid_numbers': invalid_numbers,
                'message': 'Room numbers must be positive integers between 1 and 99999'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not all_room_numbers:
        return Response(
            {'error': 'No room numbers provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check for existing rooms
    existing_rooms = Room.objects.filter(
        hotel=hotel,
        room_number__in=all_room_numbers
    ).values_list('room_number', flat=True)
    
    existing_numbers = list(existing_rooms)
    new_numbers = [num for num in all_room_numbers if num not in existing_numbers]
    
    # Create new rooms in transaction with audit trail
    created_rooms = []
    try:
        with transaction.atomic():
            for room_number in new_numbers:
                room = Room.objects.create(
                    hotel=hotel,
                    room_number=room_number,
                    room_type=room_type,
                    room_status='READY_FOR_GUEST',
                    is_active=True,
                    is_occupied=False,
                    is_out_of_order=False
                )
                created_rooms.append({
                    'id': room.id,
                    'room_number': room.room_number,
                    'room_type_id': room.room_type.id,
                    'room_status': room.room_status
                })
                # Audit trail for room creation
                RoomStatusEvent.objects.create(
                    hotel=hotel,
                    room=room,
                    from_status='',
                    to_status='READY_FOR_GUEST',
                    changed_by=staff,
                    source='SYSTEM',
                    note=f'Room created via bulk provisioning (room type: {room_type.name})'
                )
    
    except Exception as e:
        logger.error(f"Bulk room creation failed for hotel {hotel_slug}: {e}")
        return Response(
            {'error': f'Failed to create rooms: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'created_count': len(created_rooms),
        'skipped_existing': sorted(existing_numbers),
        'created_rooms': sorted(created_rooms, key=lambda x: x['room_number']),
        'room_type': {
            'id': room_type.id,
            'name': room_type.name,
            'code': room_type.code
        }
    }, status=status.HTTP_201_CREATED)


# ============================================================================
# ROOM IMAGE GALLERY
# ============================================================================

class RoomImageViewSet(viewsets.ModelViewSet):
    """
    Staff CRUD for room gallery images.
    Hotel-scoped, staff-only. Follows the GalleryImageViewSet pattern.
    """
    serializer_class = RoomImageSerializer
    permission_classes = [IsAuthenticated, IsStaffMember, IsSameHotel]

    def get_permissions(self):
        perms = [
            IsAuthenticated(),
            IsStaffMember(),
            IsSameHotel(),
            CanViewRooms(),
        ]
        if self.action in ('list', 'retrieve'):
            perms.append(CanReadRoomMedia())
        else:
            perms.append(CanManageRoomMedia())
        return perms

    def get_queryset(self):
        try:
            staff = self.request.user.staff_profile
        except AttributeError:
            return RoomImage.objects.none()

        queryset = RoomImage.objects.filter(
            room__hotel=staff.hotel
        ).select_related('room')

        # Optional filter by room
        room_id = self.request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)

        return queryset.order_by('sort_order', 'created_at')

    def _get_staff_room(self, room_id):
        """Fetch room ensuring it belongs to the staff's hotel."""
        staff = self.request.user.staff_profile
        return get_object_or_404(Room, id=room_id, hotel=staff.hotel)

    def perform_create(self, serializer):
        room = self._get_staff_room(serializer.validated_data['room'].id)

        # Auto-assign sort_order
        max_order = room.images.aggregate(
            models.Max('sort_order')
        )['sort_order__max'] or -1

        # First image becomes cover if no cover exists
        has_cover = room.images.filter(is_cover=True).exists()
        is_cover = serializer.validated_data.get('is_cover', False)
        if not has_cover and not is_cover:
            is_cover = True

        # If this image is marked as cover, unset existing cover
        if is_cover:
            room.images.filter(is_cover=True).update(is_cover=False)

        serializer.save(
            room=room,
            sort_order=max_order + 1,
            is_cover=is_cover,
        )

    def perform_update(self, serializer):
        instance = self.get_object()
        is_cover = serializer.validated_data.get('is_cover', instance.is_cover)

        # If setting this as cover, unset existing cover
        if is_cover and not instance.is_cover:
            instance.room.images.filter(is_cover=True).update(is_cover=False)

        serializer.save()

    def perform_destroy(self, instance):
        room = instance.room
        was_cover = instance.is_cover

        # Delete from Cloudinary
        if instance.image and instance.image.public_id:
            try:
                import cloudinary.uploader
                cloudinary.uploader.destroy(instance.image.public_id)
            except Exception:
                logger.warning(
                    f"Failed to delete Cloudinary image {instance.image.public_id} "
                    f"for room {room.room_number}"
                )

        instance.delete()

        # Promote next image to cover if we deleted the cover
        if was_cover:
            next_image = room.images.order_by('sort_order', 'created_at').first()
            if next_image:
                next_image.is_cover = True
                next_image.save(update_fields=['is_cover'])

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request, hotel_slug=None):
        """
        Bulk upload images to a room.
        POST body: room (ID), images (array of files)
        """
        room_id = request.data.get('room')
        if not room_id:
            return Response(
                {'error': 'room field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        room = self._get_staff_room(room_id)

        serializer = BulkRoomImageUploadSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        images = serializer.validated_data['images']

        max_order = room.images.aggregate(
            models.Max('sort_order')
        )['sort_order__max'] or -1

        has_cover = room.images.filter(is_cover=True).exists()

        created_images = []
        for idx, image_file in enumerate(images):
            is_cover = (not has_cover and idx == 0)
            if is_cover:
                has_cover = True

            room_image = RoomImage.objects.create(
                room=room,
                image=image_file,
                sort_order=max_order + idx + 1,
                is_cover=is_cover,
            )
            created_images.append(room_image)

        response_serializer = RoomImageSerializer(created_images, many=True)
        return Response({
            'message': f'{len(created_images)} image(s) uploaded successfully',
            'images': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request, hotel_slug=None):
        """
        Reorder images for a room.
        POST body: { "image_ids": [5, 3, 7, 1] }
        """
        serializer = RoomImageReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_ids = serializer.validated_data['image_ids']

        staff = request.user.staff_profile
        images = RoomImage.objects.filter(
            id__in=image_ids,
            room__hotel=staff.hotel
        )

        if images.count() != len(image_ids):
            return Response(
                {'error': 'Some image IDs are invalid or do not belong to your hotel'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for order, image_id in enumerate(image_ids):
            RoomImage.objects.filter(id=image_id).update(sort_order=order)

        return Response({'message': 'Images reordered successfully'})

    @action(detail=True, methods=['post'], url_path='set-cover')
    def set_cover(self, request, pk=None, hotel_slug=None):
        """Set an image as the cover image for its room."""
        image = self.get_object()
        image.room.images.filter(is_cover=True).update(is_cover=False)
        image.is_cover = True
        image.save(update_fields=['is_cover'])
        return Response(RoomImageSerializer(image).data)

