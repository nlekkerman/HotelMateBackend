from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import models
from datetime import datetime

from .models import Hotel, HotelPublicSettings, RoomBooking, PricingQuote
from .serializers import (
    HotelSerializer,
    HotelPublicSerializer,
    HotelPublicDetailSerializer,
    RoomBookingListSerializer,
    RoomBookingDetailSerializer
)


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
    - q: text search in name, city, country
    - city: filter by city (exact match)
    - country: filter by country (exact match)
    - tags: comma-separated list of tags
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
                models.Q(country__icontains=q)
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
        
        return Response({
            'cities': list(cities),
            'countries': list(countries),
            'tags': sorted(list(all_tags))
        })


class HotelPublicDetailView(generics.RetrieveAPIView):
    """
    Public API endpoint for single hotel details by slug.
    Returns hotel with branding and portal configuration.
    """
    serializer_class = HotelPublicSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        """Only return active hotels with access_config"""
        return Hotel.objects.filter(
            is_active=True
        ).select_related('access_config')


class HotelPublicPageView(generics.RetrieveAPIView):
    """
    Public API endpoint for complete hotel page content.
    Returns full hotel details including booking options,
    room types, offers, and leisure activities.
    For non-authenticated public users browsing hotels.
    """
    serializer_class = HotelPublicDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        """Optimized query with all related objects"""
        return Hotel.objects.filter(
            is_active=True
        ).select_related(
            'booking_options'
        ).prefetch_related(
            'room_types',
            'offers',
            'leisure_activities'
        )


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
            applied_offer=None,
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


# Hotel Public Settings Views

class HotelPublicSettingsView(APIView):
    """
    Public read-only endpoint for hotel public settings.
    GET /api/public/hotels/<hotel_slug>/settings/
    """
    permission_classes = [AllowAny]

    def get(self, request, hotel_slug):
        # Get hotel by slug
        hotel = get_object_or_404(Hotel, slug=hotel_slug)
        
        # Get or create settings for this hotel
        settings, created = HotelPublicSettings.objects.get_or_create(
            hotel=hotel
        )
        
        # Serialize and return
        from .serializers import HotelPublicSettingsPublicSerializer
        serializer = HotelPublicSettingsPublicSerializer(settings)
        return Response(serializer.data)


class HotelPublicSettingsStaffView(APIView):
    """
    Staff-only endpoint to retrieve and update hotel public settings.
    GET /api/staff/hotels/<hotel_slug>/settings/ - Retrieve settings
    PUT/PATCH /api/staff/hotels/<hotel_slug>/settings/ - Update settings
    
    Requires:
    - User is authenticated
    - User has staff_profile
    - Staff belongs to the specified hotel
    - Optionally: Staff has admin/manager access level
    """
    permission_classes = []  # Will be added in next step
    
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

        # Update settings
        from .serializers import HotelPublicSettingsStaffSerializer
        serializer = HotelPublicSettingsStaffSerializer(
            settings,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


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
