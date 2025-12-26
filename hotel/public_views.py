"""
Public-facing hotel views for guest/public access.
No authentication required.
"""
import logging
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import models

logger = logging.getLogger(__name__)

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
                'adults': booking.adults,
                'children': booking.children,
                'expected_guests': booking.adults + booking.children,
                'special_requests': booking.special_requests or '',
                'precheckin_submitted_at': booking.precheckin_submitted_at.isoformat() if booking.precheckin_submitted_at else None,
                'precheckin_payload': booking.precheckin_payload or {}
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
        
        # 🐛 DEBUG: Log the full payload to understand the structure
        import json
        print(f"\n🔍 PRECHECKIN PAYLOAD DEBUG:")
        print(f"📦 Full request.data:")
        print(json.dumps(request.data, indent=2, default=str))
        
        raw_token = request.data.get('token')
        party_payload = request.data.get('party', {})
        
        # Handle new party structure: {'primary': {...}, 'companions': [...]}
        primary_data = party_payload.get('primary', {})
        party_data = party_payload.get('companions', [])
        
        print(f"🎯 Parsed party data:")
        print(f"Primary: {json.dumps(primary_data, indent=2)}")
        print(f"Companions: {json.dumps(party_data, indent=2)}")
        print(f"Party payload: {json.dumps(party_payload, indent=2)}")
        print("="*80)
        
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
                
                # Update PRIMARY guest with new data and guest-scoped fields
                primary_guest = BookingGuest.objects.filter(booking=booking, role='PRIMARY').first()
                if primary_guest and primary_data:
                    # Update basic info if provided
                    if 'first_name' in primary_data:
                        primary_guest.first_name = primary_data['first_name']
                    if 'last_name' in primary_data:
                        primary_guest.last_name = primary_data['last_name']
                    if 'email' in primary_data:
                        primary_guest.email = primary_data.get('email', '')
                    if 'phone' in primary_data:
                        primary_guest.phone = primary_data.get('phone', '')
                    
                    # Extract guest-scoped fields for PRIMARY
                    primary_guest_fields = {}
                    print(f"🔍 PRIMARY GUEST FIELD EXTRACTION:")
                    for field_key in PRECHECKIN_FIELD_REGISTRY.keys():
                        field_config = PRECHECKIN_FIELD_REGISTRY[field_key]
                        field_scope = field_config.get('scope')
                        is_guest_scoped = field_scope == 'guest'
                        field_in_data = field_key in primary_data
                        
                        print(f"  {field_key}: scope={field_scope}, guest_scoped={is_guest_scoped}, in_primary_data={field_in_data}")
                        
                        if is_guest_scoped and field_in_data:
                            value = primary_data[field_key]
                            primary_guest_fields[field_key] = value
                            print(f"    ✅ Added {field_key} = {value}")
                    
                    print(f"🎯 PRIMARY precheckin_payload: {primary_guest_fields}")
                    primary_guest.precheckin_payload = primary_guest_fields
                    primary_guest.save()
                
                # Create new COMPANION party members
                for idx, member_data in enumerate(party_data):
                    # Extract guest-scoped fields for companion
                    companion_guest_fields = {}
                    print(f"🔍 COMPANION {idx} FIELD EXTRACTION:")
                    for field_key in PRECHECKIN_FIELD_REGISTRY.keys():
                        field_config = PRECHECKIN_FIELD_REGISTRY[field_key]
                        field_scope = field_config.get('scope')
                        is_guest_scoped = field_scope == 'guest'
                        field_in_data = field_key in member_data
                        
                        print(f"  {field_key}: scope={field_scope}, guest_scoped={is_guest_scoped}, in_companion_data={field_in_data}")
                        
                        if is_guest_scoped and field_in_data:
                            value = member_data[field_key]
                            companion_guest_fields[field_key] = value
                            print(f"    ✅ Added {field_key} = {value}")
                    
                    print(f"🎯 COMPANION {idx} precheckin_payload: {companion_guest_fields}")
                    
                    BookingGuest.objects.create(
                        booking=booking,
                        role='COMPANION',
                        first_name=member_data['first_name'],
                        last_name=member_data['last_name'],
                        email=member_data.get('email', ''),
                        phone=member_data.get('phone', ''),
                        is_staying=True,
                        precheckin_payload=companion_guest_fields
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
                
                # Guest-scoped data is now handled above per individual guest
                # No need for additional processing here
                
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


# ============================================================================
# SURVEY SYSTEM - PUBLIC GUEST ENDPOINTS
# ============================================================================

class ValidateSurveyTokenView(APIView):
    """Validate survey token and return booking information for survey form"""
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug):
        """Validate token and return booking information for survey submission"""
        import hashlib
        from django.utils import timezone
        from .models import BookingSurveyToken, RoomBooking
        
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
            token = BookingSurveyToken.objects.select_related(
                'booking', 'booking__hotel', 'booking__room_type'
            ).get(
                token_hash=token_hash,
                booking__hotel__slug=hotel_slug
            )
        except BookingSurveyToken.DoesNotExist:
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
        
        # Get survey configuration (use snapshot if available, fallback to hotel config)
        from .models import HotelSurveyConfig
        from .survey.field_registry import SURVEY_FIELD_REGISTRY
        
        # Use token snapshot if present, otherwise current hotel config
        if token.config_snapshot_enabled or token.config_snapshot_required:
            survey_config = {
                'enabled': token.config_snapshot_enabled,
                'required': token.config_snapshot_required
            }
        else:
            # Fallback for old tokens - use current hotel config
            hotel_config = HotelSurveyConfig.get_or_create_default(booking.hotel)
            survey_config = {
                'enabled': hotel_config.fields_enabled,
                'required': hotel_config.fields_required
            }
        
        # Build registry subset for enabled fields only
        enabled_registry = {}
        for field_key in survey_config['enabled'].keys():
            if survey_config['enabled'].get(field_key) and field_key in SURVEY_FIELD_REGISTRY:
                enabled_registry[field_key] = SURVEY_FIELD_REGISTRY[field_key]

        # Check if survey already submitted
        survey_already_submitted = hasattr(booking, 'survey_response') and booking.survey_response is not None

        return Response({
            'booking': {
                'id': booking.booking_id,
                'check_in': str(booking.check_in),
                'check_out': str(booking.check_out),
                'room_type_name': booking.room_type.name,
                'hotel_name': booking.hotel.name,
                'nights': booking.nights,
                'adults': booking.adults,
                'children': booking.children,
                'checked_out_at': booking.checked_out_at.isoformat() if booking.checked_out_at else None
            },
            'hotel': {
                'name': booking.hotel.name,
                'slug': booking.hotel.slug
            },
            'survey_config': survey_config,
            'survey_field_registry': enabled_registry,
            'survey_already_submitted': survey_already_submitted,
            'existing_response': booking.survey_response.payload if survey_already_submitted else None
        })


