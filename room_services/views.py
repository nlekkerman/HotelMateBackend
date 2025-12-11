from rest_framework import viewsets, mixins, permissions
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from rooms.models import Room
from hotel.models import Hotel  # Assuming you have a Hotel model
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import RoomServiceItem, BreakfastItem, Order, BreakfastOrder
from django.http import Http404
from notifications.pusher_utils import (
    notify_kitchen_staff,
    notify_porters,
    notify_room_service_waiters
)
from notifications.utils import (
    notify_porters_of_room_service_order,
    notify_kitchen_staff_of_room_service_order
)
from notifications.notification_manager import NotificationManager
from django.db import transaction
import logging

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
    permission_classes = [permissions.AllowAny]

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
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        return BreakfastItem.objects.filter(hotel=hotel)

    @action(detail=False, methods=['get'], url_path=r'room/(?P<room_number>[^/.]+)/breakfast')
    def menu(self, request, hotel_slug=None, room_number=None):
        hotel = get_hotel_from_request(request)
        items = self.get_queryset()
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        hotel = get_hotel_from_request(self.request)
        # Filter orders for rooms in this hotel only
        return Order.objects.filter(hotel=hotel).exclude(status="completed")
    
    def perform_create(self, serializer):
        hotel = get_hotel_from_request(self.request)
        order = serializer.save(hotel=hotel)

        # Notify Kitchen staff (they prepare the food)
        order_data = {
            "order_id": order.id,
            "room_number": order.room_number,
            "total_price": float(order.total_price),
            "created_at": order.created_at.isoformat(),
            "status": order.status
        }
        kitchen_count = notify_kitchen_staff(
            hotel, 'new-room-service-order', order_data
        )
        logger.info(
            f"Room service order {order.id}: "
            f"Notified {kitchen_count} kitchen staff"
        )

        # Notify Room Service Waiters (they coordinate)
        waiter_count = notify_room_service_waiters(
            hotel, 'new-room-service-order', order_data
        )
        logger.info(
            f"Room service order {order.id}: "
            f"Notified {waiter_count} room service waiters"
        )

        # Notify Porters (they deliver) - both Pusher and FCM push
        notify_porters_of_room_service_order(order)
        
        # Notify Kitchen Staff - FCM push notifications
        notify_kitchen_staff_of_room_service_order(order)
    
    @action(detail=False, methods=["get"], url_path="pending-count")
    def pending_count(self, request, *args, **kwargs):
        """
        GET /room_services/{hotel_slug}/orders/pending-count/
        Returns JSON: { "count": <int> }
        """
        hotel = get_hotel_from_request(request)
        count = Order.objects.filter(hotel=hotel).filter(status="pending").count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="room-history", permission_classes=[AllowAny])
    def room_order_history(self, request):
        hotel_slug = request.query_params.get("hotel_slug")
        room_number = request.query_params.get("room_number")

        if not hotel_slug or not room_number:
            return Response({"error": "hotel_slug and room_number are required"}, status=400)

        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        queryset = Order.objects.filter(hotel=hotel, room_number=room_number)
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
        
        # Also notify porters about updated pending count using old system
        # (This could be migrated to NotificationManager in the future)
        pending_count = Order.objects.filter(
            hotel=instance.hotel,
            status='pending'
        ).count()
        
        count_data = {
            "pending_count": pending_count,
            "order_type": "room_service_orders"
        }
        
        notify_porters(
            instance.hotel,
            'order-count-update',
            count_data
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
class BreakfastOrderViewSet(viewsets.ModelViewSet):
    serializer_class = BreakfastOrderSerializer

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
        order = serializer.save(hotel=hotel)
        
        # Prepare notification data
        order_data = {
            "order_id": order.id,
            "room_number": order.room_number,
            "delivery_time": (order.delivery_time.isoformat()
                            if order.delivery_time else None),
            "created_at": order.created_at.isoformat(),
            "status": order.status
        }
        
        # Notify Kitchen staff
        kitchen_count = notify_kitchen_staff(
            hotel, 'new-breakfast-order', order_data
        )
        logger.info(
            f"Breakfast order {order.id}: "
            f"Notified {kitchen_count} kitchen staff"
        )
        
        # Notify Room Service Waiters
        waiter_count = notify_room_service_waiters(
            hotel, 'new-breakfast-order', order_data
        )
        logger.info(
            f"Breakfast order {order.id}: "
            f"Notified {waiter_count} room service waiters"
        )
        
        # Notify Porters
        porter_count = notify_porters(
            hotel, 'new-breakfast-delivery', order_data
        )
        logger.info(
            f"Breakfast order {order.id}: "
            f"Notified {porter_count} porters"
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
def validate_pin(request, hotel_slug, room_number):  # add hotel_slug here
    hotel = get_hotel_from_request(request)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)
    pin = request.data.get('pin')
    if pin == room.guest_id_pin:
        return Response({'valid': True})
    return Response({'valid': False}, status=401)


@api_view(['POST'])
@permission_classes([AllowAny])
def save_guest_fcm_token(request, hotel_slug, room_number):
    """
    Save FCM token for anonymous guest in a specific room.
    Called after PIN verification to enable push notifications.
    """
    hotel = get_hotel_from_request(request)
    room = get_object_or_404(Room, room_number=room_number, hotel=hotel)
    fcm_token = request.data.get('fcm_token')
    
    if not fcm_token:
        return Response(
            {'error': 'fcm_token is required'},
            status=400
        )
    
    # Save FCM token to room
    room.guest_fcm_token = fcm_token
    room.save()
    
    logger.info(
        f"FCM token saved for room {room_number} "
        f"at {hotel.name}"
    )
    
    return Response({
        'success': True,
        'message': 'FCM token saved successfully'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_dinner_pin(request, hotel_slug, restaurant_slug, room_number):
    """
    Validate guest PIN for dinner booking in a specific restaurant and room.
    """
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    room = get_object_or_404(Room, hotel=hotel, room_number=room_number)
    pin = request.data.get("pin")

    if pin == room.guest_id_pin:
        return Response({'valid': True})
    return Response({'valid': False}, status=401)
