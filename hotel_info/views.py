# src/apps/hotel_info/views.py

from rest_framework import viewsets
from .models import HotelInfo, HotelInfoCategory, CategoryQRCode
from .serializers import (HotelInfoSerializer,
                          HotelInfoCategorySerializer,
                          HotelInfoCreateSerializer,
                          HotelInfoUpdateSerializer)
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from staff.permissions import (
    CanViewHotelInfoModule,
    CanReadHotelInfo,
    CanCreateHotelInfo,
    CanUpdateHotelInfo,
    CanDeleteHotelInfo,
    CanReadHotelInfoCategory,
    CanManageHotelInfoCategory,
    CanReadHotelInfoQR,
    CanGenerateHotelInfoQR,
)
from staff_chat.permissions import IsStaffMember, IsSameHotel


def _staff_hotel_or_none(request):
    """Return the request user's staff hotel, or None."""
    staff = getattr(request.user, 'staff_profile', None)
    return staff.hotel if staff and staff.hotel else None


@api_view(["GET"])
@permission_classes([
    IsAuthenticated,
    IsStaffMember,
    CanViewHotelInfoModule,
    CanReadHotelInfoQR,
])
def download_all_qrs(request):
    """List QR records for the requesting staff member's own hotel only.

    Any ``hotel_slug`` query parameter is ignored — staff must never read
    another hotel's QR records via this endpoint.
    """
    hotel = _staff_hotel_or_none(request)
    if not hotel:
        return Response(
            {"detail": "Only hotel staff can list QR codes."},
            status=status.HTTP_403_FORBIDDEN,
        )

    qrs = (
        CategoryQRCode.objects
        .filter(hotel=hotel)
        .select_related("category")
    )
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
    """Staff-zone hotel-info endpoint.

    Every method requires an authenticated same-hotel staff member.
    Anonymous reads are NOT allowed here — public consumers must use
    ``/api/public/hotel/<slug>/hotel-info/`` instead.
    """

    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category__slug"]

    def get_permissions(self):
        base = [
            IsAuthenticated(),
            IsStaffMember(),
            IsSameHotel(),
            CanViewHotelInfoModule(),
            CanReadHotelInfo(),
        ]
        method = self.request.method
        if method == 'POST':
            base.append(CanCreateHotelInfo())
        elif method in ('PUT', 'PATCH'):
            base.append(CanUpdateHotelInfo())
        elif method == 'DELETE':
            base.append(CanDeleteHotelInfo())
        return base

    def get_serializer_class(self):
        if self.action == 'create':
            return HotelInfoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return HotelInfoUpdateSerializer
        return HotelInfoSerializer

    def get_queryset(self):
        # Always scope to the URL hotel; never start from
        # HotelInfo.objects.all().
        hotel_slug = self.kwargs.get('hotel_slug')
        if hotel_slug:
            return HotelInfo.objects.filter(hotel__slug=hotel_slug)
        # No URL slug → fall back to the staff member's own hotel.
        hotel = _staff_hotel_or_none(self.request)
        if hotel:
            return HotelInfo.objects.filter(hotel=hotel)
        return HotelInfo.objects.none()

    def create(self, request, *args, **kwargs):
        # Server forces hotel_slug from URL; never trust the request body.
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug:
            staff_hotel = _staff_hotel_or_none(request)
            hotel_slug = staff_hotel.slug if staff_hotel else None
        if not hotel_slug:
            return Response(
                {"detail": "hotel_slug could not be resolved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reject body attempts to target a different hotel.
        body_slug = request.data.get('hotel_slug')
        if (
            body_slug
            and body_slug != hotel_slug
            and not getattr(request.user, 'is_superuser', False)
        ):
            return Response(
                {"detail": "hotel_slug in body does not match URL hotel."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['hotel_slug'] = hotel_slug
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HotelInfoCategoryViewSet(viewsets.ModelViewSet):
    """Global HotelInfoCategory rows.

    HotelInfoCategory has no hotel FK, so IsSameHotel does not apply.
    Reads require CanReadHotelInfoCategory. Mutations require
    CanManageHotelInfoCategory which the canonical preset maps grant only
    to Django superusers — normal hotel staff cannot mutate global
    category rows.
    """
    queryset = HotelInfoCategory.objects.all()
    serializer_class = HotelInfoCategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["infos__hotel__slug"]

    def get_permissions(self):
        base = [
            IsAuthenticated(),
            IsStaffMember(),
            CanViewHotelInfoModule(),
            CanReadHotelInfoCategory(),
        ]
        if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
            base.append(CanManageHotelInfoCategory())
        return base

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        category = HotelInfoCategory.objects.get(slug=response.data["slug"])

        # Scope QR generation to the authenticated staff member's hotel.
        staff = getattr(request.user, 'staff_profile', None)
        if staff and staff.hotel:
            qr, _ = CategoryQRCode.objects.get_or_create(
                hotel=staff.hotel, category=category,
            )
            qr.generate_qr()

        return response

    def get_queryset(self):
        qs = super().get_queryset()
        # When filtering by hotel slug, restrict to the staff member's
        # own hotel — staff cannot probe another hotel's category set.
        hotel_slug = self.request.query_params.get("infos__hotel__slug")
        if hotel_slug:
            staff_hotel = _staff_hotel_or_none(self.request)
            if (
                not getattr(self.request.user, 'is_superuser', False)
                and (not staff_hotel or staff_hotel.slug != hotel_slug)
            ):
                return qs.none()
            qs = qs.filter(infos__hotel__slug=hotel_slug).distinct()
        return qs

    @action(detail=False, url_path=r'(?P<hotel_slug>[^/.]+)/categories')
    def by_hotel(self, request, hotel_slug=None):
        # Force-scope to staff hotel.
        staff_hotel = _staff_hotel_or_none(request)
        if (
            not getattr(request.user, 'is_superuser', False)
            and (not staff_hotel or staff_hotel.slug != hotel_slug)
        ):
            return Response([], status=status.HTTP_200_OK)
        qs = (
            HotelInfoCategory.objects
            .filter(infos__hotel__slug=hotel_slug)
            .distinct()
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class HotelInfoCreateView(generics.CreateAPIView):
    serializer_class = HotelInfoCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsStaffMember,
        IsSameHotel,
        CanViewHotelInfoModule,
        CanCreateHotelInfo,
    ]

    def create(self, request, *args, **kwargs):
        # Resolve hotel_slug server-side from URL (preferred) or staff hotel.
        hotel_slug = self.kwargs.get('hotel_slug')
        if not hotel_slug:
            staff_hotel = _staff_hotel_or_none(request)
            hotel_slug = staff_hotel.slug if staff_hotel else None
        if not hotel_slug:
            return Response(
                {"detail": "hotel_slug could not be resolved from URL or staff profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reject body attempts to target a different hotel.
        body_slug = request.data.get('hotel_slug')
        if (
            body_slug
            and body_slug != hotel_slug
            and not getattr(request.user, 'is_superuser', False)
        ):
            return Response(
                {"detail": "hotel_slug in body does not match URL hotel."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data['hotel_slug'] = hotel_slug

        # 1) Run the normal creation
        create_serializer = self.get_serializer(data=data)
        create_serializer.is_valid(raise_exception=True)
        info = create_serializer.save()

        # 2) Ensure a CategoryQRCode for this hotel/category
        qr_obj, _ = CategoryQRCode.objects.get_or_create(
            hotel=info.hotel,
            category=info.category,
        )
        # 3) Generate (or re-generate) the actual QR
        qr_obj.generate_qr()

        # 4) Serialize full response (including any fields + qr_url)
        out = HotelInfoSerializer(info, context=self.get_serializer_context()).data
        out["qr_url"] = qr_obj.qr_url

        return Response(out, status=status.HTTP_201_CREATED)


class CategoryQRView(APIView):
    """Staff-only QR read / regenerate endpoint scoped to the staff hotel."""

    def get_permissions(self):
        base = [
            IsAuthenticated(),
            IsStaffMember(),
            IsSameHotel(),
            CanViewHotelInfoModule(),
        ]
        if self.request.method == 'POST':
            base.append(CanGenerateHotelInfoQR())
        else:
            base.append(CanReadHotelInfoQR())
        return base

    def get(self, request, *args, **kwargs):
        category_slug = request.query_params.get("category_slug")
        if not category_slug:
            return Response(
                {"detail": "category_slug is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Always use the requesting staff's hotel; ignore any query/body slug.
        hotel = _staff_hotel_or_none(request)
        if not hotel:
            return Response(
                {"detail": "Only hotel staff can read QR codes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        qr = get_object_or_404(
            CategoryQRCode,
            hotel=hotel,
            category__slug=category_slug,
        )
        if qr.qr_url:
            return Response({"qr_url": qr.qr_url})
        return Response({"detail": "QR code URL is missing"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        category_slug = request.data.get("category_slug")
        if not category_slug:
            return Response(
                {"detail": "category_slug is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hotel = _staff_hotel_or_none(request)
        if not hotel:
            return Response(
                {"detail": "Only hotel staff can generate QR codes"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Reject any body attempt to target a different hotel.
        body_slug = request.data.get("hotel_slug")
        if (
            body_slug
            and body_slug != hotel.slug
            and not getattr(request.user, 'is_superuser', False)
        ):
            return Response(
                {"detail": "hotel_slug in body does not match staff hotel."},
                status=status.HTTP_403_FORBIDDEN,
            )

        category = get_object_or_404(HotelInfoCategory, slug=category_slug)

        # Create or fetch the QR record
        qr_obj, _created = CategoryQRCode.objects.get_or_create(
            hotel=hotel,
            category=category,
        )
        # Always regenerate the QR
        qr_obj.generate_qr()

        return Response({"qr_url": qr_obj.qr_url}, status=status.HTTP_200_OK)
