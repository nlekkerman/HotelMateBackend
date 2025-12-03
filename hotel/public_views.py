"""
Public-facing hotel views for guest/public access.
No authentication required.
"""
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import models

from .models import Hotel, Preset
from .serializers import (
    HotelPublicSerializer,
    PublicSectionDetailSerializer,
    PresetSerializer
)


class HotelPublicListView(generics.ListAPIView):
    """
    Public API endpoint for hotel discovery.
    Returns active hotels with branding and portal configuration.
    
    Query params:
    - q: text search in name, city, country, descriptions, tagline
    - city: filter by city (exact match)
    - country: filter by country (exact match)
    - tags: comma-separated list of tags
    - hotel_type: filter by hotel type (e.g., FamilyHotel, Resort)
    - sort: 'name_asc' or default 'featured'
    """
    serializer_class = HotelPublicSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Filter and sort active hotels based on query params"""
        queryset = Hotel.objects.filter(
            is_active=True
        ).select_related('access_config')
        
        # Text search (q parameter)
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                models.Q(name__icontains=q) |
                models.Q(city__icontains=q) |
                models.Q(country__icontains=q) |
                models.Q(short_description__icontains=q) |
                models.Q(long_description__icontains=q) |
                models.Q(tagline__icontains=q)
            )
        
        # City filter
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        # Country filter
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country__iexact=country)
        
        # Tags filter (comma-separated)
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            # Filter hotels that have any of the specified tags
            for tag in tag_list:
                queryset = queryset.filter(tags__contains=[tag])
        
        # Hotel type filter
        hotel_type = self.request.query_params.get('hotel_type')
        if hotel_type:
            queryset = queryset.filter(hotel_type=hotel_type)
        
        # Sorting
        sort = self.request.query_params.get('sort', 'featured')
        if sort == 'name_asc':
            queryset = queryset.order_by('name')
        else:
            # Default: featured (sort_order, then name)
            queryset = queryset.order_by('sort_order', 'name')
        
        return queryset


class HotelFilterOptionsView(APIView):
    """
    Public API endpoint to get available filter options.
    Returns distinct cities, countries, and all tags from active hotels.
    
    GET /api/public/hotels/filters/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get distinct cities from active hotels
        cities = Hotel.objects.filter(
            is_active=True,
            city__isnull=False
        ).exclude(
            city=''
        ).values_list('city', flat=True).distinct().order_by('city')
        
        # Get distinct countries from active hotels
        countries = Hotel.objects.filter(
            is_active=True,
            country__isnull=False
        ).exclude(
            country=''
        ).values_list('country', flat=True).distinct().order_by('country')
        
        # Get all unique tags from active hotels
        all_tags = set()
        hotels_with_tags = Hotel.objects.filter(
            is_active=True
        ).exclude(tags=[]).values_list('tags', flat=True)
        
        for tag_list in hotels_with_tags:
            if tag_list:
                all_tags.update(tag_list)
        
        # Get distinct hotel types from active hotels
        hotel_types = Hotel.objects.filter(
            is_active=True,
            hotel_type__isnull=False
        ).exclude(
            hotel_type=''
        ).values_list('hotel_type', flat=True).distinct().order_by('hotel_type')
        
        return Response({
            'cities': list(cities),
            'countries': list(countries),
            'tags': sorted(list(all_tags)),
            'hotel_types': list(hotel_types)
        })


class HotelPublicPageView(APIView):
    """
    Public API endpoint to get hotel page structure with all sections.
    
    GET /api/public/hotel/<slug>/page/
    
    Returns all active sections for the hotel with their specific data
    (HeroSection, GalleryContainer, ListContainer, NewsItem).
    
    No authentication required - public endpoint.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Get or create HotelPublicPage to access preset
        public_page, created = hotel.public_page, False
        try:
            public_page = hotel.public_page
        except:
            public_page = None
        
        # Get all active sections ordered by position
        sections = hotel.public_sections.filter(is_active=True).order_by('position')
        
        # Check if hotel has any sections
        if not sections.exists():
            return Response({
                'hotel': {
                    'id': hotel.id,
                    'name': hotel.name,
                    'slug': hotel.slug,
                    'preset': public_page.global_style_variant if public_page else 1,
                },
                'message': 'Coming Soon',
                'description': "This hotel's public page is under construction.",
                'sections': []
            }, status=status.HTTP_200_OK)
        
        # Use the serializer to get full section data
        sections_data = PublicSectionDetailSerializer(
            sections, 
            many=True,
            context={'request': request}
        ).data
        
        # Build response data
        response_data = {
            'hotel': {
                'id': hotel.id,
                'name': hotel.name,
                'slug': hotel.slug,
                'tagline': hotel.tagline,
                'city': hotel.city,
                'country': hotel.country,
                'address_line_1': hotel.address_line_1,
                'address_line_2': hotel.address_line_2,
                'postal_code': hotel.postal_code,
                'latitude': float(hotel.latitude) if hotel.latitude else None,
                'longitude': float(hotel.longitude) if hotel.longitude else None,
                'phone': hotel.phone,
                'email': hotel.email,
                'website_url': hotel.website_url,
                'booking_url': hotel.booking_url,
                'hero_image': hotel.hero_image.url if hotel.hero_image else None,
                'logo': hotel.logo.url if hotel.logo else None,
                'short_description': hotel.short_description,
                'long_description': hotel.long_description,
                'hotel_type': hotel.hotel_type,
                'tags': hotel.tags,
                'preset': public_page.global_style_variant if public_page else 1,
            },
            'sections': sections_data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class PublicPresetsView(APIView):
    """
    Public endpoint for presets - no authentication required.
    Used by frontend to fetch available style presets.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return all available presets grouped by type"""
        presets = Preset.objects.all()
        serializer = PresetSerializer(presets, many=True)
        
        # Group presets by target_type and section_type for easier frontend use
        grouped = {}
        for preset_data in serializer.data:
            target_type = preset_data.get('target_type', 'unknown')
            section_type = preset_data.get('section_type', 'default')
            
            if target_type not in grouped:
                grouped[target_type] = {}
            
            if target_type == 'section':
                if section_type not in grouped[target_type]:
                    grouped[target_type][section_type] = []
                grouped[target_type][section_type].append(preset_data)
            else:
                if 'items' not in grouped[target_type]:
                    grouped[target_type]['items'] = []
                grouped[target_type]['items'].append(preset_data)
        
        return Response({
            'presets': serializer.data,
            'grouped': grouped
        }, status=status.HTTP_200_OK)