class SubmitSurveyDataView(APIView):
    """Submit survey response and mark token as used"""
    permission_classes = [AllowAny]

    def post(self, request, hotel_slug):
        """Process survey submission and mark token as used"""
        import hashlib
        from django.utils import timezone
        from django.db import transaction
        from .models import BookingSurveyToken, BookingSurveyResponse
        
        raw_token = request.data.get('token')
        survey_payload = request.data.get('survey_data', {})
        
        if not raw_token:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=404
            )
        
        # Hash the provided token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            # Find token with constant-time lookup
            token = BookingSurveyToken.objects.select_related(
                'booking', 'booking__hotel'
            ).get(
                token_hash=token_hash,
                booking__hotel__slug=hotel_slug
            )
        except BookingSurveyToken.DoesNotExist:
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
        
        # Check if survey already submitted
        if hasattr(booking, 'survey_response') and booking.survey_response is not None:
            return Response(
                {'code': 'ALREADY_SUBMITTED', 'message': 'Survey has already been submitted for this booking.'},
                status=400
            )
        
        # Get survey configuration for validation
        from .models import HotelSurveyConfig
        from .survey.field_registry import SURVEY_FIELD_REGISTRY
        
        # Use token snapshot if present, otherwise current hotel config
        if token.config_snapshot_enabled or token.config_snapshot_required:
            config_enabled = token.config_snapshot_enabled
            config_required = token.config_snapshot_required
        else:
            # Fallback for old tokens - use current hotel config
            hotel_config = HotelSurveyConfig.get_or_create_default(booking.hotel)
            config_enabled = hotel_config.fields_enabled
            config_required = hotel_config.fields_required
        
        # Validate required survey fields
        missing_fields = []
        for field_key, is_required in config_required.items():
            if is_required and field_key not in survey_payload:
                field_label = SURVEY_FIELD_REGISTRY.get(field_key, {}).get('label', field_key)
                missing_fields.append(field_label)
        
        if missing_fields:
            # Stronger validation logging
            logger.error(
                f"Survey validation failed for booking {booking.booking_id} at hotel {booking.hotel.slug}: "
                f"Missing required fields: {missing_fields}. Token state: valid={token.is_valid}, "
                f"expired={token.is_expired}, used={token.is_used}"
            )
            return Response(
                {'code': 'VALIDATION_ERROR', 'message': f'Required fields missing: {", ".join(missing_fields)}'},
                status=400
            )
        
        # Reject unknown field keys
        for field_key in survey_payload.keys():
            if field_key not in SURVEY_FIELD_REGISTRY:
                return Response(
                    {'code': 'VALIDATION_ERROR', 'message': f'Unknown field: {field_key}'},
                    status=400
                )
            # Only store enabled fields
            if not config_enabled.get(field_key, False):
                return Response(
                    {'code': 'VALIDATION_ERROR', 'message': f'Field {field_key} is not enabled for this survey'},
                    status=400
                )
        
        # Validate overall_rating if provided
        overall_rating = survey_payload.get('overall_rating')
        if overall_rating is not None:
            if not isinstance(overall_rating, int) or overall_rating < 1 or overall_rating > 5:
                return Response(
                    {'code': 'VALIDATION_ERROR', 'message': 'Overall rating must be between 1 and 5'},
                    status=400
                )
        
        # Filter payload to only include enabled fields
        filtered_payload = {}
        for field_key, value in survey_payload.items():
            if config_enabled.get(field_key, False):
                filtered_payload[field_key] = value
        
        # Process submission atomically
        try:
            with transaction.atomic():
                # Create survey response
                survey_response = BookingSurveyResponse.objects.create(
                    booking=booking,
                    hotel=booking.hotel,
                    payload=filtered_payload,
                    overall_rating=overall_rating,
                    token_used=token
                )
                
                # Mark token as used
                token.used_at = timezone.now()
                token.save()
                
        except Exception as e:
            return Response(
                {'code': 'SUBMISSION_ERROR', 'message': 'Failed to save survey response'},
                status=400
            )
        
        return Response({
            'success': True,
            'message': 'Thank you for your feedback!',
            'submitted_at': survey_response.submitted_at.isoformat(),
            'booking_id': booking.booking_id
        })


