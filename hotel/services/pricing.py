"""
Pricing Service

Advanced pricing engine with:
- Rate plan management
- Daily rate overrides
- Promotion/discount application
- Tax calculations

No DRF dependencies - pure business logic.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Tuple, Optional

from django.utils import timezone
from django.db.models import Q

from hotel.models import Hotel, PricingQuote
from rooms.models import RoomType, RatePlan, RoomTypeRatePlan, DailyRate, Promotion


# Constants
VAT_RATE = Decimal('0.09')  # Ireland VAT for accommodation
DEFAULT_RATE_PLAN_CODE = "STD"


def get_or_create_default_rate_plan(hotel: Hotel) -> RatePlan:
    """
    Ensure there's a default 'Standard' rate plan per hotel.
    Lazy creation - only creates when needed.
    
    Args:
        hotel: Hotel instance
    
    Returns:
        RatePlan instance (Standard rate plan for the hotel)
    """
    rate_plan, created = RatePlan.objects.get_or_create(
        hotel=hotel,
        code=DEFAULT_RATE_PLAN_CODE,
        defaults={
            'name': 'Standard Rate',
            'description': 'Standard flexible rate',
            'is_refundable': True,
            'default_discount_percent': Decimal('0'),
            'is_active': True
        }
    )
    return rate_plan


def get_nightly_base_rates(
    room_type: RoomType,
    check_in: date,
    check_out: date,
    rate_plan: Optional[RatePlan] = None
) -> List[Tuple[date, Decimal]]:
    """
    For the given RoomType and RatePlan, produce nightly rates.
    Returns [(date, price), ...] for each night in [check_in, check_out).
    
    Priority for each night:
    1. DailyRate for (room_type, rate_plan, date)
    2. RoomTypeRatePlan.base_price for that combo
    3. room_type.starting_price_from
    
    Args:
        room_type: RoomType instance
        check_in: Check-in date
        check_out: Check-out date
        rate_plan: RatePlan instance (if None, use default for hotel)
    
    Returns:
        List of (date, price) tuples
    """
    if rate_plan is None:
        rate_plan = get_or_create_default_rate_plan(room_type.hotel)
    
    nightly_rates = []
    current_date = check_in
    
    # Try to get RoomTypeRatePlan base price as fallback
    room_type_rate_plan_price = None
    try:
        rtrp = RoomTypeRatePlan.objects.get(
            room_type=room_type,
            rate_plan=rate_plan,
            is_active=True
        )
        if rtrp.base_price is not None:
            room_type_rate_plan_price = rtrp.base_price
    except RoomTypeRatePlan.DoesNotExist:
        pass
    
    # Default fallback price
    default_price = Decimal(str(room_type.starting_price_from))
    
    while current_date < check_out:
        # Priority 1: DailyRate
        try:
            daily_rate = DailyRate.objects.get(
                room_type=room_type,
                rate_plan=rate_plan,
                date=current_date
            )
            price = daily_rate.price
        except DailyRate.DoesNotExist:
            # Priority 2: RoomTypeRatePlan base price
            if room_type_rate_plan_price is not None:
                price = room_type_rate_plan_price
            else:
                # Priority 3: Default starting price
                price = default_price
        
        nightly_rates.append((current_date, price))
        current_date += timedelta(days=1)
    
    return nightly_rates


def apply_promotion(
    hotel: Hotel,
    room_type: RoomType,
    rate_plan: RatePlan,
    check_in: date,
    check_out: date,
    subtotal: Decimal,
    promo_code: str
) -> Tuple[Decimal, Decimal, Optional[Promotion]]:
    """
    Apply a Promotion if promo_code is valid.
    Single promotion per booking (no stacking).
    
    Priority:
    1. Try Promotion model:
       - Match code (case-insensitive), hotel, date range, is_active
       - Validate room_types, rate_plans, min_nights, max_nights restrictions
       - Apply discount_percent and/or discount_fixed
    2. Fallback to legacy hardcoded codes:
       - WINTER20 -> 20% off
       - SAVE10 -> 10% off
    
    Args:
        hotel: Hotel instance
        room_type: RoomType instance
        rate_plan: RatePlan instance
        check_in: Check-in date
        check_out: Check-out date
        subtotal: Subtotal amount before discount
        promo_code: Promo code to apply
    
    Returns:
        Tuple of (new_subtotal, discount_amount, promotion_instance_or_None)
    """
    if not promo_code:
        return subtotal, Decimal('0'), None
    
    promo_code_upper = promo_code.upper()
    nights = (check_out - check_in).days
    
    # Try to find Promotion model instance
    try:
        promotion = Promotion.objects.get(
            code__iexact=promo_code,
            hotel=hotel,
            is_active=True,
            valid_from__lte=check_in,
            valid_until__gte=check_out
        )
        
        # Validate room type restrictions
        if promotion.room_types.exists():
            if not promotion.room_types.filter(id=room_type.id).exists():
                # Room type not eligible
                return subtotal, Decimal('0'), None
        
        # Validate rate plan restrictions
        if promotion.rate_plans.exists():
            if not promotion.rate_plans.filter(id=rate_plan.id).exists():
                # Rate plan not eligible
                return subtotal, Decimal('0'), None
        
        # Validate min/max nights
        if promotion.min_nights and nights < promotion.min_nights:
            return subtotal, Decimal('0'), None
        if promotion.max_nights and nights > promotion.max_nights:
            return subtotal, Decimal('0'), None
        
        # Apply discount
        discount = Decimal('0')
        
        # Apply percentage discount
        if promotion.discount_percent:
            discount += subtotal * (promotion.discount_percent / Decimal('100'))
        
        # Apply fixed discount
        if promotion.discount_fixed:
            discount += promotion.discount_fixed
        
        # Ensure discount doesn't exceed subtotal
        discount = min(discount, subtotal)
        
        new_subtotal = subtotal - discount
        # Return immediately - only ONE promotion applies (no stacking)
        return new_subtotal, discount, promotion
        
    except Promotion.DoesNotExist:
        pass
    
    # Fallback to legacy hardcoded promo codes
    discount = Decimal('0')
    if promo_code_upper == 'WINTER20':
        discount = subtotal * Decimal('0.20')
    elif promo_code_upper == 'SAVE10':
        discount = subtotal * Decimal('0.10')
    
    if discount > 0:
        new_subtotal = subtotal - discount
        return new_subtotal, discount, None
    
    # No valid promotion found
    return subtotal, Decimal('0'), None


def apply_taxes(subtotal: Decimal) -> Tuple[Decimal, Decimal]:
    """
    Apply VAT_RATE to subtotal.
    
    Args:
        subtotal: Subtotal amount before taxes
    
    Returns:
        Tuple of (total_with_taxes, taxes_amount)
    """
    taxes = subtotal * VAT_RATE
    total = subtotal + taxes
    return total, taxes


def build_pricing_quote_data(
    hotel: Hotel,
    room_type: RoomType,
    check_in: date,
    check_out: date,
    adults: int,
    children: int,
    promo_code: str = ""
) -> Dict:
    """
    High-level pricing quote builder.
    
    Flow:
    1. Get or create default RatePlan
    2. Calculate nightly base rates and subtotal
    3. Apply promotion (if valid)
    4. Apply taxes
    5. Create PricingQuote instance
    6. Return dict matching HotelPricingQuoteView response schema
    
    Args:
        hotel: Hotel instance
        room_type: RoomType instance
        check_in: Check-in date
        check_out: Check-out date
        adults: Number of adults
        children: Number of children
        promo_code: Optional promo code
    
    Returns:
        Dict matching existing pricing quote response format
    """
    # Get rate plan
    rate_plan = get_or_create_default_rate_plan(hotel)
    
    # Calculate nightly rates
    nightly_rates = get_nightly_base_rates(room_type, check_in, check_out, rate_plan)
    nights = len(nightly_rates)
    
    # Calculate subtotal
    subtotal = sum(price for _, price in nightly_rates)
    
    # Use first night's price as base_price_per_night for backward compatibility
    base_price_per_night = nightly_rates[0][1] if nightly_rates else Decimal('0')
    
    # Apply promotion
    subtotal_after_promo, discount, promotion = apply_promotion(
        hotel, room_type, rate_plan, check_in, check_out, subtotal, promo_code
    )
    
    # Apply taxes
    total, taxes = apply_taxes(subtotal_after_promo)
    
    # Quote valid for 30 minutes
    valid_until = timezone.now() + timedelta(minutes=30)
    
    # Create PricingQuote record
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
        fees=Decimal('0'),  # No fees for now
        discount=discount,
        total=total,
        currency=room_type.currency,
        promo_code=promo_code if promo_code else '',
        valid_until=valid_until
    )
    
    # Build applied_promo data
    applied_promo = None
    if discount > 0:
        if promotion:
            # Use Promotion model data
            discount_pct = "0.00"
            if promotion.discount_percent:
                discount_pct = f"{promotion.discount_percent:.2f}"
            
            applied_promo = {
                "code": promotion.code,
                "description": promotion.name or promotion.description,
                "discount_percentage": discount_pct
            }
        else:
            # Legacy promo code
            promo_upper = promo_code.upper()
            if promo_upper == 'WINTER20':
                applied_promo = {
                    "code": "WINTER20",
                    "description": "20% off winter bookings",
                    "discount_percentage": "20.00"
                }
            elif promo_upper == 'SAVE10':
                applied_promo = {
                    "code": "SAVE10",
                    "description": "10% off your stay",
                    "discount_percentage": "10.00"
                }
    
    # Build response dict matching existing schema
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
            "check_in": check_in.strftime('%Y-%m-%d'),
            "check_out": check_out.strftime('%Y-%m-%d'),
            "nights": nights
        },
        "guests": {
            "adults": adults,
            "children": children,
            "total": adults + children
        },
        "breakdown": {
            "base_price_per_night": f"{base_price_per_night:.2f}",
            "number_of_nights": nights,
            "subtotal": f"{subtotal:.2f}",
            "taxes": f"{taxes:.2f}",
            "fees": "0.00",
            "discount": f"-{discount:.2f}" if discount > 0 else "0.00",
            "total": f"{total:.2f}"
        },
        "applied_promo": applied_promo
    }
    
    return response_data
