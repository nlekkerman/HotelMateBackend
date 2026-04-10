from rest_framework import viewsets, mixins, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from rooms.models import Room
from hotel.models import Hotel  # Assuming you have a Hotel model
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import RoomServiceItem, BreakfastItem, Order, BreakfastOrder
from django.http import Http404
# All notifications now handled by NotificationManager
from notifications.notification_manager import NotificationManager
from django.db import transaction
import logging

from common.guest_auth import (
    TokenAuthenticationMixin,
    PublicBurstThrottle,
    PublicSustainedThrottle,
    GuestTokenBurstThrottle,
    GuestTokenSustainedThrottle,
)
from common.guest_access import (
    resolve_guest_access,
    GuestAccessError,
)
from staff_chat.permissions import IsStaffMember, IsSameHotel
from staff.permissions import HasNavPermission

logger = logging.getLogger(__name__)

from .serializers import (
    RoomServiceItemSerializer,
    BreakfastItemSerializer,
    OrderSerializer,
    BreakfastOrderSerializer
)



def get_hotel_from_request(request):
    # Extract hotel_slug from URL kwargs in request
    hotel_slug = None
    if hasattr(request, 'parser_context'):
        hotel_slug = request.parser_context['kwargs'].get('hotel_slug')
    elif hasattr(request, 'resolver_match'):
        hotel_slug = request.resolver_match.kwargs.get('hotel_slug')

    if not hotel_slug:
        raise Http404("Hotel slug not provided")

    return get_object_or_404(Hotel, slug=hotel_slug)

class RoomServiceItemViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RoomServiceItemSerializer
    permission_classes = [permissions.AllowAny]  # Guest-facing: guests browse menu from room tablet

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return RoomServiceItem.objects.filter(hotel=hotel)

    @action(detail=False, methods=['get'], url_path=r'room/(?P<room_number>[^/.]+)/menu')
    def menu(self, request, hotel_slug=None, room_number=None):
        hotel = get_hotel_from_request(request)
        items = RoomServiceItem.objects.filter(hotel=hotel)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

class BreakfastItemViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BreakfastItemSerializer
    permission_classes = [permissions.AllowAny]  # Guest-facing: guests browse breakfast menu from room tablet

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return BreakfastItem.objects.filter(hotel=hotel)

    @action(detail=False, methods=['get'], url_path=r'room/(?P<room_number>[^/.]+)/breakfast')
    def menu(self, request, hotel_slug=None, room_number=None):
        hotel = get_hotel_from_request(request)
        items = self.get_queryset()
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