class HotelCancellationPolicyView(APIView):
    """
    Get detailed cancellation policy information for a hotel.
    Public endpoint - no authentication required.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, hotel_slug):
        """Return hotel's default cancellation policy details"""
        hotel = get_object_or_404(Hotel, slug=hotel_slug, is_active=True)
        
        if not hotel.default_cancellation_policy:
            return Response({
                'error': 'No default cancellation policy configured for this hotel'
            }, status=status.HTTP_404_NOT_FOUND)
        
        policy = hotel.default_cancellation_policy
        
        # Include tier information for custom policies
        tiers_data = []
        if policy.template_type == 'CUSTOM':
            for tier in policy.tiers.all().order_by('hours_before_checkin'):
                tiers_data.append({
                    'hours_before_checkin': tier.hours_before_checkin,
                    'penalty_type': tier.penalty_type,
                    'penalty_amount': str(tier.penalty_amount) if tier.penalty_amount else None,
                    'penalty_percentage': str(tier.penalty_percentage) if tier.penalty_percentage else None
                })
        
        policy_data = {
            'id': policy.id,
            'code': policy.code,
            'name': policy.name,
            'description': policy.description,
            'template_type': policy.template_type,
            'free_until_hours': policy.free_until_hours,
            'penalty_type': policy.penalty_type,
            'penalty_amount': str(policy.penalty_amount) if policy.penalty_amount else None,
            'penalty_percentage': str(policy.penalty_percentage) if policy.penalty_percentage else None,
            'no_show_penalty_type': policy.no_show_penalty_type,
            'is_active': policy.is_active,
            'tiers': tiers_data if tiers_data else None
        }
        
        return Response({
            'policy': policy_data
        }, status=status.HTTP_200_OK)


