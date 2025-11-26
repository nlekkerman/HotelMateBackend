from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import models
from datetime import datetime

from .models import (
    Hotel,
    RoomBooking,
    PricingQuote,
    PublicSection,
    PublicElement,
    PublicElementItem,
    HeroSection,
    GalleryContainer,
    ListContainer,
    NewsItem,
    ContentBlock,
)
from .serializers import (
    HotelSerializer,
    HotelPublicSerializer,
    RoomBookingListSerializer,
    RoomBookingDetailSerializer,
    PublicSectionStaffSerializer,
    PublicSectionDetailSerializer
)
from .permissions import IsSuperStaffAdminForHotel


class HotelViewSet(viewsets.ModelViewSet):
    """Admin/internal hotel management"""
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = []  # You can add IsAdminUser, etc.


class HotelBySlugView(generics.RetrieveAPIView):
    """Get hotel by slug - internal use"""
    queryset = Hotel.objects.all()
    permission_classes = [AllowAny]
    serializer_class = HotelSerializer
    lookup_field = "slug"

    def get_object(self):
        slug = self.kwargs.get("slug")
        hotel = get_object_or_404(Hotel, slug=slug)
        return hotel


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


class HotelAvailabilityView(APIView):
    """
    Check room availability for specific dates.
    Phase 1 implementation: Returns all room types with basic
    availability info.
    
    Query params:
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults (default 2)
    - children: number of children (default 0)
    """
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Parse query parameters
        check_in_str = request.query_params.get('check_in')
        check_out_str = request.query_params.get('check_out')
        adults = int(request.query_params.get('adults', 2))
        children = int(request.query_params.get('children', 0))
        
        # Validate required parameters
        if not check_in_str or not check_out_str:
            return Response(
                {"detail": "check_in and check_out dates are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate dates
        if check_out <= check_in:
            return Response(
                {"detail": "check_out must be after check_in"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate nights
        nights = (check_out - check_in).days
        
        # Get active room types for this hotel
        room_types = hotel.room_types.filter(
            is_active=True
        ).order_by('sort_order', 'name')
        
        # Build response
        available_rooms = []
        total_guests = adults + children
        
        for room_type in room_types:
            # Check if room can accommodate guests
            can_accommodate = room_type.max_occupancy >= total_guests
            
            # Build room data
            room_data = {
                "room_type_code": room_type.code or room_type.name,
                "room_type_name": room_type.name,
                "is_available": can_accommodate,
                "max_occupancy": room_type.max_occupancy,
                "bed_setup": room_type.bed_setup,
                "short_description": room_type.short_description,
                "photo": room_type.photo.url if room_type.photo else None,
                "starting_price_from": str(room_type.starting_price_from),
                "currency": room_type.currency,
                "availability_message": room_type.availability_message,
                "note": None
            }
            
            # Add note for capacity issues
            if not can_accommodate:
                room_data["note"] = (
                    f"Maximum occupancy is {room_type.max_occupancy} "
                    f"guests"
                )
            
            available_rooms.append(room_data)
        
        response_data = {
            "hotel": hotel.slug,
            "hotel_name": hotel.name,
            "check_in": check_in_str,
            "check_out": check_out_str,
            "nights": nights,
            "adults": adults,
            "children": children,
            "total_guests": total_guests,
            "available_rooms": available_rooms
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class HotelPricingQuoteView(APIView):
    """
    Calculate pricing quote for a specific room type and dates.
    Phase 1 implementation: Basic pricing calculation based on
    room type base price.
    
    POST body:
    - room_type_code: code or name of room type
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults
    - children: number of children
    - promo_code: optional promo code
    """
    permission_classes = [AllowAny]
    
    def post(self, request, slug):
        from decimal import Decimal
        from django.utils import timezone
        
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Parse request data
        room_type_code = request.data.get('room_type_code')
        check_in_str = request.data.get('check_in')
        check_out_str = request.data.get('check_out')
        adults = int(request.data.get('adults', 2))
        children = int(request.data.get('children', 0))
        promo_code = request.data.get('promo_code', '')
        
        # Validate required fields
        if not all([room_type_code, check_in_str, check_out_str]):
            return Response(
                {
                    "detail": "room_type_code, check_in, and check_out "
                    "are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate dates
        if check_out <= check_in:
            return Response(
                {"detail": "check_out must be after check_in"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find room type
        room_type = hotel.room_types.filter(
            is_active=True
        ).filter(
            models.Q(code=room_type_code) | models.Q(name=room_type_code)
        ).first()
        
        if not room_type:
            return Response(
                {"detail": f"Room type '{room_type_code}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate pricing
        nights = (check_out - check_in).days
        base_price = Decimal(str(room_type.starting_price_from))
        subtotal = base_price * nights
        
        # Calculate taxes (9% VAT for Ireland)
        tax_rate = Decimal('0.09')
        taxes = subtotal * tax_rate
        
        # Apply promo code if provided
        discount = Decimal('0')
        applied_promo = None
        
        if promo_code:
            # Simple promo code logic (can be expanded later)
            promo_code_upper = promo_code.upper()
            if promo_code_upper == 'WINTER20':
                discount = subtotal * Decimal('0.20')
                applied_promo = {
                    "code": "WINTER20",
                    "description": "20% off winter bookings",
                    "discount_percentage": "20.00"
                }
            elif promo_code_upper == 'SAVE10':
                discount = subtotal * Decimal('0.10')
                applied_promo = {
                    "code": "SAVE10",
                    "description": "10% off your stay",
                    "discount_percentage": "10.00"
                }
        
        # Calculate total
        fees = Decimal('0')
        total = subtotal + taxes + fees - discount
        
        # Quote valid for 30 minutes
        valid_until = timezone.now() + timezone.timedelta(minutes=30)
        
        # B6: Create PricingQuote record
        quote = PricingQuote.objects.create(
            hotel=hotel,
            room_type=room_type,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            base_price_per_night=base_price,
            number_of_nights=nights,
            subtotal=subtotal,
            taxes=taxes,
            fees=fees,
            discount=discount,
            total=total,
            currency=room_type.currency,
            promo_code=promo_code if promo_code else '',
            valid_until=valid_until
        )
        
        response_data = {
            "quote_id": quote.quote_id,
            "valid_until": valid_until.isoformat(),
            "currency": room_type.currency,
            "room_type": {
                "code": room_type.code or room_type.name,
                "name": room_type.name,
                "photo": room_type.photo.url if room_type.photo else None
            },
            "dates": {
                "check_in": check_in_str,
                "check_out": check_out_str,
                "nights": nights
            },
            "guests": {
                "adults": adults,
                "children": children,
                "total": adults + children
            },
            "breakdown": {
                "base_price_per_night": f"{base_price:.2f}",
                "number_of_nights": nights,
                "subtotal": f"{subtotal:.2f}",
                "taxes": f"{taxes:.2f}",
                "fees": f"{fees:.2f}",
                "discount": f"-{discount:.2f}" if discount > 0 else "0.00",
                "total": f"{total:.2f}"
            },
            "applied_promo": applied_promo
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class HotelBookingCreateView(APIView):
    """
    Create a new room booking.
    Phase 1 implementation: Creates booking record in pending state.
    
    POST body:
    - quote_id: optional quote reference
    - room_type_code: code or name of room type
    - check_in: YYYY-MM-DD
    - check_out: YYYY-MM-DD
    - adults: number of adults
    - children: number of children
    - guest: {first_name, last_name, email, phone}
    - special_requests: optional text
    - promo_code: optional promo code
    """
    permission_classes = [AllowAny]
    
    def post(self, request, slug):
        from decimal import Decimal
        
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Parse request data
        quote_id = request.data.get('quote_id', '')
        room_type_code = request.data.get('room_type_code')
        check_in_str = request.data.get('check_in')
        check_out_str = request.data.get('check_out')
        adults = int(request.data.get('adults', 2))
        children = int(request.data.get('children', 0))
        guest_data = request.data.get('guest', {})
        special_requests = request.data.get('special_requests', '')
        promo_code = request.data.get('promo_code', '')
        
        # Validate required fields
        required_fields = [room_type_code, check_in_str, check_out_str]
        if not all(required_fields):
            return Response(
                {
                    "detail": "room_type_code, check_in, and check_out "
                    "are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate guest data
        required_guest = ['first_name', 'last_name', 'email', 'phone']
        if not all(guest_data.get(field) for field in required_guest):
            return Response(
                {
                    "detail": "Guest first_name, last_name, email, and "
                    "phone are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate dates
        if check_out <= check_in:
            return Response(
                {"detail": "check_out must be after check_in"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find room type
        room_type = hotel.room_types.filter(
            is_active=True
        ).filter(
            models.Q(code=room_type_code) | models.Q(name=room_type_code)
        ).first()
        
        if not room_type:
            return Response(
                {"detail": f"Room type '{room_type_code}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate pricing (reuse pricing logic)
        nights = (check_out - check_in).days
        base_price = Decimal(str(room_type.starting_price_from))
        subtotal = base_price * nights
        tax_rate = Decimal('0.09')
        taxes = subtotal * tax_rate
        
        discount = Decimal('0')
        if promo_code:
            promo_code_upper = promo_code.upper()
            if promo_code_upper == 'WINTER20':
                discount = subtotal * Decimal('0.20')
            elif promo_code_upper == 'SAVE10':
                discount = subtotal * Decimal('0.10')
        
        total = subtotal + taxes - discount
        
        # B7: Create RoomBooking record
        booking = RoomBooking.objects.create(
            hotel=hotel,
            room_type=room_type,
            check_in=check_in,
            check_out=check_out,
            guest_first_name=guest_data['first_name'],
            guest_last_name=guest_data['last_name'],
            guest_email=guest_data['email'],
            guest_phone=guest_data['phone'],
            adults=adults,
            children=children,
            total_amount=total,
            currency=room_type.currency,
            status='PENDING_PAYMENT',
            special_requests=special_requests,
            promo_code=promo_code if promo_code else ''
        )
        # booking_id and confirmation_number auto-generated by model
        
        # Return response using booking data
        booking_data = {
            "booking_id": booking.booking_id,
            "confirmation_number": booking.confirmation_number,
            "status": booking.status,
            "created_at": booking.created_at.isoformat(),
            "hotel": {
                "name": hotel.name,
                "slug": hotel.slug,
                "phone": hotel.phone,
                "email": hotel.email
            },
            "room": {
                "type": room_type.name,
                "code": room_type.code or room_type.name,
                "photo": room_type.photo.url if room_type.photo else None
            },
            "dates": {
                "check_in": check_in_str,
                "check_out": check_out_str,
                "nights": nights
            },
            "guests": {
                "adults": adults,
                "children": children,
                "total": adults + children
            },
            "guest": {
                "name": booking.guest_name,
                "email": booking.guest_email,
                "phone": booking.guest_phone
            },
            "special_requests": special_requests,
            "pricing": {
                "subtotal": f"{subtotal:.2f}",
                "taxes": f"{taxes:.2f}",
                "discount": f"{discount:.2f}",
                "total": f"{total:.2f}",
                "currency": room_type.currency
            },
            "promo_code": promo_code if promo_code else None,
            "quote_id": quote_id if quote_id else None,
            "payment_required": True,
            "payment_url": (
                f"/api/bookings/{booking.booking_id}/payment/session/"
            )
        }
        
        return Response(booking_data, status=status.HTTP_201_CREATED)


# Staff Hotel Settings Views
# DEPRECATED: HotelPublicSettings model has been removed
# The HotelPublicSettingsStaffView class has been temporarily disabled
# TODO: Implement new hotel settings management system

# permission_classes = []  # Will be added in next step
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        from staff_chat.permissions import IsStaffMember, IsSameHotel
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def get(self, request, hotel_slug):
        """Retrieve hotel public settings"""
        # Get staff profile
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify hotel access
        if staff.hotel.slug != hotel_slug:
            return Response(
                {'error': 'You can only view settings for your hotel'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get or create settings
        settings, created = HotelPublicSettings.objects.get_or_create(
            hotel=staff.hotel
        )

        # Return settings
        from .serializers import HotelPublicSettingsStaffSerializer
        serializer = HotelPublicSettingsStaffSerializer(settings)
        return Response(serializer.data)

    def put(self, request, hotel_slug):
        return self._update_settings(request, hotel_slug, partial=False)

    def patch(self, request, hotel_slug):
        return self._update_settings(request, hotel_slug, partial=True)

    def _update_settings(self, request, hotel_slug, partial=False):
        # Get staff profile
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify hotel access
        if staff.hotel.slug != hotel_slug:
            return Response(
                {'error': 'You can only update settings for your hotel'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Optional: Restrict to admin/manager roles
        # Uncomment to enable role restriction
        # if staff.access_level not in ['super_staff_admin', 'staff_admin']:
        #     if not (staff.role and staff.role.slug in ['manager', 'admin']):
        #         return Response(
        #             {'error': 'Insufficient permissions'},
        #             status=status.HTTP_403_FORBIDDEN
        #         )

        # Get or create settings
        settings, created = HotelPublicSettings.objects.get_or_create(
            hotel=staff.hotel
        )

        # Track if any changes were made
        files_uploaded = False
        
        # Handle file uploads - Save to HOTEL model, not settings
        if 'hero_image' in request.FILES:
            staff.hotel.hero_image = request.FILES['hero_image']
            staff.hotel.save()
            files_uploaded = True
            print(f"[Settings] Hero image uploaded")
        if 'landing_page_image' in request.FILES:
            staff.hotel.landing_page_image = request.FILES['landing_page_image']
            staff.hotel.save()
            files_uploaded = True
            print(f"[Settings] Landing page image uploaded")
        if 'logo' in request.FILES:
            staff.hotel.logo = request.FILES['logo']
            staff.hotel.save()
            files_uploaded = True
            print(f"[Settings] Logo uploaded")

        # Update settings (text fields, colors, etc.)
        from .serializers import HotelPublicSettingsStaffSerializer
        serializer = HotelPublicSettingsStaffSerializer(
            settings,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()
            print(f"[Settings] Text/color fields saved")
        elif not files_uploaded:
            # Only return error if no files were uploaded
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Refresh settings from DB to get latest hotel data
        settings.refresh_from_db()
        
        # Get fresh data after save to include uploaded images
        updated_serializer = HotelPublicSettingsStaffSerializer(settings)
        
        # Log for debugging
        print(f"[Pusher] Broadcasting settings-updated to hotel-{hotel_slug}")
        print(f"[Pusher] Hero image URL: {updated_serializer.data.get('hero_image_url')}")
        
        # Broadcast settings update via Pusher with ALL fields
        try:
            from chat.utils import pusher_client
            from decimal import Decimal
            
            # Helper to convert Decimal to float for JSON serialization
            def serialize_value(value):
                if isinstance(value, Decimal):
                    return float(value)
                return value
            
            data = updated_serializer.data
            pusher_client.trigger(
                f'hotel-{hotel_slug}',
                'settings-updated',
                {
                    # Hotel override fields
                    'name_override': data.get('name_override'),
                    'name_display': data.get('name_display'),
                    'tagline_override': data.get('tagline_override'),
                    'tagline_display': data.get('tagline_display'),
                    'city_override': data.get('city_override'),
                    'city_display': data.get('city_display'),
                    'country_override': data.get('country_override'),
                    'country_display': data.get('country_display'),
                    'address_line_1_override': data.get('address_line_1_override'),
                    'address_line_1_display': data.get('address_line_1_display'),
                    'address_line_2_override': data.get('address_line_2_override'),
                    'address_line_2_display': data.get('address_line_2_display'),
                    'postal_code_override': data.get('postal_code_override'),
                    'postal_code_display': data.get('postal_code_display'),
                    'latitude_override': serialize_value(data.get('latitude_override')),
                    'latitude_display': serialize_value(data.get('latitude_display')),
                    'longitude_override': serialize_value(data.get('longitude_override')),
                    'longitude_display': serialize_value(data.get('longitude_display')),
                    'phone_override': data.get('phone_override'),
                    'phone_display': data.get('phone_display'),
                    'email_override': data.get('email_override'),
                    'email_display': data.get('email_display'),
                    'website_url_override': data.get('website_url_override'),
                    'website_url_display': data.get('website_url_display'),
                    'booking_url_override': data.get('booking_url_override'),
                    'booking_url_display': data.get('booking_url_display'),
                    # Content fields
                    'short_description': data.get('short_description'),
                    'long_description': data.get('long_description'),
                    'welcome_message': data.get('welcome_message'),
                    # Images
                    'hero_image': data.get('hero_image_url'),
                    'hero_image_url': data.get('hero_image_url'),
                    'hero_image_display': data.get('hero_image_display'),
                    'landing_page_image': data.get('landing_page_image_url'),
                    'landing_page_image_url': data.get('landing_page_image_url'),
                    'landing_page_image_display': data.get('landing_page_image_display'),
                    'logo': data.get('logo_display'),
                    'logo_display': data.get('logo_display'),
                    'galleries': data.get('galleries'),
                    'amenities': data.get('amenities'),
                    # Contact (legacy fields)
                    'contact_email': data.get('contact_email'),
                    'contact_phone': data.get('contact_phone'),
                    'contact_address': data.get('contact_address'),
                    'website': data.get('website'),
                    'google_maps_link': data.get('google_maps_link'),
                    'favicon': data.get('favicon'),
                    'slogan': data.get('slogan'),
                    # Branding colors
                    'primary_color': data.get('primary_color'),
                    'secondary_color': data.get('secondary_color'),
                    'accent_color': data.get('accent_color'),
                    'background_color': data.get('background_color'),
                    'button_color': data.get('button_color'),
                    'button_text_color': data.get('button_text_color'),
                    'button_hover_color': data.get('button_hover_color'),
                    'text_color': data.get('text_color'),
                    'border_color': data.get('border_color'),
                    'link_color': data.get('link_color'),
                    'link_hover_color': data.get('link_hover_color'),
                    'theme_mode': data.get('theme_mode'),
                    # Metadata
                    'updated_at': data.get('updated_at')
                }
            )
            print("[Pusher] Broadcast successful!")
        except Exception as e:
            print(f"[Pusher] ❌ Broadcast failed: {str(e)}")
# Staff Bookings Management Views

class StaffBookingsListView(APIView):
    """
    Staff endpoint to list room bookings for their hotel.
    GET /api/staff/hotels/<hotel_slug>/bookings/
    
    Supports filtering by:
    - status (pending, confirmed, cancelled, completed)
    - start_date / end_date (for check-in/check-out range)
    
    Requires:
    - User is authenticated
    - User has staff_profile
    - Staff belongs to the specified hotel
    """
    permission_classes = []
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        from staff_chat.permissions import IsStaffMember, IsSameHotel
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def get(self, request, hotel_slug):
        # Get staff profile
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify hotel access
        if staff.hotel.slug != hotel_slug:
            return Response(
                {'error': 'You can only view bookings for your hotel'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get bookings for staff's hotel
        bookings = RoomBooking.objects.filter(
            hotel=staff.hotel
        ).select_related('hotel', 'room_type').order_by('-created_at')

        # B8: Apply status filter with better validation
        status_filter = request.query_params.get('status')
        if status_filter:
            status_upper = status_filter.upper()
            # Validate status is a valid choice
            valid_statuses = [
                choice[0] for choice in RoomBooking.STATUS_CHOICES
            ]
            if status_upper not in valid_statuses:
                return Response(
                    {
                        'error': (
                            f'Invalid status. Choose from: '
                            f'{", ".join(valid_statuses)}'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            bookings = bookings.filter(status=status_upper)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            from datetime import datetime
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                bookings = bookings.filter(check_in__gte=start)
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date:
            from datetime import datetime
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                bookings = bookings.filter(check_out__lte=end)
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Serialize and return
        serializer = RoomBookingListSerializer(bookings, many=True)
        return Response(serializer.data)


class StaffBookingConfirmView(APIView):
    """
    Staff endpoint to confirm a booking.
    POST /api/staff/hotels/<hotel_slug>/bookings/<booking_id>/confirm/
    
    Updates booking status from PENDING_PAYMENT to CONFIRMED.
    Optionally stores confirmed_by and confirmed_at (if fields added).
    
    Requires:
    - User is authenticated
    - User has staff_profile
    - Staff belongs to the specified hotel
    - Optional: Staff has admin/manager access level
    """
    permission_classes = []
    
    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        from staff_chat.permissions import IsStaffMember, IsSameHotel
        return [IsAuthenticated(), IsStaffMember(), IsSameHotel()]

    def post(self, request, hotel_slug, booking_id):
        # Get staff profile
        try:
            staff = request.user.staff_profile
        except AttributeError:
            return Response(
                {'error': 'Staff profile not found'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify hotel access
        if staff.hotel.slug != hotel_slug:
            return Response(
                {'error': 'You can only confirm bookings for your hotel'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Optional: Restrict to admin/manager roles
        # Uncomment to enable role restriction
        # if staff.access_level not in ['super_staff_admin', 'staff_admin']:
        #     if not (staff.role and staff.role.slug in ['manager', 'admin']):
        #         return Response(
        #             {'error': 'Insufficient permissions'},
        #             status=status.HTTP_403_FORBIDDEN
        #         )

        # Get booking
        try:
            booking = RoomBooking.objects.get(
                booking_id=booking_id,
                hotel=staff.hotel
            )
        except RoomBooking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if booking can be confirmed
        if booking.status == 'CANCELLED':
            return Response(
                {'error': 'Cannot confirm a cancelled booking'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.status == 'CONFIRMED':
            return Response(
                {'message': 'Booking is already confirmed'},
                status=status.HTTP_200_OK
            )

        # Update booking status
        booking.status = 'CONFIRMED'
        
        # Store confirmation details if fields exist
        # (These fields would need to be added to model)
        # booking.confirmed_by = staff
        # booking.confirmed_at = timezone.now()
        
        booking.save()

        # Send confirmation email
        from .email_utils import send_booking_confirmation_email
        try:
            email_sent = send_booking_confirmation_email(booking)
            if not email_sent:
                # Log warning but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Booking confirmed but email failed for "
                    f"{booking.booking_id}"
                )
        except Exception as e:
            # Log error but don't crash the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"Exception sending confirmation email for "
                f"{booking.booking_id}: {str(e)}"
            )

        # Serialize and return
        serializer = RoomBookingDetailSerializer(booking)
        return Response({
            'message': 'Booking confirmed successfully',
            'booking': serializer.data
        })


class HotelPublicPageView(APIView):
    """
    Public API endpoint to get hotel page structure with all sections and elements.
    
    GET /api/public/hotel/<slug>/page/
    
    Returns all active sections for the hotel, ordered by position.
    Special handling for element_type='rooms_list' to return real room types
    from the database instead of custom items.
    
    No authentication required - public endpoint.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        # Get hotel
        hotel = get_object_or_404(Hotel, slug=slug, is_active=True)
        
        # Get all active sections with their elements, ordered by position
        sections = hotel.public_sections.filter(
            is_active=True
        ).select_related('element').prefetch_related('element__items').order_by('position')
        
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
            },
            'sections': []
        }
        
        for section in sections:
            # Skip sections without elements
            if not hasattr(section, 'element'):
                continue
            
            element = section.element
            
            # Build base section data
            section_data = {
                'id': section.id,
                'position': section.position,
                'name': section.name,
                'element': {
                    'id': element.id,
                    'element_type': element.element_type,
                    'title': element.title,
                    'subtitle': element.subtitle,
                    'body': element.body,
                    'image_url': element.image_url,
                    'settings': element.settings,
                }
            }
            
            # Special case: rooms_list element type
            if element.element_type == 'rooms_list':
                # Get real room types from the database
                room_types = hotel.room_types.filter(
                    is_active=True
                ).order_by('sort_order', 'name')
                
                # Serialize room types using RoomTypeSerializer
                from .serializers import RoomTypeSerializer
                room_types_data = RoomTypeSerializer(room_types, many=True).data
                section_data['element']['rooms'] = room_types_data
                section_data['element']['items'] = []  # No custom items for rooms_list
            else:
                # Standard elements: include custom items
                items = element.items.filter(is_active=True).order_by('sort_order')
                section_data['element']['items'] = [
                    {
                        'id': item.id,
                        'title': item.title,
                        'subtitle': item.subtitle,
                        'body': item.body,
                        'image_url': item.image_url,
                        'badge': item.badge,
                        'cta_label': item.cta_label,
                        'cta_url': item.cta_url,
                        'sort_order': item.sort_order,
                        'meta': item.meta,
                    }
                    for item in items
                ]
            
            response_data['sections'].append(section_data)
        
        return Response(response_data, status=status.HTTP_200_OK)


# ============================================================================
# STAFF PUBLIC PAGE BUILDER API
# ============================================================================

class PublicPageBuilderView(APIView):
    """
    Staff builder endpoint for a hotel's public page.
    Visible only to Super Staff Admin of that hotel.
    
    GET /api/staff/hotel/<hotel_slug>/hotel/public-page-builder/
    
    Returns:
      - hotel meta
      - sections with elements + items (or empty array if hotel is blank)
      - is_empty flag (true if no sections exist)
      - static presets for creating new sections
    
    This endpoint handles blank hotels gracefully - frontend gets all the tools
    it needs to build the page from scratch.
    """
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]

    def get(self, request, hotel_slug):
        # Get the hotel
        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        # Get all sections (active or not) for staff management
        sections = (
            PublicSection.objects
            .filter(hotel=hotel)
            .order_by("position")
            .select_related("element")
            .prefetch_related("element__items")
        )

        # Serialize sections
        section_data = PublicSectionStaffSerializer(sections, many=True).data

        # Check if hotel is empty (no sections)
        is_empty = len(section_data) == 0

        # Define presets that frontend can use to create sections
        presets = {
            "element_types": [
                "hero",
                "text_block",
                "image_block",
                "gallery",
                "cards_list",
                "reviews_list",
                "rooms_list",
                "contact_block",
                "map_block",
                "footer_block",
            ],
            "section_presets": [
                {
                    "key": "hero_default",
                    "label": "Hero Section",
                    "element_type": "hero",
                    "element_defaults": {
                        "title": "Welcome",
                        "subtitle": "Your perfect stay starts here",
                        "body": "",
                        "settings": {
                            "primary_cta_label": "Book Now",
                            "primary_cta_url": hotel.booking_url or "",
                        },
                    },
                },
                {
                    "key": "rooms_default",
                    "label": "Rooms List",
                    "element_type": "rooms_list",
                    "element_defaults": {
                        "title": "Our Rooms & Suites",
                        "subtitle": "",
                        "settings": {
                            "show_price_from": True,
                            "show_occupancy": True,
                            "columns": 2,
                        },
                    },
                },
                {
                    "key": "highlights_cards",
                    "label": "Highlights (Cards)",
                    "element_type": "cards_list",
                    "element_defaults": {
                        "title": "Why You'll Love Staying Here",
                        "subtitle": "",
                        "settings": {
                            "columns": 3,
                        },
                    },
                },
                {
                    "key": "gallery_default",
                    "label": "Gallery",
                    "element_type": "gallery",
                    "element_defaults": {
                        "title": "Explore the Hotel",
                        "subtitle": "",
                        "settings": {
                            "layout": "grid",
                        },
                    },
                },
                {
                    "key": "reviews_default",
                    "label": "Reviews",
                    "element_type": "reviews_list",
                    "element_defaults": {
                        "title": "What Our Guests Say",
                        "subtitle": "",
                    },
                },
                {
                    "key": "contact_default",
                    "label": "Contact & Map",
                    "element_type": "contact_block",
                    "element_defaults": {
                        "title": "Contact & Find Us",
                        "subtitle": "",
                        "body": "Get in touch or find us on the map.",
                    },
                },
            ],
        }

        # Build response
        response = {
            "hotel": {
                "id": hotel.id,
                "slug": hotel.slug,
                "name": hotel.name,
                "city": hotel.city,
                "country": hotel.country,
                "tagline": hotel.tagline,
                "booking_url": hotel.booking_url,
            },
            "is_empty": is_empty,
            "sections": section_data,
            "presets": presets,
        }

        return Response(response)


class HotelStatusCheckView(APIView):
    """
    Quick endpoint to check hotel's current state.
    Useful for debugging and verifying blank state.
    
    GET /api/staff/hotel/<hotel_slug>/hotel/status/
    
    Returns hotel info, section count, and blank state indicators.
    """
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]

    def get(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        section_count = PublicSection.objects.filter(hotel=hotel).count()
        
        return Response({
            "hotel": {
                "id": hotel.id,
                "name": hotel.name,
                "slug": hotel.slug,
                "city": hotel.city,
                "country": hotel.country,
            },
            "branding": {
                "has_hero_image": bool(hotel.hero_image),
                "hero_image_url": hotel.hero_image.url if hotel.hero_image else None,
                "has_logo": bool(hotel.logo),
                "logo_url": hotel.logo.url if hotel.logo else None,
                "tagline": hotel.tagline or None,
                "booking_url": hotel.booking_url or None,
            },
            "content": {
                "has_short_description": bool(hotel.short_description),
                "has_long_description": bool(hotel.long_description),
                "tags": hotel.tags or [],
            },
            "public_page": {
                "section_count": section_count,
                "is_empty": section_count == 0,
            },
            "ready_for_builder": section_count == 0,
        })


class PublicPageBootstrapView(APIView):
    """
    Bootstrap a hotel with default public page sections.
    Only works if hotel currently has ZERO sections.
    
    POST /api/staff/hotel/<hotel_slug>/hotel/public-page-builder/bootstrap-default/
    
    Creates:
    - Hero section
    - Rooms list section
    - Highlights cards section
    - Gallery section
    - Reviews section
    - Contact section
    
    Returns the same structure as PublicPageBuilderView GET endpoint.
    """
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]

    def post(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)

        # Check if hotel already has sections
        existing_count = PublicSection.objects.filter(hotel=hotel).count()
        if existing_count > 0:
            return Response(
                {
                    "detail": f"Hotel already has {existing_count} section(s). Bootstrap only works on empty hotels."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create default sections
        sections_created = []

        # 1. Hero Section
        hero_section = PublicSection.objects.create(
            hotel=hotel,
            position=0,
            name="Hero",
            is_active=True
        )
        PublicElement.objects.create(
            section=hero_section,
            element_type="hero",
            title="Welcome",
            subtitle="Your perfect stay starts here",
            body="",
            image_url="",
            settings={
                "primary_cta_label": "Book Now",
                "primary_cta_url": hotel.booking_url or "",
            }
        )
        sections_created.append("hero")

        # 2. Rooms List
        rooms_section = PublicSection.objects.create(
            hotel=hotel,
            position=1,
            name="Rooms",
            is_active=True
        )
        PublicElement.objects.create(
            section=rooms_section,
            element_type="rooms_list",
            title="Our Rooms & Suites",
            subtitle="",
            body="",
            image_url="",
            settings={
                "show_price_from": True,
                "show_occupancy": True,
                "columns": 2,
            }
        )
        sections_created.append("rooms_list")

        # 3. Highlights (Cards)
        highlights_section = PublicSection.objects.create(
            hotel=hotel,
            position=2,
            name="Highlights",
            is_active=True
        )
        highlights_element = PublicElement.objects.create(
            section=highlights_section,
            element_type="cards_list",
            title="Why You'll Love Staying Here",
            subtitle="",
            body="",
            image_url="",
            settings={"columns": 3}
        )
        # Add sample cards
        PublicElementItem.objects.create(
            element=highlights_element,
            title="Family Friendly",
            subtitle="Perfect for all ages",
            body="Spacious family rooms, kids' activities, and flexible dining options.",
            image_url="",
            sort_order=0,
            is_active=True
        )
        PublicElementItem.objects.create(
            element=highlights_element,
            title="Prime Location",
            subtitle="Easy access to attractions",
            body="Close to all major attractions, shops, and restaurants.",
            image_url="",
            sort_order=1,
            is_active=True
        )
        PublicElementItem.objects.create(
            element=highlights_element,
            title="Excellent Service",
            subtitle="5-star hospitality",
            body="Our team is dedicated to making your stay memorable.",
            image_url="",
            sort_order=2,
            is_active=True
        )
        sections_created.append("highlights")

        # 4. Gallery
        gallery_section = PublicSection.objects.create(
            hotel=hotel,
            position=3,
            name="Gallery",
            is_active=True
        )
        PublicElement.objects.create(
            section=gallery_section,
            element_type="gallery",
            title="Explore the Hotel",
            subtitle="",
            body="",
            image_url="",
            settings={"layout": "grid"}
        )
        sections_created.append("gallery")

        # 5. Reviews
        reviews_section = PublicSection.objects.create(
            hotel=hotel,
            position=4,
            name="Reviews",
            is_active=True
        )
        PublicElement.objects.create(
            section=reviews_section,
            element_type="reviews_list",
            title="What Our Guests Say",
            subtitle="",
            body="",
            image_url="",
            settings={}
        )
        sections_created.append("reviews")

        # 6. Contact
        contact_section = PublicSection.objects.create(
            hotel=hotel,
            position=5,
            name="Contact",
            is_active=True
        )
        PublicElement.objects.create(
            section=contact_section,
            element_type="contact_block",
            title="Contact & Find Us",
            subtitle="",
            body="Get in touch or find us on the map.",
            image_url="",
            settings={}
        )
        sections_created.append("contact")

        # Return the same structure as GET endpoint
        sections = (
            PublicSection.objects
            .filter(hotel=hotel)
            .order_by("position")
            .select_related("element")
            .prefetch_related("element__items")
        )

        section_data = PublicSectionStaffSerializer(sections, many=True).data

        return Response(
            {
                "message": f"Successfully created {len(sections_created)} default sections",
                "sections_created": sections_created,
                "hotel": {
                    "id": hotel.id,
                    "slug": hotel.slug,
                    "name": hotel.name,
                },
                "is_empty": False,
                "sections": section_data,
            },
            status=status.HTTP_201_CREATED
        )


class SectionCreateView(APIView):
    """
    Enhanced section creation endpoint that automatically initializes
    section-specific data based on type.
    
    POST /api/staff/hotel/<hotel_slug>/hotel/sections/create/
    
    Body:
    {
        "section_type": "hero" | "gallery" | "list" | "news" (required),
        "name": "Section name (optional, defaults to '{Type} Section')",
        "position": 0,  // optional, defaults to end
        "container_name": "Name for first gallery/list container (optional)",
        "article_title": "Title for first news article (optional, for news type)"
    }
    
    Behavior:
    - hero: Creates HeroSection with placeholder text (no name needed)
    - gallery: Creates one GalleryContainer with optional name
    - list: Creates one ListContainer with optional name
    - news: Creates first NewsItem with cover image + text/image blocks
    """
    permission_classes = [IsAuthenticated, IsSuperStaffAdminForHotel]
    
    def post(self, request, hotel_slug):
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        section_type = request.data.get('section_type')
        if not section_type:
            return Response(
                {'error': 'section_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if section_type not in ['hero', 'gallery', 'list', 'news']:
            return Response(
                {'error': 'Invalid section_type. Must be: hero, gallery, list, or news'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get optional section name, container name, and article title
        name = request.data.get('name', f'{section_type.title()} Section')
        container_name = request.data.get('container_name', '')
        article_title = request.data.get('article_title', '')
        
        # Get position (default to end)
        position = request.data.get('position')
        if position is None:
            max_pos = PublicSection.objects.filter(hotel=hotel).aggregate(
                models.Max('position')
            )['position__max']
            position = (max_pos or -1) + 1
        
        # Create section
        section = PublicSection.objects.create(
            hotel=hotel,
            position=position,
            name=name,
            is_active=True
        )
        
        # Initialize based on type
        if section_type == 'hero':
            # Create HeroSection with placeholders
            # Images will be uploaded separately via upload endpoints
            HeroSection.objects.create(
                section=section,
                hero_title="Update your hero title here",
                hero_text="Update your hero description text here.",
                # hero_image and hero_logo remain null until uploaded
            )
            
        elif section_type == 'gallery':
            # Create one gallery container with optional name
            gallery_name = container_name if container_name else "Gallery 1"
            GalleryContainer.objects.create(
                section=section,
                name=gallery_name,
                sort_order=0
            )
            
        elif section_type == 'list':
            # Create one list container with optional name
            list_title = container_name if container_name else ""
            ListContainer.objects.create(
                section=section,
                title=list_title,
                sort_order=0
            )
            
        elif section_type == 'news':
            # Create first news article with placeholders
            from datetime import date
            
            news_title = article_title if article_title else "Update Article Title"
            news_item = NewsItem.objects.create(
                section=section,
                title=news_title,
                date=date.today(),
                summary="Add a brief summary of this article here.",
                sort_order=0
            )
            
            # Create placeholder content blocks:
            # 1. Cover image block (full width)
            ContentBlock.objects.create(
                news_item=news_item,
                block_type='image',
                image_position='full_width',
                image_caption='Add cover image',
                sort_order=0
            )
            
            # 2. First text block
            ContentBlock.objects.create(
                news_item=news_item,
                block_type='text',
                body='Add your article introduction text here. This is the opening paragraph.',
                sort_order=1
            )
            
            # 3. First inline image
            ContentBlock.objects.create(
                news_item=news_item,
                block_type='image',
                image_position='right',
                image_caption='Add first inline image',
                sort_order=2
            )
            
            # 4. Second text block
            ContentBlock.objects.create(
                news_item=news_item,
                block_type='text',
                body='Add more article content here. Continue your story.',
                sort_order=3
            )
            
            # 5. Second inline image
            ContentBlock.objects.create(
                news_item=news_item,
                block_type='image',
                image_position='left',
                image_caption='Add second inline image',
                sort_order=4
            )
            
            # 6. Final text block
            ContentBlock.objects.create(
                news_item=news_item,
                block_type='text',
                body='Add your closing paragraph here. Wrap up the article.',
                sort_order=5
            )
        
        # Return detailed section data
        serializer = PublicSectionDetailSerializer(section)
        return Response({
            'message': f'{section_type.title()} section created successfully',
            'section': serializer.data
        }, status=status.HTTP_201_CREATED)
