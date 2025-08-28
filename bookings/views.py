from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes

from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
# Add this at the top of your views.py
from rest_framework.exceptions import PermissionDenied
from chat.utils import pusher_client
from rest_framework.pagination import PageNumberPagination
from django.utils.text import slugify
from staff.models import Staff
from .models import (Booking, BookingCategory,
                     RestaurantBlueprint,
                     Restaurant, BookingSubcategory,
                     DiningTable, BlueprintObjectType)
from .serializers import (BookingSerializer, BookingCategorySerializer,
                          BookingCreateSerializer,
                          RestaurantSerializer,
                          RestaurantBlueprintSerializer,
                          DiningTableSerializer, BlueprintObjectTypeSerializer,
                          BlueprintObjectSerializer)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from hotel.models import Hotel
from rooms.models import Room
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
today = timezone.localdate()

import logging

logger = logging.getLogger(__name__)

class NoPagination(PageNumberPagination):
    page_size = None


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('hotel', 'category', 'restaurant').all()
    serializer_class = BookingSerializer


class BookingCategoryViewSet(viewsets.ModelViewSet):
    """
    Returns all BookingCategory records (filtered by ?hotel_slug=<slug> if provided).
    """
    queryset = BookingCategory.objects.all().select_related("subcategory")
    serializer_class = BookingCategorySerializer

    def get_queryset(self):
        # Start from the class‐level queryset, then filter by hotel_slug if present
        qs = super().get_queryset()
        hotel_slug = self.request.query_params.get("hotel_slug")
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        return qs