class OrderViewSet(TokenAuthenticationMixin, viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    # ---- Per-action permission dispatch ----
    # Guest-facing actions (create, room_order_history) use AllowAny at the
    # DRF layer; actual auth is enforced via guest-token validation in the
    # view body.  All other actions are staff-only.
    _GUEST_ACTIONS = {'create', 'room_order_history'}

    def get_permissions(self):
        if self.action in self._GUEST_ACTIONS:
            return [AllowAny()]
        # RBAC: staff actions require nav visibility + staff membership
        return [IsAuthenticated(), HasNavPermission('room_services'), IsStaffMember(), IsSameHotel()]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_guest_context(self, request, hotel):
        """
        Authenticate via BookingManagementToken using canonical resolver.
        Returns (booking, room) or raises GuestAccessError.
        """
        token_str = self.get_token_from_request(request)
        if not token_str:
            raise GuestAccessError("Token is required", "TOKEN_REQUIRED", 401)
        ctx = resolve_guest_access(
            token_str,
            hotel_slug=hotel.slug,
            required_scopes=['ROOM_SERVICE'],
            require_in_house=True,
        )
        return ctx.booking, ctx.room

    def _is_staff_request(self, request):
        """Return True if the request comes from an authenticated staff user."""
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'staff_profile')
        )

    # ------------------------------------------------------------------
    # Queryset
    # ------------------------------------------------------------------

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        # Filter orders for rooms in this hotel only
        return Order.objects.filter(hotel=hotel).exclude(status="completed")

    # ------------------------------------------------------------------
    # Create – requires guest token (staff can also create with their auth)
    # ------------------------------------------------------------------
    
    def perform_create(self, serializer):
        hotel = get_hotel_from_request(self.request)

        # Staff bypass: authenticated staff can create orders (dashboard use)
        if self._is_staff_request(self.request):
            order = serializer.save(hotel=hotel)
        else:
            # Guest path: validate token → derive room from booking
            try:
                booking, room = self._resolve_guest_context(self.request, hotel)
            except GuestAccessError as exc:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(detail=exc.message)

            if not room:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(detail="No room assigned to this booking")

            # Override room_number from token context (ignore client-supplied value)
            order = serializer.save(hotel=hotel, room_number=room.room_number)

        # Use unified NotificationManager for all notifications
        nm = NotificationManager()
        
        # This handles all staff notifications (porters, kitchen, waiters) 
        # plus FCM push notifications automatically
        notification_sent = nm.realtime_room_service_order_created(order)
        
        if notification_sent:
            logger.info(
                f"✅ Unified notifications sent for new order {order.id} "
                f"(Room {order.room_number}, €{order.total_price})"
            )
        else:
            logger.warning(
                f"❌ Failed to send unified notifications for new order {order.id}"
            )
    
    @action(detail=False, methods=["get"], url_path="pending-count")
    def pending_count(self, request, *args, **kwargs):
        """
        GET /room_services/{hotel_slug}/orders/pending-count/
        Returns JSON: { "count": <int> }
        """
        hotel = get_hotel_from_request(request)
        count = Order.objects.filter(hotel=hotel).filter(status="pending").count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="room-history")
    def room_order_history(self, request):
        """
        GET /room_services/{hotel_slug}/orders/room-history/?token=...
        Returns order history for the guest's assigned room.
        Requires a valid GuestBookingToken with ROOM_SERVICE scope.
        Staff users with DRF TokenAuthentication may also access by
        providing hotel_slug + room_number query params.
        """
        hotel_slug = request.query_params.get("hotel_slug")
        hotel = get_object_or_404(Hotel, slug=hotel_slug) if hotel_slug else get_hotel_from_request(request)

        # Staff bypass
        if self._is_staff_request(request):
            room_number = request.query_params.get("room_number")
            if not room_number:
                return Response({"error": "room_number query param required"}, status=400)
            queryset = Order.objects.filter(hotel=hotel, room_number=room_number)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        # Guest path – validate token
        try:
            booking, room = self._resolve_guest_context(request, hotel)
        except GuestAccessError as exc:
            return Response({"error": exc.message}, status=exc.status_code)

        if not room:
            return Response({"error": "No room assigned to this booking"}, status=403)

        queryset = Order.objects.filter(hotel=hotel, room_number=room.room_number)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="all-orders-summary")
    def all_orders_summary(self, request, hotel_slug=None):
        """
        GET /room_services/{hotel_slug}/orders/all-orders-summary/
        Query params:
            - room_number: filter by specific room
            - status: filter by status (pending/accepted/completed)
            - include_completed: include completed orders (default: true)
            - page_size: number of orders per page (default: 20)
            - page: page number (default: 1)
        Returns all orders grouped by status with summary statistics
        """
        hotel = get_hotel_from_request(request)
        
        # Get query parameters
        room_number = request.query_params.get('room_number')
        status_filter = request.query_params.get('status')
        include_completed_param = request.query_params.get(
            'include_completed', 'true'
        )
        include_completed = include_completed_param.lower() == 'true'
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        # Start with base queryset - ALWAYS filter by hotel
        queryset = Order.objects.filter(hotel=hotel)
        
        # Exclude completed orders only if requested
        if not include_completed:
            queryset = queryset.exclude(status='completed')
        
        # Apply filters
        if room_number:
            queryset = queryset.filter(room_number=room_number)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Order by most recent
        queryset = queryset.order_by('-created_at')
        
        # Get total count before pagination
        total_count = queryset.count()
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_orders = queryset[start:end]
        
        # Serialize paginated orders
        serializer = self.get_serializer(paginated_orders, many=True)
        
        # Calculate summary statistics (on full queryset, not paginated)
        from django.db.models import Count
        status_summary = Order.objects.filter(hotel=hotel)
        
        # Apply same completed filter to summary
        if not include_completed:
            status_summary = status_summary.exclude(status='completed')
        
        # Apply same filters to summary
        if room_number:
            status_summary = status_summary.filter(room_number=room_number)
        
        status_summary = status_summary.values('status').annotate(
            count=Count('id')
        )
        
        # Group orders by room (from paginated results)
        room_summary = {}
        for order in paginated_orders:
            room = str(order.room_number)
            if room not in room_summary:
                room_summary[room] = {
                    'room_number': order.room_number,
                    'order_count': 0,
                    'orders': []
                }
            room_summary[room]['order_count'] += 1
            room_summary[room]['orders'].append({
                'id': order.id,
                'status': order.status,
                'total_price': float(order.total_price),
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat()
            })
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'pagination': {
                'total_orders': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous
            },
            'filters': {
                'room_number': room_number,
                'status': status_filter,
                'include_completed': include_completed
            },
            'status_breakdown': list(status_summary),
            'orders_by_room': list(room_summary.values()),
            'orders': serializer.data
        })

    @action(detail=False, methods=["get"], url_path="order-history")
    def order_history(self, request, hotel_slug=None):
        """
        GET /room_services/{hotel_slug}/orders/order-history/
        Returns ONLY completed orders with filtering options
        Query params:
            - room_number: filter by specific room
            - date_from: filter orders from this date (YYYY-MM-DD)
            - date_to: filter orders until this date (YYYY-MM-DD)
            - page_size: number of orders per page (default: 20)
            - page: page number (default: 1)
        """
        hotel = get_hotel_from_request(request)
        
        # Get query parameters
        room_number = request.query_params.get('room_number')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        # Start with completed orders only
        queryset = Order.objects.filter(
            hotel=hotel,
            status='completed'
        )
        
        # Apply filters
        if room_number:
            queryset = queryset.filter(room_number=room_number)
        
        if date_from:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from_obj)
        
        if date_to:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to_obj)
        
        # Order by most recent
        queryset = queryset.order_by('-created_at')
        
        # Get total count before pagination
        total_count = queryset.count()
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_orders = queryset[start:end]
        
        # Serialize
        serializer = self.get_serializer(paginated_orders, many=True)
        
        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'pagination': {
                'total_orders': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous
            },
            'filters': {
                'room_number': room_number,
                'date_from': date_from,
                'date_to': date_to
            },
            'orders': serializer.data
        })

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_status = instance.status
        new_status = request.data.get("status")

        # Validate status transitions - enforce proper workflow
        valid_transitions = {
            "pending": ["accepted"],
            "accepted": ["completed"],
            "completed": [],  # no further change allowed
        }

        if new_status and new_status != instance.status:
            allowed = valid_transitions.get(instance.status, [])
            if new_status not in allowed:
                return Response(
                    {"error": f"Invalid status transition from '{instance.status}' to '{new_status}'. Allowed: {allowed}"},
                    status=400
                )

        logger.info(
            f"🔄 Order {instance.id} status update: "
            f"{old_status} → {new_status} (Room {instance.room_number})"
        )

        instance.status = new_status
        instance.save()
        
        # Use unified NotificationManager for real-time notifications
        nm = NotificationManager()
        
        # Send normalized room service order updated event
        # This handles both Pusher real-time events and FCM notifications automatically
        notification_sent = nm.realtime_room_service_order_updated(instance)
        
        if notification_sent:
            logger.info(
                f"✅ Unified notifications sent successfully for order {instance.id} "
                f"(status: {old_status} → {instance.status})"
            )
        else:
            logger.warning(
                f"❌ Failed to send unified notifications for order {instance.id}"
            )
        
        # Count notifications are now handled automatically by NotificationManager
        # No additional count update calls needed with unified system
        logger.info(f"📊 Order count updates handled by unified notification system")

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
class BreakfastOrderViewSet(TokenAuthenticationMixin, viewsets.ModelViewSet):
    serializer_class = BreakfastOrderSerializer
    throttle_classes = [GuestTokenBurstThrottle, GuestTokenSustainedThrottle]

    # ---- Per-action permission dispatch ----
    # Guest-facing: create (token validated in perform_create).
    # All other actions are staff-only.
    _GUEST_ACTIONS = {'create'}

    def get_permissions(self):
        if self.action in self._GUEST_ACTIONS:
            return [AllowAny()]
        # RBAC: staff actions require nav visibility + staff membership
        return [IsAuthenticated(), HasNavPermission('room_services'), IsStaffMember(), IsSameHotel()]

    def _resolve_guest_context(self, request, hotel):
        token_str = self.get_token_from_request(request)
        if not token_str:
            raise GuestAccessError("Token is required", "TOKEN_REQUIRED", 401)
        ctx = resolve_guest_access(
            token_str,
            hotel_slug=hotel.slug,
            required_scopes=['ROOM_SERVICE'],
            require_in_house=True,
        )
        return ctx.booking, ctx.room

    def _is_staff_request(self, request):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'staff_profile')
        )

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        queryset = BreakfastOrder.objects.filter(
            hotel=hotel,
            status__in=["pending", "accepted"]
        )
        
        room_number = self.request.query_params.get('room_number')
        if room_number:
            queryset = queryset.filter(room_number=room_number)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        hotel_slug = self.kwargs.get('hotel_slug')
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        context['hotel'] = hotel
        return context

    def perform_create(self, serializer):
        hotel = self.get_serializer_context()['hotel']

        # Staff bypass: authenticated staff can create orders (dashboard use)
        if self._is_staff_request(self.request):
            order = serializer.save(hotel=hotel)
        else:
            # Guest path: validate token → derive room from booking
            try:
                booking, room = self._resolve_guest_context(
                    self.request, hotel
                )
            except GuestAccessError as exc:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(detail=exc.message)

            if not room:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(detail="No room assigned to this booking")

            order = serializer.save(hotel=hotel, room_number=room.room_number)
        
        # Prepare notification data
        order_data = {
            "order_id": order.id,
            "room_number": order.room_number,
            "delivery_time": (order.delivery_time.isoformat()
                            if order.delivery_time else None),
            "created_at": order.created_at.isoformat(),
            "status": order.status
        }
        
        # Use unified NotificationManager for all breakfast notifications
        nm = NotificationManager()
        
        # This handles all staff notifications (porters, kitchen, waiters)
        # Note: Using room service method for breakfast - may need dedicated breakfast method
        notification_sent = nm.realtime_room_service_order_created(order)
        
        if notification_sent:
            logger.info(
                f"✅ Unified breakfast notifications sent for order {order.id} "
                f"(Room {order.room_number}, delivery: {order.delivery_time})"
            )
        else:
            logger.warning(
                f"❌ Failed to send unified breakfast notifications for order {order.id}"
            )
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get("status")

        valid_transitions = {
            "pending": ["accepted"],
            "accepted": ["completed"],
            "completed": [],  # no further change allowed
        }

        if new_status and new_status != instance.status:
            allowed = valid_transitions.get(instance.status, [])
            if new_status not in allowed:
                return Response(
                    {"error": f"Invalid status transition from '{instance.status}' to '{new_status}'."},
                    status=400
                )

        return super().partial_update(request, *args, **kwargs)

    
    @action(detail=False, methods=["get"], url_path="breakfast-pending-count")
    def pending_count(self, request, hotel_slug=None):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        count = BreakfastOrder.objects.filter(hotel=hotel, status="pending").count()
        return Response({"count": count})




