from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from .models import Room, RoomType
from .serializers import RoomSerializer, RoomTypeSerializer
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
from django.utils import timezone
from staff_chat.permissions import IsStaffMember, IsSameHotel
from django.db.models import Count
from chat.utils import pusher_client


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


class RoomTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing room types"""
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        staff = getattr(user, 'staff_profile', None)
        
        if staff and staff.hotel:
            return RoomType.objects.filter(hotel=staff.hotel).order_by('sort_order', 'name')
        
        return RoomType.objects.none()
    
    def perform_create(self, serializer):
        staff = getattr(self.request.user, 'staff_profile', None)
        if staff and staff.hotel:
            serializer.save(hotel=staff.hotel)
        else:
            raise PermissionDenied("You must be assigned to a hotel to create a room type.")


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



        serializer = GuestSerializer(data=guest_data)
        if serializer.is_valid():
            guest = serializer.save(room=room)  # Set room directly on guest
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
    Bulk room checkout - Non-destructive by default
    POST /api/staff/hotel/{hotel_slug}/rooms/checkout/
    {
      "room_ids": [3, 7, 11],
      "destructive": false  // optional, requires admin for true
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
    
    # Destructive mode requires admin permissions
    if destructive and not request.user.is_superuser:
        return Response(
            {"detail": "Destructive checkout requires admin permissions."},
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
                
                # Mark room unoccupied
                room.is_occupied = False
                room.room_status = 'CHECKOUT_DIRTY'
                room.guest_fcm_token = None
                room.save()
                
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
                    room.is_occupied = False
                    room.room_status = 'CHECKOUT_DIRTY'
                    room.guest_fcm_token = None
                    
                    # Add note for rooms cleared without bookings
                    staff_name = f"{staff_user.first_name} {staff_user.last_name}".strip() or staff_user.email
                    room.add_turnover_note(
                        f"Room cleared (no active bookings) at {now().strftime('%Y-%m-%d %H:%M')} by {staff_name}",
                        staff_user
                    )
                    room.save()
                    results["rooms_cleared"].append(room.room_number)
            
            # Real-time notification for room status change
            
            pusher_client.trigger(
                f'hotel-{hotel_slug}',
                'room-status-changed',
                {
                    'room_number': room.room_number,
                    'old_status': 'OCCUPIED',
                    'new_status': 'CHECKOUT_DIRTY',
                    'timestamp': now().isoformat()
                }
            )
    
    return Response({
        "detail": f"Processed {rooms.count()} room(s) in hotel '{hotel_slug}'",
        "results": results
    }, status=status.HTTP_200_OK) 
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


# ============================================================================
# ROOM TURNOVER WORKFLOW ENDPOINTS (Staff-Only)
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def start_cleaning(request, hotel_slug, room_number):
    """Transition room to CLEANING_IN_PROGRESS"""
    # Check canonical navigation permission
    if not request.user.staff_profile.allowed_navigation_items.filter(slug='rooms').exists():
        return Response({'error': 'Rooms permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('CLEANING_IN_PROGRESS'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to CLEANING_IN_PROGRESS'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    room.room_status = 'CLEANING_IN_PROGRESS'
    room.add_turnover_note("Cleaning started", request.user.staff_profile)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': 'CLEANING_IN_PROGRESS',
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room cleaning started'})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def mark_cleaned(request, hotel_slug, room_number):
    """Mark room as cleaned, transition to CLEANED_UNINSPECTED"""
    # Check canonical navigation permission
    if not request.user.staff_profile.allowed_navigation_items.filter(slug='rooms').exists():
        return Response({'error': 'Rooms permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if not room.can_transition_to('CLEANED_UNINSPECTED'):
        return Response(
            {'error': f'Cannot transition from {room.room_status} to CLEANED_UNINSPECTED'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    notes = request.data.get('notes', '')
    old_status = room.room_status
    
    room.room_status = 'CLEANED_UNINSPECTED'
    room.last_cleaned_at = timezone.now()
    room.cleaned_by_staff = request.user.staff_profile
    
    note_text = "Room cleaned"
    if notes:
        note_text += f" - {notes}"
    room.add_turnover_note(note_text, request.user.staff_profile)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': 'CLEANED_UNINSPECTED',
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room marked as cleaned'})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def inspect_room(request, hotel_slug, room_number):
    """Inspect room - pass -> READY_FOR_GUEST, fail -> CHECKOUT_DIRTY"""
    # Check canonical navigation permission
    if not request.user.staff_profile.allowed_navigation_items.filter(slug='rooms').exists():
        return Response({'error': 'Rooms permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if room.room_status != 'CLEANED_UNINSPECTED':
        return Response(
            {'error': f'Cannot inspect room in {room.room_status} status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    passed = request.data.get('passed', False)
    notes = request.data.get('notes', '')
    old_status = room.room_status
    
    room.last_inspected_at = timezone.now()
    room.inspected_by_staff = request.user.staff_profile
    
    if passed:
        room.room_status = 'READY_FOR_GUEST'
        note_text = "Inspection passed - ready for guest"
    else:
        room.room_status = 'CHECKOUT_DIRTY'
        note_text = "Inspection failed - needs re-cleaning"
    
    if notes:
        note_text += f" - {notes}"
    room.add_turnover_note(note_text, request.user.staff_profile)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': room.room_status,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({
        'message': 'Room inspection completed',
        'passed': passed,
        'status': room.room_status
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def mark_maintenance(request, hotel_slug, room_number):
    """Mark room as requiring maintenance - requires maintenance navigation permission"""
    # Check canonical navigation permission
    if not request.user.staff_profile.allowed_navigation_items.filter(slug='maintenance').exists():
        return Response({'error': 'Maintenance permission required'}, status=403)
    
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
    room.room_status = 'MAINTENANCE_REQUIRED'
    room.maintenance_required = True
    room.maintenance_priority = priority
    room.maintenance_notes = notes
    room.add_turnover_note(f"Maintenance required ({priority} priority): {notes}", request.user.staff_profile)
    room.save()
    
    # Real-time notification
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
            'old_status': old_status,
            'new_status': 'MAINTENANCE_REQUIRED',
            'priority': priority,
            'timestamp': timezone.now().isoformat()
        }
    )
    
    return Response({'message': 'Room marked for maintenance'})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
def complete_maintenance(request, hotel_slug, room_number):
    """Mark maintenance as completed - requires maintenance navigation permission"""
    # Check canonical navigation permission
    if not request.user.staff_profile.allowed_navigation_items.filter(slug='maintenance').exists():
        return Response({'error': 'Maintenance permission required'}, status=403)
    
    room = get_object_or_404(Room, hotel__slug=hotel_slug, room_number=room_number)
    
    if room.room_status != 'MAINTENANCE_REQUIRED':
        return Response(
            {'error': f'Room is not in maintenance status'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_status = room.room_status
    room.maintenance_required = False
    room.maintenance_priority = None
    room.maintenance_notes = ''
    
    # If room was cleaned and inspected, go to ready, otherwise back to dirty
    if room.last_cleaned_at and room.last_inspected_at:
        # Check if cleaning/inspection happened after last checkout
        # For now, default to ready if both exist
        room.room_status = 'READY_FOR_GUEST'
    else:
        room.room_status = 'CHECKOUT_DIRTY'
    
    room.add_turnover_note("Maintenance completed", request.user.staff_profile)
    room.save()
    
    # Real-time notification  
    pusher_client.trigger(
        f'hotel-{hotel_slug}',
        'room-status-changed',
        {
            'room_number': room.room_number,
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
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
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
@permission_classes([IsAuthenticated, IsStaffMember, IsSameHotel])
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
@permission_classes([IsAuthenticated, IsStaffMember])
def bulk_create_rooms(request, hotel_slug, room_type_id):
    """
    POST: Bulk create Room instances for a room type
    
    Payload formats:
    1. {"room_numbers": [101, 102, 201]}
    2. {"ranges": [{"start": 101, "end": 110}, {"start": 201, "end": 205}]}
    """
    # Resolve hotel and enforce scoping
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Ensure room type belongs to this hotel
    room_type = get_object_or_404(RoomType, id=room_type_id, hotel=hotel)
    
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
    
    # Create new rooms in transaction
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
    
    except Exception as e:
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

