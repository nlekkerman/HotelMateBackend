"""
GUEST Zone Routing Wrapper - Phase 1
Routes for guest-facing public hotel pages.
Returns real hotel data including booking options.
"""

from django.urls import path
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from hotel.models import Hotel, RoomBooking, PricingQuote
from rooms.models import RoomType, Room


def guest_home(request, hotel_slug):
    """Guest home page - returns hotel info with booking options"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Get booking options if they exist
    booking_options = None
    if hasattr(hotel, 'booking_options'):
        booking_options = {
            'primary_cta_label': hotel.booking_options.primary_cta_label,
            'primary_cta_url': hotel.booking_options.primary_cta_url,
            'secondary_cta_label': hotel.booking_options.secondary_cta_label,
            'secondary_cta_phone': hotel.booking_options.secondary_cta_phone,
            'terms_url': hotel.booking_options.terms_url,
            'policies_url': hotel.booking_options.policies_url,
        }
    
    return JsonResponse({
        'hotel': {
            'id': hotel.id,
            'name': hotel.name,
            'slug': hotel.slug,
            'hero_image': hotel.hero_image.url if hotel.hero_image else None,
            'description': hotel.description,
            'address': hotel.address,
            'phone': hotel.phone,
            'email': hotel.email,
            'website': hotel.website,
            'booking_options': booking_options,
        }
    })


def guest_rooms(request, hotel_slug):
    """Guest rooms page - returns room types with photos"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    rooms = RoomType.objects.filter(hotel=hotel)
    
    return JsonResponse({
        'rooms': [
            {
                'id': room.id,
                'name': room.name,
                'code': room.code,
                'photo': room.photo.url if room.photo else None,
                'description': room.description,
                'base_price': str(room.base_price),
                'max_occupancy': room.max_occupancy,
            }
            for room in rooms
        ]
    })


def check_availability(request, hotel_slug):
    """Check room availability for given dates and occupancy"""
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    # Get query parameters
    check_in_str = request.GET.get('check_in')
    check_out_str = request.GET.get('check_out')
    adults = int(request.GET.get('adults', 2))
    children = int(request.GET.get('children', 0))
    
    # Validate dates
    if not check_in_str or not check_out_str:
        return JsonResponse({
            'error': 'check_in and check_out dates are required'
        }, status=400)
    
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=400)
    
    # Validate date logic
    today = timezone.now().date()
    if check_in < today:
        return JsonResponse({
            'error': 'Check-in date must be in the future'
        }, status=400)
    
    if check_out <= check_in:
        return JsonResponse({
            'error': 'Check-out must be after check-in'
        }, status=400)
    
    nights = (check_out - check_in).days
    
    # Get all room types for this hotel
    room_types = RoomType.objects.filter(hotel=hotel)
    
    available_rooms = []
    for room_type in room_types:
        # Count total bookable rooms of this type
        # Updated for Room Turnover Workflow - only count bookable rooms
        total_rooms = Room.objects.filter(
            room_type=room_type,
            room_status__in=['AVAILABLE', 'READY_FOR_GUEST'],
            is_active=True,
            maintenance_required=False,
            is_out_of_order=False
        ).count()
        
        # Count booked rooms for this date range
        booked_count = RoomBooking.objects.filter(
            hotel=hotel,
            room_type=room_type,
            status__in=['CONFIRMED', 'PENDING_PAYMENT'],
            check_in__lt=check_out,
            check_out__gt=check_in
        ).count()
        
        available_units = total_rooms - booked_count
        is_available = available_units > 0
        
        # Add note if low availability
        note = None
        if is_available and available_units <= 3:
            note = f"Only {available_units} room(s) remaining"
        
        available_rooms.append({
            'room_type_code': room_type.code,
            'room_type_name': room_type.name,
            'is_available': is_available,
            'available_units': available_units,
            'photo': room_type.photo.url if room_type.photo else None,
            'description': room_type.description,
            'base_price': str(room_type.base_price),
            'max_occupancy': room_type.max_occupancy,
            'note': note
        })
    
    return JsonResponse({
        'hotel': hotel.slug,
        'check_in': check_in_str,
        'check_out': check_out_str,
        'nights': nights,
        'adults': adults,
        'children': children,
        'available_rooms': available_rooms
    })


