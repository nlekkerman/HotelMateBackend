from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from PIL import Image, ImageDraw
from django.core.files.base import ContentFile
import io
from django.utils.text import slugify
from .models import (Booking, BookingCategory,
                     RestaurantBlueprint,
                     Restaurant, BookingSubcategory, DiningTable, BlueprintObjectType,
                     BlueprintObject)
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
from cloudinary.uploader import upload
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
today = timezone.localdate()


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
            return Response({"detail": "Dinner booking category or subcategory is not configured for this hotel."}, status=status.HTTP_400_BAD_REQUEST)

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
            booking_time = datetime.strptime(data.get("time"), "%H:%M").time()
        except (ValueError, TypeError):
            return Response({"detail": "Invalid date or time format."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Check available tables ---
        requested_table_ids = data.get("table_ids", [])  # List of table IDs user wants to book
        if not requested_table_ids:
            return Response({"detail": "You must select at least one table."}, status=status.HTTP_400_BAD_REQUEST)

        # Compute datetime range for overlap check
        duration_hours = data.get("duration_hours", 2)
        start_dt = datetime.combine(booking_date, booking_time)
        end_dt = start_dt + timedelta(hours=duration_hours)

        # Find tables that are already booked at that time
        conflicting_table_ids = Booking.objects.filter(
            restaurant=restaurant,
            date=booking_date,
            assigned_tables__isnull=False
        ).filter(
            Q(start_time__lt=end_dt) & Q(end_time__gt=start_dt)
        ).values_list("assigned_tables__id", flat=True)

        # Validate requested tables are available
        for table_id in requested_table_ids:
            if int(table_id) in conflicting_table_ids:
                return Response({"detail": f"Table {table_id} is already booked at this time."}, status=status.HTTP_400_BAD_REQUEST)

        data["assigned_tables"] = requested_table_ids
        data["start_time"] = booking_time
        data["end_time"] = (datetime.combine(booking_date, booking_time) + timedelta(hours=duration_hours)).time()

        serializer = BookingCreateSerializer(data=data)
        if serializer.is_valid():
            booking = serializer.save()
            out = BookingSerializer(booking)
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

    def create(self, request, *args, **kwargs):
        hotel_slug = kwargs.get("hotel_slug")
        restaurant_slug = kwargs.get("restaurant_slug")

        restaurant = get_object_or_404(Restaurant, slug=restaurant_slug, hotel__slug=hotel_slug)

        if RestaurantBlueprint.objects.filter(restaurant=restaurant).exists():
            return Response(
                {"detail": "Blueprint already exists for this restaurant."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blueprint = serializer.save(restaurant=restaurant)

        # Auto-generate image if none exists
        if not blueprint.background_image:
            width = blueprint.width
            height = blueprint.height
            grid_size = blueprint.grid_size or 25

            img = Image.new("RGB", (width, height), color="white")
            draw = ImageDraw.Draw(img)

            for x in range(0, width, grid_size):
                draw.line([(x, 0), (x, height)], fill="lightgray")
            for y in range(0, height, grid_size):
                draw.line([(0, y), (width, y)], fill="lightgray")

            temp_file = io.BytesIO()
            img.save(temp_file, format="PNG")
            temp_file.seek(0)

            # Upload to Cloudinary directly
            result = upload(temp_file, public_id=f"{restaurant_slug}_blueprint", folder="blueprints")
            blueprint.background_image = result['secure_url']
            blueprint.save()

        return Response(self.get_serializer(blueprint).data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Optionally allow changing restaurant
        restaurant_slug = request.data.get('restaurant_slug')
        if restaurant_slug:
            restaurant = get_object_or_404(Restaurant, slug=restaurant_slug)
            request.data['restaurant'] = restaurant.id

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DiningTableViewSet(viewsets.ModelViewSet):
    """
    CRUD for dining tables, placed in a blueprint. Supports creation, updating, deleting, and listing.
    """
    serializer_class = DiningTableSerializer
    lookup_field = 'id'  # Default lookup

    def get_queryset(self):
        """
        If hotel_slug and restaurant_slug are in the URL, filter tables by restaurant.
        """
        hotel_slug = self.kwargs.get('hotel_slug')
        restaurant_slug = self.kwargs.get('restaurant_slug')
        if hotel_slug and restaurant_slug:
            return DiningTable.objects.filter(
                restaurant__slug=restaurant_slug,
                restaurant__hotel__slug=hotel_slug
            )
        return DiningTable.objects.all()

    def perform_create(self, serializer):
        """
        Ensure the table is assigned to the correct restaurant via URL slugs.
        """
        hotel_slug = self.kwargs.get('hotel_slug')
        restaurant_slug = self.kwargs.get('restaurant_slug')

        restaurant = get_object_or_404(
            Restaurant, slug=restaurant_slug, hotel__slug=hotel_slug
        )
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
