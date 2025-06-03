from rest_framework import viewsets
from .models import Booking, BookingCategory
from .serializers import BookingSerializer, BookingCategorySerializer


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('hotel', 'category').all()
    serializer_class = BookingSerializer


class BookingCategoryViewSet(viewsets.ModelViewSet):
    queryset = BookingCategory.objects.prefetch_related('subcategories').all()
    serializer_class = BookingCategorySerializer
