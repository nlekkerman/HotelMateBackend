"""
Management command to populate PMS data for Killarney hotel (id=2)
Populates: RatePlans, Promotions, DailyRates, RoomTypeInventory
Does NOT create bookings - only configuration data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from hotel.models import Hotel
from rooms.models import (
    RoomType, 
    RatePlan, 
    RoomTypeRatePlan, 
    DailyRate, 
    Promotion, 
    RoomTypeInventory
)


class Command(BaseCommand):
    help = 'Populate PMS configuration data for Killarney hotel (id=2)'

    def handle(self, *args, **options):
        try:
            hotel = Hotel.objects.get(id=2)
            self.stdout.write(f"Found hotel: {hotel.name}")
        except Hotel.DoesNotExist:
            self.stdout.write(self.style.ERROR("Hotel with id=2 (Killarney) not found!"))
            return

        # Get room types for this hotel
        room_types = list(RoomType.objects.filter(hotel=hotel))
        if not room_types:
            self.stdout.write(self.style.ERROR("No room types found for Killarney hotel!"))
            return
        
        self.stdout.write(f"Found {len(room_types)} room types")

        # Clear existing PMS data for this hotel
        self.stdout.write("Clearing existing PMS data...")
        RatePlan.objects.filter(hotel=hotel).delete()
        Promotion.objects.filter(hotel=hotel).delete()
        
        # 1. Create Rate Plans
        self.stdout.write("\n=== Creating Rate Plans ===")
        
        standard_plan = RatePlan.objects.create(
            hotel=hotel,
            name="Standard Rate",
            code="STD",
            description="Standard flexible rate with free cancellation up to 24 hours before check-in",
            is_refundable=True,
            default_discount_percent=Decimal('0.00'),
            is_active=True
        )
        self.stdout.write(f"✓ Created: {standard_plan.name} ({standard_plan.code})")

        nonrefundable_plan = RatePlan.objects.create(
            hotel=hotel,
            name="Non-Refundable Rate",
            code="NRF",
            description="Save 15% with non-refundable booking - no cancellations or modifications",
            is_refundable=False,
            default_discount_percent=Decimal('15.00'),
            is_active=True
        )
        self.stdout.write(f"✓ Created: {nonrefundable_plan.name} ({nonrefundable_plan.code})")

        early_bird_plan = RatePlan.objects.create(
            hotel=hotel,
            name="Early Bird 30",
            code="EB30",
            description="Book 30 days in advance and save 20% - free cancellation up to 7 days before check-in",
            is_refundable=True,
            default_discount_percent=Decimal('20.00'),
            is_active=True
        )
        self.stdout.write(f"✓ Created: {early_bird_plan.name} ({early_bird_plan.code})")

        # 2. Link Rate Plans to Room Types with base prices
        self.stdout.write("\n=== Linking Rate Plans to Room Types ===")
        
        base_prices = {
            'Single Room': Decimal('89.00'),
            'Double Room': Decimal('129.00'),
            'Deluxe Room': Decimal('179.00'),
            'Suite': Decimal('249.00'),
            'Family Room': Decimal('199.00'),
        }

        for room_type in room_types:
            base_price = base_prices.get(room_type.name, Decimal('120.00'))
            
            # Standard rate
            RoomTypeRatePlan.objects.create(
                room_type=room_type,
                rate_plan=standard_plan,
                base_price=base_price
            )
            
            # Non-refundable (15% discount)
            nrf_price = (base_price * Decimal('0.85')).quantize(Decimal('0.01'))
            RoomTypeRatePlan.objects.create(
                room_type=room_type,
                rate_plan=nonrefundable_plan,
                base_price=nrf_price
            )
            
            # Early bird (20% discount)
            eb_price = (base_price * Decimal('0.80')).quantize(Decimal('0.01'))
            RoomTypeRatePlan.objects.create(
                room_type=room_type,
                rate_plan=early_bird_plan,
                base_price=eb_price
            )
            
            self.stdout.write(f"✓ Linked {room_type.name}: €{base_price} / €{nrf_price} / €{eb_price}")

        # 3. Create Promotions
        self.stdout.write("\n=== Creating Promotions ===")
        
        today = timezone.now().date()
        
        winter_promo = Promotion.objects.create(
            hotel=hotel,
            code="WINTER20",
            name="Winter Special",
            description="20% off winter stays",
            discount_percent=Decimal('20.00'),
            discount_fixed=None,
            valid_from=today,
            valid_until=today + timedelta(days=90),
            min_nights=2,
            is_active=True
        )
        # Apply to all room types
        winter_promo.room_types.set(room_types)
        self.stdout.write(f"✓ Created: {winter_promo.code} - {winter_promo.discount_percent}% off")

        save10_promo = Promotion.objects.create(
            hotel=hotel,
            code="SAVE10",
            name="Save €10",
            description="€10 off your booking",
            discount_percent=None,
            discount_fixed=Decimal('10.00'),
            valid_from=today,
            valid_until=today + timedelta(days=60),
            min_nights=1,
            is_active=True
        )
        save10_promo.room_types.set(room_types)
        self.stdout.write(f"✓ Created: {save10_promo.code} - €{save10_promo.discount_fixed} off")

        longstay_promo = Promotion.objects.create(
            hotel=hotel,
            code="LONGSTAY",
            name="Long Stay Discount",
            description="Stay 5+ nights, get 25% off",
            discount_percent=Decimal('25.00'),
            discount_fixed=None,
            valid_from=today,
            valid_until=today + timedelta(days=120),
            min_nights=5,
            is_active=True
        )
        longstay_promo.room_types.set(room_types)
        self.stdout.write(f"✓ Created: {longstay_promo.code} - {longstay_promo.discount_percent}% off (5+ nights)")

        lastminute_promo = Promotion.objects.create(
            hotel=hotel,
            code="LASTMINUTE30",
            name="Last Minute Deal",
            description="Book within 3 days, save 30%",
            discount_percent=Decimal('30.00'),
            discount_fixed=None,
            valid_from=today,
            valid_until=today + timedelta(days=30),
            min_nights=1,
            is_active=True
        )
        # Only apply to standard and deluxe rooms
        applicable_types = [rt for rt in room_types if rt.name in ['Standard Room', 'Deluxe Double Room']]
        if applicable_types:
            lastminute_promo.room_types.set(applicable_types)
        else:
            lastminute_promo.room_types.set(room_types)
        self.stdout.write(f"✓ Created: {lastminute_promo.code} - {lastminute_promo.discount_percent}% off (last minute)")

        # 4. Create Daily Rate Adjustments (weekend premiums)
        self.stdout.write("\n=== Creating Daily Rate Adjustments ===")
        
        adjustment_count = 0
        # Add weekend premiums for next 90 days
        for i in range(90):
            date = today + timedelta(days=i)
            # Friday and Saturday get 25% premium
            if date.weekday() in [4, 5]:  # Friday=4, Saturday=5
                for room_type in room_types:
                    # Get base price from RoomTypeRatePlan
                    try:
                        rtrp = RoomTypeRatePlan.objects.get(room_type=room_type, rate_plan=standard_plan)
                        weekend_price = (rtrp.base_price * Decimal('1.25')).quantize(Decimal('0.01'))
                        DailyRate.objects.create(
                            room_type=room_type,
                            rate_plan=standard_plan,
                            date=date,
                            price=weekend_price
                        )
                        adjustment_count += 1
                    except RoomTypeRatePlan.DoesNotExist:
                        pass
        
        self.stdout.write(f"✓ Created {adjustment_count} weekend premium daily rates")

        # 5. Create Inventory Records
        self.stdout.write("\n=== Creating Inventory Records ===")
        
        inventory_count = 0
        # Set available rooms for next 90 days
        for i in range(90):
            date = today + timedelta(days=i)
            
            for room_type in room_types:
                # Default: rooms available based on room type capacity
                total = 5  # default
                if 'Suite' in room_type.name:
                    total = 2
                elif 'Family' in room_type.name:
                    total = 3
                elif 'Standard' in room_type.name or 'Double' in room_type.name:
                    total = 8
                
                # Special cases
                stop_sell_flag = False
                
                # Christmas period (Dec 24-26) - stop sell
                if date.month == 12 and date.day in [24, 25, 26]:
                    stop_sell_flag = True
                    total = 0
                
                # New Year's Eve - limited availability
                if date.month == 12 and date.day == 31:
                    total = max(1, total // 2)
                
                # Valentine's Day - limited availability
                if date.month == 2 and date.day == 14:
                    total = max(1, total // 2)
                
                RoomTypeInventory.objects.create(
                    room_type=room_type,
                    date=date,
                    total_rooms=total,
                    stop_sell=stop_sell_flag
                )
                inventory_count += 1
        
        self.stdout.write(f"✓ Created {inventory_count} inventory records")

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("✓ PMS Data Population Complete!"))
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(f"Hotel: {hotel.name} (id={hotel.id})")
        self.stdout.write(f"Rate Plans: 3 (STD, NRF, EB30)")
        self.stdout.write(f"Room Type Links: {len(room_types) * 3}")
        self.stdout.write(f"Promotions: 4 (WINTER20, SAVE10, LONGSTAY, LASTMINUTE30)")
        self.stdout.write(f"Daily Rate Adjustments: {adjustment_count} (weekend premiums)")
        self.stdout.write(f"Inventory Records: {inventory_count} (90 days)")
        self.stdout.write(self.style.SUCCESS("\nReady to test booking flow! 🎉"))