class ValidateBookingManagementTokenView(APIView):
    """
    Validate booking management token and return booking information.
    Allows guests to view their booking status and manage their booking.
    """
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug):
        """Validate token and return booking information for management page"""
        import hashlib
        from django.utils import timezone
        from .models import BookingManagementToken, RoomBooking
        from hotel.services.cancellation import CancellationCalculator
        
        raw_token = request.query_params.get('token')
        if not raw_token:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Hash the provided token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            # Find token with constant-time lookup
            token = BookingManagementToken.objects.select_related(
                'booking', 'booking__hotel', 'booking__room_type', 'booking__cancellation_policy'
            ).get(
                token_hash=token_hash,
                booking__hotel__slug=hotel_slug
            )
        except BookingManagementToken.DoesNotExist:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate token status
        if not token.is_valid:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        booking = token.booking
        
        # Record view action
        token.record_action('VIEW')
        
        # Get cancellation policy information
        cancellation_policy_data = None
        if booking.cancellation_policy:
            policy = booking.cancellation_policy
            cancellation_policy_data = {
                'id': policy.id,
                'code': policy.code,
                'name': policy.name,
                'description': policy.description,
                'template_type': policy.template_type,
                'free_until_hours': policy.free_until_hours,
                'penalty_type': policy.penalty_type,
                'no_show_penalty_type': policy.no_show_penalty_type
            }
        
        # Calculate cancellation fees if booking can be cancelled
        cancellation_preview = None
        can_cancel = booking.status in ['CONFIRMED', 'PENDING_PAYMENT', 'PENDING_APPROVAL'] and not booking.cancelled_at
        
        if can_cancel:
            try:
                calculator = CancellationCalculator(booking)
                cancellation_preview = calculator.calculate()
            except Exception:
                # If calculation fails, still allow viewing but disable cancellation
                can_cancel = False
        
        return Response({
            'booking': {
                'id': booking.booking_id,
                'confirmation_number': booking.confirmation_number,
                'status': booking.status,
                'check_in': str(booking.check_in),
                'check_out': str(booking.check_out),
                'room_type_name': booking.room_type.name,
                'hotel_name': booking.hotel.name,
                'nights': booking.nights,
                'adults': booking.adults,
                'children': booking.children,
                'total_amount': str(booking.total_amount),
                'currency': booking.currency,
                'special_requests': booking.special_requests or '',
                'primary_guest_name': booking.primary_guest_name,
                'primary_email': booking.primary_email,
                'created_at': booking.created_at.isoformat(),
                'cancelled_at': booking.cancelled_at.isoformat() if booking.cancelled_at else None,
                'cancellation_reason': booking.cancellation_reason or ''
            },
            'hotel': {
                'name': booking.hotel.name,
                'slug': booking.hotel.slug,
                'phone': booking.hotel.phone,
                'email': booking.hotel.email
            },
            'cancellation_policy': cancellation_policy_data,
            'can_cancel': can_cancel,
            'cancellation_preview': cancellation_preview,
            'token_actions': token.actions_performed
        }, status=status.HTTP_200_OK)


