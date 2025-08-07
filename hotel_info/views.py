# src/apps/hotel_info/views.py

from rest_framework import viewsets
from .models import HotelInfo, HotelInfoCategory, CategoryQRCode, GoodToKnowEntry
from .serializers import (HotelInfoSerializer,
                          HotelInfoCategorySerializer,
                          HotelInfoCreateSerializer,
                          HotelInfoUpdateSerializer,
                          GoodToKnowEntrySerializer)
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from hotel.models import Hotel
from django_filters.rest_framework import DjangoFilterBackend

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_all_qrs(request):
    hotel_slug = request.query_params.get("hotel_slug")
    if not hotel_slug:
        return Response({"detail": "hotel_slug is required"}, status=status.HTTP_400_BAD_REQUEST)

    qrs = CategoryQRCode.objects.filter(hotel__slug=hotel_slug).select_related("category")
    data = [
        {
            "category": qr.category.name,
            "category_slug": qr.category.slug,
            "qr_url": qr.qr_url,
        }
        for qr in qrs if qr.qr_url
    ]
    return Response(data)


class HotelInfoViewSet(viewsets.ModelViewSet):
    queryset = HotelInfo.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'create':
            return HotelInfoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return HotelInfoUpdateSerializer
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
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    # this lets you do ?infos__hotel__slug=<slug> to only get categories
    filterset_fields = ["infos__hotel__slug"]
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        category = HotelInfoCategory.objects.get(slug=response.data["slug"])  
        hotel_slug = request.data.get("hotel_slug")

        if hotel_slug:
            from hotel.models import Hotel
            hotel = get_object_or_404(Hotel, slug=hotel_slug)
            qr, _ = CategoryQRCode.objects.get_or_create(hotel=hotel, category=category)
            qr.generate_qr()

        return response
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

    def create(self, request, *args, **kwargs):
        # 1) Run the normal creation
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        info = create_serializer.save()  # <– HotelInfo instance

        # 2) Ensure a CategoryQRCode for this hotel/category
        qr_obj, _ = CategoryQRCode.objects.get_or_create(
            hotel=info.hotel,
            category=info.category
        )
        # 3) Generate (or re‐generate) the actual QR
        qr_obj.generate_qr()

        # 4) Serialize full response (including any fields + qr_url)
        #    if you want to include qr_url directly here:
        out = HotelInfoSerializer(info, context=self.get_serializer_context()).data
        out["qr_url"] = qr_obj.qr_url

        return Response(out, status=status.HTTP_201_CREATED)
    
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

        qr = get_object_or_404(
            CategoryQRCode,
            hotel__slug=hotel_slug,
            category__slug=category_slug,
        )
        if qr.qr_url:
            return Response({"qr_url": qr.qr_url})
        return Response({"detail": "QR code URL is missing"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        hotel_slug = request.data.get("hotel_slug")
        category_slug = request.data.get("category_slug")
        if not hotel_slug or not category_slug:
            return Response(
                {"detail": "hotel_slug and category_slug are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch the Hotel and Category; 404 if not found
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        category = get_object_or_404(HotelInfoCategory, slug=category_slug)

        # Create or fetch the QR record
        qr_obj, created = CategoryQRCode.objects.get_or_create(
            hotel=hotel,
            category=category,
        )
        # Always regenerate the QR
        qr_obj.generate_qr()

        return Response({"qr_url": qr_obj.qr_url}, status=status.HTTP_200_OK)

class GoodToKnowEntryViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"            # For URL kwarg 'slug'
    lookup_url_kwarg = "slug"
    serializer_class = GoodToKnowEntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = GoodToKnowEntry.objects.all()
        hotel_slug = self.kwargs.get("hotel_slug")
        if hotel_slug:
            queryset = queryset.filter(hotel__slug=hotel_slug)
        return queryset

    def get_object(self):
        # Override to fetch object by both hotel_slug and slug
        queryset = self.filter_queryset(self.get_queryset())
        hotel_slug = self.kwargs.get("hotel_slug")
        slug = self.kwargs.get("slug")

        obj = get_object_or_404(queryset, hotel__slug=hotel_slug, slug=slug)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        hotel_slug = self.kwargs.get("hotel_slug")
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        serializer.save(hotel=hotel)