@api_view(['POST'])
@permission_classes([AllowAny])
def save_guest_fcm_token(request, hotel_slug, room_number):
    """
    Save FCM token for a checked-in guest's room.
    Requires a valid BookingManagementToken; the room is derived from the
    token's booking (the URL room_number must match).
    """
    hotel = get_hotel_from_request(request)
    fcm_token = request.data.get('fcm_token')

    if not fcm_token:
        return Response(
            {'error': 'fcm_token is required'},
            status=400
        )

    # --- Authenticate via canonical resolver ---
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token_str = ''
    if auth_header.startswith('Bearer '):
        token_str = auth_header[7:]
    elif auth_header.startswith('GuestToken '):
        token_str = auth_header[11:]
    else:
        token_str = request.GET.get('token', '')

    if not token_str:
        return Response({'error': 'Guest token is required'}, status=401)

    try:
        ctx = resolve_guest_access(
            token_str,
            hotel_slug=hotel.slug,
            required_scopes=['ROOM_SERVICE'],
            require_in_house=True,
        )
    except GuestAccessError as exc:
        return Response({'error': exc.message}, status=exc.status_code)

    room = ctx.room
    if not room:
        return Response({'error': 'No room assigned to this booking'}, status=403)

    # Verify URL room_number matches token-derived room
    if str(room.room_number) != str(room_number):
        return Response({'error': 'Room mismatch'}, status=403)

    # Save FCM token to token-derived room
    room.guest_fcm_token = fcm_token
    room.save(update_fields=['guest_fcm_token'])

    logger.info(
        f"FCM token saved for room {room.room_number} "
        f"at {hotel.name} (booking {ctx.booking.booking_id})"
    )

    return Response({
        'success': True,
        'message': 'FCM token saved successfully'
    })



