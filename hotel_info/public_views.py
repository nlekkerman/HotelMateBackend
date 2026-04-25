"""
Public (no-auth) read-only hotel-info endpoints.

Mounted under /api/public/hotel/<hotel_slug>/hotel-info/...
The QR codes printed in rooms point at frontend pages that call these
endpoints. They MUST stay GET-only and hotel-scoped by URL slug.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CategoryQRCode, HotelInfo, HotelInfoCategory
from .serializers import HotelInfoCategorySerializer, HotelInfoSerializer


class PublicHotelInfoListView(generics.ListAPIView):
    """List active hotel-info entries for a hotel, optionally narrowed by category."""

    serializer_class = HotelInfoSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = HotelInfo.objects.filter(
            active=True,
            hotel__slug=self.kwargs['hotel_slug'],
        )
        category_slug = (
            self.kwargs.get('category_slug')
            or self.request.query_params.get('category_slug')
        )
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs


class PublicHotelInfoCategoryListView(generics.ListAPIView):
    """List categories that have at least one active info entry for the hotel."""

    serializer_class = HotelInfoCategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            HotelInfoCategory.objects
            .filter(infos__hotel__slug=self.kwargs['hotel_slug'])
            .distinct()
        )


class PublicCategoryQRView(APIView):
    """Read-only QR URL lookup for a hotel + category."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, hotel_slug, category_slug):
        qr = get_object_or_404(
            CategoryQRCode,
            hotel__slug=hotel_slug,
            category__slug=category_slug,
        )
        if not qr.qr_url:
            return Response({"detail": "QR code URL is missing"}, status=404)
        return Response({"qr_url": qr.qr_url})