class GuestDinnerBookingView(APIView):
    """
    Public API endpoint for guests to:
      • GET /list all dinner bookings for a given hotel
      • POST /create a new dinner booking for a given hotel/restaurant/room with table selection
    """
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug):
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            return Response({"detail": f"Hotel with slug '{hotel_slug}' not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            dinner_sub = BookingSubcategory.objects.get(name__iexact="dinner", hotel=hotel)
            dinner_cat = BookingCategory.objects.get(subcategory=dinner_sub, hotel=hotel)
        except (BookingSubcategory.DoesNotExist, BookingCategory.DoesNotExist):
            return Response({"detail": "Dinner booking category or subcategory is not configured for this hotel."}, status=status.HTTP_400_BAD_REQUEST)

        qs = Booking.objects.filter(category=dinner_cat, date__gte=today).select_related(
            "hotel", "category__subcategory", "restaurant", "seats", "room"
        )
        serializer = BookingSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, hotel_slug, restaurant_slug, room_number):
        # --- Fetch hotel, restaurant, room ---
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, hotel=hotel)
        room = get_object_or_404(Room, hotel=hotel, room_number=room_number)

        # --- Get dinner category ---
        try:
            dinner_sub = BookingSubcategory.objects.get(name__iexact="dinner", hotel=hotel)
            dinner_cat = BookingCategory.objects.get(subcategory=dinner_sub, hotel=hotel)
        except (BookingSubcategory.DoesNotExist, BookingCategory.DoesNotExist):
            return Response({"detail": "Dinner booking category or subcategory is not configured for this hotel."},
                            status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.update({
            "hotel": hotel.id,
            "restaurant": restaurant.id,
            "category": dinner_cat.id,
            "room": room.id,
        })

        # --- Inject guest if exists ---
        guest = room.guests.first()
        if guest:
            data["guest"] = guest.id

        # --- Validate booking date/time ---
        try:
            booking_date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
            start_time = datetime.strptime(data.get("start_time"), "%H:%M").time()
            end_time = datetime.strptime(data.get("end_time"), "%H:%M").time()
        except (ValueError, TypeError):
            return Response({"detail": "Invalid date or time format."}, status=status.HTTP_400_BAD_REQUEST)

        if start_time >= end_time:
            return Response({"detail": "End time must be after start time."}, status=status.HTTP_400_BAD_REQUEST)

        # Compute total guests
        adults = int(data.get("adults", 1))
        children = int(data.get("children", 0))
        infants = int(data.get("infants", 0))
        total_guests = adults + children + infants
        
        # --- Default duration handling (if end_time not provided) ---
        if not data.get("end_time"):
            duration_hours = int(data.get("duration_hours", 2))
            start_dt = datetime.combine(booking_date, start_time)
            end_dt = start_dt + timedelta(hours=duration_hours)
            data["end_time"] = end_dt.time()

        # --- Check if room already has a dinner booking for that day ---
        existing_booking = Booking.objects.filter(
            hotel=hotel,
            category=dinner_cat,
            room=room,
            date=booking_date
        ).exists()

        if existing_booking:
            return Response(
                {"detail": f"Room {room.room_number} already has a dinner booking on {booking_date}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # --- Enforce maximum 8 bookings per hour ---
        hour_start = datetime.combine(booking_date, start_time.replace(minute=0, second=0))
        hour_end = hour_start + timedelta(hours=1)

        bookings_in_hour = Booking.objects.filter(
            restaurant=restaurant,
            category=dinner_cat,
            date=booking_date,
            start_time__lt=hour_end.time(),
            end_time__gt=hour_start.time()
        ).count()

        if bookings_in_hour >= 8:
            return Response(
                {"detail": f"Maximum number of bookings (8) already reached for {hour_start.strftime('%H:%M')}–{hour_end.strftime('%H:%M')}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # --- Enforce restaurant capacity ---
        # Find overlapping bookings (same restaurant, overlapping time)
        overlapping_bookings = Booking.objects.filter(
            restaurant=restaurant,
            category=dinner_cat,
            date=booking_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        print(f"Overlapping bookings found: {overlapping_bookings.count()}")
        current_guests = sum(b.total_seats() for b in overlapping_bookings)

        print(f"Current guests booked: {current_guests}, New booking guests: {total_guests}, Capacity: {restaurant.capacity}")
        
        if current_guests + total_guests > restaurant.capacity:
            logger.info(
                f"Capacity exceeded at restaurant '{restaurant.name}' "
                f"(hotel={hotel.slug}, room={room.room_number}, date={booking_date}, "
                f"start={start_time}, end={end_time}). "
                f"Requested: {total_guests}, Already booked: {current_guests}, "
                f"Capacity: {restaurant.capacity}."
            )
            return Response(
                {"detail": (
                    f"Booking exceeds restaurant capacity of {restaurant.capacity} guests "
                    f"for this time slot. Currently booked: {current_guests}."
                )},
                status=status.HTTP_400_BAD_REQUEST
            )


        # --- Serializer handles booking creation ---
        serializer = BookingCreateSerializer(data=data)
        if serializer.is_valid():
            booking = serializer.save()
            out = BookingSerializer(booking)
            
            # ✅ Notify F&B staff
            fnb_staff = Staff.get_by_department("food-and-beverage")
            if fnb_staff.exists():
                for staff in fnb_staff:
                    staff_channel = f"{hotel.slug}-staff-{staff.id}-bookings"
                    try:
                        pusher_client.trigger(
                            staff_channel,
                            "new-dinner-booking",
                            {
                                "booking_id": booking.id,
                                "room_number": room.room_number,
                                "restaurant": restaurant.name,
                                "start_time": str(booking.start_time),
                                "end_time": str(booking.end_time),
                                "adults": adults,
                                "children": children,
                                "infants": infants,
                                "total_guests": total_guests,
                            }
                        )
                        logger.info(f"Pusher triggered for F&B staff {staff.id}, booking={booking.id}")
                    except Exception as e:
                        logger.error(f"Failed to notify F&B staff_channel={staff_channel}: {e}")
            else:
                logger.warning("No Food & Beverage staff found to notify.")

            return Response(out.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RestaurantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing restaurants.
    Supports: list, retrieve, create, update, partial_update, destroy
    Filters by hotel slug if provided as a query parameter: ?hotel_slug=hotel-slug
    Only active restaurants are returned by default.
    """
    queryset = Restaurant.objects.filter(is_active=True).select_related("hotel")
    serializer_class = RestaurantSerializer
    lookup_field = 'slug'
    def get_queryset(self):
        """
        Optionally filter restaurants by hotel slug
        """
        qs = super().get_queryset()
        hotel_slug = self.request.query_params.get("hotel_slug")
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        return qs

    def perform_create(self, serializer):
        name = serializer.validated_data.get("name")

        # Only include opening/closing times if provided
        opening_time = serializer.validated_data.get("opening_time")
        closing_time = serializer.validated_data.get("closing_time")

        serializer.save(
            slug=slugify(name),
            opening_time=opening_time if opening_time else None,
            closing_time=closing_time if closing_time else None
        )

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: mark is_active=False instead of deleting
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class RestaurantBlueprintViewSet(viewsets.ModelViewSet):
    serializer_class = RestaurantBlueprintSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # read-only for guests

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        restaurant_slug = self.kwargs.get('restaurant_slug')
        return RestaurantBlueprint.objects.filter(
            restaurant__hotel__slug=hotel_slug,
            restaurant__slug=restaurant_slug
        )

    def get_object(self):
        return get_object_or_404(
            RestaurantBlueprint,
            restaurant__hotel__slug=self.kwargs.get('hotel_slug'),
            restaurant__slug=self.kwargs.get('restaurant_slug')
        )

    # Create/update/destroy stays the same but only works for authenticated users
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        hotel_slug = kwargs.get("hotel_slug")
        restaurant_slug = kwargs.get("restaurant_slug")
        restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, hotel__slug=hotel_slug)

        if RestaurantBlueprint.objects.filter(restaurant=restaurant).exists():
            return Response({"detail": "Blueprint already exists for this restaurant."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blueprint = serializer.save(restaurant=restaurant)

        return Response(self.get_serializer(blueprint).data, status=status.HTTP_201_CREATED)


class DiningTableViewSet(viewsets.ModelViewSet):
    serializer_class = DiningTableSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = NoPagination
    
    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        restaurant_slug = self.kwargs.get('restaurant_slug')
        if hotel_slug and restaurant_slug:
            return DiningTable.objects.filter(
                restaurant__slug=restaurant_slug,
                restaurant__hotel__slug=hotel_slug
            )
        return DiningTable.objects.all()

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required")

        hotel_slug = self.kwargs.get('hotel_slug')
        restaurant_slug = self.kwargs.get('restaurant_slug')
        restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, hotel__slug=hotel_slug)
        serializer.save(restaurant=restaurant)


class BlueprintObjectTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns all available object types for blueprints (e.g., Couch, Entrance, Window)
    """
    queryset = BlueprintObjectType.objects.all()
    serializer_class = BlueprintObjectTypeSerializer
    permission_classes = [AllowAny]


class BlueprintObjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for objects placed inside a RestaurantBlueprint.
    Supports list, create, retrieve, update, delete.
    """
    serializer_class = BlueprintObjectSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        hotel_slug = self.kwargs.get('hotel_slug')
        restaurant_slug = self.kwargs.get('restaurant_slug')
        blueprint_id = self.kwargs.get('blueprint_id')

        blueprint = get_object_or_404(
            RestaurantBlueprint,
            pk=blueprint_id,
            restaurant__slug=restaurant_slug,
            restaurant__hotel__slug=hotel_slug
        )

        return blueprint.blueprint_objects.all()
    
    def perform_create(self, serializer):
        hotel_slug = self.kwargs.get('hotel_slug')
        restaurant_slug = self.kwargs.get('restaurant_slug')
        blueprint_id = self.kwargs.get('blueprint_id')

        blueprint = get_object_or_404(
            RestaurantBlueprint,
            pk=blueprint_id,
            restaurant__slug=restaurant_slug,
            restaurant__hotel__slug=hotel_slug
        )

        serializer.save(blueprint=blueprint)


class AvailableTablesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug, restaurant_slug):
        date_str = request.query_params.get("date")
        start_str = request.query_params.get("start_time")
        end_str = request.query_params.get("end_time")

        if not date_str or not start_str:
            return Response({"detail": "Date and start_time required."}, status=status.HTTP_400_BAD_REQUEST)

        # Parse requested times
        try:
            booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_str, "%H:%M").time()
            start_dt = datetime.combine(booking_date, start_time)

            if end_str:
                end_time = datetime.strptime(end_str, "%H:%M").time()
                end_dt = datetime.combine(booking_date, end_time)
            else:
                # fallback: default duration 2h
                duration_hours = float(request.query_params.get("duration_hours", 1.5))
                end_dt = start_dt + timedelta(hours=duration_hours)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid date or time format."}, status=status.HTTP_400_BAD_REQUEST)

        if start_dt >= end_dt:
            return Response({"detail": "end_time must be after start_time."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Fetch restaurant and tables ---
        restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, hotel__slug=hotel_slug)
        all_tables = DiningTable.objects.filter(restaurant=restaurant)

        # --- Find conflicting bookings ---
        bookings = Booking.objects.filter(
            restaurant=restaurant,
            date=booking_date,
            booking_tables__isnull=False
        ).distinct()

        conflicting_table_ids = []
        for b in bookings:
            b_start_dt = datetime.combine(b.date, b.start_time)
            b_end_dt = datetime.combine(b.date, b.end_time)
            # Overlap check
            if (start_dt < b_end_dt) and (end_dt > b_start_dt):
                conflicting_table_ids.extend(
                    list(b.booking_tables.values_list('table_id', flat=True))
                )

        available_tables = all_tables.exclude(id__in=conflicting_table_ids)
        serializer = DiningTableSerializer(available_tables, many=True)
        return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_bookings_seen(request, hotel_slug):
    """
    Marks all unseen dinner bookings as seen for a hotel.
    Frontend calls this when staff clicks the booking icon/button.
    """
    # Filter only unseen dinner bookings
    updated_count = Booking.objects.filter(
        hotel__slug=hotel_slug,
        seen=False,
        category__subcategory__name__iexact="dinner"
    ).update(seen=True)

    # Trigger Pusher event to update clients in real time
    channel_name = f"{hotel_slug}-staff-bookings"
    pusher_client.trigger(channel_name, "bookings-seen", {"updated": updated_count})

    return Response({"marked_seen": updated_count})