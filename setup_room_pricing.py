#!/usr/bin/env python3
"""
Set base prices for all room types and update pricing logic.
This will set base_price equal to starting_price_from, then apply discounts when available.
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HotelMateBackend.settings')
django.setup()

from rooms.models import RoomType, RatePlan, RoomTypeRatePlan, Promotion
from hotel.models import Hotel


def set_base_prices():
    """Set base prices for all room types based on starting_price_from"""
    print("🏨 Setting base prices for all room types...\n")
    
    room_types = RoomType.objects.filter(is_active=True)
    updated_count = 0
    
    for room_type in room_types:
        starting_price = room_type.starting_price_from
        print(f"📝 {room_type.hotel.name} - {room_type.name}")
        print(f"   Starting price: {starting_price} {room_type.currency}")
        
        # Create or get default rate plan for this hotel
        hotel = room_type.hotel
        rate_plan, created = RatePlan.objects.get_or_create(
            hotel=hotel,
            code='STANDARD',
            defaults={
                'name': 'Standard Rate',
                'description': 'Standard room rate',
                'is_refundable': True,
                'default_discount_percent': Decimal('0.00'),
                'is_active': True,
            }
        )
        
        if created:
            print(f"   ✅ Created default rate plan for {hotel.name}")
        
        # Create or update room type rate plan with base price
        room_rate, rate_created = RoomTypeRatePlan.objects.get_or_create(
            room_type=room_type,
            rate_plan=rate_plan,
            defaults={
                'base_price': starting_price,
            }
        )
        
        if not rate_created:
            # Update existing rate with current starting price
            room_rate.base_price = starting_price
            room_rate.save()
            
        print(f"   ✅ Set base price: {starting_price} {room_type.currency}")
        updated_count += 1
        print()
    
    print(f"🎉 Updated {updated_count} room types with base pricing")


def create_sample_discounts():
    """Create sample discount promotions for testing"""
    print("\n🎁 Creating sample discount promotions...\n")
    
    from datetime import date, timedelta
    
    hotels = Hotel.objects.all()
    
    for hotel in hotels:
        # Winter discount
        winter_promo, created = Promotion.objects.get_or_create(
            hotel=hotel,
            code='WINTER20',
            defaults={
                'name': 'Winter Special',
                'description': '20% off winter stays',
                'discount_percent': Decimal('20.00'),
                'valid_from': date.today(),
                'valid_until': date.today() + timedelta(days=90),
                'is_active': True,
            }
        )
        
        if created:
            print(f"✅ Created WINTER20 promotion for {hotel.name}")
        
        # Early bird discount
        early_promo, created = Promotion.objects.get_or_create(
            hotel=hotel,
            code='EARLY10',
            defaults={
                'name': 'Early Bird Special',
                'description': '10% off for advance bookings',
                'discount_percent': Decimal('10.00'),
                'valid_from': date.today(),
                'valid_until': date.today() + timedelta(days=60),
                'is_active': True,
            }
        )
        
        if created:
            print(f"✅ Created EARLY10 promotion for {hotel.name}")


def test_pricing_calculation():
    """Test the pricing calculation with discounts"""
    print("\n🧮 Testing pricing calculations...\n")
    
    # Test with Hotel Killarney
    try:
        hotel = Hotel.objects.get(slug='hotel-killarney')
        room_type = RoomType.objects.filter(hotel=hotel, is_active=True).first()
        
        if not room_type:
            print("❌ No active room types found for testing")
            return
        
        print(f"🏨 Testing with: {room_type.name}")
        
        # Get base price from rate plan
        rate_plan = RatePlan.objects.filter(hotel=hotel, code='STANDARD').first()
        if rate_plan:
            room_rate = RoomTypeRatePlan.objects.filter(
                room_type=room_type,
                rate_plan=rate_plan
            ).first()
            
            if room_rate:
                base_price = room_rate.base_price
                print(f"   💰 Base price: {base_price} {room_type.currency}")
                
                # Test with discount
                winter_promo = Promotion.objects.filter(
                    hotel=hotel,
                    code='WINTER20',
                    is_active=True
                ).first()
                
                if winter_promo:
                    discount_amount = base_price * (winter_promo.discount_percent / 100)
                    discounted_price = base_price - discount_amount
                    
                    print(f"   🎁 With WINTER20 ({winter_promo.discount_percent}% off):")
                    print(f"      Original: {base_price} {room_type.currency}")
                    print(f"      Discount: -{discount_amount} {room_type.currency}")
                    print(f"      Final: {discounted_price} {room_type.currency}")
                
            else:
                print("❌ No rate plan link found")
        else:
            print("❌ No rate plan found")
            
    except Hotel.DoesNotExist:
        print("❌ Hotel Killarney not found")


if __name__ == '__main__':
    print("=" * 60)
    print("ROOM PRICING SETUP")
    print("=" * 60)
    
    set_base_prices()
    create_sample_discounts()
    test_pricing_calculation()
    
    print("\n" + "=" * 60)
    print("✅ PRICING SETUP COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update the public serializer to show calculated prices")
    print("2. Apply discounts in the booking flow")
    print("3. Test the pricing API endpoints")