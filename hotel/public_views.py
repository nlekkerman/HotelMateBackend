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
        
        # Get precheckin configuration (use snapshot if available, fallback to hotel config)
        from .models import HotelPrecheckinConfig
        from .precheckin.field_registry import PRECHECKIN_FIELD_REGISTRY
        
        # Use token snapshot if present, otherwise current hotel config  
        if token.config_snapshot_enabled or token.config_snapshot_required:
            precheckin_config = {
                'enabled': token.config_snapshot_enabled,
                'required': token.config_snapshot_required
            }
        else:
            # Fallback for old tokens - use current hotel config
            hotel_config = HotelPrecheckinConfig.get_or_create_default(booking.hotel)
            precheckin_config = {
                'enabled': hotel_config.fields_enabled,
                'required': hotel_config.fields_required
            }
        
        # Build registry subset for enabled fields only
        enabled_registry = {}
        for field_key in precheckin_config['enabled'].keys():
            if precheckin_config['enabled'].get(field_key) and field_key in PRECHECKIN_FIELD_REGISTRY:
                enabled_registry[field_key] = PRECHECKIN_FIELD_REGISTRY[field_key]

        return Response({
            'booking': {
                'id': booking.booking_id,
                'check_in': str(booking.check_in),
                'check_out': str(booking.check_out),
                'room_type_name': booking.room_type.name,
                'hotel_name': booking.hotel.name,
                'nights': booking.nights,
                'expected_guests': booking.adults + booking.children,
                'special_requests': booking.special_requests or ''
            },
            'party': {
                'primary': next((BookingGuestSerializer(member).data for member in party_list if member.role == 'PRIMARY'), None),
                'companions': [BookingGuestSerializer(member).data for member in party_list if member.role == 'COMPANION'],
                'total_count': len(party_list)
            },
            'party_complete': booking.party_complete,
            'party_missing_count': booking.party_missing_count,
            'precheckin_config': precheckin_config,
            'precheckin_field_registry': enabled_registry
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
        
        # Extract all possible precheckin fields from request
        precheckin_fields_data = {}
        from .precheckin.field_registry import PRECHECKIN_FIELD_REGISTRY
        for field_key in PRECHECKIN_FIELD_REGISTRY.keys():
            if field_key in request.data:
                precheckin_fields_data[field_key] = request.data[field_key]
        
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
        
        # Get precheckin configuration for validation
        from .models import HotelPrecheckinConfig
        
        # Use token snapshot if present, otherwise current hotel config
        if token.config_snapshot_enabled or token.config_snapshot_required:
            config_enabled = token.config_snapshot_enabled
            config_required = token.config_snapshot_required
        else:
            # Fallback for old tokens - use current hotel config
            hotel_config = HotelPrecheckinConfig.get_or_create_default(booking.hotel)
            config_enabled = hotel_config.fields_enabled
            config_required = hotel_config.fields_required
        
        # Validate precheckin config fields
        for field_key, is_required in config_required.items():
            if is_required and field_key not in precheckin_fields_data:
                return Response(
                    {'code': 'VALIDATION_ERROR', 'message': f'Field {field_key} is required'},
                    status=400
                )
        
        # Reject unknown field keys
        for field_key in precheckin_fields_data.keys():
            if field_key not in PRECHECKIN_FIELD_REGISTRY:
                return Response(
                    {'code': 'VALIDATION_ERROR', 'message': f'Unknown field: {field_key}'},
                    status=400
                )
            # Only store enabled fields
            if not config_enabled.get(field_key, False):
                return Response(
                    {'code': 'VALIDATION_ERROR', 'message': f'Field {field_key} is not enabled for this hotel'},
                    status=400
                )
        
        # ✅ NEW CANONICAL RULE: Companions-only party validation
        # Party data can be empty (no companions) - PRIMARY is always preserved
        
        # Reject PRIMARY in party payload  
        primary_count = sum(1 for member in party_data if member.get('role') == 'PRIMARY')
        if primary_count > 0:
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': 'Do not include PRIMARY in party; primary guest is inferred from primary_* fields.'},
                status=400
            )
        
        # Validate party size against booking (optional but recommended)
        if booking.adults is not None and booking.children is not None:
            expected_total = booking.adults + booking.children
            actual_total = 1 + len(party_data)  # 1 PRIMARY + companions
            
            if actual_total != expected_total:
                return Response(
                    {'code': 'PARTY_SIZE_MISMATCH', 'message': f'Party size mismatch. Expected {expected_total}, got {actual_total}.'},
                    status=400
                )
        
        # Validate companion data structure
        for member in party_data:
            first_name = member.get('first_name', '').strip()
            last_name = member.get('last_name', '').strip()
            
            if not first_name or not last_name:
                return Response(
                    {'code': 'VALIDATION_ERROR', 'message': 'All party members must have first_name and last_name'},
                    status=400
                )
        
        # Process submission atomically
        try:
            with transaction.atomic():
                # ✅ PRESERVE PRIMARY: Delete only COMPANION BookingGuests
                BookingGuest.objects.filter(
                    booking=booking, 
                    role='COMPANION'
                ).delete()
                
                # Create new COMPANION party members (PRIMARY stays untouched)
                for member_data in party_data:
                    BookingGuest.objects.create(
                        booking=booking,
                        role='COMPANION',  # Force all party payload items to COMPANION
                        first_name=member_data['first_name'],
                        last_name=member_data['last_name'],
                        email=member_data.get('email', ''),
                        phone=member_data.get('phone', ''),
                        is_staying=True  # All party members are staying
                    )
                
                # Separate booking-scoped vs guest-scoped fields
                booking_payload = {}
                guest_scoped_data = {}
                
                for field_key, value in precheckin_fields_data.items():
                    if not config_enabled.get(field_key, False):
                        continue
                        
                    field_config = PRECHECKIN_FIELD_REGISTRY.get(field_key, {})
                    field_scope = field_config.get('scope', 'booking')
                    
                    if field_scope == 'booking':
                        booking_payload[field_key] = value
                    elif field_scope == 'guest':
                        guest_scoped_data[field_key] = value
                
                # Update booking with booking-scoped precheckin data only
                booking.precheckin_payload = booking_payload
                booking.precheckin_submitted_at = timezone.now()
                
                # Handle special_requests if provided (backward compatibility)
                if 'special_requests' in precheckin_fields_data:
                    booking.special_requests = precheckin_fields_data['special_requests']
                
                # Store guest-scoped data (nationality, country_of_residence, etc.) on PRIMARY guest
                if guest_scoped_data:
                    # For now, apply guest-scoped data to PRIMARY guest only
                    # TODO: Frontend needs to send per-guest data structure
                    primary_guest = BookingGuest.objects.filter(booking=booking, role='PRIMARY').first()
                    if primary_guest:
                        primary_guest.precheckin_payload = guest_scoped_data
                        primary_guest.save()
                
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