class CancelBookingView(APIView):
    """
    Cancel a booking using a valid management token.
    """
    permission_classes = [AllowAny]

    def post(self, request, hotel_slug):
        """Process booking cancellation with management token using guest cancellation service"""
        import hashlib
        from .models import BookingManagementToken
        from hotel.services.guest_cancellation import (
            cancel_booking_with_token, 
            GuestCancellationError, 
            StripeOperationError
        )
        
        raw_token = request.data.get('token')
        cancellation_reason = request.data.get('reason', 'Guest cancellation via management link')
        
        if not raw_token:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Hash the provided token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            # Find token with constant-time lookup
            token = BookingManagementToken.objects.select_related(
                'booking', 'booking__hotel'
            ).get(
                token_hash=token_hash,
                booking__hotel__slug=hotel_slug
            )
        except BookingManagementToken.DoesNotExist:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate token status
        if not token.is_valid:
            return Response(
                {'message': 'Link invalid or expired.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        booking = token.booking
        
        # Call the shared cancellation service with pre-validated booking and token
        try:
            cancellation_result = cancel_booking_with_token(
                booking=booking,
                token_obj=token,
                reason=cancellation_reason
            )
            
            # Return consistent JSON format (matching BookingStatusView)
            return Response({
                'success': True,
                'message': 'Your booking has been successfully cancelled.',
                'cancellation': {
                    'cancelled_at': cancellation_result['cancelled_at'],
                    'cancellation_fee': str(cancellation_result['fee_amount']),
                    'refund_amount': str(cancellation_result['refund_amount']),
                    'description': cancellation_result['description'],
                    'refund_reference': cancellation_result.get('refund_reference', '')
                }
            }, status=status.HTTP_200_OK)
            
        except GuestCancellationError as e:
            # Business logic errors - safe to expose message
            return Response(
                {'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except StripeOperationError as e:
            # Stripe errors - return safe message (no Stripe details leaked)
            return Response(
                {'message': 'Payment processing failed. Please contact hotel directly.'},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            # Unexpected errors - safe generic message
            return Response(
                {'message': 'Failed to process cancellation.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BookingStatusView(APIView):
    """
    Get booking status by hotel slug + booking ID with REQUIRED token validation.
    Secure URL: GET /api/public/hotels/{hotel_slug}/booking/status/{booking_id}/?token={token}
    """
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug, booking_id):
        """Return booking status and details with mandatory token validation"""
        import hashlib
        from .models import BookingManagementToken, RoomBooking, Hotel
        from hotel.services.cancellation import CancellationCalculator
        
        # Token is REQUIRED - no access without it
        raw_token = request.query_params.get('token')
        if not raw_token:
            return Response(
                {'error': 'Access token is required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Hash the provided token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            # Validate hotel exists
            hotel = Hotel.objects.get(slug=hotel_slug)
            
            # Find booking - must belong to this hotel
            booking = RoomBooking.objects.select_related(
                'hotel', 'room_type', 'cancellation_policy'
            ).get(booking_id=booking_id, hotel=hotel)
            
            # Find token for this specific booking
            token = BookingManagementToken.objects.filter(
                booking=booking,
                token_hash=token_hash
            ).first()
            
            if not token:
                return Response(
                    {'error': 'Invalid or expired access token'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except Hotel.DoesNotExist:
            return Response(
                {'error': 'Hotel not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': 'Booking not found or does not belong to this hotel'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate token status
        if not token.is_valid:
            return Response(
                {'error': 'Token is no longer valid'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Record view action
        token.record_action('VIEW')
        
        # Get cancellation policy information
        cancellation_policy_data = None
        if booking.cancellation_policy:
            policy = booking.cancellation_policy
            cancellation_policy_data = {
                'id': policy.id,
                'code': policy.code,
                'name': policy.name,
                'description': policy.description,
                'template_type': policy.template_type,
                'free_until_hours': policy.free_until_hours,
                'penalty_type': policy.penalty_type,
                'no_show_penalty_type': policy.no_show_penalty_type
            }
        
        # Calculate cancellation fees if booking can be cancelled
        cancellation_preview = None
        can_cancel = booking.status in ['CONFIRMED', 'PENDING_PAYMENT', 'PENDING_APPROVAL'] and not booking.cancelled_at
        
        if can_cancel:
            try:
                calculator = CancellationCalculator(booking)
                cancellation_preview = calculator.calculate()
            except Exception:
                can_cancel = False
        
        return Response({
            'booking': {
                'id': booking.booking_id,
                'confirmation_number': booking.confirmation_number,
                'status': booking.status,
                'check_in': str(booking.check_in),
                'check_out': str(booking.check_out),
                'room_type_name': booking.room_type.name,
                'hotel_name': booking.hotel.name,
                'nights': booking.nights,
                'adults': booking.adults,
                'children': booking.children,
                'total_amount': str(booking.total_amount),
                'currency': booking.currency,
                'special_requests': booking.special_requests or '',
                'primary_guest_name': booking.primary_guest_name,
                'primary_email': booking.primary_email,
                'created_at': booking.created_at.isoformat(),
                'cancelled_at': booking.cancelled_at.isoformat() if booking.cancelled_at else None,
                'cancellation_reason': booking.cancellation_reason or ''
            },
            'hotel': {
                'name': booking.hotel.name,
                'slug': booking.hotel.slug,
                'phone': booking.hotel.phone,
                'email': booking.hotel.email
            },
            'cancellation_policy': cancellation_policy_data,
            'can_cancel': can_cancel,
            'cancellation_preview': cancellation_preview
        }, status=status.HTTP_200_OK)
    
    def post(self, request, hotel_slug, booking_id):
        """Cancel booking with token validation and hotel verification using guest cancellation service"""
        import hashlib
        from .models import BookingManagementToken, Hotel, RoomBooking
        from hotel.services.guest_cancellation import (
            cancel_booking_with_token, 
            GuestCancellationError, 
            StripeOperationError
        )
        
        # Accept token from request.data OR query_params (support both)
        raw_token = request.data.get('token') or request.query_params.get('token')
        cancellation_reason = request.data.get('reason', 'Guest cancellation via management link')
        
        if not raw_token:
            return Response(
                {'error': 'Access token is required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Hash the provided token
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        try:
            # Views retain full responsibility for hotel + booking + token validation
            hotel = Hotel.objects.get(slug=hotel_slug)
            
            # Find booking - must belong to this hotel
            booking = RoomBooking.objects.select_related('hotel').get(
                booking_id=booking_id, hotel=hotel
            )
            
            # Find token for this specific booking
            token = BookingManagementToken.objects.filter(
                booking=booking,
                token_hash=token_hash
            ).first()
            
            if not token:
                return Response(
                    {'error': 'Invalid or expired access token'},
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except Hotel.DoesNotExist:
            return Response(
                {'error': 'Hotel not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': 'Booking not found or does not belong to this hotel'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate token status (views handle token validation BEFORE calling service)
        if not token.is_valid:
            return Response(
                {'error': 'Token is no longer valid'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Call the shared cancellation service with pre-validated booking and token
        try:
            cancellation_result = cancel_booking_with_token(
                booking=booking,
                token_obj=token,
                reason=cancellation_reason
            )
            
            # Return consistent JSON format
            return Response({
                'success': True,
                'message': 'Your booking has been successfully cancelled.',
                'cancellation': {
                    'cancelled_at': cancellation_result['cancelled_at'],
                    'cancellation_fee': str(cancellation_result['fee_amount']),
                    'refund_amount': str(cancellation_result['refund_amount']),
                    'description': cancellation_result['description'],
                    'refund_reference': cancellation_result.get('refund_reference', '')
                }
            }, status=status.HTTP_200_OK)
            
        except GuestCancellationError as e:
            # Business logic errors - safe to expose message
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except StripeOperationError as e:
            # Stripe errors - return 502 with safe message (no Stripe details leaked)
            return Response(
                {'error': 'Payment processing failed. Please contact hotel directly.'},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            # Unexpected errors - safe generic message
            return Response(
                {'error': 'Failed to process cancellation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    