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
    
    def get(self, request, hotel_slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
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


class ValidatePrecheckinTokenView(APIView):
    """Validate pre-check-in token and return booking summary"""
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug):
        """Validate token and return booking information for pre-check-in form"""
        import hashlib
        from django.utils import timezone
        from .models import BookingPrecheckinToken, RoomBooking
        from .booking_serializers import BookingGuestSerializer
        
        raw_token = request.query_params.get('token')
        if not raw_token:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=404
            )
        
        # Hash the provided token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            # Find token with constant-time lookup
            token = BookingPrecheckinToken.objects.select_related(
                'booking', 'booking__hotel', 'booking__room_type'
            ).get(
                token_hash=token_hash,
                booking__hotel__slug=hotel_slug
            )
        except BookingPrecheckinToken.DoesNotExist:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=404
            )
        
        # Validate token status (unified 404 response for all invalid states)
        if not token.is_valid:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=404
            )
        
        booking = token.booking
        
        # Get current party information
        party_list = booking.party.all().order_by('role', 'first_name')
        party_data = []
        for member in party_list:
            party_data.append(BookingGuestSerializer(member).data)
        
        return Response({
            'booking_summary': {
                'booking_id': booking.booking_id,
                'hotel_name': booking.hotel.name,
                'dates': f"{booking.check_in} to {booking.check_out}",
                'nights': booking.nights,
                'adults': booking.adults,
                'children': booking.children,
                'room_type': booking.room_type.name,
                'special_requests': booking.special_requests or ''
            },
            'party': party_data,
            'party_complete': booking.party_complete,
            'party_missing_count': booking.party_missing_count
        })


class SubmitPrecheckinDataView(APIView):
    """Submit party information and complete pre-check-in"""
    permission_classes = [AllowAny]

    def post(self, request, hotel_slug):
        """Process party submission and mark token as used"""
        import hashlib
        from django.utils import timezone
        from django.db import transaction
        from .models import BookingPrecheckinToken, BookingGuest
        from .booking_serializers import BookingGuestSerializer
        
        raw_token = request.data.get('token')
        party_data = request.data.get('party', [])
        eta = request.data.get('eta')
        special_requests = request.data.get('special_requests')
        accept_terms = request.data.get('accept_terms')
        
        if not raw_token:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=404
            )
        
        # Hash the provided token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            # Find token with constant-time lookup
            token = BookingPrecheckinToken.objects.select_related(
                'booking', 'booking__hotel'
            ).get(
                token_hash=token_hash,
                booking__hotel__slug=hotel_slug
            )
        except BookingPrecheckinToken.DoesNotExist:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=404
            )
        
        # Validate token status
        if not token.is_valid:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=404
            )
        
        booking = token.booking
        
        # Validate party data
        if not party_data:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'Party information is required'},
                status=400
            )
        
        # Count staying guests and validate against booking
        staying_count = sum(1 for member in party_data if member.get('is_staying', True))
        expected_count = booking.adults + booking.children
        
        if staying_count != expected_count:
            return Response(
                {'code': 'PARTY_INCOMPLETE', 'message': f'Expected {expected_count} staying guests, got {staying_count}'},
                status=400
            )
        
        # Validate exactly one PRIMARY guest
        primary_count = sum(1 for member in party_data if member.get('role') == 'PRIMARY')
        if primary_count != 1:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'Exactly one PRIMARY guest is required'},
                status=400
            )
        
        # Process submission atomically
        try:
            with transaction.atomic():
                # Replace existing party members for this booking
                BookingGuest.objects.filter(booking=booking).delete()
                
                # Create new party members
                for member_data in party_data:
                    BookingGuest.objects.create(
                        booking=booking,
                        role=member_data.get('role', 'COMPANION'),
                        first_name=member_data['first_name'],
                        last_name=member_data['last_name'],
                        email=member_data.get('email', ''),
                        phone=member_data.get('phone', ''),
                        is_staying=member_data.get('is_staying', True)
                    )
                
                # Update booking with optional fields
                if special_requests is not None:
                    booking.special_requests = special_requests
                booking.save()
                
                # Mark token as used
                token.used_at = timezone.now()
                token.save()
                
        except Exception as e:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'Failed to save party information'},
                status=400
            )
        
        # Return updated party information
        updated_party = booking.party.all().order_by('role', 'first_name')
        party_serializer_data = []
        for member in updated_party:
            party_serializer_data.append(BookingGuestSerializer(member).data)
        
        return Response({
            'success': True,
            'party': party_serializer_data,
            'party_complete': booking.party_complete
        })
