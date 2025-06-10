# src/apps/hotel_info/views.py

from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import HotelInfo, HotelInfoCategory, CategoryQRCode
from .serializers import HotelInfoSerializer, HotelInfoCategorySerializer, HotelInfoCreateSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class HotelInfoViewSet(viewsets.ModelViewSet):
    queryset = HotelInfo.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return HotelInfoCreateSerializer
        return HotelInfoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hotel__slug", "category__slug"]

class HotelInfoCategoryViewSet(viewsets.ModelViewSet):
    """
    Returns all categories, or filter to only those with infos for a given hotel:
      GET /api/hotel_info/categories/?infos__hotel__slug=hotel-killarney
    """
    queryset = HotelInfoCategory.objects.all()
    serializer_class = HotelInfoCategorySerializer
    filter_backends = [DjangoFilterBackend]
    # this lets you do ?infos__hotel__slug=<slug> to only get categories
    filterset_fields = ["infos__hotel__slug"]
    def get_queryset(self):
        qs = super().get_queryset()
        hotel_slug = self.request.query_params.get("infos__hotel__slug")
        if hotel_slug:
            qs = qs.filter(infos__hotel__slug=hotel_slug).distinct()
        return qs
    @action(detail=False, url_path=r'(?P<hotel_slug>[^/.]+)/categories')
    def by_hotel(self, request, hotel_slug=None):
        qs = self.get_queryset().filter(infos__hotel__slug=hotel_slug).distinct()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

class HotelInfoCreateView(generics.CreateAPIView):
    serializer_class = HotelInfoCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

class CategoryQRView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hotel_slug = request.query_params.get("hotel_slug")
        category_slug = request.query_params.get("category_slug")

        if not hotel_slug or not category_slug:
            return Response(
                {"detail": "hotel_slug and category_slug are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the category
            category = HotelInfoCategory.objects.get(slug=category_slug)
        except HotelInfoCategory.DoesNotExist:
            return Response({"detail": "Category not found"}, status=404)

        try:
            # Find the QR code for the hotel + category
            qr = CategoryQRCode.objects.get(hotel__slug=hotel_slug, category=category)
        except CategoryQRCode.DoesNotExist:
            return Response({"detail": "QR code not found"}, status=404)

        if qr.qr_url:
            return Response({"qr_url": qr.qr_url})
        else:
            return Response({"detail": "QR code URL is missing"}, status=404)