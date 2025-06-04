from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Booking, BookingCategory
from .serializers import BookingSerializer, BookingCategorySerializer, BookingCreateSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Restaurant, BookingSubcategory
from hotel.models import Hotel
from rooms.models import Room
from .serializers import BookingCreateSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('hotel', 'category').all()
    serializer_class = BookingSerializer


class BookingCategoryViewSet(viewsets.ModelViewSet):
    queryset = BookingCategory.objects.prefetch_related('subcategories').all()
    serializer_class = BookingCategorySerializer


class GuestDinnerBookingView(APIView):
    """
    Public view for guests to make a dinner booking using a QR code URL.
    """
    def post(self, request, hotel_slug, restaurant_slug, room_number):
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
            restaurant = Restaurant.objects.get(slug=restaurant_slug, hotel=hotel)
            room = Room.objects.get(hotel=hotel, room_number=room_number)
        except (Hotel.DoesNotExist, Restaurant.DoesNotExist, Room.DoesNotExist):
            return Response({"detail": "Invalid hotel, restaurant, or room."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure there's a dinner subcategory
        try:
            subcategory = BookingSubcategory.objects.get(name__iexact="dinner", hotel=hotel)
            category = BookingCategory.objects.get(subcategory=subcategory, hotel=hotel)
        except (BookingSubcategory.DoesNotExist, BookingCategory.DoesNotExist):
            return Response({"detail": "Dinner category is not configured."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data.update({
            "hotel": hotel.id,
            "category": category.id,
            "restaurant": restaurant.id,
        })

        serializer = BookingCreateSerializer(data=data)
        if serializer.is_valid():
            booking = serializer.save()
            return Response(BookingCreateSerializer(booking).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    queryset = Booking.objects.all()
    serializer_class = BookingCreateSerializer
    permission_classes = [AllowAny]