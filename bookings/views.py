from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Booking, BookingCategory
from .serializers import BookingSerializer, BookingCategorySerializer, BookingCreateSerializer, RestaurantSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Restaurant, BookingSubcategory
from hotel.models import Hotel
from rooms.models import Room
from .serializers import BookingCreateSerializer
from django.utils import timezone
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
      • POST /create a new dinner booking for a given hotel/restaurant/room

    URL patterns (example):
      GET   /api/dinner-bookings/{hotel_slug}/
      POST  /api/dinner-bookings/{hotel_slug}/{restaurant_slug}/{room_number}/

    This view is accessible without authentication (AllowAny).
    """
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug):
        # ——————————————————————
        # 1) LIST all “Dinner” bookings for this hotel
        # ——————————————————————
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            return Response(
                {"detail": f"Hotel with slug '{hotel_slug}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Find the subcategory named “Dinner” for this hotel (case‐insensitive)
        try:
            dinner_sub = BookingSubcategory.objects.get(name__iexact="dinner", hotel=hotel)
            dinner_cat = BookingCategory.objects.get(subcategory=dinner_sub, hotel=hotel)
        except BookingSubcategory.DoesNotExist:
            return Response(
                {"detail": "Dinner subcategory is not configured for this hotel."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except BookingCategory.DoesNotExist:
            return Response(
                {"detail": "Dinner booking category is not configured for this hotel."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch all Booking objects whose category matches “dinner_cat”
        qs = Booking.objects.filter(category=dinner_cat, date__gte=today).select_related(
            "hotel", "category__subcategory", "restaurant", "seats"
        )
        serializer = BookingSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, hotel_slug, restaurant_slug, room_number):
        # —————————————————————————————————————————————
        # 2) CREATE a new “Dinner” booking for this hotel
        # —————————————————————————————————————————————
        #
        # The URL is expected to be:
        #   POST /api/dinner-bookings/{hotel_slug}/{restaurant_slug}/{room_number}/
        #
        # Body JSON should at least include:
        #   {
        #     "date":      "YYYY-MM-DD",
        #     "time":      "HH:MM:SS",
        #     "note":      "Optional note string",
        #     "seats": {   <-- nested seats payload
        #         "total":    4,
        #         "adults":   2,
        #         "children": 2,
        #         "infants":  0
        #     }
        #   }
        #
        # We will:
        #   1. Validate the hotel by slug
        #   2. Validate the restaurant by slug + hotel
        #   3. Validate the room number under this hotel
        #   4. Ensure a “Dinner” subcategory and category exist for this hotel
        #   5. Merge those IDs into `request.data` and run BookingCreateSerializer

        # STEP 1: Validate hotel
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            return Response(
                {"detail": f"Hotel with slug '{hotel_slug}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # STEP 2: Validate restaurant under that hotel
        try:
            restaurant = Restaurant.objects.get(slug=restaurant_slug, hotel=hotel)
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": f"Restaurant '{restaurant_slug}' not found for hotel '{hotel_slug}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        # STEP 3: Validate room under that hotel
        try:
            room = Room.objects.get(hotel=hotel, room_number=room_number)
        except Room.DoesNotExist:
            return Response(
                {"detail": f"Room '{room_number}' not found in hotel '{hotel_slug}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        # STEP 4: Validate “Dinner” subcategory & category for this hotel
        try:
            dinner_sub = BookingSubcategory.objects.get(name__iexact="dinner", hotel=hotel)
            dinner_cat = BookingCategory.objects.get(subcategory=dinner_sub, hotel=hotel)
        except BookingSubcategory.DoesNotExist:
            return Response(
                {"detail": "Dinner booking subcategory is not configured for this hotel."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except BookingCategory.DoesNotExist:
            return Response(
                {"detail": "Dinner booking category is not configured for this hotel."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # STEP 5: Merge in the required IDs and hand off to BookingCreateSerializer
        data = request.data.copy()
        data.update({
            "hotel": hotel.id,
            "restaurant": restaurant.id,
            "category": dinner_cat.id,
            # If your Booking model does not have a “room_number” field,
            # just omit this. If it does, include it here:
            # "room_number": room.room_number,
        })

        serializer = BookingCreateSerializer(data=data)
        if serializer.is_valid():
            booking = serializer.save()
            # Return the fully‐nested representation using BookingSerializer
            out = BookingSerializer(booking)
            return Response(out.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.filter(is_active=True).select_related("hotel")
    serializer_class = RestaurantSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        hotel_slug = self.request.query_params.get("hotel_slug")
        if hotel_slug:
            qs = qs.filter(hotel__slug=hotel_slug)
        return qs

