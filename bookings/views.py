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
    """
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug):
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
        except Hotel.DoesNotExist:
            return Response(
                {"detail": f"Hotel with slug '{hotel_slug}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            dinner_sub = BookingSubcategory.objects.get(name__iexact="dinner", hotel=hotel)
            dinner_cat = BookingCategory.objects.get(subcategory=dinner_sub, hotel=hotel)
        except (BookingSubcategory.DoesNotExist, BookingCategory.DoesNotExist):
            return Response(
                {"detail": "Dinner booking category or subcategory is not configured for this hotel."},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = Booking.objects.filter(category=dinner_cat, date__gte=today).select_related(
            "hotel", "category__subcategory", "restaurant", "seats", "room"
        )
        serializer = BookingSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, hotel_slug, restaurant_slug, room_number):
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
            restaurant = Restaurant.objects.get(slug=restaurant_slug, hotel=hotel)
            room = Room.objects.get(hotel=hotel, room_number=room_number)
        except (Hotel.DoesNotExist, Restaurant.DoesNotExist, Room.DoesNotExist) as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        try:
            dinner_sub = BookingSubcategory.objects.get(name__iexact="dinner", hotel=hotel)
            dinner_cat = BookingCategory.objects.get(subcategory=dinner_sub, hotel=hotel)
        except (BookingSubcategory.DoesNotExist, BookingCategory.DoesNotExist):
            return Response(
                {"detail": "Dinner booking category or subcategory is not configured for this hotel."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data.copy()
        data.update({
            "hotel": hotel.id,
            "restaurant": restaurant.id,
            "category": dinner_cat.id,
            "room": room.id,
        })

        # ✅ Inject guest ID if one exists on the room
        guest = room.guests.first()
        if guest:
            data["guest"] = guest.id

        serializer = BookingCreateSerializer(data=data)
        if serializer.is_valid():
            booking = serializer.save()
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