@csrf_exempt
def get_pricing_quote(request, hotel_slug):
    """Calculate pricing quote for a booking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Extract data
    room_type_code = data.get('room_type_code')
    check_in_str = data.get('check_in')
    check_out_str = data.get('check_out')
    adults = data.get('adults', 2)
    children = data.get('children', 0)
    promo_code = data.get('promo_code', '')
    
    # Validate
    if not all([room_type_code, check_in_str, check_out_str]):
        return JsonResponse({
            'error': 'room_type_code, check_in, check_out required'
        }, status=400)
    
    # Get room type
    try:
        room_type = RoomType.objects.get(code=room_type_code, hotel=hotel)
    except RoomType.DoesNotExist:
        return JsonResponse({'error': 'Room type not found'}, status=404)
    
    # Parse dates
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({
            'error': 'Invalid date format'
        }, status=400)
    
    # Calculate pricing
    nights = (check_out - check_in).days
    base_price_per_night = Decimal(str(room_type.base_price))
    subtotal = base_price_per_night * nights
    
    # Calculate taxes (9% VAT for Ireland)
    taxes = subtotal * Decimal('0.09')
    
    # Check for promo/offer
    discount = Decimal('0')
    applied_offer = None
    
    if promo_code:
        try:
            offer = Offer.objects.get(
                hotel=hotel,
                promo_code=promo_code,
                is_active=True
            )
            if offer.discount_percentage:
                discount = subtotal * (offer.discount_percentage / 100)
                applied_offer = {
                    'code': promo_code,
                    'description': offer.description,
                    'discount_percentage': str(offer.discount_percentage)
                }
        except Offer.DoesNotExist:
            pass
    
    total = subtotal + taxes - discount
    
    # Create quote
    quote = PricingQuote.objects.create(
        hotel=hotel,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        children=children,
        base_price_per_night=base_price_per_night,
        number_of_nights=nights,
        subtotal=subtotal,
        taxes=taxes,
        fees=Decimal('0'),
        discount=discount,
        total=total,
        currency='EUR',
        promo_code=promo_code,
        valid_until=timezone.now() + timedelta(minutes=30)
    )
    
    return JsonResponse({
        'quote_id': quote.quote_id,
        'valid_until': quote.valid_until.isoformat(),
        'currency': 'EUR',
        'breakdown': {
            'base_price_per_night': str(base_price_per_night),
            'number_of_nights': nights,
            'subtotal': str(subtotal),
            'taxes': str(taxes),
            'fees': '0.00',
            'discount': str(discount),
            'total': str(total)
        },
        'applied_promo': applied_offer
    })


@csrf_exempt
def create_booking(request, hotel_slug):
    """Create a new room booking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    hotel = get_object_or_404(Hotel, slug=hotel_slug)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Extract data using NEW field structure
    quote_id = data.get('quote_id')
    room_type_code = data.get('room_type_code')
    check_in_str = data.get('check_in')
    check_out_str = data.get('check_out')
    adults = data.get('adults', 2)
    children = data.get('children', 0)
    
    # NEW primary guest fields
    primary_first_name = data.get('primary_first_name')
    primary_last_name = data.get('primary_last_name')
    primary_email = data.get('primary_email')
    primary_phone = data.get('primary_phone', '')
    
    special_requests = data.get('special_requests', '')
    promo_code = data.get('promo_code', '')
    
    # Validate required fields
    required_fields = ['room_type_code', 'check_in', 'check_out']
    required_primary_fields = ['primary_first_name', 'primary_last_name', 'primary_email']
    
    if not all(data.get(f) for f in required_fields):
        return JsonResponse({
            'error': 'Missing required fields'
        }, status=400)
    
    if not all(data.get(f) for f in required_primary_fields):
        return JsonResponse({
            'error': 'Missing primary guest information'
        }, status=400)
    
    # Get room type
    try:
        room_type = RoomType.objects.get(code=room_type_code, hotel=hotel)
    except RoomType.DoesNotExist:
        return JsonResponse({'error': 'Room type not found'}, status=404)
    
    # Parse dates
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get quote if provided
    total_amount = Decimal('0')
    if quote_id:
        try:
            quote = PricingQuote.objects.get(quote_id=quote_id)
            if not quote.is_valid():
                return JsonResponse({
                    'error': 'Quote has expired'
                }, status=400)
            total_amount = quote.total
        except PricingQuote.DoesNotExist:
            return JsonResponse({'error': 'Invalid quote'}, status=404)
    else:
        # Calculate on the fly
        nights = (check_out - check_in).days
        subtotal = Decimal(str(room_type.base_price)) * nights
        taxes = subtotal * Decimal('0.09')
        total_amount = subtotal + taxes
    
    # Create booking using NEW field structure
    booking = RoomBooking.objects.create(
        hotel=hotel,
        room_type=room_type,
        check_in=check_in,
        check_out=check_out,
        primary_first_name=primary_first_name,
        primary_last_name=primary_last_name,
        primary_email=primary_email,
        primary_phone=primary_phone,
        booker_type='SELF',  # Default to self-booking for this endpoint
        adults=adults,
        children=children,
        total_amount=total_amount,
        currency='EUR',
        status='PENDING_PAYMENT',
        special_requests=special_requests,
        promo_code=promo_code
    )
    
    return JsonResponse({
        'booking_id': booking.booking_id,
        'confirmation_number': booking.confirmation_number,
        'status': booking.status,
        'hotel': {
            'name': hotel.name,
            'slug': hotel.slug
        },
        'room': {
            'type': room_type.name,
            'code': room_type.code
        },
        'dates': {
            'check_in': check_in_str,
            'check_out': check_out_str,
            'nights': booking.nights
        },
        'guest': {
            'name': booking.primary_guest_name,
            'email': booking.primary_email,
            'phone': booking.primary_phone
        },
        'pricing': {
            'total': str(booking.total_amount),
            'currency': booking.currency
        },
        'created_at': booking.created_at.isoformat(),
        'payment_required': True
    }, status=201)


urlpatterns = [
    # Base guest hotel endpoint
    path(
        'hotels/<str:hotel_slug>/',
        guest_home,
        name='guest-hotel-detail'
    ),
    path(
        'hotels/<str:hotel_slug>/site/home/',
        guest_home,
        name='guest-home'
    ),
    path(
        'hotels/<str:hotel_slug>/site/rooms/',
        guest_rooms,
        name='guest-rooms'
    ),
    # Booking endpoints
    path(
        'hotels/<str:hotel_slug>/availability/',
        check_availability,
        name='check-availability'
    ),
    path(
        'hotels/<str:hotel_slug>/pricing/quote/',
        get_pricing_quote,
        name='pricing-quote'
    ),
    path(
        'hotels/<str:hotel_slug>/bookings/',
        create_booking,
        name='create-booking'
    ),
]
